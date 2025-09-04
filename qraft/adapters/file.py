import asyncio
import csv
import glob
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List, Tuple

from loguru import logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from .base import BaseAdapter


class FileWatchHandler(FileSystemEventHandler):
    """文件监控处理器"""
    
    def __init__(self, callback):
        """
        初始化文件监控处理器
        
        Args:
            callback: 文件变化回调函数
        """
        self.callback = callback
    
    def on_created(self, event):
        """文件创建事件处理
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            self.callback(event.src_path)
    
    def on_modified(self, event):
        """文件修改事件处理
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            self.callback(event.src_path)


class FileAdapter(BaseAdapter):
    """文件适配器，用于监控文件变化"""
    
    def __init__(self, name: str, config: Dict[str, Any], nats_client):
        """
        初始化文件适配器
        
        Args:
            name: 适配器名称
            config: 适配器配置
            nats_client: NATS客户端实例
        """
        super().__init__(name, config, nats_client)
        self.path = config["path"]
        self.watch = config.get("watch", True)
        self.parser_name = config["parser"]
        self.parser = self._get_parser(self.parser_name)
        self.options = config.get("options", {})
        self.processed_files = set()
        self.observer = None
        self.loop = asyncio.get_event_loop()
    
    def _get_parser(self, parser_name: str) -> Callable:
        """获取解析器函数
        
        Args:
            parser_name: 解析器名称
            
        Returns:
            解析器函数
            
        Raises:
            ValueError: 如果解析器不存在
        """
        # 这里可以实现一个解析器注册表
        # 简化起见，这里使用一个示例解析器
        if parser_name == "csv_parser":
            return self._parse_csv
        elif parser_name == "json_parser":
            return self._parse_json
        else:
            raise ValueError(f"Unknown parser: {parser_name}")
    
    def _parse_csv(self, file_path: str) -> List[Tuple[str, Dict[str, Any], datetime]]:
        """解析CSV文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            事件类型、负载和时间戳的元组列表
        """
        events = []
        delimiter = self.options.get("delimiter", ",")
        has_header = self.options.get("header", True)
        timestamp_field = self.options.get("timestamp_field", "timestamp")
        timestamp_format = self.options.get("timestamp_format", "%Y-%m-%d %H:%M:%S")
        event_type = self.options.get("event_type", "file_data")
        
        try:
            with open(file_path, "r", newline="") as csvfile:
                if has_header:
                    reader = csv.DictReader(csvfile, delimiter=delimiter)
                    for row in reader:
                        try:
                            if timestamp_field in row:
                                timestamp = datetime.strptime(row[timestamp_field], timestamp_format)
                            else:
                                timestamp = datetime.utcnow()
                            
                            events.append((event_type, dict(row), timestamp))
                        except Exception as e:
                            self.logger.error(f"Row parse error: {e}")
                else:
                    reader = csv.reader(csvfile, delimiter=delimiter)
                    for row in reader:
                        try:
                            payload = {f"field_{i}": value for i, value in enumerate(row)}
                            events.append((event_type, payload, datetime.utcnow()))
                        except Exception as e:
                            self.logger.error(f"Row parse error: {e}")
        except Exception as e:
            self.logger.error(f"CSV parse error: {e}")
        
        return events
    
    def _parse_json(self, file_path: str) -> List[Tuple[str, Dict[str, Any], datetime]]:
        """解析JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            事件类型、负载和时间戳的元组列表
        """
        events = []
        timestamp_field = self.options.get("timestamp_field", "timestamp")
        timestamp_format = self.options.get("timestamp_format", "%Y-%m-%d %H:%M:%S")
        event_type = self.options.get("event_type", "file_data")
        
        try:
            with open(file_path, "r") as jsonfile:
                data = json.load(jsonfile)
                
                if isinstance(data, list):
                    for item in data:
                        try:
                            if timestamp_field in item:
                                if isinstance(item[timestamp_field], str):
                                    timestamp = datetime.strptime(item[timestamp_field], timestamp_format)
                                elif isinstance(item[timestamp_field], (int, float)):
                                    timestamp = datetime.fromtimestamp(item[timestamp_field])
                                else:
                                    timestamp = datetime.utcnow()
                            else:
                                timestamp = datetime.utcnow()
                            
                            events.append((event_type, item, timestamp))
                        except Exception as e:
                            self.logger.error(f"Item parse error: {e}")
                else:
                    if timestamp_field in data:
                        if isinstance(data[timestamp_field], str):
                            timestamp = datetime.strptime(data[timestamp_field], timestamp_format)
                        elif isinstance(data[timestamp_field], (int, float)):
                            timestamp = datetime.fromtimestamp(data[timestamp_field])
                        else:
                            timestamp = datetime.utcnow()
                    else:
                        timestamp = datetime.utcnow()
                    
                    events.append((event_type, data, timestamp))
        except Exception as e:
            self.logger.error(f"JSON parse error: {e}")
        
        return events
    
    def _file_callback(self, file_path: str):
        """文件变化回调函数
        
        Args:
            file_path: 文件路径
        """
        if file_path in self.processed_files and not self.options.get("reprocess", False):
            return
        
        self.logger.info(f"Processing file: {file_path}")
        
        try:
            events = self.parser(file_path)
            
            for event_type, payload, timestamp in events:
                asyncio.run_coroutine_threadsafe(
                    self.emit_event(event_type, payload, timestamp),
                    self.loop
                )
            
            self.processed_files.add(file_path)
        except Exception as e:
            self.logger.error(f"File processing error: {e}")
    
    async def _process_existing_files(self):
        """处理现有文件"""
        for file_path in glob.glob(self.path):
            if os.path.isfile(file_path):
                self._file_callback(file_path)
    
    async def _run(self):
        """文件适配器主循环"""
        # 处理现有文件
        await self._process_existing_files()
        
        # 如果启用监控，设置文件监控
        if self.watch:
            self.observer = Observer()
            handler = FileWatchHandler(self._file_callback)
            
            # 获取目录路径
            dir_path = os.path.dirname(self.path)
            if not dir_path:
                dir_path = "."
            
            self.observer.schedule(handler, dir_path, recursive=False)
            self.observer.start()
            
            try:
                while self.running:
                    await asyncio.sleep(1)
            finally:
                if self.observer.is_alive():
                    self.observer.stop()
                    self.observer.join()
        else:
            # 如果不监控，只处理一次后退出
            self.running = False