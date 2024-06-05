from .enums import *
from common.model import *


class User(ModelBase, ModelTimeColumns):
    """
    用户信息
    """

    __tablename__ = "user"
    identify: Mapped[UserIdentifyEnum]
    email: Mapped[str]
    phone: Mapped[str]
    username: Mapped[str]
    password: Mapped[str]
    status: Mapped[UserStatusEnum] = mapped_column(default=UserStatusEnum.ACTIVE)
