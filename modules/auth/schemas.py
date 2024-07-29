from .enums import *
from common.schema import *


class UserSchema(SchemaBase):
    """
    用户信息
    """

    username: str = ""
    email: str = ""
    phone: str = ""
    status: UserStatusEnum = UserStatusEnum.ACTIVE


class UpdatePasswordRequest(SchemaBase):
    """
    修改密码
    """

    old: str
    new: str


class LoginRequest(SchemaBase):
    """
    登录认证
    """

    username: str = Field(title="账号")
    password: str = Field(title="密码")


class LoginResponse(SchemaBase):
    """
    登录成功响应
    """

    user: UserSchema
    token: str = Field(title="访问令牌")


class RegisterRequest(SchemaBase):
    """
    注册用户
    """

    username: str = Field(title="账号")
    password: str = Field(title="密码")
    phone: str = Field("", title="手机号")
    email: str = Field("", title="邮箱")


class ResetPasswordRequest(SchemaBase):
    """
    重置密码
    """

    username: str = Field(title="账号")
    password: str = Field(title="密码")
    captcha: str = Field(title="验证码")
