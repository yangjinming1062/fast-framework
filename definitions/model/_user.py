from .base import *
from ..enums import *


class User(ModelBase, TimeColumns):
    """
    用户信息
    """

    __tablename__ = "user"
    identify: Mapped[UserIdentifyEnum] = mapped_column(comment="角色")
    email: Mapped[str] = mapped_column(comment="邮箱")
    phone: Mapped[str] = mapped_column(comment="手机")
    username: Mapped[str] = mapped_column(comment="用户名")
    password: Mapped[str] = mapped_column(comment="密码")
    status: Mapped[UserStatusEnum] = mapped_column(default=UserStatusEnum.ACTIVE)
