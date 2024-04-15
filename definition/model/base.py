"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : base.py
Author      : jinming.yang
Description : model基础信息定义
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.properties import ColumnProperty
from typing_extensions import Annotated

str_id = Annotated[str, mapped_column(String(36), index=True)]
str_small = Annotated[str, mapped_column(String(32))]
str_medium = Annotated[str, mapped_column(String(64))]
str_large = Annotated[str, mapped_column(String(128))]
str_huge = Annotated[str, mapped_column(String(256))]


def get_timestamp():
    """
    数据库时间函数
    """
    return datetime.now().astimezone()


class ModelBase(DeclarativeBase):
    """
    提供公共方法的基类
    """

    __abstract__ = True

    id: Mapped[str_id] = mapped_column(primary_key=True, default=lambda: uuid.uuid4().hex[-24:])

    @classmethod
    def get_columns(cls):
        """
        获取类中的全部数据库列。

        Returns:
            dict[str, ColumnProperty]: key是列名称，value是列定义
        """
        return {p.key: p for p in cls.__mapper__.iterate_properties if isinstance(p, ColumnProperty)}


class TimeColumns:
    """
    时间列基类
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_timestamp)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_timestamp, onupdate=get_timestamp)