#!/bin/bash

migrate() {
  echo "Init Migrations"
  mkdir -p ./migrations/oltp/versions  # 防止没有文件夹生成迁移文件失败
  rsync -a ./migrations_init/ ./migrations/
  sleep 3
  alembic -c ./migrations/oltp/alembic.ini revision --autogenerate  # 生成迁移文件
  alembic -c ./migrations/oltp/alembic.ini upgrade head  # 执行数据库迁移
  python command.py init  # 初始化数据库数据
}

migrate || {
		echo "迁移执行命令失败，请人工确认"
}
