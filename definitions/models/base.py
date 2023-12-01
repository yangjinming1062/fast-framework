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

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.properties import ColumnProperty
from typing_extensions import Annotated

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
        获取类中的全部数据库列。

        Returns:
            dict[str, ColumnProperty]: key是列名称，value是列定义
        """
        return {p.key: p for p in cls.__mapper__.iterate_properties if isinstance(p, ColumnProperty)}


class PostgresModelBase(DeclarativeBase, ModelBase):
    """
    OLTP模型基类
    """

    __abstract__ = True

    id: Mapped[str_id] = mapped_column(primary_key=True, default=lambda: uuid.uuid4().hex[-12:])


class ClickhouseModelBase(DeclarativeBase, ModelBase):
    """
    OLAP模型基类
    """

    __abstract__ = True

    @classmethod
    def ip_filter(cls, column, value):
        """
        添加IP类型列的查询条件。

        Args:
            column (Column): 需要查询的列。
            value (str): 需要查询的IP。

        Returns:
            ColumnElement[bool]: 搜索条件。
        """
        if '*' in value:
            return func.IPv4NumToString(column).like(value.replace('*', '%'))
        elif '/' in value:
            ip_net = ip_network(value, strict=False)
            return and_(column >= ip_net.network_address, column <= ip_net.broadcast_address)
        else:
            return func.IPv4NumToString(column) == value


class TimeColumns:
    """
    时间列基类
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)
