import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

import nats
from loguru import logger

from qraft.utils.config import load_config


class PatternEngine:
    """模式发现引擎，使用River库检测数据流中的模式"""
    
    def __init__(self, config: Dict[str, Any], nats_client, clickhouse_client):
        """
        初始化模式引擎
        
        Args:
            config: 引擎配置
            nats_client: NATS客户端实例
            clickhouse_client: ClickHouse客户端实例
        """
        self.config = config
        self.nats = nats_client
        self.clickhouse = clickhouse_client
        self.logger = logger.bind(component="pattern_engine")
        self.detectors = {}
        
        # 初始化检测器
        for detector_config in config.get("detectors", []):
            name = detector_config.get("name")
            detector_type = detector_config.get("type")
            source = detector_config.get("source")
            detector_config = detector_config.get("config", {})
            
            from qraft.patterns.detectors import get_detector
            detector = get_detector(name, detector_type, detector_config)
            if detector:
                if source not in self.detectors:
                    self.detectors[source] = []
                self.detectors[source].append({
                    "name": name,
                    "type": detector_type,
                    "detector": detector
                })
            else:
                self.logger.warning(f"Unknown detector type: {detector_type}")
    
    async def start(self):
        """启动模式引擎"""
        self.logger.info("Starting pattern engine")
        
        # 订阅处理后的事件
        await self.nats.subscribe("processed.events", cb=self._handle_event)
    
    async def _handle_event(self, msg):
        """处理事件并检测模式
        
        Args:
            msg: NATS消息
        """
        try:
            # 解析事件
            event = json.loads(msg.data.decode())
            source = event.get("source")
            
            # 如果没有该源的检测器，直接返回
            if source not in self.detectors:
                return
            
            # 应用所有检测器
            for detector_info in self.detectors[source]:
                detector = detector_info["detector"]
                detector_name = detector_info["name"]
                detector_type = detector_info["type"]
                
                # 提取需要的字段
                features = self._extract_features(event, detector.feature_fields)
                if not features:
                    continue
                
                # 检测模式
                pattern = await detector.detect(features, event)
                
                if pattern:
                    # 添加检测器信息
                    if "details" not in pattern:
                        pattern["details"] = {}
                    pattern["details"]["detector"] = detector_name
                    pattern["type"] = detector_type
                    
                    # 存储模式事件
                    await self._store_pattern(pattern)
                    
                    # 发布模式事件
                    await self.nats.publish(
                        "patterns", 
                        json.dumps(pattern).encode()
                    )
        
        except Exception as e:
            self.logger.error(f"Pattern detection error: {e}")
    
    def _extract_features(self, event: Dict[str, Any], feature_fields: List[str]) -> Optional[Dict[str, float]]:
        """从事件中提取特征
        
        Args:
            event: 事件数据
            feature_fields: 特征字段列表
            
        Returns:
            特征字典，如果没有特征则返回None
        """
        features = {}
        payload = event.get("payload", {})
        
        for field in feature_fields:
            if field in payload and isinstance(payload[field], (int, float)):
                features[field] = payload[field]
        
        return features if features else None
    
    async def _store_pattern(self, pattern: Dict[str, Any]):
        """存储模式事件到ClickHouse
        
        Args:
            pattern: 模式事件
        """
        try:
            await self.clickhouse.insert_event("pattern_events", pattern)
        except Exception as e:
            self.logger.error(f"Pattern storage error: {e}")