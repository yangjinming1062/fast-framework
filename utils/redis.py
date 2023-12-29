"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : redis.py
Author      : jinming.yang@qingteng.cn
Description : Redis相关封装
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import json

from redis import ConnectionPool
from redis import Redis
from redis.asyncio import ConnectionPool as AsyncConnectionPool
from redis.asyncio import Redis as AsyncRedis

from configs import CONFIG
from .classes import JSONExtensionEncoder


class RedisManager:
    """
    Redis管理器
    PS: 使用get_client方法获取目标数据库的redis客户端
    """

    _async_clients = {}
    _clients = {}
    REDIS_CONFIG = {
        'host'            : CONFIG.redis_host,
        'port'            : CONFIG.redis_port,
        'password'        : CONFIG.redis_password,
        'decode_responses': True,
    }
    client: Redis

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
        if not cls.client:
            cls.client = cls.get_client()
        if value := cls.client.get(key):
            return json.loads(value)
        else:
            return default

    @classmethod
    def set_object(cls, key, value, ex=None):
        """
        使用指定的键在缓存中设置一个值。

        Args:
            key (str): 储值的键。
            value (dict | list): 可json.dumps的数据。
            ex (int | None): 以秒为单位的过期时间。默认为None。
        """
        if not cls.client:
            cls.client = cls.get_client()
        if not isinstance(value, str):
            value = json.dumps(value, cls=JSONExtensionEncoder)
        cls.client.set(key, value, ex)

    @staticmethod
    def get_client(db=0):
        """
        获取Redis的client。

        Args:
            db (int): redis的数据库序号，默认0。

        Returns:
            Redis: client实例。
        """
        # 每个数据库复用同一个Client，判断是否存在
        if db not in RedisManager._clients:
            # 添加一个指定db的client实例
            RedisManager._clients[db] = Redis(
                connection_pool=ConnectionPool(db=db, **RedisManager.REDIS_CONFIG)
            )

        # 返回指定db的client实例
        return RedisManager._clients[db]

    @staticmethod
    def get_async_client(db=0):
        """
        获取Redis的client。

        Args:
            db (int): redis的数据库序号，默认0。

        Returns:
            AsyncRedis: client实例。
        """
        # 每个数据库复用同一个Client，判断是否存在
        if db not in RedisManager._async_clients:
            # 添加一个指定db的client实例
            RedisManager._async_clients[db] = AsyncRedis(
                connection_pool=AsyncConnectionPool(db=db, **RedisManager.REDIS_CONFIG)
            )

        # 返回指定db的client实例
        return RedisManager._async_clients[db]
