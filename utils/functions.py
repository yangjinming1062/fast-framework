"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : functions.py
Author      : jinming.yang
Description : 基础方法的定义实现
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import uuid
from functools import wraps

from defines import OLAPModelsDict
from utils import logger
from .classes import DatabaseManager
from .classes import OLAPManager
from .classes import OLTPManager

_OLAP_TABLES = {item.__tablename__ for item in OLAPModelsDict.values()}


def exceptions(default=None):
    """
    装饰器: 异常捕获。

    Args:
        default: 当发生异常时返回的值。

    Returns:
        返回结果取决于执行的函数是否发生异常，如果发生异常则返回default的值，没有则返回函数本身的执行结果。
    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as ex:
                logger.exception(ex)
                return default

        return wrapper

    return decorator


@exceptions(default=(None, False))
def execute_sql(sql, *, fetchall=False, scalar=True, params=None, session=None):
    """
    执行SQL语句。

    Args:
        sql: SQLAlchemy的select/insert/update/delete语句。
        fetchall (bool): 是否拉取全部数据，默认是False。
        scalar (bool): 是否需要对查询结果执行scalar，查询Model对象或者单独一列时传True，查询多列时传False，默认True。
        params: 批量插入时传list，单独插入时传dict。
        session: 执行SQL对象的数据库连接，默认None时会根据SQL对象来判断是OLAP还是OLTP自动创建数据库连接，但是SQL对象使用了join则需要明确指定,
            默认是None。

    Returns:
        Any, bool: 第一位是查询结果，第二位是操作是否成功的标识位
    """
    # 根据SQL对象判断该使用哪个数据库连接
    if session is None:
        inherit = False
        if sql.is_select:
            session_type = OLAPManager if sql.froms[0].name in _OLAP_TABLES else OLTPManager
        else:
            session_type = OLAPManager if sql.table.name in _OLAP_TABLES else OLTPManager
    else:
        inherit = True
        session_type = None
    # 根据不同数据库类型执行数据查询操作
    with DatabaseManager(session=session, session_type=session_type) as db:
        if not inherit:
            # 如果是传递了session对象则session_type初始为None，这里需要明确具体的类型
            session_type = DatabaseManager.get_session_type(db)
        if session_type is OLTPManager:
            if sql.is_select:
                executed = db.execute(sql)
                if fetchall:
                    result = executed.scalars().all() if scalar else executed.fetchall()
                else:
                    result = executed.scalar() if scalar else executed.first()
                # 使查询结果脱离当前session，不然离开当前方法后无法访问里面的数据
                if not inherit:
                    db.expunge_all()
                return result, True
            elif sql.is_insert:
                result = db.execute(sql, params) if params else db.execute(sql)
                db.flush()
                if hasattr(result, 'inserted_primary_key_rows'):
                    created_id = [key[0] for key in result.inserted_primary_key_rows]
                    return created_id if params else created_id[0], True
                else:
                    return '', True
            else:
                result = db.execute(sql)
                db.flush()
                return result.rowcount, True if result else 'SQL执行失败', False
        elif session_type is OLAPManager:
            if sql.is_select:
                executed = db.execute(sql.compile(compile_kwargs={'literal_binds': True}).string)
                if fetchall:
                    result = [row[0] for row in executed] if scalar else executed
                else:
                    result = executed[0] if executed else None
                    if scalar and result:
                        result = result[0]
                return result, True
            elif sql.is_insert:
                # ClickHouse目前没有直接支持，需要将SQL对象编译成SQL字符串再通过Client去执行
                sql = sql.compile(compile_kwargs={'literal_binds': True}).string
                if params:
                    sql = sql.split('VALUES')[0] + 'VALUES'
                    db.execute(sql, params=params)
                else:
                    db.execute(sql)
                return '', True
            else:
                result = db.execute(sql)
                return result.rowcount, True if result else 'SQL执行失败', False


def generate_key(*args):
    """
    根据输入的参数生成一个12个字符的key。

    Args:
        *args: 用于生成Key的参数。

    Returns:
        str: 生成的Key。
    """
    if args:
        source = '-'.join(list(map(str, args)))
        tmp = uuid.uuid5(uuid.NAMESPACE_DNS, source)
    else:
        tmp = uuid.uuid4()
    return tmp.hex[-12:]
