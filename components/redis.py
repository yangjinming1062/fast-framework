import json

from redis import ConnectionPool
from redis import Redis

from .classes import JSONExtensionEncoder
from config import CONFIG


class RedisManager:
    """
    Redis管理器
    PS: 使用get_client方法获取目标数据库的redis客户端
    """

    _REDIS_CONFIG = {
        "host": CONFIG.redis_host,
        "port": CONFIG.redis_port,
        "password": CONFIG.redis_password,
        "decode_responses": True,
        "health_check_interval": 30,
    }
    _CLIENT: Redis

    @classmethod
    def get_object(cls, key, default=None):
        """
        使用给定的键从缓存中检索对象。

        Args:
            key (str): 储值的键。
            default (Any): 没查到数据时返回的值，默认None。

        Returns:
            list | dict | Any: json.loads后的对象或default
        """
        if not getattr(cls, "_CLIENT", None):
            cls._CLIENT = cls.get_client(keepalive=True)
        if value := cls._CLIENT.get(key):
            return json.loads(value)
        else:
            return default

    @classmethod
    def set_object(cls, key, value, ex=None):
        """
        使用指定的键在缓存中设置一个值。

        Args:
            key (str): 储值的键。
            value (dict | list | str): 可json.dumps的数据。
            ex (int | None): 以秒为单位的过期时间。默认为None。
        """
        if not getattr(cls, "_CLIENT", None):
            cls._CLIENT = cls.get_client(keepalive=True)
        if not isinstance(value, str):
            value = json.dumps(value, cls=JSONExtensionEncoder)
        cls._CLIENT.set(key, value, ex)

    @staticmethod
    def get_client(db=0, keepalive=False):
        """
        获取Redis的client。

        Args:
            db (int): redis的数据库序号，默认0。
            keepalive (bool): socket_keepalive，默认False。

        Returns:
            Redis: client实例。
        """
        # 返回指定db的client实例
        return Redis(
            socket_keepalive=keepalive,
            connection_pool=ConnectionPool(db=db, **RedisManager._REDIS_CONFIG),
        )
