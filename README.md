# Qraft7.0

## 数据流驱动自动化模式探索平台

Qraft7.0是一个以**实时/近实时数据流**为输入、对多源数据做**统一预处理 + 自动化模式发现**，并以**结构化 + 可视化**方式呈现的轻量级平台。

## 特性

- **轻量至上**：选择轻量级组件，避免过度设计，确保系统资源占用最小化
- **性能优先**：关键路径使用高性能组件，确保数据处理低延迟
- **模块化设计**：每层职责单一，接口清晰，便于替换或扩展
- **配置驱动**：通过配置文件管理数据源与处理逻辑，避免代码修改
- **可观测性**：每个环节可监控、可调试，确保系统透明
- **工程防护**：对外部依赖做版本锁定与适配层隔离，确保系统稳定性

## 技术栈

| 层级 | 技术选择 | 选择理由 |
| --- | --- | --- |
| **消息总线** | **NATS** | 极轻量(单二进制)、低延迟、简单部署、资源占用小 |
| **数据处理** | **Python + asyncio + polars** | asyncio提供异步非阻塞处理能力，polars提供高性能数据处理 |
| **模式引擎** | **River** | 纯Python实现、API稳定、文档完善、维护活跃 |
| **存储层** | **ClickHouse** | 列式存储高效、查询性能优异、资源占用可控 |
| **监控** | **Prometheus + Grafana** | 轻量级监控栈，部署简单，社区支持好 |
| **可视化** | **FastAPI + 轻量级前端** | 提供最小可用的API与前端界面 |

## 快速开始

### 前置条件

- Python 3.10+
- Docker & Docker Compose
- Poetry

### 安装

1. 克隆仓库

```bash
git clone https://github.com/your-org/qraft.git
cd qraft
```

2. 安装依赖

```bash
poetry install
```

3. 启动服务

```bash
docker-compose up -d
```

4. 运行应用

```bash
poetry run uvicorn qraft.api.main:app --reload
```

5. 访问API文档

打开浏览器访问 http://localhost:8000/docs

## 项目结构

```
qraft/
├── configs/                # 配置文件目录
├── qraft/                  # 主代码目录
│   ├── adapters/           # 适配器模块
│   ├── preprocessing/      # 预处理模块
│   ├── patterns/           # 模式引擎模块
│   ├── storage/            # 存储模块
│   ├── api/                # API模块
│   ├── monitoring/         # 监控模块
│   └── utils/              # 工具模块
├── tests/                  # 测试目录
├── scripts/                # 脚本目录
└── ui/                     # 前端目录
```

## 贡献

欢迎贡献代码，请参阅[贡献指南](CONTRIBUTING.md)。

## 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。