#!/bin/bash

migrate() {
  echo "开始执行数据库迁移..."
  if [ ! -d "./migrations" ]; then
    alembic init ./migrations
    mv ./resources/migration/env.py ./migrations/env.py
  fi
  sleep 1
  alembic revision --autogenerate
  alembic upgrade head
  python command.py init
}

migrate || {
  echo "迁移执行命令失败，请人工确认"
}
