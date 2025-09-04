# 任务 6.2：灰度与上线流程（实现与使用说明）

本节交付“审批流与发布流程”的可运行最小闭环，涵盖：一致性预检查（quick vs precise）、纸上交易 Canary、候选生成与审批发布、CURRENT/HISTORY 管理与回滚。所有能力均通过 qraft CLI 暴露，配合策略池与回测引擎完成端到端灰度上线路径。

---

## 一、总体设计

- 灰度流程对象：GrayscaleDeployer（文件级部署编排器），负责：
  - 质量闸门预检查：对比快速/精撮回测一致性，输出是否通过与细节
  - Canary 纸上交易：小资金向量化模拟，返回核心指标
  - 候选 → 审批发布：复用策略池的 propose/approve，发布后维护 CURRENT.json/HISTORY.json
  - 回滚：回退到上一个稳定版本，并记录历史
- CLI 封装：`qraft deploy` 顶层命令，提供 precheck/canary/propose/approve-and-publish/current/history/rollback 子命令。

目录与工件约定：
- 策略池：`artifacts/pool/`（候选与稳定清单、快照目录等）
- 部署目录：`artifacts/deploy/`（CURRENT.json 与 HISTORY.json）

---

## 二、CLI 用法

以下命令均支持 `--fmt text|json` 输出格式（默认 text）。

1) 一致性预检查（质量闸门）
- 目的：在“快速通道（vectorbt）”与“精撮通道（Nautilus Trader）”之间进行一致性校验，作为上线前硬门槛之一。
- 命令：
  
  qraft deploy precheck \
    --strategy path/to/strategy.json \
    --prices path/to/prices.csv \
    --start 2023-01-01 --end 2024-01-01 \
    --fmt text
  
- 返回：是否通过（passed）、对齐细节（details）。当本机未安装 Nautilus Trader 时将提示无法进行精撮，需按需安装后再执行。

2) 纸上交易 Canary（向量化）
- 目的：以小资金比例进行快速模拟，观察收益/波动/回撤等指标，作为“上线前小额灰度”替身。
- 命令：
  
  qraft deploy canary \
    --strategy path/to/strategy.json \
    --prices path/to/prices.csv \
    --cash-ratio 0.05 --base-cash 1000000 \
    --fmt text
  
- 返回：核心统计指标（可选 JSON）。

3) 生成候选（接入策略池）
- 目的：将策略候选材质（payload+metadata）生成候选快照，进入审批通道。
- 命令：
  
  qraft deploy propose \
    --payload artifacts/pool/payload.json \
    --metadata artifacts/pool/metadata.json \
    --pool-root artifacts/pool \
    --fmt text
  
- 返回：候选清单信息（manifest_hash 与输出目录）。

4) 审批并发布 CURRENT
- 目的：审批指定候选并发布，将 CURRENT.json 指向稳定版本，同时在 HISTORY.json 记录一条 publish 事件。
- 命令：
  
  qraft deploy approve-and-publish \
    --hash <manifest_hash> \
    --approver alice --note "上线说明" \
    --pool-root artifacts/pool \
    --deploy-dir artifacts/deploy \
    --fmt text
  
- 返回：稳定条目与当前 CURRENT 内容。

5) 查看 CURRENT 与 HISTORY
- 当前：
  
  qraft deploy current --deploy-dir artifacts/deploy --fmt json
  
- 历史：
  
  qraft deploy history --deploy-dir artifacts/deploy --fmt json

6) 回滚至上一个稳定版本
- 条件：HISTORY 至少有两条发布相关记录；回滚会在 HISTORY 追加一条 rollback 事件，并更新 CURRENT.json。
- 命令：
  
  qraft deploy rollback --deploy-dir artifacts/deploy --fmt text

---

## 三、工件与状态管理

- CURRENT.json：当前生效的稳定版本（包含 manifest_hash、approved_by、note、ts）。
- HISTORY.json：按时间追加的历史事件列表，支持 action ∈ {publish, rollback}。
- 所有 JSON 文件均位于 `--deploy-dir`（默认 artifacts/deploy）。

---

## 四、与策略池对接

- `propose` 与 `approve-and-publish` 直接复用策略池管理器：
  - propose(payload, metadata) → 生成候选快照，返回 manifest_hash 与输出路径
  - approve(manifest_hash, approver, note) → 产出稳定版本清单
  - 发布时将稳定版本写入 CURRENT，并在 HISTORY 记录一次 publish

payload/metadata 结构参考策略池文档与示例（详见 `qraft/strategy_pool` 相关模块与测试样例）。

---

## 五、质量闸门建议（MVP）

建议在预检与灰度阶段遵循以下门槛（可按项目实际调参）：
- 两阶段一致性：vectorbt vs Nautilus 关键指标差异 < 2%
- 冷启动复跑：同快照与参数下波动 < 1%
- 成本敏感性：成本参数 ±50% 时 Top‑N 重叠率 ≥ 70%
- 泄漏/对齐：左闭/滞后/对齐单测全过

上述规则由质量模块与测试用例共同保障，作为进入“审批发布”的前置条件。

---

## 六、最小自测路径（示例）

1) 预检（需已安装 Nautilus Trader 才能跑精撮通道）：
- `qraft deploy precheck --strategy examples/strategy.json --prices examples/prices.csv --start 2023-01-01 --end 2024-01-01`

2) Canary（本机向量化通道）：
- `qraft deploy canary --strategy examples/strategy.json --prices examples/prices.csv`

3) 生成候选并审批发布：
- `qraft deploy propose --payload artifacts/pool/payload.json --metadata artifacts/pool/metadata.json`
- `qraft deploy approve-and-publish --hash <manifest_hash> --approver <name> --note "说明"`

4) 查看与回滚：
- `qraft deploy current`
- `qraft deploy history`
- `qraft deploy rollback`

---

## 七、已知限制与后续增强

- 精撮通道依赖 Nautilus Trader，如未安装将无法完成一致性预检。
- 当前 Canary 仅走向量化简化版撮合；后续可增加成本/滑点/风控模板的可配置项，以收敛到实盘配置。
- 审批流程现为本地文件级编排；规模化后可对接审计/权限系统与远程存储。

---

## 八、验收清单（对齐 task_list.md）

- CLI 顶层命令 `qraft deploy` 与七个子命令已落地，覆盖预检/灰度/候选/审批/发布/回滚闭环。
- 部署工件 CURRENT.json/HISTORY.json 设计与路径一致。
- 与策略池 propose/approve 完成解耦对接。
- 自测样例（最小路径）可跑通；已有单测通过，未破坏既有能力。