# Task 6.3.6 Fix Plus — evidence.json 校验：定义 JSONSchema 与 CLI --validate

目标：
- 为 evidence.json 定义独立 JSON Schema，确保第三方可离线校验。
- 在 CLI `qraft validate` 中新增 `--type evidence`，与策略校验共用统一入口与错误格式。
- 复用现有 API 与风格（StrategyValidator → EvidenceValidator），禁止过度/重复设计。

落地改动：
1) 新增 Schema
- 文件：qraft/schemas/evidence_v1.json
- 结构对齐 evidence_cmd._build_evidence_document 的产出：
  - schema_version, inputs, fingerprints, stats, sensitivity, env, created_at, evidence_fingerprint
  - 严格限制指纹字段为 sha256 格式；其余字段保持最小约束，避免过拟合。

2) 新增 EvidenceValidator（最小一致风格）
- 文件：qraft/validators/evidence_validator.py
- 校验步骤：
  - JSON Schema 校验（Draft 2020-12，与策略校验一致）
  - 核心指纹一致性：按 evidence_cmd 的构造方式，用 core 字段重算 evidence_fingerprint，对比一致性。
- 对外导出：qraft/validators/__init__.py 暴露 EvidenceValidator。

3) CLI 集成（与策略校验一致风格）
- validate_cmd.py：
  - _cmd_validate(path, type="strategy")，当 type=="evidence" 调用 EvidenceValidator。
  - 维持原有错误语义：校验失败抛 QraftError(ErrorCode.VALIDATION_ERROR, details={errors})。
- cli.py：
  - validate 子命令增加 `--type {strategy,evidence}`，默认 strategy。
  - 统一错误处理沿用 cli.main 已实现的特判：保留人类友好输出与 rc=1。

设计与约束遵循：
- 充分利用现成 API：
  - 继续复用 jsonschema 骨架与 validators 包结构，无自研解析器/DSL。
  - 指纹复算复用 EvidencePack.compute_content_hash 与 evidence_cmd 的核心布局。
- 禁止过度/重复设计：
  - 不引入额外的包/复杂插件；仅最小必要字段与一致性校验。
  - 不假设外部目录结构；纯基于 evidence.json 自身即可校验。

使用方法：
- 校验策略：
  - qraft validate path/to/strategy.json --type strategy
- 校验证据：
  - qraft validate path/to/evidence.json --type evidence
- 输出与退出码：
  - 成功：打印 OK 文本，退出码 0。
  - 失败：人类可读“FAILED: …”+ 列出 errors，退出码 1（沿用现有 validate 特判）。

兼容性与影响评估：
- 与现有 evidence_cmd 产出的 evidence.json 完全对齐；第三方仅需 jsonschema 与本仓 JSON 即可离线校验。
- 对其他模块无破坏性影响；validate 子命令保持向后兼容（默认策略）。

相关文件：
- qraft/schemas/evidence_v1.json（新增）
- qraft/validators/evidence_validator.py（新增）
- qraft/validators/__init__.py（导出新增）
- qraft/cli_impl/validate_cmd.py（扩展类型选择）
- qraft/cli.py（增加 --type）

结论：
- 已按“先落地，后完美”的原则完成最小可用实现；第三方可独立对 evidence.json 进行结构与指纹一致性的校验，满足可审计与可复现目标。