CREATE USER 'admin'@'0.0.0.0' IDENTIFIED BY 'IDoNotKnow';
CREATE DATABASE IF NOT EXIST fast CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON fast.* TO 'admin'@'0.0.0.0';


CREATE TABLE IF NOT EXIST user (
    role VARCHAR(255) COMMENT '角色',
    email VARCHAR(255) COMMENT '邮箱',
    phone VARCHAR(50) COMMENT '手机',
    username VARCHAR(50) COMMENT '用户名',
    account VARCHAR(255) NOT NULL UNIQUE COMMENT '账号',
    password VARCHAR(50) COMMENT '密码',
    valid TINYINT DEFAULT 1 COMMENT '是否有效'
);
