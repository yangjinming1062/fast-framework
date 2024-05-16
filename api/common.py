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
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from components import *
from config import *
from definitions import *

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="token")


async def get_user(token: str = Depends(OAUTH2_SCHEME)):
    """
    需要鉴权的接口通过查询用户信息判断用户是否有权限访问。

    Args:
        token:

    Returns:

    """
    try:
        payload = jwt.decode(token, CONFIG.jwt_secret, algorithms=[CONSTANTS.JWT_ALGORITHM])
        if uid := payload.get("uid"):
            with DatabaseManager() as db:
                if user := db.get(User, uid):
                    if user.status == UserStatusEnum.FORBIDDEN:
                        raise HTTPException(403, "账号已被禁用, 请联系管理员")
                    db.expunge(user)
                    return user
                else:
                    raise HTTPException(403, "用户不存在")
        else:
            raise HTTPException(401, "无效的token")
    except JWTError:
        raise HTTPException(401, "无效的token")


def get_router(path, name):
    """
    使用给定的路径和名称为API生成一个路由器。

    Args:
        path (str): 路由的路径。
        name (str): 路由的名称。

    Returns:
        APIRouter: FastAPI的路由。
    """
    url_prefix = f'/{path.replace(".", "/")}'
    return APIRouter(prefix=url_prefix, tags=[name])


def create_instance(instance, error_msg=None) -> str:
    """
    新增数据实例。

    Args:
        instance: ORM类实例。
        error_msg (str): 数据重复时的错误消息。

    Returns:
        str: 新增数据的ID。
    """
    try:
        with DatabaseManager() as db:
            db.add(instance)
            db.flush()
            return instance.id
    except IntegrityError as ex:
        logger.debug(ex)
        raise HTTPException(422, error_msg)


def delete_instance(cls, data):
    """
    删除数据实例。

    Args:
        cls: ORM类定义。
        data (list[str] | str): 待删除的数据ID列表。

    Returns:
        None
    """

    try:
        with DatabaseManager() as db:
            if isinstance(data, str):
                instance = db.get(cls, data)
                db.delete(instance)
            else:
                for instance in db.scalars(select(cls).where(cls.id.in_(data))).all():
                    db.delete(instance)
    except Exception as ex:
        logger.exception(ex)
        raise HTTPException(400, str(ex))


def paginate_query(sql, paginate, resp_schema, id_column, format_func=None, session=None):
    """
    分页查询结果。
    PS：因为paginate_query中执行数据查询的时候scalar被固定为False，因此不能直接select(cls)

    Args:
        sql (Select): SQL查询。
        paginate (PaginateRequest): 分页参数。
        resp_schema (Type[PaginateResponse]): 接口响应数据定义。
        id_column (Column): 下载时按id过滤的列。
        format_func: 用于格式化查询结果的函数， 默认None则不进行额外操作。
        session (Session | None): 默认None时自动新建。

    Returns:
        包含总计数和查询结果数据的词典。
    """
    # 计算总行数
    with DatabaseManager(session=session) as db:
        total = db.scalar(select(func.count()).select_from(sql))
        # 将分页参数应用于查询
        if paginate.size is not None:
            sql = sql.limit(paginate.size)
        if paginate.page is not None:
            sql = sql.offset(paginate.page * paginate.size)
        # 导出数据时可以提供待导出数据的ID进行过滤
        if paginate.export and paginate.key:
            sql = sql.where(id_column.in_(paginate.key))
        # 对查询结果进行排序
        for column_name in paginate.sort or []:
            if column_name == "":
                continue
            if column_name[0] in ("+", "-"):
                direct = "DESC" if column_name[0] == "-" else "ASC"
                column_name = column_name[1:]
            else:
                direct = "ASC"
            sql = sql.order_by(text(f"{column_name} {direct}"))
        # 执行查询
        data = db.execute(sql).fetchall()
        # 应用format_func（如果提供）
        if format_func:
            data = [format_func(x) for x in data]
        result = resp_schema(total=total, data=data)
        # 统一进行数据导出的处理
        return download_file(result.data, resp_schema.__doc__.strip()) if paginate.export else result


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
        raise HTTPException(404, "无数据")

    file_name = f"{file_name}_{datetime.now().strftime(CONSTANTS.FORMAT_DATE)}.csv"
    headers = {
        "Content-Type": "text/csv;charset=utf-8",
        "Content-Disposition": f'attachment; filename="{file_name}"',
    }
    return StreamingResponse(get_csv(), headers=headers)
