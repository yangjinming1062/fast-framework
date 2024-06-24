import csv
import inspect
from datetime import datetime
from enum import auto
from enum import Enum
from io import StringIO
from urllib.parse import quote

from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose import JWTError
from sqlalchemy import Column
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import text

from common.schema import DateFilterSchema
from components import *
from config import *
from modules.user.enums import UserStatusEnum
from modules.user.models import User

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="token")


class FilterTypeEnum(Enum):
    """
    操作类型
    """

    Datetime = auto()
    Like = auto()
    In = auto()
    NotIn = auto()
    Equal = auto()
    NotEqual = auto()
    GreaterThan = auto()
    GreaterThanOrEqual = auto()
    LessThan = auto()
    LessThanOrEqual = auto()


class APICode(Enum):
    """
    API接口错误响应代码枚举
    """

    # PS: 使用auto()自动生成枚举值，因此新增的错误只能在末尾添加，不能插入中间（避免对过往的报错信息）
    EXCEPTION = auto(), "系统异常", 500
    VALIDATION = auto(), "入参不合法", 422
    QUERY = auto(), "数据查询失败", 400
    CREATE = auto(), "资源创建失败", 400
    UPDATE = auto(), "资源更新失败", 400
    DELETE = auto(), "资源删除失败", 400
    NO_DATA = auto(), "所选范围无数据", 404
    NOT_FOUND = auto(), "数据不存在", 404
    INVALID_USER = auto(), "用户不存在", 401
    INVALID_TOKEN = auto(), "无效的token", 401
    INVALID_CAPTCHA = auto(), "验证码错误", 403
    INVALID_PASSWORD = auto(), "用户名或密码错误", 403
    INVALID_USERNAME = auto(), "用户名已存在", 403
    UN_SUPPORT = auto(), "不支持的操作", 403
    FORBIDDEN = auto(), "账号已被禁用, 请联系管理员", 403
    DUPLICATE_NAME = auto(), "名称重复", 422


class APIException(Exception):
    """
    API接口报错信息类
    """

    def __init__(self, code: APICode, msg: str = None, status_code: int = None):
        """

        Args:
            code (APICode): 内部报错信息枚举
            msg (str | None): 附加报错信息，默认None使用code中的报错信息
            status_code (int): HTTP状态码, 默认使用APICode中定义的状态码，但是也可以自定义。
        """
        _c, _m, _sc = code.value
        self.status_code: int = status_code or _sc
        self.code: int = _c
        self.msg: str = msg or _m


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
                        raise APIException(APICode.FORBIDDEN)
                    db.expunge(user)
                    return user
                else:
                    raise APIException(APICode.INVALID_USER)
        else:
            raise APIException(APICode.INVALID_TOKEN)
    except JWTError:
        raise APIException(APICode.INVALID_TOKEN)


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
        file_name = response_schema.__doc__.strip() if response_schema.__doc__ else "数据导出"
        return download_file(result.data, file_name) if request.export else result


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
        raise APIException(APICode.NO_DATA)

    file_name = f"{file_name}_{datetime.now().strftime(CONSTANTS.FORMAT_DATE)}.csv"
    headers = {
        "Content-Type": "text/csv;charset=utf-8",
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_name)}",
    }
    return StreamingResponse(get_csv(), headers=headers)


def get_condition(column, value, op_type):
    """
    生成过滤条件。

    Args:
        column (Column | InstrumentedAttribute): 要查询的列。
        value (Any): 查询参数。
        op_type (FilterTypeEnum): 操作类型。

    Returns:
        ColumnElement[bool] | None
    """

    if value is not None:
        if op_type == FilterTypeEnum.Datetime:
            assert isinstance(value, DateFilterSchema), "value must be a DateFilterSchema"
            return column.between(value.started_at, value.ended_at)
        elif op_type == FilterTypeEnum.Like:
            if isinstance(value, list):
                # like也可以用于列表：以或的关系
                return or_(*[column.like(f"%{x}%") for x in value])
            else:
                # 使用like运算符
                return column.like(f"%{value}%")
        elif op_type == FilterTypeEnum.In:
            # in运算符
            return column.in_(value)
        elif op_type == FilterTypeEnum.NotIn:
            # notin运算符
            return column.notin_(value)
        elif op_type == FilterTypeEnum.Equal:
            # 添加等于条件
            return column == value
        elif op_type == FilterTypeEnum.NotEqual:
            # 添加不等于条件
            return column != value
        elif op_type == FilterTypeEnum.GreaterThan:
            # 添加大于条件
            return column > value
        elif op_type == FilterTypeEnum.GreaterThanOrEqual:
            # 添加大于等于条件
            return column >= value
        elif op_type == FilterTypeEnum.LessThan:
            # 添加小于条件
            return column < value
        elif op_type == FilterTypeEnum.LessThanOrEqual:
            # 添加小于等于条件
            return column <= value


def add_filters(sql, query, columns):
    """
    向SQL对象添加Where查询条件。

    Args:
        sql (Select): SQLAlchemy SQL语句对象。
        query (SchemaBase): xxxRequest中的Query对象。
        columns (dict[Column | InstrumentedAttribute, FilterTypeEnum]): 要查询的列及期望的查询方式。

    Returns:
        添加了where条件的SQL对象。
    """
    if not query:
        return sql
    args = []
    for column, op_type in columns.items():
        if (arg := get_condition(column, getattr(query, column.key), op_type)) is not None:
            args.append(arg)
    return sql.where(*args) if args else sql
