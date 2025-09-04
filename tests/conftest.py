import os
import pytest
import asyncio
from typing import Dict, Any, Generator, AsyncGenerator

import nats
from clickhouse_driver import Client

from qraft.utils.config import load_config
from qraft.storage.clickhouse import ClickHouseClient


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环
    
    Returns:
        事件循环
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def config() -> Dict[str, Any]:
    """加载测试配置
    
    Returns:
        配置字典
    """
    config_dir = os.environ.get("QRAFT_CONFIG_DIR", "./configs")
    configs = {}
    
    # 加载适配器配置
    adapters_config = load_config(os.path.join(config_dir, "adapters.yaml"))
    configs["adapters"] = adapters_config
    
    # 加载预处理配置
    preprocessing_config = load_config(os.path.join(config_dir, "preprocessing.yaml"))
    configs["preprocessing"] = preprocessing_config
    
    # 加载检测器配置
    detectors_config = load_config(os.path.join(config_dir, "detectors.yaml"))
    configs["detectors"] = detectors_config
    
    # 加载API配置
    api_config = load_config(os.path.join(config_dir, "api.yaml"))
    configs["api"] = api_config
    
    return configs


@pytest.fixture(scope="session")
async def nats_client(event_loop) -> AsyncGenerator[nats.NATS, None]:
    """创建NATS客户端
    
    Args:
        event_loop: 事件循环
        
    Returns:
        NATS客户端
    """
    # 连接NATS
    client = await nats.connect("nats://localhost:4222")
    yield client
    await client.close()


@pytest.fixture(scope="session")
def clickhouse_client() -> ClickHouseClient:
    """创建ClickHouse客户端
    
    Returns:
        ClickHouse客户端
    """
    return ClickHouseClient(
        host="localhost",
        port=9000,
        user="default",
        password="",
        database="default"
    )


@pytest.fixture(scope="session")
def sample_event() -> Dict[str, Any]:
    """创建示例事件
    
    Returns:
        示例事件
    """
    return {
        "event_id": "test-event-id",
        "source": "test-source",
        "type": "test-type",
        "timestamp": "2023-01-01T00:00:00Z",
        "payload": {
            "field1": "value1",
            "field2": 123,
            "field3": True
        },
        "meta": {
            "meta1": "value1",
            "meta2": 456
        }
    }


@pytest.fixture(scope="session")
def sample_pattern() -> Dict[str, Any]:
    """创建示例模式
    
    Returns:
        示例模式
    """
    return {
        "pattern_id": "test-pattern-id",
        "type": "test-pattern-type",
        "timestamp": "2023-01-01T00:00:00Z",
        "source": "test-source",
        "details": {
            "detector": "test-detector",
            "confidence": 0.95
        },
        "contributors": [
            {"field": "field1", "score": 0.7},
            {"field": "field2", "score": 0.3}
        ]
    }