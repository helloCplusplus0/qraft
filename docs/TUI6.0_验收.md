## 操作：qraft tui
## 结果：
```text
╭───────────────────────────────────────── Dashboard ─────────────────────────────────────────╮                                                                                     
│ Keys: [0-9] flow  o open  s<idx> run  r refresh  l +log  t tasks  m monitor  q quit  ? help │                                                                                     
╰─────────────────────────────────────────────────────────────────────────────────────────────╯                                                                                     
             Flows              ╭───────────────── Main ─────────────────╮                                                                        Recent Runs                       
╭───────── Log tail ──────────╮                                                                                                                                                     
│ (select a run to view tail) │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
╰─────────────────────────────╯                                                                                                                                                     


输入命令（0..N 选Flow，s<idx> 选run，o 打开，l +日志，t Tasks，a Artifacts）：
> 
```

## 操作：dashboard 底部输入：0+enter
## 结果：快速跳出显示：已选择 flow:strategy (可用)，之后迅速消失(说明：0是我随意选择，因为我没有看到flow的相关信息，我不知道0到底意味着什么？)

## 操作：输入o+enter
## 结果：
```text
输入命令（0..N 选Flow，s<idx> 选run，o 打开，l +日志，t Tasks，a Artifacts）：
> o
strategy path  选择编号或直接输入路径 (回车使用默认)
  [0] /home/dell/Projects/Qraft/tmp_strategy.json
  [1] /home/dell/Projects/Qraft/sample_strategy.json
  [2] /home/dell/Projects/Qraft/sample_engine_config_strict.json
  [3] /home/dell/Projects/Qraft/tmp/quick_sma_cross.json
> 3+enter(跳转Preview)

Preview:
qraft validate /home/dell/Projects/Qraft/tmp/quick_sma_cross.json
[r]un | [b]ack
> r+enter(跳转dashboard)

╭───────────────────────────────────────── Dashboard ─────────────────────────────────────────╮                                                                                     
│ Keys: [0-9] flow  o open  s<idx> run  r refresh  l +log  t tasks  m monitor  q quit  ? help │                                                                                     
╰─────────────────────────────────────────────────────────────────────────────────────────────╯                                                                                     
             Flows              ╭───────────────── Main ─────────────────╮                                                                        Recent Runs                       
╭───────── Log tail ──────────╮                                                                                                                                                     
│ (select a run to view tail) │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
│                             │                                                                                                                                                     
╰─────────────────────────────╯                                                                                                                                                     


输入命令（0..N 选Flow，s<idx> 选run，o 打开，l +日志，t Tasks，a Artifacts）：
> （dashboard没有任何显示，空白的，我根本不清楚是否执行状态）
```

## 操作：输入s0+enter
## 结果：快速跳出显示：已选择：run: ut_xxxxxxx->快速消失（说明：我根本不清楚flow是什么？s0到底意味着什么？整个过程dashboard中的flows,main,recent runs,log tail什么都没有显示）

## 操作：输入：t+enter
## 结果：
```text
Dashboard mode: ON
╭────────────────────────────────────────────╮                                                                                                                                      
│ Qraft TUI - Home | v0.0.1 | deps: Rich=yes │                                                                                                                                      
╰────────────────────────────────────────────╯                                                                                                                                      
                                                                                    Recent Runs                                                                                     
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ run_id                                                  ┃ status                                                 ┃ elapsed                                                       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
└─────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────┘
                                                                                                                                                                                    
                                                                                                                                                                                    
                                                                                                                                                                                    
                                                                                                                                                                                    
                                                                                                                                                                                    
╭─────────────────────────╮                                                                                                                                                         
│ CPU: 0.0%  RSS: 141.1MB │                                                                                                                                                         
╰─────────────────────────╯                                                                                                                                                         


[H]ome  [T]asks  [R]un  [M]onitor  [?] help  [Q]uit
> 
```

## 操作：输入：m+enter
## 结果：
```text
Dashboard mode: ON
╭────────────────────────────────────────────╮                                                                                                                                      
│ Qraft TUI - Home | v0.0.1 | deps: Rich=yes │                                                                                                                                      
╰────────────────────────────────────────────╯                                                                                                                                      
                                                                                    Recent Runs                                                                                     
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ run_id                                                  ┃ status                                                 ┃ elapsed                                                       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
└─────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────┘
                                                                                                                                                                                    
                                                                                                                                                                                    
                                                                                                                                                                                    
                                                                                                                                                                                    
                                                                                                                                                                                    
╭─────────────────────────╮                                                                                                                                                         
│ CPU: 0.0%  RSS: 141.1MB │                                                                                                                                                         
╰─────────────────────────╯                                                                                                                                                         


[H]ome  [T]asks  [R]un  [M]onitor  [?] help  [Q]uit
> 

说明：
在 Monitor：
- `/` 过滤（如 `state=running prefix=run_2024`），`n/p` 翻页，`o` 打开某个 run 的日志尾巴（这段表述根本无法执行）
```

## 整体使用总结
- 整个操作流程Flows,Main,Recent Runs,Log Tail什么都没有显示，我根本不清楚是否执行状态
- Flows,s<idx>这些概念根本无法理解，无法使用
- [task_list.md](../task_list.md)和[](./TUI6.0_task_list.md)所定义的flow:Flows 信息架构映射：Data→Features→Strategy→Search→Backtest→Portfolio→Risk→Reports→Pool→Deploy→Monitor,整个流程应该以data为源头，但是在[TUI6.0_cookbook.md](./TUI6.0_cookbook.md)实际操作中，我根本体会不到这个流程逻辑
- TUI是Qraft操作中台的承载，提供展示和交互两个功能，我使用到了部分交互，但是使用没有看到期待的展示，Flows,Main,Recent Runs,Log Tail什么都没有显示,这不是我希望的中台效果

## 操作：
-打开 TUI：`qraft tui`
- 选 Flow：输入 `0`（Data），按 `o`，选择 `batch` 预览后按 `b` 返回（可跳过运行）
## 结果：
- 词条路径已经实现选择价格数据，选择策略，最后执行，但是之后性dashboard依然没有任何执行痕迹
## 问题：
[](./TUI6.0_cookbook.md)中：

```text
打开 TUI：`qraft tui`
选 Flow：输入 `0`（Data），按 `o`，选择 `batch` 预览后按 `b` 返回（可跳过运行）。
选 Flow：输入 `2`（Strategy），按 `o`，选择策略文件（支持数字选择），预览后按 `r` 运行 `validate`。
回到 Dashboard：主区会显示“上次执行命令摘要”。
```
根本不成了，dashboard没有任何执行痕迹