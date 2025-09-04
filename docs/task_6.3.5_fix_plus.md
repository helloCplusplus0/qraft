# Task 6.3.5 Fix Plus — deploy precheck：精撮依赖可用时默认走 e2e 精撮 vs 快速对比；不可用时保留友好提示

本次完善目标
- 在部署前检查（deploy precheck）中，当 Nautilus Trader 依赖可用时，默认执行“精撮（Nautilus 引擎 e2e）与快速（vectorbt）”的结果对比；当依赖不可用时，提供明确、友好的提示信息。
- 严格遵循“充分利用现有 API，避免过度/重复设计”。

落地实现（最小增量，复用现有模块）
1) 入口：CLI 子命令 deploy precheck
- 逻辑集中于 qraft/cli_impl/deploy_cmd.py 的 _cmd_deploy_precheck：
  - 统一从策略 JSON 与价格 CSV 构建 price_df 与二值化信号（与已有 CLI 一致）。
  - 快速通道：使用 VectorbtAdapter.run 计算 quick 结果。
  - 精撮通道：在运行前先进行 importlib.import_module("nautilus_trader.backtest.engine") 检查；成功后通过 NautilusAdapter.run 执行 e2e 精撮路径（默认严格模式，直达引擎链路）。
  - 依赖缺失或精撮不可达时，将异常统一包装为 QraftError(ErrorCode.DEPENDENCY_MISSING) 并携带友好提示，避免栈追踪污染用户界面。
  - 两通道结果交由 GrayscaleDeployer.precheck 进行一致性门槛判定，并按 --fmt 输出。

2) 精撮执行路径选择与严格性
- NautilusAdapter.run 在 engine_config 缺省时即默认走 "engine" 模式，并在进入前显式检查 nautilus_trader 依赖；因此 deploy precheck 的精撮通道天然是 e2e 引擎路径，无需额外参数。
- 保持严格模式（strict=True），如果引擎执行出错，将抛出异常，由外层捕获并给出友好提示；在 deploy precheck 中不启用开发回退（hold-cash），以确保对比有效性。

3) 质量门：一致性对比
- GrayscaleDeployer.precheck 调用 enforce_pool_quality 进行 quick 与 precise 的一致性度量与门槛判断，返回结构化结果（passed 与 details），统一由 CLI 打印。

行为验证（手动自测指南）
- 依赖可用场景（已安装 nautilus-trader）：
  - 命令：
    qraft deploy precheck --strategy examples/strategy.json --prices examples/prices.csv --fmt text
  - 预期：先运行快速回测，再运行 e2e 精撮回测，输出一致性门控结果（passed 与细节）。
- 依赖不可用场景（未安装 nautilus-trader）：
  - 同上命令。
  - 预期：快速回测完成；精撮通道在依赖检查时报错，但以 QraftError(ErrorCode.DEPENDENCY_MISSING) 的形式返回友好提示信息（包含 pip 安装建议），并以非零退出码结束。

关键变更点（本次为“确认与巩固”）
- 复核 deploy precheck 的实现：已满足“依赖可用时默认 e2e 精撮 vs 快速对比；不可用时保留友好提示”的要求，无需新增设计与参数；保持最小增量与一致的错误模型。
- 明确并记录了 NautilusAdapter 在 engine_config 缺省时默认走 e2e 引擎路径的约定，避免误用 MVP 路径导致的对比失真。

影响评估
- 对外部 API 与 CLI 行为无破坏性改动。
- 友好提示在依赖缺失时更加清晰且结构化（QraftError + ErrorCode.DEPENDENCY_MISSING）。
- 保持严格模式下的失败即显错，避免在部署前检查阶段因 silent fallback 误导判断。

复用与依赖
- 快速回测：VectorbtAdapter（既有实现）。
- 精撮回测：NautilusAdapter（默认 engine 模式） → nautilus_engine.run_precise（构建与运行 Nautilus 引擎）。
- 一致性门：GrayscaleDeployer.precheck → enforce_pool_quality（既有实现）。

使用提示
- 如需开启开发态容错（非本 precheck 场景），可在其他入口（如 UnifiedRunner）通过 allow_fallback_dev 控制；deploy precheck 保持严格以确保对比有效性。

附：相关文件
- qraft/cli_impl/deploy_cmd.py：部署前检查子命令实现
- qraft/deployment/grayscale.py：灰度部署器与 precheck 门控
- qraft/engines/nautilus_adapter.py：精撮适配器（默认 e2e 引擎路径）
- qraft/engines/nautilus_engine.py：精撮引擎桥接（依赖检查、构建与运行）

结论
- 本任务按“充分利用现成 API、禁止过度/重复设计”的约束完成落地：当精撮依赖可用时默认执行 e2e 精撮与快速对比；不可用时以统一、友好的提示信息返回，便于用户按需安装依赖后重试。