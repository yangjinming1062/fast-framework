from enum import Enum


class RoleEnum(Enum):
    """
    合规枚举
    """
    Admin = '超级管理员'
    User = '用户'


class DBTypeEnum(Enum):
    """
    数据连接类型
    """
    OLAP = 'clickhouse'
    OLTP = 'postgresql'
