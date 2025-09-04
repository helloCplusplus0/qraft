# Task 2.2: Nautilus Trader精确回测集成

## 设计概览

### 目标与动机
基于现有的快速回测（vectorbt）设施，集成 Nautilus Trader 作为精确回测引擎，实现高保真度的交易模拟，包括订单生命周期、市场微观结构和真实的成交机制。遵循 Qraft 6.0「薄适配 + 原生 API」设计原则，强制依赖就绪，不做任何回退或桥接模拟。

### 核心差异化定位

| 维度 | VectorBT适配器 | Nautilus适配器 |
|------|---------------|----------------|
| 精度 | 快速近似，基于信号直接转换为持仓 | 精确模拟，逐个订单处理与撮合 |
| 数据支持 | Bar/OHLC 数据 | 支持 Tick/Order Book/Bar 多层次数据 |
| 订单类型 | 简化市价单模拟 | 支持限价单、止损单、OCO 等高级订单 |
| 成交机制 | 即时成交假设 | 真实撮合模型（Queue Position、Slippage） |
| 成本模型 | 简单费率 | 精细化 Bid-Ask Spread、Impact、延迟等 |
| 依赖策略 | 必须安装 vectorbt，否则报错退出 | 必须安装 nautilus-trader，否则报错退出 |
| 应用场景 | 策略快速验证、参数粗扫 | 实盘前最终验证、高频策略、复杂订单逻辑 |

注：本任务仅描述 Nautilus 精确回测通道；快速通道由 <mcfile name="vectorbt_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/vectorbt_adapter.py"></mcfile> 提供，二者在报表与对齐层保持一致。

## 技术架构设计

### 1. 核心适配器设计
- 已实现 <mcfile name="nautilus_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/nautilus_adapter.py"></mcfile>，遵循「薄适配 + 原生 API」原则，接口与 VectorBT 适配器对齐，返回同构的 <mcsymbol name="BacktestResult" filename="nautilus_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/nautilus_adapter.py" startline="9" type="class"></mcsymbol>。
- 实现包含：强制依赖检查、导入保护、start/end 切片、信号/价格对齐与单列自动对齐、仅使用原生 Nautilus 引擎。

### 2. 市场环境与成本/撮合配置
- 通过 `engine_config` 注入拍卖所/交易日历、费用与撮合参数；适配器内不重造模型，直接对接 Nautilus 组件。

### 3. 强制依赖检查
- 在 `engine` 或 `auto` 模式下，必须可导入 `nautilus-trader`，否则直接抛出 RuntimeError。
- 不提供任何 MVP/桥接回退路径；失败即显式报错，便于定位与修复。

## 接口集成

### CLI 集成
- 新增 `precisebt` 子命令，入口在 <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile>，复用 `quickbacktest` 的信号构建流程，调用 <mcsymbol name="NautilusAdapter" filename="nautilus_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/nautilus_adapter.py" startline="14" type="class"></mcsymbol> 执行回测。
- 强制注入 `engine_config` 参数，确保使用原生 Nautilus 引擎。
- 提供 `--strict` 标志：在引擎初始化/执行失败时不降级，直接抛错（与配置键 `strict_engine`/`strict` 等价）。

#### 使用示例
- CLI：`qraft precisebt --strategy strat.json --prices prices.csv --strict`
- 配置文件示例：<mcfile name="sample_engine_config_strict.json" path="/home/dell/Projects/Qraft/sample_engine_config_strict.json"></mcfile>

### Python API
- 与 VectorBT 适配器一致的 `run` 接口，支持 `price_df, signal, start, end, engine_config`。
- 通过 `engine_config["mode"]` 控制执行路径（`engine`/`auto`），并严格遵循依赖约束。

## 测试与覆盖率
- 单元测试：<mcfile name="test_nautilus_adapter.py" path="/home/dell/Projects/Qraft/tests/unit/test_nautilus_adapter.py"></mcfile> 覆盖导入保护、Series→DataFrame 转换、列与索引对齐、时间切片、依赖检查与失败分支等。

## 验收结论
- 与 VectorBT 适配器保持相同的接口签名：已满足。
- 支持基础的 Bar 数据精确回测：已满足（仅原生 Nautilus 引擎）。
- 可配置成本与撮合：通过 `engine_config` 与原生 Nautilus 组件对接。
- CLI 子命令可用：已集成，并提供严格模式与友好错误提示。
- 强制依赖约束：`engine`/`auto` 模式缺失 `nautilus-trader` 时直接报错，不做任何回退。

## Qraft 6.0 设计原则落地
- 薄适配 + 原生 API：适配层最小化，仅做数据规范化与注入，引擎能力完全复用。
- 强制依赖就绪：明确硬边界，去除回退与桥接代码，降低维护成本与歧义。
- 统一报表与对齐：与快速通道共享一致性对齐与指标报表，保证可比性与可审计。

## 后续计划
- 持续完善与 Nautilus BacktestEngine 的对接细节（订单生命周期、部分成交、滑点/拒单等情境）。
- 版本锁定与环境验证（依赖检查、版本白名单）。

## 结论
- 按照 Qraft 6.0「薄适配 + 原生 API + 强制依赖」原则完成精确回测通道的对接。
- 放弃传统的“MVP/桥接回退”，生产级路径仅保留：vectorbt 快速回测 + Nautilus 精确回测的双通道策略。