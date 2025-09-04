# Task 3.1：组合优化引擎集成（Pre-Design）

## 目标与范围
依据 task_list.md“任务3.1：组合优化引擎集成”，在不自研复杂求解内核的前提下，集成业界成熟库（PyPortfolioOpt、Riskfolio-Lib），实现均值-方差（MV）、分层风险平价（HRP）、Black–Litterman（BL）三类优化方法；支持常见工程约束（持仓上下限、行业/组约束、仓位合规等）、交易成本感知（对换手惩罚）以及可行域预置与 warm-start，形成可扩展、可测试、可审计的组合优化子系统。

非目标（本阶段不做）：
- 不自研新优化算法及数值求解器；不引入重量级商业求解器适配（可在后续按需加）。
- 不实现完整风险管理体系（移交 Task 3.2）。

## 外部库与关键能力（简要）
- PyPortfolioOpt 提供 EfficientFrontier（均值-方差优化）、HRPOpt（分层风险平价）、BlackLittermanModel（BL 后验收益/协方差估计）等核心能力，且内置与 pandas 友好集成，示例化 API 完整。<mcreference link="https://pyportfolioopt.readthedocs.io/en/latest/" index="5">5</mcreference> <mcreference link="https://pyportfolioopt.readthedocs.io/en/latest/OtherOptimizers.html" index="4">4</mcreference> <mcreference link="https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html" index="1">1</mcreference>
- 使用 expected_returns.mean_historical_return 与 risk_models.sample_cov 可从历史价格快速得到 μ 与 Σ 作为 MV/BL 的输入。<mcreference link="https://pyportfolioopt.readthedocs.io/en/latest/" index="5">5</mcreference>
- Riskfolio-Lib 基于 CVXPY，覆盖 HRP/HERC/NCO 等层次化方法并支持大量风险度量（含 CVaR 系列），可复用其对复杂风险目标和求解器的集成（ECOS/SCS/CLARABEL 等）。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/index.html" index="2">2</mcreference> <mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/hcportfolio.html" index="1">1</mcreference>

## 与 Qraft 设计思想一致性
- 最大化复用现成 API，最小化自研（只做薄封装与契约层）。
- 分层解耦：优化器封装层与约束/配置层分离；对上暴露统一 Optimizer 接口；对下可插拔选用 PyPortfolioOpt 或 Riskfolio-Lib。
- 可复现与审计：输入（价格/收益、配置、约束、warm-start 状态）与输出（权重、目标值、约束对偶信息如可获得）纳入审计工件，兼容 Task 2.4 的审计包机制。

## 输入与输出（I/O 契约）
输入：
- 资产价格序列或收益序列（pd.DataFrame, index=Date, columns=Tickers）。
- 优化方法："mv" | "hrp" | "bl"（后续可扩展为 "cvar", "herc", "nco" 等）。
- 约束配置：权重上下限、行业/组约束、总仓位/杠杆、净/多空杠杆、持仓数量上限（可选，尽量保持凸性）、禁买清单等。
- 交易成本参数：换手惩罚系数、基于上期权重 w_prev 的 L1/L2 罚项参数等。
- BL 专用参数：先验（市场隐含或自定义）、观点 Q/P/Ω、τ 等。
- 求解器与容错：solver 选择与 solver_options，最大迭代/容忍度，warm_start 开关。

输出：
- 权重向量（OrderedDict[str, float] 或 pd.Series）。
- 组合绩效估计（预期收益、波动/风险度量、Sharpe 等，按所选方法可用项返回）。
- 约束执行日志与可能的不可行诊断（若可获得）。

## 模块与文件交付
- <mcfile name="optimizers.py" path="/home/dell/Projects/Qraft/qraft/portfolio/optimizers.py"></mcfile>
  - 统一调度封装：MV/HRP/BL 三类优化方法；可选后续扩展（CVaR/HERC/NCO）。
  - 与 PyPortfolioOpt/Riskfolio-Lib 的桥接适配（根据 method 选择后端）。
- <mcfile name="constraints.py" path="/home/dell/Projects/Qraft/qraft/portfolio/constraints.py"></mcfile>
  - 约束与目标的声明式配置（dataclass）；
  - 约束应用器：将通用约束映射到具体后端（PyPortfolioOpt.add_constraint / Riskfolio 参数）。
- 组合优化配置模板：已迁移为包内模板（qraft/portfolio/templates/），并提供轻量加载函数（见“实现总结”）。

## API 设计（草案）
- 顶层入口（示意）：
  - optimize_portfolio(prices: pd.DataFrame | returns: pd.DataFrame, method: str, config: PortfolioConfig, constraints: ConstraintSet, prev_weights: Optional[pd.Series] = None) -> OptimizationResult
- PortfolioConfig（核心字段）：
  - method: "mv"|"hrp"|"bl"
  - risk_free_rate, frequency, weight_bounds=(0,1)
  - cov_method: "sample"|"shrinkage"（先仅支持简单法）
  - solver: Optional[str]（如 "ECOS"/"SCS"/"CLARABEL"；透传给底层）
  - solver_options: Dict[str, Any]
  - trans_cost: TransactionCostConfig = None（turnover 惩罚）
  - bl: BLConfig = None（仅 method=="bl" 生效）
- ConstraintSet（常用约束）：
  - bounds（全局与逐资产）、budget（sum(w)=1 或 其他预算）、leverage、long_short（净/总敞口）
  - group/industry exposure（A w <= b, A_eq w = b_eq），持仓数量上限（近似或软约束）
  - blacklist（w_i=0）
- OptimizationResult：weights, diagnostics（status, solver, obj_value）, perf_estimates

## 方法与后端映射
- MV（PyPortfolioOpt.EfficientFrontier）：
  - μ、Σ由 expected_returns 与 risk_models 计算；调用 max_sharpe / min_volatility / efficient_return 等目标（首期提供 max_sharpe 与 min_volatility）。
  - 约束通过 add_constraint（线性）与 add_objective（L1/L2 正则/换手惩罚）。
- HRP（PyPortfolioOpt.HRPOpt）：
  - 基于收益或协方差直接 optimize() 获取权重；适合规模较大或协方差病态的场景。<mcreference link="https://pyportfolioopt.readthedocs.io/en/latest/OtherOptimizers.html" index="4">4</mcreference>
- BL（PyPortfolioOpt.BlackLittermanModel + EfficientFrontier）：
  - 先用 BL 得到后验 μ̂、Σ̂，再交给 EfficientFrontier 做 MV 优化；支持绝对/相对观点与不确定度 Ω。<mcreference link="https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html" index="1">1</mcreference>
- 高级风险度量（可选增强，Riskfolio-Lib）：
  - 需要 CVaR/EDaR 等广义风险目标时，调用 Riskfolio-Lib 的 Portfolio/HCPortfolio/NCO 等对象，保持相同的 ConstraintSet 到参数映射；原则上仅在“方法="cvar"/"herc"/"nco"”时启用。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/index.html" index="2">2</mcreference> <mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/hcportfolio.html" index="1">1</mcreference>

## 约束与目标的实现策略
- 线性约束：
  - 持仓上下限：bounds 或 add_constraint(w[i] >= li, w[i] <= ui)。
  - 行业/组约束：通过 A w <= b / A_eq w = b_eq 映射；A 由行业暴露矩阵构造。
  - 预算/杠杆：sum(w)=1，||w||_1 <= leverage 等（多空在 Task 3.2 进一步完善）。
- 交易成本感知：
  - 对换手加入惩罚项：λ * ||w - w_prev||_1（或 L2）；在 PyPortfolioOpt 中通过 add_objective 注入 CVXPY 表达式；在 Riskfolio-Lib 中通过相应参数或额外目标项模拟（保持凸性优先）。
- 可行域预置与 warm-start：
  - 通过 solver_options 传递 warm_start=True，复用上期解作初值；对 HRP 这类非凸/启发式方法不强制 warm-start。

## 事务一致性与审计
- 优化调用的输入参数、库版本、求解器/选项、约束配置与输出权重，将以 JSON 形式落盘，并与 Task 2.4 的 EvidencePack/AuditPackage 对接（例如保存 weights.json、optimizer_config.json、constraints.json、diagnostics.json）。

## 验收标准（结合 task_list.md）
功能性：
- 支持 MV、HRP、BL 三种方法，最少覆盖：MV(max_sharpe/min_volatility)、HRP(optimize)、BL(后验→MV)。
- 支持持仓上下限与行业/组约束；预算/杠杆控制；黑名单资产；基本的交易成本感知（基于 w_prev 的 L1/L2 惩罚）。
- 支持 solver 与 solver_options 透传，允许 warm_start。
- 输出权重可靠（和约束一致，数值稳定），提供基础绩效估计（可选）。
工程性：
- 统一 API；配置/约束强类型定义；无过度设计；遵循现有代码风格。
- 单测覆盖：核心路径 + 约束生效 + 交易成本惩罚有效性 + BL 流程；CI 可运行。
- 文档：本文件描述、使用示例与限制说明充分。

## 测试计划（最小可行用例）
- 数据：使用小型玩具数据集（5-20 支，100-500 个交易日）。
- MV：
  - max_sharpe：检查 sum(w)=1、bounds 合规、行业约束合规；与不加交易成本的解相比，加 λ 后换手下降。
  - min_volatility：同上。
- HRP：
  - optimize：输出权重非负且和为 1，权重分散度合理；与 MV 在病态协方差场景下对比稳定性。
- BL：
  - 构造简单绝对观点（两三个资产），检查后验 μ̂ 与 Σ̂ 被使用，产出权重与观点方向一致。
- 容错：
  - 参数缺失/维度不匹配/不可行约束时返回明确错误；
  - solver 不可用时的降级或提示；
  - warm_start 有/无时解的可复现性（随机性受控）。

## 迭代与里程碑
- D1：实现 MV（max_sharpe/min_volatility）+ 线性约束 + 基础交易成本惩罚（L2）。
- D2：接入 HRP（optimize）。
- D3：完成 BL（后验→MV），补充单测。
- D4：完善 warm_start/solver 选项；对接审计落盘；文档收尾。

## 未来可扩展项（非本阶段必做）
- CVaR/EDaR 等复杂风险度量与 Risk Parity（Riskfolio-Lib 路线）。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/index.html" index="2">2</mcreference>
- 组合整数约束（持仓数量上限的精确建模）与分段交易成本（非凸，会引入求解复杂度）。
- 因子暴露约束与跟踪误差目标；指数化复制等自定义目标。

## 使用示例（高层伪代码）
- MV：
  1) 由价格转收益，计算 μ、Σ；
  2) optimize_portfolio(method="mv", config=..., constraints=...);
- HRP：
  1) 由价格转收益或估协方差；
  2) optimize_portfolio(method="hrp", config=..., constraints=...);
- BL：
  1) 准备先验与观点（绝对/相对），得到后验 μ̂、Σ̂；
  2) 将后验传给 MV 优化，得到权重。

## 参考资料
- PyPortfolioOpt 安装与总览、μ/Σ 估计示例、统一 API 示例。<mcreference link="https://pyportfolioopt.readthedocs.io/en/latest/" index="5">5</mcreference>
- PyPortfolioOpt HRPOpt（HRP 优化器）。<mcreference link="https://pyportfolioopt.readthedocs.io/en/latest/OtherOptimizers.html" index="4">4</mcreference>
- PyPortfolioOpt BlackLittermanModel（BL 模型）。<mcreference link="https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html" index="1">1</mcreference>
- Riskfolio-Lib 总览（CVXPY、丰富风险度量与求解器）。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/index.html" index="2">2</mcreference>
- Riskfolio-Lib 层次化组合（HRP/HERC/NCO 与风险度量）。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/hcportfolio.html" index="1">1</mcreference>

---

# Task 3.1：实现总结（Post-Implementation）

本次提交已完成最小可用的组合优化引擎集成：
- 代码交付：
  - <mcfile name="optimizers.py" path="/home/dell/Projects/Qraft/qraft/portfolio/optimizers.py"></mcfile>
  - <mcfile name="constraints.py" path="/home/dell/Projects/Qraft/qraft/portfolio/constraints.py"></mcfile>
  - 新增包入口：<mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/portfolio/__init__.py"></mcfile> 与 <mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/__init__.py"></mcfile>
  - 新增内置模板：<mcfolder name="templates" path="/home/dell/Projects/Qraft/qraft/portfolio/templates"></mcfolder>（mv_basic.json / hrp_basic.json / bl_basic.json）。
  - 公共 API 追加：在包入口新增模板加载工具函数 list_portfolio_config_templates 与 load_portfolio_config_template。
- 功能点：
  - MV（PyPortfolioOpt.EfficientFrontier）：支持 max_sharpe / min_volatility，支持预算、逐资产/全局 bounds、线性行业/组约束、L1 杠杆、换手 L1/L2 惩罚（cvxpy）。
  - HRP（PyPortfolioOpt.HRPOpt）：基于收益 optimize() 产出权重（目前不支持线性约束）。
  - BL（PyPortfolioOpt.BlackLittermanModel + EfficientFrontier）：后验 μ̂/Σ̂ → MV 目标，约束与 MV 一致。
  - 统一入口 optimize(...) 与强类型配置 PortfolioConfig/ConstraintSet。
- 打包与分发：
  - 在 <mcfile name="pyproject.toml" path="/home/dell/Projects/Qraft/pyproject.toml"></mcfile> 中新增 package-data 声明："qraft.portfolio" = ["templates/*.json"]，确保模板随包发布。
- 依赖与兼容：
  - 项目依赖包含 numpy/pandas/scipy/pypfopt/cvxpy；因环境兼容性，单测对 pypfopt/cvxpy 使用 pytest.importorskip 条件跳过。
  - 兼容性修复：移除对 PyPortfolioOpt 不支持的 frequency 参数调用。

使用要点：
- 使用模板：
  - from qraft import load_portfolio_config_template
  - cfg_dict = load_portfolio_config_template("mv_basic.json")
  - 然后将字典映射/构建 PortfolioConfig 并调用 optimize。
- 列举可用模板：
  - from qraft import list_portfolio_config_templates; print(...)
- HRP 不支持线性约束属库特性限制，如需约束化 HRP/HERC，请在后续阶段使用 Riskfolio-Lib 的 HCPortfolio/NCO 方案。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/hcportfolio.html" index="1">1</mcreference>

验收自查（对照“验收标准”）：
- 方法覆盖：MV、HRP、BL 均已实现（满足最低目标）。
- 约束支持：预算、边界、黑名单、线性组约束、L1 杠杆、换手惩罚（L1/L2）已落地；HRP 约束限制已注明。
- 工程性：统一 API + dataclass 配置；依赖声明；模板与加载函数简洁、无重复设计；代码风格符合项目规范。
- 绩效估计：返回 expected_return/volatility/sharpe（若底层可计算）。

已知限制与后续计划：
- Riskfolio-Lib 的 CVaR/EDaR/HERC/NCO 等高阶方法未纳入本阶段实现，将在后续方法标识启用时接入。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/index.html" index="2">2</mcreference>
- HRP 的约束化与交易成本纳入需依赖替代后端或自定义流程。

# 反思（Reflection）
- 与预设计一致：实现范围、方法映射、约束与交易成本策略均按预案完成；未过度设计，优先复用库 API。
- 任务状态：满足本阶段验收标准的“最小可用”，已补充内置模板与加载器，支持更快落地与复用。
- 下一步建议：基于实际场景扩展更多模板（如多空、行业中性、跟踪误差约束变体）与高阶方法接入；完善与 Task 2.4 的审计工件联动。