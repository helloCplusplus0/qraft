# Qraft 6.0 TUI（统一 Dashboard）开发规划表

> 原则：小步快跑、最小可用优先；严格复用现有 CLI/API/工件；避免假设开发与重复设计。

---

## 里程碑与任务拆解（WBS）

### ✅ M0：基线确认与接口清单（0.5d）
- 清点现有 CLI/任务入口、面板与工件：
  - 运行入口：run_local/run_remote、recipes、回测/搜索/组合/风险/部署等现有命令。
  - 工件规范：artifacts/{run_id}/ 下 _status.json、stdout/stderr、search/aggregated.json、deploy/*。
- 输出接口对照表：TUI → CLI 参数映射，不新增/不改变现有参数。
- 定义 Dashboard 路由开关（保留旧 Tab 模式）。

### ✅ M1：P0 最小可用增强（1–2d）
- 右侧迷你监控栏：读取最近 N 条 run（沿用 panels.list_recent_runs）+ 状态徽章。
- 进程活性校验：扩展 Monitor 以 PID/心跳/host 校验 running，识别 zombie（不改变执行方，仅读取）。
- 底部日志尾巴：根据当前选中 run 实时 tail stdout/stderr；提供“展开更多/暂停”。
- 键位：Tab/Shift+Tab 切焦点，Enter 打开详情，? 显示帮助。

### ✅ M2：P1 Dashboard 骨架（1–2w）
- 布局与路由：实现四区布局（侧栏/主区/右监控/底日志），F2 在 Dashboard 与旧模式切换。
- Flows 信息架构：梳理 Data→Features→Strategy→Search→Backtest→Portfolio→Risk→Reports→Pool→Deploy→Monitor 的入口项与显示名称。
- 表单集成（不改变现有 API）：
  - 扩展 forms.py：
    - 如安装 prompt_toolkit：提供 PathCompleter、枚举/布尔选择器、数值步进、日期快捷；
    - 未安装：回退至 input + 基础校验。
  - Dry-run 预览按钮：展示将要执行的命令行参数（已转义）。
- 联动：监控区选择 run → 主区打开对应详情页，底部日志同步。
- 帮助与空态：? 调出键位；列表空态给出“如何开始”。

### ✅ M3：P2 打磨与增强（按需 1–3w）
- 指标卡片：在监控区显示 Top-N 搜索结果、最近回测收益概览（只读自现有 JSON）。
- 过滤与搜索：侧栏与监控支持 / 快速过滤；按标签/前缀筛选 run。
- Artifacts 浏览器：树形浏览 artifacts，支持打开详情/复制路径。
- 主题与徽章：统一配色与状态样式；可配置主题。
- 远端只读监控（如已有）：读取远端 artifacts 索引或 metrics 端点，仅展示，不新增写入路径。
 - 单一 Dashboard 模式：默认进入 Dashboard；F2 切换提示移除；`t` 打开 Tasks。
 - 全量命令接入：Flows 与 Tasks 覆盖全部 CLI（含 ops、quality、riskattr 等）；Search Flow 提供 `search run / gridsearch` 二选一菜单。
 - 表单易用性：智能路径选择器（候选 + 数字选择）；环境变量：`QRAFT_TUI_SMART_PATHS`、`QRAFT_TUI_CANDIDATE_DIRS`。

### M4：验收与文档（0.5–1d）
- 按验收标准逐项自测：
  - 同屏四区联动；
  - 活性校验识别 zombie；
  - 表单补全/选择器/历史与 Dry-run；
  - Flows 各节点均可发起或灰态占位并有文档跳转；
  - PT 缺失时回退不崩溃。
- 更新 docs：键位一览、已覆盖能力与限制说明。

---

## 任务清单（可执行项）

1) Dashboard 路由与启动开关
- 在 tui_cmd 增加 --dashboard 与 F2 切换；保留现有 Tab 模式。

2) 右侧迷你监控 + 活性校验
- 新建 MonitorService：
  - 读取 artifacts/*/_status.json → 最近 N 个 run；
  - 若 state=running 且含 pid/host，探测本机进程存活与 last_heartbeat_ts；
  - 生成状态：running/success/failed/zombie，附最近错误摘要（若有）。

3) 底部日志尾巴
- 根据监控选中 run 实时 tail stdout/stderr；提供暂停、展开更多。

4) 侧栏 Flows
- 静态清单映射到现有 CLI/表单；未实现项灰态并提供文档链接。

5) 主区表单增强（复用 forms.py）
- 若安装 prompt_toolkit：
  - 文件路径 PathCompleter + 存在性校验；
  - 枚举/布尔选择器、数值步进、日期快捷（YTD/MAX/2020Q1 等）；
  - 历史记忆与默认值（最近使用/Recipe 预设）。
- Dry-run 预览 → 确认后执行。
- 无 PT 时回退到基础 input 校验。

6) 键位与帮助
- Tab/Shift+Tab、Enter、/、?、F2；
- 帮助弹层与空态指引。

7) Artifacts 只读组件
- 统一的路径打开/复制；
- 详情页面跳转与返回。

---

## 风险与回退
- PT 不可用：回退到基础交互，保留 Dashboard 主体布局与只读监控；表单功能降级但不阻塞执行。
- 文件体量大：tail 与轮询节流；提供暂停与“展开更多”。
- 活性误判：仅当有 pid/host 且本机进程已不存在且心跳超时才判为 zombie；否则维持 running 并提示“未确认”。

---

## 里程碑交付物
- M1：右侧迷你监控 + 日志尾巴 + 活性校验；
- M2：可交互的四区 Dashboard，联动与表单增强就绪；
- M3：过滤、指标卡片、Artifacts 浏览；
- M4：文档与验收报告。

### M5：状态与编排重构（1–2d）
- 目标：以最小改动实现“状态驱动 + 流程编排”，确保 Dashboard 四区稳定联动，符合 Data-first 的自动化探索闭环。
- 范围（不新增依赖、不改 CLI 契约）：
  1) 状态与存储：新增 `qraft/tui/state.py`（`UIState`：当前 Flow/Run、上次执行摘要；`RunStore`：最近运行缓存与索引）。
  2) 事件循环：`qraft/cli_impl/tui_cmd.py` 改为 event → reduce → render，一次性渲染 `render_dashboard`，移除旧 Tab 残留逻辑耦合。
  3) 流程编排最小骨架：新增 `qraft/tui/workflows.py`，提供“一键 Demo 流程”（Data→Search→QuickBT→PreciseBT→Portfolio→Risk→Evidence→Pool eval/propose→Deploy precheck/canary），每步映射既有 CLI；支持 dry-run 预览与失败续跑元数据（`artifacts/<pipeline_run>/_pipeline.json`）。
  4) 展示一致性：Dashboard Header 显示当前 Flow/Run；Main 显示流程进度与上次执行摘要（即使无日志/工件）；右栏 Recent 与底部 Log tail 联动。
- 交付物：
  - `qraft/tui/state.py`、`qraft/tui/workflows.py`、更新后的 `qraft/cli_impl/tui_cmd.py` 与 `qraft/tui/panels.py` 渲染调用（仅读状态）。
  - 更新 `docs/TUI6.0_cookbook.md`：加入“一键流程”章节与录屏脚本要点。
- 验收（对齐 M1–M4 标准并新增）：
  - Dashboard 四区在执行前/执行后/空态均稳定显示且联动；
  - 一键 Demo 可从 Data→Monitor 跑通闭环，步骤可复现与续跑；
  - flake8 0 告警（改动文件），pytest 全量通过。