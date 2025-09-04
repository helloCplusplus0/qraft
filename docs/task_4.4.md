# 任务 4.4：最小配方（Recipes）与可复现执行（事前设计）

本任务旨在在不引入新依赖（如 PyYAML）的前提下，提供一个最小可用的“配方（Recipe）”清单格式与渲染执行引擎，支持声明式地组合 Qraft CLI 子命令参数，实现可预览、可复用、可干跑（dry-run）与可复现的执行路径。

- 约束与原则：
  - 不新增第三方依赖（使用内置 json）。
  - 复用现有能力：qraft.cli（命令集合）、qraft.tui.launcher.run_local（子进程执行、run_id/工件管理）。
  - 安全：严格以 argv 列表方式传参，不经过 shell 解析；提供 dry-run 预览。
  - 轻量：最小化 Schema，避免模板引擎；不做复杂 DSL。

- 交付物：
  - 源码：qraft/tui/recipes.py（加载/校验/渲染/预览/执行/预设）。
  - 文档示例：docs/examples/tui_recipes/*.json（run / quickbacktest / precisebt / gridsearch / search run）。
  - 设计与验收文档：本页，后续更新为事后总结。

## 1. Recipe Manifest 规范（JSON）

采用 JSON 清单，字段如下：
- name: 配方名称（字符串）
- cmd: 基础子命令令牌列表（数组），例如 ["run"], ["quickbacktest"], 或多级子命令 ["search","run"]
- vars: 变量定义（对象，键为变量名）
  - type: 可选，str|int|float|bool|path（用于类型转换和校验）
  - default: 可选，默认值
  - choices: 可选，枚举集合
  - required: 可选，布尔，默认在没有 default 时视为 True
- params: 参数映射（数组，每个元素定义如何把变量映射为 CLI 参数）
  - key: 变量名（与 vars 中一致）
  - arg: 可选，字符串，CLI 选项名（如 "--strategy"）；当省略且 positional=true 时作为位置参数加入
  - positional: 可选，布尔，若为 True 则仅将值追加为位置参数
  - style: 可选，仅对 bool 有效，"flag"（值为 True 时输出 arg）或 "switch"（true_arg/false_arg 二选一）
  - true_arg/false_arg: 可选，当 style="switch" 时指定

说明：
- 不引入占位符模板，变量通过 vars 定义与 params 绑定，渲染时在 overrides 中提供值。
- bool 类型默认采用 style="flag"（True 输出 arg，False 不输出）。

## 2. 渲染与校验算法

- 加载：从 JSON 文件读取 manifest（UTF-8）。
- 校验：
  - cmd 必须为非空字符串数组；vars/params 类型正确。
  - 每个 params[i].key 必须存在于 vars。
  - required 变量必须在 overrides 或 default 中给出。
  - choices 校验（在转换后进行）。
- 类型转换：按 vars[key].type 将字符串/数字/布尔转换为目标类型；path 视为 str。
- 参数展开：
  - argv 基础为 cmd 列表；随后按 params 顺序展开。
  - 若 positional=true：append(str(value))。
  - 若 arg 存在：
    - 非 bool：append(arg); append(str(value))。
    - bool + style=flag：value 为 True 时 append(arg)。
    - bool + style=switch：append(true_arg/false_arg)。
- 预览：生成 "qraft " + " ".join(shlex.quote(t) for t in argv)。
- 执行：调用 qraft.tui.launcher.run_local(argv, run_id_prefix="recipe")，实时日志与状态写入 artifacts/<run_id>/。
- dry-run：返回 (preview, argv) 不执行。

## 3. 资产化与复用

- 预设（preset）保存/加载：提供 save_preset(path, values) 与 load_preset(path) 简单 JSON 序列化，便于复用同一配方的参数集合。
- 内置示例：在 docs/examples/tui_recipes/ 提供 4-5 个 JSON 清单，覆盖 run/quickbacktest/precisebt/gridsearch/search run。

## 4. 安全与可复现

- 全流程使用 argv 列表传参，不经 shell。
- dry-run 输出完整预览和 argv，便于在 CI/评审中复核。
- 执行引擎复用 run_local，run_id 与产物路径统一管理；日志写入 artifacts/<run_id>/<run_id>.log，状态写入 *_status.json。

## 5. 与现有代码的集成点

- qraft/cli.py 已具备 run/quickbacktest/precisebt/gridsearch/search run 等子命令，recipes 仅构造 argv 后交由 CLI 执行。
- qraft/tui/launcher.py 提供 run_local/iter_stream 等能力，直接复用。

## 6. 最小使用示例（预期）

- 加载清单：manifest = load_manifest("docs/examples/tui_recipes/quickbacktest.json")
- dry-run：preview, argv = preview_recipe(manifest, overrides)
- 执行：status, tail = run_recipe(manifest, overrides)

其中 overrides 例如：
```
{
  "strategy": "sample_strategy.json",
  "prices": "sample_prices.csv",
  "start": null,
  "end": null
}
```

## 7. 验收标准（对齐 task_list.md）

- 定义 Recipe Manifest（JSON）：支持变量、默认值、枚举/校验；渲染为 CLI argv 并提供预览。
- 执行引擎：以子进程方式执行组合后的 CLI，实时流式日志；退出码与错误路径可见；产物路径与 run_id 统一管理。
- 资产化与复用：可保存/导入参数预设；提供 run/quickbacktest/precisebt/gridsearch/search 的内置示例清单。
- 安全与可复现：严格安全转义（通过 argv 列表传参）；支持 --dry-run（API 暴露）。

## 8. 任务拆解

1) 编写本设计文档（本文件）
2) 实现 qraft/tui/recipes.py：加载/校验/渲染/预览/执行/预设
3) 新增 docs/examples/tui_recipes/*.json 内置清单
4) 本地最小验证：对 quickbacktest 清单进行 dry-run 与实际执行
5) 更新本文件为事后总结（完成度、差异、后续项）

---

下方将在实现与验收后追加“事后总结”。

---

# 事后总结（验收）

本节在实现与本地验证后补充，记录完成度、与设计差异以及后续优化项。

- 完成度：
  - 核心模块 qraft/tui/recipes.py 已实现，包含：Manifest 加载/校验、类型转换与 choices 校验、参数渲染、预览（dry-run）、执行（复用 run_local）、预设保存/加载。
  - 内置示例清单已添加：docs/examples/tui_recipes/{run, quickbacktest, precisebt, gridsearch, search_run}.json。
  - 本地验证：
    - dry-run 预览 run.json 成功生成：qraft run --strategy ... --prices ... --mode auto --fmt text。
    - 实际执行示例：以最小 manifest（cmd=["ops"]) 触发 qraft ops，子进程运行成功，日志流式写入 artifacts/recipe_*，尾部输出包含运算符列表，退出码为 0。

- 与设计差异：
  - 无新增依赖，严格遵循设计约束。
  - bool 渲染实现同时支持 flag 与 switch，两者在示例中均有覆盖（如 run.json 的 freeze、search_run.json 的 fast/precise）。

- 后续优化建议：
  - 为 manifest 增加可选的简单静态描述字段（如 doc/notes），用于 TUI 展示。
  - 结合 qraft.tui.panels 在 TUI 界面中提供 manifest 的引导式填写与执行入口。
  - 增加基础校验器，针对不同 cmd 的最小参数集合给出更友好错误提示。