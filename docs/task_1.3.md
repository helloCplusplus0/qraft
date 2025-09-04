# 任务1.3：数据层架构与快照机制（事前任务设计）

本任务目标：基于最小可用原则，在不引入复杂外部依赖和不自研重型组件的前提下，完成数据层的核心能力：
- 数据快照（snapshot）机制与内容寻址（snapshot_id）
- 交易日历与时区对齐的最小工具
- CSV/Parquet 数据导入器（基于已引入的 Polars/Pandas）
- 最小的数据版本化与谱系（lineage）记录
- 提供最小样例数据集（artifacts/data/sample）与使用文档

约束与原则：
- 禁止过度设计，优先交付可验证的最小闭环
- 严格遵循现有依赖（requirements-stable + constraints），不新增第三方依赖
- 设计风格与代码规范保持与项目一致（类型注解、测试覆盖、mypy/lint）

---

## 1. 架构与目录

- qraft/data/calendar.py：交易日历与时区对齐工具
- qraft/data/snapshot.py：快照的内容寻址、落盘、加载与元数据
- qraft/data/importers/
  - csv.py：CSV 导入器（返回 Polars DataFrame）
  - parquet.py：Parquet 导入器（返回 Polars DataFrame）
- artifacts/data/sample/：最小样例数据（CSV）
- 文档：docs/task_1.3.md（本文件，事前设计 + 事后总结）

## 2. 核心接口设计（MVP）

1) 交易日历（仅工作日，暂不含节假日）：
- class TradingCalendar:
  - sessions(start: date/datetime, end: date/datetime) -> list[date]: 返回[start, end]之间的工作日（Mon-Fri）
  - is_trading_day(d: date) -> bool
  - tz: str（默认"UTC"）
- 辅助：
  - align_tz(df: pl.DataFrame, column: str = "timestamp", tz: str = "UTC") -> pl.DataFrame

2) 快照机制（内容寻址）：
- compute_snapshot_id(datasets: dict[str, pl.DataFrame], extra_meta: dict[str, object] | None) -> str
  - 使用稳定序列化（按列名排序、行排序可选）与哈希（SHA256），结合可选的额外元数据字段
- save_snapshot(datasets: dict[str, pl.DataFrame], base_dir: str = "artifacts/data/snapshots", meta: dict | None = None) -> tuple[str, str]
  - 将每个 DataFrame 落盘为 Parquet（或 CSV 作为回退），写入 metadata.json（包含：snapshot_id、created_at、sources、parent_snapshot_id、columns、n_rows）
  - 返回 (snapshot_id, path)
- load_snapshot(snapshot_id: str, base_dir: str = "artifacts/data/snapshots") -> dict[str, pl.DataFrame]

3) 导入器：
- read_csv(path: str, *, infer_schema_length: int | None = None) -> pl.DataFrame
- read_parquet(path: str) -> pl.DataFrame

4) 版本化与谱系（最小）：
- metadata.json 中记录：
  - snapshot_id（内容寻址）
  - created_at（ISO8601, UTC）
  - sources（输入文件路径及其哈希，可选）
  - parent_snapshot_id（可选）
  - tables 概览（列名、行数）

## 3. 验收标准

- 功能性：
  - 能够生成 snapshot_id，并将数据与元数据落盘，再成功加载
  - 交易日历能正确过滤周末，时区转换对齐正常
  - 导入器可以读取 CSV 与 Parquet（基于现有 Polars）
- 质量门：
  - make lint && make mypy && make test 全部通过
  - 新增单测覆盖核心路径（快照、日历、导入器），总体覆盖率≥80%
- 文档：
  - 本文件事后更新为总结，包含样例与限制说明
  - 提供 artifacts/data/sample/ 的最小数据示例并在文档中示范

## 4. 样例与使用

- 生成快照：
  - 从 CSV 导入数据：qraft.data.importers.read_csv
  - 保存快照：qraft.data.snapshot.save_snapshot
  - 加载快照：qraft.data.snapshot.load_snapshot
- 交易日历：
  - TradingCalendar().sessions(start, end)
  - align_tz(df, column="timestamp", tz="Asia/Shanghai")

## 5. 局限与后续计划（不阻碍验收）
- 暂不包含节假日日历（仅工作日 Mon-Fri），后续可接入 pandas_market_calendars 或 exchange specific 日历
- 复权/连一流水线仅在元数据层面预留，不在本任务实现
- 谱系追踪为最小实现（sources 路径与哈希），后续可扩展为图模式

以上为本任务的事前设计。实现完成并通过质量门后，将在本文件追加“事后总结与反思”。

---

# 事后总结与验收（MVP v1 可用）

验收结论：通过。已实现并验证以下内容：
- 数据快照：compute_snapshot_id / save_snapshot / load_snapshot（内容寻址、Parquet落盘、metadata写入）
- 交易日历：TradingCalendar.sessions/ is_trading_day；align_tz实现时区对齐
- 导入器：read_csv / read_parquet（基于Polars）
- 最小样例目录：artifacts/data/sample/（占位符，测试按需生成文件）

质量门：
- make lint && make mypy && make test 全部通过
- 覆盖率：Total 92%

关键实现说明：
- snapshot_id：对每张表按列名排序后进行行序列化为JSON，再做sha256（前16位作为ID）；extra_meta纳入hash保证可复现
- metadata.json：记录snapshot_id、created_at(UTC-ISO8601)、parent_snapshot_id（可选）、tables（name/n_rows/columns）
- 时区对齐：align_tz使用Polars dt.convert_time_zone，调用方须保证列为Datetime类型（若原始为naive需先设置时区）

限制与后续：
- 节假日未覆盖，仅Mon-Fri；后续如需更精细可引入交易所日历
- 复权/连一流水线未实现，仅在元数据层面预留parent_snapshot_id
- 谱系追踪为最小实现，后续可扩展sources与hash

测试样例（摘要）：
- test_snapshot_save_and_load：生成快照后再次加载，结构一致
- test_snapshot_id_stable：列顺序变化不影响snapshot_id
- test_sessions_excludes_weekends：周内5个交易日
- test_align_tz_polars：timestamp列时区对齐为Asia/Shanghai
- test_read_csv_and_parquet：CSV/Parquet导入成功

反思：
- 坚持“最小可用”原则，避免提前设计复杂的数据编目/谱系图；接口尽量稳定、实现可迭代
- 在Polars下进行内容寻址需注意datetime可序列化性，本次通过ISO化修复
- 将更大功能（节假日、复权流水线）留作后续任务，保持边界清晰