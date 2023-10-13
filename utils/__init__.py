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

from .classes import DatabaseManager
from .classes import JSONExtensionEncoder
from .classes import KafkaManager
from .classes import RedisManager
from .classes import Singleton
from .constants import Constants
from .functions import exceptions
from .functions import execute_sql
from .functions import generate_key

# 日志记录
if not os.path.exists('./logs'):
    os.mkdir('./logs')
logger.add(
    './logs/info.log',
    format='{time:YYYY-MM-DD HH:mm:ss}|<level>{message}</level>',
    filter=lambda x: x['level'].name in ['TRACE', 'DEBUG', 'INFO'],
    colorize=True,
    retention='1 days',
    level='TRACE',
)
logger.add(
    './logs/error.log',
    format='{time:YYYY-MM-DD HH:mm:ss}|<level>{message}</level>',
    filter=lambda x: x['level'].name in ['WARNING', 'ERROR', 'CRITICAL'],
    colorize=True,
    retention='1 days',
    level='WARNING',
)
logger.add(sys.stdout, colorize=True, format='{time:YYYY-MM-DD HH:mm:ss}|<level>{message}</level>')
