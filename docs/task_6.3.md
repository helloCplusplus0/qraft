# 任务6.3：TUI 运行态监控与远程交互（设计与落地记录）

> 目标（来自 task_list.md）：
> - 在 TUI 中新增 Monitor 面板：展示 Runner/Search 关键实时指标、质量闸门与金套件状态摘要；默认从本地文件化指标/日志汇总读取
> - 支持 SSH 端口转发查看远端导出指标（可选）：提供示例命令与参数说明（不引入后台守护进程）
> - 低占用与无竞态：单线程渲染，采集异步节流，确保与主流程零竞争

对应实现代码：
- Monitor 面板渲染与数据读取：<mcfile name="panels.py" path="/home/dell/Projects/Qraft/qraft/tui/panels.py"></mcfile>
- TUI 入口与 Monitor 路由：<mcfile name="tui_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/tui_cmd.py"></mcfile>
- CLI 子命令注册与参数：<mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile>
- 灰度部署工件（CURRENT/HISTORY）来源：<mcfile name="grayscale.py" path="/home/dell/Projects/Qraft/qraft/deployment/grayscale.py"></mcfile>
- 监控导出器背景与远端指标说明：<mcfile name="task_6.1.md" path="/home/dell/Projects/Qraft/docs/task_6.1.md"></mcfile>


## 1. 范围与现状

本任务在既有 TUI 框架下新增“Monitor”面板，聚合三类信息：
- 系统资源与近期运行摘要（本地 artifacts/*_status.json）
- 搜索（search）最新汇总（artifacts/search/<run>/aggregated.json）
- 部署灰度状态（artifacts/deploy/CURRENT.json, HISTORY.json）

此外，支持可选的“远端 Prometheus 文本指标预览”，便于在仅 CLI/TUI 环境中快速查看远端节点的导出指标。

当前已落地内容：
- 完成 Monitor 面板的基础渲染（Rich/纯文本双模式自动降级）
- 新增部署摘要（CURRENT/HISTORY）读取与面板呈现
- 增加远端 Prometheus 文本端点采样读取与过滤（仅显示以 qraft_ 开头的行）

后续增强（部分已实现，本次提交已落地 Rich 历史表）：
- Rich 模式下的 Deploy 区域：新增“Deploy History (tail)”表格，按 action 颜色标注（publish=绿色、rollback=红色），并与“Deploy Summary”组成上下两段；无历史时展示占位面板
- 质量闸门与金套件摘要的本地化缓存与展示（当前其 CLI 输出以 stdout 为主，后续补充 JSON 摘要并接入）


## 2. 设计要点

### 2.1 面板布局与渲染策略
- 头/体/尾三段式布局：
  - Header：CPU 与 RSS 资源快照
  - Body：左右双列
    - 左列：Recent Runs 列表
    - 右列：上为 Search Summary（latest），下为 Deploy Summary
  - Footer：Remote Metrics（sample，如未配置则显示提示）
- Rich 可用时使用 Layout/Panel/Table 进行排版；Rich 不可用时输出纯文本，保证一致的信息密度与降级体验。

### 2.2 本地数据源与文件协议
- Recent Runs：遍历 artifacts 目录下含 *_status.json 的子目录，读取 run_id/state/elapsed/started_at，以 mtime 排序并截断显示
- Search Summary：读取 artifacts/search/<latest_run>/aggregated.json，如不存在则仅回显所在 run 目录
- Deploy Summary（新增）：
  - CURRENT.json：当前已发布的工件（manifest_hash/approved_by/ts/note 等）
  - HISTORY.json：按时间顺序记录的发布/回滚事件；面板统计 publishes/rollbacks/total，并显示最近 3 条紧凑摘要
- 数据缺失时的优雅降级：以“(no data)/(no deploy data)”占位，避免异常中断

### 2.3 远端指标采样（Prometheus 文本）
- 通过简单的 HTTP GET（超时 1.5s）获取远端 /metrics 文本
- 仅保留以 qraft_ 开头的指标行，最多 30 行；忽略注释与非 Qraft 前缀行
- 默认禁用：只有在 TUI 交互中填写 URL 或使用 CLI 参数传入时才启用

### 2.4 低占用与无竞态
- 资源采样：通过 /proc 读取 CPU 与 RSS（单次快照），不引入后台线程
- 渲染：单线程、一次性渲染（非交互刷新模式下）；交互界面中也仅在用户显式进入 Monitor 时渲染
- 远端请求：短超时 + 行数截断 + 前缀过滤，避免噪声与长阻塞


## 3. 关键函数与入口

- 面板渲染与数据汇总：见 <mcfile name="panels.py" path="/home/dell/Projects/Qraft/qraft/tui/panels.py"></mcfile>
  - list_recent_runs(base, limit)：扫描 artifacts 子目录，读取 *_status.json 并生成最近运行列表
  - summarize_search_latest(root)：从 artifacts/search 选择最新 run，并读取 aggregated.json 形成摘要
  - summarize_deploy_state(deploy_dir, history_tail)：读取 CURRENT/HISTORY，统计发布与回滚次数，并裁剪历史尾部
  - fetch_remote_metrics(url, max_lines)：抓取远端 Prometheus 文本，过滤 qraft_ 前缀指标
  - render_monitor(use_rich, remote_metrics_url)：整合上述数据并输出 Rich/纯文本；Rich 模式下将 Deploy 分区拆分为“Summary + History”两段，并对历史记录按 action 着色（publish=绿色、rollback=红色）

- TUI 主循环：见 <mcfile name="tui_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/tui_cmd.py"></mcfile>
  - 用户在主菜单选择 Monitor 后，支持 [u] 更新远端 URL；每次进入或更新时调用 render_monitor 重新渲染

- CLI 子命令：见 <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile>
  - `qraft tui [--plain] [--non-interactive] [--monitor-url URL]`
  - 当传入 `--non-interactive` 时仅渲染一次并退出，方便 CI 快速验证

- 部署工件来源：见 <mcfile name="grayscale.py" path="/home/dell/Projects/Qraft/qraft/deployment/grayscale.py"></mcfile>
  - 灰度编排器在发布/回滚时维护 artifacts/deploy/CURRENT.json 与 HISTORY.json；Monitor 直接消费本地文件


## 4. 使用说明与示例

### 4.1 本地查看 Monitor 面板
- 交互模式：`qraft tui`
- 纯文本/一次性渲染（CI 友好）：`qraft tui --plain --non-interactive`
- 带远端指标 URL：`qraft tui --monitor-url http://127.0.0.1:8001/metrics`

### 4.2 远端指标与 SSH 端口转发（可选）
- 在远端节点启动导出器（参考 <mcfile name="task_6.1.md" path="/home/dell/Projects/Qraft/docs/task_6.1.md"></mcfile>）
- 本地建立端口转发：`ssh -L 8001:127.0.0.1:8001 user@remote-host`
- 在 TUI Monitor 中设置 URL：`http://127.0.0.1:8001/metrics`

### 4.3 部署摘要数据结构（约定）
- CURRENT.json（示例字段）：`manifest_hash, approved_by, ts, note`
- HISTORY.json（事件序列）：每个事件包含 `action in {publish, rollback}, manifest_hash, ts, approved_by, note`


## 5. 性能与鲁棒性
- I/O：仅在进入 Monitor 时扫描 artifacts；限制最近条目数（默认 8 个运行、历史尾部 5 条）
- 网络：可选的远端请求，设置短超时并限制输出行数
- 错误处理：所有数据加载均包裹 try/except，失败时返回空摘要并在 UI 上以占位提示


## 6. 验收与演示

- 功能验收：
  - Monitor 面板在 Rich 与纯文本模式均可渲染
  - 本地数据缺失时不崩溃并显示占位
  - 当 artifacts/deploy 具备 CURRENT/HISTORY 时，Deploy Summary 正确显示当前状态、计数与历史尾部
  - 远端 URL 配置后可显示 qraft_ 前缀指标行

- 演示验证：
  - 通过脚本在隔离目录生成模拟 CURRENT.json 与 HISTORY.json 后，调用 `render_monitor(use_rich=False)` 输出的文本包含 “Deploy Summary” 区段与相应字段，验证 TUI 已正确接入部署摘要


## 7. 与计划差异与后续工作
- 质量/金套件摘要：当前 CLI 输出以 stdout 为主，未形成规范化本地缓存文件；Monitor 先落地部署摘要，质量/金套件将于后续任务补充本地 JSON 摘要并接入
- Rich 增强：部署历史将新增可展开的表格与颜色标注（发布/回滚），作为 Monitor 的可用性增强项


## 8. 文件清单与改动点
- 新增/修改：
  - <mcfile name="panels.py" path="/home/dell/Projects/Qraft/qraft/tui/panels.py"></mcfile>：新增 summarize_deploy_state，扩展 render_monitor 展示部署摘要与远端指标
  - <mcfile name="tui_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/tui_cmd.py"></mcfile>：在 Monitor 分支中支持在线更新远端 URL，并调用 render_monitor 渲染
  - <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile>：为 `qraft tui` 增加 `--plain/--non-interactive/--monitor-url` 参数


## 9. 风险与边界
- 不引入后台线程或守护进程，避免与主流程竞态
- 仅消费本地文件与一次性 HTTP 请求，不依赖持久连接
- Rich 缺失时自动回退到纯文本，功能不受影响