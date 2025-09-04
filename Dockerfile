FROM python:3.10-slim

WORKDIR /app

# 安装Poetry
RUN pip install poetry==1.6.1

# 复制项目文件
COPY pyproject.toml poetry.lock* /app/

# 配置Poetry不创建虚拟环境，直接安装到系统Python
RUN poetry config virtualenvs.create false

# 安装依赖
RUN poetry install --no-dev --no-interaction --no-ansi

# 复制应用代码
COPY . /app/

# 设置环境变量
ENV PYTHONPATH=/app

CMD ["uvicorn", "qraft.api.main:app", "--host", "0.0.0.0", "--port", "8000"]