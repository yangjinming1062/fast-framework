"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : __init__.py
Author      : jinming.yang
Description : 在__init__.py中统一导入
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""

from ._system import User
from .base import ModelBase

_base = [
    "ModelBase",
    "ModelsDict",
]

ModelsDict = {x.__name__: x for x in ModelBase.__subclasses__()}

# 限制 from model import * 时导入的内容
__all__ = _base + list(ModelsDict.keys())
