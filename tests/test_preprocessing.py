import pytest
import asyncio
from unittest.mock import MagicMock, patch
from typing import Dict, Any

import nats
import json

from qraft.preprocessing.pipeline import Pipeline
from qraft.preprocessing.operators import (
    get_operator, create_validate_schema_operator,
    create_add_timestamp_operator, create_drop_malformed_operator
)


@pytest.mark.asyncio
async def test_pipeline_init():
    """测试预处理管道初始化"""
    # 创建模拟客户端
    mock_nats = MagicMock()
    mock_clickhouse = MagicMock()
    
    # 创建管道配置
    config = {
        "default": [
            {"name": "validate_schema", "config": {"strict": True}},
            {"name": "add_timestamp", "config": {"field": "processing_time"}}
        ],
        "pipelines": [
            {
                "source": "test-source",
                "operators": [
                    {"name": "normalize_price", "config": {"fields": ["price"]}}
                ]
            }
        ]
    }
    
    # 创建管道
    with patch("qraft.preprocessing.operators.get_operator") as mock_get_operator:
        mock_get_operator.return_value = lambda x: x
        pipeline = Pipeline(config, mock_nats, mock_clickhouse)
        
        # 验证属性
        assert len(pipeline.default_operators) == 2
        assert "test-source" in pipeline.source_operators
        assert len(pipeline.source_operators["test-source"]) == 1


@pytest.mark.asyncio
async def test_validate_schema_operator():
    """测试架构验证操作符"""
    # 创建操作符
    operator = create_validate_schema_operator({"strict": True})
    
    # 测试有效事件
    valid_event = {
        "event_id": "test-event-id",
        "source": "test-source",
        "type": "test-type",
        "timestamp": "2023-01-01T00:00:00Z",
        "payload": {}
    }
    result = await operator(valid_event)
    assert result == valid_event
    
    # 测试无效事件
    invalid_event = {
        "source": "test-source",
        "type": "test-type"
    }
    result = await operator(invalid_event)
    assert result is None
    
    # 测试非严格模式
    operator = create_validate_schema_operator({"strict": False})
    result = await operator(invalid_event)
    assert result is not None
    assert "event_id" in result
    assert "timestamp" in result
    assert "payload" in result


@pytest.mark.asyncio
async def test_add_timestamp_operator():
    """测试添加时间戳操作符"""
    # 创建操作符
    operator = create_add_timestamp_operator({"field": "test_time"})
    
    # 测试事件
    event = {
        "event_id": "test-event-id",
        "source": "test-source",
        "type": "test-type",
        "timestamp": "2023-01-01T00:00:00Z",
        "payload": {}
    }
    result = await operator(event)
    
    # 验证结果
    assert "meta" in result
    assert "test_time" in result["meta"]
    assert isinstance(result["meta"]["test_time"], str)


@pytest.mark.asyncio
async def test_drop_malformed_operator():
    """测试丢弃畸形数据操作符"""
    # 创建操作符
    operator = create_drop_malformed_operator({"required_payload_fields": ["field1", "field2"]})
    
    # 测试有效事件
    valid_event = {
        "event_id": "test-event-id",
        "source": "test-source",
        "type": "test-type",
        "timestamp": "2023-01-01T00:00:00Z",
        "payload": {"field1": "value1", "field2": "value2"}
    }
    result = await operator(valid_event)
    assert result == valid_event
    
    # 测试无效事件
    invalid_event = {
        "event_id": "test-event-id",
        "source": "test-source",
        "type": "test-type",
        "timestamp": "2023-01-01T00:00:00Z",
        "payload": {"field1": "value1"}
    }
    result = await operator(invalid_event)
    assert result is None