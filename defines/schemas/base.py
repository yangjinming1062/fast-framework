from typing import List

from pydantic import BaseModel
from pydantic import Field


class SchemaBase(BaseModel):
    id: str | None

    class Config:
        """
        表示可以是来自数据库的ORM实例
        """
        orm_mode = True


class IDSchema(BaseModel):
    id: List[str]


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
