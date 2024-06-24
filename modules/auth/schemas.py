from ..user.schemas import UserSchema
from common.schema import *


class LoginRequest(BaseModel):
    """
    登录认证
    """

    username: str = Field(title="账号")
    password: str = Field(title="密码")


class RegisterRequest(BaseModel):
    """
    注册用户
    """

    username: str = Field(title="账号")
    password: str = Field(title="密码")
    phone: str = Field("", title="手机号")
    email: str = Field("", title="邮箱")


class PasswordRequest(BaseModel):
    """
    重置密码
    """

    username: str = Field(title="账号")
    password: str = Field(title="密码")
    captcha: str = Field(title="验证码")


class CapchaRequest(BaseModel):
    """
    获取验证码
    """

    username: str = Field(title="账号")


class LoginResponse(BaseModel):
    """
    登录成功响应
    """

    user: UserSchema
    token: str = Field(title="访问令牌")
