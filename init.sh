#!/usr/bin/env bash

# 先初始化数据库（建库）
python command.py database
# 执行数据库迁移（建表）
alembic upgrade head
# 各自服务初始化数据（内置数据）
python command.py user --username=admin
