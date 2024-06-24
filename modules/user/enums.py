from enum import Enum


class UserIdentifyEnum(Enum):
    """
    用户类型
    """

    ADMIN = "admin"
    USER = "user"


class UserStatusEnum(Enum):
    """
    用户状态
    """

    ACTIVE = "active"
    FORBIDDEN = "forbidden"
