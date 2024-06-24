import re

import pymysql

from .constants import INIT_SQL
from common.command import CommandBase
from config import CONFIG


class DatabaseCommand(metaclass=CommandBase):
    name = "database"

    @classmethod
    def run(cls, _):
        cls.init_db()

    @classmethod
    def init_db(cls):
        if match := re.match(r"doris\+pymysql://(.*?):(.*?)@(.*?):(\d+)/\w+", CONFIG.db_uri):
            connection = pymysql.connect(
                host=match.group(3),
                port=int(match.group(4)),
                user=match.group(1),
                password=match.group(2),
            )
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(INIT_SQL)
            connection.close()
        else:
            print("获取数据库连接信息失败")
