import os
import sys

from loguru import logger

from .classes import Singleton
from .database import DatabaseManager
from .functions import bytes_to_str
from .functions import exceptions
from .functions import generate_key
from .functions import orjson_dump_extend
from .functions import str_to_bytes
from .kafka import KafkaManager
from .redis import RedisManager
from .secret import SecretManager
from config import CONFIG

if CONFIG.log_dir or CONFIG.log_stdout:
    _c = {"handlers": []}
    # 日志存放目录
    if CONFIG.log_dir:
        if not os.path.exists(CONFIG.log_dir):
            os.mkdir(CONFIG.log_dir)
        # 多个进程的时候考虑再次细化日志目录
        if CONFIG.program:
            dir_name = os.path.join(CONFIG.log_dir, CONFIG.program)
            if not os.path.exists(dir_name):
                os.mkdir(dir_name)
            info_log_path = os.path.join(CONFIG.log_dir, CONFIG.program, CONFIG.log_info_name)
            error_log_path = os.path.join(CONFIG.log_dir, CONFIG.program, CONFIG.log_error_name)
        else:
            info_log_path = os.path.join(CONFIG.log_dir, CONFIG.log_info_name)
            error_log_path = os.path.join(CONFIG.log_dir, CONFIG.log_error_name)
        _c["handlers"].extend(
            [
                {
                    "sink": info_log_path,
                    "format": CONFIG.log_format,
                    "filter": lambda _x: _x["level"].name in ["DEBUG", "INFO"],
                    "level": CONFIG.log_level,
                    "rotation": CONFIG.log_rotation,
                    "retention": CONFIG.log_retention,
                },
                {
                    "sink": error_log_path,
                    "format": CONFIG.log_format,
                    "filter": lambda _x: _x["level"].name in ["WARNING", "ERROR", "CRITICAL"],
                    "level": "WARNING",
                    "rotation": CONFIG.log_rotation,
                    "retention": CONFIG.log_retention,
                },
            ]
        )
    # 日志输出到控制台
    if CONFIG.log_stdout:
        _c["handlers"].append(
            {
                "sink": sys.stdout,
                "colorize": True,
                "format": CONFIG.log_format,
                "level": CONFIG.log_level,
            }
        )
    logger.configure(**_c)

__all__ = [
    "logger",
    "Singleton",
    "DatabaseManager",
    "bytes_to_str",
    "exceptions",
    "generate_key",
    "orjson_dump_extend",
    "str_to_bytes",
    "KafkaManager",
    "RedisManager",
    "SecretManager",
]
