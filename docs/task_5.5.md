# 任务5.5：策略池与质量闸门（事前设计 + 事后总结）

目的
- 将通过稳健性评估与一致性校验的策略纳入“策略池”，实现 candidate → stable 的治理流程
- 以清单化与哈希溯源确保快照可追溯、可复盘、可审计
- 将质量闸门阈值落地为代码接口，支持两阶段一致性、冷启动复跑与 Top‑N 重叠率判定

范围与不做清单
- 范围：
  - 策略池目录结构与元数据清单（artifacts/pool/）
  - Candidate 提案与 Stable 批准流程（快照+MANIFEST）
  - 质量闸门接口：enforce_pool_quality（两阶段一致性<2%、冷启动复跑<1%、Top‑N≥70%）
  - 代码位置：qraft/strategy_pool/manager.py、qraft/quality/gates.py（扩展）
- 不做：
  - 复杂的权限/审批流、服务化接口；
  - 实盘接入与风控联动；
  - 数据湖与大规模存储方案；

MVP 能力
- StrategyPoolManager
  - propose(candidate): 将策略产出与元数据固化为 EvidencePack，写出 MANIFEST.json 与 blobs/
  - approve(candidate_hash): 将 candidate 升级为 stable（复制快照并记录批准信息）
  - list_pool(): 返回 candidate/stable 清单及其元数据
  - 目录布局（相对仓库根）：
    - artifacts/pool/
      - candidates/<hash>/MANIFEST.json, blobs/
      - stable/<hash>/MANIFEST.json, blobs/
- 质量闸门 enforce_pool_quality
  - 输入：
    - quick 与 precise 的 BacktestResult（双通道）
    - signals_quick/signals_precise（用于 Top-N）
    - run_cold_start: 可调用的复跑函数（两次运行对 total_return 的相对差值）
    - thresholds: 复用 ConsistencyThresholds（限定：统计差<2%、equity末值差<2%、Top‑N≥70%、cold start <1%）
  - 输出：
    - detail dict：包含 consistency、cold_start 两大 gate 结果与聚合 passed 标记

核心接口与数据结构
- qraft/strategy_pool/manager.py
  - class StrategyPoolManager:
    - __init__(root_dir: Path | str = "artifacts/pool")
    - propose(payload: dict, metadata: dict) -> dict: 返回 manifest（含 manifest_hash）
    - approve(manifest_hash: str, approver: str, note: str = "") -> dict
    - list_pool() -> dict: {"candidates": [...], "stable": [...]}（读取各自 MANIFEST.json）
  - 依赖：qraft.evidence.EvidencePack（现有 compute_content_hash/generate_manifest/save_to_directory/verify_integrity）
- qraft/quality/gates.py（扩展）
  - def enforce_pool_quality(...):
    - 内部调用 run_consistency_suite 与 evaluate_cold_start
    - 聚合 rules：
      - 两阶段一致性：默认阈值2%（已有 ConsistencyThresholds 默认值即 2%）
      - 冷启动复跑：<=1%（ConsistencyThresholds.cold_start_total_return_pct 默认 1%）
      - Top‑N 重叠率：>=70%（ConsistencyThresholds.topn_overlap_ratio 默认 0.7）
    - 返回：{"passed": bool, "consistency": {...}, "cold_start": {...}}

与既有模块的复用
- 复用 qraft.validation.consistency:
  - ConsistencyThresholds、run_consistency_suite、evaluate_cold_start
- 复用 qraft.evidence.EvidencePack：
  - 内容寻址、MANIFEST 生成、完整性校验、保存/加载

测试计划与验收标准（事前）
- 新增 tests/unit/test_strategy_pool.py
  - test_enforce_pool_quality_pass：构造近似 quick/precise 与轻微噪声 signals，确保通过；冷启动复跑 run_func 稳定，差值<1%
  - test_propose_and_approve_and_list：
    - 使用 StrategyPoolManager.propose 写出 candidate 快照
    - verify_integrity(manifest) == True
    - approve 后 stable 目录存在对应快照
    - list_pool() 返回包含 candidate 和 stable 两侧记录
- 全量 pytest 通过

实现清单（事后）
- 源码
  - 新增 <mcfile name="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py"></mcfile>
  - 扩展 <mcfile name="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py"></mcfile>，新增 <mcsymbol name="enforce_pool_quality" filename="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py" startline="45" type="function"></mcsymbol> 并保留 <mcsymbol name="dual_channel_consistency" filename="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py" startline="26" type="function"></mcsymbol>
  - 导出更新 <mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/quality/__init__.py"></mcfile>
  - 策略池维护与稳健性打通（新增方法）：
    - <mcsymbol name="StrategyPoolManager.tag" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="162" type="function"></mcsymbol>
    - <mcsymbol name="StrategyPoolManager.deprecate" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="179" type="function"></mcsymbol>
    - <mcsymbol name="StrategyPoolManager.replace" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="188" type="function"></mcsymbol>
    - <mcsymbol name="StrategyPoolManager.cleanup_deprecated" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="201" type="function"></mcsymbol>
    - <mcsymbol name="StrategyPoolManager.evaluate_and_propose" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="232" type="function"></mcsymbol>
- 测试
  - 新增 <mcfile name="test_strategy_pool.py" path="/home/dell/Projects/Qraft/tests/unit/test_strategy_pool.py"></mcfile>
  - 全量测试通过

测试与验收结果（事后）
- 执行 pytest -q：全部通过（含新增用例），未破坏既有测试
- 关键断言：
  - enforce_pool_quality 通过，consistency 与 cold_start 子项均通过
  - propose -> approve -> list_pool 流程完整，MANIFEST 与 APPROVAL.json 正确产生，完整性校验通过

对照验收项（task_list.md 任务5.5）
- 建立 candidate→stable 流程与清单化管理，固定参数与快照：已完成（EvidencePack + MANIFEST + 目录结构）
- 质量闸门集成：两阶段一致性 <2%、冷启动复跑 <1%、Top‑N重叠率 ≥70%：已完成（enforce_pool_quality 复用 ConsistencyThresholds）
- 工件登记与可追溯（MANIFEST + 哈希）：已完成（EvidencePack.generate_manifest/verify_integrity）

增量扩展（已实现）
- 与稳健性评估打通：在 <mcsymbol name="StrategyPoolManager.evaluate_and_propose" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="232" type="function"></mcsymbol> 中集成 <mcsymbol name="enforce_pool_quality" filename="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py" startline="45" type="function"></mcsymbol> 与 <mcsymbol name="run_robustness_evaluation" filename="robustness.py" path="/home/dell/Projects/Qraft/qraft/validation/robustness.py" startline="1" type="function"></mcsymbol>，当 quality.passed 且 robustness.recommend 为 True 时自动触发 propose。
- 策略池维护工具：已补充标签、废弃、替换与清理能力，分别见 <mcsymbol name="StrategyPoolManager.tag" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="162" type="function"></mcsymbol>、<mcsymbol name="StrategyPoolManager.deprecate" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="179" type="function"></mcsymbol>、<mcsymbol name="StrategyPoolManager.replace" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="188" type="function"></mcsymbol>、<mcsymbol name="StrategyPoolManager.cleanup_deprecated" filename="manager.py" path="/home/dell/Projects/Qraft/qraft/strategy_pool/manager.py" startline="201" type="function"></mcsymbol>。

使用示例
- 质量判定 + 稳健性 + 自动提案（推荐方式）：
  - from qraft.strategy_pool import StrategyPoolManager
  - mgr = StrategyPoolManager()
  - rep = mgr.evaluate_and_propose(
      quick=quick, precise=precise,
      signals_quick=s1, signals_precise=s2, topn=10,
      run_cold_start=lambda: run_once(),
      robustness_index=idx,  # 稳健性评估所需索引/上下文
      run_with_cost=runner,  # 带交易成本的回测执行器
      payload={"name": "stratA", "params": {...}},
      metadata={"owner": "qa"},
    )
  - if rep["proposed"]: print("candidate saved at", rep["manifest"]["output_path"])
- 传统方式（仅质量 gate 后手动提案）：
  - from qraft.quality import enforce_pool_quality
  - rep = enforce_pool_quality(quick, precise, signals_quick=s1, signals_precise=s2, topn=10, run_cold_start=lambda: run_once())
  - if rep["passed"]:
      - from qraft.strategy_pool import StrategyPoolManager
      - mgr = StrategyPoolManager(); mgr.propose({"name": "stratA"}, metadata={"owner": "qa"})
- 池管理与维护：
  - mgr.tag(manifest_hash, add=["meanreversion", "v1"])
  - mgr.deprecate(old_hash, note="superseded by new tuning")
  - mgr.replace(old_hash, new_hash, note="better robustness score")
  - mgr.cleanup_deprecated(tier="candidates", older_than_days=7)

后续建议
- CLI 一体化（将在任务5.6实现）：qraft pool propose/approve/list/tag/deprecate/replace/cleanup

结论
- 任务5.5 按规划完成：接口复用、MVP 功能齐备、测试覆盖并通过；并完成增量扩展（稳健性打通与池维护工具）。未引入过度设计，满足可追溯治理目标。