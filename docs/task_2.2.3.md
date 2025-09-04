# 任务2.2.3：订单生命周期追踪（预设计 + 实施总结）

目的
- 在不依赖特定撮合内核实现细节的前提下，为回测/执行阶段提供通用的订单生命周期追踪与统计能力。
- 支持部分成交、挂撤改、拒单与滑点/费用模拟的基础场景，用于后续与 Nautilus Trader/实盘对接时直接复用。

设计约束
- 禁止过度设计：仅实现通用事件模型、轻量状态机与统计接口，不实现撮合引擎本身。
- 复用既有模型：费用/滑点参数复用 <mcfile name="cost_models.py" path="/home/dell/Projects/Qraft/qraft/models/cost_models.py"></mcfile> 的 QraftFillModel/QraftFeeModel。
- 与现有引擎解耦：不修改 BacktestResult 结构，追踪器作为可选工具，由引擎/策略在需要时注入使用。

数据模型（MVP）
- OrderStatus：NEW, PARTIALLY_FILLED, FILLED, CANCELED, REJECTED, AMENDED。
- Side：BUY, SELL。
- OrderEvent：统一事件结构，字段包含：ts, order_id, symbol, side, qty, price(意向价), event_type（submitted/partial_fill/filled/canceled/rejected/amended）, exec_price(成交价), fill_qty, fees, note。
- OrderState：每笔订单的累积状态（原始数量、已成交数量、成交 VWAP、累计费用、当前状态、事件历史）。

核心API
- OrderTracker.track_event(event)：按事件推进订单状态机，记录历史。
- OrderTracker.simulate_and_track(order_id, symbol, side, qty, price, ...)：基于 Fill/Fee 模型给出成交价与费用，生成并落账 fill 事件（可配置拒单率）。
- OrderTracker.build_stats()：汇总统计（订单数、成交/部分成交/撤单/拒单、总体成交率、成交金额与费用、平均滑点bp 等）。
- OrderTracker.to_events_frame()/to_orders_frame()：导出明细与订单快照用于报表。

集成点
- Vectorbt/Nautilus 适配器或策略执行层在产生信号→下单→成交时调用 OrderTracker 记录事件；暂不改变 <mcfile name="vectorbt_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/vectorbt_adapter.py"></mcfile> 与 <mcfile name="nautilus_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/nautilus_adapter.py"></mcfile> 的返回结构。

验收标准（本任务）
- 新增 <mcfile name="order_tracker.py" path="/home/dell/Projects/Qraft/qraft/execution/order_tracker.py"></mcfile> 与 <mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/execution/__init__.py"></mcfile>。
- 能构造提交/部分成交/全部成交/撤单/拒单场景，并正确反映累积成交与状态。
- 能输出事件明细与汇总统计（包含基础滑点/费用指标）。
- 保持与现有引擎解耦，零侵入。

——

实施结果
- 代码实现：
  - 新增模块：<mcfile name="order_tracker.py" path="/home/dell/Projects/Qraft/qraft/execution/order_tracker.py"></mcfile> 与 <mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/execution/__init__.py"></mcfile>
  - 提供 OrderStatus/Side/OrderEvent/OrderState/OrderTracker 五个公开符号。
  - OrderTracker 支持：
    - 事件推进：submitted/partial_fill/filled/canceled/rejected/amended
    - 基础成交仿真：基于 <mcfile name="cost_models.py" path="/home/dell/Projects/Qraft/qraft/models/cost_models.py"></mcfile> 的 spread_bps、线性 impact 与 taker 费率计算
    - 拒单率控制（rejection_rate）与部分成交（allow_partial, partial_ratio）
    - 统计导出（build_stats）与明细快照（to_events_frame/to_orders_frame）

- 与现有代码集成：
  - 未改动 <mcfile name="vectorbt_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/vectorbt_adapter.py"></mcfile>、<mcfile name="nautilus_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/nautilus_adapter.py"></mcfile>、<mcfile name="nautilus_engine.py" path="/home/dell/Projects/Qraft/qraft/engines/nautilus_engine.py"></mcfile> 的接口，保持解耦。
  - 后续在 precise 模式下，可在策略或 engine 侧将真实成交（fills）映射为 OrderEvent 以复用统计逻辑。

简单验收用例（示例）
- 提交一笔买单并模拟部分成交→完全成交，检查：
  - cum_filled 与 vwap 递增，状态从 PARTIALLY_FILLED → FILLED。
  - build_stats 中 fill_rate_qty>0，总费用>0，avg_slippage_bps 合理（买方向为正）。
- 提交一笔拒单：状态为 REJECTED，成交与费用均为0。
- 提交一笔撤单：状态为 CANCELED，成交数量不变。

反思与结论
- 是否按规划完成：是。实现了订单生命周期追踪、部分成交/拒单/滑点与费用模拟、统计与报表导出，且保持与引擎解耦。
- 后续改进建议：
  - 当接入 Nautilus 精确回测后，增加真实事件到 OrderEvent 的适配层。
  - 丰富统计维度（延迟、拒单原因码、按 symbol/方向分组统计等）。
  - 根据实际数据特征，调优价格冲击与滑点模型参数映射。