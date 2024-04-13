from datetime import timedelta

from fastapi import Body

from ..common import *

router = get_router(__name__, "鉴权登陆", True)


def _create_token(identity):
    """
    创建JWT Token

    Args:
        identity (Any): jwt有效载荷需要负载的信息

    Returns:

    """
    expire = datetime.utcnow() + timedelta(days=CONFIG.jwt_token_expire_days)
    to_encode = {"uid": identity, "exp": expire}
    return jwt.encode(to_encode, CONFIG.jwt_secret, algorithm=ALGORITHM)


@router.post("/login", summary="登录接口")
async def login(data: LoginRequest = Body()) -> LoginResponse:
    with DatabaseManager() as db:
        if user := db.scalar(select(User).where(User.account == data.account)):
            if data.password == SecretManager.decrypt(user.password):
                return LoginResponse(
                    username=user.username,
                    identify=user.identify,
                    access_token=_create_token(identity=user.id),
                )
        raise APIException(403, APICode.AUTH_FAILED)
