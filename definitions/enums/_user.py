from enum import Enum


class UserIdentifyEnum(Enum):
    """
    用户类型
    """

    ADMIN = "admin"
    USER = "user"


class UserStatusEnum(Enum):
    ACTIVE = "active"
    FORBIDDEN = "forbidden"
