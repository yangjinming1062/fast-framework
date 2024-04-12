"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : __init__.py.py
Author      : jinming.yang@qingteng.cn
Description : 常量、环境变量，各种参数配置
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""

from .argument import Config
from .constant import CONSTANTS

CONFIG = Config()

__all__ = ["CONFIG", "CONSTANTS"]
