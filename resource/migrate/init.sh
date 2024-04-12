#!/bin/bash

# 设置要执行的SQL文件路径
SQL_FILE="/docker-entrypoint-initdb.d/migrate.sql"

# 执行SQL文件
mysql -uroot -P9030 -h 127.0.0.1 < $SQL_FILE
