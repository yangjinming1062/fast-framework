"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : base.py
Author      : jinming.yang
Description : API接口会共用到的一些类、方法的定义实现
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
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

from defines import *
from utils import *

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


def get_router(path, name, skip_auth=False):
    """
    使用给定的路径和名称为API生成一个路由器。

    Args:
        path (str): 路由的路径。
        name (str): 路由的名称。
        skip_auth (bool): 是否跳过鉴权。

    Returns:
        APIRouter: FastAPI的路由。
    """
    url_prefix = f'/{path.replace(".", "/")}'
    if skip_auth:
        return APIRouter(prefix=url_prefix, tags=[name])
    else:
        return APIRouter(prefix=url_prefix, tags=[name], dependencies=[Depends(get_user)])


def orm_create(cls, params, repeat_msg='关键字重复') -> str:
    """
    创建数据实例。

    Args:
        cls: ORM类定义。
        params (BaseModel): 请求参数。
        repeat_msg (str): 数据重复时的错误消息。

    Returns:
        str: 新增数据的ID。
    """
    # 将模型转储到字典中
    params = params.model_dump()
    # 因为updated_at在定义时是可选的，所以要加上默认值
    params['updated_at'] = datetime.now()
    # 剔除掉不属于该ORM类的参数
    _params = {k: v for k, v in params.items() if k in cls.get_columns()}
    # 执行SQL插入语句
    result, flag = execute_sql(insert(cls).values(**_params))
    # 检查结果，如果成功则返回ID
    if flag:
        return result
    else:
        # 如果存在重复记录，则返回repeat_msg，否则按照默认的错误信息
        if result.lower().find('duplicate') > 0:
            raise HTTPException(422, repeat_msg)
        else:
            raise HTTPException(422, '无效输入')


def orm_update(cls, resource_id, params, error_msg='无效输入'):
    """
    更新ORM数据。

    Args:
        cls: ORM类定义。
        resource_id (str): 数据的ID。
        params (BaseModel): 更新参数。
        error_msg (str): 更新失败时的错误消息。

    Returns:
        None
    """
    # 转储模型并排除未设置的字段
    params = params.model_dump(exclude_unset=True)
    # 因为updated_at在定义时是可选的，所以要加上默认值
    params['updated_at'] = datetime.now()
    # 剔除掉不属于该ORM类的参数
    _params = {k: v for k, v in params.items() if k in cls.get_columns()}
    # 执行SQL更新语句
    result, flag = execute_sql(update(cls).where(cls.id == resource_id).values(**_params))
    # 检查执行结果
    if flag and not result:
        raise HTTPException(404, '未找到对应资源')
    elif not flag:
        raise HTTPException(422, error_msg)


def orm_delete(cls, data):
    """
    删除数据实例。

    Args:
        cls: ORM类定义。
        data (List[str]): 待删除的数据ID列表。

    Returns:
        None
    """
    with DatabaseManager() as db:
        try:
            # 通过delete方法删除实例数据可以在有关联关系时删除级联的子数据
            for instance in db.oltp.scalars(select(cls).where(cls.id.in_(data))).all():
                db.oltp.delete(instance)
        except Exception as ex:
            db.oltp.rollback()
            logger.exception(ex)
            raise HTTPException(400, '无效资源选择')
        finally:
            db.oltp.commit()


def paginate_query(sql, paginate, scalar=False, format_func=None, session=None, with_total=False):
    """
    分页查询结果。

    Args:
        sql (Select): SQL查询。
        paginate (PaginateRequest): 分页参数。
        scalar (bool): 执行查询时是否返回结果的第一列。
        format_func: 用于格式化查询结果的函数。
        session: 无法自动判断查询数据库时需要指定的查询连接。
        with_total (bool): 查询结果中的最后一列是否为总数。

    Returns:
        包含总计数和查询结果数据的词典。
    """
    # Calculate the total count of rows
    if not with_total:
        total_sql = select(func.count()).select_from(sql)
        total = execute_sql(total_sql, fetchall=False, scalar=True, session=session)
    else:
        total = 0
    # Apply pagination parameters to the query
    sql = sql.limit(paginate.size).offset(paginate.page * paginate.size)
    # Sort the query result
    for column in paginate.sort or []:
        if column == '':
            continue
        if column[0] in ('+', '-'):
            direct = 'DESC' if column[0] == '-' else 'ASC'
            column = column[1:]
        else:
            direct = 'ASC'
        sql = sql.order_by(text(f'{column} {direct}'))
    # Execute the query
    result = {
        'total': total,
        'data': execute_sql(sql, fetchall=True, scalar=scalar, session=session)
    }
    # Update the total count if the last column is the total count
    if with_total and len(result['data']) > 0:
        result['total'] = result['data'][0][-1]
    # Apply the format_func if provided
    if format_func:
        result['data'] = list(map(format_func, result.get('data')))
    return result


def add_filter(sql, column, value, op_type):
    """
    向SQL对象添加查询条件。

    Args:
        sql (Select): SQLAlchemy SQL语句对象。
        column (Column): 要查询的列。
        value: 查询参数。
        op_type: 操作类型。

    Returns:
        添加了where条件的SQL对象。
    """
    if value is not None:
        if op_type == 'like':
            if isinstance(value, list):
                # Use the like operator with a list of values
                return sql.where(or_(*[column.like(f'%{x}%') for x in value]))
            else:
                # Use the like operator with a single value
                return sql.where(column.like(f'%{value}%'))
        elif op_type == 'in':
            # Use the in operator
            return sql.where(column.in_(value))
        elif op_type == 'notin':
            # Use the notin operator
            return sql.where(column.notin_(value))
        elif op_type == 'datetime':
            # Get the start and end values for the datetime condition
            assert isinstance(value, DateFilterSchema), 'value must be a DateFilterSchema'
            return sql.where(column.between(value.started_at, value.ended_at))
        elif op_type == 'json':
            # Translate column to text
            return sql.where(func.text(column).like(f'%{value}%'))
        elif op_type == 'ip':
            return OLAPModelBase.add_ip_filter(sql, column, value)
        else:
            # Evaluate the operation type with the column and parameter
            return sql.where(eval(f'column {op_type} value'))
    else:
        return sql
