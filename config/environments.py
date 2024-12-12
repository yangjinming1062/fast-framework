import os

import yaml
from cryptography.fernet import Fernet
from pydantic import BaseModel


def get_env(name, default):
    """
    获取变量值，优先级：环境变量 > .env文件 > yaml文件 > 默认值

    Args:
        name: 变量名称
        default: 默认值

    Returns:

    """

    def load_env_file(file_path):
        tmp = {}
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                for line in file:
                    if line.strip() and not line.startswith("#"):
                        key, value = line.strip().split("=")
                        tmp[key.strip()] = value.strip()
        return tmp

    def load_yaml_file(file_path):
        tmp = {}
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                tmp = yaml.safe_load(file)
        return tmp

    def _get_env():
        return os.getenv(name) or _ENV_FILE_CONFIG.get(name) or _YAML_FILE_CONFIG.get(name) or default

    _ENV_FILE_CONFIG = {}
    _YAML_FILE_CONFIG = {}

    # 注入env文件
    _ENV_FILE_CONFIG.update(load_env_file(".env"))
    _ENV_FILE_CONFIG.update(load_env_file("dev.env"))
    # 注入yaml文件
    _YAML_FILE_CONFIG.update(load_yaml_file("config.yaml"))

    return _get_env()


class Config(BaseModel):
    debug: bool = bool(get_env("DEBUG", True))
    # 日志记录
    log_dir: str = get_env("LOG_DIR", "")
    log_level: str = get_env("LOG_LEVEL", "INFO")
    log_info_name: str = get_env("LOG_INFO_NAME", "info.log")
    log_error_name: str = get_env("LOG_ERROR_NAME", "error.log")
    log_stdout: bool = bool(get_env("LOG_STDOUT", False))
    log_rotation: str = get_env("LOG_ROTATION", "10 MB")
    log_retention: str = get_env("LOG_RETENTION", "10 days")
    log_format: str = get_env("LOG_FORMAT", "{file}|{time:YYYY-MM-DD HH:mm:ss}|{level}|{message}")
    # DB参数
    db_pool_size: int = int(get_env("DB_POOL_SIZE", 150))
    db_pool_recycle: int = int(get_env("DB_POOL_RECYCLE", 60))
    db_echo: bool = bool(get_env("DB_ECHO", False))
    db_uri: str = get_env("DB_URI", "doris+pymysql://admin:IDoNotKnow@db:9030/app")
    # REDIS相关参数
    redis_host: str = get_env("REDIS_HOST", "redis")
    redis_port: int = get_env("REDIS_PORT", 6379)
    redis_password: str = get_env("REDIS_PASSWORD", "")
    # KAFKA相关参数
    kafka_address: str = get_env("KAFKA_ADDRESS", "kafka:9092")
    kafka_consumer_timeout: int = get_env("KAFKA_CONSUMER_TIMEOUT", 1000)
    kafka_protocol: str = get_env("KAFKA_PROTOCOL", "PLAINTEXT")
    kafka_message_max_bytes: int = int(get_env("KAFKA_MESSAGE_MAX_BYTES", 1000000))
    kafka_producer_queue_size: int = int(get_env("KAFKA_PRODUCER_QUEUE_SIZE", 100000))
    kafka_group: str = get_env("KAFKA_GROUP", "app")
    # JWT
    jwt_token_expire_days: int = int(get_env("JWT_TOKEN_EXPIRE_DAYS", 7))
    jwt_secret: str = get_env("JWT_SECRET", "DEMO-SECRET-KEY")
    # Secret ※注意：请不要在生产环境中使用默认的随机密钥
    secret_key: bytes = bytes(get_env("SECRET_KEY", "").encode()) or Fernet.generate_key()
    # 其他参数
    program: str = get_env("PROGRAM_NAME", "")

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
