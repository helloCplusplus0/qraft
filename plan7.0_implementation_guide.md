# Qraft7.0 实施指南

本文档提供Qraft7.0 MVP版本的详细实施指南，包括环境设置、开发步骤、测试策略和部署方法。

## 一、技术栈详细说明

### 1. 核心技术栈

| 组件 | 技术选择 | 版本 | 说明 |
| --- | --- | --- | --- |
| **编程语言** | Python | 3.10+ | 主要开发语言，提供良好的生态系统 |
| **异步框架** | asyncio + uvloop | 最新稳定版 | 提供高性能异步I/O |
| **数据处理** | polars | 0.19.0+ | 高性能数据处理库，比pandas更快 |
| **API框架** | FastAPI | 0.100.0+ | 现代、高性能的API框架 |
| **消息总线** | NATS | 2.10.0+ | 轻量级、高性能消息系统 |
| **存储系统** | ClickHouse | 23.8+ | 高性能列式数据库 |
| **模式引擎** | River | 0.15.0+ | 在线机器学习库 |
| **监控系统** | Prometheus + Grafana | 最新稳定版 | 监控和可视化 |
| **容器化** | Docker + Docker Compose | 最新稳定版 | 容器化部署 |

### 2. 依赖库详细清单

```
# 核心依赖
python = "^3.10"
asyncio = "*"
uvloop = "^0.17.0"
polars = "^0.19.0"
pydantic = "^2.4.0"
fastapi = "^0.100.0"
uvicorn = "^0.23.0"

# 消息系统
nats-py = "^2.3.1"

# 数据库
clickhouse-driver = "^0.2.6"
asyncx = "^0.0.3"  # 异步ClickHouse客户端

# 模式引擎
river = "^0.15.0"
scikit-learn = "^1.3.0"  # 用于降维和可视化

# 监控
prometheus-client = "^0.17.0"

# 工具库
pyyaml = "^6.0.1"
loguru = "^0.7.0"
uuid = "^1.30"

# 测试
pytest = "^7.4.0"
pytest-asyncio = "^0.21.1"
```

## 二、项目结构

```
qraft/
├── pyproject.toml           # 项目元数据和依赖
├── README.md               # 项目说明
├── docker-compose.yml      # Docker Compose配置
├── configs/                # 配置文件目录
│   ├── adapters.yaml       # 适配器配置
│   ├── preprocessing.yaml  # 预处理配置
│   ├── detectors.yaml      # 检测器配置
│   └── api.yaml            # API配置
├── qraft/                  # 主代码目录
│   ├── __init__.py
│   ├── adapters/           # 适配器模块
│   │   ├── __init__.py
│   │   ├── base.py         # 基础适配器
│   │   ├── websocket.py    # WebSocket适配器
│   │   ├── rest.py         # REST适配器
│   │   └── file.py         # 文件适配器
│   ├── preprocessing/      # 预处理模块
│   │   ├── __init__.py
│   │   ├── pipeline.py     # 处理管道
│   │   ├── operators.py    # 处理算子
│   │   └── state.py        # 状态管理
│   ├── patterns/           # 模式引擎模块
│   │   ├── __init__.py
│   │   ├── engine.py       # 引擎核心
│   │   ├── detectors.py    # 检测器实现
│   │   └── formatter.py    # 模式格式化
│   ├── storage/            # 存储模块
│   │   ├── __init__.py
│   │   ├── clickhouse.py   # ClickHouse客户端
│   │   └── schema.py       # 表结构定义
│   ├── api/                # API模块
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI应用
│   │   ├── routes.py       # API路由
│   │   └── models.py       # API模型
│   ├── monitoring/         # 监控模块
│   │   ├── __init__.py
│   │   ├── metrics.py      # 指标定义
│   │   └── health.py       # 健康检查
│   └── utils/              # 工具模块
│       ├── __init__.py
│       ├── config.py       # 配置加载
│       └── logging.py      # 日志工具
├── tests/                  # 测试目录
│   ├── __init__.py
│   ├── conftest.py         # 测试配置
│   ├── test_adapters.py    # 适配器测试
│   ├── test_preprocessing.py # 预处理测试
│   └── test_patterns.py    # 模式引擎测试
├── scripts/                # 脚本目录
│   ├── setup.sh            # 环境设置脚本
│   ├── replay.py           # 数据回放脚本
│   └── benchmark.py        # 性能测试脚本
└── ui/                     # 前端目录
    ├── index.html          # 主页
    ├── js/                 # JavaScript文件
    └── css/                # CSS文件
```

## 三、核心组件实现指南

### 1. 适配器框架

适配器框架负责从不同数据源获取数据并转换为标准格式。

**基础适配器实现**：

```python
# qraft/adapters/base.py
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import nats
from pydantic import BaseModel
from loguru import logger

class EventModel(BaseModel):
    event_id: str
    source: str
    type: str
    timestamp: datetime
    payload: Dict[str, Any]
    meta: Dict[str, Any]

class BaseAdapter:
    """基础适配器类，提供通用功能"""
    
    def __init__(self, name: str, config: Dict[str, Any], nats_client):
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
        """发送标准格式事件到NATS"""
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
```

**WebSocket适配器示例**：

```python
# qraft/adapters/websocket.py
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import websockets
from .base import BaseAdapter

class WebSocketAdapter(BaseAdapter):
    """WebSocket适配器，用于连接WebSocket数据源"""
    
    def __init__(self, name: str, config: Dict[str, Any], nats_client):
        super().__init__(name, config, nats_client)
        self.url = config["url"]
        self.reconnect_interval = config.get("reconnect_interval", 5)
        self.parser_name = config["parser"]
        self.parser = self._get_parser(self.parser_name)
        self.batch_size = config.get("batch_size", 1)
        self.batch_interval = config.get("batch_interval_ms", 0) / 1000
        self.batch = []
    
    def _get_parser(self, parser_name: str) -> Callable:
        """获取解析器函数"""
        # 这里可以实现一个解析器注册表
        # 简化起见，这里使用一个示例解析器
        if parser_name == "binance_trade_parser":
            return self._parse_binance_trade
        else:
            raise ValueError(f"Unknown parser: {parser_name}")
    
    def _parse_binance_trade(self, data: Dict[str, Any]) -> tuple:
        """解析Binance交易数据"""
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
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            event_type, payload, timestamp = self.parser(data)
            
            if event_type and payload:
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
    
    async def _batch_timer_loop(self):
        """批处理定时器循环"""
        while self.running:
            await asyncio.sleep(self.batch_interval)
            if self.batch:
                await self._emit_batch()
```

### 2. 预处理管道

预处理管道负责数据清洗、验证和转换。

**管道框架实现**：

```python
# qraft/preprocessing/pipeline.py
from typing import Dict, Any, List, Callable, Optional
import json
import asyncio
import nats
from loguru import logger
from .operators import get_operator

class Pipeline:
    """预处理管道，处理从NATS接收的事件"""
    
    def __init__(self, config: Dict[str, Any], nats_client, clickhouse_client):
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
        """设置操作符列表"""
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
        """处理NATS消息"""
        try:
            # 解析事件
            event = json.loads(msg.data.decode())
            source = event.get("source")
            
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
            await self._store_event(processed_event)
            
            # 发布到模式引擎主题
            await self.nats.publish(
                "processed.events", 
                json.dumps(processed_event).encode()
            )
            
        except Exception as e:
            self.logger.error(f"Event processing error: {e}")
    
    async def _store_event(self, event: Dict[str, Any]):
        """存储事件到ClickHouse"""
        try:
            # 简化实现，实际应该使用批量插入
            await self.clickhouse.insert_event("clean_events", event)
        except Exception as e:
            self.logger.error(f"Event storage error: {e}")
```

**操作符实现示例**：

```python
# qraft/preprocessing/operators.py
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import polars as pl

def get_operator(name: str, config: Dict[str, Any]) -> Optional[Callable]:
    """获取操作符函数"""
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
    """创建架构验证操作符"""
    strict = config.get("strict", True)
    
    async def validate_schema(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """验证事件架构"""
        required_fields = ["event_id", "source", "type", "timestamp", "payload"]
        
        for field in required_fields:
            if field not in event:
                if strict:
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
    """创建添加时间戳操作符"""
    field = config.get("field", "processing_time")
    
    async def add_timestamp(event: Dict[str, Any]) -> Dict[str, Any]:
        """添加处理时间戳"""
        if "meta" not in event:
            event["meta"] = {}
        
        event["meta"][field] = datetime.utcnow().isoformat()
        return event
    
    return add_timestamp

def create_normalize_operator(config: Dict[str, Any]) -> Callable:
    """创建归一化操作符"""
    fields = config.get("fields", [])
    method = config.get("method", "min_max")
    
    # 保存最近的值用于归一化
    state = {field: {"min": None, "max": None, "sum": 0, "count": 0} for field in fields}
    
    async def normalize(event: Dict[str, Any]) -> Dict[str, Any]]:
        """归一化字段"""
        payload = event.get("payload", {})
        
        for field in fields:
            if field in payload and isinstance(payload[field], (int, float)):
                value = payload[field]
                
                # 更新状态
                if state[field]["min"] is None or value < state[field]["min"]:
                    state[field]["min"] = value
                
                if state[field]["max"] is None or value > state[field]["max"]:
                    state[field]["max"] = value
                
                state[field]["sum"] += value
                state[field]["count"] += 1
                
                # 归一化
                if method == "min_max" and state[field]["min"] != state[field]["max"]:
                    normalized = (value - state[field]["min"]) / (state[field]["max"] - state[field]["min"])
                    payload[f"{field}_normalized"] = normalized
                
                elif method == "z_score" and state[field]["count"] > 1:
                    mean = state[field]["sum"] / state[field]["count"]
                    # 简化实现，实际应该计算标准差
                    std = 1.0
                    normalized = (value - mean) / std
                    payload[f"{field}_normalized"] = normalized
        
        event["payload"] = payload
        return event
    
    return normalize
```

### 3. 模式引擎

模式引擎使用River库实现在线学习和模式检测。

**引擎核心实现**：

```python
# qraft/patterns/engine.py
import json
import asyncio
from typing import Dict, Any, List
import nats
from loguru import logger
from .detectors import get_detector

class PatternEngine:
    """模式发现引擎，使用River库检测数据流中的模式"""
    
    def __init__(self, config: Dict[str, Any], nats_client, clickhouse_client):
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
        """处理事件并检测模式"""
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
    
    def _extract_features(self, event: Dict[str, Any], feature_fields: List[str]) -> Dict[str, float]:
        """从事件中提取特征"""
        features = {}
        payload = event.get("payload", {})
        
        for field in feature_fields:
            if field in payload and isinstance(payload[field], (int, float)):
                features[field] = payload[field]
        
        return features if features else None
    
    async def _store_pattern(self, pattern: Dict[str, Any]):
        """存储模式事件到ClickHouse"""
        try:
            await self.clickhouse.insert_event("pattern_events", pattern)
        except Exception as e:
            self.logger.error(f"Pattern storage error: {e}")
```

**检测器实现示例**：

```python
# qraft/patterns/detectors.py
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import river.drift as drift
import river.anomaly as anomaly

def get_detector(name: str, detector_type: str, config: Dict[str, Any]):
    """获取检测器实例"""
    if detector_type == "adwin":
        return DriftDetector(name, config)
    elif detector_type == "half_space_trees":
        return AnomalyDetector(name, config)
    elif detector_type == "cluster_detector":
        return ClusterDetector(name, config)
    return None

class BaseDetector:
    """检测器基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.feature_fields = config.get("fields", [])
    
    async def detect(self, features: Dict[str, float], event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """检测模式，子类必须实现"""
        raise NotImplementedError("Subclasses must implement detect()")
    
    def _create_pattern_event(self, event: Dict[str, Any], pattern_type: str, details: Dict[str, Any], contributors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建模式事件"""
        return {
            "pattern_id": str(uuid.uuid4()),
            "type": pattern_type,
            "timestamp": event.get("timestamp"),
            "source": event.get("source"),
            "details": details,
            "contributors": contributors
        }

class DriftDetector(BaseDetector):
    """概念漂移检测器"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.delta = config.get("delta", 0.002)
        self.grace_period = config.get("grace_period", 100)
        
        # 为每个特征创建一个检测器
        self.detectors = {}
        for field in self.feature_fields:
            self.detectors[field] = drift.ADWIN(delta=self.delta)
        
        # 保存最近的值用于计算变化
        self.recent_values = {field: [] for field in self.feature_fields}
        self.max_recent = 100
    
    async def detect(self, features: Dict[str, float], event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """检测概念漂移"""
        drift_detected = False
        drift_fields = []
        details = {"detector": self.name}
        
        for field, value in features.items():
            if field in self.detectors:
                # 更新检测器
                detector = self.detectors[field]
                old_mean = detector.mean
                drift_detected_on_field = detector.update(value)
                
                # 保存最近的值
                self.recent_values[field].append(value)
                if len(self.recent_values[field]) > self.max_recent:
                    self.recent_values[field].pop(0)
                
                # 如果检测到漂移
                if drift_detected_on_field:
                    drift_detected = True
                    drift_fields.append(field)
                    
                    # 计算变化
                    new_mean = detector.mean
                    if old_mean != 0:
                        change_pct = (new_mean - old_mean) / abs(old_mean) * 100
                    else:
                        change_pct = 0
                    
                    details[f"{field}_prev_mean"] = old_mean
                    details[f"{field}_new_mean"] = new_mean
                    details[f"{field}_change_pct"] = change_pct
        
        if drift_detected:
            # 计算置信度（简化实现）
            confidence = 0.9
            details["confidence"] = confidence
            
            # 创建贡献者列表
            contributors = []
            for field in drift_fields:
                contributors.append({"field": field, "score": 1.0 / len(drift_fields)})
            
            return self._create_pattern_event(
                event, "drift", details, contributors
            )
        
        return None
```

## 四、开发流程

### 1. 环境设置

**开发环境设置**：

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install poetry
poetry install

# 启动开发服务
docker-compose up -d nats clickhouse
```

**Docker Compose配置**：

```yaml
# docker-compose.yml
version: '3'

services:
  nats:
    image: nats:2.10-alpine
    ports:
      - "4222:4222"
      - "8222:8222"
    volumes:
      - ./data/nats:/data
    command: ["-js", "-m", "8222"]

  clickhouse:
    image: clickhouse/clickhouse-server:23.8
    ports:
      - "8123:8123"
      - "9000:9000"
    volumes:
      - ./data/clickhouse:/var/lib/clickhouse
      - ./configs/clickhouse:/etc/clickhouse-server/conf.d
    ulimits:
      nofile:
        soft: 262144
        hard: 262144

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus:/etc/prometheus
      - ./data/prometheus:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./data/grafana:/var/lib/grafana
    depends_on:
      - prometheus
      - clickhouse

  qraft:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/app
    depends_on:
      - nats
      - clickhouse
    ports:
      - "8000:8000"
    command: ["uvicorn", "qraft.api.main:app", "--host", "0.0.0.0", "--reload"]
```

### 2. 数据库初始化

**ClickHouse表结构**：

```sql
-- 原始事件表
CREATE TABLE raw_events (
    event_id String,
    source String,
    type String,
    timestamp DateTime64(3),
    ingest_time DateTime64(3),
    payload String,  -- JSON
    meta String      -- JSON
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (timestamp, source, type, event_id);

-- 处理后事件表
CREATE TABLE clean_events (
    event_id String,
    source String,
    type String,
    timestamp DateTime64(3),
    processing_time DateTime64(3),
    payload String,  -- JSON
    meta String      -- JSON
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (timestamp, source, type, event_id);

-- 模式事件表
CREATE TABLE pattern_events (
    pattern_id String,
    type String,
    timestamp DateTime64(3),
    source String,
    details String,  -- JSON
    contributors String  -- JSON
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (timestamp, source, type, pattern_id);

-- 用户反馈表
CREATE TABLE pattern_feedback (
    feedback_id String,
    pattern_id String,
    timestamp DateTime64(3),
    user_id String,
    rating Int8,  -- -1: 负面, 0: 中性, 1: 正面
    comment String
) ENGINE = MergeTree()
ORDER BY (pattern_id, timestamp);
```

### 3. 测试策略

**单元测试示例**：

```python
# tests/test_adapters.py
import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch
from qraft.adapters.base import BaseAdapter, EventModel
from qraft.adapters.websocket import WebSocketAdapter

@pytest.fixture
def nats_client():
    """模拟NATS客户端"""
    client = MagicMock()
    client.publish = asyncio.coroutine(lambda topic, data: None)
    return client

@pytest.mark.asyncio
async def test_base_adapter_emit_event(nats_client):
    """测试基础适配器的事件发送"""
    adapter = BaseAdapter("test", {}, nats_client)
    
    # 发送测试事件
    await adapter.emit_event("test_event", {"value": 123})
    
    # 验证NATS发布被调用
    nats_client.publish.assert_called_once()
    topic, data = nats_client.publish.call_args[0]
    
    assert topic == "events.test"
    event = json.loads(data.decode())
    assert event["source"] == "test"
    assert event["type"] == "test_event"
    assert event["payload"]["value"] == 123

@pytest.mark.asyncio
async def test_websocket_adapter_parse_message(nats_client):
    """测试WebSocket适配器的消息解析"""
    config = {
        "url": "ws://test.com",
        "parser": "binance_trade_parser"
    }
    adapter = WebSocketAdapter("binance", config, nats_client)
    
    # 模拟Binance消息
    message = json.dumps({
        "e": "trade",
        "s": "BTCUSDT",
        "p": "29876.45",
        "q": "0.125",
        "T": 1630000000123,
        "m": False
    })
    
    # 模拟_process_message方法
    with patch.object(adapter, 'emit_event') as mock_emit:
        await adapter._process_message(message)
        
        # 验证emit_event被调用
        mock_emit.assert_called_once()
        event_type, payload, timestamp = mock_emit.call_args[0]
        
        assert event_type == "trade"
        assert payload["symbol"] == "BTCUSDT"
        assert payload["price"] == 29876.45
        assert payload["quantity"] == 0.125
        assert payload["side"] == "sell"
```

**集成测试示例**：

```python
# tests/test_integration.py
import pytest
import asyncio
import json
import nats
from clickhouse_driver import Client as ClickHouseClient
from qraft.adapters.websocket import WebSocketAdapter
from qraft.preprocessing.pipeline import Pipeline
from qraft.patterns.engine import PatternEngine

@pytest.fixture(scope="module")
async def nats_client():
    """NATS客户端"""
    client = await nats.connect("nats://localhost:4222")
    yield client
    await client.close()

@pytest.fixture(scope="module")
def clickhouse_client():
    """ClickHouse客户端"""
    client = ClickHouseClient(host='localhost')
    return client

@pytest.mark.asyncio
async def test_end_to_end_flow(nats_client, clickhouse_client):
    """端到端流程测试"""
    # 清理测试数据
    clickhouse_client.execute("TRUNCATE TABLE raw_events")
    clickhouse_client.execute("TRUNCATE TABLE clean_events")
    clickhouse_client.execute("TRUNCATE TABLE pattern_events")
    
    # 创建测试配置
    adapter_config = {
        "url": "ws://echo.websocket.org",
        "parser": "test_parser"
    }
    
    pipeline_config = {
        "default": [
            {"name": "validate_schema", "config": {}},
            {"name": "add_timestamp", "config": {}}
        ]
    }
    
    detector_config = {
        "detectors": [
            {
                "name": "test_detector",
                "type": "adwin",
                "source": "test",
                "config": {
                    "fields": ["value"],
                    "delta": 0.01
                }
            }
        ]
    }
    
    # 初始化组件
    adapter = WebSocketAdapter("test", adapter_config, nats_client)
    pipeline = Pipeline(pipeline_config, nats_client, clickhouse_client)
    engine = PatternEngine(detector_config, nats_client, clickhouse_client)
    
    # 启动组件
    await pipeline.start()
    await engine.start()
    
    # 模拟发送事件
    for i in range(100):
        value = 100 if i < 50 else 200  # 制造漂移
        await adapter.emit_event("test_event", {"value": value})
        await asyncio.sleep(0.01)
    
    # 等待处理完成
    await asyncio.sleep(1)
    
    # 验证结果
    raw_count = clickhouse_client.execute("SELECT count() FROM raw_events")
    clean_count = clickhouse_client.execute("SELECT count() FROM clean_events")
    pattern_count = clickhouse_client.execute("SELECT count() FROM pattern_events")
    
    assert raw_count[0][0] > 0
    assert clean_count[0][0] > 0
    assert pattern_count[0][0] > 0  # 应该检测到漂移
```

### 4. 部署指南

**生产环境部署**：

1. **准备服务器**：
   - 推荐配置：8+ CPU核心，16GB+ RAM，100GB+ SSD
   - 安装Docker和Docker Compose

2. **克隆代码并配置**：
   ```bash
   git clone https://github.com/your-org/qraft.git
   cd qraft
   
   # 配置生产环境
   cp configs/adapters.yaml.example configs/adapters.yaml
   cp configs/preprocessing.yaml.example configs/preprocessing.yaml
   cp configs/detectors.yaml.example configs/detectors.yaml
   
   # 编辑配置文件
   nano configs/adapters.yaml
   nano configs/preprocessing.yaml
   nano configs/detectors.yaml
   ```

3. **构建和启动服务**：
   ```bash
   # 构建Docker镜像
   docker-compose build
   
   # 启动服务
   docker-compose up -d
   ```

4. **初始化数据库**：
   ```bash
   # 运行初始化脚本
   docker-compose exec qraft python -m scripts.init_db
   ```

5. **验证部署**：
   - 访问API: http://server-ip:8000/docs
   - 访问Grafana: http://server-ip:3000
   - 检查日志: `docker-compose logs -f qraft`

## 五、性能优化建议

### 1. 数据处理优化

1. **批处理**：
   - 实现批量事件处理而非逐条处理
   - 使用polars的并行处理能力

2. **内存管理**：
   - 使用滑动窗口而非无限增长的数据结构
   - 定期清理过期状态
   - 实现背压机制防止内存溢出

### 2. 存储优化

1. **ClickHouse优化**：
   - 使用批量插入而非单条插入
   - 优化分区策略，按日期分区
   - 设置合理的TTL策略

2. **查询优化**：
   - 创建物化视图加速常用查询
   - 使用预聚合表减少查询压力

### 3. 通信优化

1. **NATS优化**：
   - 使用JetStream持久化关键消息
   - 实现消息批处理减少网络开销

2. **API优化**：
   - 实现缓存减少重复查询
   - 分页加载大结果集

## 六、扩展路径

### 1. 功能扩展

1. **更多检测器**：
   - 集成CapyMOA提供更多高性能算法
   - 添加深度学习模型支持

2. **高级可视化**：
   - 实现交互式时间线视图
   - 添加模式关联分析

3. **告警系统**：
   - 实现基于规则的告警
   - 支持多渠道通知（邮件、Slack等）

### 2. 架构扩展

1. **水平扩展**：
   - 实现适配器和处理器的多实例部署
   - 使用Kubernetes进行编排

2. **消息系统升级**：
   - 从NATS升级到Redpanda/Kafka
   - 实现更复杂的流处理拓扑

3. **LLM集成**：
   - 添加模式解释层
   - 实现自然语言查询接口

## 七、总结

本实施指南提供了Qraft7.0 MVP版本的详细开发路线图，包括核心组件实现、开发流程、测试策略和部署方法。通过遵循这些指南，开发团队可以在7周内交付一个功能完整、性能优异的数据流模式探索平台。

系统采用轻量级技术栈，确保资源占用最小化，同时保持高性能和可扩展性。模块化设计使每个组件都可以独立升级或替换，为未来扩展提供灵活性。

通过专注于核心功能和精简实现，Qraft7.0 MVP能够快速交付并提供实际价值，同时为后续迭代奠定坚实基础。