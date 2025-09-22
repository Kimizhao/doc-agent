FROM ubuntu:22.04

# 设置非交互式安装
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 设置清华镜像源
RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 安装Python 3.11及libreoffice
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-venv python3.11-dev python3-pip libreoffice \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 创建Python虚拟环境
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 设置pip使用清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# 设置默认命令
CMD ["python3", "main.py"]