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

    def json(self, excluded=None) -> dict:
        """
        将ORM实例转换为可序列化字典。

        Args:
            excluded (set | None): 要从结果中排除的列名。

        Returns:
            dict: 序列化结果。
        """
        result = {}
        ignored_fields = excluded or set()

        # 遍历ORM实例的属性
        for prop in self.__mapper__.iterate_properties:
            # 跳过非列的属性
            if not isinstance(prop, ColumnProperty):
                continue
            # 跳过以“_”开头或位于ignored_fields集中的属性
            if prop.key.startswith('_') or prop.key in ignored_fields:
                continue
            value = getattr(self, prop.key)
            # 如果该值是ORM实例的列表，则对每个项递归调用json（）方法
            if isinstance(value, InstrumentedList):
                result[prop.key] = [item.json() for item in value]
            # 如果该值是另一个ORM实例，则递归调用json（）方法
            elif isinstance(value, ModelBase):
                result[prop.key] = value.json()
            # 如果列类型为JSON，则直接返回json内容
            elif isinstance(prop.columns[0].type, JSON):
                result[prop.key] = value if value else None
            # 如果列类型为DateTime，当日期为空时返回'-'字符串
            elif isinstance(prop.columns[0].type, DateTime):
                result[prop.key] = value if value else '-'
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
    def add_ip_filter(cls, sql, column, ip):
        """
        添加IP类型列的查询条件。

        Args:
            sql: SQL对象。
            column (Column): 需要查询的列。
            ip (str): 需要查询的IP。

        Returns:
            添加了搜索条件的SQL对象。
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
