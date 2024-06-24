from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.properties import ColumnProperty


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
    # 尽量选择整型类型。因为整型类型的计算和查找效率远高于字符串。
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    @classmethod
    def get_columns(cls):
        """
        获取类中的全部数据库列。

        Returns:
            dict[str, ColumnProperty]: key是列名称，value是列定义
        """
        return {p.key: p for p in cls.__mapper__.iterate_properties if isinstance(p, ColumnProperty)}


class ModelTimeColumns:
    """
    时间列基类
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_timestamp)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_timestamp, onupdate=get_timestamp)
