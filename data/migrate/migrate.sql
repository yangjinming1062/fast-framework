CREATE DATABASE IF NOT EXISTS app;
CREATE USER IF NOT EXISTS 'admin' @'0.0.0.0' IDENTIFIED BY 'IDoNotKnow';
SET
  PASSWORD FOR 'admin' = PASSWORD('IDoNotKnow');
GRANT SELECT_PRIV,
  LOAD_PRIV,
  ALTER_PRIV,
  CREATE_PRIV,
  DROP_PRIV ON fast.* TO 'admin';

USE app;

CREATE TABLE IF NOT EXISTS user (
  `id` CHAR(24),
  `created_at` DATETIME(6) DEFAULT current_timestamp(6),
  `updated_at` DATETIME(6) DEFAULT current_timestamp(6) on update current_timestamp(6),
  `identify` CHAR(12),
  `email` VARCHAR(64),
  `phone` VARCHAR(32),
  `username` VARCHAR(32),
  `password` VARCHAR(64),
  `status` CHAR(12) DEFAULT "active"
) UNIQUE KEY(id) DISTRIBUTED BY HASH(id) BUCKETS AUTO PROPERTIES ("replication_num" = "1");
