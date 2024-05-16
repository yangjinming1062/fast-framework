from .base import *
from ..enums import *


class UserSchema(BaseSchema):
    username: str = ""
    email: str = ""
    phone: str = ""
    avatar: str = ""
    status: UserStatusEnum = UserStatusEnum.ACTIVE


class UpdatePasswordRequest(BaseModel):
    old: str
    new: str
