"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : base.py
Author      : jinming.yang
Description : API接口会共用到的一些类、方法的定义实现
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
from datetime import datetime
from typing import Union

from clickhouse_driver import Client
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from jose import jwt
from sqlalchemy import Column
from sqlalchemy import func
from sqlalchemy import insert
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy import update
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from defines import *
from utils import *

oltp_session_factory = scoped_session(sessionmaker(bind=OLTPEngine))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
ALGORITHM = 'HS256'


async def get_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, CONFIG.jwt_secret, algorithms=[ALGORITHM])
        if uid := payload.get('uid'):
            if user := execute_sql(select(User).where(User.id == uid), fetchall=False):
                return user
            else:
                raise HTTPException(404)
        else:
            raise HTTPException(401, '无效的认证信息')
    except JWTError:
        raise HTTPException(401, '无效的认证信息')


class SessionManager:
    def __init__(self):
        self.oltp = oltp_session_factory()
        self.olap = Client.from_url(CONFIG.olap_uri)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.oltp.close()
        self.olap.disconnect()


def get_router(path, name, skip_auth=False):
    """
    生成API的路由：方便统一调整
    """
    url_prefix = f'/{path.replace(".", "/")}'
    if skip_auth:
        return APIRouter(prefix=url_prefix, tags=[name])
    else:
        return APIRouter(prefix=url_prefix, tags=[name], dependencies=[Depends(get_user)])


def orm_create(cls, params: dict, repeat_msg='关键字重复'):
    """
    创建数据实例
    Args:
        cls: ORM类定义
        params: 参数
        repeat_msg: 新增重复时的响应

    Returns:
        新增数据的ID
    """
    params['updated_at'] = datetime.now()
    _params = {k: v for k, v in params.items() if k in cls.get_columns()}
    result, flag = execute_sql(insert(cls).values(**_params))
    if flag:
        return result
    else:
        if result.lower().find('duplicate') > 0:
            raise HTTPException(422, repeat_msg)
        else:
            raise HTTPException(422, '无效输入')


def orm_update(cls, resource_id: str, params: dict, error_msg='无效输入'):
    """
    ORM数据的更新
    Args:
        cls: ORM类定义
        resource_id: 资源ID
        params: 更新数据
        error_msg: 更新失败时的响应状态

    Returns:
        None
    """
    if not params:
        raise HTTPException(422, '缺少必填参数')
    params['updated_at'] = datetime.now()
    _params = {k: v for k, v in params.items() if k in cls.get_columns()}
    result, flag = execute_sql(update(cls).where(cls.id == resource_id).values(**_params))
    if flag and not result:
        raise HTTPException(404, '未找到对应资源')
    elif not flag:
        raise HTTPException(422, error_msg)


def orm_delete(cls, resource_id: Union[str, list, set]):
    """
    删除数据实例
    Args:
        cls: ORM类定义
        resource_id:  资源ID

    Returns:
        None
    """
    session = oltp_session_factory()
    try:
        if isinstance(resource_id, (list, set)):
            for instance in session.scalars(select(cls).where(cls.id.in_(resource_id))).all():
                session.delete(instance)
        else:
            if instance := session.query(cls).get(resource_id):
                session.delete(instance)  # 通过该方式可以级联删除子数据
    except Exception as ex:
        session.rollback()
        logger.exception(ex)
        raise HTTPException(400, '请求无效')
    finally:
        session.commit()


def paginate_query(sql, paginate: PaginateRequest, scalar=False, format_func=None, session=None):
    """
    统一分分页查询操作
    Args:
        sql: 查询SQL
        paginate: 分页参数
        scalar: 是否需要scalars
        format_func: 直接返回查询后的数据，不进行响应，用于数据结构需要特殊处理的情况
        session: 特殊OLAP等情况需要方法自己提供session

    Returns:
        {
            'total': int,
            'data': List[Any]
        }
    """

    def _add_sort(_sql):
        for column in paginate.sort or []:
            if column == '':
                continue
            if column[0] in ('+', '-'):
                direct = 'DESC' if column[0] == '-' else 'ASC'
                column = column[1:]
            else:
                direct = 'ASC'
            _sql = _sql.order_by(text(f'{column} {direct}'))
        return _sql

    if paginate.size == 0:
        # 特殊约定的查询全量数据的方式，可以以其他方式，比如size是-1等
        sql = _add_sort(sql)
        data = execute_sql(sql, fetchall=True, scalar=scalar, session=session)
        result = {'total': len(data), 'data': data}
    else:
        total_sql = select(func.count()).select_from(sql)
        total = execute_sql(total_sql, fetchall=False, scalar=True, session=session)
        sql = sql.limit(paginate.size).offset(paginate.page * paginate.size)
        result = {
            'total': total,
            'data': execute_sql(_add_sort(sql), fetchall=True, scalar=scalar, session=session)
        }
    if format_func:
        # 需要按照特定格式对数据进行修改的时候使用format_func
        result['data'] = list(map(format_func, result['data']))
    return result


def query_condition(sql, params: dict, column: Column, field_name=None, op_func=None, op_type=None):
    """
    添加查询参数
    Args:
        sql: SQL对象
        params: 接口参数
        column: 查询的列
        field_name: 条件名称(默认为空时和查询列同名)
        op_func: 操作函数(op_func优先于op_type)
        op_type: 操作类型(op_func和op_type至少一个不为None)

    Returns:
        添加where条件后的SQL对象
    """
    if (param := params.get(field_name or column.key)) is not None or op_type == 'datetime':
        if op_func:
            return sql.where(op_func(param))
        else:
            assert op_type is not None, 'op_type 和 op_func 至少一个不为None'
            if op_type == 'like':
                if isinstance(param, list):
                    return sql.where(or_(*[column.like(f'%{x}%') for x in param]))
                else:
                    return sql.where(column.like(f'%{param}%'))
            elif op_type == 'in':
                return sql.where(column.in_(param))
            elif op_type == 'notin':
                return sql.where(column.notin_(param))
            elif op_type == 'datetime':
                if start := params.get(f'{field_name or column.key}_start'):
                    sql = sql.where(column >= start)
                if end := params.get(f'{field_name or column.key}_end'):
                    sql = sql.where(column <= end)
                return sql
            else:
                return sql.where(eval(f'column {op_type} param'))
    else:
        return sql
