# 任务1.1：项目初始化与环境搭建 - 设计文档

## 1. 事前设计概述

### 1.1 任务目标
根据 Qraft 6.0 设计蓝图，建立项目基础架构和开发环境，实现：
- 创建符合"分层解耦"原则的 mono-repo 项目结构
- 建立多 Python 版本支持（3.10/3.11）的开发环境
- 配置双通道（stable/candidate）依赖管理体系
- 搭建基础 CI/CD 流水线确保代码质量
- 提供容器化部署和开发环境快速启动能力

### 1.2 设计约束
- **轻量化原则**：优先使用成熟开源组件，避免过度设计
- **算法优先原则**：为后续算法模块和LLM增强层建立清晰接口
- **分层解耦原则**：确保数据层、特征层、策略层、执行层的独立性
- **可复现原则**：所有环境配置和依赖版本化管理

### 1.3 预期交付物
- 完整的 mono-repo 项目结构
- requirements-stable.txt, requirements-candidate.txt 
- constraints/3.10.txt, constraints/3.11.txt
- Dockerfile 与 docker-compose.yml
- .github/workflows/ 基础 CI 配置
- Makefile 与环境启动脚本
- 项目 README 与开发环境文档

---

## 2. 项目架构设计

### 2.1 目录结构设计（mono-repo 布局）

```
Qraft/
├── README.md                    # 项目说明
├── LICENSE                      # 许可证
├── Makefile                     # 开发环境管理
├── docker-compose.yml           # 服务编排
├── pyproject.toml              # Python 项目配置
│
├── requirements/                # 依赖管理
│   ├── requirements-stable.txt
│   ├── requirements-candidate.txt
│   └── constraints/
│       ├── 3.10.txt
│       └── 3.11.txt
│
├── docker/                      # 容器化配置
│   ├── Dockerfile.base
│   ├── Dockerfile.dev
│   └── Dockerfile.prod
│
├── scripts/                     # 环境启动脚本
│   ├── setup.sh
│   ├── dev-env.sh
│   └── test-env.sh
│
├── qraft/                       # 核心代码（分层设计）
│   ├── __init__.py
│   ├── data/                    # 数据层
│   │   ├── __init__.py
│   │   ├── snapshot.py
│   │   ├── calendar.py
│   │   └── importers/
│   ├── features/                # 特征层
│   │   ├── __init__.py
│   │   ├── indicators.py
│   │   └── pipeline.py
│   ├── schemas/                 # 协议与规范
│   │   ├── __init__.py
│   │   └── strategy_v1.json
│   ├── validators/              # 校验器
│   │   ├── __init__.py
│   │   └── strategy_validator.py
│   ├── engines/                 # 执行引擎
│   │   ├── __init__.py
│   │   └── adapters/
│   └── utils/                   # 公共工具
│       ├── __init__.py
│       └── logging.py
│
├── tests/                       # 测试代码
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/                        # 文档
│   ├── architecture.md
│   ├── api/
│   └── examples/
│
├── artifacts/                   # 构建产物
│   ├── data/
│   │   └── sample/
│   ├── models/
│   └── reports/
│
└── .github/                     # CI/CD 配置
    └── workflows/
        ├── ci.yml
        └── cd.yml
```

### 2.2 技术栈选择

#### 核心技术栈
- **Python 版本**：3.10/3.11（根据 plan6.0.md 要求）
- **依赖管理**：pip-tools（constraints 文件支持）
- **构建工具**：setuptools + pyproject.toml
- **测试框架**：pytest + pytest-cov
- **代码质量**：black, isort, flake8, mypy

#### 引入的开源组件（基于 dev_tools_fix.md 选择）
- **数据存储**：ClickHouse（高性能分析数据库）
- **对象存储**：MinIO（分布式对象存储）
- **数据处理**：Polars（高性能数据处理引擎）
- **容器化**：Docker + docker-compose

---

## 3. 详细实施步骤

### 3.1 阶段一：基础项目结构创建

#### 步骤 1：创建 mono-repo 目录结构
- 创建根据设计的完整目录树
- 初始化各模块的 `__init__.py` 文件
- 建立模块间的基础导入关系

#### 步骤 2：配置 Python 项目管理
- 创建 `pyproject.toml` 配置文件
- 定义项目元数据、依赖关系和构建配置
- 配置开发工具（black, isort, flake8, mypy）的规则

### 3.2 阶段二：多版本 Python 支持

#### 步骤 1：建立 constraints 文件体系
- 创建 `requirements/constraints/3.10.txt`
- 创建 `requirements/constraints/3.11.txt`
- 定义核心依赖的版本约束

#### 步骤 2：双通道依赖管理
- **stable 通道**：经过验证的稳定版本依赖
- **candidate 通道**：包含最新特性的候选版本
- 使用 pip-tools 生成和管理依赖锁定文件

### 3.3 阶段三：容器化与环境配置

#### 步骤 1：Docker 镜像构建
- **Dockerfile.base**：基础运行环境
- **Dockerfile.dev**：开发环境（包含调试工具）
- **Dockerfile.prod**：生产环境（精简镜像）

#### 步骤 2：docker-compose 服务编排
- 配置开发服务：应用、数据库、存储
- 配置环境变量和数据卷映射
- 建立服务间网络通信

### 3.4 阶段四：CI/CD 流水线配置

#### 步骤 1：基础 CI 流水线
- 代码质量检查（linting）
- 单元测试执行
- 测试覆盖率报告
- 多 Python 版本矩阵测试

#### 步骤 2：CD 流水线准备
- 镜像构建与推送
- 依赖安全扫描
- 文档生成与部署

### 3.5 阶段五：开发环境快速启动

#### 步骤 1：Makefile 命令封装
- `make setup`：环境初始化
- `make dev`：启动开发环境
- `make test`：运行测试套件
- `make lint`：代码质量检查
- `make clean`：清理构建产物

#### 步骤 2：脚本工具
- `scripts/setup.sh`：一键环境搭建
- `scripts/dev-env.sh`：开发环境启动
- `scripts/test-env.sh`：测试环境管理

---

## 4. 质量控制与验收标准

### 4.1 功能验收标准
- [ ] 项目结构符合分层设计原则
- [ ] 支持 Python 3.10 和 3.11 版本
- [ ] 双通道依赖管理正常工作
- [ ] Docker 容器构建和运行成功
- [ ] CI/CD 流水线执行通过
- [ ] 开发环境可一键启动

### 4.2 质量门槛
- [ ] 代码覆盖率 ≥ 80%
- [ ] 所有 linting 检查通过
- [ ] 类型检查（mypy）无错误
- [ ] 依赖安全扫描无高危漏洞
- [ ] 构建时间 < 5 分钟
- [ ] 容器镜像大小 < 1GB

### 4.3 性能基准
- [ ] 环境启动时间 < 30 秒
- [ ] 测试套件执行时间 < 2 分钟
- [ ] 镜像构建时间 < 3 分钟

---

## 5. 风险识别与缓解

### 5.1 技术风险
- **风险**：Python 版本兼容性问题
  - **缓解**：使用 tox 进行多版本测试，建立兼容性检查机制

- **风险**：依赖冲突
  - **缓解**：使用 constraints 文件锁定版本，定期更新依赖

- **风险**：容器镜像过大
  - **缓解**：使用多阶段构建，优化基础镜像选择

### 5.2 开发风险
- **风险**：开发环境配置复杂
  - **缓解**：提供自动化脚本和详细文档

- **风险**：CI/CD 配置错误
  - **缓解**：使用模板和最佳实践，逐步验证

---

## 6. 预期产出与时间计划

### 6.1 里程碑规划
- **Day 1**：完成项目结构设计与创建
- **Day 2**：配置 Python 环境和依赖管理
- **Day 3**：完成容器化配置和 CI/CD 设置

### 6.2 关键交付物
1. **项目骨架结构**：完整的 mono-repo 布局
2. **环境配置文件**：requirements, constraints, Docker 配置
3. **自动化脚本**：Makefile 和 shell 脚本
4. **CI/CD 流水线**：GitHub Actions 配置
5. **文档**：README 和开发指南

---

## 7. 后续任务接口

### 7.1 为任务 1.2 准备的接口
- `qraft/schemas/` 目录已创建，准备策略协议定义
- `qraft/validators/` 目录已创建，准备校验器实现

### 7.2 为任务 1.3 准备的接口
- `qraft/data/` 目录已创建，准备数据层实现
- `artifacts/data/sample/` 目录已创建，准备样例数据

### 7.3 扩展性考虑
- 模块化设计支持后续功能扩展
- 统一的配置管理支持环境适配
- 标准化的测试框架支持质量保证

---

*本文档将在任务执行过程中实时更新，记录实际实施情况与经验总结。*