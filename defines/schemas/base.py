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
    page: int | None = Field(None, ge=0)
    size: int | None = Field(None, gt=0, lt=100)
    sort: List[str] | None = None
    export: bool = Field(False, title='是否导出数据')
    data: List[str] | None = Field(None, title='按ID导出时的ID列表')


class PaginateResponse(BaseModel):
    """
    分页类响应共同参数定义
    """
    total: int = Field(default=0, title='总数')

    @property
    def data(self):
        """
        数据列表: 需要具体子类实现
        """
        raise NotImplementedError
