# 任务 2.1：vectorbt 快速回测适配（实现完成，已与 CLI 对齐）

本页文档已对齐当前实现，覆盖 CLI 子命令的强制依赖与错误提示、ops 子命令用途与输出示例、precisebt 成本参数配置与传递路径，以及最小可运行示例与常见错误排查，力求让你无需阅读源码即可按文档复现实验。

- 相关代码位置：
  - CLI 入口与子命令实现：<mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile>
  - 快速回测适配器（vectorbt）：<mcfile name="vectorbt_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/vectorbt_adapter.py"></mcfile>
  - 精准回测适配器（Nautilus）：<mcfile name="nautilus_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/nautilus_adapter.py"></mcfile>
  - 批量/网格回测引擎：<mcfile name="batch_backtest.py" path="/home/dell/Projects/Qraft/qraft/engines/batch_backtest.py"></mcfile>
  - 算子注册表（ops 列表来源）：<mcfile name="registry.py" path="/home/dell/Projects/Qraft/qraft/operators/registry.py"></mcfile>
  - 模板库（可直接使用）：/home/dell/Projects/Qraft/qraft/strategies/templates/

---

## 1. 目标与范围（MVP）

在不自研回测内核的前提下，基于 vectorbt 构建“快速回测”适配层，实现从策略协议 v1（expr → signal）到向量化回测的一键驱动；并提供批量/网格搜索与 Nautilus 精准回测的最小打通。

- 覆盖：
  - 单资产/多资产日频价格 CSV → 表达式解释 → 信号构建 → 向量化回测（vectorbt）
  - 参数网格（gridsearch）与批量（batch）回测
  - Nautilus 精准回测（precisebt）最小可用路径与成本参数透传（点差/佣金/滑点）
- 非目标（本任务不含）：复杂交易成本/滑点、订单撮合细节、组合优化与风控等高级功能（后续任务）

---

## 2. CLI 子命令与强制依赖（硬约束）

当前提供的子命令：validate、ops、quickbacktest、gridsearch、batch、precisebt（详见 <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile>）。

- quickbacktest / gridsearch / batch 均“强制依赖 vectorbt”。若缺失，退出码为 2，并打印安装指引与替代建议：

  示例（未安装 vectorbt）：
  ```
  $ qraft quickbacktest --strategy s.json --prices prices.csv
  Error: vectorbt is not installed or not available.
  
  The 'quickbacktest' command requires vectorbt for fast vectorized backtesting.
  Please install it using:
  
      pip install vectorbt
  
  Alternatively, if you have Nautilus Trader installed, you can try 'precisebt':
  
      qraft precisebt --strategy <strategy.json> --prices <prices.csv>
  ```

- precisebt“强制依赖 nautilus-trader”。若缺失，退出码为 2，并打印安装指引与替代建议：

  示例（未安装 nautilus-trader）：
  ```
  $ qraft precisebt --strategy s.json --prices prices.csv
  Error: nautilus-trader is not installed or not available.
  
  The 'precisebt' command requires Nautilus Trader for high-fidelity backtesting.
  Please install it using:
  
      pip install nautilus-trader
  
  For development/testing purposes, you can use 'quickbacktest' instead:
  
      qraft quickbacktest --strategy <strategy.json> --prices <prices.csv>
  ```

说明：以上错误消息与退出码行为由 <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile> 明确定义并在单测中覆盖。

---

## 3. ops 子命令：算子列表与用途

- 用途：列出策略表达式可用的算子（白名单）与参数个数（arity），用于编写/验证 expr。
- 使用：
  ```
  qraft ops
  ```
- 典型输出（节选，数量可能随实现变动）：
  ```
  operators (10):
  - ATR  arity=2
  - BBANDS  arity=2
  - CROSS  arity=2
  - EMA  arity=2
  - MACD  arity=3
  - RANK  arity=1
  - ROLL_MEAN  arity=2
  - ROLL_STD  arity=2
  - RSI  arity=2
  - SMA  arity=2
  ```
- 约束与说明：
  - 表达式安全由注册表与解释器共同保障，禁止任意代码执行。
  - 当前 CROSS 仅支持嵌套 SMA，即形如：`CROSS(SMA(close,a), SMA(close,b))`。

---

## 4. precisebt 成本参数配置与传递路径

precisebt 命令用于调用 Nautilus Trader 进行高保真回测，支持通过 CLI 传入基础成本参数，这些参数会被注入到 engine_config 并传递给适配器：

- CLI 参数（默认值）：
  - --spread-bps 10.0（点差，单位 bps）
  - --commission-bps 1.0（佣金，单位 bps）
  - --slippage-bps 5.0（滑点，单位 bps）
  - 可选：--engine-mode（启用 engine 模式）与 --engine-config <path>（从 JSON 文件加载配置）

- 传递路径（简化示意，详见 <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile> 与 <mcfile name="nautilus_adapter.py" path="/home/dell/Projects/Qraft/qraft/engines/nautilus_adapter.py"></mcfile>）：
  1) CLI 解析参数后构造/合并 engine_config（未显式传入时默认设定 `{"mode": "engine"}` 触发正确路径）。
  2) 将成本参数注入 engine_config：
     - fill_model.spread_bps = --spread-bps
     - fill_model.slippage_bps = --slippage-bps
     - fill_model.price_impact = "linear"（当前固定为线性）
     - fees.taker_rate = commission_bps / 10000.0（bps → 小数）
     - fees.maker_rate = commission_bps / 10000.0
     - fees.min_commission = 0.0
  3) 调用 NautilusAdapter.run(..., engine_config=engine_config)。

- 合并与优先级：
  - 若提供 --engine-config，文件中的其它字段会保留；上述与成本相关的键（spread_bps、slippage_bps、fees.*）由 CLI 参数覆盖写入。
  - 模板示例：/home/dell/Projects/Qraft/qraft/strategies/templates/nautilus_config.json 可作为起点按需扩展。

---

## 5. 最小可运行示例（一步步复现）

准备数据与策略：

1) 准备价格 CSV（单资产），包含列 ts,close：
```
 ts,close
 2020-01-01,100
 2020-01-02,101
 2020-01-03,102
```

2) 准备策略 JSON（SMA 示例），或直接使用模板库：
- 模板路径：/home/dell/Projects/Qraft/qraft/strategies/templates/
  - ma_cross.json（包含 {fast},{slow} 占位符）
  - rsi_threshold.json

校验与回测：

A) 校验策略（本地 JSON）：
```
qraft validate path/to/strategy.json
```
输出包含 “OK: strategy is valid” 则通过。

B) 查看可用算子：
```
qraft ops
```
输出以 operators (N): 开头，包含 “- SMA  arity=2” 等条目。

C) 快速回测（vectorbt）：
```
qraft quickbacktest --strategy path/to/strategy.json --prices path/to/prices.csv [--start YYYY-MM-DD] [--end YYYY-MM-DD]
```
成功后控制台以 “Quick Backtest Stats:” 开头打印指标（total_return、sharpe_ratio 等）。若未安装 vectorbt，参考第 2 节错误提示与安装指引。

D) 参数网格（gridsearch）：
```
# params.json 例如：{"fast": [5, 10], "slow": [20, 30]}
qraft gridsearch --strategy /home/dell/Projects/Qraft/qraft/strategies/templates/ma_cross.json \
                 --params path/to/params.json \
                 --prices path/to/prices.csv [--start --end --workers 1]
```
控制台包含 “Grid Search Aggregated Stats:” 与 “Best Params:” 摘要。

E) 批量回测（batch）：
```
# 目录内放多个有效策略 JSON
qraft batch --dir path/to/strategies_dir --prices path/to/prices.csv [--start --end --workers 1]
```
控制台包含 “Batch Backtest Finished: X strategies” 与 “mean_total_return:” 摘要。

F) 精准回测（precisebt，需 nautilus-trader）：
```
qraft precisebt --strategy path/to/strategy.json --prices path/to/prices.csv \
                [--engine-mode] [--engine-config path/to/nautilus_config.json] \
                [--spread-bps 12.3 --commission-bps 2.5 --slippage-bps 7.7]
```
成功后以 “Precise Backtest Stats:” 打印指标；若未安装 nautilus-trader，参考第 2 节错误提示与安装指引。

---

## 6. 数据与对齐约定（关键点）

- CSV 支持两种列格式：
  - 单资产：[ts, close]；内部转为单列宽表 close
  - 多资产：[ts, symbol, close]；内部透视为列为 symbol 的宽表
- 表达式解释与信号：
  - 使用 <mcfile name="registry.py" path="/home/dell/Projects/Qraft/qraft/operators/registry.py"></mcfile> 白名单（SMA/EMA/RSI/RANK/ROLL_*、MACD、BBANDS、CROSS 等）
  - 当前 CROSS 仅允许嵌套 SMA；RSI 示例采用默认阈值二值化（< 30 做多）
  - NaN 在起始窗口会被安全二值化处理（例如 CROSS → 填充 0）
- 时间切片：--start/--end 会在进入引擎前进行左闭右闭的时间对齐/切片。

---

## 7. 常见错误与排查

- 缺少 vectorbt（quickbacktest/gridsearch/batch）：退出码 2，控制台给出 pip 安装指引与 precisebt 替代建议。
- 缺少 nautilus-trader（precisebt）：退出码 2，控制台给出 pip 安装指引与 quickbacktest 替代建议。
- 路径错误：当策略/价格/参数文件缺失时，提示 “file not found” 或相应错误并退出码 2。
- CSV 列缺失：必须包含 ts 与 close 列（多资产需 symbol）；否则报错并退出码 2。
- batch 目录无有效策略：会提示 “no valid strategies found” 并退出码 2。
- 未知命令或参数错误：显示帮助并返回退出码 2。
- 多资产信号对齐：内部已做安全对齐，确保与宽表价格列一致；若表达式生成的信号没有 symbol 维度，会广播至所有列。

---

## 8. 验收与测试

- 单测覆盖了上述依赖检查、输出格式与关键路径：
  - CLI：validate/ops/quickbacktest/gridsearch/batch/precisebt 的成功与错误分支
  - 适配器：vectorbt 对齐/切片与指标聚合；Nautilus 成本参数透传
- 你可以运行：
```
pytest -q
```
所有测试应通过。

---

## 9. 参考与后续

- 性能基线脚本：/home/dell/Projects/Qraft/scripts/benchmark_quickbacktest.py（可选）
- 后续增强：交易成本/滑点精细化、组合与风控、Bayesian/稳健性评估、执行与实盘联通等按路线图推进。