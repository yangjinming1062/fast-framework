"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : __init__.py
Author      : jinming.yang
Description : 在__init__.py中统一导入
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
from .base import ModelBase
from .base import OLAPModelBase
from .base import OLTPModelBase
from .system import User

_base = [
    'ModelBase',
    'OLAPModelBase',
    'OLAPModelsDict',
    'OLTPModelBase',
    'OLTPModelsDict',
]

OLAPModelsDict = {x.__name__: x for x in OLAPModelBase.__subclasses__()}
OLTPModelsDict = {x.__name__: x for x in OLTPModelBase.__subclasses__()}

# 限制 from models import * 时导入的内容
__all__ = _base + list(OLAPModelsDict.keys()) + list(OLTPModelsDict.keys())
