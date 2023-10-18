from .base import *
from ..enums import *


class UserBaseSchema(BaseSchema):
    account: str = Field(title='账号')
    username: str = Field(title='用户名')
    role: RoleEnum = Field(title='角色')
    valid: bool = Field(title='是否有效')
    phone: str = Field(title='手机号')
    email: str = Field(title='邮箱')


class LoginRequest(BaseModel):
    account: str = Field(title='账号')
    password: str = Field(title='密码')


class LoginResponse(BaseModel):
    username: str = Field(title='用户名')
    role: RoleEnum = Field(title='角色')
    token_type: str = Field(title='token类型')
    access_token: str = Field(title='访问令牌')


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
    class Query(BaseModel):
        keyword: str = Field(title='用户名/账户')

    query: Query | None


class UsersResponse(PaginateResponse):
    """
    用户列表
    """
    data: List[UserBaseSchema]
