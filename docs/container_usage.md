# 容器使用指南

## 概述

本文档提供了在本地开发环境中使用GitHub Container Registry (GHCR)中的Docker镜像的详细说明，以及如何解决常见问题。

## 使用GitHub Container Registry镜像

### 认证与拉取

1. **登录到GitHub Container Registry**

   ```bash
   echo $GITHUB_TOKEN | podman login ghcr.io -u USERNAME --password-stdin
   ```

   > 注意：需要替换`USERNAME`为你的GitHub用户名，`$GITHUB_TOKEN`为你的GitHub个人访问令牌。

2. **拉取镜像**

   ```bash
   podman pull ghcr.io/hellocplusplus0/qraft/qraft-app:latest
   ```

### 使用docker-compose

我们的`docker-compose.yml`文件已配置为使用GHCR中的镜像：

```yaml
services:
  qraft:
    image: ghcr.io/hellocplusplus0/qraft/qraft-app:latest
    # 其他配置...
```

启动服务：

```bash
podman-compose up -d
```

## 本地开发工作流

### 开发流程

1. **克隆仓库**

   ```bash
   git clone https://github.com/helloCplusplus0/qraft.git
   cd qraft
   ```

2. **修改代码**

   在本地进行代码修改和测试。

3. **提交并推送**

   ```bash
   git add .
   git commit -m "描述你的更改"
   git push origin master
   ```

4. **等待GitHub Actions构建**

   GitHub Actions会自动构建并推送新的Docker镜像到GHCR。

5. **使用最新镜像**

   ```bash
   podman pull ghcr.io/hellocplusplus0/qraft/qraft-app:latest
   podman-compose up -d
   ```

## 故障排除

### 常见问题

1. **拉取镜像失败**

   **问题**：`Error: initializing source docker://ghcr.io/...`

   **解决方案**：
   - 确认已登录到GHCR
   - 检查网络连接
   - 验证镜像名称和标签

2. **容器启动失败**

   **问题**：容器无法启动或健康检查失败

   **解决方案**：
   - 检查容器日志：`podman logs qraft-app`
   - 确认所有依赖服务（NATS、ClickHouse等）都已启动
   - 验证配置文件是否正确

3. **网络代理问题**

   **问题**：容器无法访问外部网络

   **解决方案**：
   - 确认宿主机网络设置
   - 检查容器网络配置
   - 如果使用代理，确保代理设置正确

## 数据卷管理

为确保数据持久化，我们使用以下数据卷：

- **NATS数据**：`./data/nats:/data`
- **ClickHouse数据**：`./data/clickhouse:/var/lib/clickhouse`
- **Prometheus数据**：`./data/prometheus:/prometheus`
- **Grafana数据**：`./data/grafana:/var/lib/grafana`
- **日志**：`./logs:/app/logs`

如果遇到权限问题，可以执行：

```bash
chmod -R 777 ./data ./logs
```

## 最佳实践

1. **定期更新镜像**

   ```bash
   podman pull ghcr.io/hellocplusplus0/qraft/qraft-app:latest
   ```

2. **使用特定版本标签**

   对于生产环境，建议使用特定版本标签而不是`latest`：

   ```bash
   podman pull ghcr.io/hellocplusplus0/qraft/qraft-app:v1.0.0
   ```

3. **备份数据**

   定期备份重要数据：

   ```bash
   tar -czf backup-$(date +%Y%m%d).tar.gz ./data
   ```

4. **监控容器健康状态**

   ```bash
   podman ps -a
   ```

   或使用Prometheus和Grafana监控容器健康状态。