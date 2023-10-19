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
def post_user(params: UserCreateRequest):
    params.password = generate_key(params.password)
    return orm_create(User, params)


@router.patch('/users/{user_id}', status_code=204, summary='编辑用户')
def patch_user(user_id, params: UserUpdateRequest):
    return orm_update(User, user_id, params)


@router.delete('/users', status_code=204, summary='删除用户')
def delete_user(params: List[str] = Query(), db: DatabaseManager = Depends()):
    for uid in params:
        user = db.oltp.get(User, uid)
        if user.role != RoleEnum.Admin:
            user.valid = False
            db.oltp.commit()
