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
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm.properties import ColumnProperty
from typing_extensions import Annotated

from config import Configuration

CONFIG = Configuration()

str_id = Annotated[str, mapped_column(String(16))]
str_small = Annotated[str, mapped_column(String(32))]
str_medium = Annotated[str, mapped_column(String(64))]
str_large = Annotated[str, mapped_column(String(128))]
str_huge = Annotated[str, mapped_column(String(256))]


class ModelBase(DeclarativeBase):
    """
    提供公共方法的基类
    """

    @classmethod
    def get_columns(cls):
        """
        获取类中的全部数据库列的名称
        Returns:
            列名称列表
        """
        return [prop.key for prop in cls.__mapper__.iterate_properties if isinstance(prop, ColumnProperty)]

    @classmethod
    def to_property(cls, columns):
        """
        根据列名获取对应的列
        """
        return getattr(cls, columns) if isinstance(columns, str) else [getattr(cls, name) for name in columns]

    def json(self, excluded: set = None) -> dict:
        """
        Convert the ORM instance to a serializable dictionary.

        Args:
            excluded: A set of columns to be excluded from the dictionary.

        Returns:
            dict: The serialized dictionary.
        """
        result = {}
        ignored_fields = excluded or set()

        # Iterate over the properties of the ORM instance
        for prop in self.__mapper__.iterate_properties:
            # Skip properties that are not columns
            if not isinstance(prop, ColumnProperty):
                continue
            # Skip properties that start with '_' or are in the ignored_fields set
            if prop.key.startswith('_') or prop.key in ignored_fields:
                continue
            value = getattr(self, prop.key)
            # If the value is a list of ORM instances, recursively call the json() method on each item
            if isinstance(value, InstrumentedList):
                result[prop.key] = [item.json() for item in value]
            # If the value is another ORM instance, recursively call the json() method
            elif isinstance(value, ModelBase):
                result[prop.key] = value.json()
            # If the column type is JSON, set the value directly
            elif isinstance(prop.columns[0].type, JSON):
                result[prop.key] = value if value else None
            # If the column type is DateTime, set the value to '-' if it is None
            elif isinstance(prop.columns[0].type, DateTime):
                result[prop.key] = value if value else '-'
            # Otherwise, set the value directly
            else:
                result[prop.key] = value

        return result


class OLTPModelBase(ModelBase):
    """
    OLTP模型基类
    """
    __abstract__ = True

    id: Mapped[str_id] = mapped_column(primary_key=True, default=lambda: uuid.uuid4().hex[-12:])


class OLAPModelBase(ModelBase):
    """
    OLAP模型基类
    """
    __abstract__ = True

    @classmethod
    def add_ip_filter(cls, sql, column: Column, ip: str):
        """
        Execute IP column retrieval.

        Args:
            sql: Query statement
            column: Column to query
            ip: Search condition

        Returns:
            SQL object with the added search condition
        """
        if '*' in ip:
            ip = ip.replace('*', '%')
            sql = sql.where(func.IPv4NumToString(column).like(ip))
        elif '/' in ip:
            try:
                ip_net = ip_network(ip, strict=False)
            except Exception:
                raise ValueError({f'IP地址格式错误': str(column)})
            sql = sql.where(
                column >= ip_net.network_address,
                column <= ip_net.broadcast_address,
            )
        else:
            sql = sql.where(func.IPv4NumToString(column) == ip)
        return sql


class TimeColumns:
    """
    时间列基类
    """
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), nullable=True)
