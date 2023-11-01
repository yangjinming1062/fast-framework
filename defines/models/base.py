"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : base.py
Author      : jinming.yang
Description : model基础信息定义
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import uuid
from datetime import datetime
from ipaddress import ip_network

from cryptography.fernet import Fernet
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.properties import ColumnProperty
from typing_extensions import Annotated

from config import Configuration

CONFIG = Configuration()
SECRET = Fernet(CONFIG.secret_key)

str_id = Annotated[str, mapped_column(String(16), index=True)]
str_small = Annotated[str, mapped_column(String(32))]
str_medium = Annotated[str, mapped_column(String(64))]
str_large = Annotated[str, mapped_column(String(128))]
str_huge = Annotated[str, mapped_column(String(256))]


class ModelBase:
    """
    提供公共方法的基类
    """

    @classmethod
    def get_columns(cls):
        """
        获取类中的全部数据库列的名称。

        Returns:
            dict: key是列名称，value是列定义
        """
        return {p.key: p for p in cls.__mapper__.iterate_properties if isinstance(p, ColumnProperty)}

    @staticmethod
    def encrypt(data):
        """
        加密给定的数据并返回加密的结果。

        Parameters:
            data (str | bytes): 需要加密的数据。

        Returns:
            str: 加密的结果。
        """
        if isinstance(data, str):
            data = data.encode()
        return SECRET.encrypt(data).decode('utf-8')

    @staticmethod
    def decrypt(data):
        """
        解密给定数据并返回解码后的字符串。

        Args:
            data (bytes): 要解密的加密数据。

        Returns:
            str: 解码后的字符串。
        """
        return SECRET.decrypt(data).decode('utf-8')


class OLTPModelBase(DeclarativeBase, ModelBase):
    """
    OLTP模型基类
    """
    __abstract__ = True

    id: Mapped[str_id] = mapped_column(primary_key=True, default=lambda: uuid.uuid4().hex[-12:])


class OLAPModelBase(DeclarativeBase, ModelBase):
    """
    OLAP模型基类
    """
    __abstract__ = True

    @classmethod
    def add_ip_filter(cls, sql, column, value):
        """
        添加IP类型列的查询条件。

        Args:
            sql: SQL对象。
            column (Column): 需要查询的列。
            value (str): 需要查询的IP。

        Returns:
            添加了搜索条件的SQL对象。
        """
        if '*' in value:
            return sql.where(func.IPv4NumToString(column).like(value.replace('*', '%')))
        elif '/' in value:
            ip_net = ip_network(value, strict=False)
            return sql.where(
                column >= ip_net.network_address,
                column <= ip_net.broadcast_address,
            )
        else:
            return sql.where(func.IPv4NumToString(column) == value)


class TimeColumns:
    """
    时间列基类
    """
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)
