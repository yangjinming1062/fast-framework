"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : __init__.py
Author      : jinming.yang
Description : 在__init__.py中统一导入
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
from ._system import User
from .base import ClickhouseModelBase
from .base import ModelBase
from .base import PostgresModelBase

_base = [
    'ModelBase',
    'ClickhouseModelBase',
    'ClickhouseModelsDict',
    'PostgresModelBase',
    'PostgresModelsDict',
]

ClickhouseModelsDict = {x.__name__: x for x in ClickhouseModelBase.__subclasses__()}
PostgresModelsDict = {x.__name__: x for x in PostgresModelBase.__subclasses__()}

# 限制 from models import * 时导入的内容
__all__ = _base + list(ClickhouseModelsDict.keys()) + list(PostgresModelsDict.keys())
