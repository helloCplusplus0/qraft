#!/bin/bash

set -e

echo "=== Qraft7.0 环境设置脚本 ==="

# 检查Python版本
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ $PYTHON_MAJOR -lt 3 ] || [ $PYTHON_MAJOR -eq 3 -a $PYTHON_MINOR -lt 10 ]; then
    echo "错误: 需要Python 3.10或更高版本，当前版本为 $PYTHON_VERSION"
    exit 1
fi

echo "Python版本检查通过: $PYTHON_VERSION"

# 检查Poetry是否安装
if ! command -v poetry &> /dev/null; then
    echo "未找到Poetry，正在安装..."
    curl -sSL https://install.python-poetry.org | python3 -
else
    echo "Poetry已安装: $(poetry --version)"
fi

# 创建数据目录
echo "创建数据目录..."
mkdir -p data/{nats,clickhouse,prometheus,grafana,states}

# 创建ClickHouse配置目录
echo "创建ClickHouse配置目录..."
mkdir -p configs/clickhouse

# 创建Prometheus配置目录
echo "创建Prometheus配置目录..."
mkdir -p configs/prometheus

# 创建Prometheus配置文件
echo "创建Prometheus配置文件..."
cat > configs/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'qraft'
    static_configs:
      - targets: ['qraft:8000']

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'clickhouse'
    static_configs:
      - targets: ['clickhouse:8123']

  - job_name: 'nats'
    static_configs:
      - targets: ['nats:8222']

  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
EOF

# 安装依赖
echo "安装项目依赖..."
poetry install

# 初始化Git仓库（如果尚未初始化）
if [ ! -d .git ]; then
    echo "初始化Git仓库..."
    git init
    git add .
    git commit -m "初始化项目"
fi

echo "=== 环境设置完成 ==="
echo "使用以下命令启动服务:"
echo "  docker-compose up -d"
echo "使用以下命令启动应用:"
echo "  poetry run uvicorn qraft.api.main:app --reload"