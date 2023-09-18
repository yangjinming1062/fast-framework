from .base import *
from .system import *

_base = {x.__name__ for x in BaseModel.__subclasses__()}
_schema = {x.__name__ for x in SchemaBase.__subclasses__()}
_paginate_req = {x.__name__ for x in PaginateRequest.__subclasses__()}
_paginate_resp = {x.__name__ for x in PaginateResponse.__subclasses__()}


# 限制 from models import * 时导入的内容
__all__ = list(_base | _schema | _paginate_req | _paginate_resp)
