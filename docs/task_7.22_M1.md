# Task 7.22 — TUI6.1 M1：框架收口（Live-only + 统一输入 + 固定输入栏）

## 1. 目标与范围
- 仅保留 Live-only 渲染路径：Dashboard 通过 `Live.update(...)` 单帧直绘；禁止穿插 `print/clear`。
- 统一输入：优先 `PromptSession`（如可用），否则 `live.console.input()`；无 PT 回退 `input()`；不暂停 Live。
- 固定输入栏：任何时刻都有输入入口；输入在 Live 顶部显示，主帧持续可见。
- 单一入口：不再存在旧 Tab 模式代码路径。

不改变既有 CLI/工件协议；禁止过度设计。

## 2. 变更清单（最小化）
- `qraft/cli_impl/tui_cmd.py`
  - Dashboard 主循环：
    - 渲染：仅用 `live.update`（Rich 存在且未强制 plain）；plain 模式一次性 `render_dashboard(...)` 输出。
    - 输入：
      - `PromptSession.prompt()`（如安装 PT）或 `live.console.input()`；
      - `QRAFT_TUI_NONBLOCK=1` 时轮询 `_getch_nonblocking()`；
      - 不再暂停 live 以显示输入提示。
    - 去除在 Dashboard 主循环中的 `_clear()`、`_print()` 提示式反馈；统一通过 `UIState.last_exec_summary` 在 Main 区域显示。
  - 移除/清理不可达的旧 Tab 模式代码块。
- 文档：新增本文件，事前/事后记录。

## 3. 验收标准
- 进入 `qraft tui`：
  - 无“标题反复重绘/下压”；四区稳定；输入栏始终存在。
  - 输入通过 Live 顶部出现，不遮挡主帧；Enter 后主帧仍保持单帧更新，无闪屏。
- 非阻塞模式（设置 `QRAFT_TUI_NONBLOCK=1`）：Dashboard 周期性刷新，无输入也不阻塞。
- 代码质量：改动文件 flake8 0 告警；pytest 全量通过。

## 4. 风险与降级
- 终端兼容：若 `screen=True` 导致冲突，可设 `QRAFT_TUI_LIVE_SCREEN=0`；
- 强制纯文本：设 `QRAFT_TUI_FORCE_PLAIN=1`；
- 无 PT：回退 `live.console.input()` 或 `input()`。

## 5. 执行记录（事后更新）
- 实施项：
  - [x] 代码改造与清理：
    - Dashboard 主循环 Live-only：渲染仅通过 `live.update`；移除暂停/清屏/直接打印提示，改为 `UIState.last_exec_summary` 状态化反馈。
    - 覆盖层 Tasks：以输入询问方式在 Live 顶部完成选择/确认/执行，执行后刷新 `RunStore` 并尝试选中新 run。
    - 删除不可达的旧 Tab 模式代码块与无用变量。
  - [x] flake8 + pytest 验收：改动文件 0 告警；测试全量通过。
- 结论：
  - [x] 通过验收
  - [ ] 待修正项（如有）：

## 6. 反思
- 设计/实现是否与 `docs/TUI6.1_task_list.md` M1 完全对齐？
- 交互是否稳定、清晰、无历史残留？
- 是否为后续 M2（SSOT）铺平路径？
