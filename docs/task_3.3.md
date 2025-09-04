# Task 3.3：质量闸门与验收标准（Pre-Design）

## 目标与范围
依据 task_list.md“任务3.3：质量闸门与验收标准”，在不重复造轮子的前提下，基于既有模块最小增量实现质量闸门与报告：
- 质量闸门自动化检查（Consistency/Performance/Leakage/Reproducibility）。
- 双通道同门槛验证（快速/精确回测结果一致性）。
- 泄漏/对齐单元测试（跨期相关最大滞后位点判定、索引对齐校验）。
- 性能预算监控（运行时间预算门槛）。
- 工件复现性校验（EvidencePack 清单一致与完整性校验）。
- 质量报告生成器（文本与JSON）。

非目标（本阶段不做）：
- 不新增重型度量/回放系统，只做“闸门式”校验；CI 流水线配置放在后续阶段接入。
- 不引入外部监控/Profiler 依赖，采用轻量计时与统计。

## 复用与新增
- 复用：
  - 一致性验证：<mcfile name="consistency.py" path="/home/dell/Projects/Qraft/qraft/validation/consistency.py"></mcfile>，使用 <mcsymbol name="run_consistency_suite" filename="consistency.py" path="/home/dell/Projects/Qraft/qraft/validation/consistency.py" startline="196" type="function"></mcsymbol> 与 <mcsymbol name="ConsistencyThresholds" filename="consistency.py" path="/home/dell/Projects/Qraft/qraft/validation/consistency.py" startline="12" type="class"></mcsymbol>。
  - 工件/清单：<mcfile name="package.py" path="/home/dell/Projects/Qraft/qraft/audit/package.py"></mcfile>、<mcfile name="pack.py" path="/home/dell/Projects/Qraft/qraft/evidence/pack.py"></mcfile>。
  - 回测结果类型：<mcsymbol name="BacktestResult" filename="vectorbt_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/vectorbt_adapter.py" startline="8" type="class"></mcsymbol>。
- 新增：
  - <mcfile name="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py"></mcfile> 质量闸门与报告生成器。
  - <mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/quality/__init__.py"></mcfile> 暴露公共API。
  - 单元测试：tests/unit/test_quality_gates.py。

## API 设计（最小可用集）
- 数据类与阈值：
  - QualityThresholds：聚合质量闸门阈值（性能预算秒数、泄漏检测最大滞后窗口、顶层通过条件）。
  - 直接复用 <mcsymbol name="ConsistencyThresholds" filename="consistency.py" path="/home/dell/Projects/Qraft/qraft/validation/consistency.py" startline="12" type="class"></mcsymbol>。
- 闸门函数：
  - dual_channel_consistency(quick, precise, thresholds, signals_quick=None, signals_precise=None, topn=10) → dict：封装 <mcsymbol name="run_consistency_suite" filename="consistency.py" path="/home/dell/Projects/Qraft/qraft/validation/consistency.py" startline="196" type="function"></mcsymbol>。
  - monitor_performance(func, budget_sec) → dict：计时并与预算比较。
  - detect_leakage_alignment(signals, returns, max_lag=3) → dict：计算滞后(-k..+k)的相关，若最佳相关出现在负滞后（信号“领先”收益）→ 疑似泄漏。
  - verify_reproducibility(build_pack_func, metadata=None) → dict：两次构建 EvidencePack，比较 MANIFEST 等价并执行完整性校验。
- 报告：
  - generate_quality_report(consistency=None, performance=None, leakage=None, reproducibility=None) → {json, text}。

## 验收标准（与 task_list.md 对齐）
- 质量闸门自动化检查：提供上述四类闸门函数；集成报告生成器输出文本与JSON。
- 双通道同门槛验证：默认阈值与 <mcsymbol name="ConsistencyThresholds" filename="consistency.py" path="/home/dell/Projects/Qraft/qraft/validation/consistency.py" startline="12" type="class"></mcsymbol> 一致；支持Top-N重叠。
- 泄漏/对齐单元测试：
  - 当信号由未来收益构造（典型泄漏：signals = returns.shift(-1)），detect_leakage_alignment 返回 best_lag<0 且 leakage_suspected=True。
  - 基本索引对齐检查通过。
- 性能预算监控：当函数耗时<=budget_sec 返回通过，否则失败。
- 工件复现性校验：对相同输入构建的 EvidencePack，其 MANIFEST 完全一致，且 verify_integrity(True)。
- 质量报告生成器：包含 overall passed 与各闸门子结果；文本摘要可读。

## 测试计划
- 新增 tests/unit/test_quality_gates.py 覆盖：
  - dual_channel_consistency 正路径（构造近似相等的 BacktestResult）。
  - monitor_performance 通过/失败各一例（短耗时 vs 极小预算）。
  - detect_leakage_alignment 对泄漏样本识别（best_lag<0）。
  - verify_reproducibility 构建同一 EvidencePack 两次一致。
  - generate_quality_report 文本包含 Overall Passed。

## 代码结构
- 位置：
  - 质量闸门：<mcfile name="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py"></mcfile>
  - 测试：tests/unit/test_quality_gates.py

## 里程碑与输出
- 里程碑1（本次提交）：完成 gates.py 与单测，输出初版报告生成器；创建本设计文档。
- 里程碑2：回归全量测试，更新本文档为“实施后总结与反思”。

---

本文档为事前设计，后续将在实现完成后追加“实施小结与反思”章节。

## 实施后总结与反思（Post-Implementation）

### 实施内容概述
- 新增 <mcfile name="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py"></mcfile>，实现以下接口：
  - <mcsymbol name="dual_channel_consistency" filename="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py" startline="18" type="function"></mcsymbol>
  - <mcsymbol name="monitor_performance" filename="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py" startline="38" type="function"></mcsymbol>
  - <mcsymbol name="detect_leakage_alignment" filename="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py" startline="58" type="function"></mcsymbol>
  - <mcsymbol name="verify_reproducibility" filename="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py" startline="107" type="function"></mcsymbol>
  - <mcsymbol name="generate_quality_report" filename="gates.py" path="/home/dell/Projects/Qraft/qraft/quality/gates.py" startline="121" type="function"></mcsymbol>
- 新增 <mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/quality/__init__.py"></mcfile> 暴露公共 API。
- 新增单测 <mcfile name="test_quality_gates.py" path="/home/dell/Projects/Qraft/tests/unit/test_quality_gates.py"></mcfile> 覆盖四类闸门与报告生成。

### 单测与结果
- 运行全量测试：全部通过。
- 关键断言：
  - dual_channel_consistency 在近似结果下 `passed=True`；
  - monitor_performance 在合理预算下 `passed=True`，极小预算下 `passed=False`；
  - detect_leakage_alignment 对 signals=returns.shift(-1) 识别为泄漏（best_lag<0）；
  - verify_reproducibility 对同一输入两次构建 EvidencePack，manifest 相同且 integrity 校验通过；
  - generate_quality_report 文本包含 "Overall Passed"。

### 与规划对齐与不足
- 对齐：满足 task_list.md 的六项交付点（质量闸门函数、双通道验证、泄漏/对齐测试、性能预算、复现性校验、质量报告）。
- 不足与后续：
  - 性能监控目前为总耗时门槛，未来可扩展为分阶段/指标细分；
  - 泄漏检测基于相关与滞后扫描，适合线性关系，非线性泄漏需更复杂方法；
  - 质量报告目前为纯文本与JSON，不含HTML可视化；可在 Task 2.4 报表模块里接入模板化展示。

### 结论
- 本任务已按规划完成并通过验收标准。后续可按需将质量闸门集成至 CI 工作流与回归套件。