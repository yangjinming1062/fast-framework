from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from config import CONFIG

_ENGINE_PARAMS = {
    "pool_size": CONFIG.db_pool_size,
    "pool_recycle": CONFIG.db_pool_recycle,
    "echo": CONFIG.db_echo,
}
_DB = create_engine(CONFIG.db_uri, **_ENGINE_PARAMS)


class DatabaseManager:
    """
    数据库连接管理器
    PS: 统一实现Postgres和ClickHouse的连接创建、关闭、提交回滚等逻辑
    """

    __slots__ = ("session", "autocommit", "type")
    session: Session | None

    def __init__(self, session=None):
        """
        请使用with 或 async with的上下文语法创建数据库连接。

        Args:
            session (Session | None): 默认None，如果传递了非None的数据库链接则复用该链接
        """
        if session is None:
            self.autocommit = True
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
            self.session = Session(_DB)
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
