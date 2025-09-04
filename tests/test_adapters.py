import pytest
import asyncio
from unittest.mock import MagicMock, patch
from typing import Dict, Any

import nats

from qraft.adapters.base import BaseAdapter, EventModel
from qraft.adapters.websocket import WebSocketAdapter
from qraft.adapters.rest import RESTAdapter
from qraft.adapters.file import FileAdapter


@pytest.mark.asyncio
async def test_base_adapter_emit_event():
    """测试基础适配器的事件发送功能"""
    # 创建模拟NATS客户端
    mock_nats = MagicMock()
    mock_nats.publish = MagicMock(return_value=asyncio.Future())
    mock_nats.publish.return_value.set_result(None)
    
    # 创建适配器
    adapter = BaseAdapter("test-adapter", {}, mock_nats)
    
    # 发送事件
    await adapter.emit_event("test-event", {"field": "value"})
    
    # 验证NATS发布被调用
    mock_nats.publish.assert_called_once()
    args, kwargs = mock_nats.publish.call_args
    assert args[0] == "events.test-adapter"
    assert isinstance(args[1], bytes)


@pytest.mark.asyncio
async def test_websocket_adapter_init():
    """测试WebSocket适配器初始化"""
    # 创建模拟NATS客户端
    mock_nats = MagicMock()
    
    # 创建适配器配置
    config = {
        "url": "wss://example.com/ws",
        "reconnect_interval": 10,
        "parser": "binance_trade_parser",
        "batch_size": 50,
        "batch_interval_ms": 1000
    }
    
    # 创建适配器
    with patch("qraft.adapters.websocket.WebSocketAdapter._get_parser") as mock_get_parser:
        mock_get_parser.return_value = lambda x: ("test", {}, None)
        adapter = WebSocketAdapter("test-websocket", config, mock_nats)
        
        # 验证属性
        assert adapter.name == "test-websocket"
        assert adapter.url == "wss://example.com/ws"
        assert adapter.reconnect_interval == 10
        assert adapter.parser_name == "binance_trade_parser"
        assert adapter.batch_size == 50
        assert adapter.batch_interval == 1.0


@pytest.mark.asyncio
async def test_rest_adapter_init():
    """测试REST适配器初始化"""
    # 创建模拟NATS客户端
    mock_nats = MagicMock()
    
    # 创建适配器配置
    config = {
        "url": "https://example.com/api",
        "interval_sec": 30,
        "params": {"param1": "value1"},
        "headers": {"header1": "value1"},
        "parser": "yahoo_finance_parser",
        "retry_count": 5,
        "retry_delay": 10
    }
    
    # 创建适配器
    with patch("qraft.adapters.rest.RESTAdapter._get_parser") as mock_get_parser:
        mock_get_parser.return_value = lambda x: ("test", {}, None)
        adapter = RESTAdapter("test-rest", config, mock_nats)
        
        # 验证属性
        assert adapter.name == "test-rest"
        assert adapter.url == "https://example.com/api"
        assert adapter.interval == 30
        assert adapter.params == {"param1": "value1"}
        assert adapter.headers == {"header1": "value1"}
        assert adapter.parser_name == "yahoo_finance_parser"
        assert adapter.retry_count == 5
        assert adapter.retry_delay == 10


@pytest.mark.asyncio
async def test_file_adapter_init():
    """测试文件适配器初始化"""
    # 创建模拟NATS客户端
    mock_nats = MagicMock()
    
    # 创建适配器配置
    config = {
        "path": "/data/test/*.csv",
        "watch": True,
        "parser": "csv_parser",
        "options": {
            "delimiter": ",",
            "header": True
        }
    }
    
    # 创建适配器
    with patch("qraft.adapters.file.FileAdapter._get_parser") as mock_get_parser:
        mock_get_parser.return_value = lambda x: []
        adapter = FileAdapter("test-file", config, mock_nats)
        
        # 验证属性
        assert adapter.name == "test-file"
        assert adapter.path == "/data/test/*.csv"
        assert adapter.watch == True
        assert adapter.parser_name == "csv_parser"
        assert adapter.options == {"delimiter": ",", "header": True}