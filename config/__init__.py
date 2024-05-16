"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : __init__.py.py
Author      : jinming.yang@qingteng.cn
Description : 常量、环境变量，各种参数配置
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""

from .constants import CONSTANTS
from .environments import Config

CONFIG = Config()

__all__ = ["CONFIG", "CONSTANTS"]
