from .base import *
from ..enums import *


class UserBaseSchema(BaseSchema):
    account: str
    username: str
    role: RoleEnum
    valid: bool
    phone: str
    email: str


class LoginResponse(BaseModel):
    username: str
    role: RoleEnum
    token_type: str
    access_token: str


class UserCreateRequest(BaseModel):
    account: str
    username: str
    password: str
    phone: str
    email: str


class UserUpdateRequest(BaseModel):
    account: str | None = None
    username: str | None = None
    phone: str | None = None
    email: str | None = None


class UsersRequest(PaginateRequest):
    class UsersRequestQuery:
        keyword: str = Field(title='用户名/账户')

    query: UsersRequestQuery | None


class UsersResponse(PaginateResponse):
    data: List[UserBaseSchema]
