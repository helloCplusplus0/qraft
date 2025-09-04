# Task 6.3.1 Fix Plus — 工件写入的原子性与一致性加固（P0）

目标（不改动架构、低风险高价值）：
- 对 artifacts 关键工件写入采用原子写（tmp → fsync → rename），必要时引入文件锁（同机并发生效）。
- 覆盖范围：EvidencePack blobs/manifest、部署 CURRENT.json/HISTORY.json、TUI 运行状态、benchmark 快速回测输出等已落地的关键写入点。
- 充分复用现有 API，按最小改动原则落地，不做过度设计。

实现摘要：
- 新增 <mcfile name="atomic.py" path="/home/dell/Projects/Qraft/qraft/utils/atomic.py"></mcfile>：提供原子写工具函数
  - <mcsymbol name="safe_write_bytes" filename="atomic.py" path="/home/dell/Projects/Qraft/qraft/utils/atomic.py" startline="40" type="function"></mcsymbol>：字节写入（同目录临时文件 → fsync → os.replace → fsync 父目录），可选同机锁
  - <mcsymbol name="safe_write_text" filename="atomic.py" path="/home/dell/Projects/Qraft/qraft/utils/atomic.py" startline="73" type="function"></mcsymbol>：文本写入（封装字节）
  - <mcsymbol name="safe_json_dump" filename="atomic.py" path="/home/dell/Projects/Qraft/qraft/utils/atomic.py" startline="77" type="function"></mcsymbol>：JSON 写入（封装文本），默认 ensure_ascii=False, indent=2
- POSIX 保障：rename 原子性 + fsync 数据与目录项，锁采用 fcntl.flock（若不可用则降级为无锁但仍保持原子替换）。

接入点改动（按模块）：
- 部署灰度
  - <mcfile name="grayscale.py" path="/home/dell/Projects/Qraft/qraft/deployment/grayscale.py"></mcfile>
    - <mcsymbol name="approve_and_publish" filename="grayscale.py" path="/home/dell/Projects/Qraft/qraft/deployment/grayscale.py" startline="215" type="function"></mcsymbol>：CURRENT.json、HISTORY.json 改为 <mcsymbol name="safe_json_dump" filename="atomic.py" path="/home/dell/Projects/Qraft/qraft/utils/atomic.py" startline="77" type="function"></mcsymbol>
    - <mcsymbol name="rollback" filename="grayscale.py" path="/home/dell/Projects/Qraft/qraft/deployment/grayscale.py" startline="260" type="function"></mcsymbol>：同上。
- Evidence Pack
  - <mcfile name="pack.py" path="/home/dell/Projects/Qraft/qraft/evidence/pack.py"></mcfile>
    - <mcsymbol name="EvidencePack.save_to_directory" filename="pack.py" path="/home/dell/Projects/Qraft/qraft/evidence/pack.py" startline="96" type="function"></mcsymbol>：blobs 写入由 write_bytes 改为 <mcsymbol name="safe_write_bytes" filename="atomic.py" path="/home/dell/Projects/Qraft/qraft/utils/atomic.py" startline="40" type="function"></mcsymbol>；MANIFEST.json 改为 <mcsymbol name="safe_json_dump" filename="atomic.py" path="/home/dell/Projects/Qraft/qraft/utils/atomic.py" startline="77" type="function"></mcsymbol>
- TUI 运行状态
  - <mcfile name="launcher.py" path="/home/dell/Projects/Qraft/qraft/tui/launcher.py"></mcfile>
    - <mcsymbol name="write_status" filename="launcher.py" path="/home/dell/Projects/Qraft/qraft/tui/launcher.py" startline="35" type="function"></mcsymbol>：状态 JSON 改为 <mcsymbol name="safe_json_dump" filename="atomic.py" path="/home/dell/Projects/Qraft/qraft/utils/atomic.py" startline="77" type="function"></mcsymbol>
- 辅助脚本
  - <mcfile name="benchmark_quickbacktest.py" path="/home/dell/Projects/Qraft/scripts/benchmark_quickbacktest.py"></mcfile>：输出 artifacts/benchmark_quickbacktest.json 使用 <mcsymbol name="safe_json_dump" filename="atomic.py" path="/home/dell/Projects/Qraft/qraft/utils/atomic.py" startline="77" type="function"></mcsymbol>
- CLI 证据包命令
  - <mcfile name="evidence_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/evidence_cmd.py"></mcfile>：顶层 evidence.json 使用 <mcsymbol name="safe_json_dump" filename="atomic.py" path="/home/dell/Projects/Qraft/qraft/utils/atomic.py" startline="77" type="function"></mcsymbol>

兼容性与行为说明：
- 读路径保持不变，不影响 TUI Monitor 与 CLI 读取逻辑。
- 在单机并发写同一路径时，.lock 文件用于短时互斥，降低并发写入破坏概率；若系统无 fcntl，降级为无锁但保留原子替换。
- 临时文件位于目标目录，避免跨文件系统 rename 失去原子性；写入后 fsync 目录项，增强崩溃后一致性。

设计取舍与遵循：
- 轻量化：仅新增一个小型工具模块，无外部依赖；调用点最小改动。
- 充分复用：统一以 safe_* API 封装，调用端无需关心细节；参数默认值与之前一致（indent/ensure_ascii）。
- 无过度设计：未引入全局锁服务、未改变目录结构与 Schema。

验证与影响面：
- 单元测试与 TUI 演示路径无需改动；人工复测了部署发布/回滚，Monitor 面板正常显示，HISTORY 追加记录正确。
- EvidencePack 保存目录的 blobs 在写入失败时不会出现半文件；MANIFEST.json 与 evidence.json 保证写入完整性。

后续可选（非 P0）：
- 针对 results.jsonl/aggregated.json 的写入点，一旦落地实现后，直接复用同一套 safe_* API 即可，无需新增设计。
- 在需要时暴露 use_lock=False 的选项，让只读 NFS 或 CI 环境可关闭锁以规避兼容性问题。