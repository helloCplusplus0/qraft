# 任务4.1：统一Runner实现（事前设计）

本文档基于 task_list.md 第4阶段 任务4.1 的要求，给出最小可行（MVP）的事前设计，严格复用现有组件，避免过度设计与无依据的实现。

## 目标与范围
- 统一Runner：用一个Runner封装“快速回测（vectorbt）”与“精确回测（Nautilus Trader）”。
- 策略协议解析：复用 StrategyValidator 与 ExpressionInterpreter，从策略JSON与价格数据生成交易信号。
- 参数冻结与锁定：对策略与关键运行参数生成指纹并在一次运行内锁定，避免运行中被修改；可输出指纹便于审计复现。
- 灰度与回滚（最小实现）：记录最近一次成功运行的指纹与配置到本地JSON状态文件；提供回滚到上一次成功指纹的能力（库内函数）。
- 一键切换实盘接口（最小实现）：通过 mode=auto/quick/precise 或 engine_config 决定走 VectorbtAdapter 或 NautilusAdapter。
- Runner状态监控（最小实现）：记录状态机（idle→running→succeeded/failed）、时间戳、最近错误、最近统计等，支持写入到state_store JSON。
- 交付物：qraft/runner/unified_runner.py；在 qraft/cli.py 新增 run 子命令；本文档事后更新记录实现与验收。

非目标/暂不实现：
- 不引入外部持久化后端（仅本地JSON）。
- 不实现真实实盘下单，只提供“接口切换”的管道与配置打通。

## 设计与接口
- BacktestResult：沿用 qraft.engines.vectorbt_adapter.BacktestResult（避免重复定义）。
- UnifiedRunner 类（库内API）
  - 初始化参数：
    - mode: "auto"|"quick"|"precise"（默认auto，自动检测nautilus是否可用）
    - init_cash: float（默认100万）
    - freeze_params: bool（默认True）
    - state_store: str|Path|None（状态文件路径，可选）
  - 方法：
    - run_from_paths(strategy_path, prices_csv, start=None, end=None, engine_config=None, allow_fallback_dev=False) -> BacktestResult
    - run_with_data(strategy_dict, prices_df, start=None, end=None, engine_config=None, allow_fallback_dev=False) -> BacktestResult
    - rollback() -> None（最小实现：从state_store恢复上一次成功的“冻结指纹”，仅在调用者希望二次运行时生效）
  - 行为：
    - 验证：StrategyValidator().full_validate
    - 解析表达式：ExpressionInterpreter().build_signal（沿用已有cli实现的阈值二值化规则）
    - 适配器：
      - quick → VectorbtAdapter.run
      - precise → NautilusAdapter.run（engine_config 控制 strict/allow_fallback_dev 等）
    - 冻结/指纹：将策略与关键运行参数序列化JSON，生成sha256指纹；在一次运行内固定使用该副本。
    - 状态：更新到内存并按需写入 state_store JSON（state, started_at, finished_at, last_error, stats, fingerprint, mode）。

- CLI：qraft run（主入口）
  - 参数：
    - --strategy, --prices（必填）
    - --mode [auto|quick|precise]（默认auto）
    - --start, --end（可选）
    - --engine-config <json>（可选）
    - --allow-fallback-dev（布尔，影响engine_config.strict*）
    - --no-freeze（可选；默认冻结）
    - --state-store <path>（可选）
    - --fmt [text|json]（默认text）
  - 输出：打印BacktestResult.stats，text 或 json。

## 数据契约
- 策略JSON：复用 qraft/schemas/strategy_v1.json 与 StrategyValidator。
- 价格数据：CSV 含列 ts, close[, symbol]；与现有 quickbacktest/precisebt 一致。
- BacktestResult：equity_curve: pd.Series；stats: Dict[str, Any]。

## 验收标准（对应任务清单）
- [x] 统一Runner类与API实现（unified_runner.py）。
- [x] 策略协议解析与执行（Validator+Interpreter 复用）。
- [x] 参数冻结与配置锁定（生成指纹并在运行期固定）。
- [x] 灰度与回滚（最小：state_store记录与rollback接口）。
- [x] 一键切换实盘接口（mode与engine_config）。
- [x] Runner状态监控（最小：内存与state_store JSON）。
- [x] CLI集成：qraft run 子命令。

## 风险与取舍
- 当选择 quick 且未安装 vectorbt → 直接报错，提示安装。
- 当选择 precise 且未安装 nautilus → 若严格模式则报错；若允许fallback-dev，则返回持币轨迹并标记失败元数据（沿用 NautilusAdapter 行为）。
- 不引入新的依赖或重复定义类型，确保最小增量实现。

## 自测计划（最小）
- 运行 `python -m qraft.cli run --help` 正常。
- 使用示例CSV/策略JSON运行 quick/precise（在依赖可用情况下）并返回统计。

## 实施记录与验收结论（事后）
- 代码实现：
  - 完成 qraft/runner/unified_runner.py（含状态、指纹冻结、auto/quick/precise 分流、回滚最小实现）。
  - 完成 qraft/runner/__init__.py 导出。
  - 修复并集成 qraft/cli.py 的 `run` 子命令，支持所列参数，支持 text/json 输出。
- 自测与验证矩阵（当前环境 + 单元测试模拟）：
  - CLI帮助：`python -m qraft.cli run --help` 正常显示。
  - quick 路径（真实运行）：使用 sample_strategy.json + sample_prices.csv，成功执行并输出统计（需已安装 vectorbt）。
  - auto 路径（无 nautilus-trader）：自动降级为 quick，走 VectorbtAdapter（单元测试覆盖 _detect_mode 分流与调用）。
  - precise 路径（engine 成功，模拟）：注入 nautilus_trader 伪模块并 monkeypatch NautilusAdapter._execute_engine，Runner 通过 precise 分支拿到 BacktestResult（单元测试覆盖）。
  - precise 路径（engine 执行失败，启用 dev 回退）：在存在 nautilus 前提下，_execute_engine 抛错且显式设置 allow_fallback_dev=True 时返回“持币回退”并带 engine_failed 标记（单元测试覆盖）；
  - precise 路径（缺失 nautilus-trader）：无论是否启用 dev 回退，均抛出清晰错误 `nautilus-trader is not installed`（单元测试覆盖）。
  - 状态/指纹与回滚：state_store JSON 持久化 state/last_stats/fingerprint，rollback() 使状态回到 idle 并保留指纹（单元测试覆盖）。
- 数据契约符合性：
  - 策略JSON符合 qraft/schemas/strategy_v1.json；表达式经 StrategyValidator 与 ExpressionInterpreter 校验与构建（Runner 内部复用，单元测试对信号构建采用桩替身聚焦路径验证）。
  - 价格CSV包含 ts, close 列；对齐并透视逻辑与既有 quickbacktest 兼容。
- 风险与取舍落实：
  - quick 模式严格依赖 vectorbt；缺失即报错。
  - precise 模式：
    - 缺失 nautilus-trader → 抛错（不触发回退）。
    - 存在 nautilus-trader 且执行失败，且显式启用 allow_fallback_dev → 返回持币回退并标注 engine_failed。

### 验收结果
- 按照“验收标准”清单，所有项均已实现并通过当前环境下的最小自测与单元测试验证。若需端到端验证 precise+nautilus，请按“后续建议”操作。
- 后续建议：
  - 在安装 nautilus-trader 的环境中，准备最小的 engine_config（含具体 Strategy 实例）并运行：
    - 示例：`python -m qraft.cli run --strategy sample_strategy.json --prices sample_prices.csv --mode precise --engine-config engine_config.json`
    - 观察输出是否包含非零总收益、年化收益等统计，并确认无错误抛出。
  - 在 docs/examples/ 添加更丰富的多资产CSV与策略示例，完善回测对齐覆盖面。