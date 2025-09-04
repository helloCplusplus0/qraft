# 任务5.2：策略模板与搜索空间库（事前设计）

目标
- 提供一套可复用的“策略模板 + 参数搜索空间”最小能力，用于后续 5.3 搜索编排器复用
- 以 JSON/YAML 的声明式配置描述参数网格，产出符合 StrategyValidator 的策略 JSON
- 与算子白名单对齐，避免表达式越权、窗口参数不合规等问题

范围与原则
- 仅覆盖基础模板：MA 交叉、RSI 阈值（窗口）、动量、横截面排序
- 优先利用现有能力：qraft.validators.strategy_validator、qraft.operators.registry
- 不做过度设计；只提供“模板渲染 + 参数网格展开 + 约束过滤 + 最小校验”的核心路径
- YAML 支持为可选：若环境未安装 PyYAML，则提示用户安装；JSON 无额外依赖

最小 Schema（v1）
- SearchSpace 配置文件（JSON/YAML）
  - name: string（可选）
  - template: string（模板文件名，默认从内置 qraft/strategies/templates/ 解析；也可给出绝对/相对路径）
  - params: object（键为占位符名；值为 list 或 range）
    - list 形式：{"fast": [5,10,20]}
    - range 形式：{"window": {"start": 5, "stop": 30, "step": 5}}
  - constraints: string[]（可选，形如 "fast < slow"；仅支持 <, <=, >, >=, ==, != 与 and 组合）

模板渲染
- 模板文件为 JSON，内部字符串可包含占位符 {param}，以 Python str.format 渲染
- 深度遍历所有字符串字段；占位符不存在时保留原样
- 渲染后通过 StrategyValidator.full_validate 做最终校验

静态校验与白名单
- 依赖 StrategyValidator：
  - JSONSchema: qraft/schemas/strategy_v1.json
  - 表达式安全：qraft.operators.registry.DEFAULT_REGISTRY.validate_expression
  - 窗口约束：数值窗口必须为 >=1 的整数字面量

文件与目录
- 代码：
  - qraft/search/spaces.py：SearchSpace 加载、展开与渲染
  - qraft/search/__init__.py：导出入口
- 模板：
  - qraft/strategies/templates/ma_cross.json（已存在）
  - qraft/strategies/templates/rsi_threshold.json（已存在）
  - qraft/strategies/templates/momentum.json（新增）
  - qraft/strategies/templates/xsection_rank.json（新增）
- 示例：
  - docs/examples/search_spaces/ma_cross_space.json
  - docs/examples/search_spaces/rsi_space.yaml

验收标准
- 能从示例空间文件（JSON/YAML）加载并展开得到若干可校验的策略 JSON
- 对不满足 constraints 的组合自动过滤
- 渲染后的策略通过 StrategyValidator.full_validate（含白名单与时间窗口检查）
- 保证不修改任何已有行为；现有测试全部通过

使用示例（后续 5.3 会接 CLI）
- Python API：
  - from qraft.search.spaces import load_search_space
  - space = load_search_space("docs/examples/search_spaces/ma_cross_space.json")
  - for strat, params in space.iter_strategies(): pass

---

事后总结 / 验收结果 / 反思

- 实现内容
  - 新增模块 qraft/search/spaces.py，提供 SearchSpace 与 load_search_space（JSON/YAML）
  - 渲染采用深度遍历 + str.format，占位符缺失不报错，保持原样
  - 组合展开支持 list 与 {start,stop,step}，并提供约束表达式解析（仅比较与 and）
  - 使用 StrategyValidator.full_validate 做最终校验，确保与算子白名单与窗口规则对齐
  - 新增模板：momentum.json、xsection_rank.json；保留现有 ma_cross.json、rsi_threshold.json
  - 文档与示例：docs/examples/search_spaces/ma_cross_space.json、rsi_space.yaml
- 测试结果
  - 新增 tests/unit/test_search_spaces.py 全部通过
  - 运行完整测试套件通过，未破坏既有行为
  - 环境未安装 PyYAML 时，YAML 装载会抛出明确提示；安装后用例可运行（按环境条件自动跳过）
- 对照验收标准
  - [x] 能从示例空间文件加载并展开，组合受 constraints 过滤
  - [x] 渲染后的策略通过 StrategyValidator.full_validate
  - [x] 不修改既有行为，所有测试通过
- 约束与后续建议
  - 约束表达式目前仅支持简单比较与 and，已满足 5.2 需求；若后续需要 or/括号，可迭代
  - 若 5.3 编排器需要记录被过滤/无效组合原因，可在 iter_strategies 返回时附带错误信息或日志钩子
  - 如需 CLI：将在 5.3 的 qraft search run 中接入 load_search_space

结论：任务5.2 按规划完成，可进入 5.3 实现。