CREATE DATABASE IF NOT EXISTS fast;
CREATE USER IF NOT EXISTS 'admin'@'0.0.0.0' IDENTIFIED BY 'IDoNotKnow';
GRANT SELECT_PRIV,LOAD_PRIV,ALTER_PRIV,CREATE_PRIV,DROP_PRIV ON fast.* TO 'admin';

USE fast;

CREATE TABLE IF NOT EXISTS user
(
    id         VARCHAR(24),
    created_at DATETIME(6) DEFAULT current_timestamp(6),
    updated_at DATETIME(6) DEFAULT current_timestamp(6) on update current_timestamp(6),
    identify   VARCHAR(12),
    email      VARCHAR(64),
    phone      VARCHAR(32),
    username   VARCHAR(32),
    account    VARCHAR(64),
    password   VARCHAR(64),
    valid      TINYINT     DEFAULT "1"
) UNIQUE KEY(id)
DISTRIBUTED BY HASH(id) BUCKETS 4
PROPERTIES (
    "replication_num" = "1"
);

