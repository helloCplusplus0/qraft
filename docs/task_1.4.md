# 任务1.4：特征工程流水线（事前设计）

本文档基于 task_list.md 的任务1.4条目，明确范围、接口、执行约束与验收标准，遵循“最小可行+可扩展”，避免过度设计与无根据假设。

## 一、范围（Scope）
- 实现基础技术指标：
  - 简单移动平均 MA(window)
  - 指数加权移动平均 EMA(span)
  - 相对强弱指标 RSI(window)
- 建立左闭/滞后/对齐器框架：
  - 左闭窗口约定：时间t的值不包含t时刻新样本，等同于对输入序列做lag(1)后再rolling。
  - 滞后Lagger：对序列做严格滞后，避免未来函数。
  - 多源时间对齐：基于Polars Lazy按列Join，键为(ts,symbol)或(ts)；NaN传播采用内连接/外连接+显式fill策略。
- 横截面与数值变换：
  - 横截面排序：按某列对同一时刻、不同symbol排序，输出rank[0,1]或[1..N]
  - 分组中性化：对同一时刻内，按group列做组内标准化（z-score），输出去组均值后值
  - 去极值：按时点对横截面做winsorize（分位阈值）
  - 标准化：横截面z-score
- 执行引擎：以Polars LazyFrame为主，尽量采用列式表达式。

非目标（本任务不做）：
- 不引入完整因子库/学术指标全集，仅做MA/EMA/RSI与基本横截面处理。
- 不实现复杂泄漏检测、行业中性回归与IC评估，这些在后续任务实现。

## 二、输入/输出契约（API）
- 数据模型：
  - 时间戳列："ts"（Datetime，建议UTC或已由calendar.align_tz对齐）
  - 资产列："symbol"（Utf8），可选；若不存在则视为单资产时序
  - 数值列：任意浮点列，如"close"
- 指标计算（时序）：
  - ma(lf, col: str, window: int, min_periods: int | None = None, lag: int = 1) -> pl.LazyFrame
  - ema(lf, col: str, span: int, adjust: bool = False, lag: int = 1) -> pl.LazyFrame
  - rsi(lf, col: str, window: int, lag: int = 1) -> pl.LazyFrame
  - 约定：
    - 默认左闭：计算在lag后进行
    - 分组：若存在symbol列则按["symbol"]分组滚动
    - 输出列名：{col}_ma{window} / {col}_ema{span} / {col}_rsi{window}
- 横截面/变换（同一时刻内 across symbols）：
  - cs_rank(lf, col: str, method: Literal["dense","minmax"] = "dense") -> pl.LazyFrame
  - cs_winsorize(lf, col: str, lower: float = 0.01, upper: float = 0.99) -> pl.LazyFrame
  - cs_zscore(lf, col: str) -> pl.LazyFrame
  - neutralize_by_group(lf, col: str, group_col: str) -> pl.LazyFrame
  - 输出列名：追加后缀 _rank / _wins / _z / _neu
- 多源对齐：
  - align_on_ts(lfs: dict[str, pl.LazyFrame], how: Literal["inner","outer"] = "inner") -> pl.LazyFrame
  - 约定：按["ts","symbol"]存在时对齐，否则按["ts"]。
- NaN传播：
  - 指标计算中使用min_periods控制；横截面操作对每个时点独立，保留NaN并在后续由用户决定填充或过滤。

## 三、实现要点
- 以Polars表达式实现，避免collect中间结果；
- 避免未来函数：指标默认对输入做lag(1)；
- 窗口滚动：使用 group_by_rolling 或 group_by_dynamic 按["symbol"]与时间窗口在Lazy模式下实现；
- 当window为整数时，采用行数窗口（如最近N条），需要输入数据按时间升序分组有序；
- 统一常量：时间列名TS = "ts"，资产列名SYMBOL = "symbol"；
- 容错：当缺少symbol列时，自动退化为单序列计算。

## 四、验收标准（Acceptance）
- 代码：qraft/features/indicators.py, pipeline.py, transforms.py 均实现并通过类型检查；
- 单测：新增 tests/unit/test_indicators.py, test_pipeline.py, test_transforms.py；
- 功能：
  - 对示例数据（两只股票的close）计算MA/EMA/RSI，验证左闭滞后；
  - 对同一时点横截面排名、去极值、zscore与分组中性化；
  - 多源对齐：将两份LazyFrame按[ts,symbol]内连接/外连接成功；
- 质量门：make lint && make mypy && make test 全部通过，覆盖率≥80%。

## 五、样例数据与用例
- 构造两只symbol的日频close数据（含NaN边界），验证：
  - MA(window=3)与EMA(span=3)的首行NaN与左闭性；
  - RSI(window=3)在涨/跌情境下的数值范围0..100；
  - 横截面rank的范围与并列处理；
  - winsorize在1%/99%剪裁；
  - group内zscore与neutralize_by_group对组内均值为0。

## 六、非功能与限制
- 暂不实现复杂节假日与分钟级窗口；
- 对齐仅支持[ts]或[ts,symbol]键；
- 横截面计算在每个ts snapshot上执行，可能在极大横截面时内存敏感，后续再优化。

---

## 七、事后总结（Postmortem & Acceptance）

本节基于已落地的源代码与质量门结果，对任务 1.4 的交付进行复盘与验收评估。

### 1. 实际交付概述
- 指标实现（qraft/features/indicators.py）：
  - ma(col, window, lag)、ema(col, span, lag, adjust)、rsi(col, window, lag)
  - 默认左闭（lag=1），存在 symbol 列时自动分组滚动。
- 流水线工具（qraft/features/pipeline.py）：
  - lag(df, col, by=["symbol"])：严格滞后，防未来函数。
  - align_on_ts({name: lf}, how=inner|outer)：按 [ts, symbol] 或 [ts] 自动对齐，列名冲突规避。
- 横截面变换（qraft/features/transforms.py）：
  - cs_rank(col, method="dense|minmax")、cs_winsorize(col, q) 、cs_zscore(col)、neutralize_by_group(col, group_col)
  - 每个时点对不同 symbol 的横截面处理，输出列追加 _rank/_wins/_z/_neu 后缀。
- API 汇出（qraft/features/__init__.py）：导出指标、流水线与横截面函数作为公共 API。
- 单元测试（tests/unit）：
  - test_indicators.py 验证 MA/EMA/RSI 的左闭与列命名。
  - test_transforms_pipeline.py 验证横截面变换与对齐/滞后。

### 2. 质量门结果
- Lint：通过（flake8/black/isort）
- 类型检查：通过（mypy）
- 测试：通过（26 passed）
- 覆盖率：91.49%（阈值≥80%）

上述结果满足文档“验收标准（Acceptance）”中的全部质量门约束。

### 3. 偏差与修复记录（关键问题与解决）
- Polars API 差异：
  - 测试中对 pl.date_range 的参数兼容性存在差异（periods/start 等）。
  - 解决：测试统一改用 Python datetime 生成日期序列，避免版本差异导致用例失败。
- 类型提示与 mypy：
  - 早期在 transforms/indicators 中与 polars API 的类型签名不一致（如 quantile 调用方式、rolling_mean 参数名）。
  - 解决：修正 rolling_mean 的 min_periods，用列名优先的 quantile 调用方式，并在表达式构造中避免对 list[Expr] 进行无效方法调用。
- Lint：
  - 未使用导入与文档字符串行宽超限。
  - 解决：移除冗余导入、拆分长行，统一遵循 max-line-length=100。

### 4. 验收对照（逐条核对“二、输入/输出契约（API）”与“四、验收标准”）
- 功能项：
  - MA/EMA/RSI：已实现，默认左闭；存在 symbol 时分组滚动；列命名符合约定。
  - 横截面：cs_rank/cs_winsorize/cs_zscore/neutralize_by_group 均已实现并在单测覆盖。
  - 多源对齐：align_on_ts 支持 [ts, symbol] 或 [ts] 键，支持 inner/outer。
  - 滞后：lag 严格滞后，满足防未来函数要求。
- 质量门：
  - Lint/Mypy/Test 全通过；覆盖率 91.49% ≥ 80%。
- 结论：
  - 本任务所有必达项均满足，达到“可验收”标准。

### 5. 使用与注意事项（简要）
- 默认左闭：指标计算前先 lag(1)，如需调整可显式传参。
- 对齐策略：多源对齐默认按 [ts, symbol]，若无 symbol 列则退化到 [ts]。
- NaN 传播：横截面在每个时点独立处理，保留 NaN，由下游显式填充或过滤。

### 6. 后续增强建议（不影响本次验收）
- 扩展指标库：更多技术/统计指标（分位、波动率、ATR、动量/回撤等）。
- 行业/风格中性化：引入回归法与暴露约束，完善横截面中性化工具。
- IC/IR 与稳健性：增加时序/横截面因子的 IC/IR 与稳定性面板。
- 更丰富的对齐器：支持更细粒度的 join 策略与外连接的缺失填充策略模板。
- 分钟级与复杂窗口：在性能与内存评估后引入。

### 7. 结论：任务 1.4 验收通过
- 交付物与质量门均满足《任务1.4：特征工程流水线》文档约定，任务 1.4 予以完结。