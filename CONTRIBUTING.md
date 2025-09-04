# 贡献指南

感谢您对Qraft7.0项目的关注！我们欢迎各种形式的贡献，包括但不限于代码贡献、文档改进、问题报告和功能建议。

## 贡献流程

### 1. 提交问题

如果您发现了bug或有新功能建议，请先查看[问题列表](https://github.com/your-org/qraft/issues)，确认该问题尚未被报告。如果没有，请创建一个新的issue，并提供以下信息：

- 对问题的清晰描述
- 复现步骤（如适用）
- 预期行为与实际行为
- 环境信息（操作系统、Python版本等）

### 2. 代码贡献

1. Fork仓库
2. 创建特性分支（`git checkout -b feature/your-feature`）
3. 提交更改（`git commit -am 'Add some feature'`）
4. 推送到分支（`git push origin feature/your-feature`）
5. 创建Pull Request

### 3. 开发规范

#### 代码风格

我们使用以下工具确保代码质量和一致性：

- **flake8**：代码风格检查
- **black**：代码格式化
- **isort**：导入排序

提交代码前，请运行以下命令：

```bash
poetry run flake8 qraft tests
poetry run black qraft tests
poetry run isort qraft tests
```

#### 测试

所有新功能和bug修复都应该包含测试。运行测试：

```bash
poetry run pytest
```

#### 文档

- 所有公共API都应该有文档字符串
- 复杂的功能应该在文档中有详细说明

### 4. Pull Request流程

1. 确保您的PR针对`develop`分支
2. 确保所有测试通过
3. 更新相关文档
4. 在PR描述中清晰说明您的更改

### 5. 代码审查

所有PR都需要至少一名维护者的审查。审查过程中可能会要求您进行更改。

## 开发环境设置

1. 克隆仓库

```bash
git clone https://github.com/your-org/qraft.git
cd qraft
```

2. 安装依赖

```bash
poetry install
```

3. 启动开发服务

```bash
docker-compose up -d
```

## 分支策略

- `main`：主分支，稳定版本
- `develop`：开发分支，集成最新功能
- `feature/*`：功能分支，用于开发新功能
- `bugfix/*`：修复分支，用于修复bug

## 版本发布流程

1. 从`develop`分支创建`release/vX.Y.Z`分支
2. 在release分支上进行最终测试和bug修复
3. 合并到`main`分支并打标签
4. 合并回`develop`分支

## 行为准则

请尊重所有项目参与者，保持专业和友好的交流环境。

## 许可证

通过贡献代码，您同意您的贡献将在项目的许可证下发布。