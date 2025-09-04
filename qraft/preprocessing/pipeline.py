import json
import asyncio
from typing import Dict, Any, List, Callable, Optional

import nats
from loguru import logger

from qraft.utils.config import load_config


class Pipeline:
    """预处理管道，处理从NATS接收的事件"""
    
    def __init__(self, config: Dict[str, Any], nats_client, clickhouse_client):
        """
        初始化预处理管道
        
        Args:
            config: 管道配置
            nats_client: NATS客户端实例
            clickhouse_client: ClickHouse客户端实例
        """
        self.config = config
        self.nats = nats_client
        self.clickhouse = clickhouse_client
        self.logger = logger.bind(component="pipeline")
        self.default_operators = self._setup_operators(config.get("default", []))
        self.source_operators = {}
        
        # 设置源特定操作符
        for pipeline_config in config.get("pipelines", []):
            source = pipeline_config.get("source")
            if source:
                operators = self._setup_operators(pipeline_config.get("operators", []))
                self.source_operators[source] = operators
    
    def _setup_operators(self, operator_configs: List[Dict[str, Any]]) -> List[Callable]:
        """设置操作符列表
        
        Args:
            operator_configs: 操作符配置列表
            
        Returns:
            操作符函数列表
        """
        from qraft.preprocessing.operators import get_operator
        
        operators = []
        for op_config in operator_configs:
            op_name = op_config.get("name")
            op_config = op_config.get("config", {})
            operator = get_operator(op_name, op_config)
            if operator:
                operators.append(operator)
            else:
                self.logger.warning(f"Unknown operator: {op_name}")
        return operators
    
    async def start(self):
        """启动管道"""
        self.logger.info("Starting preprocessing pipeline")
        
        # 订阅所有事件主题
        await self.nats.subscribe("events.*", cb=self._handle_event)
    
    async def _handle_event(self, msg):
        """处理NATS消息
        
        Args:
            msg: NATS消息
        """
        try:
            # 解析事件
            event = json.loads(msg.data.decode())
            source = event.get("source")
            
            # 存储原始事件
            await self._store_raw_event(event)
            
            # 应用默认操作符
            processed_event = event
            for operator in self.default_operators:
                processed_event = await operator(processed_event)
                if processed_event is None:
                    # 事件被过滤掉
                    return
            
            # 应用源特定操作符
            if source in self.source_operators:
                for operator in self.source_operators[source]:
                    processed_event = await operator(processed_event)
                    if processed_event is None:
                        # 事件被过滤掉
                        return
            
            # 存储处理后的事件
            await self._store_clean_event(processed_event)
            
            # 发布到模式引擎主题
            await self.nats.publish(
                "processed.events", 
                json.dumps(processed_event).encode()
            )
            
        except Exception as e:
            self.logger.error(f"Event processing error: {e}")
    
    async def _store_raw_event(self, event: Dict[str, Any]):
        """存储原始事件到ClickHouse
        
        Args:
            event: 原始事件
        """
        try:
            # 简化实现，实际应该使用批量插入
            await self.clickhouse.insert_event("raw_events", event)
        except Exception as e:
            self.logger.error(f"Raw event storage error: {e}")
    
    async def _store_clean_event(self, event: Dict[str, Any]):
        """存储处理后的事件到ClickHouse
        
        Args:
            event: 处理后的事件
        """
        try:
            # 简化实现，实际应该使用批量插入
            await self.clickhouse.insert_event("clean_events", event)
        except Exception as e:
            self.logger.error(f"Clean event storage error: {e}")