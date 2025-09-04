# TUI 6.0 M4：验收与文档（事前任务设计）

## 1. 目标
- 完成 TUI 6.0 阶段性验收，确认“单一 Dashboard 模式 + 全量命令接入 + 智能表单”达到“用户操作中台”的使用标准。
- 交付用户上手手册 `docs/TUI6.0_cookbook.md`（简洁直观、覆盖全量功能与操作路径）。

## 2. 验收范围与标准
- 功能无盲区：Dashboard Flows 与 Tasks 列表覆盖全部已实现 CLI（validate/run/quickbacktest/precisebt/search/gridsearch/batch/optimize/riskctrl/riskattr/evidence/quality/pool/deploy/golden/deps/ops/monitor）。
- 交互一致性：Search Flow 提供二选一菜单（search run / gridsearch）；Pool/Deploy/Ops 等含子命令的 Flow 以菜单选择进入表单。
- 表单易用：智能路径选择器默认开启（可用 `QRAFT_TUI_SMART_PATHS=0` 关闭），支持数字选择候选与直接输入；路径补全与存在性校验可用。
- 文案一致：帮助提示与文档一致，不再出现 F2 切换旧模式的提示；默认进入 Dashboard。
- 质量门槛：flake8 改动文件 0 告警；pytest 全量通过（允许既有 skip）。

## 3. 任务拆解
1) 整理帮助与键位说明，移除 F2 旧模式残留（代码与文档）。
2) 编写 `docs/TUI6.0_cookbook.md`：覆盖安装/启动、Dashboard 导航、Flows 与 Tasks 的全部功能、智能路径选择器与环境变量、监控/日志/Artifacts 浏览、常见问题。
3) 自测与验收：按 Cookbook 逐条手动验证；运行 flake8/pytest；在本文档更新“任务执行与验收（事后）”。

## 4. 里程碑与产出
- 代码：帮助文案更新（若存在残留）。
- 文档：`docs/TUI6.0_cookbook.md`、本文档事后总结。
- 质量：flake8/pytest 通过。

---

## 任务执行与验收（事后更新）
- 实现清单：
  - 已移除帮助文本中的 F2 提示/残留，保持“单一 Dashboard 模式”。
  - 已交付 `docs/TUI6.0_cookbook.md`，简洁覆盖全部功能与操作路径。
  - 运行 flake8（改动代码文件）与 pytest 全量，测试通过（含若干 skip）。
- 自测要点：
  - `qraft tui`：默认进入 Dashboard；帮助与键位一致；Flows/Tasks 覆盖全部命令；Search 二选一菜单存在；智能路径选择器可用。
  - Monitor 过滤、Artifacts 浏览、日志尾巴可用。
- 验收结论：
  - 达成 M4 目标：文案与交互一致、功能无盲区、Cookbook 提供全量指引；测试通过，验收通过。
