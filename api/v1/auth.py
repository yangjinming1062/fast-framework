from datetime import timedelta

from common.api import *
from modules.auth.models import *
from modules.auth.schemas import *

router = get_router()

REDIS = RedisManager.get_client(keepalive=True)


def _response(user: User):
    expire = datetime.now() + timedelta(days=CONFIG.jwt_token_expire_days)
    to_encode = {"uid": user.id, "exp": expire}
    token = jwt.encode(to_encode, CONFIG.jwt_secret, algorithm=CONSTANTS.JWT_ALGORITHM)
    return LoginResponse(user=UserSchema.model_validate(user), token=token)


@router.post("/register", summary="注册")
async def register(request: RegisterRequest) -> LoginResponse:
    with DatabaseManager() as db:
        sql = select(User).where(
            or_(
                User.username == request.username,
                User.email == request.email,
                User.phone == request.phone,
            )
        )
        if db.scalar(sql):
            raise APIException(APICode.INVALID_USERNAME)
        else:
            user = User(
                id=generate_key(request.username),
                username=request.username,
                password=SecretManager.encrypt(request.password),
                phone=request.phone,
                email=request.email,
            )
            db.add(user)
            db.commit()
            return _response(user)


@router.post("/login", summary="登录")
async def login(request: LoginRequest) -> LoginResponse:
    with DatabaseManager() as db:
        sql = select(User).where(
            or_(
                User.username == request.username,
                User.email == request.username,
                User.phone == request.username,
            )
        )
        if user := db.scalar(sql):
            if request.password == SecretManager.decrypt(user.password):
                return _response(user)
        raise APIException(APICode.INVALID_PASSWORD)


@router.post("/reset-password", summary="重置密码")
async def password(request: ResetPasswordRequest) -> LoginResponse:
    with DatabaseManager() as db:
        sql = select(User).where(
            or_(
                User.username == request.username,
                User.email == request.username,
                User.phone == request.username,
            )
        )
        if user := db.scalar(sql):
            if request.captcha == REDIS.hget("user:captcha", user.id):
                user.password = SecretManager.encrypt(request.password)
                REDIS.hdel("user:captcha", user.id)
                db.commit()
                return _response(user)
            else:
                raise APIException(APICode.INVALID_CAPTCHA)
        raise APIException(APICode.INVALID_PASSWORD)


@router.get("/captcha", summary="获取验证码")
def get_captcha(username: str):
    with DatabaseManager() as db:
        sql = select(User).where(
            or_(
                User.username == username,
                User.email == username,
                User.phone == username,
            )
        )
        if user := db.scalar(sql):
            code = generate_key(key_len=4)
            REDIS.hset("user:captcha", user.id, code)
            # TODO: 发送验证码
        else:
            raise APIException(APICode.NOT_FOUND)


@router.put("/users", status_code=204, summary="编辑用户信息")
def edit_user(request: UserSchema, _user: User = Depends(get_user)):
    with DatabaseManager() as db:
        if user := db.get(User, _user.id):
            user.username = request.username
            user.email = request.email
            user.phone = request.phone
        else:
            raise APIException(APICode.NOT_FOUND)


@router.post("/users/password", status_code=204, summary="修改登录密码")
def edit_password(request: UpdatePasswordRequest, _user: User = Depends(get_user)):
    with DatabaseManager() as db:
        if user := db.get(User, _user.id):
            if request.old == SecretManager.decrypt(user.password):
                user.password = SecretManager.encrypt(request.new)
            else:
                raise APIException(APICode.INVALID_PASSWORD)
        else:
            raise APIException(APICode.NOT_FOUND)
