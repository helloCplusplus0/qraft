# Task 6.3.2 — 日志规范化与 TUI 复盘增强（fix plus）

本次任务目标：
- 统一关键路径的结构化日志输出（JSON lines），并保留人类可读的文本摘要，便于 TUI/监控侧“解析 + 回放”。
- 结构化日志统一包含字段：run_id、strategy_id、snapshot_id（= manifest_hash）。
- 修正 TUI Monitor 文本模式的标题与远端指标区块，以匹配现有单测与回放需求。

## 改动范围与要点

1) 结构化日志统一规范（双通道：文本 + JSON）
- 使用 qraft/utils/logging.py 中的 log_event + with_context，确保同一事件既有文本摘要，也有 JSON 结构化日志；当环境变量 QRAFT_RUN_ID 存在时，为日志上下文注入 run_id。
- 在以下关键路径补齐/增强结构化字段：
  - qraft/strategy_pool/manager.py
    - propose/approve/list_pool/evaluate_and_propose：
      - snapshot_id：与 manifest_hash 等价别名统一输出
      - strategy_id：从 payload.strategy_id 或 payload.strategy.{name|id} 中“尽力提取”
      - run_id：通过 with_context 从环境变量 QRAFT_RUN_ID 注入
  - qraft/deployment/grayscale.py
    - propose/approve_and_publish/rollback：
      - snapshot_id：与 manifest_hash 等价别名统一输出
      - strategy_id：从 propose 的 payload 中“尽力提取”
      - run_id：通过 with_context 注入

2) CLI 初始化与 run_id 传播
- qraft/cli.py：入口会检测环境变量 QRAFT_RUN_ID，并调用 setup_once 初始化“文本 + JSON 双 handler”的日志。
- qraft/tui/launcher.py：在启动子进程前临时设置父进程 os.environ 中的 QRAFT_RUN_ID，保证子进程继承；避免以 Popen(env=...) 方式触发单测 fake_popen 的不兼容问题。

3) TUI Monitor 文本模式修正
- qraft/tui/panels.py：文本模式标题改为“-- Search Summary (latest) --”，并统一展示“-- Remote Metrics (sample) --”区块（无指标时显示“(no remote metrics)”），与单测期望一致。

## 使用方式（如何开启结构化 JSON）
- 运行 CLI 或由 TUI 调度时，设置环境变量 QRAFT_RUN_ID（例如：`export QRAFT_RUN_ID=$(date +%s)`）。
- 之后的关键事件会同时输出：
  - 文本摘要：面向控制台/TUI 直接可读
  - JSON 行：面向日志采集与 TUI/监控侧解析，可基于 event/type 等键进行筛选

示例（示意，字段将随上下文扩展）：
- 文本：
  - Published 9f2a... to stable
  - Rolled back to 7ab1...
- JSON：
  - {"event":"deploy.publish.success","run_id":"...","manifest_hash":"9f2a...","snapshot_id":"9f2a...","action":"publish","state":"success","path":"artifacts/deploy"}
  - {"event":"pool.propose.success","run_id":"...","strategy_id":"mean_rev_v1","manifest_hash":"7ab1...","snapshot_id":"7ab1...","output_path":"..."}

## 兼容性与回放
- 文本摘要保留，不影响现有 TUI/Rich 展示；TUI 可选按 JSON lines 做结构化解析与回放。
- strategy_id 的获取为尽力而为（从 payload.strategy_id 或 payload.strategy.{name|id} 提取），不会影响主流程与单测。

## 测试结果
- 全量单测通过（pytest -q 100% 通过）。
- 关键用例：
  - tests/unit/test_tui_launcher.py：子进程环境变量注入修复
  - tests/unit/test_tui_panels.py：Monitor 文本模式标题/远端指标区块修正

## 后续建议
- 将更多模块的日志事件对齐到统一的字段规范（特别是 strategy_id 的显式传递）。
- 增补 Prometheus 导出器（可选），用于远程监控指标聚合。
- Rich 模式增强：Monitor 的 Deploy 区域支持展开 HISTORY 表格并颜色标注 publish/rollback（计划项）。