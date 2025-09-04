# Task 3.2：风险管理与控制（Pre-Design）

## 目标与范围
依据 task_list.md“任务3.2：风险管理与控制”，在不重复造轮子的前提下，基于现有优化与约束层，补齐事前风险控制与分析工具：
- 事前风险控制（VaR/ES 上限与缩放策略）。
- 杠杆与仓位上限控制（总杠杆L1、单票上限）。
- 波动率目标（Target Volatility）与动态缩放。
- 行业/风格中性化（等式暴露约束下的最小偏离调整）。
- 单票风控与集中度限制（cap & redistribute）。
- 风险归因分析工具（方差/波动贡献、因子/行业暴露贡献）。

非目标（本阶段不做）：
- 不实现全量复杂风险度量族（如 EVaR、CDaR 等）的求解器级优化，仅提供事前校验与缩放；若需将 CVaR 作为优化目标/硬约束，在后续“方法=cvar”时接入 Riskfolio-Lib。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/index.html" index="2">2</mcreference>
- 不引入非凸/整数类配置（如持仓数量精确上限）超过最小可行范围。

## 外部库与参考
- Riskfolio-Lib：覆盖 CVaR 等风险度量与多种优化模型，为后续扩展提供路径；当前阶段仅在文档与接口设计上预留对接点。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/index.html" index="2">2</mcreference> <mcreference link="https://pypi.org/project/Riskfolio-Lib/" index="1">1</mcreference>
- Expected Shortfall/Conditional VaR（ES/CVaR）定义参考：在最坏 α 分位场景下的平均损失；常用于替代 VaR 的一致性度量。<mcreference link="https://en.wikipedia.org/wiki/Expected_shortfall" index="5">5</mcreference>

## 与 Qraft 设计思想一致性
- 充分复用既有 API：优化阶段继续使用 PyPortfolioOpt 与现有 ConstraintSet；风险控制作为“后处理钩子”，保持解耦与可插拔。
- 简化求解：能通过简单缩放/投影得到的控制，不引入复杂解算；确需等式约束时，使用 CVXPY 最小二乘偏移求解，遵循凸性最佳实践。
- 可复现与审计：风险控制的输入（限额/目标、估计参数）、输出（缩放因子、告警）纳入审计工件，与 Task 2.4 对接。

## I/O 契约
输入：
- 权重向量 w（pd.Series, index=tickers）。
- 历史收益或协方差（returns: pd.DataFrame 或 cov: pd.DataFrame）。
- 风险控制配置（RiskControlConfig 或等价 dict）。
- 可选暴露矩阵（行业/风格等，DataFrame index=factors, columns=tickers）。

输出：
- 调整后的权重 w_ctrl（pd.Series）。
- 风险度量与缩放日志（dict：包括当前 VaR/ES/Vol、缩放因子、触发项、是否达标）。

## 模块与文件交付
- <mcfile name="controls.py" path="/home/dell/Projects/Qraft/qraft/risk/controls.py"></mcfile>
  - 事前控制函数：VaR/ES 计算、波动目标缩放、L1 杠杆上限、单票上限、行业/风格中性化投影、统一管道 apply_risk_controls。
- <mcfile name="attribution.py" path="/home/dell/Projects/Qraft/qraft/risk/attribution.py"></mcfile>
  - 风险归因：方差/波动贡献（RC/MC）、因子或行业暴露贡献（B w）。
- 风险管理配置模板：包内模板 qraft/risk/templates/*.json，并暴露加载工具（与 portfolio 模块一致）。

## API 设计（草案）
- RiskControlConfig（核心字段）
  - alpha: float=0.05（VaR/ES 分位）
  - var_limit: Optional[float]（单期 VaR 上限；以损失比例正数表示）
  - es_limit: Optional[float]（单期 ES 上限）
  - vol_target: Optional[float]（年化波动目标，如 0.15）
  - gross_leverage_cap: Optional[float]（∥w∥_1 上限）
  - max_weight: Optional[float]（单资产权重上限）
  - frequency: int=252（年化因子，波动目标用）
  - neutralize: dict = {"industry": bool, "style": bool}（若提供对应暴露矩阵，则启用等式中性化）
- controls：
  - compute_var_es(returns, w, alpha) -> {"var", "es"}
  - target_volatility(w, cov|returns, target, frequency) -> (w_scaled, info)
  - cap_gross_leverage(w, cap) -> (w_scaled, info)
  - cap_max_weight(w, cap) -> (w_capped, info)
  - neutralize_weights(w, exposures, targets=None, budget=None, bounds=None) -> (w_proj, info)
  - apply_risk_controls(w, returns|cov, exposures?, config) -> (w_ctrl, log)
- attribution：
  - risk_contributions_variance(w, cov) -> Series（RC_i，使和为组合方差）
  - marginal_risk_contributions_vol(w, cov) -> Series（对组合波动的边际贡献）
  - exposure_attribution(w, exposures) -> Series（各因子/行业暴露）

## 关键实现策略
- VaR/ES：采用历史法估计组合单期收益分布，计算 VaR=−q_α，ES=最坏 α 分位平均损失；如超过限额，按比例缩放权重，保留现金头寸。<mcreference link="https://en.wikipedia.org/wiki/Expected_shortfall" index="5">5</mcreference>
- 波动目标：基于协方差估计 σ_p=√(wᵀΣw) 年化；若 σ_p>target，按 target/σ_p 比例缩放权重（不加杠杆）。
- 杠杆与集中度：∥w∥_1 超限则等比例缩放；单票上限采用 cap-and-redistribute（对未触顶资产按原占比重分配剩余预算）。
- 中性化：若给定暴露矩阵 B 及目标 b（默认 0），求解 min ∥w′−w∥₂² s.t. B w′=b, 1ᵀw′=1（可选加入简单边界），使用 CVXPY 求解凸二次规划。
- 归因：方差贡献 RC_i = w_i·(Σw)_i，分解到资产；波动边际贡献 MC_i = (Σw)_i / σ_p；因子/行业暴露直接为 B w。

## 验收标准
功能性：
- 提供统一入口 apply_risk_controls，实现上述 5 类控制与组合日志输出；空缺项不生效但不报错。
- 提供归因计算函数（方差/波动/暴露）。
工程性：
- 新模块 qraft/risk 可独立导入；模板加载函数与 portfolio 模块风格一致。
- 与既有优化模块解耦，可在优化结果后直接调用。
- 文档：本文件作为设计说明，完工后补充“实现与总结”。

## 测试计划（最小用例）
- 构造 5-10 支资产的历史收益，随机权重：
  - VaR/ES：设置小限额，验证缩放因子 < 1 且组合 VaR/ES 降至限额以内。
  - 波动目标：设置 target 小于当前波动，验证缩放后年化波动接近 target。
  - L1 杠杆与单票：构造越界权重，验证缩放和 cap-and-redistribute 正确性（和为预算，个体上限满足）。
  - 中性化：给定行业 one-hot 暴露，验证投影后 B w′≈0 且偏离最小。
  - 归因：验证 RC 求和等于组合方差；暴露归因等于 B w。

---

# 实施与总结（Post-Implementation）

本次已完成如下实现并通过测试：
- 新增模块 <mcfile name="controls.py" path="/home/dell/Projects/Qraft/qraft/risk/controls.py"></mcfile> 与 <mcfile name="attribution.py" path="/home/dell/Projects/Qraft/qraft/risk/attribution.py"></mcfile>，并在 <mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/risk/__init__.py"></mcfile> 暴露 API；根包 <mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/__init__.py"></mcfile> 同步导出。
- 事前风险控制：
  - 历史法 VaR/ES 计算 compute_var_es，支持 α 分位；apply_risk_controls 中按限额比例缩放。
  - 目标波动率 target_volatility（基于协方差；不加杠杆，仅向下缩放）。
  - 总杠杆上限 cap_gross_leverage（∥w∥₁ 超限等比例缩放）。
  - 单票上限 cap_max_weight（CVXPY 最小二乘投影，保持预算与边界）。
  - 行业/风格中性化 neutralize_weights（CVXPY 等式约束最小偏离，支持预算与可选边界）。
  - 统一管道 apply_risk_controls：按“杠杆→单票→中性化→波动目标→VaR/ES”顺序应用并产生日志。
- 风险归因：
  - 方差贡献 risk_contributions_variance，边际波动贡献 marginal_risk_contributions_vol。
  - 暴露归因 exposure_attribution（B w）。
- 模板：新增 <mcfile name="basic_conservative.json" path="/home/dell/Projects/Qraft/qraft/risk/templates/basic_conservative.json"></mcfile>，并提供 list_risk_config_templates / load_risk_config_template。
- 打包配置：在 <mcfile name="pyproject.toml" path="/home/dell/Projects/Qraft/pyproject.toml"></mcfile> 增加 qraft.risk 模板文件包含。
- 测试：新增 <mcfile name="test_risk_controls.py" path="/home/dell/Projects/Qraft/tests/unit/test_risk_controls.py"></mcfile>，覆盖 VaR/ES 缩放、目标波动、L1 杠杆、单票上限投影、中性化投影、归因与模板加载。完整测试套件已全部通过。
- CLI：在 <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile> 新增 `riskattr` 子命令，支持权重 + 协方差/收益（可选因子暴露）输入，输出文本或 JSON（便于流水线集成）。

限制与后续建议：
- VaR/ES 采用历史法单期估计；若需多期路径与更稳健估计，建议引入长窗口/重采样或使用 Riskfolio-Lib 的 CVaR 优化器。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/index.html" index="2">2</mcreference>
- 单票上限与中性化依赖 CVXPY；若环境缺失将跳过相关测试，但运行时需给出清晰错误信息（已在代码中处理）。
- 当前不做加杠杆的波动目标（只下调风控）；如需“波动目标+杠杆”策略，可在管道外部自行放大现金配比。

验收自检：
- 需求覆盖：事前 VaR/ES、杠杆/单票、波动目标、中性化、归因与模板，均已落地并提供统一入口。
- 工程规范：新模块解耦、API 与 portfolio 模板工具保持一致，单元测试通过。

结论：本任务按规划完成并通过自检，如后续需要扩展到 CVaR/EDaR 等更复杂约束与目标，可在不破坏现有 API 的情况下对接 Riskfolio-Lib。<mcreference link="https://riskfolio-lib.readthedocs.io/en/latest/index.html" index="2">2</mcreference>