# 任务5.4：稳健性评估与多重比较偏误治理（事前设计 + 事后总结）

目的与范围
- 目的：为搜索编排产出的候选策略提供稳健性评估，降低多重比较偏误风险，形成可量化的稳健性评分与是否进入策略池的建议。
- 范围：
  - 支持 OOS（训练/测试）切分与滚动检验
  - 支持交易成本 ±50% 敏感性复测
  - 支持基于权益序列的 bootstrap 统计（置信区间）
  - 生成稳健性报告（text/html/json）与综合评分
  - 将稳健性阈值接入质量闸门（后续由策略池任务统一串联）

设计原则
- 复用现有 API 与风格：延续 validation/consistency.py 的函数式签名（以 Callable 作为回测入口），延续 reports/generators.py 的报告风格（轻量 HTML + 内嵌 SVG）。
- 禁止过度设计：优先实现 MVP 能力，保留扩展点（如滚动指标选择、block bootstrap），但默认配置走常用路径。
- 与产出对接：输入以回测运行函数 run_func(start, end, cost_multiplier) 抽象，输出为字典 summary，便于与质量闸门/策略池串联。

能力清单（MVP）
- OOS 切分：按比例切分索引（默认 70/30），分别运行 in-sample 与 out-of-sample，产出各自核心指标（total_return/sharpe）。
- 滚动检验：按固定窗口与步长滑动，统计窗口内 total_return>0 与 sharpe>0 的占比（positive rate）。
- 成本敏感性：对 cost_multiplier∈{0.5,1.0,1.5} 复跑，复用 evaluate_cost_sensitivity，汇总总收益对成本的敏感曲线。
- Bootstrap：从权益序列推导简单日收益，做 i.i.d. 重采样，估计总收益分布的置信区间（默认 95%），给出下界 lower_ci。
- 综合评分与建议：以门槛驱动：
  - OOS 测试集 total_return ≥ 0
  - 滚动 positive_rate_sharpe ≥ 0.6
  - Bootstrap lower_ci ≥ 0
  满足则 recommend=true；并给出 0~1 的稳健性评分（主要由滚动占比驱动，OOS/Bootstrap 作为硬闸）。

核心接口（已实现）
- qraft/validation/robustness.py
  - RobustnessConfig/RobustnessThresholds 两个 dataclass
  - run_oos、run_rolling_validation、run_bootstrap_statistics、run_robustness_evaluation 四个入口
  - 复用 evaluate_cost_sensitivity
- qraft/reports/robustness_report.py
  - RobustnessReportGenerator：text/html/json 三种格式
  - RobustnessReportConfig：title/format/precision 三项
- 汇总导出：validation/__init__.py 与 reports/__init__.py 已导出新 API

输入输出
- 输入：
  - index: pd.DatetimeIndex（源数据时间轴，供 OOS/滚动切分）
  - run_func(start, end, cost_multiplier): 统一的回测入口
- 输出：
  - summary: Dict，包含 oos/rolling/sensitivity/bootstrap/score/recommend 等字段
  - report: 由 RobustnessReportGenerator 生成的文本/HTML/JSON

测试与验收（已通过）
- 新增 tests/unit/test_robustness.py，覆盖：
  - OOS/滚动/Bootstrap/综合评估与报告生成
  - 使用确定性随机种子，确保测试稳定
- pytest -q 全量通过，未破坏既有测试

使用示例
- 组装 run_func(start,end,cost_multiplier) 后：
  - from qraft.validation import run_robustness_evaluation, RobustnessConfig, RobustnessThresholds
  - from qraft.reports import RobustnessReportGenerator, RobustnessReportConfig
  - summary = run_robustness_evaluation(index, run_func, config=RobustnessConfig(), thresholds=RobustnessThresholds())
  - html = RobustnessReportGenerator().generate(summary, RobustnessReportConfig(format="html"))

后续扩展
- Block bootstrap、滚动指标的可配置选择、多资产多窗口分位数统计
- 将稳健分与阈值接入 quality.gates 的统一总报告（由任务5.5/5.6 串联）

事后反思
- 是否按规划完成：是。实现范围与 task_list.md 对齐，未做过度设计，充分复用现有 API（BacktestResult、evaluate_cost_sensitivity、报告风格）。
- 稳定性：测试采用确定性随机，CI 可稳定通过。
- 扩展性：接口面向 Callable，适配不同回测引擎/参数结构；报告采用轻量 HTML/JSON，便于下游接入。