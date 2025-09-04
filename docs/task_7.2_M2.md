# TUI 6.0 M2：P1 Dashboard 骨架（事前任务设计）

## 1. 任务目标
- 交付“统一 Dashboard”四区骨架（侧栏/主区/右监控/底日志）与路由切换；与既有 CLI/API/工件完全兼容。
- 不改变现有行为与参数；仅做可视层与调度层的最小增强；保留旧 Tab 模式（F2 切换）。

## 2. 范围边界（禁止过度设计）
- 仅实现 TUI 布局、路由与联动，严格复用 `qraft.tui` 现有模块：`forms.py`、`panels.py`、`recipes.py`、`launcher.py`。
- 不新增后台服务、守护进程、长连接；不引入新依赖。`prompt_toolkit` 如未安装自动回退。
- 数据来源仅读取 `artifacts/` 现有工件与 `_status.json`、`stdout/stderr` 等文件；不新增写路径。

## 3. 功能需求
- 四区布局：
  - 左侧导航（Flows/Tasks 快捷入口，灰态映射未实现功能）。
  - 中部主工作区（表单/详情/报表占位）。
  - 右侧监控栏（最近运行、状态徽章、活性校验结果）。
  - 底部日志尾巴（选中 run 的 stdout/stderr tail）。
- 路由切换：F2 在 Dashboard 与旧 Tab 模式间切换；命令行 `--dashboard` 启动参数。
- 表单增强：如安装 `prompt_toolkit`，提供路径补全/存在性校验、枚举/布尔选择器、数值步进、日期快捷；否则回退基础 input。
- Dry-run 预览：展示将要执行的 CLI 参数串（安全转义），确认后执行。
- 联动：监控区选择 run → 主区打开详情，底部日志尾巴同步。
- 帮助与空态：`?` 打开键位帮助；列表空态显示“如何开始”。

## 4. 技术选型与复用
- 终端渲染：`rich`（既有），可选 `prompt_toolkit`（存在即用）。
- 日志/工件读取：标准文件 I/O；tail 采用节流轮询（0.5–2s）。
- 不新增第三方库；不改变 `qraft/cli.py` 入口契约（仅新增可选参数）。

## 5. 模块与接口
- `qraft/cli_impl/tui_cmd.py`：新增 `--dashboard` 参数与主路由；F2 切换。
- `qraft/tui/panels.py`：新增/复用组件（运行列表、状态徽章、日志尾巴）。
- `qraft/tui/forms.py`：增强 PT 能力（路径补全、选择器、历史、Dry-run 预览）。
- `qraft/tui/launcher.py`：统一 run 执行与 Dry-run 渲染。
- `qraft/tui/recipes.py`：提供最近使用与预设，填充表单默认值。

## 6. 数据与状态
- 读取：`artifacts/{run_id}/_status.json`、`stdout`、`stderr`、`search/aggregated.json` 等（只读）。
- 活性校验（本机）：当 `_status.json` 含 `pid`、`host`、`last_heartbeat_ts` 时，检测本机进程是否存在；无心跳且进程消失超阈值标记为 `zombie`（可疑）。
- 轮询节流：监控/日志默认 0.5–2s；每次 tail N 行（默认 100）。

## 7. 开发任务分解（对齐 TUI6.0_task_list M2）
1) 布局与路由：四区布局、`--dashboard`、F2 切换。
2) 侧栏 Flows：映射 Data→Features→Strategy→Search→Backtest→Portfolio→Risk→Reports→Pool→Deploy→Monitor（未实现项灰态）。
3) 主区表单：PT 增强 + Dry-run 预览；无 PT 回退基础输入。
4) 右侧监控：最近运行列表 + 状态徽章 + 活性校验。
5) 底部日志尾巴：选中 run 的 stdout/stderr tail（暂停/展开更多）。
6) 帮助与空态：键位帮助与引导。

## 8. 验收标准
- 单屏四区同屏呈现，并实现“监控选中 run → 主区详情 + 底部日志联动”。
- 活性校验：可识别 `zombie`（仅在 pid/host 存在、本机进程消失且心跳超时）。
- 表单体验：路径补全/存在性校验、枚举/布尔/数值/日期选择器、历史默认值；Dry-run 可用。
- 兼容性：未安装 PT 或文件缺失时界面不崩溃，功能回退可用。
- 不修改既有 CLI 参数/工件约定；无新依赖。

## 9. 风险与回退
- PT 不可用：自动回退基础输入；Dashboard 仍可运行。
- 活性误判：严格判定条件，边界维持 running 并提示“未确认”。
- 大文件/高频刷新：tail 与监控节流；提供暂停与“展开更多”。

## 10. 里程碑与时间预估
- 实现周期：1–2 周；本阶段目标为“骨架 + 联动 + 回退”。

---

## 任务执行与验收记录（事后更新）
- 实际实现清单：
  - 新增 `render_dashboard`（`qraft/tui/panels.py`），四区布局合成输出；右侧迷你监控与底部日志尾巴联动。
  - 扩展 `tui_cmd`：`--dashboard` 启动、F2 切换、Flows 映射（Strategy/Search/Backtest/Monitor 可用，其余灰态），Dashboard 交互循环（数字选 Flow、`s<idx>` 选 run、`l` 增加日志行、`t` 转 Tasks）。
  - 表单增强（`qraft/tui/forms.py`）：接入 `prompt_toolkit.PathCompleter` 路径补全；所有路径型输入支持补全与存在性校验；Preview 渲染保持不变。
  - 监控与日志：复用 `list_recent_runs` 活性校验与 `_status.json` 读取；日志 tail 采用本地文件读取，带节流与行数上限。
  - 兼容回退：Rich/PT 缺失时在 header/Plain 模式显示降级提示；Rich/PT 缺失不阻塞功能。
- 单测/自测要点：
  - `qraft cli tui --non-interactive --dashboard` 输出包含 Dashboard 标识与键位帮助；Rich 存在时稳定渲染。
  - Forms 路径补全在安装 PT 环境下可用；未安装时不影响交互。
  - Flows 打开 Strategy/Search/Backtest 表单后生成 Preview 串并可执行；执行后可在 Monitor 中看到新 run，并选择查看日志尾巴。
- 发现问题与修复：
  - 非交互模式按兼容策略仅渲染 Home；Dashboard 完整交互在交互模式下体验，已补充键位提示与快速选择。
- 验收结论：
  - 达成 M2 骨架目标：四区布局、路由切换、Flows 映射、表单增强、监控与日志联动均已实现；未新增依赖；与既有 CLI/工件兼容。

---

## 反思与改进建议（针对用户反馈）
- TUI是否完备可用：
  - 当前为“骨架”版，已可用但未达最佳体验；已补充顶部键位帮助、索引选择、状态着色与降级提示，交互路径更直观。
- 功能盲区自检（Qraft CLI 已有但 TUI 未接入）：
  - 已接：validate/quickbacktest/precisebt/run/gridsearch/search/monitor。
  - 未接：batch、optimize、riskctrl、pool、deploy、evidence、golden、deps（仍在侧栏灰态）。
  - 计划：按 TUI6.0_task_list 的 M3/M4 逐步引入，保持不越权假设开发。
- 以开发者视角：TUI 应至少提供
  - 已有 CLI 的可视表单与 Preview、最近运行与活性校验、日志尾巴、快速流转（Search→Backtest→Reports）、键位帮助、降级提示。
- 以用户视角：更高体验的改进点（不超范围）
  - 右侧监控支持筛选与分页（已添加），状态颜色、进度条、指标卡片（M3）；
  - 主区针对“Backtest/Reports”提供最小指标概览与工件跳转（M3），Artifacts 只读浏览（M3）；
  - 远端只读监控（如已有 metrics），仅展示不引入后台（M3）。
