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

from config import CONFIG
from defines import DatabaseTypeEnum

DB_ENGINE_CH = create_engine(CONFIG.clickhouse_uri, pool_size=150, pool_recycle=60)
DB_ENGINE_CH_ASYNC = create_async_engine(CONFIG.clickhouse_async_uri, pool_size=150, pool_recycle=60)
DB_ENGINE_PG = create_engine(CONFIG.postgres_uri, pool_size=150, pool_recycle=60)
DB_ENGINE_PG_ASYNC = create_async_engine(CONFIG.postgres_async_uri, pool_size=150, pool_recycle=60)


class DatabaseManager:
    """
    数据库管理: 统一实现Postgres和ClickHouse的连接创建、关闭、提交回滚等逻辑
    """
    __slots__ = ('session', 'autocommit', 'type')
    session: Session | AsyncSession

    def __init__(self, db_type, session=None):
        """

        Args:
            db_type (DatabaseTypeEnum): 数据库类型
            session (Session | None): 默认None，如果传递了非None的数据库链接则复用该链接
        """
        if session is None:
            self.autocommit = True
            self.type = db_type
            # 延迟创建session，在进入上下文的时候根据是with还是async with选择不同的连接引擎
        else:
            self.autocommit = False
            self.session = session

    def __enter__(self):
        """
        with的进入方法，返回一个上下文对象。

        Returns:
            数据管理器
        """
        if self.session is None:
            if self.type == DatabaseTypeEnum.CH:
                self.session = Session(DB_ENGINE_CH)
            else:
                self.session = Session(DB_ENGINE_PG)
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
            数据管理器
        """
        if self.session is None:
            if self.type == DatabaseTypeEnum.CH:
                self.session = AsyncSession(DB_ENGINE_CH_ASYNC)
            else:
                self.session = AsyncSession(DB_ENGINE_PG_ASYNC)
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
            await self.session.commit()
        await self.session.close()
