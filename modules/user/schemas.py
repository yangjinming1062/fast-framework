from .enums import *
from common.schema import *


class UserSchema(SchemaBase):
    username: str = ""
    email: str = ""
    phone: str = ""
    avatar: str = ""
    status: UserStatusEnum = UserStatusEnum.ACTIVE


class UpdatePasswordRequest(BaseModel):
    old: str
    new: str
