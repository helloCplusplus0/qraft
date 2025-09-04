import pytest
import asyncio
from unittest.mock import MagicMock, patch
from typing import Dict, Any

import nats
import json

from qraft.patterns.engine import PatternEngine
from qraft.patterns.detectors import (
    get_detector, BaseDetector, DriftDetector, AnomalyDetector, ClusterDetector
)
from qraft.patterns.formatter import PatternFormatter


@pytest.mark.asyncio
async def test_pattern_engine_init():
    """测试模式引擎初始化"""
    # 创建模拟客户端
    mock_nats = MagicMock()
    mock_clickhouse = MagicMock()
    
    # 创建引擎配置
    config = {
        "detectors": [
            {
                "name": "test-detector",
                "type": "adwin",
                "source": "test-source",
                "config": {
                    "delta": 0.002,
                    "fields": ["price"]
                }
            }
        ]
    }
    
    # 创建引擎
    with patch("qraft.patterns.detectors.get_detector") as mock_get_detector:
        mock_detector = MagicMock()
        mock_detector.feature_fields = ["price"]
        mock_get_detector.return_value = mock_detector
        
        engine = PatternEngine(config, mock_nats, mock_clickhouse)
        
        # 验证属性
        assert "test-source" in engine.detectors
        assert len(engine.detectors["test-source"]) == 1
        assert engine.detectors["test-source"][0]["name"] == "test-detector"
        assert engine.detectors["test-source"][0]["type"] == "adwin"


def test_base_detector_init():
    """测试基础检测器初始化"""
    # 创建检测器
    detector = BaseDetector("test-detector", {"fields": ["field1", "field2"]})
    
    # 验证属性
    assert detector.name == "test-detector"
    assert detector.feature_fields == ["field1", "field2"]


def test_drift_detector_init():
    """测试漂移检测器初始化"""
    # 创建检测器
    detector = DriftDetector("test-drift", {
        "delta": 0.001,
        "grace_period": 200,
        "fields": ["price", "volume"]
    })
    
    # 验证属性
    assert detector.name == "test-drift"
    assert detector.delta == 0.001
    assert detector.grace_period == 200
    assert detector.feature_fields == ["price", "volume"]
    assert "price" in detector.detectors
    assert "volume" in detector.detectors


def test_anomaly_detector_init():
    """测试异常检测器初始化"""
    # 创建检测器
    detector = AnomalyDetector("test-anomaly", {
        "n_trees": 15,
        "height": 10,
        "window_size": 200,
        "threshold": 0.98,
        "fields": ["price", "volume"]
    })
    
    # 验证属性
    assert detector.name == "test-anomaly"
    assert detector.n_trees == 15
    assert detector.height == 10
    assert detector.window_size == 200
    assert detector.threshold == 0.98
    assert detector.feature_fields == ["price", "volume"]


def test_cluster_detector_init():
    """测试聚类检测器初始化"""
    # 创建检测器
    detector = ClusterDetector("test-cluster", {
        "n_clusters": 5,
        "window_size": 100,
        "threshold": 0.4,
        "fields": ["feature1", "feature2"]
    })
    
    # 验证属性
    assert detector.name == "test-cluster"
    assert detector.n_clusters == 5
    assert detector.window_size == 100
    assert detector.threshold == 0.4
    assert detector.feature_fields == ["feature1", "feature2"]


def test_pattern_formatter():
    """测试模式格式化器"""
    # 创建格式化器
    formatter = PatternFormatter()
    
    # 创建模式
    pattern = {
        "pattern_id": "test-pattern-id",
        "type": "drift",
        "timestamp": "2023-01-01T00:00:00Z",
        "source": "test-source",
        "details": {
            "detector": "test-detector",
            "confidence": 0.95,
            "price_prev_mean": 100.0,
            "price_new_mean": 110.0,
            "price_change_pct": 10.0
        },
        "contributors": [
            {"field": "price", "score": 1.0}
        ]
    }
    
    # 格式化模式
    formatted = formatter.format_pattern(pattern)
    
    # 验证结果
    assert "explanation" in formatted
    assert isinstance(formatted["explanation"], str)
    assert "检测到概念漂移" in formatted["explanation"]
    assert "price" in formatted["explanation"]
    assert "10.0%" in formatted["explanation"]