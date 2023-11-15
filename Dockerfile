# 构建运行时环境
FROM python:3.11-slim-buster
# 设置时区
ENV TZ=Asia/Shanghai
# 设置语言
ENV LANG=zh_CN.UTF-8
# 设置工作目录
WORKDIR /fast
# 安装python库
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple
# 拷贝项目内容
## 相对固定的内容
### API服务启动文件
COPY main.py .
### 环境变量配置读取
COPY .env .
COPY configuration.py .
### 数据库迁移
COPY resources/initDB.sh initDB.sh
### 基础数据目录
COPY resources resources
### 基础工具方法/类的目录
COPY utils utils
## 可能经常变动的内容
### API接口
COPY api api
### 非接口命令文件
COPY command.py .
### 数据模型定义
COPY defines defines

### 对外暴露端口
EXPOSE 8080

# 启动时执行的命令，一定会被执行（先于CMD）:先执行数据库迁移
# ENTRYPOINT ["/bin/bash", "-c", "source ./initDB.sh"]

# 容器启动后默认执行的命令及参数，能够被docker run 命令后面的命令行参数替换
CMD ["/bin/bash", "-c", "source ./initDB.sh && uvicorn main:app --port=8080"]
