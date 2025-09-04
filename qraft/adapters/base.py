import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

import nats
from pydantic import BaseModel
from loguru import logger


class EventModel(BaseModel):
    """标准事件模型"""
    event_id: str
    source: str
    type: str
    timestamp: datetime
    payload: Dict[str, Any]
    meta: Dict[str, Any]


class BaseAdapter:
    """适配器基类，提供通用功能"""
    
    def __init__(self, name: str, config: Dict[str, Any], nats_client):
        """
        初始化适配器
        
        Args:
            name: 适配器名称
            config: 适配器配置
            nats_client: NATS客户端实例
        """
        self.name = name
        self.config = config
        self.nats = nats_client
        self.running = False
        self.topic = f"events.{name}"
        self.logger = logger.bind(adapter=name)
    
    async def start(self):
        """启动适配器"""
        self.running = True
        self.logger.info(f"Starting adapter {self.name}")
        await self._run()
    
    async def stop(self):
        """停止适配器"""
        self.running = False
        self.logger.info(f"Stopping adapter {self.name}")
    
    async def _run(self):
        """适配器主循环，子类必须实现"""
        raise NotImplementedError("Subclasses must implement _run()")
    
    async def emit_event(self, event_type: str, payload: Dict[str, Any], 
                        timestamp: Optional[datetime] = None, 
                        meta: Optional[Dict[str, Any]] = None):
        """发送标准格式事件到NATS
        
        Args:
            event_type: 事件类型
            payload: 事件负载
            timestamp: 事件时间戳，默认为当前时间
            meta: 事件元数据，默认为空字典
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        if meta is None:
            meta = {}
        
        # 添加适配器版本信息
        meta["adapter_version"] = "1.0"
        
        event = EventModel(
            event_id=str(uuid.uuid4()),
            source=self.name,
            type=event_type,
            timestamp=timestamp,
            payload=payload,
            meta=meta
        )
        
        # 发送到NATS
        await self.nats.publish(self.topic, event.model_dump_json().encode())
        self.logger.debug(f"Emitted event: {event.event_id}")