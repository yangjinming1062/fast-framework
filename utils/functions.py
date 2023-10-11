"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : functions.py
Author      : jinming.yang
Description : 基础方法的定义实现
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import uuid
from functools import wraps

from clickhouse_driver import Client
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import Configuration
from defines import *
from utils import logger

_OLAP_TABLES = {item.__tablename__ for item in OLAPModelsDict.values()}
CONFIG = Configuration()
OLTP_ENGINE = create_engine(CONFIG.oltp_uri, pool_size=150, pool_recycle=60)


def execute_sql(sql, *, fetchall=False, scalar=True, params=None, session=None):
    """
    Executes SQL statements.

    Args:
        sql: SQLAlchemy SQL statement object
        fetchall (bool): Whether to fetch all rows, defaults to False
        scalar (bool): Whether to return model instances when querying models, defaults to True
        params: Data to be inserted in bulk insert operations, defaults to None
        session: Session to execute the SQL statement, defaults to None

    Returns:
        When the SQL statement is a query:
            - List of rows, model instances or Row objects
        When the SQL statement is not a query:
            - Number of affected rows, error message or None, and a flag indicating whether the execution was successful
    """
    is_oltp = not isinstance(session, Client)
    # Determine the session and connection based on the SQL statement
    if sql.is_select:
        if session_flag := session is None:
            if sql.froms[0].name in _OLAP_TABLES:
                is_oltp = False
                session = Client.from_url(CONFIG.olap_uri)
            else:
                session = Session(OLTP_ENGINE)
    else:
        if session_flag := session is None:
            if sql.table.name in _OLAP_TABLES:
                is_oltp = False
                session = Client.from_url(CONFIG.oltp_uri)
            else:
                session = Session(OLTP_ENGINE)

    try:
        if sql.is_select:
            # Execute the select statement
            if not is_oltp:
                sql = sql.compile(compile_kwargs={'literal_binds': True}).string
            executed = session.execute(sql)
            if fetchall:
                result = executed.fetchall() if is_oltp else executed
                if scalar:
                    result = [row[0] for row in result]
            else:
                if is_oltp:
                    result = executed.first()
                else:
                    if executed:
                        result = executed[0]
                    else:
                        return None
                if scalar and result:
                    result = result[0]
            # Expunge the instances from the session if necessary
            if session_flag and is_oltp:
                session.expunge_all()
            return result
        elif sql.is_insert:
            # Insert statement, return the inserted ID
            if is_oltp:
                result = session.execute(sql, params) if params else session.execute(sql)
                session.flush()
                if hasattr(result, 'inserted_primary_key_rows'):
                    created_id = [key[0] for key in result.inserted_primary_key_rows]
                    return created_id if params else created_id[0], True
                else:
                    return '', True
            else:
                sql = sql.compile(compile_kwargs={'literal_binds': True}).string
                if params:
                    sql = sql.split('VALUES')[0] + 'VALUES'
                    session.execute(sql, params=params)
                else:
                    session.execute(sql)
                return '', True
        else:
            # Update or delete statement, return the number of affected rows
            result = session.execute(sql)
            session.flush()
            if result:
                return result.rowcount, True
            else:
                return 'SQL执行失败', False
    except IntegrityError as ex:
        if is_oltp:
            session.rollback()
        logger.exception(ex)
        return ex.args[0], False
    except Exception as ex:
        if is_oltp:
            session.rollback()
        logger.exception(ex)
        return str(ex), False
    finally:
        if session_flag:
            if is_oltp:
                session.commit()
                session.close()
            else:
                session.disconnect()


def exceptions(default=None):
    """
    Decorator: Exception handling

    Args:
        default: The value to return when an exception occurs

    Returns:
        The return value of the decorated function if no exception occurs,
        otherwise it returns the default value
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


def generate_key(*args):
    """
    Generate a 12-character key based on the given source.
    Args:
        *args: Variable number of arguments to generate the key from.
    Returns:
        str: The generated key.
    """
    if args:
        source = '-'.join(list(map(str, args)))
        tmp = uuid.uuid5(uuid.NAMESPACE_DNS, source)
    else:
        tmp = uuid.uuid4()
    return tmp.hex[-12:]
