# 中医聊天机器人 Docker镜像

FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p data/vector_db data/documents logs plugins

# 暴露端口
EXPOSE 8000 7860

# 设置环境变量
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/tcm_chatbot.db

# 启动命令
CMD ["python", "main.py", "--all"]
