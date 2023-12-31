from datetime import timedelta

from fastapi import Body

from ..common import *

router = get_router(__name__, '鉴权登陆')


def _create_token(identity):
    expire = datetime.utcnow() + timedelta(days=CONFIG.jwt_token_expire_days)
    to_encode = {'uid': identity, 'exp': expire}
    return jwt.encode(to_encode, CONFIG.jwt_secret, algorithm=ALGORITHM)


@router.post('/login')
async def login(data: LoginRequest = Body()) -> LoginResponse:
    with DatabaseManager(SessionTypeEnum.PG) as db:
        if user := db.scalar(select(User).where(User.account == data.account)):
            if generate_key(data.password) == user.password:
                return LoginResponse(
                    username=user.username,
                    role=user.role,
                    access_token=_create_token(identity=user.id),
                )
        raise HTTPException(403, '用户名或密码错误', headers={'WWW-Authenticate': 'Bearer'})
