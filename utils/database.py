"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : database.py
Author      : jinming.yang@qingteng.cn
Description : 数据库连接封装
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session

from configuration import CONFIG
from defines import SessionTypeEnum

_ENGINE_PARAMS = {
    'pool_size': CONFIG.db_pool_size,
    'pool_recycle': CONFIG.db_pool_recycle,
    'echo': CONFIG.db_echo,
}
_CH = create_engine(CONFIG.clickhouse_uri, **_ENGINE_PARAMS)
_CH_ASYNC = create_async_engine(CONFIG.clickhouse_async_uri, **_ENGINE_PARAMS)
_PG = create_engine(CONFIG.postgres_uri, **_ENGINE_PARAMS)
_PG_ASYNC = create_async_engine(CONFIG.postgres_async_uri, **_ENGINE_PARAMS)


class DatabaseManager:
    """
    数据库连接管理器
    PS: 统一实现Postgres和ClickHouse的连接创建、关闭、提交回滚等逻辑
    """

    __slots__ = ('session', 'autocommit', 'type')
    session: Session | AsyncSession | None

    def __init__(self, db_type, session=None):
        """
        请使用with 或 async with的上下文语法创建数据库连接。

        Args:
            db_type (SessionTypeEnum): 数据库类型
            session (Session | None): 默认None，如果传递了非None的数据库链接则复用该链接
        """
        if session is None:
            self.autocommit = True
            self.type = db_type
            self.session = None  # 延迟创建session，在进入上下文的时候根据是with还是async with选择不同的连接引擎
        else:
            self.autocommit = False
            self.session = session

    def __enter__(self):
        """
        with的进入方法，返回一个上下文对象。

        Returns:
            Session: 数据库连接
        """
        if self.session is None:
            if self.type == SessionTypeEnum.CH:
                self.session = Session(_CH)
            else:
                self.session = Session(_PG)
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        """
        当离开上下文时关闭数据库连接。

        Args:
            exc_type (type): The type of the exception that occurred, if any.
            exc_value (Exception): The exception object that was raised, if any.
            traceback (traceback): The traceback object that contains information about the exception, if any.
        """
        if exc_value:
            self.session.rollback()
        if self.autocommit:
            self.session.commit()
        self.session.close()

    async def __aenter__(self):
        """
        async with的进入方法，返回一个上下文对象。

        Returns:
            AsyncSession: 数据库连接
        """
        if self.session is None:
            if self.type == SessionTypeEnum.CH:
                self.session = AsyncSession(_CH_ASYNC)
            else:
                self.session = AsyncSession(_PG_ASYNC)
        return self.session

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        当离开上下文时关闭数据库连接。

        Args:
            exc_type (type): The type of the exception that occurred, if any.
            exc_value (Exception): The exception object that was raised, if any.
            traceback (traceback): The traceback object that contains information about the exception, if any.
        """
        if exc_value:
            await self.session.rollback()
        if self.autocommit:
            # !!! asynch的commit会raise errors.NotSupportedError
            # SQLAlchemy的commit在运行完会调用底层driver的commit也就是会抛出异常（但是数据已经提交了），因此改用flush
            await self.session.flush()
        await self.session.close()
