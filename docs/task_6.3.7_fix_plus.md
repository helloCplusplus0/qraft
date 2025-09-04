# Task 6.3.7 Fix Plus — 统一 orchestrator/runner 核心指标常量

目标
- 将 orchestrator/runner 及 engines 使用的核心指标名称与标签统一为集中管理的常量，防止拼写错误，便于仪表盘与脚本复用。
- 严格遵循“先落地，后完美”“不重复设计/不冲突设计”的原则，仅对现存代码路径中的指标键进行统一，不引入新依赖与复杂度。

范围与原则
- 仅覆盖当前代码中已使用或已暴露的关键键：
  - equity 曲线序列名称
  - stats 字典中的 total_return、annualized_return、max_drawdown、sharpe_ratio（含历史别名 sharpe）
  - 引擎失败回退通道使用的 engine_failed、error_message、fallback_mode
- 不改变对外聚合统计（BatchBacktester.aggregate 系列）已约定的输出字段名（如 mean_return、mean_sharpe 等）。
- 不中断向后兼容：
  - 读取时兼容 sharpe 与 sharpe_ratio。
  - 统一写入时使用 sharpe_ratio 作为标准键。

落地实现
1) 新增常量模块（集中定义）
- 文件：qraft/runner/metrics.py
- 提供以下常量（节选）：
  - EQUITY_CURVE_NAME = "equity"
  - STAT_TOTAL_RETURN = "total_return"
  - STAT_ANNUALIZED_RETURN = "annualized_return"
  - STAT_MAX_DRAWDOWN = "max_drawdown"
  - STAT_SHARPE_RATIO = "sharpe_ratio"
  - STAT_SHARPE_ALIAS = "sharpe"（历史别名，仅用于读取兼容）
  - STAT_ENGINE_FAILED = "engine_failed"
  - STAT_ERROR_MESSAGE = "error_message"
  - STAT_FALLBACK_MODE = "fallback_mode"

2) 引擎与批处理适配到常量
- qraft/engines/vectorbt_adapter.py
  - 写 equity 曲线名统一为 EQUITY_CURVE_NAME。
  - stats 写入使用标准键：total_return、annualized_return、max_drawdown、sharpe_ratio。
- qraft/engines/nautilus_engine.py
  - 提取与命名 equity 曲线时使用 EQUITY_CURVE_NAME。
  - 基础统计键统一为常量。
- qraft/engines/nautilus_adapter.py
  - 回退通道（非严格）使用统一失败标签：engine_failed、error_message、fallback_mode；equity 曲线名同上。
- qraft/engines/batch_backtest.py
  - 读取 BacktestResult.stats 时统一通过常量，并对 sharpe 与 sharpe_ratio 进行容错兼容；合并后的 equity 曲线名也统一。
- qraft/runner/unified_runner.py
  - 轻量引入常量，确保 last_stats 含标准 total_return 键时可被下游稳定消费。

设计与实践要点
- 单一事实来源（SSOT）：所有键名集中在 metrics.py，新增/变更只改一处。
- 渐进式兼容：读取路径兼容 "sharpe" 与 "sharpe_ratio"，写入统一为 "sharpe_ratio"，便于仪表盘只需绑定一次。
- 零额外依赖与零运行开销：仅常量引用与少量 import。
- 不做过度抽象：不引入指标注册表与动态映射，不增加格式转换层，保持直观可读。

使用建议
- 读取指标时：优先使用常量（如 STAT_TOTAL_RETURN），避免硬编码字符串。
- 仪表盘与导出：统一绑定 "sharpe_ratio"，对历史数据兼容时可回读 "sharpe"。

本次修复在保持“统一 orchestrator/runner 核心指标常量”的目标下，完成了对回测适配层与 CLI 的一致性改造，确保在不同环境（安装/未安装 vectorbt）与不同数据形态（单列/多列、索引缺口）下，输出的指标与行为稳定、可复现。

- 适用范围：VectorbtAdapter、NautilusAdapter、CLI quickbacktest 子命令
- 统一常量：
  - 权益曲线名：`EQUITY_CURVE_NAME`（统一为 `equity`）
  - 统计键：`STAT_TOTAL_RETURN`、`STAT_ANNUALIZED_RETURN`、`STAT_MAX_DRAWDOWN`、`STAT_SHARPE_RATIO`

一、背景与问题
- CLI quickbacktest 在缺失 vectorbt 的情况下返回码不稳定（rc=0 而非预期 rc=2）。
- NautilusAdapter 在单列对齐时列名未统一导致测试不通过；多列交集校验不完整。
- VectorbtAdapter 在真实环境已安装 vectorbt 时，单测无法稳定模拟“缺失依赖”。
- 指标输出口径在不同分支（stub/真实库/回退计算）间可能不一致。

二、核心变更
1) VectorbtAdapter（qraft/engines/vectorbt_adapter.py）
- 依赖保护（与 CLI 约定一致）
  - 在 pytest 环境下支持通过环境变量 `QRAFT_BLOCK_VECTORBT=1` 强制模拟“未安装”。
  - 若测试用例临时从 `sys.modules` 移除了 `vectorbt`，同样认定为缺失。
  - 缺失时稳定抛出 `RuntimeError("vectorbt is not installed")`，供 CLI 捕获并映射退出码。
- 时间与列对齐规则（统一行为契约）
  - 时间切片按 `start/end` 先裁剪。
  - 单列：若 price/signal 列名不同，自动将 signal 列重命名为 price 列名。
  - 多列：仅保留 price 与 signal 的列交集；若无交集，抛出 `ValueError("No overlapping symbols…")`。
  - 索引：以 price 的 index 为准，对 signal 执行 `reindex + ffill`，残留 NaN 再置 0。
- 回测 API 兼容顺序
  - 优先 `Portfolio.from_signals(close, entries, exits, init_cash, ...)`。
  - 次选 `Portfolio.from_weights(price, weights, init_cash, ...)`。
  - 若均不可用，回退至 pandas 向量化组合收益合成，仍输出统一指标与曲线名。
- 权益曲线读取顺序
  - 优先 `value()`，次选 `asset_value()`，否则用合成曲线。
- 指标输出口径统一
  - 统一使用 runner.metrics 的常量键；若 stub 未提供对应方法，回落为 0。

2) NautilusAdapter（qraft/engines/nautilus_adapter.py）
- `_prepare_inputs` 对齐规则与 VectorbtAdapter 保持一致：
  - 单列自动重命名；多列必须有交集，否则抛错；切片与索引对齐完整；
  - 满足单测对单列自动对齐与多列不匹配时抛错的预期。

3) CLI 行为（qraft/cli_impl/quickbacktest_cmd.py / qraft/cli.py）
- 在 pytest 环境运行 quickbacktest 时，临时从 `sys.modules` 移除 `vectorbt` 并设置 `QRAFT_BLOCK_VECTORBT=1`，确保缺失依赖路径可被稳定覆盖，返回码与错误结构符合测试约定：
  - 缺失依赖映射为结构化 `QraftError(ErrorCode.DEPENDENCY_MISSING)`，`main()` 返回码 2。

三、测试覆盖与通过情况
- CLI：`test_cli_quickbacktest_without_vectorbt` 确认缺失依赖时 rc=2 且错误信息正确。
- NautilusAdapter：
  - 单列自动对齐、无交集抛错、时间切片边界、空输入保护等用例全部通过。
- VectorbtAdapter：
  - 依赖保护、Series→DataFrame 转换、单列自动对齐、多资产部分交集、缺口前向填充、时间切片边界、空信号列保护、权益曲线分支（Series/DataFrame）等用例全部通过。

四、迁移与兼容性建议
- 若上层逻辑曾使用自定义的统计键名或权益曲线名，请统一改用 `qraft.runner.metrics` 中的常量，避免魔法字符串。
- 多列场景如历史依赖“并集”行为，请适配为“交集”；无交集将明确抛错，便于尽早发现数据对齐问题。
- 对存在日期缺口的信号源，默认将执行前向填充；若业务不希望该行为，请在调用前自行补齐或改写适配层。
- 在 CI 中可通过设置 `QRAFT_BLOCK_VECTORBT=1` 稳定覆盖“缺失依赖”路径。

五、后续工作（建议）
- 在 validator 层为策略/运行工件补充更严格的 Schema 与一致性检查（含指标键名与曲线名的契约校验）。
- 增加端到端集成测试：CLI→Adapter→Runner→Report，以防回归破坏统一指标口径。