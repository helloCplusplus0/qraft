# Task 7.22 — TUI6.1 M2：SSOT 状态化（事件 → reducer → render）

## 1. 目标与范围
- 扩展 `UIState/RunStore` 为单一事实源（SSOT），覆盖：
  - 选择与历史摘要：`selected_flow_idx/selected_run_idx/last_exec_*`
  - 日志尾巴：`log_tail_lines/log_tail_offset`
  - 覆盖层：`active_overlay`（tasks/monitor/artifacts）
  - 监控分页与过滤：`monitor.{runs_limit, runs_offset, runs_states_filter, runs_min_age_days, runs_max_age_days, runs_prefix}`
  - 工作流占位：`workflow_state`
- 在 `tui_cmd.py` 引入“事件 → reducer → render”循环：所有交互只改状态/仓库，不直接 print；渲染读取状态。
- 移除局部状态变量（tail_lines/tail_offset/monitor_state 等），以 `UIState` 为准。

## 2. 变更清单（最小化）
- `qraft/tui/state.py`：补齐字段（如上）。
- `qraft/cli_impl/tui_cmd.py`：
  - 将 `tail_lines/tail_offset/monitor_state` 等迁移到 `ui_state`；
  - 统一通过 reducer 更新状态（函数化封装）并 `live.update`；
  - 渲染与输入不再修改局部变量；仅写入 `ui_state`；
  - 维持 M1 的 Live-only 与统一输入约束。

## 3. 验收标准
- 选中/刷新/滚动/分页/过滤均通过 `UIState` 字段生效；无局部漂移状态。
- 源码中不再出现与上述状态重复的局部变量（tail_lines/tail_offset/monitor_state）。
- 改动文件 flake8 0 告警；pytest 全量通过。

## 4. 风险与降级
- 日志尾巴与 monitor 滚动/分页需正确夹取（clamp）范围，避免越界。
- Live 全屏模式异常可通过 `QRAFT_TUI_LIVE_SCREEN=0` 降级；纯文本用 `QRAFT_TUI_FORCE_PLAIN=1`。

## 5. 执行记录（事后更新）
- 实施项：
  - [x] `state.py` 字段扩展（tail/overlay/monitor/workflow）。
  - [x] `tui_cmd.py` 将 `tail_lines/tail_offset/monitor_state` 迁移到 `UIState`；输入事件仅更新状态，渲染读取状态；删除局部漂移状态。
  - [x] flake8 + pytest 通过，改动文件 0 告警。
- 结论：
  - [x] 通过验收
  - [ ] 待修正项：

## 6. 反思
- 事件驱动是否清晰，渲染是否完全只读状态？
- 是否为后续 M3（监控与日志）铺平路径？
