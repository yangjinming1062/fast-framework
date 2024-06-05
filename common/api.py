import csv
import inspect
from datetime import datetime
from io import StringIO
from urllib.parse import quote

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose import JWTError
from sqlalchemy import Column
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import text

from components import *
from config import *
from modules.user.enums import UserStatusEnum
from modules.user.models import User

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


def get_router(path=None, name=None) -> APIRouter:
    """
    使用给定的路径和名称为API生成一个路由器。

    Args:
        path (str): 路由的路径(默认是调用所在文件的__name__参数自动拆分出路由路径，如有特殊需求可手动指定，如：console.agent)。
        name (str): 路由的名称(主要用于接口文档，默认None时取path最后一节作为名称)。

    Returns:
        APIRouter: FastAPI的路由。
    """
    if not path:
        caller_info = inspect.getmodule(inspect.currentframe().f_back)
        path = caller_info.__name__
    if not name:
        name = path.split(".")[-1]
    url_prefix = f'/{path.replace(".", "/")}'
    return APIRouter(prefix=url_prefix, tags=[name])


def paginate_query(stmt, request, response_schema, id_column=None, format_func=None):
    """
    分页查询结果。
    PS：因为paginate_query中执行数据查询的时候scalar被固定为False，因此不能直接select(cls)

    Args:
        stmt (Select): SQL查询（需要select具体的列，不能直接select(cls)）。
        request (PaginateRequest): 分页接口的请求参数（一定是PaginateRequest的子类）。
        response_schema (Type[PaginateResponse]): 接口响应数据定义（一定是PaginateResponse的子类）。
        id_column (Column | None): 如果接口提供下载功能则需要指定下载时按id过滤的列。
        format_func: 用于格式化查询结果的函数（会应用到查询结果的每一个对象上，之后再传递给response_schema）， 默认None则不进行额外操作。

    Returns:
        response_schema实例
    """
    # 计算总行数
    with DatabaseManager() as db:
        total = db.scalar(select(func.count()).select_from(stmt))
        # 将分页参数应用于查询
        if request.size is not None:
            stmt = stmt.limit(request.size)
        if request.page is not None:
            stmt = stmt.offset(request.page * request.size)
        # 导出数据时可以提供待导出数据的ID进行过滤
        if request.export and id_column is not None and request.key:
            stmt = stmt.where(id_column.in_(request.key))
        # 对查询结果进行排序
        for column_name in request.sort or []:
            if column_name == "":
                continue
            if column_name[0] in ("+", "-"):
                direct = "DESC" if column_name[0] == "-" else "ASC"
                column_name = column_name[1:]
            else:
                direct = "ASC"
            stmt = stmt.order_by(text(f"{column_name} {direct}"))
        # 执行查询
        data = db.execute(stmt).fetchall()
        # 应用format_func（如果提供）
        if format_func:
            data = [format_func(x) for x in data]
        result = response_schema(total=total, data=data)
        # 统一进行数据导出的处理
        return download_file(result.data, response_schema.__doc__.strip()) if request.export else result


def download_file(data, file_name):
    """
    统一实现从DataFrame下载CSV文件。

    Args:
        data (list[Type[BaseSchema]]): 要转换为CSV的DataFrame。
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
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_name)}",
    }
    return StreamingResponse(get_csv(), headers=headers)
