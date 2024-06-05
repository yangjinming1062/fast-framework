import os

from cryptography.fernet import Fernet
from pydantic import BaseModel

_ENV = os.getenv


class Config(BaseModel):
    # 日志记录
    log_dir: str = _ENV("LOG_DIR", "")
    log_level: str = _ENV("LOG_LEVEL", "INFO")
    log_info_name: str = _ENV("LOG_INFO_NAME", "info.log")
    log_error_name: str = _ENV("LOG_ERROR_NAME", "error.log")
    log_stdout: bool = bool(_ENV("LOG_STDOUT", False))
    log_rotation: str = _ENV("LOG_ROTATION", "10 MB")
    log_retention: str = _ENV("LOG_RETENTION", "10 days")
    log_format: str = _ENV("LOG_FORMAT", "{file}|{time:YYYY-MM-DD HH:mm:ss}|{level}|{message}")
    # DB参数
    db_pool_size: int = int(_ENV("DB_POOL_SIZE", 150))
    db_pool_recycle: int = int(_ENV("DB_POOL_RECYCLE", 60))
    db_echo: bool = bool(_ENV("DB_ECHO", False))
    db_uri: str = _ENV("DB_URI", "doris+pymysql://admin:IDoNotKnow@db:9030/app")
    # REDIS相关参数
    redis_host: str = _ENV("REDIS_HOST", "redis")
    redis_port: int = _ENV("REDIS_PORT", 6379)
    redis_password: str = _ENV("REDIS_PASSWORD", "")
    # KAFKA相关参数
    kafka_address: str = _ENV("KAFKA_ADDRESS", "kafka:9092")
    kafka_consumer_timeout: int = _ENV("KAFKA_CONSUMER_TIMEOUT", 1000)
    kafka_protocol: str = _ENV("KAFKA_PROTOCOL", "PLAINTEXT")
    kafka_message_max_bytes: int = int(_ENV("KAFKA_MESSAGE_MAX_BYTES", 1000000))
    kafka_producer_queue_size: int = int(_ENV("KAFKA_PRODUCER_QUEUE_SIZE", 100000))
    kafka_group: str = _ENV("KAFKA_GROUP", "app")
    # JWT
    jwt_token_expire_days: int = int(_ENV("JWT_TOKEN_EXPIRE_DAYS", 7))
    jwt_secret: str = _ENV("JWT_SECRET", "DEMO-SECRET-KEY")
    # Secret ※注意：请不要在生产环境中使用默认的随机密钥
    secret_key: bytes = bytes(_ENV("SECRET_KEY", Fernet.generate_key()))
    # 其他参数
    program: str = _ENV("PROGRAM_NAME", "")

    # 拓展属性
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
            "bootstrap.servers": self.kafka_address,
            "auto.offset.reset": "earliest",
            "group.id": self.kafka_group,
        }
