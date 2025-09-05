# 任务0.2: Docker环境配置（事前设计）

## 1. 任务概述

根据Qraft7.0设计方案和开发规划表，设置开发和测试所需的容器环境，包括配置NATS、ClickHouse、Prometheus和Grafana等服务容器，以及创建应用服务的Dockerfile。

## 2. 设计内容

### 2.1 容器技术选择

考虑到开发环境已安装podman而非docker，我们将使用podman作为容器运行时，并利用podman对docker-compose.yml的兼容性，通过`podman-compose`工具来管理容器。

### 2.2 Docker Compose配置文件

创建`docker-compose.yml`文件，定义以下服务：

1. **NATS服务**：消息总线，用于组件间通信
2. **ClickHouse服务**：列式数据库，用于存储事件和模式数据
3. **Prometheus服务**：监控系统，收集各组件指标
4. **Grafana服务**：可视化监控数据
5. **应用服务**：Qraft主应用容器

### 2.3 数据卷配置

为确保数据持久化，需要配置以下数据卷：

1. **NATS数据卷**：存储NATS持久化数据
2. **ClickHouse数据卷**：存储ClickHouse数据和配置
3. **Prometheus数据卷**：存储监控数据
4. **Grafana数据卷**：存储仪表板配置
5. **配置卷**：存储各服务配置文件
6. **日志卷**：存储应用和服务日志

### 2.4 网络配置

创建自定义网络，确保容器间通信安全高效：

1. **前端网络**：连接API服务和前端服务
2. **后端网络**：连接内部服务（NATS、ClickHouse等）

### 2.5 应用Dockerfile

创建应用服务的Dockerfile，包含以下内容：

1. 基于Python 3.10镜像
2. 安装项目依赖
3. 配置应用环境变量
4. 设置启动命令

## 3. 实施步骤

### 3.1 创建项目容器目录结构

```
qraft/
├── docker-compose.yml       # 容器编排配置
├── Dockerfile               # 应用容器定义
├── data/                    # 数据卷目录
│   ├── nats/                # NATS数据
│   ├── clickhouse/          # ClickHouse数据
│   ├── prometheus/          # Prometheus数据
│   └── grafana/             # Grafana数据
├── configs/                 # 配置文件目录
│   ├── clickhouse/          # ClickHouse配置
│   └── prometheus/          # Prometheus配置
└── logs/                    # 日志目录
```

### 3.2 编写Docker Compose配置

创建`docker-compose.yml`文件，定义所有服务、网络和卷。

### 3.3 编写应用Dockerfile

创建应用服务的Dockerfile，定义应用容器构建过程。

### 3.4 创建必要的配置文件

为各服务创建基础配置文件，如Prometheus配置、ClickHouse配置等。

### 3.5 测试容器环境

使用podman-compose启动服务，验证容器间通信和数据卷持久化。

## 4. 测试计划

### 4.1 容器启动测试

- 验证所有容器能正常启动
- 检查容器日志是否有错误
- 确认容器健康状态

### 4.2 网络通信测试

- 测试NATS与应用服务间通信
- 测试应用服务与ClickHouse通信
- 测试Prometheus对各服务的监控

### 4.3 数据持久化测试

- 重启容器后验证数据是否保留
- 测试数据卷权限设置
- 验证日志正确写入

## 5. 验收标准

- 完整的docker-compose.yml文件，可通过podman-compose正常启动
- 所有服务容器能正常启动和运行
- 容器间网络通信正常
- 数据卷正确挂载和持久化
- 应用容器能正确构建和运行

## 6. 风险与对策

| 风险 | 对策 |
| --- | --- |
| podman与docker-compose兼容性问题 | 使用最新版podman-compose，必要时调整配置适配podman |
| 容器间网络延迟 | 配置合适的网络模式，优化网络设置 |
| 数据卷权限问题 | 明确设置卷权限，使用适当的用户运行容器 |
| 资源占用过高 | 为容器设置资源限制，避免单个服务占用过多资源 |
| 本地构建时网络代理问题 | 使用GitHub Actions在云端构建镜像，并推送到GitHub Container Registry |

## 7. 事后总结

任务0.2已成功完成，Docker环境配置工作按照计划顺利实施。具体完成情况如下：

### 7.1 目录结构创建

已创建完整的项目容器目录结构，包括：

- 数据卷目录（data/nats, data/clickhouse, data/prometheus, data/grafana）
- 配置目录（configs/clickhouse, configs/prometheus）
- 日志目录（logs/）

### 7.2 Docker Compose配置

已更新`docker-compose.yml`文件，添加了以下增强功能：

- 网络配置（前端网络和后端网络）
- 容器命名和健康检查
- 环境变量配置
- 服务依赖关系
- 重启策略
- 使用GitHub Container Registry镜像，避免本地构建问题

### 7.3 服务配置文件

已创建以下服务配置文件：

- Prometheus配置（prometheus.yml）
- ClickHouse配置（custom-config.xml, users.xml）

### 7.4 应用Dockerfile

已更新应用的Dockerfile，添加了以下功能：

- 系统依赖安装
- 健康检查配置
- 环境变量设置
- 日志目录创建

### 7.5 测试脚本

创建了容器环境测试脚本（test_containers.sh），用于验证：

- 容器启动状态
- 服务健康状态
- 网络通信
- 数据卷挂载

### 7.6 使用文档

创建了容器环境使用指南（CONTAINER_README.md）和其他文档，提供了：

- 环境要求说明
- 使用方法指导
- 常见问题解决方案
- 开发工作流说明
- GitHub CI/CD与容器镜像构建指南
- 容器使用指南

### 7.7 GitHub Actions配置

创建了GitHub Actions工作流配置文件，用于：

- 自动构建Docker镜像
- 推送镜像到GitHub Container Registry
- 解决本地构建时的网络代理问题

## 8. 反思

本次任务按照计划顺利完成，Docker环境配置工作已经完成并可以支持后续开发。在实施过程中，我们注意到以下几点：

### 8.1 成功之处

1. **兼容性考虑**：成功将Docker配置调整为兼容Podman的方式，满足了开发环境的实际需求。
2. **完整性**：配置了所有必要的服务，包括NATS、ClickHouse、Prometheus和Grafana，为后续开发提供了完整的基础设施。
3. **可测试性**：创建了测试脚本，确保容器环境可以被验证和测试。
4. **文档完善**：提供了详细的使用文档，便于团队成员理解和使用容器环境。
5. **CI/CD集成**：通过GitHub Actions实现了自动化构建和发布，解决了本地构建时的网络代理问题。

### 8.2 改进空间

1. **初始化脚本**：可以考虑添加一个初始化脚本，自动创建必要的数据库表和初始数据。
2. **资源限制**：当前配置未设置容器资源限制，在生产环境中应该添加CPU和内存限制。
3. **安全性**：默认配置中的密码和认证较为简单，生产环境需要加强安全配置。

### 8.3 经验教训

1. **工具选择灵活性**：在实际开发中，需要根据环境实际情况选择合适的工具，如本次从Docker调整为Podman。
2. **配置分层**：将配置分为开发环境和生产环境两套，可以更好地满足不同场景的需求。
3. **测试自动化**：自动化测试脚本对于确保环境一致性和可靠性非常重要。
4. **云服务利用**：当本地环境存在限制时，可以利用云服务（如GitHub Actions）来解决问题，提高开发效率。
5. **容器镜像分发**：使用容器镜像仓库（如GitHub Container Registry）可以简化镜像分发和版本管理。

总体而言，任务0.2已按照预期完成，Docker环境配置工作已经就绪，可以支持后续的开发工作。