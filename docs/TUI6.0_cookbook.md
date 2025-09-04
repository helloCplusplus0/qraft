# Qraft TUI 6.0 Cookbook（快速上手与全量功能手册）

> 面向终端使用者：本手册帮助你在终端中用 TUI 完成对 Qraft 的全部操作路径。无 Web 依赖，轻量稳定。

## 1. 安装与启动
- 激活环境并安装可选增强库（建议）：
  - `pip install rich prompt_toolkit`
- 启动 TUI（默认进入 Dashboard）：
  - `qraft tui`
- 非交互一次性渲染（CI/冒烟）：
  - `python -m qraft.cli tui --non-interactive`

## 2. 界面结构与键位
- 四区布局：左侧导航（Flows/Tasks）/ 主区（表单与预览）/ 右侧监控 / 底部日志尾巴。
- 主要键位：
  - 在 Dashboard：
    - 输入数字 0..N 选择 Flow（顺序：Data→Features→Strategy→Search→Backtest→Portfolio→Risk→Reports→Pool→Deploy→Monitor）
    - `o` 打开当前 Flow 的菜单/表单
    - `s<idx>` 选择右侧最近运行；`l` 增加日志行数；`a` 进入 Artifacts 浏览
    - `t` 打开 Tasks（全量命令清单）；`m` 打开 Monitor；`q` 退出
  - 在 Monitor：
    - `/` 过滤（如 `state=running prefix=run_2024`），`n/p` 翻页，`o` 打开某个 run 的日志尾巴；回车返回 Dashboard

## 3. 智能路径选择器（减少输入错误）
- 所有常见“文件/目录”字段都会优先显示候选项（当前目录与 `./tmp`），并支持数字选择；也可直接输入路径或按回车使用默认。
- 环境变量：
  - 关闭：`QRAFT_TUI_SMART_PATHS=0`
  - 扩展扫描目录：`QRAFT_TUI_CANDIDATE_DIRS=/data:/mnt/xxx`

## 4. Flows（推荐入口）
- Data（数据/批处理）：`batch`（目录批量回测，支持并发与聚合）
- Features（特征流水线）：占位（按规划待接入）
- Strategy（策略校验/入口）：`validate` → 校验策略 JSON
- Search（搜索编排）：菜单二选一
  - `[1] search run`：运行搜索编排器（空间/计划/并发/时间窗/输出目录）
  - `[2] gridsearch`：参数网格搜索（策略/价格/参数表/并发）
- Backtest（回测）：菜单三选一
  - `[1] quickbacktest`（向量化快速）
  - `[2] precisebt`（Nautilus 精撮）
  - `[3] run`（统一 Runner，自动/双引擎）
- Data（批处理）：`batch`（目录批量回测，支持并发与聚合）
- Portfolio（组合/风险）：`optimize` 与 `riskctrl`
- Reports（报表/证据/依赖）：`evidence`、`golden`、`deps`
- Pool（策略池全量子命令）：`propose/approve/list/tag/deprecate/replace/cleanup/evaluate-and-propose`
- Deploy（上线/灰度）：`precheck/canary/propose/approve-and-publish/current/history/rollback`
- Ops（运维）：`list/repair/cleanup`
- Monitor（监控）：快速过滤、分页、日志尾巴查看

## 5. Tasks（全量命令清单）
- `t` 打开任务清单，选择任何命令进入相应表单（与 Flows 等价）。清单已覆盖：
  - `validate/run/quickbacktest/precisebt/search/gridsearch/batch/optimize/riskctrl/riskattr/evidence/quality/pool/deploy/golden/deps/ops`

## 6. 表单与执行
- 表单字段包含默认值/历史回填，支持布尔/枚举/数值输入；路径字段支持补全与候选选择。
- 确认前会显示 “Preview” 命令（安全转义），确认 `r` 运行；输出工件位于 `artifacts/{run_id}`。上次执行命令摘要会在 Dashboard 主区显示，便于回溯。

## 7. 监控与日志
- 右侧“最近运行”显示 run 状态（彩色徽章）：running/finished/failed/zombie。
- 选择 run 后，底部显示日志尾巴；`l` 增加行数。按 `m` 打开 Monitor（嵌入视图），可 `/` 过滤、`n/p` 翻页、`o` 打开 tail，并回车返回。

## 8. Artifacts 浏览（只读）
- 在 Dashboard 输入 `a` 进入浏览器：
  - 输入编号进入子目录或文件预览；`..` 返回上级；`m` 增加文本预览行数；`c` 打印当前文件路径。

## 9. 环境变量与主题
- `QRAFT_TUI_THEME`：切换主题（light/dark，若使用 rich）。
- `QRAFT_TAIL_REFRESH_SEC`：日志自动刷新间隔（缺省 1.0s）。

## 10. 常见问题（FAQ）
- 没装 rich 或 prompt_toolkit？
  - TUI 会自动降级为纯文本与基础输入，功能可用但视觉/输入体验简化。
- 输入路径麻烦？
  - 已启用“智能路径选择器”，优先数字选择候选文件；也可通过环境变量扩展候选目录。
- 运行哪里看结果？
  - `artifacts/{run_id}`；右侧“最近运行”与底部日志会联动显示；主区会显示上次执行命令摘要。

## 11. 最佳实践
- 以 Flows 为主线（流程心智），复杂命令使用 Tasks 直接进入。
- 执行前始终查看 Preview，确认无误后再运行。
- 保持 `artifacts/` 清理：使用 `ops cleanup`（dry-run 预览 → `--apply` 执行）。

---

如发现问题或需要新入口，请在 Issue 中附带：命令预览串、报错与 `artifacts/{run_id}` 关键文件路径。

## 12. 端到端 Demo（从零到 Pool/Deploy/Monitor）

前置：仓库根目录有示例文件：`sample_strategy.json`、`sample_prices.csv`。若无，请先准备策略 JSON 与价格 CSV。

步骤 1：数据与策略校验（了解输入是否可用）
- 打开 TUI：`qraft tui`
- 选 Flow：输入 `0`（Data），按 `o`，选择 `batch` 预览后按 `b` 返回（可跳过运行）。
- 选 Flow：输入 `2`（Strategy），按 `o`，选择策略文件（支持数字选择），预览后按 `r` 运行 `validate`。
- 回到 Dashboard：主区会显示“上次执行命令摘要”。

步骤 2：搜索编排（生成候选搭配）
- 选 Flow：输入 `3`（Search），按 `o`，在菜单选择 `[1] search run`。
- 选择搜索空间/价格等，预览命令，按 `r` 运行。
- 运行过程中可按 `m` 查看 Monitor；完成后右侧 Recent Runs 会出现记录。

步骤 3：回测（两级回测：quick → precise）
- 选 Flow：输入 `4`（Backtest），按 `o`，先选 `[1] quickbacktest` 填写策略/价格/时间窗，按 `r` 运行。
- 再次进入 Backtest 选 `[2] precisebt` 执行精撮回测（如环境具备）。
- 选中右侧某条 run（`s<idx>`），底部会展示日志尾巴；主区可查看 run 概要。

步骤 4：组合与风控（可选）
- 选 Flow：输入 `5`（Portfolio），按 `o`，选择 `optimize` 或 `riskctrl`，根据需要输出权重与风控结果。

步骤 5：证据与报表（可选）
- 选 Flow：输入 `7`（Reports），按 `o`，选择 `evidence`（生成 Evidence Pack）或 `golden/deps` 等工具。

步骤 6：策略池（治理与门槛）
- 选 Flow：输入 `8`（Pool），按 `o`，根据流程选择：
  - `evaluate-and-propose`：对候选策略做质量/稳健性评估并提案到池；或
  - `propose/approve/list/tag/deprecate/replace/cleanup` 完成治理操作。

步骤 7：上线与监控
- 选 Flow：输入 `9`（Deploy），按 `o`，先 `precheck`（一致性预检），再 `canary`（纸上/小资金），通过后 `approve-and-publish`。
- 监控：按 `m` 打开 Monitor（嵌入视图），可 `/ state=running` 过滤、`n/p` 翻页、`o` 打开 tail；回车返回 Dashboard。

步骤 8：运维清理（可选）
- 选 Flow：输入 `10`（Monitor）检视运行；按 `t` → `ops cleanup` 进行工件清理（先 dry-run 预览）。
