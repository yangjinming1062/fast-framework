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
    Generate a router for the API with the given path and name.

    Args:
        path (str): The path for the API.
        name (str): The name for the API.
        skip_auth (bool): Skip auth.

    Returns:
        APIRouter: The generated router.
    """
    url_prefix = f'/{path.replace(".", "/")}'
    if skip_auth:
        return APIRouter(prefix=url_prefix, tags=[name])
    else:
        return APIRouter(prefix=url_prefix, tags=[name], dependencies=[Depends(get_user)])


def orm_create(cls, params, repeat_msg='关键字重复') -> str:
    """
    Create a data instance.

    Args:
        cls: The ORM class definition.
        params (BaseModel): The parameters.
        repeat_msg (str): The response when there is a duplicate record.

    Returns:
        The ID of the newly created data.
    """
    # Dump the model into a dictionary
    params = params.model_dump()
    # Set the 'updated_at' field to the current datetime
    params['updated_at'] = datetime.now()
    # Filter out the parameters that are not part of the class columns
    _params = {k: v for k, v in params.items() if k in cls.get_columns()}
    # Execute the SQL insert statement
    result, flag = execute_sql(insert(cls).values(**_params))
    # Check the result and return the ID if successful
    if flag:
        return result
    else:
        # Raise an exception if there is a duplicate record
        if result.lower().find('duplicate') > 0:
            raise HTTPException(422, repeat_msg)
        else:
            raise HTTPException(422, '无效输入')


def orm_update(cls, resource_id, params, error_msg='无效输入'):
    """
    Update the ORM data.

    Args:
        cls: The ORM class definition.
        resource_id (str): The resource ID.
        params (BaseModel): The updated data.
        error_msg (str): The response message when update fails.

    Returns:
        None
    """
    # Dump the model and exclude unset fields
    params = params.model_dump(exclude_unset=True)
    # Set the 'updated_at' field to the current datetime
    params['updated_at'] = datetime.now()
    # Only include the parameters that are in the class columns
    _params = {k: v for k, v in params.items() if k in cls.get_columns()}
    # Execute the SQL update query
    result, flag = execute_sql(update(cls).where(cls.id == resource_id).values(**_params))
    # Check the result and raise appropriate exceptions
    if flag and not result:
        raise HTTPException(404, '未找到对应资源')
    elif not flag:
        raise HTTPException(422, error_msg)


def orm_delete(cls, data):
    """
    Delete data instance.

    Args:
        cls: ORM class definition.
        data (List[str]): Resource ID.

    Returns:
        None
    """
    with DatabaseManager() as db:
        try:
            # Delete instances in batch if resource_id is a list or set
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
    Paginate a query result.

    Args:
        sql (Select): The SQL query.
        paginate (PaginateRequest): The pagination parameters.
        scalar (bool): Whether to return scalars.
        format_func: Function to format the query result.
        session: The session to use for special cases.
        with_total (bool): Whether the last column in the query result is the total count.

    Returns:
        A dictionary with the total count and the query result data.
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
    Adds a query condition to the SQL object.

    Args:
        sql (Select): SQLAlchemy SQL statement object.
        column (Column): The column to query.
        value: The query parameters.
        op_type: The operation type.

    Returns:
        The SQL object with the added where condition.
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
