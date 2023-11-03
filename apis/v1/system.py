from fastapi import Body
from fastapi import Query
from sqlalchemy import true

from ..common import *

router = get_router(__name__, '系统管理')


@router.get('/users', summary='用户列表')
def get_users(params: UsersRequest) -> UsersResponse:
    sql = (
        select(
            User.id,
            User.account,
            User.role,
            User.username,
            User.phone,
            User.email,
            User.valid,
        )
        .where(User.valid == true())
    )
    if query := params.query:
        if keyword := query.keyword:
            sql = sql.where(User.account.like(f'%{keyword}%') | User.username.like(f'%{keyword}%'))
    return paginate_query(sql, params, UsersResponse)


@router.post('/users', status_code=201, summary='新建用户')
def post_user(
        account: str = Body(),
        username: str = Body(),
        password: str = Body(),
        phone: str = Body(),
        email: str = Body(),
):
    user = User()
    user.account = account
    user.username = username
    user.password = generate_key(password)
    user.phone = phone
    user.email = email
    return orm_create(user, '用户名已存在')


@router.patch('/users/{user_id}', status_code=204, summary='编辑用户')
def patch_user(
        user_id,
        account: str = Body(None),
        username: str = Body(None),
        phone: str = Body(None),
        email: str = Body(None),
):
    params = {
        'account': account,
        'username': username,
        'phone': phone,
        'email': email,
    }
    return orm_update(User, user_id, params, '用户名已存在')


@router.delete('/users', status_code=204, summary='删除用户')
def delete_user(params: list[str] = Query()):
    with OLTPManager() as db:
        for uid in params:
            user = db.get(User, uid)
            if user.role != RoleEnum.Admin:
                user.valid = False
