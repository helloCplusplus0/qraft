# Task 2.2.1: Nautilus Trader 引擎接入设计

## 概述

目标：在具备 nautilus-trader 环境时，将 `NautilusAdapter` 从占位实现改造为真正接入 Nautilus Trader `BacktestEngine`、配置 Venue 和撮合/费用模型，替换任何简化逻辑。遵循 Qraft 6.0 的“薄适配+原生API、强制依赖就绪、不做回退”原则。

## 现状分析

当前 `NautilusAdapter` 实现（位于 `qraft/engines/nautilus_adapter.py`）：
- 已实现导入保护 + 数据对齐 + 时间切片 + 依赖检查
- `engine`/`auto` 模式严格要求 `nautilus-trader` 可用；缺失则抛出 `RuntimeError`
- 与 `VectorbtAdapter` 保持接口一致

## 设计目标

1. 真正使用 Nautilus Trader 的 BacktestEngine：替换任何占位逻辑
2. 配置 Venue 和撮合/费用模型：基于 `QraftVenue`、`QraftFillModel`、`QraftFeeModel`
3. 保持接口兼容性：不破坏与 `VectorbtAdapter` 的接口一致性
4. 确保测试通过：所有现有单测必须继续通过
5. 强制依赖就绪：不引入任何回退/降级策略

## 技术方案

### 1. Nautilus Trader 组件接入

参考官方组件：

```python
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.backtest.node import BacktestNode, BacktestVenueConfig
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.wranglers import QuoteTickDataWrangler
```

### 2. 数据转换流程

```
价格 DataFrame → QuoteTick 数据 → ParquetDataCatalog → BacktestEngine
信号 DataFrame → Strategy 仓位目标 → 订单生成
```

### 3. 策略适配

创建轻量级策略类，接收 Qraft 信号并转换为 Nautilus 订单：

```python
class QraftSignalStrategy(Strategy):
    def __init__(self, signal_df: pd.DataFrame):
        self.signal_df = signal_df
    
    def on_bar(self, bar: Bar):
        # 根据当前时间从 signal_df 读取仓位目标
        # 生成相应的订单（MarketOrder）
```

### 4. 配置映射

将 Qraft 配置模型转换为 Nautilus 配置：

```python
def create_venue_config(qraft_venue: QraftVenue, fill_model: QraftFillModel, fee_model: QraftFeeModel) -> BacktestVenueConfig:
    return BacktestVenueConfig(
        name=qraft_venue.name,
        account_type=AccountType.CASH,
        base_currency=qraft_venue.base_currency,
        # TODO: 映射 fill/fee 模型
    )
```

### 5. 执行引擎配置

```python
engine_config = BacktestEngineConfig(
    trader_id=TraderId("QRAFT-001"),
    cache_database_flush=False,
)
```

## 实现步骤

- 数据适配器：创建 QuoteTick、构建临时 ParquetDataCatalog
- 策略适配器：`QraftSignalStrategy` 将信号映射为订单
- 配置生成器：将 Qraft 配置转换为 Nautilus 配置
- 引擎集成：替换 `run()` 中的占位逻辑，返回标准化结果
- 错误处理：保留导入保护，缺失依赖时直接抛错；不做回退

## 接口兼容性

确保以下接口保持不变：
- `NautilusAdapter.__init__(init_cash: float = 1_000_000.0)`
- `NautilusAdapter.run(price_df, signal, start, end, engine_config) -> BacktestResult`
- `BacktestResult.equity_curve: pd.Series`
- `BacktestResult.stats: Dict[str, float]`

## 测试策略

1. 现有单测必须通过：
   - 导入守卫/依赖缺失错误
   - Series 到 DataFrame 转换、单列自动对齐
   - 时间切片与无重叠检查
2. 新增单测覆盖：
   - BacktestEngine 配置正确性
   - 数据转换准确性
   - 多资产信号处理
   - 配置模型映射

## 风险与缓解

- 性能：Nautilus 初始化较慢 → 采用内存模式，必要时缓存配置对象
- 兼容性：Nautilus 版本差异 → 锁定版本并加版本检查
- 精度：数值差异 → 设置合理测试容忍度

## 验收标准

- 所有现有单测通过
- `precisebt` CLI 命令在依赖就绪环境下正常工作
- 收益计算与 VectorbtAdapter 差异 < 5%
- 支持多资产组合回测
- 配置模型正确映射

## 结论

严格遵循“薄适配+原生API、强制依赖就绪、不做回退”的硬约束推进引擎接入，确保回测与实盘接口同构、行为一致。