# 构建运行时环境
FROM python:3.12-slim-buster
# 设置时区
ENV TZ=Asia/Shanghai
# 设置语言
ENV LANG=zh_CN.UTF-8
# 设置工作目录
WORKDIR /fast
# 安装 Supervisor
RUN pip install supervisor -i https://pypi.mirrors.ustc.edu.cn/simple
# 安装python库
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 拷贝项目内容
COPY . .

CMD ["supervisord","-c","./supervisord.conf"]
