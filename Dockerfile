FROM docker.io/library/python:3.10-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    QRAFT_CONFIG_DIR=/app/configs

# 安装系统依赖，只安装必要的包
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install --no-cache-dir poetry==1.6.1

# 复制项目文件
COPY pyproject.toml poetry.lock* /app/

# 配置Poetry不创建虚拟环境，直接安装到系统Python
RUN poetry config virtualenvs.create false

# 安装依赖
RUN poetry install --no-dev --no-interaction --no-ansi

# 创建日志目录
RUN mkdir -p /app/logs && chmod 777 /app/logs

# 复制应用代码
COPY . /app/

# 已在前面设置了环境变量，这里不需要重复设置

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

CMD ["uvicorn", "qraft.api.main:app", "--host", "0.0.0.0", "--port", "8000"]