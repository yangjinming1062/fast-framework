# 构建运行时环境
FROM python:3.11-slim-buster
# 设置时区
ENV TZ=Asia/Shanghai
# 设置语言
ENV LANG=zh_CN.UTF-8
# 安装一些辅助apt包
RUN sed -i s@/deb.debian.org/@/mirrors.ustc.edu.cn/@g /etc/apt/sources.list && \
    sed -i s@/security.debian.org/@/mirrors.ustc.edu.cn/@g /etc/apt/sources.list && \
    apt-get clean && apt update && \
    apt install -y vim lrzsz supervisor && \
    apt clean -y &&  rm -rf /var/cache/debconf/* /var/lib/apt/lists/* /var/log/* /var/tmp/* /tmp/*
# 设置工作目录
WORKDIR /app
# 对外端口
EXPOSE 8080
# 安装python库
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple
# 拷贝项目内容
COPY . .
# 启动脚本
RUN chmod +x init.sh
ENTRYPOINT ["./init.sh"]
# 启动命令
CMD ["supervisord","-c","./supervisord.conf"]
