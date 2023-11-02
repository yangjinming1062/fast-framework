"""
Usage:
    command.py user [--account=<admin>] [--username=<username>] [--password=<password>]
    command.py init
    command.py -h | --help
Options:
    --account=<admin>            初始账号 [default: admin]
    --username=<username>        初始用户名 [default: 默认管理员]
    --password=<password>        初始用户密码 [default: m/W*0-nS0t5]
"""
from docopt import docopt

from defines import *
from utils import *


@exceptions()
def init_user(account, username, password):
    """
    添加初始用户。

    Args:
        account (str): 账号。
        username (str): 用户名。
        password (str): 密码。

    Returns:
        None
    """
    with OLTPManager() as db:
        uid = generate_key(account)  # 保证多环境管理员的id一致
        user = db.get(User, uid) or User()
        user.id = uid
        user.account = account
        user.username = username
        user.password = generate_key(password)
        user.role = RoleEnum.Admin
        user.phone = '-'
        user.email = '-'
        user.updated_at = datetime.now()
        db.add(user)
        print('Success!')


def init_database():
    """
    初始化数据库

    Returns:
        None
    """
    pass


if __name__ == '__main__':
    options = docopt(__doc__, version='Command v1.0')
    if options['user']:
        init_user(options['--account'], options['--username'], options['--password'])
    elif options['init']:
        init_database()
    else:
        print('Missed Options')
    print('Success!')
