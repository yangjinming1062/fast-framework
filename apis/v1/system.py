from sqlalchemy import true

from ..common import *

router = get_router(__name__, '系统管理')


@router.get('/users', response_model=UsersResponse)
def get_users(params: UsersRequest = Depends()):
    """
    用户列表
    """
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
    return paginate_query(sql, params, False)


@router.post('/users', status_code=201)
def post_user(params: UserCreateRequest):
    """
    新建用户
    """
    params = params.model_dump()
    params['password'] = User.generate_hash(params['password'])
    return orm_create(User, params)


@router.patch('/users/{uid}', status_code=204)
def patch_user(uid, params: UserUpdateRequest):
    """
    编辑用户
    """
    return orm_update(User, uid, params.model_dump())


@router.delete('/users', status_code=204)
def delete_user(params: IDSchema, session: SessionManager = Depends()):
    """
    删除用户
    """
    for uid in params.id:
        user = session.oltp.get(User, uid)
        if user.role != RoleEnum.Admin:
            user.valid = False
            user.credential.clear()
            session.oltp.commit()
