# Qraft 6.0

Qraft 是一个研究到执行的一体化量化平台，采用分层解耦的单仓（mono-repo）结构。

## 快速开始

1) 准备环境

- Python 3.10 或 3.11
- 可选：Docker / Docker Compose

2) 安装依赖（本地）

```
make setup
```

3) 代码质量与测试

```
make lint
make mypy
make test
```

4) 使用 Docker 开发环境

```
./scripts/dev-env.sh
```

## 目录结构

- qraft/ 核心代码（数据/特征/策略/引擎/工具等）
- requirements/ 依赖与多 Python 版本约束
- docker/ Dockerfile.dev 与 Dockerfile.prod
- .github/workflows/ GitHub Actions CI
- scripts/ 常用脚本（setup/dev/test）

## 许可证

TBD