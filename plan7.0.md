下面是我根据你给出的原始草案、补充说明，以及我们整个讨论（多数据源、轻量化、模式发现优先、透明化/可解释性要求）重新整理并**完善后的 Qraft7.0 — 数据流驱动自动化模式探索（MVP）设计文档**。
目标是：**MVP 功能简洁但架构完整、且严格保证可扩展性、可观测性与对人/LLM 的可解释性**。请把它当作工程级交付物：既能交付最小可运行版本，也能做为后续迭代的蓝图。

---

# Qraft7.0 — 数据流驱动自动化模式探索（MVP）设计文档（最终版）

## 一、总览（一句话）

Qraft7.0 是一个以**实时/近实时数据流**为输入、对多源多模态数据做**统一预处理 + 自动化模式发现（漂移/聚类/异常/频繁模式）**，并把结果以**结构化 + 可视化 + 可解释**的方式呈现给人或 LLM 的平台。MVP 聚焦模式发现核心能力与可见性/透明性。

---

## 二、设计原则（必须遵守）

1. **最小实现，架构完备**：MVP 功能可简，但每一层都必须规范化、模块化，便于未来替换或扩展（插件化、接口化）。
2. **配置驱动，不改代码**：新增/修改数据源与预处理策略通过配置或 UI，不修改运行代码。
3. **轻量优先、按需升级**：MVP 用更轻量的消息总线（NATS / Redpanda）与 Python 微服务；当规模扩大再切换 Kafka/Flink。
4. **可观测 + 透明**：每个环节必须可视化（数据接入 → 预处理 → 模式引擎 → 存储 → 呈现），避免黑箱。
5. **结果对人/LLM 双可读**：模式事件既有结构化 JSON 也有自然语言解释（可由规则 + LLM 生成）。
6. **工程防护**：对外部库（如 CapyMOA）做版本锁定、adapter 抽象、自动回放测试与回退路径。

---

## 三、逻辑架构（高层）

```
多数据源(行情/新闻/DB/文件/爬取) 
     ↓
[Data Ingest / Adapters]  (config-driven)
     ↓
[Message Bus] (NATS / Redpanda; Kafka 可替换)
     ↓
[Preprocessing & Stream Manager] 
     ├─ Common cleaning/validation
     ├─ Source-specific operator pipelines (config-driven)
     └─ Windowing / Basic feature enrichment
     ↓
[Pattern Discovery Engine]
     ├─ River (baseline)
     └─ CapyMOA (performance / extended algos)
     ↓
[Pattern Store] (ClickHouse)
     ↓
[Presentation Layer]
     ├─ Real-time Monitoring (Grafana + Prometheus)
     ├─ Pattern Exploration (Superset + custom frontend)
     └─ Explain API (LLM integration / human-readable cards)
     ↓
[Audit / Experiment Records] (MLflow / DVC + Git)
```

---

## 四、详细设计（按层）

### 1) 数据接入层（Data Ingest / Adapter）

**职责**：把任意数据源（结构化/半/非结构化）安全、统一、低延迟地接入系统，输出标准事件到消息总线。

**实现要点（MVP）**

* **适配器插件**（每类源一或多个 adapter）

  * Market websocket adapter, REST poller, DB poller, file watcher, web crawler, email/pdf ingestor, social stream.
  * 每个 adapter 只负责：拉取 → 初步 parsing → 抽取 timestamp/unique id → emit event。
* **配置驱动**：YAML/JSON 存放源配置（`name/type/endpoint/parser/transform`），支持动态 reload。
* **管理界面（后期）**：MVP 先用配置文件 + CLI 管理，短期内实现一个简单 Web 表单读写配置（可选）。
* **输出格式（标准事件）**（示例 schema，下文重复使用）：

```json
{
  "event_id": "uuid",
  "source": "binance_spot",
  "type": "trade",
  "timestamp": "2025-09-04T11:00:00.123Z",
  "ingest_time": "2025-09-04T11:00:00.321Z",
  "payload": { ... },
  "meta": { "parser_version": "v1.2", "raw_checksum": "..." }
}
```

**消息总线（MVP 选择）**

* 推荐：**NATS**（极轻、低延迟）或 **Redpanda**（兼容 Kafka API，单机性能高）。
* 预留接口：当规模到达时，可无缝替换为 Kafka（保持 topic、schema 不变）。

**安全 & 运维**

* TLS for adapters → broker; API key 管理；速率限制；adapter 自动重连。

---

### 2) 预处理与流管理层（Preprocessing & Stream Manager）

**职责**：把各种事件规范化到统一 schema，进行数据质量保障、时间对齐、基础特征增强与算子路由。

**设计要点**

* **两层管道**：

  1. **Universal (通用) pipeline**（必须）—— schema validation, fill timestamps, basic sanity checks, drop malformed.
  2. **Source-specific pipeline**（可配置）—— sliding-window aggregate, text NLP, field extraction, normalization, enrichment（外部因子 join）。
* **算子（operator）模型**：每个预处理步骤是一个可插拔算子（operator），支持组合与并行（类似 Flink 的算子概念）。
* **配置驱动**（示例）：

```yaml
preprocessing:
  default:
    - validate_schema
    - add_ingest_time
    - drop_malformed
  pipeline_by_source:
    - source: binance_spot
      operators:
        - aggregate: {window: "1m", method: "ohlcv"}
        - normalize: {fields: ["price"]}
    - source: twitter_news
      operators:
        - text_clean
        - keyword_extract: {topk: 20}
```

* **Implementation (MVP)**: Python async microservice using `asyncio` + `pydantic` for validation + `polars`/`pandas` for aggregates. Keep operators stateless where possible; stateful ops (windowing) use small in-memory state with periodic checkpoint to disk.

**Routing & Fusion**

* Streams can be **branched**: same event can go to pattern engine and also to a storage/warehouse.
* **Stream fusion** for multimodal patterns: join events across sources by aligned time windows (configurable join keys).

**Robustness**

* Backpressure handling: when downstream congested, buffer with bounded queue and emit backpressure metrics.
* Dead-letter queue: malformed events store for inspection.

---

### 3) 模式探索引擎（Pattern Discovery Engine）

**职责**：执行在线 / 近实时模式发现任务（聚类、漂移、异常、频繁/序列模式等），输出结构化模式事件供存储和展示。

**MVP 技术栈与策略**

* **Baseline**：River（Python）——用于快速实验与稳定基线（漂移 ADWIN/DDM、HST 异常等）。
* **Performance / Extended**：CapyMOA（Python wrapper，接近 MOA 算法族）——提供更多流挖掘算法（频繁模式、批量高效聚类等）。
* **当用法**：两者并行运行在同一输入流（或同一时间窗口），输出并列结果以便交叉验证/ensemble 策略。
* **算法模块化**：每种 detector/algorithm 为单独微服务/算子，配置其参数与评估阈值。

**输出（模式事件）格式（核心）**

```json
{
  "pattern_id": "uuid",
  "type": "concept_drift|anomaly|cluster_change|freq_pattern",
  "timestamp": "...",
  "source_streams": ["binance_spot", "news_stream"],
  "details": {
    "prev_state": "Cluster#2",
    "new_state": "Cluster#4",
    "metric_changes": { "volatility": "+37%", "avg_spread": "+12bps" },
    "confidence": 0.82,
    "algorithm": { "name": "capymoa_clust_v1", "params": {...} }
  },
  "explain": { "top_contributors": [{"field":"price","score":0.6}, ...] }
}
```

**工程保证**

* 对 CapyMOA 做 **version-lock**，并在 adapter 层提供 fallback（若 CapyMOA API 变更，切换到 River 或 MOA JVM）。
* 所有模式算子在 CI 中通过回放测试（历史数据回放），并记录预期输出/回归测试结果。

---

### 4) 模式存储（Pattern Store）

**职责**：持久化模式事件、原始/清洗数据（用于回放与审计）、实验记录与版本信息。

**技术选型**

* **ClickHouse**：主存储（事件型 + 时序查询高效）。表结构：`raw_events`, `clean_events`, `pattern_events`, `pattern_catalog`, `experiment_runs`。
* **MLflow / DVC**：用于实验/参数/模型（如在线模型快照）版本管理与可复现记录（MVP 用 MLflow 记录 runs/params/metrics）。
* **Archive（冷存）**：长期历史数据写入对象存储（S3/MinIO）。

**Schema & Indexing**

* pattern\_events 索引按 time, source, type, pattern\_id，以支持快速回查与用户查询（按时间窗口回放某模式的上下文）。

---

### 5) 呈现与解释层（Presentation & Explainability）

**职责**：把模式事件、管道健康、处理细节可视化并以人/LLM 可理解的形式呈现，保证透明性与审计能力。

**分层 UI 设计（MVP）**

1. **System Monitor (Grafana)**

   * 数据接入延迟、throughput、adapter errors、queue lengths、pattern event rate、CPU/memory。
   * Alerts（Prometheus → Alertmanager）用于告警（数据中断、模式风暴、算子故障）。
2. **Pattern Exploration (Superset + Custom Frontend)**

   * Superset：聚类散点（PCA/UMAP 投影）、时间序列叠加/标注、频繁模式表格、统计报表（pattern lifetime、support/confidence）。
   * Custom Frontend（SolidJS）作为统一入口（Dashboard 页）：集成 Grafana iframe + Superset iframe + 自研“事件详情/解释卡片”。
3. **Explain API / LLM Integration**

   * 每个 pattern\_event 可请求 `GET /explain/{pattern_id}?mode=human|llm`
   * `human`：基于 template + `details.top_contributors` 生成简洁专业文本（rule-based），例如：

     > “2025-09-04 10:32：检测到概念漂移。市场从 Cluster#2（低波动）跳到 Cluster#4（高波动），当期波动率较前 30 分钟+37%。主要驱动字段：price volatility (0.6), trade volume (0.3)。建议：暂停高频策略并人工审查。”
   * `llm`：将 `pattern_event + recent context window` 发给被允许的 LLM（用户可配置 API key），返回更自然语言的解释/推断（注意 LLM 输出只作为辅助，前端需标注“LLM-based”）。
4. **Full Pipeline Visualizer（透明性）**

   * 页面包括：Data Ingest → Preprocessing → Pattern Engine → Pattern Store 流线图（实时高亮当前步骤、最近 N 个事件、每步处理时间），并带“回放”按钮（选择时间窗，回放事件与算子输出）。

**交互 UX 要点**

* Pattern 卡片必须包含：时间、类型、confidence、top contributors、上下文（前后 5min 原始清洗数据片段）、算法版本、可回放按钮、标注/备注字段（供人工注释）。
* 所有关键数据/事件都必须可以导出（CSV/JSON）用于离线分析或法律合规。

---

### 6) 监控、审计与治理

**监控（MVP）**：Prometheus metrics from adapters + operators；Grafana dashboards + Alertmanager。
**审计**：所有 pipeline 操作、配置变更、pattern 确认动作都写入 audit logs（append-only），并保存在 ClickHouse 或 ELK。
**Data Governance**：数据源 metadata registry（name, owner, schema, retention, sensitivity）——MVP 为 YAML/DB 表管理，后期接 OpenMetadata。

---

### 7) 测试 / CI / 部署

**回放测试**：核心——历史行情回放脚本，模拟数据流并校验模式事件与基线（River）一致或在阈值范围内。
**回归策略**：任何依赖库升级（如 CapyMOA）必须在 CI 中跑回放测试并比较关键度量（drift triggers, anomaly rate）。
**部署**：Docker Compose for MVP (adapters + message bus + preprocess svc + pattern svc + ClickHouse + Superset + Grafana + Prometheus + custom frontend). Kubernetes-ready manifests prepared for later scaling.
**备份/恢复**：ClickHouse backups + object storage for raw archives + periodic MLflow snapshot exports。

---

## 五、数据与 API 规范（示例）

### A. 标准事件 JSON schema (简要)

```json
{
  "event_id": "uuid",
  "source": "string",
  "type": "string",
  "timestamp": "ISO8601",
  "ingest_time": "ISO8601",
  "payload": { "object": {} },
  "meta": { "parser_version": "string", "original_schema": "..." }
}
```

### B. 模式事件 JSON schema (简要)

```json
{
  "pattern_id": "uuid",
  "type": "enum",
  "timestamp": "ISO8601",
  "source_streams": ["..."],
  "details": { "prev_state": "...", "new_state":"...", "metrics": {...} },
  "explain": { "top_contributors":[ {"field":"...", "score":0.6} ] },
  "algorithm": { "name":"", "version":"", "params": {} },
  "confidence": 0.0
}
```

### C. 关键 REST API（MVP）

* `POST /config/sources` — add/update source config (auth required)
* `GET /sources` — list registered sources/status
* `GET /patterns?start=&end=&type=` — query pattern events
* `GET /pattern/{id}` — get detail + context + explain (human text + LLM option)
* `POST /replay` — request replay of historical window (start,end,source) for debugging/CI

---

## 六、实施路线与里程碑（MVP 迭代计划）

**原则**：短周期交付可见物，逐步完善透明化与自动化。

**Sprint 0（准备） — 1 周**

* 项目骨架（repo、Docker Compose、CI 基础）
* 决定消息总线（NATS / Redpanda）并部署本地实例
* ClickHouse 本地部署

**Sprint 1（基础数据管道） — 2 周**

* 实现 3 个 adapter（Binance trade websocket, simple REST ticker, file watcher）配 YAML 配置
* 自写拉取器 → publish to message bus
* 基础 universal preprocessing (schema validation, timestamp add)
* Insert clean events to ClickHouse

**Sprint 2（模式发现 baseline） — 2 周**

* 集成 River（漂移 + HST anomaly）算子，处理 clean events，并写 pattern\_events 到 ClickHouse
* Superset 基本 dashboards（pattern\_events, raw/clean ingestion stats）
* Grafana 基本监控（adapter lag, queue depth）

**Sprint 3（CapyMOA & Explain） — 2 周**

* 并行接入 CapyMOA（adapter层封装、version-lock）并对同一流进行并行检测
* 输出 explain cards（rule-based human text）
* Custom frontend：Dashboard 集成 Grafana + Superset + pattern list + pattern detail

**Sprint 4（Transparency & Replay） — 2 周**

* 回放 API + CI 回放测试用例
* Audit logs + MLflow experiment recording of runs
* LLM integration hook (configurable API key) and LLM explain button (flagged UI)

**交付（约 7 周 内可得 MVP）**

---

## 七、运维/容量/资源建议（个人开发者视角）

* **最小开发机器**：16 GB RAM, 4 CPU cores（本地开发 &小规模回放）
* **生产最小**：建议 2-3 node 小集群；若单机部署：32GB RAM, 8+ CPU, SSD，高 IO ；选择 Redpanda 或 NATS 可在单机上取得高吞吐。
* **算力（模式引擎）**：River 及多数在线算法可在 CPU 上运行；仅在需要 DeepRiver（在线 NN）时考虑 GPU（租用云 GPU 做试验）。
* **Data retention**：clickhouse 保存 raw/clean 最小 7-30 天；pattern\_events 保留更久（可归档）。

---

## 八、风险、替代与工程保障

1. **外部库（CapyMOA）API 变动**：采用 adapter + version-lock + CI 回放验证 + River 作为备份。
2. **数据爆发**：MVP 先选轻量总线（NATS/Redpanda），并预留 Kafka 替换方案与 schema compatibility。
3. **误报/过度告警**：多算法并行、交叉验证，并在 UI 中提供人工标注与 feedback loop（将人工判断记录入 pattern\_catalog 用于未来筛选）。
4. **LLM 可信性**：LLM 的解释仅作为辅助，前端必须标注“LLM-based”；核心结论靠结构化 metrics 支撑。

---

## 九、交付物（对你/开发团队）

* Git repo（代码、Docker Compose、K8s manifests）
* Config examples（sources YAML, preprocessing YAML, operators）
* Demo dataset + replay script（用于 CI）
* Superset + Grafana dashboards templates
* Frontend minimal Dashboard（pattern list/detail + explain button）
* CI tests including historical replay tests（River baseline vs CapyMOA outputs）
* 运维手册（部署/backup/restore/scale）

---

## 十、下一步（建议你现在可以立刻做的 3 件事）

1. **确认消息总线选择**：NATS（极轻）或 Redpanda（Kafka API 兼容）——我建议 MVP 先用 **Redpanda**（兼具轻量与未来兼容性）。
2. **挑 2-3 个数据源作为 MVP**（例如：Binance websocket、Yahoo REST、local CSV log），我可以给出 adapter 模板代码与配置。
3. **决定是否需要 LLM 即刻集成**（若是，准备好 API key 管理与审计策略；若否，先用 rule-based explain）。

---

如果你愿意，我可以立刻为你生成下面任一交付物（选一项或多项）并把可运行文件放成下载链接：

* A. **完整 Docker Compose MVP**（Redpanda、ClickHouse、River service、CapyMOA adapter stub、Superset、Grafana、Prometheus、frontend）和启动说明；
* B. **Adapter + Preprocessing Python 模板代码**（包含 YAML 配置示例）并带本地回放脚本；
* C. **Superset/Grafana 仪表板 JSON** + 前端 pattern card mockup（HTML/JS）。

你想先要哪个？我会直接生成并附上要运行的具体步骤。
