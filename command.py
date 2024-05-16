import argparse

from components import *
from definitions import *


def init_user(username, password):
    """
    添加初始用户。

    Args:
        username (str): 用户名。
        password (str): 密码。

    Returns:
        None
    """
    with DatabaseManager() as db:
        uid = generate_key(username)  # 保证多环境管理员的id一致
        user = db.get(User, uid) or User()
        user.id = uid
        user.username = username
        user.password = generate_key(password)
        user.identify = UserIdentifyEnum.ADMIN
        user.phone = "-"
        user.email = "-"
        db.add(user)


def init_database():
    """
    初始化数据库

    Returns:
        None
    """
    pass


def main():
    parser = argparse.ArgumentParser(description="Command v1.0")
    # 添加位置参数
    parser.add_argument("command", help="命令")
    # 添加选项参数
    parser.add_argument(
        "--username",
        default="默认管理员",
        help="初始用户名",
    )
    parser.add_argument(
        "--password",
        default="m/W*0-nS0t5",
        help="初始用户密码",
    )

    args = parser.parse_args()

    # 处理命令
    if args.command == "user":
        init_user(args.username, args.password)
    elif args.command == "init":
        init_database()
    else:
        print("Missed Options")
    print("Success!")


if __name__ == "__main__":
    main()
