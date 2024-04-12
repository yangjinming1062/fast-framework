"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : argument.py
Author      : jinming.yang@qingteng.cn
Description : 环境变量
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("resource/args.env", "dev.env"), env_file_encoding="utf-8", extra="ignore"
    )
    # 日志记录
    log_dir: str = ""
    log_level: str = "INFO"
    log_info_name: str = "info.log"
    log_error_name: str = "error.log"
    log_stdout: bool = True
    log_rotation: str = "10 MB"
    log_retention: str = "10 days"
    log_format: str = "{file}|{time:YYYY-MM-DD HH:mm:ss}|{level}|{message}"
    # DB连接参数
    db_pool_size: int = 150
    db_pool_recycle: int = 60
    db_echo: bool = False
    # 数据库相关参数
    db_address: str
    db_username: str
    db_password: str
    db_name: str
    # REDIS相关参数
    redis_host: str
    redis_port: int = 6379
    redis_password: str
    # KAFKA相关参数
    kafka_address: str
    kafka_consumer_timeout: int = 10
    kafka_protocol: str = "PLAINTEXT"
    kafka_message_max_bytes: int
    kafka_producer_queue_size: int = 1000
    kafka_group: str = "demo"
    # JWT
    jwt_token_expire_days: int = 7
    jwt_secret: str = "DEMO_KEY"
    # Secret
    secret_key: bytes = b"_6TMXZCARlHQyko-3pQJLKNF_niJwDxtVzHn0BdHmlM="

    # 拓展属性

    @property
    def db_uri(self):
        return f"doris+pymysql://{self.db_username}:{self.db_password}@{self.db_address}/{self.db_name}"

    @property
    def kafka_producer_config(self):
        return {
            "bootstrap.servers": self.kafka_address,
            "security.protocol": self.kafka_protocol,
            "message.max.bytes": self.kafka_message_max_bytes,
            "queue.buffering.max.messages": self.kafka_producer_queue_size,
        }

    @property
    def kafka_consumer_config(self):
        return {
            "auto.offset.reset": "earliest",
            "group.id": self.kafka_group,
            "bootstrap.servers": self.kafka_address,
        }
