我将快速扫描你本地的 `RD-Agent` 源码，定位是否存在对 `qlib` 的硬依赖、耦合点与可替换接口；并并行查看 `README.md`、`requirements.txt`、`pyproject.toml` 与代码中关于量化/回测集成的模块，随后给出能否脱离 `qlib` 与如何集成入 `Qraft 4.0` 的建议。接下来开始读取与检索。

我已深入阅读你本地 `RD-Agent` 仓库并检索了核心代码路径，结论与证据如下。

### 结论（直答）
- 第一：RD-Agent 可以脱离 Qlib，不被 Qlib 深度绑定。Qlib 只是 RD-Agent 中“量化场景”的一个适配实现，RD-Agent 的核心框架（场景/提案/开发/运行/反馈/Loop）是通用的。项目并未在全局依赖中强制引入 Qlib，而是在 Qlib 场景的环境封装里按需安装/调用。
- 第二：可以。按 `plan4.0.md` 的“无模型、规则/因子组合驱动”路线，建议以“新场景插件”的方式引入 RD-Agent：重用其 R/D 螺旋闭环与多代理能力，用我们自己的回测/成本/稳健性栈（vectorbt + Nautilus + 成本敏感性/多重检验）替换 Qlib 场景即可。

### 关键证据（源码）
- Qlib 仅作为“场景”依赖，被局部化在 Qlib 场景与环境封装中；不是全局强依赖
```654:701:/home/dell/Projects/Qraft/RD-Agent/rdagent/utils/env.py
class QlibCondaConf(CondaConf):
    conda_env_name: str = "rdagent4qlib"
...
                subprocess.check_call(
                    f"conda run -n {self.conf.conda_env_name} pip install git+https://github.com/microsoft/qlib.git@3e72593b8c985f01979bebcf646658002ac43b00",
                    shell=True,
                )
...
class QlibDockerConf(DockerConf):
...
    dockerfile_folder_path: Path = Path(__file__).parent.parent / "scenarios" / "qlib" / "docker"
    image: str = "local_qlib:latest"
    mount_path: str = "/workspace/qlib_workspace/"
    default_entry: str = "qrun conf.yaml"
```
- Qlib 工作空间的执行就是“qrun conf.yaml”，可被同构的自定义工作空间替换
```18:35:/home/dell/Projects/Qraft/RD-Agent/rdagent/scenarios/qlib/experiment/workspace.py
    def execute(self, qlib_config_name: str = "conf.yaml", run_env: dict = {}, *args, **kwargs) -> str:
        if MODEL_COSTEER_SETTINGS.env_type == "docker":
            qtde = QTDockerEnv()
        elif MODEL_COSTEER_SETTINGS.env_type == "conda":
            qtde = QlibCondaEnv(conf=QlibCondaConf())
...
        execute_qlib_log = qtde.check_output(
            local_path=str(self.workspace_path),
            entry=f"qrun {qlib_config_name}",
            env=run_env,
        )
```
- CLI 同时支持 Qlib 场景与通用数据科学场景（后者与 Qlib 无关）
```64:71:/home/dell/Projects/Qraft/RD-Agent/rdagent/app/cli.py
app.command(name="fin_factor")(fin_factor)
app.command(name="fin_model")(fin_model)
app.command(name="fin_quant")(fin_quant)
app.command(name="fin_factor_report")(fin_factor_report)
app.command(name="general_model")(general_model)
app.command(name="data_science")(data_science)
```
- README 直接暴露 Qlib 场景命令，但它只是众场景之一
```255:269:/home/dell/Projects/Qraft/RD-Agent/README.md
- Run the **Automated Quantitative Trading & Iterative Factors Model Joint Evolution**:  [Qlib] ...
  rdagent fin_quant
- Run the **Automated Quantitative Trading & Iterative Factors Evolution**:  [Qlib] ...
  rdagent fin_factor
- Run the **Automated Quantitative Trading & Iterative Model Evolution**: [Qlib] ...
  rdagent fin_model
```

### 如何按 plan4.0 集成到 Qraft（最小侵入）
- 新增“Qraft 无模型场景”而非改 Qlib 场景
  - `QraftRuleScenario`：提供规则/DSL接口、输出格式与模拟器描述（替代 `QlibQuantScenario`）。
  - `QraftFBWorkspace`：执行 vectorbt 快扫与 Nautilus 精撮，产出统一制品（如 `equity.pkl`、`metrics.csv`、“成本敏感性/Top-N重叠率曲线”）。
  - `RuleCoder/RuleRunner`：把 LLM 产出的规则 DSL 编译为回测脚本并运行。
  - `Experiment2Feedback`：读取指标/曲线，生成稳健性反馈（支持 DSR/Reality Check/Top-N 重叠率/成本±50%）。
- 复用 RD-Agent 的“提案→开发→运行→反馈→循环”骨架
  - 直接沿用 `RDLoop` 与 `BasePropSetting`，增加 `QraftPropSetting` 指向上述新类。
  - 添加新 CLI 命令（例如 `rdagent qraft_rules`），或用环境变量将现有入口指向 Qraft 场景。
- 与 plan4.0 的一致性
  - 无模型：只走“因子/规则→信号→回测→稳健性→策略池”链路（可直接用 factor-only 路径作为模板）。
  - 成本/稳健性：在 summarizer 层固化“成本敏感性曲线+Top-N 重叠率+跨期验证+DSR/SPA”。

### 实施优先级（按工作量低→高）
- P0（1–2 天）：新建 `QraftFBWorkspace`（vectorbt 执行）、`QraftRuleScenario`（接口与输出），在 CLI 暴露入口，先打通“规则→vectorbt 粗回测→反馈”闭环。
- P1（2–4 天）：接入 Nautilus 精撮、成本模型包（点差+冲击+延迟）、输出敏感性曲线与 Top-N 重叠率曲线。
- P2（3–5 天）：补多重检验（DSR/Reality Check/SPA）、策略去重与资金分配（等权/目标波动率/风险平价）、灰度与审计包。

### 风险与注意
- RD-Agent 的现有量化命名多带 “qlib” 前缀（如 env_prefix），建议新建独立的 `Qraft*` Setting/Scenario，避免语义混淆。
- 需要一份规范的“规则/DSL”与固定输出制品协议，便于审计与可复现。
- 许可证：RD-Agent MIT，可安全集成；Qlib 亦为 MIT，不构成阻碍。

- 我已在你本地仓库完成代码级核查，确认 RD-Agent 对 Qlib 仅限于“场景实现”，并提供了基于 `plan4.0.md` 的可执行集成方案（新场景+新工作空间），无需被 Qlib 绑定。