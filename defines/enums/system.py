from enum import Enum


class SessionTypeEnum(Enum):
    """
    数据库类型
    """
    PG = 'postgres'
    CH = 'clickhouse'


class RoleEnum(Enum):
    """
    合规枚举
    """
    Admin = 'admin'
    User = 'user'
