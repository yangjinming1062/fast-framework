import json
from datetime import date
from datetime import datetime
from enum import Enum
from ipaddress import IPv4Address
from ipaddress import IPv6Address

from sqlalchemy.engine import Row

from .functions import bytes_to_str
from config import CONSTANTS


class Singleton(type):
    """
    实现单例的基类
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class JSONExtensionEncoder(json.JSONEncoder):
    """
    处理枚举等各种无法JSON序列化的类型
    """

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, datetime) or isinstance(obj, date):
            return obj.strftime(CONSTANTS.FORMAT_DATE)
        if isinstance(obj, Row):
            return dict(obj._mapping)
        if isinstance(obj, (IPv4Address, IPv6Address)):
            return str(obj)
        if isinstance(obj, bytes):
            # 将bytes类型转为base64编码的字符串
            return bytes_to_str(obj)
        return json.JSONEncoder.default(self, obj)
