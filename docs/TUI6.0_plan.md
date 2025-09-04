# Qraft 6.0 TUI（统一 Dashboard）设计方案

> 目标：以“统一 Dashboard”的多面板终端界面，替代当前“多 Tab 单视图”模式，在单屏内同时呈现导航、主工作区、运行监控与日志尾巴，提升态势感知与操作效率；严格复用现有 CLI/API 与工件约定，避免过度设计与重复造轮子。

---

## 0. 设计原则（用户优先 + 最小变更）
- 先落地，后完美：优先实现单屏多面板的可用闭环，不引入 Web/UI 服务端。
- 复用现有能力：基于 Rich + prompt_toolkit（可选安装，未安装则回退至内置 input），数据源均来自现有工件（artifacts 下的文件）。
- 无功能盲区：覆盖 Qraft 已有主要功能（数据→特征→策略/搜索→回测→组合→风险→报表→策略池→上线→监控）的最小操作路径。
- 安全与可复现：严格参数转义（shlex.quote）、不暴露密钥；run_id/工件与当前约定一致。
- 轻量与稳定：单进程、单线程渲染；监控以轮询文件为主，不与执行流程发生资源竞争。

---

## 1. 现状回顾与问题定位
- 单页 Tab 模式：Home/Tasks/Run/Monitor/… 互斥显示，无法同时查看“参数表单 + 最近运行 + 日志尾巴”，排障与对账低效。
- 监控可信度：Monitor 仅读取 artifacts 下 _status.json、search/aggregated.json、deploy/CURRENT.json 等，未做进程活性校验，历史/僵尸 run 可能被误判为 running。
- 表单易错：目前仅基础校验，未充分利用 prompt_toolkit 的补全/选择器/历史能力，路径与枚举输入易误。
- 信息架构：以命令为中心，难以反映“数据→特征→策略→回测→组合→风险→上线”的流程心智。

---

## 2. 统一 Dashboard 总览

布局（示意）：
```
┌─────────────┬───────────────────────────────┬───────────────┐
│ 导航侧栏     │ 主工作区（表单/详情/报表）       │ 右侧监控栏       │
│ Flows/Tasks │ - 表单：参数与预填/校验           │ - 最近运行列表   │
│ 快捷入口     │ - 详情：策略/回测/组合/风控详情   │ - 指标/状态徽章   │
│ 过滤与搜索   │ - 报表：概览与跳转                │ - 异常/告警计数   │
├─────────────┴───────────────────────────────┴───────────────┤
│ 底部日志尾巴（当前选中 run 的 stdout/stderr tail N 行 + 状态）            │
└───────────────────────────────────────────────────────────────┘
```
交互（默认快捷键，可配置）：
- Tab/Shift+Tab：在侧栏/主区/监控/日志之间切换焦点；方向键或 j/k 导航列表。
- Enter：在侧栏选择节点后在主区打开相应表单/详情/报表；在监控区选 run 联动主区与底部日志。
- F2：Dashboard 与“传统 Tab 模式”一键切换（过渡期保留）。
- /：快速过滤（支持在侧栏与监控区生效）。
- ?：帮助与键位提示；c：复制选中文件/目录路径。

---

## 3. 信息架构（Flow → 功能映射，无盲区）
- Data（数据快照）→ qraft.data.snapshot：导入/快照/校验；主区表单+最近使用；监控显示最新数据任务。
- Features（特征流水线）→ qraft.features.pipeline：指标/对齐/去极值/标准化；主区选择模板与参数；产物路径跳转。
- Strategy（策略与模板）→ qraft.golden/strategies + strategies/templates：选择模板/参数网格；与 Search 联动。
- Search（搜索编排）→ qraft.search.spaces + orchestrator：启动网格/随机搜索（fast）；监控进度与 Top-N。
- Backtest（回测）→ engines/vectorbt（fast）、nautilus（precise）：统一表单，双引擎开关；报告跳转。
- Portfolio（组合优化）→ portfolio/optimizers + constraints：MV/HRP/BL 与约束；结果持久化与报表。
- Risk（风险控制与归因）→ risk/controls + attribution：阈值与归因报表。
- Reports（报表与审计包）→ reports/generators + audit/package + evidence/pack：概览与下载路径。
- Strategy Pool（策略池）→ strategy_pool/manager：提案/批准/清单查看。
- Deploy（上线/灰度）→ deployment：参数冻结、纸上交易/小资金、回滚入口（按当前已实现范围呈现）。
- Monitor（监控）→ tui/panels + runner/metrics：最近运行、活性校验、指标与告警摘要。

注：各节点仅暴露当前代码库已具备的功能与参数；未实现的能力不在 UI 暴露按钮（避免假设开发），仅提供“文档跳转/灰态占位”。

---

## 4. 数据与状态模型（复用 + 增量）
- run_id：沿用 `prefix_YYYYMMDD_HHMMSS_PID` 生成规则；工件路径 `artifacts/{run_id}/...`。
- 状态文件：`artifacts/{run_id}/_status.json`（现有）新增可选字段：`pid`、`last_heartbeat_ts`（ISO8601）、`host`。
- 活性校验：Monitor 在读取 state=running 的同时，尝试按 `pid` + `host`（本机）探测进程是否存活；若超过阈值（如 > 10s 无心跳且进程不存在）标记为“可疑（zombie）”。
- 指标文件：继续读取 search/aggregated.json、deploy/CURRENT.json/HISTORY.json；不修改其生成逻辑，仅作为只读来源。
- 刷新节流：监控与日志 tail 默认 0.5–2s 轮询（可配置）。

---

## 5. 表单交互（prompt_toolkit 增强，自动回退）
- 文件路径：PathCompleter + 目录常用入口（artifacts/, tmp/, docs/, data/）；存在性即时校验；缺失高亮提示。
- 枚举/布尔：单键切换与下拉选择（如 y/n、向上/向下选择项）；数值支持步进与范围提示。
- 日期/时间：常用快捷（YTD、MAX、2020Q1）；校验格式并显示解析结果。
- 历史与默认：记忆最近输入，表单初始值优先取“最近使用/Recipe 预设”。
- 安全与预览：Dry-run 输出“将要执行的 CLI 参数串”（严格转义），确认后再执行。
- 回退策略：未安装 prompt_toolkit 时，自动退化到内置 input + 基础校验，不影响核心流程。

---

## 6. 组件与模块
- Router：在现有 `tui_cmd` 主循环上增加 `Dashboard` 路由，保留旧 Tab 模式为兼容选项。
- Panels：拆分可复用小部件（运行列表、状态徽章、迷你报表卡片、日志尾巴）。
- MonitorService：封装文件轮询、活性校验与缓存，供右侧监控栏与底部日志共用。
- FormEngine：在 `forms.py` 基础上扩展 PT 能力（可选），API 不破坏现有调用。
- Recipes：保留 `recipes.py` 作为预设与最近使用来源，支持一键填充表单。

---

## 7. UX 规范与快捷键
- 统一配色与徽章：state=running/success/failed/zombie 分色；关键指标卡片（收益/时延/进度）。
- 帮助与空态：? 打开帮助面板；列表空态给出“如何开始”的动作建议。
- 键位默认：Tab/Shift+Tab（焦点）、Enter（打开）、Esc（返回/关闭弹层）、F2（模式切换）、/（过滤）。

---

## 8. 性能与可靠性
- 刷新节流：监控 0.5–2s；日志 tail 每次最多 N 行（默认 100），并可手动“展开更多”。
- 失败回退：任何 PT 功能不可用时，保证 CLI 可执行路径不受影响；读取文件异常以友好提示代替崩溃。
- 资源约束：TUI 自身 CPU/内存开销低于既有基线；长任务执行在子进程，TUI 仅消费文件与 stdout。

---

## 9. 安全与合规
- 不输出/存储任何密钥；远程执行若启用，沿用现有 ssh 调用方式（如已存在），不引入持久化会话。
- Shell 注入防护：所有参数经安全转义；日志输出做最小必要截断与脱敏。

---

## 10. 验收标准（针对 TUI 6.0）
- 单屏全览：Dashboard 同屏呈现导航/主区/监控/日志，并实现跨面板联动（监控选中 run → 主区详情 + 底部日志联动）。
- 监控可信度：对 running 状态进行活性校验并识别 zombie；误判率显著下降。
- 表单易用：路径补全/存在性校验、枚举/布尔选择器、历史默认值、Dry-run 预览。
- 无盲区覆盖：Flows 中的每个节点均能发起相应已实现的 CLI/流程，或明确灰态占位并提供文档跳转。
- 兼容回退：未安装 prompt_toolkit 或文件缺失时，界面不崩溃、功能可退化。

---

## 11. 推进节奏（概览）
- P0（最小可用，1–2 天）：嵌入“迷你监控 + 底部日志尾巴”，加活性校验；保留原 Tab。
- P1（Dashboard 骨架，1–2 周）：实现四区布局与联动；Flows → 功能映射与表单；键位与帮助。
- P2（增强与打磨，按需）：报表卡片/过滤、主题与状态徽章、Artifacts 浏览与跳转、远端只读监控（如已具备）。