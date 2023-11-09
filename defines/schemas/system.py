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
    """
    登录请求
    """
    account: str = Field(title='账号')
    password: str = Field(title='密码')


class LoginResponse(BaseModel):
    """
    登录响应
    """
    username: str = Field(title='用户名')
    role: RoleEnum = Field(title='角色')
    token_type: str = Field('bearer', title='token类型')
    access_token: str = Field(title='访问令牌')


class UsersRequest(PaginateRequest):
    """
    用户列表
    """

    class Query(BaseModel):
        keyword: str = Field(title='用户名/账户')

    query: Query | None


class UsersResponse(PaginateResponse):
    """
    用户列表
    """
    data: list[UserBaseSchema]
