# 任务1.2：策略协议v1设计与实现

## 📋 任务概述

### 目标
基于`plan6.0.md`的统一策略协议设计，实现策略协议v1的JSONSchema规范、算子注册表机制、校验器与安全约束。

### 预计耗时
3-4天

### 交付物
- qraft/schemas/strategy_v1.json
- qraft/validators/strategy_validator.py
- qraft/operators/registry.py
- 策略协议文档与示例

---

## 🎯 功能需求分析

### 1. 策略协议v1 JSONSchema规范
基于`plan6.0.md`中的策略输出Schema，定义标准化的策略描述格式：

**必填字段**：
- `name`: 策略名称 (string)
- `universe`: 标的证券池 (array of strings/filters)
- `signals`: 信号表达式列表 (array of signal objects)
- `positioning`: 仓位管理配置 (object)
- `risk_constraints`: 风险约束条件 (object)
- `exec`: 执行参数 (object)
- `meta`: 元数据信息 (object)

**信号对象结构**：
```json
{
  "expr": "表达式字符串",
  "weight": "权重值",
  "description": "描述（可选）"
}
```

### 2. 算子注册表与白名单机制
实现受限的算子生态：

**技术指标算子**（基于TA-Lib/pandas-ta）：
- 趋势类：MA, EMA, SMA, MACD, ADX
- 振荡类：RSI, STOCH, CCI, Williams %R
- 成交量：OBV, AD, CHAIKIN
- 波动率：ATR, BBANDS, NATR

**统计算子**：
- 滚动窗口：rolling_mean, rolling_std, rolling_min, rolling_max
- 分位数：quantile, rank, pct_rank
- 横截面：cross_sectional_rank, neutralize

**约束条件**：
- 禁止未来函数（look-ahead bias）
- 强制左闭窗口（避免数据泄漏）
- 支持滞后参数验证

### 3. 静态检查与校验规则

**JSONSchema校验**：
- 结构完整性校验
- 数据类型验证
- 必填字段检查
- 值域范围校验

**静态安全检查**：
- 算子白名单验证
- 表达式语法检查
- 时间窗口合规性
- 参数有效性验证

**能力协商框架**：
- 支持的算子清单查询
- 参数约束获取
- 兼容性检查接口

---

## 🏗️ 技术设计

### 1. 目录结构
```
qraft/
├── schemas/
│   ├── __init__.py
│   └── strategy_v1.json          # JSONSchema定义
├── operators/
│   ├── __init__.py
│   └── registry.py               # 算子注册表
├── validators/
│   ├── __init__.py
│   └── strategy_validator.py     # 策略校验器
└── ...
```

### 2. 核心接口设计

#### OperatorRegistry类
```python
class OperatorRegistry:
    def register_operator(self, name: str, func: callable, constraints: dict)
    def get_operator(self, name: str) -> OperatorInfo
    def list_operators(self) -> List[str]
    def validate_expression(self, expr: str) -> ValidationResult
```

#### StrategyValidator类
```python
class StrategyValidator:
    def validate_schema(self, strategy: dict) -> ValidationResult
    def validate_expression_safety(self, expr: str) -> ValidationResult
    def validate_time_windows(self, strategy: dict) -> ValidationResult
    def full_validate(self, strategy: dict) -> ValidationResult
```

### 3. 依赖管理
新增依赖到requirements-stable.txt：
- jsonschema==4.21.1
- pydantic==2.5.3（用于类型验证）

---

## ✅ 实施结果与事后总结

### 1) 本次交付内容
- 已落地 JSONSchema v1、算子注册表与最小校验器：
  - 文件：`qraft/schemas/strategy_v1.json`、`qraft/operators/registry.py`、`qraft/validators/strategy_validator.py`
  - 单元测试：`tests/unit/test_strategy_validator.py` 覆盖有效/无效用例与错误信息路径
- 新增最小 CLI：
  - 校验：`qraft validate path/to/strategy.json`
  - 能力协商（简洁）：`qraft ops`（列出注册算子与参数位数 arity）
  - 入口点：`pyproject.toml` 中 `[project.scripts] qraft = "qraft.cli:main"`
  - Makefile 集成：`make install`（安装包启用 CLI）、`make validate FILE=...`（调用校验）
- 质量门结果：
  - 格式化与静态检查：black/isort/flake8 全部通过（Makefile 对 flake8 统一了行宽与忽略项）
  - 类型检查：mypy 通过（新增 CLI 代码已检查）
  - 覆盖率：90%+（>= 80% 阈值），新增 `tests/unit/test_cli.py` 覆盖 `validate` 与 `ops`

### 2) 验收结果对照
- 功能验收
  - [x] JSONSchema 定义最小必填字段与基本结构（name/universe/signals 等）
  - [x] 白名单机制有效拦截未知算子（仅允许注册表内算子）
  - [x] 静态检查：基础表达式语法限制 + 窗口参数 ≥ 1
  - [x] 有效策略通过，常见无效策略被拒并返回明确错误信息
  - [x] 能力协商/参数约束查询（最小）：`qraft ops` 列出算子与 arity
  - [ ] 算子注册表 20+ 常用指标（当前为最小集 9 个，计划逐步扩充）
- 质量门槛
  - [x] 代码覆盖率 ≥ 80%
  - [x] 通过 flake8/black/isort 检查
  - [x] 通过 mypy 类型检查
  - [x] 所有单元测试通过
- 性能基准（本阶段未专项评测，MVP 规模下运行良好）
  - [ ] 单策略校验 < 100ms（后续基准化）
  - [ ] 并发校验能力评测

### 3) 实现细节与取舍
- 能力协商子命令选择简洁命名 `ops`，避免冗长指令（例如 `list-operators`），输出控制在一行一项：`- NAME  arity=N`，利于命令行过滤与人读。
- 暂仅展示稳定可得的元数据（名称与参数位数 arity），不引入假设的约束字段，避免过度设计；后续若注册表补充参数域/默认值等，再增量展示。
- 其他保持与 v1 一致的最小实现，遵循“先落地，后完善”。

### 4) 已知限制与风险
- `ops` 当前仅展示 arity；更丰富的参数约束需要注册表扩展 `constraints` 元数据并补充测试后再开放。
- 算子白名单仍为最小集（SMA/EMA/RSI/ATR/MACD/BBANDS/ROLL_MEAN/ROLL_STD/RANK）。

### 5) 下一步计划（增量路线）
1. 在注册表中逐步补全 `constraints` 结构（参数类型/范围/默认值），并在 `qraft ops` 中以可选 `--json` 输出更详细的能力描述。
2. 扩充算子白名单至 20+ 并补充单测。
3. 评估是否提供 `qraft check-expr 'OP(...)'` 快速检查表达式合法性的子命令（待需求确认）。

### 6) 示例（文档用）
- CLI 用法：
```
make install
qraft validate path/to/strategy.json
qraft ops
```

---

以上变更已提交并通过质量门校验，可作为 Qraft 6.0 策略协议 v1 的最小可用实现基线。