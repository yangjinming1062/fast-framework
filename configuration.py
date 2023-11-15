"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : configuration.py
Author      : jinming.yang
Description : 常量、环境变量，各种参数配置
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class CONSTANTS:
    """
    常量定义：常量类型_常量名称
    """
    FORMAT_DATE = '%Y-%m-%d %H:%M:%S'


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=('.env', 'dev.env'), env_file_encoding='utf-8', extra='ignore')
    # 日志记录
    log_dir: str = ''
    log_level: str = 'DEBUG'
    log_info_name: str = 'info.log'
    log_error_name: str = 'error.log'
    log_stdout: bool = True
    log_format: str = '{time:YYYY-MM-DD HH:mm:ss}|<level>{message}</level>'
    log_retention: str = '1 days'
    # DB连接参数
    db_pool_size: int = 150
    db_pool_recycle: int = 60
    db_echo: bool = False
    # OLTP数据库相关参数
    pg_address: str
    pg_username: str = Field(alias='POSTGRESQL_USERNAME')
    pg_password: str = Field(alias='POSTGRESQL_PASSWORD')
    pg_db: str = Field(alias='POSTGRESQL_DATABASE')
    # OLAP数据库相关参数
    ch_address: str
    ch_username: str = Field(alias='CLICKHOUSE_ADMIN_USER')
    ch_password: str = Field(alias='CLICKHOUSE_ADMIN_PASSWORD')
    ch_db: str = Field(alias='CLICKHOUSE_DATABASE')
    # REDIS相关参数
    redis_host: str
    redis_port: int = 6379
    redis_password: str
    # KAFKA相关参数
    kafka_address: str
    kafka_consumer_timeout: int = 10
    kafka_protocol: str = 'PLAINTEXT'
    kafka_message_max_bytes: int
    kafka_producer_queue_size: int = 1000
    kafka_group: str = 'demo'
    # JWT
    jwt_token_expire_days: int = 7
    jwt_secret: str = 'DEMO_KEY'
    # Secret
    secret_key: bytes = b'_6TMXZCARlHQyko-3pQJLKNF_niJwDxtVzHn0BdHmlM='

    # 拓展属性

    @property
    def postgres_uri(self):
        return f'postgresql+psycopg://{self.pg_username}:{self.pg_password}@{self.pg_address}/{self.pg_db}'

    @property
    def postgres_async_uri(self):
        return f'postgresql+asyncpg://{self.pg_username}:{self.pg_password}@{self.pg_address}/{self.pg_db}'

    @property
    def clickhouse_uri(self):
        return f'clickhouse+native://{self.ch_username}:{self.ch_password}@{self.ch_address}/{self.ch_db}'

    @property
    def clickhouse_async_uri(self):
        return f'clickhouse+asynch://{self.ch_username}:{self.ch_password}@{self.ch_address}/{self.ch_db}'

    @property
    def kafka_producer_config(self):
        return {
            'bootstrap.servers': self.kafka_address,
            'security.protocol': self.kafka_protocol,
            'message.max.bytes': self.kafka_message_max_bytes,
            'queue.buffering.max.messages': self.kafka_producer_queue_size,
        }

    @property
    def kafka_consumer_config(self):
        return {
            'auto.offset.reset': 'earliest',
            'group.id': self.kafka_group,
            'bootstrap.servers': self.kafka_address,
        }


CONFIG = Config()

__all__ = ['CONFIG', 'CONSTANTS']
