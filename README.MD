![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0+-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-v2.0+-green)

<br/>
<h1 align="center">
FastAPI后端项目框架
</h1>
<h4 align="center">专注于你的业务逻辑.</h4>

[//]: # (<h4 align="center">)

[//]: # (  <a href="https://placehold">Quickstart</a> |)

[//]: # (  <a href="https://placehold/">Docs</a> |)

[//]: # (  <a href="https://placehold">Tutorials</a> |)

[//]: # (</h4>)
<br/>

## 💡 功能特点

- 容器化：提供Docker及docker-compose文件，按需修改其中的参数即可使用（不改也能用）
- 轻量化：依赖的库尽可能的少
- 分层归类：实体、枚举、业务逻辑条理清晰
- 封装：接口的请求响应等常规内容均进行了统一的封装，专注于实现业务逻辑本身就好

# ⚡ 快速开始

1. （可选）修改model等业务逻辑相关的代码
2. （可选）修改docker.env及docker-compose.yml等文件中诸如镜像名称等需要自定义的参数
3. 生成服务端镜像
4. 通过docker-compose整体启动

```部署doris数据库
cd resource/doris
kubectl apply -f crd.yaml
kubectl apply -f operator.yaml
kubectl create namespace doris
kubectl apply -f cluster.yaml -n doris
```

```启动docker-compose
docker-compose -f docker-compose.yml up -d
```

# 📚 其他补充

## 数据迁移

迁移命令见根目录的initDB.sh脚本
