# Task 6.3.3 — CLI 错误模型统一与退出码规范化（fix_plus）

本次改进目标：在不改变现有行为与文案的前提下，补充统一的错误模型与错误码枚举，并确保 CLI 错误路径统一以 exit code=2 收敛，增强下游编排与可观测性。


## 设计原则（务实落地）
- 不做过度设计：仅引入最小可用的错误类型与错误码枚举，保持与现有 CLI 行为一致。
- 充分利用现有 API：沿用既有打印文案与返回码规范；新增统一异常供后续逐步采用。
- 向后兼容：不修改既有用户可见文案与返回码语义，测试保持通过。


## 实现内容
1) 新增统一错误类型与错误码枚举
- 位置：qraft/errors.py
- 内容：
  - ErrorCode（Enum）：VALIDATION_ERROR、FILE_NOT_FOUND、DEPENDENCY_MISSING、INVALID_ARGUMENT、ENGINE_CONFIG_NOT_FOUND、RUNTIME_ERROR
  - QraftError（Exception）：包含 code、message、details；提供 to_dict() 便于结构化输出。

2) CLI 入口统一异常处理
- 位置：qraft/cli.py → main()
- 逻辑：
  - 捕获 QraftError：
    - 当 fmt=json 时，输出标准 JSON：{"ok": false, "error": {"code": <name>, "message": <str>, "details": {...}}}；
    - 当 fmt=text 或无 fmt 时，输出人类可读错误：Error[<CODE>]: <message> 到 stderr；
    - 统一返回码 2。
  - 其他未捕获异常保留原有逻辑：打印 "Error: ..." 到 stderr，返回码 2。
- 说明：现阶段未强制子命令改造为抛出 QraftError，保持向后兼容；后续可在关键路径逐步替换（例如文件不存在、依赖缺失等）。

3) 退出码规范
- 成功：0（不变）
- 策略校验失败（已存在约定）：1（validate 子命令保持不变）
- 其他错误：2（不变，且主入口对 QraftError 与一般异常统一为 2）


## 使用示例（逐步采纳）
- 在子命令中，如需统一错误模型，可按需抛出：
  - from qraft.errors import QraftError, ErrorCode
  - raise QraftError(ErrorCode.FILE_NOT_FOUND, f"file not found: {path}")
- main() 将按 fmt 输出结构化/文本错误，并以 rc=2 退出；现有测试断言的关键文案（如 "file not found"、"engine-config file not found"）保持可匹配。


## 向后兼容性与影响面
- 行为兼容：不改变现有 stdout/stderr 主要文案与返回码；现有测试全部通过。
- 采纳节奏：
  - 立即可用：新路径可直接抛出 QraftError 以获得一致的结构化输出与 rc=2；
  - 渐进替换：老路径继续沿用 print + return 2，不影响；后续按需替换为 QraftError。


## 测试结论
- 全量测试已通过（含 CLI 解析与各子命令的成功/失败情形）。


## 变更清单
- 新增：qraft/errors.py（ErrorCode, QraftError）
- 修改：qraft/cli.py（main 捕获 QraftError，统一错误输出与 rc=2）


## 后续建议（可选）
- 按模块（deploy / precisebt / gridsearch / quickbacktest / riskctrl）分阶段将典型错误（文件缺失、依赖缺失、参数非法、运行时失败）改为抛出 QraftError，保证文案不变、rc 仍为 2。
- 当下游需要机器可读错误时，优先在支持 --fmt json 的子命令中配合 QraftError 使用，便于编排与告警。