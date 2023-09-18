"""
这里可以定义一些接口可以共用到的Schema
"""
from typing import List

from fastapi import Query
from pydantic import BaseModel


class PaginateRequest(BaseModel):
    """
    分页类请求共同参数定义
    """
    page: int = Query(ge=0)
    size: int = Query(gt=0, lt=100)
    sort: List[str] | None


class PaginateResponse(BaseModel):
    """
    分页类响应共同参数定义
    """
    total: int
    data: list
