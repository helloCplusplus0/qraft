# 任务5.6：CLI/报告/CI 整合（事前设计 + 事后总结）

目的
- 打通从搜索/回测产物到策略池治理与报告输出的命令行入口，降低人工操作成本，形成一键式流程。
- 梳理报告生成器（回测/稳健性）在 CLI 与库层的使用方式，沉淀可复用模版。
- 在现有 CI 基础上给出端到端串联（搜索 → 稳健性 → 策略池 → 金套件）的最小落地路径与扩展建议。

范围与不做清单
- 范围：
  - CLI：策略池维护子命令、质量与“评估+提案”一体化子命令接入主 CLI。
  - 报告：回测报告与稳健性报告生成器的对齐与示例。
  - CI：现有工作流说明与端到端串联建议（后续 PR 接入）。
- 不做：
  - 复杂 Web/可视化看板与服务化 API（维持 CLI/库模式）。
  - 大规模管道调度（Airflow/Argo 等），后续视需要补充。

实现概览
- CLI 接入
  - 主入口文件：<mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile>
  - 策略池子命令（pool）：实现 propose/approve/list/tag/deprecate/replace/cleanup，并新增 evaluate-and-propose 一键式门控与提案。
    - 处理器所在：<mcfile name="pool_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/pool_cmd.py"></mcfile>
      - <mcsymbol name="_cmd_pool_propose" filename="pool_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/pool_cmd.py" startline="31" type="function"></mcsymbol>
      - <mcsymbol name="_cmd_pool_approve" filename="pool_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/pool_cmd.py" startline="51" type="function"></mcsymbol>
      - <mcsymbol name="_cmd_pool_list" filename="pool_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/pool_cmd.py" startline="66" type="function"></mcsymbol>
      - <mcsymbol name="_cmd_pool_tag" filename="pool_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/pool_cmd.py" startline="91" type="function"></mcsymbol>
      - <mcsymbol name="_cmd_pool_deprecate" filename="pool_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/pool_cmd.py" startline="108" type="function"></mcsymbol>
      - <mcsymbol name="_cmd_pool_replace" filename="pool_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/pool_cmd.py" startline="122" type="function"></mcsymbol>
      - <mcsymbol name="_cmd_pool_cleanup" filename="pool_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/pool_cmd.py" startline="136" type="function"></mcsymbol>
      - 新增一体化评估提案：<mcsymbol name="_cmd_pool_evaluate_and_propose" filename="pool_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/pool_cmd.py" startline="153" type="function"></mcsymbol>
  - 与策略池管理器对接：<mcfile name="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py"></mcfile>
    - 质量闸门+稳健性评估 → 自动提案：<mcsymbol name="StrategyPoolManager.evaluate_and_propose" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="232" type="function"></mcsymbol>
  - Evidence Pack 构建（复用）：<mcfile name="evidence_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/evidence_cmd.py"></mcfile>
    - <mcsymbol name="_cmd_evidence" filename="evidence_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/evidence_cmd.py" startline="115" type="function"></mcsymbol>

- 报告生成器
  - 回测报告（文本/HTML/JSON）：<mcfile name="generators.py" path="/home/dell/Projects/Qraft/qraft/reports/generators.py"></mcfile>
    - <mcsymbol name="ReportConfig" filename="generators.py" path="/home/dell/Projects/Qraft/qraft/reports/generators.py" startline="14" type="class"></mcsymbol>
    - <mcsymbol name="BacktestReportGenerator" filename="generators.py" path="/home/dell/Projects/Qraft/qraft/reports/generators.py" startline="29" type="class"></mcsymbol>
    - 统一从 BacktestResult 生成文本/HTML/JSON，内置 SVG 迷你火柴线图。
  - 稳健性报告（文本/HTML/JSON）：<mcfile name="robustness_report.py" path="/home/dell/Projects/Qraft/qraft/reports/robustness_report.py"></mcfile>
    - <mcsymbol name="RobustnessReportConfig" filename="robustness_report.py" path="/home/dell/Projects/Qraft/qraft/reports/robustness_report.py" startline="10" type="class"></mcsymbol>
    - <mcsymbol name="RobustnessReportGenerator" filename="robustness_report.py" path="/home/dell/Projects/Qraft/qraft/reports/robustness_report.py" startline="16" type="class"></mcsymbol>
    - 输出 OOS/滚动/成本敏感性/Bootstrap/全样本等指标版块，给出 recommend/score。
  - 质量报告（文本/JSON）：由质量子命令内部生成（复用 generate_quality_report），详情见 <mcfile name="quality_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/quality_cmd.py"></mcfile>。
    - <mcsymbol name="_cmd_quality" filename="quality_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/quality_cmd.py" startline="23" type="function"></mcsymbol>

使用方法（CLI）
- 查看帮助
  - python -m qraft.cli --help
  - python -m qraft.cli pool --help

- 策略池基础操作
  - 提案：
    - python -m qraft.cli pool propose --payload artifacts/evidence/packX/manifest/payload.json --metadata artifacts/evidence/packX/manifest/metadata.json --root-dir artifacts/pool
  - 批准：
    - python -m qraft.cli pool approve --hash <manifest_hash> --approver alice --note "checked"
  - 查看：
    - python -m qraft.cli pool list --root-dir artifacts/pool --fmt json
  - 维护：
    - python -m qraft.cli pool tag --hash <manifest_hash> --add meanreversion --add v1
    - python -m qraft.cli pool deprecate --hash <manifest_hash> --note "superseded"
    - python -m qraft.cli pool replace --old <old_hash> --new <new_hash> --note "better robustness"
    - python -m qraft.cli pool cleanup --tier candidates --older-than-days 7

- 一键评估并提案（质量+稳健性）
  - python -m qraft.cli pool evaluate-and-propose \
    --strategy examples/strategy.json \
    --prices data/prices.csv \
    --start 2020-01-01 --end 2024-12-31 \
    --payload artifacts/evidence/payload.json \
    --metadata artifacts/evidence/metadata.json \
    --engine-config configs/nautilus_engine.json \
    --allow-fallback-dev \
    --topn 10 \
    --rob-oos-ratio 0.3 \
    --rob-rolling-window 252 --rob-rolling-step 21 \
    --rob-bootstrap-samples 500 --rob-ci-alpha 0.05 \
    --rob-oos-min-tr 0.0 --rob-rolling-min-positive 0.6 --rob-bootstrap-lower-ci-min 0.0 \
    --fmt text
  - 说明：该命令内部完成信号计算、快速与精确回测、质量闸门（双通道一致性+冷启动复跑）与稳健性评估，全部通过后自动生成候选快照并写入策略池。

- Evidence Pack（可选）：
  - python -m qraft.cli evidence --action build --strategy examples/strategy.json --prices data/prices.csv --start 2020-01-01 --end 2024-12-31 --mode quick --fmt json

报告产出（库层示例）
- 回测报告（BacktestReportGenerator）：统一生成文本/HTML/JSON，可嵌入到研发记录或审计包中（详见 generators.py）。
- 稳健性报告（RobustnessReportGenerator）：对 OOS/滚动/成本敏感性/Bootstrap/全样本进行汇总输出（详见 robustness_report.py）。
- 质量报告：qraft quality 子命令内生成文本/JSON 汇总，便于快速核对。

CI 集成现状与扩展建议
- 现有工作流：<mcfile name="ci.yml" path="/home/dell/Projects/Qraft/.github/workflows/ci.yml"></mcfile>
  - Lint：black/isort/flake8
  - 类型检查：mypy
  - 依赖审计：pip-audit --strict
  - 测试：pytest 覆盖率门槛 --cov-fail-under=80
- 端到端串联（建议在后续 PR 加入，配合集成测试）：
  - 新增 tests/integration/test_search_and_pool.py，串起“qraft search run → 稳健性评估 → pool.propose/approve → 金套件回归校验”。
  - 在 CI 中增加 integration 任务：
    - 预热小样本数据（或使用内置样例）。
    - 运行 qraft search run 产出 topN 与 Evidence Pack。
    - 触发 qraft pool evaluate-and-propose（或直接调用 StrategyPoolManager.evaluate_and_propose）。
    - 执行金套件检查（复用 Golden Backtests）。
  - 失败回退：保持现有单测任务独立，integration 失败不影响核心单测的快速反馈（可设为可选作业）。

对照验收项（task_list.md 任务5.6）
- 新增 CLI：qraft pool propose/approve/list，qraft report search-run
  - 已完成（pool）：propose/approve/list/tag/deprecate/replace/cleanup 全部接入主 CLI（见 pool_cmd.py）。
  - 增量实现：evaluate-and-propose 一体化门控与提案（见 _cmd_pool_evaluate_and_propose）。
  - 待补充：report search-run 独立 CLI 尚未提供；当前可通过质量/稳健性报告生成器与 quality 子命令替代。
- 在 CI 中串联搜索→稳健性→策略池→金套件
  - 当前：保留基础 CI（lint/type/audit/tests）。
  - 计划：新增 integration 作业与示例数据，串联全链路，作为后续 PR。
- 增加端到端示例
  - 文档内已给出完整 CLI 命令示例与参数说明；
  - docs/examples/algorithm_channel_e2e/ 目录与脚本将在引入集成测试时一并提交。

结论与后续工作
- 结论：
  - 策略池 CLI 与一体化“评估+提案”流程已落地，报告生成器可用于回测与稳健性结果的标准化输出；现有 CI 稳定运行并提供基础质量保障。
- 后续工作（建议按优先级推进）：
  - 补充 report search-run CLI（基于运行产物聚合 HTML/JSON 报告）。
  - 新增端到端集成测试与示例目录，扩展 CI 串联流程。
  - 将质量/稳健性报告的 HTML 输出嵌入 Evidence Pack，完善审计链路。