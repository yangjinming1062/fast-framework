#!/bin/bash

migrate() {
  echo "执行数据库迁移"
  alembic init ./migrations  # 直接初始化迁移目录：如果已存在就是一个失败，没啥影响
  mv ./data/migration/env.py ./migrations/env.py
  sleep 1
  alembic revision --autogenerate  # 生成迁移文件
  alembic upgrade head  # 执行数据库迁移
  python command.py init  # 初始化数据库数据
}

migrate || {
		echo "迁移执行命令失败，请人工确认"
}
