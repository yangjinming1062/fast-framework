USE ueba;

CREATE TABLE IF NOT EXISTS user (
  `id` CHAR(24),
  `identify` CHAR(12),
  `email` VARCHAR(64),
  `phone` VARCHAR(32),
  `username` VARCHAR(32),
  `password` VARCHAR(64),
  `status` CHAR(12) DEFAULT "active"
) UNIQUE KEY(id) DISTRIBUTED BY HASH(id) BUCKETS AUTO PROPERTIES ("replication_num" = "1");
