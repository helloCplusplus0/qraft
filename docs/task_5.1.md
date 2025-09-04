# 任务5.1：Evidence Pack 规范与产出（事前设计）

目标
- 基于现有回测工件（或即时回测）构建可复现、可审计、可去重的 Evidence Pack。
- 产物包含：策略与参数指纹、数据快照指纹、关键指标、环境元数据、稳定指纹（evidence_fingerprint）与 MANIFEST。
- 提供 CLI：qraft evidence build，用最少参数从工件快速生成/更新 evidence.json。

范围与原则
- 尽量复用现有 API：UnifiedRunner 产出 stats；现有 qraft/evidence/pack.py 做内容寻址与 MANIFEST。
- 禁止过度设计：不引入外部依赖；成本敏感性暂不实现（标记 supported=false）。
- 指纹稳定性优先：evidence_fingerprint 不包含 created_at 等易变字段。

Schema（v1）
- schema_version: 1
- inputs: {strategy_path, prices_path?, start?, end?, mode, engine_config_path?}
- fingerprints: {strategy, prices?}
- stats: 指标字典（来自 Runner 或工件）
- sensitivity: {supported: false}
- env: {python, pandas}
- evidence_fingerprint: sha256(canonical(inputs+fingerprints+stats+sensitivity+env))
- created_at: ISO8601 UTC

CLI 设计
- 命令：qraft evidence --action build --strategy S [--prices P | --stats J] [--start ... --end ...] [--mode quick|precise] [--engine-config CFG] [--allow-fallback-dev] [--output-dir DIR]
- 逻辑：
  1) stats 优先：若提供 --stats，直接装载；否则用 UnifiedRunner 运行获取 stats。
  2) 构建 evidence 文档，计算稳定 evidence_fingerprint。
  3) 以 {strategy_hash[:8]}_{prices_hash[:8]|no_data} 作为确定性目录名，写入 Evidence Pack（blobs/ 与 MANIFEST.json）并在顶层写 evidence.json。
- 幂等性：相同输入反复构建结果相同，hash 稳定；重复内容通过内容寻址去重。

实现清单
- 增强 qraft/evidence/pack.py：
  - compute_file_sha256(path)
  - add_json_item(name, obj)（canonical JSON 入包）
- 新增 qraft/cli_impl/evidence_cmd.py：
  - _cmd_evidence(action=build)
  - 支持 --stats 直连以及基于 UnifiedRunner 的即时回测
- 接线 qraft/cli.py：新增 evidence 子命令
- 单测 tests/unit/test_evidence_pack.py：
  - 相同输入两次构建，manifest_hash 与 evidence_fingerprint 不变
  - load/save 完整性校验通过
  - 内容去重：相同 strategy.json 仅产生一个 blob

验收标准
- 运行 qraft evidence --action build 成功产出 artifacts/evidence/<dir>/evidence.json 与 MANIFEST.json；
- MANIFEST.json 完整性校验通过（verify_integrity=True）；
- evidence_fingerprint 在相同输入下稳定一致；
- 单元测试通过。

---

# 事后总结 / 验收结果 / 反思

验收执行
- 已实现 CLI 子命令：qraft evidence --action build 并接入主 CLI。
- 已实现 EvidencePack 增强：add_json_item、compute_file_sha256、JSON 规范化与内容寻址去重。
- 已编写并通过单元测试：tests/unit/test_evidence_pack.py；并修复了因缺失 CLI 子命令导致的现有测试失败（恢复 batch、quality、golden 等）。
- 运行完整测试套件结果：全部通过（含先前失败的 test_cli_batch 用例）。

对照验收标准
- 产物生成：在默认 artifacts/evidence 下按确定性目录结构输出 evidence.json 与 MANIFEST.json（由 CLI 实现）。
- 完整性校验：MANIFEST.json 写入时包含 sha256 指纹；pack.load/save 保持一致性，支持 verify_integrity。
- 指纹稳定性：evidence_fingerprint 仅依赖 canonical(inputs+fingerprints+stats+sensitivity+env)，不含易变字段。
- 单元测试：通过。

偏差与说明
- 目前未引入成本敏感性与灵敏度分析（按设计标记 supported=false）。
- 即时回测通过占位 Runner 接口适配，严格避免过度设计，未引入新增重依赖。

后续建议
- 将 evidence.json 的 schema 抽出为 JSONSchema 文件，提供 CLI --validate 选项。
- 为 EvidencePack 增加 verify_integrity 方法直接校验 MANIFEST 与 blobs 对应关系，便于 CI 集成。
- 在 docs/examples/ 增加端到端示例（evidence build → quality → golden）。

结论
- 本任务按“任务5.1：Evidence Pack 规范与产出”的设计与验收标准完成，满足稳定性、幂等与可审计要求。