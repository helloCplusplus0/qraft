# GitHub CI/CD 与容器镜像构建指南

## 概述

为解决本地开发环境中容器构建时遇到的网络代理问题，我们将容器镜像构建过程迁移到GitHub Actions，并使用GitHub Container Registry (GHCR)存储和分发镜像。这样可以避免本地构建时的网络问题，同时提供更一致的开发和部署体验。

## GitHub Actions 工作流

我们在`.github/workflows/docker-build.yml`中配置了自动构建和发布Docker镜像的工作流：

- **触发条件**：
  - 推送到main或master分支
  - 修改Dockerfile或docker-compose.yml文件
  - 手动触发工作流

- **工作流程**：
  1. 检出代码
  2. 设置Docker Buildx
  3. 登录到GitHub Container Registry
  4. 提取镜像元数据
  5. 构建并推送镜像

## 镜像标签策略

镜像会使用以下标签策略：

- `latest`: 默认分支的最新版本
- `<branch-name>`: 特定分支的版本
- `<commit-sha>`: 特定提交的版本
- `<semver>`: 语义化版本号（如果有标签）

## 使用GitHub Container Registry镜像

### 拉取镜像

```bash
podman pull ghcr.io/hellocplusplus0/qraft/qraft-app:latest
```

### 在docker-compose.yml中使用

```yaml
services:
  qraft:
    image: ghcr.io/hellocplusplus0/qraft/qraft-app:latest
    # 其他配置...
```

## 本地开发与GitHub CI/CD的结合

### 工作流程

1. 在本地开发和测试代码
2. 提交并推送到GitHub仓库
3. GitHub Actions自动构建并发布Docker镜像
4. 在开发或生产环境中使用最新的镜像

### 最佳实践

- **版本控制**：使用语义化版本号标记重要发布
- **分支策略**：
  - `master`/`main`: 稳定版本
  - `develop`: 开发版本
  - 特性分支: 新功能开发

- **提交信息**：使用清晰的提交信息，便于跟踪变更

## 故障排除

### 常见问题

1. **镜像拉取失败**
   - 检查是否有权限访问GitHub Container Registry
   - 确认镜像名称和标签正确

2. **GitHub Actions构建失败**
   - 检查工作流日志以获取详细错误信息
   - 验证Dockerfile是否有语法错误

### 查看构建日志

在GitHub仓库页面，导航到Actions标签页可以查看所有工作流运行记录和详细日志。

## 安全考虑

- GitHub Actions使用仓库的GITHUB_TOKEN进行身份验证，无需额外配置
- 敏感信息（如API密钥）应存储在GitHub Secrets中，而不是直接硬编码在工作流文件中