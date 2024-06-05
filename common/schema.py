from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class SchemaBase(BaseModel):
    class Config:
        """
        可以通过ORM对象实例序列化Schema
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
    size: int | None = Field(None, gt=0)
    sort: list[str] | None = None
    export: bool = Field(False, title="是否导出数据")
    key: list[str] | None = Field(None, title="按ID导出时的ID列表")


class PaginateResponse(BaseModel):
    """
    分页类响应共同参数定义: 注意子类需要提供类的的注释，因为其作用是提供下载时文档的名称
    """

    total: int = Field(default=0, title="总数")
    data: list
