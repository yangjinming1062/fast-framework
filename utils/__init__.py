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

from config import CONFIG
from .classes import JSONExtensionEncoder
from .classes import Singleton
from .constants import Constants
from .database import DatabaseManager
from .functions import base64_to_str
from .functions import exceptions
from .functions import generate_key
from .functions import str_to_base64
from .kafka import KafkaManager
from .redis import RedisManager

if CONFIG.log_dir:
    # 日志记录
    if not os.path.exists(CONFIG.log_dir):
        os.mkdir(CONFIG.log_dir)
    logger.add(
        os.path.join(CONFIG.log_dir, CONFIG.log_info_name),
        format=CONFIG.log_format,
        filter=lambda x: x['level'].name in ['DEBUG', 'INFO'],
        retention=CONFIG.log_retention,
        level=CONFIG.log_level,
    )
    logger.add(
        os.path.join(CONFIG.log_dir, CONFIG.log_error_name),
        format=CONFIG.log_format,
        filter=lambda x: x['level'].name in ['WARNING', 'ERROR', 'CRITICAL'],
        retention=CONFIG.log_retention,
        level='WARNING',
    )
if CONFIG.log_stdout:
    logger.add(sys.stdout, colorize=True, format=CONFIG.log_format)
