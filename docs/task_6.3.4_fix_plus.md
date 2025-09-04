# Task 6.3.4 Fix Plus — Nautilus Strategy 集成稳定性修复记录

日期：2025-08-27

## 背景
在运行集成测试（engine 模式）时，发现 `qraft/engines/nautilus_strategy.py` 存在语法及构造期依赖问题：
- 文件内出现 `from __future__ import annotations` 非置于文件首行，触发 Python 语法错误。
- `QraftSignalStrategy`（`SignalFollowStrategy` 别名）在构造函数阶段尝试导入 Nautilus Trader 的 `Strategy` 基类，导致在未安装 Nautilus 的测试环境下抛出异常，破坏了应有的“导入保护（import guard）”与可替换模拟策略的测试路径。

## 问题与根因
1. SyntaxError：`from __future__` 语句必须位于文件最顶部，否则 Python 直接报错，阻塞测试执行。
2. 构造期过早依赖：`SignalFollowStrategy` 在初始化阶段导入 Nautilus 依赖，违背了“按需检查依赖”的设计，导致在通过 monkeypatch/stub 的集成测试中仍然抛错。

## 变更清单
- 文件：`qraft/engines/nautilus_strategy.py`
  - 移除位于非首行的 `from __future__ import annotations` 语句，消除 SyntaxError。
  - 移除重复且未使用的导入（如重复 `import pandas as pd`），精简依赖。
  - 简化 `SignalFollowStrategy` 构造逻辑：
    - 不再在构造函数中尝试导入 Nautilus 的 `Strategy` 基类。
    - 保留必要的元数据字段（满足集成测试对元数据的读取）。
    - 将 Nautilus 依赖检查限制在确需调用 Nautilus 引擎路径时（由引擎层完成），实现“惰性依赖”。
  - 保留并明确 `DevSignalFollowSimulator` 的定位：在无 Nautilus 环境下提供信号跟随的轻量模拟，用于单元测试与快速验证。

上述修改未变更外部 API，保持向后兼容。

## 回归验证
- 单元测试：
  - `tests/unit/test_nautilus_strategy.py` 全部通过（含：无 Nautilus 环境下的异常路径与模拟器路径）。
- 集成测试：
  - `tests/integration/test_engine_mode_e2e.py::test_e2e_engine_mode_with_parquet_catalog_and_qraft_strategy` 通过。
- 全量测试：
  - 在本地环境执行完整测试套件，全部通过，确认无回归与新隐患。

## 影响评估
- 对生产环境无破坏性影响：当实际使用 Nautilus 精撮路径（如 precise 回测）时，依赖检查仍由引擎层（`nautilus_engine.run_precise` 链路）统一触发，行为与预期一致。
- 对测试与开发者体验更友好：在未安装 Nautilus 的环境中，策略类构造与轻量模拟不再硬失败，符合“按需依赖”的设计原则。

## 复现与运行指南
- 仅运行受影响的集成测试：
  - `pytest tests/integration/test_engine_mode_e2e.py::test_e2e_engine_mode_with_parquet_catalog_and_qraft_strategy -q`
- 运行单元测试（策略相关）：
  - `pytest tests/unit/test_nautilus_strategy.py -q`
- 运行全量测试：
  - `pytest -q`

## 相关文件
- 策略垫片与模拟：
  - `qraft/engines/nautilus_strategy.py`
- 引擎适配与回测：
  - `qraft/engines/nautilus_engine.py`
  - `qraft/engines/nautilus_adapter.py`
- 转换器（无改动，供参考）：
  - `qraft/engines/nautilus_converters.py`
- 测试：
  - `tests/unit/test_nautilus_strategy.py`
  - `tests/integration/test_engine_mode_e2e.py`

## 变更要点（Changelog）
- fix(engines): 移除错误位置的 `from __future__`，修复 SyntaxError。
- refactor(engines): 清理重复/未使用导入，降低噪音。
- feat(engines): 简化 `SignalFollowStrategy` 构造逻辑，支持无 Nautilus 环境的构造与模拟；依赖检查下沉至引擎调用路径。

## 后续建议（非阻断）
- 继续统一错误处理：在 CLI 与库边界处规范化抛出自定义错误类型（如 `QraftError`），并在主入口统一映射退出码，提升可诊断性与一致性。
- 为策略/引擎的导入保护补充契约测试（contract tests），覆盖“无 Nautilus”“有 Nautilus”“stub/monkeypatch”三类场景。