from .base import *
from ..enums import *


class LoginResponse(BaseModel):
    username: str
    role: RoleEnum
    token_type: str
    access_token: str


class UserBase(SchemaBase):
    account: str
    username: str
    role: RoleEnum
    valid: bool
    phone: str
    email: str


class UserCreateRequest(SchemaBase):
    account: str
    username: str
    password: str
    phone: str
    email: str


class UserUpdateRequest(SchemaBase):
    account: str | None
    username: str | None
    phone: str | None
    email: str | None


class UsersRequest(PaginateRequest):
    class UsersRequestQuery:
        keyword: str = Field(title='用户名/账户')

    query: UsersRequestQuery | None


class UsersResponse(PaginateResponse):
    data: List[UserBase]
