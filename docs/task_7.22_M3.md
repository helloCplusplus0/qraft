# Task 7.22 — TUI6.1 M3：监控与日志（僵尸检测 + Tail 可滚动）

## 1. 目标与范围
- Recent Runs：分页/筛选/状态徽章；僵尸检测（pid/host/心跳，保守判定）。
- Log tail：后台 `LogTailMonitor`，支持 `j/k/pgup/pgdn/home/end` 滚动；`l/x` 调整窗口；切换 run 即切尾巴。
- 交付：右栏/底部与状态一致；返回 Dashboard 后自动跟随选中 run 的尾巴。

## 2. 变更清单（最小化）
- 保持现有 `panels.list_recent_runs` 僵尸检测逻辑与样式（仅小修必要参数传递）。
- `tui_cmd.py`：
  - Monitor 打开时的选择 run 同步到 `UIState.selected_run_idx`，返回后 Dashboard 尾巴自动跟随（已实现）。
  - Tail 滚动/窗口大小完全使用 `UIState.log_tail_*` 字段，消除局部状态（已实现于 M2/M3）。
- 文档：本文件记录事前/事后与验收。

## 3. 验收标准
- 监控列表存在 `state_eff=zombie` 时有状态标注；过滤/分页有效。
- 选择 run 后，返回 Dashboard，底部尾巴显示该 run 日志；`j/k/pgup/pgdn/home/end` 正常滚动；`l/x` 调整窗口生效。
- 改动文件 flake8 0 告警；pytest 全量通过。

## 4. 风险与降级
- 心跳阈值：以 `QRAFT_HEARTBEAT_TIMEOUT_*` 为上限，保守判定僵尸；异常维持 running+未确认提示。
- Terminal 冲突：`QRAFT_TUI_LIVE_SCREEN`/`QRAFT_TUI_FORCE_PLAIN` 可降级。

## 5. 执行记录（事后更新）
- 实施项：
  - [x] Monitor 选择 run 同步至 SSOT，返回后自动切尾巴；尾巴滚动/大小取自状态。
  - [x] flake8 + pytest 通过。
- 结论：
  - [x] 通过验收
  - [ ] 待修正项：

## 6. 反思
- 监控/尾巴是否已稳定，交互是否一致？
- 是否为后续 M4 覆盖层表单/Artifacts 铺平路径？
