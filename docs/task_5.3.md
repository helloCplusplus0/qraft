# 任务 5.3：搜索编排器（Search Orchestrator）

目标（MVP 可落地）：
- 在不自研 DSL/微内核的前提下，基于现有适配层（VectorbtAdapter / 未来 NautilusAdapter）实现“策略参数空间 → 批量回测 → 结果聚合 → Top‑N 固化为 Evidence Pack”闭环；
- 支持 grid / random 搜索，最小并发与断点续跑；
- 产出统一的运行工件（results.jsonl / aggregated.json / topN/）；
- 可选接入 Prometheus/OpenMetrics 指标，形成统一的“多引擎一致”观测视图；
- CLI：qraft search run 一键驱动，明确依赖提示与错误回退。

范围与非目标：
- 范围：参数空间遍历（grid/random）、回测任务调度（本地进程池）、结果聚合与Top‑N冻结、工件落盘、CLI与日志、可选Prometheus指标；
- 非目标：自研回测引擎；分布式调度/队列；复杂采样设计（留待后续分层/拉丁超立方）。

设计要点与复用：
- 参数空间：<mcsymbol name="SearchSpace" filename="spaces.py" path="/home/dell/Projects/Qraft/qraft/search/spaces.py" startline="1" type="class"></mcsymbol>
- 单次回测：<mcsymbol name="_run_single_backtest" filename="batch_backtest.py" path="/home/dell/Projects/Qraft/qraft/engines/batch_backtest.py" startline="1" type="function"></mcsymbol>（内部适配 <mcfile name="vectorbt_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/vectorbt_adapter.py"></mcfile>）
- 结果聚合：<mcsymbol name="_build_aggregated_stats" filename="batch_backtest.py" path="/home/dell/Projects/Qraft/qraft/engines/batch_backtest.py" startline="1" type="function"></mcsymbol>
- 证据包：<mcfile name="package.py" path="/home/dell/Projects/Qraft/qraft/audit/package.py"></mcfile>
- CLI：<mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile> + <mcfile name="search_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/search_cmd.py"></mcfile>

可观测性与指标（统一命名规范；多引擎一致）：
- 指标总览（均带标签 space, plan, mode）：
  - Counter qraft_search_runs_total：编排器触发的 run 次数
  - Gauge qraft_search_runs_in_progress：进行中的 run 数
  - Histogram qraft_search_run_duration_seconds：单次 run 持续时间
  - Counter qraft_search_backtests_total：执行的回测次数（含失败）
  - Counter qraft_search_backtests_failed_total：失败回测次数，额外标签 error_type ∈ {vectorbt, nautilus, other}
  - Histogram qraft_search_backtest_duration_seconds：单次回测持续时间
- 记录时机：
  - run.started：启动时立即 inc runs_total 与 in_progress.inc（即使 precise 模式早退也保持一致）；
  - backtest.completed：每次回测完成后 inc backtests_total，observe backtest_duration，若失败则按 error_type inc failed_total；
  - run.completed：run 结束后 observe run_duration 并 in_progress.dec；若异常早退（例如 precise 模式占位错误），在 finally 中也会保证 observe/dec。
- precise 模式一致性：
  - 目前 precise 为占位（抛出 RuntimeError 并由 CLI 友好提示），但已纳入同一指标命名与标签体系，保证多引擎视图一致；
  - 当未来接入 Nautilus Trader 时，沿用相同 metrics 名称，仅通过 mode 标签区分，同时在失败计数中打上 error_type="nautilus"。
- 启动导出与开箱默认：
  - CLI 提供 --metrics-port（如 8001），会按需启动 PrometheusHTTP exporter；未安装 prometheus_client 时静默跳过；
  - 指标埋点代码在运行时动态检测 prometheus_client 是否存在，避免强依赖。

实现位置（核心文件）：
- <mcfile name="orchestrator.py" path="/home/dell/Projects/Qraft/qraft/search/orchestrator.py"></mcfile>：
  - 统一定义上述 Counter/Gauge/Histogram；所有指标均携带 space、plan、mode 标签；
  - precise 模式：在抛错前即更新 runs_total 与 in_progress，并在 finally 中对 run_duration 与 in_progress 做兜底 finalize，保证观测一致；
  - backtest 失败类型归一化：从日志 error 文本中提取 vectorbt/nautilus 关键词作为 error_type，未命中则归为 other；
  - run/backtest 生命周期事件通过 logger.info 输出结构化 JSON（search.run.started / prepared / backtest.completed / run.completed）。
- <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile>：新增 --metrics-port 选项并传递至命令实现。
- <mcfile name="search_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/search_cmd.py"></mcfile>：按需启动 Prometheus 指标导出 HTTP 服务，兼容 pytest 下 vectorbt 缺失的短路分支。

运行产物与目录结构：
- artifacts/search/{run_id}/
  - results.jsonl（逐条回测记录，含 param_hash/params/stats/equity_len）
  - aggregated.json（聚合统计，包含成功率、失败数、最佳/均值 Sharpe 等）
  - topN/（Top‑N 候选冻结为 EvidencePack 目录）

CLI 使用示例：
- 快速通道（vectorbt）：
  - qraft search run --space docs/examples/search_spaces/ma.yaml --prices data/prices.csv --plan grid --trials 50 --top-n 5 --fast --metrics-port 8001
- 精确通道（Nautilus，占位错误提示但指标仍按一致规范打点）：
  - qraft search run --space docs/examples/search_spaces/ma.yaml --prices data/prices.csv --plan grid --top-n 5 --precise --metrics-port 8001

测试与验收：
- 单测覆盖：
  - 断点续跑：已处理 results.jsonl 去重；
  - 缺依赖容错：vectorbt 缺失 → CLI 友好提示；precise 模式 → 抛错并提示使用 precisebt；
  - Top‑N 固化：产出 EvidencePack 目录与文件完整；
- 全量运行：pytest -q 应全部通过。

后续建议：
- precise 模式接入 NautilusAdapter，复用同一指标与标签；
- 失败样本错误类型结构化（error_code/error_stage），便于下游诊断面板；
- 增加 budget/并发/成功率等 run 级别指标，完善仪表盘；
- 提供 Onlook/Grafana 仪表盘模板（对接 VictoriaMetrics/Prometheus）。