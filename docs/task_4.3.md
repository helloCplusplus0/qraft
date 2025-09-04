# Task 4.3: TUI MVP（CLI-first 轻 UI）设计文档

## 1. 任务范围

### 1.1 核心功能
根据 `task_list.md` 第254-266行，本任务需实现：
- **`qraft tui` 子命令**：无守护/无服务端，以终端面板呈现 Home/Tasks/Run 三个页签
- **关键信息展示**：进度、耗时、关键指标摘要与日志尾部
- **交互表单**：基础类型校验、默认值与最近使用；支持 Dry-run 预览
- **运行控制**：统一 run_id 与工件目录命名；Ctrl-C 安全中断；CPU/内存开销可见
- **最小远程执行（可选）**：读取主机配置，通过 ssh 在远端执行，流式读取输出

### 1.2 技术栈约束
- **Rich + prompt_toolkit**：作为 extras 可选依赖，按需懒加载
- **回退策略**：若未安装则回退到纯 CLI 提示
- **轻量原则**：CPU/内存开销低于基线，无持久状态

### 1.3 设计边界
- **不引入**：守护进程、Web 服务、持久会话/队列
- **最小实现**：优先完成基础面板与表单，远程执行作为可选扩展
- **CLI-first**：TUI 是 CLI 的增强展示，非独立应用

## 2. 系统架构

### 2.1 模块结构
```
qraft/
├── cli.py                    # 注册 tui 子命令
├── cli_impl/
│   └── tui_cmd.py           # TUI 主入口与控制逻辑
└── tui/                     # TUI 实现模块（新增）
    ├── __init__.py
    ├── panels.py            # Home/Tasks/Run 面板渲染
    ├── forms.py             # 交互表单与校验
    └── launcher.py          # 执行控制与 run_id 管理
```

### 2.2 依赖策略
- **可选导入**：在模块级别检查 `rich` 和 `prompt_toolkit` 可用性
- **懒加载**：仅在 `qraft tui` 调用时导入相关模块
- **安全回退**：缺少依赖时提供纯文本替代，不中断程序

### 2.3 数据流设计
```
用户输入 → 表单校验 → CLI 参数渲染 → 子进程执行 → 实时输出流 → 面板刷新
         ↑                                                      ↓
    默认值/历史参数                                         run_id/工件管理
```

## 3. 核心组件设计

### 3.1 面板系统（panels.py）
**Home 面板**：
- Qraft 版本信息与基础状态
- 最近执行任务摘要（run_id, 耗时, 状态）
- 系统资源概览（CPU/内存使用率）

**Tasks 面板**：
- 可用 CLI 命令列表（validate, run, search 等）
- 参数表单入口与预览
- 执行历史与快速重复

**Run 面板**：
- 当前执行任务的实时状态
- 日志尾部滚动显示
- 进度指示与错误高亮

**技术实现**：
- Rich 可用时：使用 `rich.console` 与 `rich.layout` 渲染
- 回退模式：纯文本格式化输出，定期清屏刷新

### 3.2 表单系统（forms.py）
**基础功能**：
- 字符串、数字、布尔、枚举类型校验
- 必填项检查与默认值填充
- 文件路径存在性验证

**增强功能**（prompt_toolkit 可用时）：
- 自动补全与历史记录
- 多行编辑与语法高亮
- 实时校验反馈

**安全特性**：
- 严格参数转义，避免 shell 注入
- Dry-run 模式预览命令串
- 敏感参数（如密码）的遮蔽处理

### 3.3 执行控制（launcher.py）
**run_id 生成**：
- 格式：`{command}_{timestamp}_{short_hash}`
- 示例：`run_20240101_120000_a1b2c3`

**子进程管理**：
- 使用 `subprocess.Popen` 非阻塞执行
- 实时捕获 stdout/stderr 流
- Ctrl-C 信号处理与优雅终止

**工件管理**：
- 统一输出目录：`artifacts/{run_id}/`
- 日志文件：`{run_id}.log`
- 状态追踪：`{run_id}_status.json`

## 4. UI 流程与交互

### 4.1 启动流程
```
qraft tui → 检查依赖 → 初始化面板 → 显示 Home 页面
         ↓
      显示依赖状态（Rich/prompt_toolkit 可用性）
         ↓
      提供键位提示（Tab 切换，Ctrl-C 退出）
```

### 4.2 任务执行流程
```
Tasks 面板 → 选择命令 → 填写表单 → Dry-run 预览 → 确认执行
           ↓                    ↓
        参数校验              命令串展示
           ↓                    ↓
        保存历史           → Run 面板监控
```

### 4.3 键位映射
- **Tab/Shift-Tab**：面板切换
- **Enter**：确认/执行
- **Ctrl-C**：中断当前操作
- **Ctrl-D**：退出 TUI
- **↑/↓**：历史浏览

## 5. 异常处理与回退

### 5.1 依赖缺失处理
```python
# 示例：优雅降级
try:
    from rich.console import Console
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    
def render_panel(data):
    if HAS_RICH:
        return rich_render(data)
    else:
        return text_render(data)
```

### 5.2 执行异常恢复
- **命令失败**：显示错误码与错误信息，保留日志
- **网络中断**（远程执行）：重试机制与状态保存
- **资源不足**：内存/CPU 监控与警告

### 5.3 数据丢失防护
- 表单输入临时保存
- 执行历史持久化（可选）
- 崩溃后的状态恢复

## 6. 远程执行设计（可选扩展）

### 6.1 配置格式
```yaml
# ~/.qraft/hosts.yml
hosts:
  dev-server:
    host: 192.168.1.100
    user: qraft
    key: ~/.ssh/id_rsa
  prod-cluster:
    host: cluster.example.com
    user: deploy
    port: 2222
```

### 6.2 执行机制
- 使用系统 `ssh` 命令，避免引入额外依赖
- 命令模板：`ssh {user}@{host} -p {port} "cd {workdir} && qraft {args}"`
- 流式读取：`subprocess.PIPE` 实时捕获输出

### 6.3 安全考虑
- SSH 密钥认证优先
- 命令参数严格转义
- 不在命令行暴露敏感信息

## 7. 性能与监控

### 7.1 性能基线
- **启动时间**：< 1秒（冷启动）
- **内存占用**：< 50MB（基础运行）
- **CPU 使用**：< 5%（空闲时）

### 7.2 监控指标
- 实时 CPU/内存使用率（通过 `psutil` 或 `/proc` 读取）
- 执行任务数量与耗时统计
- 错误率与重试次数

### 7.3 优化策略
- 延迟加载非必需模块
- 最小化轮询频率
- 及时释放大对象引用

## 8. 验收标准

### 8.1 功能完整性
- [ ] `qraft tui` 命令正常启动
- [ ] Home/Tasks/Run 三个面板正确显示
- [ ] 基础表单输入与校验工作
- [ ] Dry-run 预览命令准确
- [ ] Ctrl-C 中断安全可靠

### 8.2 兼容性测试
- [ ] Rich 可用环境：面板渲染正常
- [ ] Rich 缺失环境：回退到纯文本
- [ ] prompt_toolkit 可用：表单增强功能
- [ ] prompt_toolkit 缺失：回退到 input()

### 8.3 性能验收
- [ ] 启动时间符合基线要求
- [ ] 内存使用无明显泄漏
- [ ] CPU 占用在可接受范围

### 8.4 文档完整性
- [ ] 用法示例文档
- [ ] 依赖安装说明
- [ ] 常见问题与排错

## 9. 实现计划

### 9.1 优先级排序
1. **核心框架**：tui_cmd.py 基础结构
2. **面板系统**：panels.py 最小实现
3. **表单系统**：forms.py 基础校验
4. **CLI 集成**：cli.py 子命令注册
5. **文档与测试**：示例文档与验收测试

### 9.2 预计工期
- **Day 1**：核心框架 + 面板系统
- **Day 2**：表单系统 + CLI 集成
- **Day 3**：测试、文档与优化

### 9.3 里程碑检查点
- **M1**：基础 TUI 启动与面板切换
- **M2**：表单输入与命令预览
- **M3**：完整执行流程与错误处理

## 10. 风险与缓解

### 10.1 技术风险
- **依赖冲突**：Rich/prompt_toolkit 版本兼容性
  - 缓解：最小版本要求 + 兼容性测试
- **终端兼容性**：不同 shell 与 terminal emulator
  - 缓解：fallback 机制 + 主流环境测试

### 10.2 用户体验风险
- **学习曲线**：从 CLI 到 TUI 的适应
  - 缓解：保持 CLI 习惯 + 清晰的键位提示
- **性能感知**：相比纯 CLI 的延迟感
  - 缓解：优化渲染频率 + 性能监控

### 10.3 维护风险
- **代码复杂度**：TUI 逻辑相比 CLI 更复杂
  - 缓解：模块化设计 + 清晰的抽象边界

## 11. 事后总结（Postmortem）

本次任务按“CLI-first 轻 UI”的原则完成 TUI MVP，实现范围与 task_4.3 规划一致：新增 `qraft tui` 子命令，提供 Home/Tasks/Run 的最小交互与渲染，并在依赖缺失时按设计回退到纯文本路径。

- 实施产物
  - 子命令集成：<mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile>
  - 主控制逻辑：<mcfile name="tui_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/tui_cmd.py"></mcfile>
  - 面板渲染：<mcfile name="panels.py" path="/home/dell/Projects/Qraft/qraft/tui/panels.py"></mcfile>
  - 表单与校验：<mcfile name="forms.py" path="/home/dell/Projects/Qraft/qraft/tui/forms.py"></mcfile>
  - 执行与工件：<mcfile name="launcher.py" path="/home/dell/Projects/Qraft/qraft/tui/launcher.py"></mcfile>

- 关键修复
  - 修复 TypeError: write() argument must be str, not Text（Rich 渲染对象），通过统一使用导出文本的方式解决。
  - 在 `--plain` 模式下关闭 prompt_toolkit，避免在无 TTY 或非交互场景中阻塞与 KeyboardInterrupt。
  - 新增 `--non-interactive` 模式，便于 CI/自检时一次性渲染 Home 并退出。
  - 修复远程执行工具中的 `shlex` 导入遗漏导致的潜在 NameError。

- 自检与验收
  - CLI 注册检查：`python -m qraft.cli --help` 可见 `tui` 子命令。
  - 非交互渲染：`python -m qraft.cli tui --plain --non-interactive` 退出码为 0；输出包含 Home 面板、依赖状态与资源占用信息。
  - 交互路径：在 `--plain` 环境中不使用 prompt_toolkit；在具备 Rich 的环境中，面板文本通过 Rich 导出为字符串进行展示（确保兼容性）。

- 已知限制（MVP 范围内接受）
  - Tasks 面板仅提供 `run` 的最小化入口；其他命令仅列出，未接通表单与执行。
  - Run 面板的资源监控为近似实现（基于 process_time 与 /proc），多核场景可能偏差。
  - `--plain` 当前主要影响输入路径（禁用 prompt_toolkit）；渲染层在安装了 Rich 时仍使用 Rich 的文本导出以获得更清晰的表格展示（可按需求改为完全禁用 Rich）。
  - 远程执行为可选最小实现（基于系统 ssh），真实环境下需补足主机配置管理与错误处理策略。

- 后续可迭代项（非本次验收范围）
  - 完成 Tasks 面板对更多命令的表单与执行串接。
  - 引入更细粒度的日志滚动与过滤、进度条与指标摘要卡片。
  - 丰富非交互模式输出（如 JSON）以支持可编排的上层工具。
  - 增强资源采样精度（如引入 psutil 为可选依赖）。

- 结论
  - 按 task_4.3 的范围与标准，MVP 已通过最小验收：命令可启动、面板可渲染、表单回退合理、Dry-run 预览与本地执行链路具备、并提供 CI 友好的非交互模式。
  - 若需更严格的交互体验与远程编排能力，可在后续里程碑按“后续可迭代项”推进。


## 11. 增量扩展（2025-08）

本次在不改变 MVP 设计边界的前提下，按“CLI-first、轻 UI、优雅回退”的原则，补充了以下能力：

### 11.1 Tasks 面板扩展：支持 validate / quickbacktest / precisebt
- 新增表单：
  - validate：输入 strategy 路径，存在性校验；构建 argv `validate {strategy}`
  - quickbacktest：输入 strategy、prices、可选 start/end；构建 argv `quickbacktest --strategy PATH --prices CSV [--start S] [--end E]`
  - precisebt：在 quickbacktest 基础上，增加 `--engine-mode`（布尔）、`--engine-config`（可选文件路径）、`--spread-bps`、`--commission-bps`、`--slippage-bps`（浮点，提供默认值）、`--allow-fallback-dev`（布尔）；与 CLI 参数保持一致。
- 参数校验：全部使用现有表单工具进行必填/文件存在性检查，避免重复实现。
- 执行路径：统一通过现有 `run_local(argv)` 子进程调用 CLI 实现，避免直接耦合内部函数。
- Dry-run：在执行前展示 `qraft ` 前缀的命令预览，确保可追踪与可审计。

对应代码：
- 表单与参数构建：<mcfile name="forms.py" path="/home/dell/Projects/Qraft/qraft/tui/forms.py"></mcfile>
- TUI 入口与 Tasks 分支：<mcfile name="tui_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/tui_cmd.py"></mcfile>

### 11.2 Run 面板增强：进度、指标卡片与日志过滤
- 进度：
  - 基于日志启发式解析 `progress: 37%` 或 `37/100` 模式，渲染文本进度条（Rich 可用时以 Panel 呈现，否则纯文本）。
- 指标卡片：
  - 从日志尾部提取常见指标（Sharpe、return、max_drawdown、win_rate），以表格展示；未检测到时提示空。
- 日志过滤：
  - 支持运行结束后的临时查看环节中按关键字筛选日志尾部（大小写不敏感），便于快速定位问题。

对应代码：
- 渲染与解析：<mcfile name="panels.py" path="/home/dell/Projects/Qraft/qraft/tui/panels.py"></mcfile>
- 交互入口：<mcfile name="tui_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/tui_cmd.py"></mcfile>

### 11.3 使用说明（新增能力）
- 启动：`qraft tui`（带 Rich/prompt_toolkit 自动增强；`--plain` 回退纯文本；`--non-interactive` 用于 CI 渲染一次即退出）
- 执行 validate/quickbacktest/precisebt：进入 Tasks 面板，选择命令 → 填写表单 → Dry-run 预览 → 确认执行。
- 查看结果：执行结束后进入 Run 面板查看摘要、进度与日志；可按 `f` 进行临时关键字过滤，`b` 返回。

### 11.4 范围控制与依赖
- 未引入新强依赖；继续遵循可选依赖策略（Rich/prompt_toolkit）。
- 仍使用子进程方式调用既有 CLI，避免重复设计与内部接口耦合。
- 所有参数均以 CLI 中 `argparse` 定义为准，表单默认值与类型与 CLI 保持一致。

### 11.5 验收补充
- 纯文本模式与 Rich 模式下的 Tasks 选择与 Run 渲染均正常。
- validate/quickbacktest/precisebt 的命令预览与执行退出码符合预期（以示例路径/数据进行本地验证）。
- Run 面板能在包含典型关键字的日志中解析出进度与指标；在无法解析时优雅显示 N/A。