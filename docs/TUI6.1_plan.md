# Qraft 6.1 TUI（统一 Dashboard v2）设计方案（SSOT + 单帧直绘 + 流程编排）

> 目标：在不新增后端/守护的前提下，严格复用既有 CLI/API/工件，重构 TUI 为“状态驱动 + 单帧直绘 + 统一输入”的单屏操作中台，并内置最小的一键流程编排（可干跑/可执行/可续跑），满足“自动策略探索平台”的交互与可复现要求。

---

## 0. 设计原则（用户优先，最小改动）
- 状态唯一（SSOT）：所有 UI 读取 UIState/RunStore，所有动作只改状态，不直接打印。
- 单帧直绘（Live-only）：仅用 Rich Live 更新一帧布局；无穿插清屏/print；溢出裁剪。
- 统一输入：固定输入栏；默认阻塞读取；有 prompt_toolkit 则增强补全/选择器；无 PT 自动回退。
- 流程编排：以既有 CLI 组合“一键流程”（可干跑/可执行/可续跑），产物落到 artifacts；Main 显示“进度 + 摘要 + 下一步”。
- 零假设开发：不改 CLI 契约、不改工件格式；只做读状态与编排胶水；禁止过度设计。

---

## 1. 布局与交互（单屏操作中台）
- 固定四区：
  - Header：键位/模式/当前 Flow 与 Run 状态。
  - 左侧导航：Flows/Tasks；支持过滤与索引选择。
  - Main：表单/详情/流程进度；空态给出“如何开始”。
  - 右侧监控：Recent Runs（分页/筛选/状态徽章）+ 指标卡（search/evidence）+ 质量门槛卡片。
  - 底部：Log tail（可滚动/分页；后台刷新）。
- 子视图与覆盖层：Tasks/Monitor/Artifacts 作为“覆盖层”在主帧内呈现；返回即恢复；不切屏、不退化 plain。
- 键位：
  - 数字 0..N 选 Flow；`o` 打开子菜单/表单；`s<idx>` 选 Run；`t` 任务；`m` 监控；`a` 工件浏览。
  - Log：`j/k` 单行，`pgup/pgdn` 翻页，`home/end` 顶/底，`l/x` 调整窗口。
  - `?` 帮助；`q` 退出。

---

## 2. 状态模型（SSOT）
- UIState：
  - `selected_flow_idx`、`selected_run_idx`、`last_exec_preview/summary`、`filters/pagination`、`log_tail_offset/lines`、`active_overlay`（none/tasks/monitor/artifacts）、`workflow_state`（步骤列表、当前步骤、结果/可续跑标志）。
- RunStore：
  - 最近运行缓存与索引；从 `artifacts/*/_status.json`、`artifacts/search/*/aggregated.json`、`artifacts/deploy/*` 只读聚合；保守的僵尸检测（pid/host/心跳超时）。
- 事件循环：输入 → 事件 → reducer 更新状态 → 单次 `render_dashboard()`；面板只读状态，不直接打印。

---

## 3. 渲染与输入（最佳实践）
- Live-only：`live.update(layout, refresh=True)`；`vertical_overflow='crop'`；
  - 兼容：`QRAFT_TUI_LIVE_SCREEN=0/1` 控制是否占用备用屏；`QRAFT_TUI_FORCE_PLAIN=1` 强制纯文本兜底。
- 输入：
  - 默认 `live.console.input()` 顶部阻塞读取；
  - 有 PT：`PromptSession` + PathCompleter/枚举/历史/数值步进/日期快捷；
  - 无 PT：回退基础 `input()`，不破坏主帧；输入不暂停 Live 帧。
- Tail：后台 `LogTailMonitor` 刷新缓冲；窗口由 `tail_offset/lines` 计算；切换 run 自动切换尾巴。

---

## 4. 信息架构（Flow → CLI 映射，零盲区）
- 仅暴露已实现能力：
  - Data：`batch`
  - Features：`features`（可灰态占位）
  - Strategy：`validate`
  - Search：`search run / gridsearch`
  - Backtest：`quickbacktest / precisebt / run`
  - Portfolio：`optimize / riskctrl`
  - Risk：`riskattr`
  - Reports：`evidence / golden / deps`
  - Pool：`evaluate-and-propose / propose / approve ...`
  - Deploy：`precheck / canary / publish / rollback / history`
  - Monitor：本地只读监控（可选远端指标只读）

---

## 5. 一键流程编排（最小闭环）
- 定义：`qraft/tui/workflows.py` 提供 builder，将既有 CLI 组合为：
  - Data → Search → QuickBT（vectorbt）→ PreciseBT（Nautilus）→ Portfolio → Risk → Evidence → Pool(evaluate-and-propose) → Deploy(precheck/canary)
- 能力：
  - Dry-run 预览（安全转义的 argv）；
  - 执行：分步运行、失败可重试、可从中断点恢复；
  - 持久化：`artifacts/<pipeline_run>/_pipeline.json`（步骤/参数/产物/状态）。
- 展示：Main 显示进度条与当前步骤摘要、下一步指引；右栏与底部联动；子步骤日志可一键切换。

---

## 6. 工件与质量门槛
- Artifacts 浏览：树/表模式、复制路径、文本预览、跳转相关步骤。
- 质量门槛可见：两阶段一致性、冷启动复跑、成本敏感性、Top‑N 重叠率（读取既有报表/聚合 JSON，只读展示）。

---

## 7. 配置与降级
- 环境变量：
  - `QRAFT_TUI_LIVE_SCREEN`（默认 1）、`QRAFT_TUI_DASH_REFRESH_SEC`（默认 1.0）、`QRAFT_TUI_FORCE_PLAIN`（默认 0）。
  - `QRAFT_TUI_SMART_PATHS`、`QRAFT_TUI_CANDIDATE_DIRS` 控制路径候选。
- 缺失 Rich/PT：退纯文本四区；键位与心智保持一致。

---

## 8. 验收标准（TUI 6.1）
- 单屏四区稳定联动，任何时刻都有输入栏；无标题叠加/闪屏/plain 回退现象。
- 执行后：Main 摘要与右栏立即刷新，Run 自动选中；Tail 可滚动查看。
- 一键流程：可干跑/可执行/可续跑；产物与状态可复现；质量门槛可见。
- 代码质量：改动文件 flake8 0 告警；pytest 全量通过。

---

## 9. 风险与缓解
- 终端兼容：默认全屏 Live；异常用环境变量关闭；保留纯文本兜底。
- 文件体量：tail 与监控分页/节流；
- 活性误判：pid/host/心跳超时的保守检测；未知状态维持 running 并标注“未确认”。
