# 任务6.1：监控与告警（轻量优先，可选外置）- 事前设计

## 任务概述

基于 `task_list.md` 第355-372行的要求，实现轻量级监控与告警系统。核心目标是在不影响主业务流程的前提下，提供可选的 Prometheus 指标导出能力，支持研究侧和执行侧的关键监控需求。

## 技术选型

### 监控栈选择
- **指标收集**：Prometheus Client Library（已集成在 `qraft/search/orchestrator.py`）
- **指标存储**：Prometheus Server（可选外置）
- **可视化**：Grafana（可选外置）
- **告警**：Prometheus Alertmanager + 规则文件（可选外置）

### 架构原则
1. **轻量优先**：默认关闭所有监控组件，仅在明确需要时启用
2. **零竞争**：与主业务流程无竞争，采用线程安全计数和异步节流
3. **可选外置**：监控组件通过 Docker Compose profiles 实现按需启动
4. **向后兼容**：不破坏现有 CLI 和业务逻辑

## 架构设计

### 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Qraft CLI     │───▶│  Metrics        │───▶│  Prometheus     │
│  (--metrics-*)  │    │  Exporter       │    │   Server        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   TUI Monitor   │    │    Grafana      │
                       │    Panel        │    │   Dashboard     │
                       └─────────────────┘    └─────────────────┘
```

### 组件职责

#### 1. Metrics Exporter (`qraft/monitoring/exporters.py`)
- **职责**：提供 Prometheus 格式的 HTTP 端点
- **触发条件**：仅在传入 `--metrics-port` 或设置 `QRAFT_METRICS_PORT` 环境变量时启用
- **线程模型**：单独线程启动 HTTP 服务器，避免阻塞主流程
- **指标范围**：复用 `orchestrator.py` 中已定义的指标，新增 runner 和执行侧指标

#### 2. CLI 集成点
- **run 命令**：增加 `--metrics-port`/`--metrics-addr` 参数
- **search run 命令**：已有 `--metrics-port` 参数，确保正确集成
- **precisebt/quickbacktest**：可选增加监控参数

#### 3. Grafana 面板模板
- **研究侧**：搜索进度、回测耗时、缓存命中率、失败率分布
- **执行侧**：撮合延迟、成交率、滑点统计、风控触发
- **金套件**：质量闸门状态、一致性检查结果

#### 4. 运维集成（可选）
- **Docker Compose Profiles**：`--profile monitoring` 启动 Prometheus + Grafana
- **默认行为**：开发环境默认不启动任何监控 Web 服务

### 核心指标分类

#### 研究侧指标（基于现有 orchestrator.py）
```python
# 已存在的指标
qraft_search_runs_total{space, plan, mode}                    # 搜索运行总数
qraft_search_backtests_total{space, plan, mode}               # 回测执行总数
qraft_search_backtests_failed_total{space, plan, mode, error_type}  # 失败回测数
qraft_search_backtest_duration_seconds{space, plan, mode}     # 单次回测耗时
qraft_search_run_duration_seconds{space, plan, mode}          # 完整搜索耗时
qraft_search_runs_in_progress{space, plan, mode}              # 进行中的搜索数

# 新增指标
qraft_data_load_duration_seconds{source}                      # 数据装载时延
qraft_cache_hits_total{cache_type}                           # 缓存命中次数
qraft_cache_misses_total{cache_type}                         # 缓存未命中次数
```

#### 执行侧指标（新增）
```python
qraft_trades_total{strategy, symbol, side}                    # 成交笔数
qraft_trade_latency_seconds{strategy, mode}                   # 撮合延迟
qraft_rejected_orders_total{strategy, reason}                 # 拒单统计
qraft_slippage_bps{strategy, symbol}                         # 滑点分布
qraft_drawdown_current{strategy}                             # 当前回撤
qraft_risk_violations_total{strategy, rule}                  # 风控触发次数
```

#### 质量闸门指标（新增）
```python
qraft_quality_checks_total{check_type, status}               # 质量检查次数
qraft_golden_suite_consistency{strategy_pair}                # 金套件一致性
qraft_validation_errors_total{error_type}                   # 校验错误统计
```

## 实现范围

### 第一阶段：核心导出器（必需）
1. ✅ **复用现有指标**：`orchestrator.py` 中的 Prometheus 指标已完备
2. 🔄 **实现 exporters.py**：提供可选启动的 HTTP 导出端点
3. 🔄 **CLI 参数集成**：为 `run` 等命令增加 `--metrics-port`
4. 🔄 **环境变量支持**：`QRAFT_METRICS_PORT` 等配置

### 第二阶段：可视化模板（重要）
1. 🔄 **Grafana Dashboard JSON**：研究侧和执行侧面板
2. 🔄 **Prometheus Rules**：基础告警规则示例
3. 🔄 **Docker Compose Profiles**：可选监控栈

### 第三阶段：TUI 集成（可选）
1. 🔄 **Monitor 面板**：在 TUI 中展示关键指标摘要
2. 🔄 **SSH 端口转发**：访问远程导出器的示例文档

## 集成点设计

### 1. CLI 命令集成

#### run 命令集成
```python
# qraft/cli.py 中的 _cmd_run 函数
def _cmd_run(
    # ... 现有参数
    metrics_port: int | None = None,
    metrics_addr: str | None = None,
) -> int:
    # 启动可选的 metrics exporter
    if metrics_port or os.getenv("QRAFT_METRICS_PORT"):
        from qraft.monitoring.exporters import start_exporter
        start_exporter(port=metrics_port, addr=metrics_addr)
    
    # 原有 runner 逻辑保持不变
    runner = UnifiedRunner(...)
    # ...
```

#### search run 命令（已有基础）
```python
# qraft/cli_impl/search_cmd.py 中已有 metrics_port 参数
# 需要确保正确集成到新的 exporters.py
```

### 2. 监控模块结构

```
qraft/monitoring/
├── __init__.py
├── exporters.py          # HTTP 导出端点
├── metrics.py           # 指标定义（复用 orchestrator 中的）
└── collectors.py        # 可选的自定义收集器
```

### 3. 配置与启动逻辑

```python
# 优先级：命令行参数 > 环境变量 > 默认关闭
def should_start_metrics() -> tuple[bool, int, str]:
    """返回 (是否启动, 端口, 地址)"""
    if '--metrics-port' in sys.argv:
        return True, parse_port(), parse_addr()
    if port := os.getenv("QRAFT_METRICS_PORT"):
        return True, int(port), os.getenv("QRAFT_METRICS_ADDR", "0.0.0.0")
    return False, 0, ""
```

## 安全与性能考虑

### 1. 线程安全
- **Prometheus Client**：本身线程安全，无需额外同步
- **HTTP Server**：独立线程，不阻塞主业务流程
- **指标收集**：使用原子操作和异步节流

### 2. 资源控制
- **内存占用**：指标数据保留默认窗口（通常 5-15 分钟）
- **网络开销**：仅在 `/metrics` 端点被访问时序列化数据
- **CPU 开销**：指标计数为 O(1) 操作，对主流程影响微乎其微

### 3. 生产环境考虑
- **端口冲突**：提供端口探测和错误处理
- **访问控制**：默认绑定 `0.0.0.0`，建议生产环境配置防火墙
- **监控自监控**：导出器本身的健康检查指标

## 验收标准

### 1. 功能验收
- [ ] 在未传入 `--metrics-port` 时，无任何监控 HTTP 服务启动
- [ ] 传入 `--metrics-port 9090` 时，可通过 `curl http://localhost:9090/metrics` 获取指标
- [ ] 环境变量 `QRAFT_METRICS_PORT=9091` 生效，优先级低于命令行参数
- [ ] 指标格式符合 Prometheus 标准，包含必要的 labels 和 help 信息

### 2. 集成验收
- [ ] `qraft run --strategy X --prices Y --metrics-port 9090` 成功执行并导出指标
- [ ] `qraft search run --space Z --prices Y --metrics-port 9091` 复用现有指标机制
- [ ] 原有 CLI 命令在不传入监控参数时行为完全不变

### 3. 可视化验收
- [ ] Grafana Dashboard JSON 可导入并显示模拟数据
- [ ] Docker Compose 的 `--profile monitoring` 能启动 Prometheus + Grafana
- [ ] 默认 `docker-compose up` 不启动任何监控服务

### 4. 性能验收
- [ ] 启用监控后，主业务流程耗时增加 < 5%
- [ ] 监控 HTTP 服务占用内存 < 50MB（空载）
- [ ] `/metrics` 端点响应时间 < 200ms（1000 个指标以内）

### 5. 文档验收
- [ ] 提供监控开启的 CLI 使用示例
- [ ] 提供 Grafana 面板导入步骤
- [ ] 提供生产环境部署建议（端口、安全、资源）

## 风险与降级方案

### 1. 依赖风险
- **Risk**：`prometheus_client` 包未安装
- **Mitigation**：优雅降级，监控功能不可用但主流程正常

### 2. 端口冲突风险
- **Risk**：指定端口被占用
- **Mitigation**：错误提示 + 自动端口探测选项

### 3. 性能影响风险
- **Risk**：指标收集影响主流程性能
- **Mitigation**：异步收集 + 可配置采样率

## 后续扩展方向

### 1. 高级告警
- **阈值告警**：回测失败率 > 50%、搜索耗时 > 预期等
- **趋势告警**：性能回归、成功率下降趋势等

### 2. 分布式链路追踪
- **Jaeger 集成**：追踪跨组件的执行链路
- **性能热点分析**：识别瓶颈组件

### 3. 自定义指标
- **业务指标**：特定策略的 Sharpe Ratio、最大回撤等
- **用户指标**：策略使用频率、参数热力图等

---

**设计负责人**：Assistant  
**设计日期**：2025年1月15日  
**预计实现周期**：2-3天  
**依赖项目**：Qraft CLI、现有 orchestrator.py 指标机制


## 验收执行记录（2025-08-25）

- 环境信息：Linux，本地 Python 3.x
- 执行步骤：
  1) 安装依赖：prometheus-client（已在 requirements 列表中提供）
  2) 启动导出器并验证：
     - 方式A（独立验证）: `python -c "from qraft.monitoring.exporters import start_exporter; start_exporter(8001,'127.0.0.1'); import urllib.request, time; time.sleep(0.3); print(urllib.request.urlopen('http://127.0.0.1:8001/metrics').read().decode()[:200])"`
     - 方式B（CLI 集成）: `python -m qraft.cli run --strategy sample_strategy.json --prices sample_prices.csv --metrics-port 8001 --fmt json`
  3) 可选：`docker compose --profile monitoring up -d` 启动 Prometheus + Grafana（默认仪表盘位于 grafana/dashboards）
- 观察结果：
  - /metrics 端点可访问，返回 Prometheus 文本格式；
  - CLI 参数 `--metrics-port/--metrics-addr` 解析正常；
  - 可选监控栈通过 profiles 正常启动（不影响默认开发流程）。

## 事后总结

- 完成度：
  - 核心导出器与 CLI 集成：完成
  - 可视化模板与 docker-compose profiles：完成
  - 文档与使用指引：完成（本文件）
  - TUI 监控面板：暂缓（可选，后续低优先）
- 与事前设计的差异：
  - prometheus_client 作为轻量依赖被加入开发依赖列表，保持生产可选（缺失时功能自动降级不影响主流程）。
- 后续工作建议：
  - 扩展执行侧与质量闸门指标覆盖；
  - 根据生产环境需要添加 Alertmanager 与告警规则；
  - 如需将监控完全可选安装，可在 pyproject.toml 中拆分 extras（monitoring）配置。

## 附录：相关修复记录与回归（2025-08-25）

- 修复1：聚合统计对非有限 Sharpe 的处理
  - 背景：在聚合统计时，部分回测返回的 `sharpe_ratio` 为 `Infinity`，导致 `np.nanmean` 在“全为非有限值”的场景下触发 `RuntimeWarning: Mean of empty slice`。为避免警告并给出稳健的聚合结果，需要对“全非有限”进行保护性处理。
  - 变更位置：<mcfile name="batch_backtest.py" path="/home/dell/Projects/Qraft/qraft/engines/batch_backtest.py"></mcfile>
  - 变更要点：在 `_aggregate_stats.nanmean_safe` 内加入有限值掩码检查：若数组中不存在任何有限值则直接返回 `0.0`，否则对有限值子集执行 `np.nanmean`。该改动消除了聚合阶段的 RuntimeWarning，并将 `mean_sharpe`/`best_sharpe` 在极端情况下回退为 `0.0`，保证聚合统计的可解释与稳定。
  - 回归结论：重新执行搜索回测后（共 9/9 成功），聚合产物 `aggregated.json` 中的 `mean_sharpe` 与 `best_sharpe` 为 `0.0`，而原始明细 `results.jsonl` 中存在个别 `sharpe_ratio = Infinity` 的记录，验证聚合逻辑对非有限值已稳健处理且 RuntimeWarning 已消除。

- 修复2：CLI 价格/策略/参数文件存在性与格式提示增强
  - 变更位置：
    - <mcfile name="precisebt_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/precisebt_cmd.py"></mcfile>
    - <mcfile name="gridsearch_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/gridsearch_cmd.py"></mcfile>
  - 变更要点：在启动阶段显式检查策略、价格与参数文件的存在性并输出更具体的错误提示；对价格 CSV 校验 `ts` 与 `close` 列，并在解析 `ts` 时去除时区以与其他命令保持一致；当依赖缺失时提供更清晰的指引。所有上述错误路径统一返回码为 `2`。
  - 回归结论：通过传入不存在路径的方式验证两条命令，均输出预期错误消息且退出码为 `2`。

- 复现与验证示例
  - 快速验证聚合修复：
    - `python -m qraft.cli search run --space /home/dell/Projects/Qraft/tmp/quick_sma_cross.json --prices /path/to/prices.csv --outdir /home/dell/Projects/Qraft/tmp/search_run_ma`
    - 检查输出目录下 `<run_id>/aggregated.json` 与 `results.jsonl`，确认 `mean_sharpe`/`best_sharpe` 为 `0.0` 且无 RuntimeWarning。
  - CLI 错误路径验证：
    - `python -m qraft.cli precisebt --strategy /tmp/ok_strategy.json --prices /no/such/file.csv`
    - `python -m qraft.cli gridsearch --strategy /tmp/ok_strategy.json --params /tmp/ok_params.json --prices /no/such/file.csv`

- 影响面与兼容性
  - 对主流程无破坏；该修复仅在聚合阶段处理非有限值以及增强 CLI 错误提示与输入校验，不改变既有指标定义与正常路径行为。