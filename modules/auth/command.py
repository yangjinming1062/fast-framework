from .enums import UserIdentifyEnum
from .models import User
from common.command import CommandBase
from components import *


class AuthCommand(metaclass=CommandBase):
    name = "auth"

    @staticmethod
    def add_parser(parser):
        parser.add_argument("--username", default="admin", help="管理员账号")
        parser.add_argument("--password", default="", help="管理员密码")

    @staticmethod
    def run(params):
        with DatabaseManager() as db:
            uid = generate_key(params["username"])  # 保证多环境管理员的id一致
            user = db.get(User, uid) or User()
            user.id = uid
            user.username = params["username"]
            password = params["password"] or generate_key(key_len=8)
            logger.info(f"初始密码：{password=}，请及时修改")
            user.password = SecretManager.encrypt(password)
            user.identify = UserIdentifyEnum.ADMIN
            user.phone = "-"
            user.email = "-"
            db.add(user)
