# Task 7.2 – M0 基线确认与接口清单（Pre-Task Design）

目标与范围（对应 docs/TUI6.0_task_list.md L9–14）：
- 清点现有 CLI/任务入口、TUI 面板与工件（artifacts）。
- 输出 TUI → CLI 参数映射对照表（不新增/不改变现有参数）。
- 定义 Dashboard 路由开关（保留旧 Tab 模式）。
- 坚持“最小可用、严格复用现有能力、禁止假设开发、禁止过度设计”。

一、现状基线清点
1) CLI 任务入口（来自 qraft/cli.py）
- 子命令清单（节选与本任务相关）：tui、validate、ops、quickbacktest、precisebt、run、gridsearch、search run、optimize、batch、riskattr、riskctrl、quality、golden、evidence、pool、deploy、deps。
- TUI 子命令已存在，参数：--plain、--non-interactive、--monitor-url（映射至实现）。
- 参考：文件 qraft/cli.py 中 _build_parser() 的子命令注册。

2) TUI 相关实现
- 主循环入口：qraft/cli_impl/tui_cmd.py 的 _tui_loop 与 _cmd_tui。
- 面板：qraft/tui/panels.py 提供 render_home、render_tasks、render_run、render_monitor、sample_resources 等。
- 表单与参数构建：qraft/tui/forms.py，包括 build_run_argv、build_validate_argv、build_quickbacktest_argv、build_precisebt_argv、build_gridsearch_argv、build_search_run_argv 以及对应 prompt_* 函数。
- 运行发起器：qraft/tui/launcher.py，定义 run_local、gen_run_id、ensure_artifacts_dir、write_status 等。

3) 工件（artifacts）规范（以现有代码为准）
- 目录：artifacts/{run_id}/
- 状态文件：{run_id}_status.json（包含 run_id/state/started_at/finished_at/exit_code/elapsed）。
- 日志文件：{run_id}.log（run_local 写入，包含带 [stdout]/[stderr] 前缀的行）。
- 备注：未发现 _status.json 或 aggregated.json 的现成实现，严格以现有实现作为规范基线。

二、TUI → CLI 参数映射（以现有实现为准）
- run → qraft run：由 forms.build_run_argv 生成参数。
- validate → qraft validate：由 forms.build_validate_argv 生成参数。
- quickbacktest → qraft quickbacktest：由 forms.build_quickbacktest_argv 生成参数。
- precisebt → qraft precisebt：由 forms.build_precisebt_argv 生成参数。
- gridsearch → qraft gridsearch：由 forms.build_gridsearch_argv 生成参数。
- search（run）→ qraft search run：由 forms.build_search_run_argv 生成参数。
- 说明：不新增、不改变任何既有 CLI 参数，仅复用。

三、Dashboard 路由开关定义（M0 输出）
- CLI 开关：为 qraft tui 增加 --dashboard 布尔开关，仅表示以 Dashboard 模式启动；不改变既有参数。
- 运行时切换：在 _tui_loop 增加 start_dashboard 参数与 runtime 开关变量 dashboard_mode；允许在交互界面通过输入“f2”进行切换（当前交互基于 input() 行模式，先以字符串“f2”替代真实 F2 按键）。
- 保留旧 Tab 模式：默认维持现有 Home/Tasks/Run/Monitor 菜单与渲染。
- M0 范围内仅提供开关与占位展示（例如在 Home 顶部增加“Dashboard mode: ON/OFF”提示），不构建 Dashboard 布局骨架（骨架将在 M2 实现）。

四、实现计划（最小变更）
- 在 qraft/cli.py 的 tui 子命令添加 --dashboard，并传递给实现。
- 修改 qraft/cli_impl/tui_cmd.py：
  - _tui_loop(force_plain, non_interactive, monitor_url, start_dashboard=False)
  - _cmd_tui(plain, non_interactive, monitor_url, dashboard=False) → 传入 _tui_loop
  - 主循环中维护 dashboard_mode（初值为 start_dashboard），主菜单与 Monitor 子菜单均支持输入“f2”切换；non-interactive 模式下若指定 --dashboard，仅渲染一次并退出（保持与现有 non-interactive 语义一致）。
- 不新增任何外部依赖，不改动现有表单和面板能力。

五、验收标准（M0）
- 命令 qraft tui --non-interactive 正常输出，与变更前行为一致。
- 命令 qraft tui --dashboard --non-interactive 正常输出，且包含“Dashboard mode: ON”或等效提示。
- 交互模式：启动 qraft tui 后，可输入 f2 切换 Dashboard/Tab 模式，切换后提示更新。
- 不破坏既有 CLI/TUI 的参数与行为；不新增假设的 artifacts 结构。

六、风险与边界
- 当前交互读取为 input()，暂以“f2”作为切换输入，后续若集成 prompt_toolkit 再支持真实功能键。
- Dashboard 仅建立路由与占位提示，不提供新布局与联动（按 M2 计划实现）。

——

实施后将于本文件尾部追加“Post-Implementation Summary（事后总结）”与“Reflection（反思）”。


## M0 实施小结（Post‑Mortem）

本次 M0 实施围绕“新增 TUI Dashboard 路由开关 + 非交互模式提示 + 交互模式切换入口（F2 占位）”完成最小改动集，确保兼容既有行为且便于后续增量扩展。

### 1) 变更概览
- CLI 参数层：在 <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile> 的 `tui` 子命令中新增 `--dashboard` 布尔开关，并将其透传给实现函数（`ctui._cmd_tui`）。
- TUI 实现层：在 <mcfile name="tui_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/tui_cmd.py"></mcfile> 中：
  - `_tui_loop` 新增 `start_dashboard` 入参，作为初始路由开关。
  - 非交互模式下，当传入 `--dashboard` 时输出轻量的“Dashboard 模式提示/占位渲染”，并正常退出（保持单次渲染、无阻塞）。
  - 交互模式下加入“F2”占位切换（当前以输入字符串 `f2` 代表），用于在 Dashboard 与既有面板间切换；后续将替换为真实键位事件绑定。

### 2) 验证记录（命令级）
- 基线验证：`python -m qraft.cli tui --non-interactive` 正常退出（exit code=0），输出包含 Home/Tasks 列表与资源采样（CPU/RSS），确认未引入回归。
- Dashboard 开关验证：`python -m qraft.cli tui --dashboard --non-interactive` 正常退出（exit code=0），输出包含“Dashboard 模式”提示/占位渲染与资源采样信息。
- 测试引用检查：在 `tests/` 下未检出依赖 `tui` 子命令参数的现有用例，新增开关未破坏当前测试面。

### 3) 与验收标准对照
- [x] `qraft tui` 增加 `--dashboard` 开关，默认关闭，不影响旧行为。
- [x] 非交互模式：
  - `qraft tui --non-interactive` 维持旧输出。
  - `qraft tui --dashboard --non-interactive` 输出“Dashboard 模式”提示/占位渲染，并正常退出。
- [x] 交互模式：保留现有路由与渲染；提供 F2（暂以输入 `f2` 代表）切换 Dashboard 的占位入口。

### 4) 风险与限制
- F2 键位绑定为临时实现（以输入 `f2` 代替真实键盘事件），仅用于 M0 可见性验证；后续需接入真实按键事件处理并优化状态提示。
- Dashboard 仅提供占位渲染，不含真实指标/图表；不会改动 `panels.py` 的既有复杂渲染逻辑，避免影响现有体验。
- 非交互模式输出做了最小化提示，确保脚本化场景下可感知开关状态但不改变退出语义。

### 5) 后续工作（M1 建议）
- 将 F2 切换接入真实键盘事件通道，并在界面上显式显示当前模式状态与切换提示。
- 在 <mcfile name="panels.py" path="/home/dell/Projects/Qraft/qraft/tui/panels.py"></mcfile> 中实现真正的 Dashboard 面板（资源/队列/作业/运行状态聚合），复用既有采样与表格渲染工具。
- 与 `launcher.py` 工件约定打通：聚合 `artifacts/{run_id}/` 下的 `_status.json` 与 `.log`，在 Dashboard 汇总最新/进行中任务。
- 增加端到端用例与快照测试，覆盖 `--dashboard` 与非交互/交互两种运行路径。
- 结合 `--monitor-url` 行为，考虑当可用时在 Dashboard 中显示监控端点连通性/状态摘要。

> 注：本次改动严格遵循“先落地，后完美”的原则，仅引入最小开关与占位渲染，确保零破坏与可迭代。