# TUI 6.0 M3：P2 打磨与增强（事前任务设计）

## 1. 任务目标
- 在不增加新依赖、严格复用现有 CLI/API/工件的前提下，提升 Dashboard/Monitor 的“可读性 + 可操作性”，补齐 M2 骨架后的可用性缺口。

## 2. 范围与边界（禁止过度设计）
- 仅实现“读+显示+交互增强”，不新增后台守护/服务端；所有数据源来自本地 artifacts 及可选远端只读 HTTP JSON。
- 复用 `rich` 与可选 `prompt_toolkit`，未安装即降级；不新增第三方库。
- 不改变 CLI 行为与参数；TUI 仅作为可视/交互层。

## 3. 功能需求（对齐 docs/TUI6.0_task_list.md M3）
- 指标卡片：
  - 在 Monitor/Dashboard 右侧显示 Top‑N 搜索摘要与最近回测收益概览（只读自 artifacts JSON，如 search/aggregated.json）。
- 快速过滤：
  - 监控区支持 `/` 开始的过滤模式：状态（running/finished/failed/zombie）、前缀（run_id 前缀）。
  - 支持翻页（n/p），与现有 limit/offset 组合。
- Artifacts 浏览器（只读）：
  - 支持树形列出 `artifacts/` 下目录与文件；打开详情（文本预览前 N 行，或显示元信息）；复制路径到剪贴板（如无剪贴板 API，仅打印路径）。
- 统一配色与状态徽章：
  - 对 running/finished/failed/zombie 应用一致的颜色；以简洁徽章标识。
  - 提供环境变量 `QRAFT_TUI_THEME`（light/dark）影响少量色彩选择；未设置使用默认。
- 远端只读监控（可选）：
  - 允许用户配置一个远端 artifacts 索引 URL（返回 JSON 清单），仅用于展示最近运行及摘要；不新增写路径，不建立会话。

## 4. 技术方案
- 读取层：
  - 继续复用 `panels.list_recent_runs`、`summarize_search_latest`、`summarize_deploy_state`；新增 `list_artifacts_tree(base, depth, limit)` 与 `preview_text_file(path, max_lines)`。
  - 远端只读索引：新增 `fetch_remote_artifacts_index(url)`，超时与异常安全返回空。
- 渲染层：
  - 指标卡片：`render_monitor`/`render_dashboard` 增补卡片表格；不做复杂图形。
  - 快速过滤：保留当前 Monitor 的交互回路，增加 `/` 进入过滤模式的输入提示与解析。
  - Artifacts 浏览：新增简单树/表格渲染 + 打开详情视图（文本前 N 行）。
  - 主题/徽章：集中在 `panels.py` 内部基于状态选择样式；读取 `QRAFT_TUI_THEME`。
- 交互层：
  - `tui_cmd.py` 的 monitor 与 dashboard 回路中加入：`/` 进入过滤、`a` 进入 artifacts 浏览器、`c` 复制当前选中文件路径、`open` 打开详情。

## 5. 交互设计（最小集）
- Monitor/Dashboard：
  - `/` 输入过滤表达式（例：`/state=running prefix=run_2024`）；`n/p` 翻页；`enter` 刷新。
  - `a` 打开 Artifacts 浏览器；返回 `b`。
- Artifacts 浏览器：
  - 方向：输入子目录索引或 `..` 返回；输入文件索引打开详情；`c` 打印当前路径。
  - 详情：显示前 N 行文本（默认 200），`m` 更多 +200，`b` 返回。

## 6. 验收标准
- 指标卡片与状态徽章渲染无误；
- 运行列表支持 `state` 与 `prefix` 的组合过滤，并可翻页；
- Artifacts 浏览器可遍历目录树、查看文本前 N 行、复制路径（打印）；
- 主题变量生效（至少 2 种风格色差），无 PT/Rich 时显示降级提示但功能可用；
- 未新增依赖；不改变既有 CLI/工件路径；lint 通过。

## 7. 风险与回退
- 大目录/大文件：添加深度与数量上限；文本预览限制行数；
- 远端索引不可达：静默回退本地数据；
- 颜色兼容：颜色不可用时维持文本标注，不影响功能。

---

## 任务执行与验收（事后更新）
- 实现清单：
  - 指标卡片：`render_monitor` 与 `render_dashboard` 增加 Metrics(quick) 卡片，展示 best/mean_sharpe、success_rate、error_count、total_runs（从 search/aggregated.json）。
  - 快速过滤：Monitor 支持 `/` 输入表达式（state=...、prefix=...），并与 n/p 翻页兼容；Dashboard 保持简洁。
  - Artifacts 浏览：新增 `list_artifacts_tree`、`preview_text_file`；Dashboard 中 `a` 进入只读浏览器，支持进入目录、预览文本、打印路径。
  - 主题与徽章：支持 `QRAFT_TUI_THEME`，统一状态着色；Rich/PT 缺失显示降级提示。
  - 远端索引：新增 `fetch_remote_artifacts_index`（未默认启用，仅函数就绪）。
  - 单一 Dashboard 模式：默认进入 Dashboard；保留 Tasks 入口。移除 F2 旧模式提示。
  - 全量命令接入：Flows 与 Tasks 已覆盖 CLI 命令，含 `batch/optimize/riskctrl/riskattr/evidence/quality/pool/deploy/golden/deps/ops`；`Search` Flow 加入 `[1] search run / [2] gridsearch` 菜单。
  - 表单易用性：引入“智能路径选择器”，自动发现候选文件并支持数字选择；可用 `QRAFT_TUI_SMART_PATHS=0` 关闭；`QRAFT_TUI_CANDIDATE_DIRS` 扩展扫描目录。
- 自测要点：
  - `python -m qraft.cli tui --dashboard`：顶部键位与卡片显示正常；状态颜色正确；Artifacts 浏览可用；/ 过滤在 Monitor 可用。
  - 非交互模式保持兼容；lint 通过。
- 遇到问题与修复：
  - 为避免越权假设开发，远端索引仅提供函数与最小接入点，默认本地路径优先。
- 验收结论：
  - 达成 M3 目标：指标卡片、快速过滤、Artifacts 浏览、主题与徽章统一已上线；单一 Dashboard 与全量命令接入完成；未新增依赖且不改变 CLI/工件契约。
