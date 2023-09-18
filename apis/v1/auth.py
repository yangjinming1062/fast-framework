from datetime import timedelta

from fastapi.security import OAuth2PasswordRequestForm

from ..common import *

router = get_router(__name__, '鉴权登陆')


def _create_token(identity):
    expire = datetime.utcnow() + timedelta(days=CONFIG.jwt_token_expire_days)
    to_encode = {'uid': identity, 'exp': expire}
    return jwt.encode(to_encode, CONFIG.jwt_secret, algorithm=ALGORITHM)


@router.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if user := execute_sql(select(User).where(User.account == form_data.username), fetchall=False):
        if user.check_password(form_data.password):
            return {
                'username': user.username,
                'role': user.role,
                'token_type': 'bearer',
                'access_token': _create_token(identity=user.id),
            }
    raise HTTPException(403, '用户名或密码错误', headers={'WWW-Authenticate': 'Bearer'})
