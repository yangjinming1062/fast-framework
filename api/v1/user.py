from ..common import *

router = get_router(__name__, "账户")


@router.put("", status_code=204)
def edit_user(request: UserSchema, _user: User = Depends(get_user)):
    with DatabaseManager() as db:
        if user := db.scalar(select(User).where(User.id == _user.id)):
            user.avatar = request.avatar
            user.username = request.username
            user.email = request.email
            user.phone = request.phone
        else:
            raise HTTPException(404)


@router.post("/password", status_code=204)
def edit_password(request: UpdatePasswordRequest, _user: User = Depends(get_user)):
    with DatabaseManager() as db:
        if user := db.scalar(select(User).where(User.id == _user.id)):
            if request.old == SecretManager.decrypt(user.password):
                user.password = SecretManager.encrypt(request.new)
            else:
                raise HTTPException(403, "密码错误")
        else:
            raise HTTPException(404, "用户不存在")
