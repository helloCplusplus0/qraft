import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Tuple

import aiohttp
from loguru import logger

from .base import BaseAdapter


class RESTAdapter(BaseAdapter):
    """REST适配器，用于定时轮询REST API"""
    
    def __init__(self, name: str, config: Dict[str, Any], nats_client):
        """
        初始化REST适配器
        
        Args:
            name: 适配器名称
            config: 适配器配置
            nats_client: NATS客户端实例
        """
        super().__init__(name, config, nats_client)
        self.url = config["url"]
        self.interval = config.get("interval_sec", 60)
        self.params = config.get("params", {})
        self.headers = config.get("headers", {})
        self.parser_name = config["parser"]
        self.parser = self._get_parser(self.parser_name)
        self.retry_count = config.get("retry_count", 3)
        self.retry_delay = config.get("retry_delay", 5)
    
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
        if parser_name == "yahoo_finance_parser":
            return self._parse_yahoo_finance
        else:
            raise ValueError(f"Unknown parser: {parser_name}")
    
    def _parse_yahoo_finance(self, data: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[datetime]]:
        """解析Yahoo Finance数据
        
        Args:
            data: 原始数据
            
        Returns:
            事件类型、负载和时间戳的元组
        """
        try:
            event_type = "price"
            chart = data.get("chart", {})
            result = chart.get("result", [{}])[0]
            meta = result.get("meta", {})
            timestamp_list = result.get("timestamp", [])
            indicators = result.get("indicators", {})
            quote = indicators.get("quote", [{}])[0]
            
            if not timestamp_list or not quote:
                return None, None, None
            
            # 获取最新数据点
            latest_idx = -1
            latest_ts = timestamp_list[latest_idx]
            timestamp = datetime.fromtimestamp(latest_ts)
            
            payload = {
                "symbol": meta.get("symbol"),
                "open": quote.get("open", [])[latest_idx],
                "high": quote.get("high", [])[latest_idx],
                "low": quote.get("low", [])[latest_idx],
                "close": quote.get("close", [])[latest_idx],
                "volume": quote.get("volume", [])[latest_idx]
            }
            
            return event_type, payload, timestamp
        except (KeyError, IndexError, ValueError) as e:
            self.logger.error(f"Parse error: {e}")
            return None, None, None
    
    async def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """从REST API获取数据
        
        Returns:
            API响应数据，如果失败则为None
        """
        retry = 0
        while retry < self.retry_count:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.url, params=self.params, headers=self.headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            self.logger.error(f"API error: {response.status} - {await response.text()}")
            except Exception as e:
                self.logger.error(f"Fetch error: {e}")
            
            retry += 1
            if retry < self.retry_count:
                self.logger.info(f"Retrying in {self.retry_delay}s ({retry}/{self.retry_count})")
                await asyncio.sleep(self.retry_delay)
        
        return None
    
    async def _run(self):
        """REST适配器主循环"""
        while self.running:
            try:
                self.logger.debug(f"Fetching data from {self.url}")
                data = await self._fetch_data()
                
                if data:
                    event_type, payload, timestamp = self.parser(data)
                    if event_type and payload and timestamp:
                        await self.emit_event(event_type, payload, timestamp)
            except Exception as e:
                self.logger.error(f"Run error: {e}")
            
            await asyncio.sleep(self.interval)