from .enums import UserIdentifyEnum
from .models import User
from common.command import CommandBase
from components import *


class UserCommand(metaclass=CommandBase):
    name = "user"

    @staticmethod
    def add_parser(parser):
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

    @staticmethod
    def run(params):
        with DatabaseManager() as db:
            uid = generate_key(params["username"])  # 保证多环境管理员的id一致
            user = db.get(User, uid) or User()
            user.id = uid
            user.username = params["username"]
            user.password = generate_key(params["password"])
            user.identify = UserIdentifyEnum.ADMIN
            user.phone = "-"
            user.email = "-"
            db.add(user)
