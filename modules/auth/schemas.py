from ..user.schemas import UserSchema
from common.schema import *


class LoginRequest(BaseModel):
    username: str = Field(title="账号")
    password: str = Field(title="密码")


class RegisterRequest(BaseModel):
    username: str = Field(title="账号")
    password: str = Field(title="密码")
    phone: str = Field("", title="手机号")
    email: str = Field("", title="邮箱")


class PasswordRequest(BaseModel):
    username: str = Field(title="账号")
    password: str = Field(title="密码")
    captcha: str = Field(title="验证码")


class CapchaRequest(BaseModel):
    username: str = Field(title="账号")


class LoginResponse(BaseModel):
    user: UserSchema
    token: str = Field(title="访问令牌")
