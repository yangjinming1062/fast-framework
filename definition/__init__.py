from .enums import *
from .model import *
from .schema import *


class APIException(Exception):
    """
    API接口报错信息类
    """

    def __init__(self, status_code: int, code: APICode, msg: str = None):
        """

        Args:
            status_code (int): HTTP状态码
            code (APICode): 内部报错信息枚举
            msg (str | None): 附加报错信息，默认None使用code中的报错信息
        """
        self.status_code: int = status_code
        _c, _m = code.value
        self.code: str = _c
        self.msg: str = msg or _m
