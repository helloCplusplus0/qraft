# Task 2.4: 回测报表与审计包

## 设计目标

基于`task_list.md`要求，实现标准化回测报表生成和审计包系统，确保回测结果的可追溯性、完整性和透明度。该系统将：

1. 将`BacktestResult`对象转换为标准化报表（文本、HTML、JSON格式）
2. 创建包含内容寻址和哈希校验的审计包（Audit Package）
3. 实现Evidence Pack生成机制，确保数据完整性
4. 提供MANIFEST文件生成和验证功能

## 输入与输出

### 输入
- `BacktestResult` 对象（来自`qraft.engines.vectorbt_adapter`）
- 可选的元数据（策略名称、参数、时间戳等）
- 可选的自定义报表模板配置

### 输出
- 标准化报表（多种格式）
- 审计包（包含报表、元数据、校验和）
- Evidence Pack（带内容寻址的数据包）
- MANIFEST清单文件

## 关键组件与API设计

### 1. qraft/reports/generators.py
报表生成器模块，将`BacktestResult`转换为可读格式。

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
import pandas as pd
from qraft.engines.vectorbt_adapter import BacktestResult

@dataclass
class ReportConfig:
    """报表生成配置"""
    title: str = "Backtest Report"
    include_plots: bool = True
    format: str = "html"  # html, text, json
    precision: int = 4

class BacktestReportGenerator:
    """标准化回测报表生成器"""
    
    def generate_text_report(self, result: BacktestResult, config: ReportConfig) -> str:
        """生成纯文本报表"""
        
    def generate_html_report(self, result: BacktestResult, config: ReportConfig) -> str:
        """生成HTML报表，包含简单的SVG图表"""
        
    def generate_json_report(self, result: BacktestResult, config: ReportConfig) -> Dict[str, Any]:
        """生成结构化JSON报表"""
        
    def create_simple_sparkline(self, series: pd.Series, width: int = 200, height: int = 50) -> str:
        """创建简单的SVG sparkline图表（避免外部绘图依赖）"""
```

### 2. qraft/evidence/pack.py
Evidence Pack生成和验证，实现内容寻址和哈希校验。

```python
from dataclasses import dataclass
from typing import Dict, Any, List
from pathlib import Path
import hashlib

@dataclass
class EvidenceItem:
    """Evidence Pack中的单个项目"""
    name: str
    content: bytes
    content_hash: str
    size: int

class EvidencePack:
    """Evidence Pack管理器"""
    
    def __init__(self):
        self.items: Dict[str, EvidenceItem] = {}
        
    def add_item(self, name: str, content: bytes) -> str:
        """添加项目到Evidence Pack，返回内容哈希"""
        
    def compute_content_hash(self, content: bytes) -> str:
        """计算内容的SHA256哈希"""
        
    def generate_manifest(self) -> Dict[str, Any]:
        """生成MANIFEST清单"""
        
    def verify_integrity(self) -> bool:
        """验证包的完整性"""
        
    def save_to_directory(self, output_dir: Path) -> Path:
        """保存Evidence Pack到目录"""
        
    @classmethod
    def load_from_directory(cls, pack_dir: Path) -> 'EvidencePack':
        """从目录加载Evidence Pack"""
```

### 3. qraft/audit/package.py
审计包组装器，整合回测结果、报表和Evidence Pack。

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from qraft.engines.vectorbt_adapter import BacktestResult
from qraft.reports.generators import BacktestReportGenerator, ReportConfig
from qraft.evidence.pack import EvidencePack

@dataclass
class AuditMetadata:
    """审计包元数据"""
    strategy_name: str
    creation_time: datetime = field(default_factory=datetime.now)
    qraft_version: str = "6.0"
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

class AuditPackage:
    """审计包组装器"""
    
    def __init__(self, metadata: AuditMetadata):
        self.metadata = metadata
        self.evidence_pack = EvidencePack()
        self.report_generator = BacktestReportGenerator()
        
    def add_backtest_result(self, result: BacktestResult, config: Optional[ReportConfig] = None) -> None:
        """添加回测结果并生成报表"""
        
    def add_custom_file(self, name: str, content: bytes) -> None:
        """添加自定义文件到审计包"""
        
    def finalize(self, output_dir: Path) -> Path:
        """最终化审计包并保存到目录"""
        
    @classmethod
    def load_from_directory(cls, audit_dir: Path) -> 'AuditPackage':
        """从目录加载审计包"""
```

## 实现原则

1. **复用现有API**：基于已有的`BacktestResult`结构，避免重复设计
2. **无外部绘图依赖**：使用简单的SVG生成替代matplotlib等重量级库
3. **内容寻址**：使用SHA256哈希确保数据完整性
4. **轻量化设计**：避免过度工程，专注核心功能
5. **格式多样性**：支持文本、HTML、JSON多种输出格式

## 交付物

### 源代码
- `qraft/reports/generators.py` - 报表生成器
- `qraft/evidence/pack.py` - Evidence Pack管理
- `qraft/audit/package.py` - 审计包组装器
- 对应的`__init__.py`文件暴露公共API

### 测试
- `tests/unit/test_reports_and_audit.py` - 单元测试覆盖所有核心功能

### 文档
- 更新本文档的后实施总结

## 验收标准

1. **报表生成**：能成功将`BacktestResult`转换为文本、HTML、JSON三种格式
2. **Evidence Pack**：能正确计算内容哈希、生成MANIFEST、验证完整性
3. **审计包**：能组装完整的审计包并支持保存/加载
4. **测试覆盖**：所有核心功能通过单元测试
5. **API一致性**：遵循Qraft项目的代码风格和命名约定
6. **无外部依赖**：不引入matplotlib、plotly等新的绘图库
7. **内容寻址**：SHA256哈希正确实现，MANIFEST完整

## 技术约束

- 使用标准库和已有依赖（pandas、pathlib等）
- SVG图表通过字符串模板生成，避免重量级绘图库
- 文件操作使用pathlib，确保跨平台兼容性
- 遵循现有项目的logging和error handling模式

---

## 实施总结与复盘（Post-Implementation Summary）

### 实施内容
- 按设计实现了以下模块：
  - <mcfile name="generators.py" path="/home/dell/Projects/Qraft/qraft/reports/generators.py"></mcfile>
  - <mcfile name="pack.py" path="/home/dell/Projects/Qraft/qraft/evidence/pack.py"></mcfile>
  - <mcfile name="package.py" path="/home/dell/Projects/Qraft/qraft/audit/package.py"></mcfile>
  - 以及对应包的<mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/reports/__init__.py"></mcfile>、<mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/evidence/__init__.py"></mcfile>、<mcfile name="__init__.py" path="/home/dell/Projects/Qraft/qraft/audit/__init__.py"></mcfile>
- 新增单元测试：<mcfile name="test_reports_and_audit.py" path="/home/dell/Projects/Qraft/tests/unit/test_reports_and_audit.py"></mcfile>
- 运行pytest通过，未引入新的第三方可视化依赖。

### 与规划对齐情况
- 标准化报表生成：提供文本、HTML、JSON三种格式，HTML内置轻量SVG sparkline，满足“创建报表模板与可视化组件”要求。
- 审计包结构：通过EvidencePack实现内容寻址（SHA256）与blobs目录存储，并生成MANIFEST.json，满足“建立审计包结构”“建立内容寻址与哈希校验”“实现MANIFEST文件生成”。
- Evidence Pack生成机制：提供add_item、save/load、verify_integrity等API，支持端到端保存/加载与校验。

### 使用方式（示例）
- 报表生成：
  - from qraft.reports import BacktestReportGenerator, ReportConfig
  - gen = BacktestReportGenerator(); html_doc = gen.generate(result, ReportConfig(format="html"))
- 审计包：
  - from qraft.audit import AuditPackage, AuditMetadata
  - pkg = AuditPackage(AuditMetadata(strategy_name="demo")); pkg.add_backtest_result(result); pkg.finalize(Path("./out"))

### 后续改进建议
- 报表模板化：后续可加入简单占位符模板引擎，支持自定义主题与布局。
- 统计细化：在JSON报表中扩充更多统计字段（如月度收益、回撤周期）。
- CI集成：将审计包生成接入回测流水线，自动产出报告与MANIFEST校验。
- 签名与安全：可扩展PGP签名/公钥验证，增强不可抵赖性。

### 结论
本任务已按设计与验收标准完成，实现了回测报表与审计包的核心能力，测试全部通过，可用于后续集成与扩展。