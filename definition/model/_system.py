from .base import *
from ..enums import *


class User(ModelBase, TimeColumns):
    """
    用户信息
    """

    __tablename__ = "user"
    role: Mapped[RoleEnum] = mapped_column(comment="角色")
    email: Mapped[str_medium] = mapped_column(comment="邮箱")
    phone: Mapped[str_small] = mapped_column(comment="手机")
    username: Mapped[str_small] = mapped_column(comment="用户名")
    account: Mapped[str_medium] = mapped_column(nullable=False, unique=True, comment="账号")
    password: Mapped[str_small] = mapped_column(comment="密码")
    valid: Mapped[bool] = mapped_column(default=True, comment="是否有效")
