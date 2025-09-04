# 任务7.1：开源依赖升级SOP（事前设计）

目标：建立一套轻量、可落地、与现有仓库结构契合的依赖升级SOP，覆盖“发现→验证→合并→回滚/记录”的闭环，避免过度设计，优先复用现有工具链与API。

范围与约束：
- 仅围绕 Python 依赖（pip/requirements/constraints）与 GitHub 平台能力展开。
- 不假设额外基础设施（如自建制品库）；若上游仅有源码仓库（无发行包），通过策略化管理避免直接修改上游源码。
- 与现有目录保持一致：requirements/ 下 stable/candidate 双通道与 3.11 约束文件。

核心设计：
1) 发现与提案（自动化）
- 使用 GitHub Dependabot 监控 pip 与 GitHub Actions 依赖变更，自动发起 PR（每周频率）。
- 变更范围优先指向 requirements/ 下文件；限制并发 PR 数，降低干扰。

2) 分层验证清单（最小可行）
- 语法与类型：flake8 + black --check + mypy
- 单元与接口：pytest（现有全量测试）
- CLI 接线冒烟：tests/unit/test_cli_wiring_smoke.py（已存在）
- 回测关键路径冒烟：vectorbt_adapter 与 NautilusAdapter 的单元测试（已存在）
- 说明：本阶段不引入新的复杂集成测试，优先复用现有测试覆盖。

3) 升级验证流水线（CI）
- 在 PR（特别是 Dependabot PR）上运行：
  - 使用 requirements/requirements-stable.txt + constraints/3.11.txt 安装依赖
  - 执行 make test 与 make mypy，失败则阻断合并
- 采用单一 Python 3.11 版本矩阵，后续可按需扩展

4) 回滚与监控
- 通过 CLI 提供“依赖快照（snapshot）”能力，基于 importlib.metadata 导出当前已安装包版本（JSON），用于回滚参考
- 监控采用最简策略：CI 失败即阻断，无额外守护进程

5) 变更记录（UPGRADELOG 生成器）
- 提供 CLI 工具对比两个 requirements/constraints 文件，输出 Markdown/JSON 摘要：新增、移除、版本升降级（基于“==”精确钉死版本优先，其次回退到原始规范串对比）
- 工具仅输出到 stdout 或写文件，不强制维护固定文档

实施清单与交付物：
- Dependabot 集成：.github/dependabot.yml
- 升级验证流水线：.github/workflows/deps-upgrade.yml（稳定通道 + Python 3.11）
- CLI：qraft/cli_impl/deps_cmd.py，注册到 qraft/cli.py 的 "deps" 子命令
  - deps upgradelog --old <path> --new <path> [--fmt text|json]
  - deps snapshot [--output <path>] [--fmt json|text]
- 文档：本文件（task_7.1.md）

验收标准（DoD）：
- 新增的 CLI 子命令可运行且具备帮助文案
- 依赖文件差异可生成 UPGRADELOG 摘要（stdout/JSON）
- 快照命令可导出 JSON；可作为回滚参考
- CI 能在依赖变更 PR 上自动运行，并执行测试与类型检查
- 不破坏现有单元测试（全量测试应通过）

后续可迭代项（非本次强制）：
- 增加 candidate 通道在CI矩阵
- 对接 Release Note 自动化（根据 upgradelog 生成 PR 描述）
- 引入“潜在破坏性变更”识别（基于包级别的 SemVer 解析与变更等级评估）

---

# 任务7.1：开源依赖升级SOP（实现与验收）

实现内容要点：
- CLI 新增 deps 子命令（qraft deps ...）：
  - snapshot：导出当前环境已安装包的快照（JSON/text）
  - upgradelog：对比两个 requirements 文件差异，输出升级日志摘要（JSON/text）
- CI 增强：新增 .github/workflows/deps-upgrade.yml，在依赖变更 PR 上自动执行 lint/mypy/tests
- Dependabot 集成：.github/dependabot.yml，按周生成 pip 与 GitHub Actions 升级 PR

关键文件：
- <mcfile name="cli.py" path="/home/dell/Projects/Qraft/qraft/cli.py"></mcfile>
- <mcfile name="deps_cmd.py" path="/home/dell/Projects/Qraft/qraft/cli_impl/deps_cmd.py"></mcfile>
- <mcfile name="deps-upgrade.yml" path="/home/dell/Projects/Qraft/.github/workflows/deps-upgrade.yml"></mcfile>
- <mcfile name="dependabot.yml" path="/home/dell/Projects/Qraft/.github/dependabot.yml"></mcfile>

用法示例：
- 生成快照（stdout）：
  qraft deps snapshot --fmt json
- 生成快照（写文件）：
  qraft deps snapshot --output artifacts/snapshot.json --fmt json
- 生成升级日志（requirements 对比）：
  qraft deps upgradelog --old requirements/requirements-stable.txt --new requirements/requirements-candidate.txt --fmt text

测试与回归：
- 运行全量单测：通过
- 关键 CLI 冒烟与解析测试：通过

---

事后总结（AAR）：
- 按照事前设计完成了“发现→验证→合并→回滚/记录”的最小闭环：Dependabot + CI + CLI 工具
- 未引入过度设计，未修改现有工程结构，完全复用既有 Makefile 与测试基线
- 兼容性：默认使用 stable 通道与 3.11 约束，后续如需添加矩阵可平滑扩展
- 后续建议：结合 release 流程将 upgradelog 输出纳入 PR 描述模板，并在 candidate 通道上建立周期性预检