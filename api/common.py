"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : base.py
Author      : jinming.yang
Description : API接口会共用到的一些类、方法的定义实现
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import csv
from io import StringIO

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from jose import jwt
from sqlalchemy import Column
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from configs import *
from definitions import *
from utils import *

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl='token')
ALGORITHM = 'HS256'

_CH_TABLES = {item.__tablename__ for item in ClickhouseModelsDict.values()}


async def get_user(token: str = Depends(OAUTH2_SCHEME)):
    try:
        payload = jwt.decode(token, CONFIG.jwt_secret, algorithms=[ALGORITHM])
        if uid := payload.get('uid'):
            with DatabaseManager(SessionTypeEnum.PG) as db:
                if user := db.get(User, uid):
                    db.expunge(user)
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


def create_instance(instance, error_msg='无效输入') -> str:
    """
    新增数据实例。

    Args:
        instance: ORM类实例。
        error_msg (str): 数据重复时的错误消息。

    Returns:
        str: 新增数据的ID。
    """
    instance.updated_at = datetime.now()
    try:
        with DatabaseManager(SessionTypeEnum.PG) as db:
            db.add(instance)
            db.flush()
            return instance.id
    except IntegrityError as ex:
        logger.debug(ex)
        raise HTTPException(422, error_msg)


def update_instance(cls, instance_id, params, error_msg='无效输入'):
    """
    更新ORM数据。

    Args:
        cls: ORM类定义。
        instance_id (str): 数据的ID。
        params (dict): 更新参数。
        error_msg (str): 更新失败时的错误消息。

    Returns:
        None
    """
    params['updated_at'] = datetime.now()
    with DatabaseManager(SessionTypeEnum.PG) as db:
        if item := db.get(cls, instance_id):
            try:
                for key, value in params.items():
                    if value is not None:
                        setattr(item, key, value)
                db.commit()
            except IntegrityError as ex:
                logger.debug(ex)
                raise HTTPException(422, error_msg)
        else:
            raise HTTPException(404, '未找到对应资源')


def orm_delete(cls, data):
    """
    删除数据实例。

    Args:
        cls: ORM类定义。
        data (List[str]): 待删除的数据ID列表。

    Returns:
        None
    """

    try:
        with DatabaseManager(SessionTypeEnum.PG) as db:
            # 通过delete方法删除实例数据可以在有关联关系时删除级联的子数据
            for instance in db.scalars(select(cls).where(cls.id.in_(data))).all():
                db.delete(instance)
    except Exception as ex:
        logger.exception(ex)
        raise HTTPException(400, '无效资源选择')


def paginate_query(sql, paginate, schema, format_func=None, session=None):
    """
    分页查询结果。
    PS：因为paginate_query中执行数据查询的时候scalar被固定为False，因此不能直接select(cls)

    Args:
        sql (Select): SQL查询。
        paginate (PaginateRequest): 分页参数。
        schema (Type[PaginateResponse]): 接口响应数据定义。
        format_func: 用于格式化查询结果的函数， 默认None则不进行额外操作。
        session (Session | None): 默认None时根据查询对象自动判断，无法自动判断查询数据库时需要指定的查询连接。

    Returns:
        包含总计数和查询结果数据的词典。
    """
    engine = SessionTypeEnum.CH if sql.froms[0].name in _CH_TABLES else SessionTypeEnum.PG
    # 计算总行数
    with DatabaseManager(engine, session=session) as db:
        total = db.scalar(select(func.count()).select_from(sql))
        # 将分页参数应用于查询
        if paginate.size is not None:
            sql = sql.limit(paginate.size)
        if paginate.page is not None:
            sql = sql.offset(paginate.page * paginate.size)
        # 导出数据时可以提供待导出数据的ID进行过滤
        if paginate.export and paginate.keys:
            sql = sql.where(Column('id').in_(paginate.keys))
        # 对查询结果进行排序
        for column_name in paginate.sort or []:
            if column_name == '':
                continue
            if column_name[0] in ('+', '-'):
                direct = 'DESC' if column_name[0] == '-' else 'ASC'
                column_name = column_name[1:]
            else:
                direct = 'ASC'
            sql = sql.order_by(text(f'{column_name} {direct}'))
        # 执行查询
        data = db.execute(sql).fetchall()
        # 应用format_func（如果提供）
        if format_func:
            data = [format_func(x) for x in data]
        result = schema(total=total, data=data)
        # 统一进行数据导出的处理
        return download_file(result.data, schema.__doc__.strip()) if paginate.export else result


def _add_filter(column, value, op_type):
    """
    向SQL对象添加查询条件。

    Args:
        column (Column): 要查询的列。
        value (Any): 查询参数。
        op_type (str): 操作类型。

    Returns:
        ColumnElement | None
    """

    if value is not None:
        if op_type == 'like':
            if isinstance(value, list):
                # like也可以用于列表：以或的关系
                return or_(*[column.like(f'%{x}%') for x in value])
            else:
                # 使用like运算符
                return column.like(f'%{value}%')
        elif op_type == 'in':
            # in运算符
            return column.in_(value)
        elif op_type == 'notin':
            # notin运算符
            return column.notin_(value)
        elif op_type == 'datetime':
            # 添加时间过滤参数：这个地方可以根据情况调整
            assert isinstance(value, DateFilterSchema), 'value must be a DateFilterSchema'
            return column.between(value.started_at, value.ended_at)
        elif op_type == 'json':
            # 列类型是json时添加检索条件，这里直接将json变成text属于一种偷懒做法，具体取决用的数据库类型
            return func.text(column).like(f'%{value}%')
        elif op_type == 'ip':
            # Clickhouse添加IP列的过滤条件
            return ClickhouseModelBase.ip_filter(column, value)
        else:
            # 其他类似于==,>,<等这种运算符直接添加
            return eval(f'column {op_type} value')


def add_filter(sql, query, columns):
    """
    向SQL对象添加查询条件。

    Args:
        sql (Select): SQLAlchemy SQL语句对象。
        query (dict): 过滤参数
        columns (dict[Column, str]): 要查询的列。

    Returns:
        添加了where条件的SQL对象。
    """
    args = []
    for column, op_type in columns.items():
        if (arg := _add_filter(column, query.get(column.key), op_type)) is not None:
            args.append(arg)
    return sql.where(*args) if args else sql


def download_file(data, file_name):
    """
    从DataFrame下载CSV文件。

    Args:
        data (List[BaseSchema]): 要转换为CSV的DataFrame。
        file_name (str): 文件名称。

    Returns:
        StreamingResponse: 带有CSV文件的流式响应对象。
    """

    def get_csv():
        # 将DataFrame转换为CSV并将其存储在BytesIO对象中
        with StringIO() as csv_data:
            writer = csv.writer(csv_data)
            # 第一行先写入文件的title
            writer.writerow([v.title or k for k, v in data[0].model_fields.items()])
            for row in data:
                # 之后再把数据序列化成dict然后取出value
                writer.writerow([x for x in row.model_dump().values()])
            yield csv_data.getvalue()

    if not data:
        raise HTTPException(400, '所选范围无数据，下载失败')

    file_name = f'{file_name}_{datetime.now().strftime(CONSTANTS.FORMAT_DATE)}.csv'
    headers = {
        'Content-Type': 'text/csv;charset=utf-8',
        'Content-Disposition': f'attachment; filename="{file_name}"',
    }
    return StreamingResponse(get_csv(), headers=headers)
