from .enums import *
from common.schema import *


class UserSchema(SchemaBase):
    """
    用户信息
    """

    username: str = ""
    email: str = ""
    phone: str = ""
    avatar: str = ""
    status: UserStatusEnum = UserStatusEnum.ACTIVE


class UpdatePasswordRequest(BaseModel):
    """
    修改密码
    """

    old: str
    new: str
