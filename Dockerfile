# 构建运行时环境
FROM python:3.11-slim-buster
# 设置时区
ENV TZ=Asia/Shanghai
# 设置语言
ENV LANG=zh_CN.UTF-8
# 设置工作目录
WORKDIR /fast
# 安装依赖
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
# 拷贝项目内容
COPY . .
RUN mv migrations migrations_init

EXPOSE 8000

# 单独只启动后端接口服务
CMD ["uvicorn", "main:app"]
