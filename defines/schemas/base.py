from datetime import datetime
from typing import List

from pydantic import BaseModel
from pydantic import Field


class BaseSchema(BaseModel):
    """
    ORM类的Schema基类：也就省了一个id列，同时不要单独定义下面的Config了
    """
    id: str | None

    class Config:
        """
        表示可以是来自数据库的ORM实例
        """
        from_attributes = True


class DateFilterSchema(BaseModel):
    """
    时间过滤参数
    """
    started_at: datetime
    ended_at: datetime


class PaginateRequest(BaseModel):
    """
    分页类请求共同参数定义
    """
    page: int = Field(ge=0)
    size: int = Field(gt=0, lt=100)
    sort: List[str] | None


class PaginateResponse(BaseModel):
    """
    分页类响应共同参数定义
    """
    total: int = Field(default=0, title='总数')
    data: list
