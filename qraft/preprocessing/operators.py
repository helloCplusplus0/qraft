from datetime import datetime
from typing import Dict, Any, Callable, Optional, List

import polars as pl
import numpy as np
from loguru import logger


def get_operator(name: str, config: Dict[str, Any]) -> Optional[Callable]:
    """获取操作符函数
    
    Args:
        name: 操作符名称
        config: 操作符配置
        
    Returns:
        操作符函数，如果不存在则返回None
    """
    operators = {
        "validate_schema": create_validate_schema_operator,
        "add_timestamp": create_add_timestamp_operator,
        "drop_malformed": create_drop_malformed_operator,
        "normalize_price": create_normalize_operator,
        "aggregate": create_aggregate_operator,
        "extract_features": create_feature_extraction_operator
    }
    
    if name in operators:
        return operators[name](config)
    return None


def create_validate_schema_operator(config: Dict[str, Any]) -> Callable:
    """创建架构验证操作符
    
    Args:
        config: 操作符配置
        
    Returns:
        架构验证操作符函数
    """
    strict = config.get("strict", True)
    
    async def validate_schema(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """验证事件架构
        
        Args:
            event: 事件数据
            
        Returns:
            验证后的事件，如果验证失败则返回None
        """
        required_fields = ["event_id", "source", "type", "timestamp", "payload"]
        
        for field in required_fields:
            if field not in event:
                if strict:
                    logger.warning(f"Schema validation failed: missing field '{field}'")
                    return None
                else:
                    # 添加默认值
                    if field == "event_id":
                        import uuid
                        event["event_id"] = str(uuid.uuid4())
                    elif field == "timestamp":
                        event["timestamp"] = datetime.utcnow().isoformat()
                    elif field == "payload":
                        event["payload"] = {}
                    elif field == "meta":
                        event["meta"] = {}
        
        return event
    
    return validate_schema


def create_add_timestamp_operator(config: Dict[str, Any]) -> Callable:
    """创建添加时间戳操作符
    
    Args:
        config: 操作符配置
        
    Returns:
        添加时间戳操作符函数
    """
    field = config.get("field", "processing_time")
    
    async def add_timestamp(event: Dict[str, Any]) -> Dict[str, Any]:
        """添加处理时间戳
        
        Args:
            event: 事件数据
            
        Returns:
            添加时间戳后的事件
        """
        if "meta" not in event:
            event["meta"] = {}
        
        event["meta"][field] = datetime.utcnow().isoformat()
        return event
    
    return add_timestamp


def create_drop_malformed_operator(config: Dict[str, Any]) -> Callable:
    """创建丢弃畸形数据操作符
    
    Args:
        config: 操作符配置
        
    Returns:
        丢弃畸形数据操作符函数
    """
    required_payload_fields = config.get("required_payload_fields", [])
    
    async def drop_malformed(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """丢弃畸形数据
        
        Args:
            event: 事件数据
            
        Returns:
            验证后的事件，如果验证失败则返回None
        """
        payload = event.get("payload", {})
        
        # 检查必需的负载字段
        for field in required_payload_fields:
            if field not in payload:
                logger.warning(f"Malformed event: missing payload field '{field}'")
                return None
        
        return event
    
    return drop_malformed


def create_normalize_operator(config: Dict[str, Any]) -> Callable:
    """创建归一化操作符
    
    Args:
        config: 操作符配置
        
    Returns:
        归一化操作符函数
    """
    fields = config.get("fields", [])
    method = config.get("method", "min_max")
    window_size = config.get("window_size", 100)
    
    # 保存最近的值用于归一化
    state = {field: {"values": [], "min": None, "max": None, "sum": 0, "sum_sq": 0, "count": 0} for field in fields}
    
    async def normalize(event: Dict[str, Any]) -> Dict[str, Any]:
        """归一化字段
        
        Args:
            event: 事件数据
            
        Returns:
            归一化后的事件
        """
        payload = event.get("payload", {})
        
        for field in fields:
            if field in payload and isinstance(payload[field], (int, float)):
                value = payload[field]
                field_state = state[field]
                
                # 更新状态
                field_state["values"].append(value)
                if len(field_state["values"]) > window_size:
                    field_state["values"].pop(0)
                
                field_state["min"] = min(field_state["values"])
                field_state["max"] = max(field_state["values"])
                field_state["sum"] = sum(field_state["values"])
                field_state["sum_sq"] = sum(v**2 for v in field_state["values"])
                field_state["count"] = len(field_state["values"])
                
                # 归一化
                if method == "min_max" and field_state["min"] != field_state["max"]:
                    normalized = (value - field_state["min"]) / (field_state["max"] - field_state["min"])
                    payload[f"{field}_normalized"] = normalized
                
                elif method == "z_score" and field_state["count"] > 1:
                    mean = field_state["sum"] / field_state["count"]
                    variance = (field_state["sum_sq"] / field_state["count"]) - (mean ** 2)
                    std = max(np.sqrt(variance), 1e-8)  # 避免除零
                    normalized = (value - mean) / std
                    payload[f"{field}_normalized"] = normalized
        
        event["payload"] = payload
        return event
    
    return normalize


def create_aggregate_operator(config: Dict[str, Any]) -> Callable:
    """创建聚合操作符
    
    Args:
        config: 操作符配置
        
    Returns:
        聚合操作符函数
    """
    window = config.get("window", "1m")
    method = config.get("method", "ohlcv")
    
    # 解析窗口大小
    window_size = int(window[:-1])
    window_unit = window[-1]
    
    if window_unit == "s":
        window_seconds = window_size
    elif window_unit == "m":
        window_seconds = window_size * 60
    elif window_unit == "h":
        window_seconds = window_size * 3600
    else:
        window_seconds = 60  # 默认1分钟
    
    # 保存窗口数据
    windows = {}
    
    async def aggregate(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """聚合数据
        
        Args:
            event: 事件数据
            
        Returns:
            聚合后的事件，如果不是窗口结束则返回None
        """
        source = event.get("source")
        event_type = event.get("type")
        timestamp = datetime.fromisoformat(event.get("timestamp"))
        payload = event.get("payload", {})
        
        # 计算窗口ID
        window_id = int(timestamp.timestamp() / window_seconds) * window_seconds
        window_key = f"{source}:{event_type}:{window_id}"
        
        # 初始化窗口
        if window_key not in windows:
            windows[window_key] = {
                "data": [],
                "start_time": datetime.fromtimestamp(window_id),
                "end_time": datetime.fromtimestamp(window_id + window_seconds)
            }
        
        # 添加数据到窗口
        windows[window_key]["data"].append(payload)
        
        # 检查是否超过窗口结束时间
        if timestamp >= windows[window_key]["end_time"]:
            # 执行聚合
            if method == "ohlcv" and "price" in payload and "quantity" in payload:
                window_data = windows[window_key]["data"]
                
                if not window_data:
                    del windows[window_key]
                    return None
                
                prices = [item.get("price", 0) for item in window_data if "price" in item]
                volumes = [item.get("quantity", 0) for item in window_data if "quantity" in item]
                
                if not prices or not volumes:
                    del windows[window_key]
                    return None
                
                aggregated_payload = {
                    "open": prices[0],
                    "high": max(prices),
                    "low": min(prices),
                    "close": prices[-1],
                    "volume": sum(volumes),
                    "count": len(window_data)
                }
                
                # 创建聚合事件
                aggregated_event = {
                    "event_id": event["event_id"],
                    "source": source,
                    "type": f"{event_type}_aggregated",
                    "timestamp": windows[window_key]["end_time"].isoformat(),
                    "payload": aggregated_payload,
                    "meta": {
                        "window": window,
                        "method": method,
                        "original_count": len(window_data)
                    }
                }
                
                # 清理窗口
                del windows[window_key]
                
                return aggregated_event
            else:
                # 清理窗口
                del windows[window_key]
        
        return None
    
    return aggregate


def create_feature_extraction_operator(config: Dict[str, Any]) -> Callable:
    """创建特征提取操作符
    
    Args:
        config: 操作符配置
        
    Returns:
        特征提取操作符函数
    """
    features = config.get("features", [])
    window_size = config.get("window_size", 20)
    
    # 保存历史数据
    history = {}
    
    async def extract_features(event: Dict[str, Any]) -> Dict[str, Any]:
        """提取特征
        
        Args:
            event: 事件数据
            
        Returns:
            添加特征后的事件
        """
        source = event.get("source")
        event_type = event.get("type")
        payload = event.get("payload", {})
        
        # 初始化历史数据
        key = f"{source}:{event_type}"
        if key not in history:
            history[key] = []
        
        # 添加当前数据到历史
        history[key].append(payload)
        if len(history[key]) > window_size * 2:  # 保留足够的历史数据
            history[key].pop(0)
        
        # 提取特征
        for feature in features:
            if feature.startswith("sma_"):
                # 简单移动平均线
                try:
                    period = int(feature.split("_")[1])
                    if "close" in payload and len(history[key]) >= period:
                        closes = [item.get("close", 0) for item in history[key][-period:]]
                        payload[feature] = sum(closes) / period
                except (ValueError, IndexError):
                    pass
            
            elif feature.startswith("ema_"):
                # 指数移动平均线
                try:
                    period = int(feature.split("_")[1])
                    if "close" in payload and len(history[key]) >= period:
                        closes = [item.get("close", 0) for item in history[key][-period:]]
                        alpha = 2 / (period + 1)
                        ema = closes[0]
                        for close in closes[1:]:
                            ema = alpha * close + (1 - alpha) * ema
                        payload[feature] = ema
                except (ValueError, IndexError):
                    pass
            
            elif feature == "rsi_14":
                # 相对强弱指数
                try:
                    period = 14
                    if "close" in payload and len(history[key]) >= period + 1:
                        closes = [item.get("close", 0) for item in history[key][-(period+1):]]
                        gains = [max(closes[i] - closes[i-1], 0) for i in range(1, len(closes))]
                        losses = [max(closes[i-1] - closes[i], 0) for i in range(1, len(closes))]
                        avg_gain = sum(gains) / period
                        avg_loss = sum(losses) / period
                        if avg_loss == 0:
                            payload[feature] = 100
                        else:
                            rs = avg_gain / avg_loss
                            payload[feature] = 100 - (100 / (1 + rs))
                except (ValueError, IndexError, ZeroDivisionError):
                    pass
        
        event["payload"] = payload
        return event
    
    return extract_features