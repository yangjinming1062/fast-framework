from enum import Enum, auto


class APICode(Enum):
    """
    API接口错误响应代码
    """

    QUERY = "0201", "数据查询失败"
    CREATE = "0202", "资源创建失败"
    UPDATE = "0203", "资源更新失败"
    DELETE = "0204", "资源删除失败"
    NO_DATA = "0402", "所选范围无数据"
    INVALID_TOKEN = "0401", "无效的认证信息"
    UN_SUPPORT = "0403", "不支持的操作"
    AUTH_FAILED = "0403", "用户名或密码错误"


class FilterTypeEnum(Enum):
    """
    参数过滤类型
    """

    Like = auto()
    Datetime = auto()
    In = auto()
    NotIn = auto()
    Equal = auto()
    NotEqual = auto()
    GreaterThan = auto()
    GreaterThanOrEqual = auto()
    LessThan = auto()
    LessThanOrEqual = auto()


class UserIdentifyEnum(Enum):
    """
    用户类型
    """

    Admin = "admin"
    User = "user"
