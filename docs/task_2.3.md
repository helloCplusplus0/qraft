# 任务2.3：两阶段回测一致性验证（Pre-Design）

目标
- 在不引入过度设计的前提下，提供一个轻量的“一致性验证”工具，用于对比两种回测阶段（快速/精确）的输出一致性，并形成可复用的验证报告与单测用例。
- 复用现有 API 与数据结构，仅围绕 BacktestResult 与可选的信号数据进行比对，不侵入引擎实现。

输入/输出与范围
- 输入：
  - 两个 BacktestResult（通常对应 quick=VectorbtAdapter、precise=NautilusAdapter）。
  - 可选：对应阶段的信号矩阵（DataFrame，index为时间，列为标的），用于 Top-N 重叠率度量。
  - 可选：回测执行回调（用于冷启动复跑与成本敏感性评估），签名如下：
    - 冷启动：run_func() -> BacktestResult（无副作用或显式固定随机种子）。
    - 成本敏感性：run_func(cost_multiplier: float) -> BacktestResult（外部负责把成交/费用参数乘以 multiplier 再执行）。
- 输出：
  - 指标度量结构体/字典（包含差异率、相关性、Top-N重叠率等）。
  - 总结报告文本（可打印/日志上报）。
  - 单元测试覆盖核心功能。

关键指标与阈值（默认，可通过参数覆盖）
- 统计指标一致性：
  - total_return 差异率 < 2%
  - annualized_return 差异率 < 2%
  - max_drawdown 差异率 < 2%
  - sharpe_ratio 绝对差 |Δ| < 0.10
- 净值曲线一致性：
  - 末值相对差 |eq1_T - eq2_T| / mean(eq1_T, eq2_T) < 2%
  - 可选：皮尔逊相关系数 corr ≥ 0.98（不作为强制门槛，先报告展示）
- 冷启动复跑一致性：
  - 两次独立复跑（同配置）之间 total_return 差异率 < 1%
- 成本敏感性：
  - 在 ±50% 成本因子下，报告 total_return 变化情况（不强制门槛，仅报告）
- Top-N 重叠率（若提供 signals_quick 与 signals_precise）：
  - 平均重叠率（Top-K）≥ 70%（默认 K=10，可配置）

与现有代码的关系与复用
- 复用 <mcfile name="vectorbt_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/vectorbt_adapter.py"></mcfile> 中的 <mcsymbol name="BacktestResult" filename="vectorbt_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/vectorbt_adapter.py" startline="1" type="class"></mcsymbol> 作为一致性对比的统一结果数据结构。
- 不修改任何引擎/适配器实现；一致性验证仅在结果层与可选信号矩阵层进行。

公共API设计（MVP）
- 模块：<mcfile name="consistency.py" path="/home/dell/Projects/Qraft/qraft/validation/consistency.py"></mcfile>
  - ConsistencyThresholds：阈值配置数据类（含统计、净值、冷启动、Top-N 门槛）。
  - compare_results(quick: BacktestResult, precise: BacktestResult, ..., signals_quick: Optional[pd.DataFrame]=None, signals_precise: Optional[pd.DataFrame]=None, topn: Optional[int]=10) -> Dict[str, Any]
    - 核心对比，返回 metrics 与 pass 标记。
  - evaluate_cold_start(run_func: Callable[[], BacktestResult], thresholds: ConsistencyThresholds) -> Dict[str, Any]
  - evaluate_cost_sensitivity(run_func: Callable[[float], BacktestResult], multipliers: Sequence[float]=(0.5, 1.5)) -> Dict[str, Any]
  - generate_report_text(summary: Dict[str, Any]) -> str
  - run_consistency_suite(...) -> Dict[str, Any]

交付物
- 源码：
  - <mcfile name="consistency.py" path="/home/dell/Projects/Qraft/qraft/validation/consistency.py"></mcfile>
  - <mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/validation/__init__.py"></mcfile>
- 单测：
  - <mcfile name="test_consistency.py" path="/home/dell/Projects/Qraft/tests/unit/test_consistency.py"></mcfile>
- 报告：
  - 由 generate_report_text 输出到控制台/日志，不额外生成文件。

验收标准（Acceptance）
- compare_results 在统计与净值曲线指标上，通过默认阈值时返回 passed=True。
- evaluate_cold_start 在确定性 run_func 下返回 passed=True；在指标上给出差异率。
- evaluate_cost_sensitivity 返回不同 multiplier 下的 total_return 报告。
- 若提供 signals_*，topn_overlap ≥ 70% 时 passed_topn=True。
- 单测覆盖 compare_results、topn_overlap、cold_start、cost_sensitivity 的主路径。

事后总结（Post-Implementation）
- 实现概述：
  - 新增 <mcfile name="consistency.py" path="/home/dell/Projects/Qraft/qraft/validation/consistency.py"></mcfile>，实现 ConsistencyThresholds、compare_results、compute_topn_overlap、evaluate_cold_start、evaluate_cost_sensitivity、generate_report_text、run_consistency_suite。
  - 新增 <mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/validation/__init__.py"></mcfile> 暴露公共接口。
  - 新增 <mcfile name="test_consistency.py" path="/home/dell/Projects/Qraft/tests/unit/test_consistency.py"></mcfile>，覆盖主路径：统计对比、净值末值对比、Top-N 重叠、冷启动一致性、成本敏感性，以及报告文本生成。
- 与预期对比：
  - 完全复用现有 BacktestResult 定义 <mcsymbol name="BacktestResult" filename="vectorbt_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/vectorbt_adapter.py" startline="1" type="class"></mcsymbol>，未侵入 engines/adapter 代码。
  - 指标与阈值严格对齐 task_list.md：2%/1% 门槛、±50% 成本敏感区间、Top-N≥70% 判定。
  - CI 单测全部通过，未引入额外外部依赖。
- 后续改进建议：
  - 可在报告中增加按区间的分段相关性与滚动差异分析。
  - 引入可选的对齐方式参数（内联/外联/前后截断）以适配不同数据管线。
  - 提供 CLI 子命令（可选），集成到回归套件，生成一致性报告。

验收与结论
- 依据验收标准：
  - compare_results：通过默认阈值返回 passed=True（单测覆盖）。
  - 冷启动复跑 evaluate_cold_start：确定性 run_func 返回 passed=True（单测覆盖）。
  - 成本敏感 evaluate_cost_sensitivity：返回 multiplier→total_return 报告（单测覆盖）。
  - Top-N：当 signals_* 接近时，overlap≥70% 且 passed_topn=True（单测覆盖）。
- 结论：本任务已按规划完成并通过验收标准。