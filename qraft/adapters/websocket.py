import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List, Tuple

import websockets
from loguru import logger

from .base import BaseAdapter


class WebSocketAdapter(BaseAdapter):
    """WebSocket适配器，用于连接WebSocket数据源"""
    
    def __init__(self, name: str, config: Dict[str, Any], nats_client):
        """
        初始化WebSocket适配器
        
        Args:
            name: 适配器名称
            config: 适配器配置
            nats_client: NATS客户端实例
        """
        super().__init__(name, config, nats_client)
        self.url = config["url"]
        self.reconnect_interval = config.get("reconnect_interval", 5)
        self.parser_name = config["parser"]
        self.parser = self._get_parser(self.parser_name)
        self.batch_size = config.get("batch_size", 1)
        self.batch_interval = config.get("batch_interval_ms", 0) / 1000
        self.batch: List[Tuple[str, Dict[str, Any], datetime]] = []
    
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
        if parser_name == "binance_trade_parser":
            return self._parse_binance_trade
        else:
            raise ValueError(f"Unknown parser: {parser_name}")
    
    def _parse_binance_trade(self, data: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[datetime]]:
        """解析Binance交易数据
        
        Args:
            data: 原始数据
            
        Returns:
            事件类型、负载和时间戳的元组
        """
        try:
            event_type = "trade"
            timestamp = datetime.fromtimestamp(data["T"] / 1000)
            payload = {
                "symbol": data["s"],
                "price": float(data["p"]),
                "quantity": float(data["q"]),
                "side": "buy" if data["m"] else "sell"
            }
            return event_type, payload, timestamp
        except (KeyError, ValueError) as e:
            self.logger.error(f"Parse error: {e}")
            return None, None, None
    
    async def _process_message(self, message: str):
        """处理WebSocket消息
        
        Args:
            message: WebSocket消息
        """
        try:
            data = json.loads(message)
            event_type, payload, timestamp = self.parser(data)
            
            if event_type and payload and timestamp:
                if self.batch_size > 1:
                    # 批处理模式
                    self.batch.append((event_type, payload, timestamp))
                    if len(self.batch) >= self.batch_size:
                        await self._emit_batch()
                else:
                    # 单条处理模式
                    await self.emit_event(event_type, payload, timestamp)
        except Exception as e:
            self.logger.error(f"Process error: {e}")
    
    async def _emit_batch(self):
        """发送批量事件"""
        if not self.batch:
            return
        
        for event_type, payload, timestamp in self.batch:
            await self.emit_event(event_type, payload, timestamp)
        
        self.batch = []
    
    async def _batch_timer_loop(self):
        """批处理定时器循环"""
        while self.running:
            await asyncio.sleep(self.batch_interval)
            if self.batch:
                await self._emit_batch()
    
    async def _run(self):
        """WebSocket适配器主循环"""
        batch_timer = None
        
        if self.batch_interval > 0 and self.batch_size > 1:
            batch_timer = asyncio.create_task(
                self._batch_timer_loop()
            )
        
        while self.running:
            try:
                self.logger.info(f"Connecting to {self.url}")
                async with websockets.connect(self.url) as websocket:
                    while self.running:
                        message = await websocket.recv()
                        await self._process_message(message)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                if self.running:
                    self.logger.info(f"Reconnecting in {self.reconnect_interval}s")
                    await asyncio.sleep(self.reconnect_interval)
        
        if batch_timer:
            batch_timer.cancel()