from config import CONFIG

_db_name = CONFIG.db_uri.split("/")[-1]

INIT_SQL = f"""
CREATE DATABASE IF NOT EXISTS {_db_name};

CREATE TABLE IF NOT EXISTS {_db_name}.alembic_version (
  `id` VARCHAR(32),
  `version_num` VARCHAR(32)
) UNIQUE KEY(`id`) DISTRIBUTED BY HASH(id) BUCKETS AUTO PROPERTIES ("replication_num" = "1");
"""
