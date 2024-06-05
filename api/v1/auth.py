from datetime import timedelta

from sqlalchemy import or_

from common.api import *
from modules.auth.schemas import *

router = get_router()


def _response(user):
    expire = datetime.utcnow() + timedelta(days=CONFIG.jwt_token_expire_days)
    to_encode = {"uid": user.id, "exp": expire}
    token = jwt.encode(to_encode, CONFIG.jwt_secret, algorithm=CONSTANTS.JWT_ALGORITHM)
    return LoginResponse(user=user, token=token)


@router.post("/login")
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
        raise HTTPException(403, "用户名或密码错误")


@router.post("/password")
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
                raise HTTPException(403, "验证码错误")
        raise HTTPException(403, "用户名或密码错误")


@router.post("/register")
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
            raise HTTPException(403, "用户名已存在")
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


@router.get("/captcha")
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
            raise HTTPException(404, "用户名不存在")
