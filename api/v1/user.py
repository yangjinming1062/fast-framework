from common.api import *
from modules.user.schemas import *

router = get_router()


@router.put("", status_code=204, summary="编辑用户信息")
def edit_user(request: UserSchema, _user: User = Depends(get_user)):
    with DatabaseManager() as db:
        if user := db.get(User, _user.id):
            user.avatar = request.avatar
            user.username = request.username
            user.email = request.email
            user.phone = request.phone
        else:
            raise APIException(APICode.NOT_FOUND)


@router.post("/password", status_code=204, summary="修改密码")
def edit_password(request: UpdatePasswordRequest, _user: User = Depends(get_user)):
    with DatabaseManager() as db:
        if user := db.get(User, _user.id):
            if request.old == SecretManager.decrypt(user.password):
                user.password = SecretManager.encrypt(request.new)
            else:
                raise APIException(APICode.INVALID_PASSWORD)
        else:
            raise APIException(APICode.NOT_FOUND)
