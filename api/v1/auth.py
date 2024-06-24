from datetime import timedelta

from common.api import *
from modules.auth.schemas import *

router = get_router()


def _response(user):
    expire = datetime.utcnow() + timedelta(days=CONFIG.jwt_token_expire_days)
    to_encode = {"uid": user.id, "exp": expire}
    token = jwt.encode(to_encode, CONFIG.jwt_secret, algorithm=CONSTANTS.JWT_ALGORITHM)
    return LoginResponse(user=user, token=token)


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


@router.post("/password", summary="重置密码")
async def password(request: PasswordRequest) -> LoginResponse:
    with DatabaseManager() as db:
        sql = select(User).where(
            or_(
                User.username == request.username,
                User.email == request.username,
                User.phone == request.username,
            )
        )
        if user := db.scalar(sql):
            if request.captcha == user.captcha:
                user.password = SecretManager.encrypt(request.password)
                user.captcha = ""
                db.commit()
                return _response(user)
            else:
                raise APIException(APICode.INVALID_CAPTCHA)
        raise APIException(APICode.INVALID_PASSWORD)


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
                username=request.username,
                password=SecretManager.encrypt(request.password),
                phone=request.phone,
                email=request.email,
                status=UserStatusEnum.FORBIDDEN,
            )
            db.add(user)
            db.commit()
            return _response(user)


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
            db.commit()
            # TODO: 发送验证码
        else:
            raise APIException(APICode.NOT_FOUND)
