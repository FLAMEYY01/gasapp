# 使用华为云Python 3.11镜像
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim

# 设置工作目录
WORKDIR /app

# 配置国内apt源并安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件并安装Python依赖（使用清华镜像源）
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口，只是个"标签/备注"，不做任何实际操作
EXPOSE 8501

# 环境变量由 docker-compose.yml 统一配置，避免重复

# 启动命令
CMD ["streamlit", "run", "integrator2025.py", "--server.address=0.0.0.0", "--server.port=8501"]
