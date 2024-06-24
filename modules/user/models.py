from .enums import *
from common.model import *
from components import generate_key


class User(ModelBase, ModelTimeColumns):
    """
    用户信息
    """

    __tablename__ = "user"

    # 用户id为了防止被轻易猜到不采用数字递增的方式，而是采用随机生成的字符串作为id
    id: Mapped[str] = mapped_column(primary_key=True, default=generate_key)
    identify: Mapped[UserIdentifyEnum]
    email: Mapped[str]
    phone: Mapped[str]
    username: Mapped[str]
    password: Mapped[str]
    status: Mapped[UserStatusEnum] = mapped_column(default=UserStatusEnum.ACTIVE)
