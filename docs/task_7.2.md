# 任务7.2：性能优化与稳定性（事前设计）

目标（对应 task_list.md 第7阶段 7.2 条款）：
- 实现数值稳定性保障
- 建立跨平台一致性测试
- 实现性能基准测试
- 优化热点计算路径
- 建立压力测试框架
- 实现自动化回归检测

范围与约束：
- 仅针对现有快速回测与质量门能力做最小增量：优先聚焦 VectorbtAdapter 的 fallback 计算路径与可复用的 validation/quality 模块；不引入新大型依赖。
- 不做过度设计；以脚本 + Makefile 目标 + 轻量 CI 作为闭环，未来可平滑扩展。

设计与落地计划：
1) 数值稳定性保障（VectorbtAdapter fallback 最小增强）
- 在不依赖 vectorbt Portfolio API 的回退路径中，加入稳健计算：
  - 使用 numpy 向量化进行加速与一致性；
  - 对日收益 port_ret 使用 log1p-cumsum 的方式合成权益曲线，避免极端值导致的 cumprod 漂移或溢出；
  - Sharpe 的标准差加入下界 ε=1e-12，避免除零/过小波动导致的数值不稳定；
  - 对输入收益中的 inf/-inf/NaN 做归零处理，再计算。
- 兼容既有接口与指标键名，确保单测无破坏。

2) 跨平台一致性测试（复用现有能力）
- 复用 qraft.validation.consistency 与 qraft.quality.gates：
  - compare_results / run_consistency_suite 已覆盖指标、权益末值与 TopN 重叠率等；
  - CLI 已有 quality 子命令（quality_cmd）封装双通道一致性（有 precise 时）与性能/复现性等校验。
- 本任务不新增复杂跨平台 Runner；以文档与 Makefile 驱动：通过 make test 运行 tests/unit/test_consistency.py 即可验证一致性能力。

3) 性能基准测试（最小闭环）
- 复用已有脚本 scripts/benchmark_quickbacktest.py；
- 新增 Makefile 目标 bench，便于统一执行与在 CI 中调用；
- 脚本输出 artifacts/benchmark_quickbacktest.json，便于后续可视化与阈值对比。

4) 优化热点计算路径（最小可验证增量）
- 对 VectorbtAdapter 回退路径进行 numpy 向量化（weights/rets 点乘求和、log1p 累积）；
- 保持与现有对齐/切片/列广播逻辑一致，不改变外部行为，仅优化速度与稳定性。

5) 压力测试框架（轻量脚本）
- 新增 scripts/stress_quickbacktest.py：
  - 生成多资产、长区间的价格数据，构造若干代表性信号，循环运行回测；
  - 记录耗时与异常计数，输出 artifacts/stress_quickbacktest.json；
  - 不引入外部依赖，默认在开发机/CI 以小规模参数运行，避免波动过大。

6) 自动化回归检测（轻量 CI）
- 新增 .github/workflows/quality.yml：
  - 触发条件：对 qraft/**、scripts/**、.github/workflows/quality.yml 的 PR；
  - 复用 Makefile 安装依赖，执行 make bench；
  - 基于基准脚本退出码判定是否失败（出现异常或脚本显式失败即失败）；
  - 时间阈值采取宽松策略（仅校验执行成功），避免 CI 波动导致误报；后续可按仓库稳定性逐步收紧。

验收标准：
- 单测：pytest 全量通过；tests/unit/test_consistency.py 通过；
- 性能脚本：scripts/benchmark_quickbacktest.py 可独立运行，生成 JSON 结果且无报错；
- Makefile：make bench 与 make stress 可执行且产出 artifacts；
- 数值稳定性：在极端输入（含 NaN/inf）下 VectorbtAdapter fallback 不抛异常，指标计算有限值；
- CI：quality.yml 在 PR 上成功执行并产出日志（可在 Actions 查看）。

后续可迭代项（不在本次范围内）：
- 在稳定后为基准引入“阈值回归门”，例如运行时间/Sharpe 基线波动区间；
- precise 通道集成更丰富的指标对齐，对 run_consistency_suite 增加更多 gates；
- 更全面的压力场景（极端跳空、停牌补齐、成交量容量约束等）。


## 事后总结（Postmortem）

本次任务聚焦于“性能优化与稳定性”的最小闭环落地，在推进过程中暴露并解决了因频率处理不当引发的数值与兼容性问题。主要结论如下：

- 症状与日志
  - 基准脚本与压力脚本初始运行时出现指标为 NaN（如 Sharpe）与 eq_len=0、ok=False 的问题。
  - artifacts 中的错误信息表明根因与频率有关，典型报错为：
    - “Value must be Timedelta, string, integer, float, timedelta or convertible, not BusinessDay”。
    - “invalid unit abbreviation: B”。

- 根因定位
  - 在回测适配层中，尝试将交易日频率以业务日偏移别名 'B' 传入下游（包括 pandas/NumPy 的 to_timedelta 与 vectorbt 的 Portfolio 工厂）。
  - NumPy/pandas 对 'B' 的支持存在局限，导致 to_timedelta/np.timedelta64 解析失败；同时下游 Portfolio 在缺失明确频率时对部分指标（如波动年化）表现不稳定。

- 修复方案
  - 频率推导统一化：基于索引相邻差分的中位数推导“真实时间跨度”，优先构造 pandas.Timedelta / np.timedelta64，再将其作为频率参数传递给下游；当无法可靠推导时，回退至少量“安全别名”（如 'D'、'h'），避免直接使用 'B'。
  - 数值稳定性增强（回退路径）：
    - 日收益合成采用 log1p → cumsum 再 expm1 的方式替代简单 cumprod，降低极端值漂移风险。
    - 波动标准差加入下界 ε=1e-12，避免除零与过小波动放大。
    - 对输入中的 NaN/±inf 做统一净化处理后再计算。
  - 代码整理：移除重复/分叉的频率处理代码，统一入口以降低回归风险。

- 验证结果
  - 单测：pytest 全量通过。
  - 性能基准：make bench 成功生成有效指标，Sharpe 不再为 NaN（例如 MA_CROSS≈0.134、RSI_14≈0.782，具体值以 artifacts 为准）。
  - 压力测试：make stress 运行通过，多个场景 ok=True，eq_len 为非零（例如 504）。
  - 工件检查：artifacts/benchmark_quickbacktest.json 与 artifacts/stress_quickbacktest.json 无错误字段，关键统计均为有限值。
  - CI：新增的 quality 工作流可在 PR 上执行基准脚本，作为轻量回归门（后续可逐步收紧阈值）。

- 结果快照（实际运行工件）：
  - artifacts/benchmark_quickbacktest.json：
    - MA_CROSS：ok=true，time_sec=5.7103，sharpe=0.1343955128640332
    - RSI_14：ok=true，time_sec=0.0207，sharpe=0.7820959927450014
  - artifacts/stress_quickbacktest.json：
    - MOM_MA20：ok=true，eq_len=504，time_sec=5.6284，sharpe_ratio=0.19767321288594436
    - LOW_VOL：ok=true，eq_len=504，time_sec=0.0164，sharpe_ratio=-0.2207045715882121
    - NOISE：ok=true，eq_len=504，time_sec=0.0148，sharpe_ratio=0.25708865884261867

- 影响范围与兼容性
  - 外部接口与指标键名保持不变；仅在适配层内部实现频率推导与稳定性增强，向下兼容既有调用。
  - 适配了交易日（BusinessDay）等常见索引；对于强不规则时间序列将自动降级为更保守的处理策略，避免误用。

- 后续建议（可选）
  - 为基准与压力脚本增加“阈值门”（如运行时长与 Sharpe 的容忍区间），并纳入 CI。
  - 引入对“不规则时间序列”的显式检测与告警，必要时自动切换到纯时间差推导模式。
  - 扩充交易日历/时区用例，增加属性与基于性质的测试（Hypothesis）覆盖极端场景。
  - 在稳定后补充可视化报表与更细粒度的数值诊断日志，便于持续演进。