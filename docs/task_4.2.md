# 任务4.2：金套件（Golden Backtests）事前任务设计

目标
- 构建一套稳定、可复现的“金套件”回测集合，用于回归检测与合同测试（Contract Tests）。
- 通过统一Runner（quick/precise）在固定数据快照上产出基线指标，后续版本回归时与基线对比，快速发现行为漂移。

范围与原则
- 避免过度设计：优先复用现有组件（ExpressionInterpreter、UnifiedRunner、VectorbtAdapter、NautilusAdapter）。
- 仅使用 MVP 表达式与策略协议（Schema v1）；不引入新的策略描述语言。
- 基线以“统计指标”与“数据快照指纹”为主，避免过于依赖具体实现细节。

策略集合（3-5个基准策略）
- MA交叉：CROSS(SMA(close, 10), SMA(close, 30))
- EMA动量：EMA(close, 12)
- RSI均值回复：RSI(close, 14)
- 横截面排序：RANK(close)（当价格为多标的时生效；单标的环境下默认跳过该策略的强校验）

数据快照
- 使用 CSV 宽表或单列格式：
  - 单资产：列为 ts, close
  - 多资产：列为 ts, symbol, close（内部透视为宽表）
- 对快照进行 SHA256 指纹，记录于基线文件，确保复现性。

执行与产物
- 新增模块：qraft/golden/strategies.py 提供内置策略构建器（返回符合 Schema v1 的 strategy JSON）。
- 新增命令：qraft golden
  - 生成基线：qraft golden --prices prices.csv --action generate --output artifacts/golden/baseline.json
  - 校验回归：qraft golden --prices prices.csv --action check --input artifacts/golden/baseline.json
  - 可选参数：--start --end --fmt [text|json] --epsilon <浮点阈值，默认1e-6>
- 基线文件结构（示例）：
  {
    "created_at": "2025-08-24T12:00:00Z",
    "data_fingerprint": "<sha256(prices.csv contents)>",
    "strategies": {
      "ma_cross": {"stats": {"total_return": 0.123456, "annualized_return": 0.234567, "max_drawdown": 0.111111, "sharpe_ratio": 1.2345}},
      "ema_momentum": {"stats": {...}},
      "rsi_mean_reversion": {"stats": {...}},
      "cs_rank": {"stats": {...}}
    }
  }

契约与回归校验
- 对齐指标集：total_return, annualized_return, max_drawdown, sharpe_ratio。
- 比较策略：逐项|绝对差值 <= epsilon（默认1e-6）；支持 --epsilon 覆盖。
- 特殊策略：cs_rank 仅在多标的时纳入强校验；单标的时报告“跳过”。
- 缺失/新增策略：
  - 基线存在但当前缺失 → 失败
  - 当前存在但基线无 → 警告（不影响退出码）

实现步骤
1) qraft/golden/strategies.py：内置策略工厂与注册表
2) qraft/cli_impl/golden_cmd.py：实现 generate / check 两个动作
   - 复用 UnifiedRunner(mode=quick) 构建信号与执行回测
   - 生成或对比基线，并输出文本或JSON报告
3) qraft/cli.py：增加 golden 子命令并接线
4) 测试：tests/integration/test_golden_suite.py
   - monkeypatch UnifiedRunner 所在模块内的 VectorbtAdapter，避免真实依赖
   - 覆盖：生成→读取→校验 全流程；以及失败场景

验收标准
- 命令可运行：
  - qraft golden --prices sample_prices.csv --action generate → 生成基线文件
  - qraft golden --prices sample_prices.csv --action check → 基于同数据与策略，校验通过（退出码0）
- 集成测试通过，且在未安装 vectorbt/nautilus 的环境下仍可运行（通过打桩）
- 文档（本文件）更新：实现摘要、产物说明、回归策略、已知限制

已知限制与后续可选增强
- cs_rank 需要多标的数据才具备区分性
- 当前基线对指标仅做标量平均（与 VectorbtAdapter 对齐），未来可扩展维度级别对比
- 可扩展 precise 通道对比（当环境可用时）

---

事后总结（实现摘要与验收）
- 代码实现：
  - 新增 <mcfile name="strategies.py" path="/home/dell/Projects/Qraft/qraft/golden/strategies.py"></mcfile> 提供 4 个内置基准策略：<mcsymbol name="ma_cross" filename="strategies.py" path="/home/dell/Projects/Qraft/qraft/golden/strategies.py" startline="8" type="function"></mcsymbol>、<mcsymbol name="ema_momentum" filename="strategies.py" path="/home/dell/Projects/Qraft/qraft/golden/strategies.py" startline="23" type="function"></mcsymbol>、<mcsymbol name="rsi_mean_reversion" filename="strategies.py" path="/home/dell/Projects/Qraft/qraft/golden/strategies.py" startline="38" type="function"></mcsymbol>、<mcsymbol name="cs_rank" filename="strategies.py" path="/home/dell/Projects/Qraft/qraft/golden/strategies.py" startline="53" type="function"></mcsymbol>；
  - 新增 <mcfile name="golden_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/golden_cmd.py"></mcfile>，实现 generate 与 check 两个动作，复用 <mcfile name="unified_runner.py" path="/home/dell/Projects/Qraft/qraft/runner/unified_runner.py"></mcfile> 的 <mcsymbol name="run_with_data" filename="unified_runner.py" path="/home/dell/Projects/Qraft/qraft/runner/unified_runner.py" startline="170" type="function"></mcsymbol>；
  - 在 <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile> 新增 golden 子命令接线；
  - 新增集成测试 <mcfile name="test_golden_suite.py" path="/home/dell/Projects/Qraft/tests/integration/test_golden_suite.py"></mcfile>，通过注入 fake vectorbt 实现端到端验证；
- 自测结果：
  - 执行 pytest 全量测试通过，新增测试覆盖“生成→校验”流程与“指纹不一致失败”场景。
- 产物与使用：
  - 生成基线：qraft golden --prices <csv> --action generate --output artifacts/golden/baseline.json
  - 回归校验：qraft golden --prices <csv> --action check --input artifacts/golden/baseline.json
  - 基线文件包含字段：created_at、data_fingerprint、strategies[*].stats(total_return, annualized_return, max_drawdown, sharpe_ratio)
- 验收结论：
  - 按设计完成：策略工厂、CLI 命令、回归与合同测试逻辑、指纹校验与报告输出，且无额外依赖；
  - 兼容无 vectorbt 环境：测试通过注入 stub 验证，符合“充分利用现成 API、禁止重复设计”的约束。
- 反思与后续：
  - 当前以 quick 通道为主，可在有条件时扩展 precise 通道一致性基线；
  - 可增加多标的数据样例，增强 cs_rank 的实际效力；
  - epsilon 默认 1e-6 对浮点抖动较严格，必要时在 CI 环境按数据规模做分层阈值。