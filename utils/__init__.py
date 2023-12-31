"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : __init__.py
Author      : jinming.yang
Description : 在init中导入各个子文件中的类、方法就可以直接从utils导入而无需关心具体路径了
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import os
import sys
from loguru import logger

from configs import CONFIG
from .classes import JSONExtensionEncoder
from .classes import Singleton
from .database import DatabaseManager
from .functions import bytes_to_str
from .functions import exceptions
from .functions import generate_key
from .functions import str_to_bytes
from .functions import time_function
from .kafka import KafkaManager
from .redis import RedisManager
from .secret import SecretManager

if CONFIG.log_dir:
    # 日志记录
    if not os.path.exists(CONFIG.log_dir):
        os.mkdir(CONFIG.log_dir)
    _c = {
        'handlers': [
            {
                'sink'  : os.path.join(CONFIG.log_dir, CONFIG.log_info_name),
                'format': CONFIG.log_format,
                'filter': lambda _x: _x['level'].name in ['DEBUG', 'INFO'],
                'level' : CONFIG.log_level,
            },
            {
                'sink'  : os.path.join(CONFIG.log_dir, CONFIG.log_error_name),
                'format': CONFIG.log_format,
                'filter': lambda _x: _x['level'].name in ['WARNING', 'ERROR', 'CRITICAL'],
                'level' : 'WARNING',
            }
        ],
    }
    if CONFIG.log_stdout:
        _c['handlers'].append({
            'sink'    : sys.stdout,
            'colorize': True,
            'format'  : CONFIG.log_format,
            'level'   : CONFIG.log_level,
        })
    logger.configure(**_c)

__all__ = [
    'logger',
    'JSONExtensionEncoder',
    'Singleton',
    'DatabaseManager',
    'bytes_to_str',
    'exceptions',
    'generate_key',
    'str_to_bytes',
    'time_function',
    'KafkaManager',
    'RedisManager',
    'SecretManager',
]
