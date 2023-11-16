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

from configuration import CONFIG
from .classes import JSONExtensionEncoder


class RedisManager:
    """
    Redis管理器
    PS: 使用get_client方法获取目标数据库的redis客户端
    """

    _async_clients = {}
    _clients = {}
    REDIS_CONFIG = {
        'host': CONFIG.redis_host,
        'port': CONFIG.redis_port,
        'password': CONFIG.redis_password,
        'decode_responses': True,
    }

    class RedisClient(Redis):
        """
        封装对象操作的Redis客户端
        """

        def __init__(self, db):
            super().__init__(connection_pool=ConnectionPool(db=db, **RedisManager.REDIS_CONFIG))

        def get_object(self, key, default=None):
            """
            使用给定的键从缓存中检索对象。

            Args:
                key (str): 储值的键。
                default (Any, optional): 没查到数据时返回的值，默认None。

            Returns:
                list | dict | Any: json.loads后的对象或default
            """
            if value := self.get(key):
                return json.loads(value)
            else:
                return default

        def set_object(self, key, value, ex=None):
            """
            使用指定的键在缓存中设置一个值。

            Args:
                key (str): 储值的键。
                value (dict | list): 可json.dumps的数据。
                ex (int, optional): 以秒为单位的过期时间。默认为None。
            """
            if not isinstance(value, str):
                value = json.dumps(value, cls=JSONExtensionEncoder)
            self.set(key, value, ex)

    class AsyncRedisClient(AsyncRedis):
        """
        封装对象操作的AsyncRedis客户端
        """

        def __init__(self, db):
            super().__init__(connection_pool=AsyncConnectionPool(db=db, **RedisManager.REDIS_CONFIG))

        async def get_object(self, key, default=None):
            """
            使用给定的键从缓存中检索对象。

            Args:
                key (str): 储值的键。
                default (Any, optional): 没查到数据时返回的值，默认None。

            Returns:
                list | dict | Any: json.loads后的对象或default
            """
            if value := await self.get(key):
                return json.loads(value)
            else:
                return default

        async def set_object(self, key, value, ex=None):
            """
            使用指定的键在缓存中设置一个值。

            Args:
                key (str): 储值的键。
                value (dict | list): 可json.dumps的数据。
                ex (int, optional): 以秒为单位的过期时间。默认为None。
            """
            if not isinstance(value, str):
                value = json.dumps(value, cls=JSONExtensionEncoder)
            await self.set(key, value, ex)

    @staticmethod
    def get_client(db=0):
        """
        获取Redis的client。

        Args:
            db (int): redis的数据库序号，默认0。

        Returns:
            RedisManager.RedisClient: client实例。
        """
        # 每个数据库复用同一个Client，判断是否存在
        if db not in RedisManager._clients:
            # 添加一个指定db的client实例
            RedisManager._clients[db] = RedisManager.RedisClient(db)

        # 返回指定db的client实例
        return RedisManager._clients[db]

    @staticmethod
    def get_async_client(db=0):
        """
        获取Redis的client。

        Args:
            db (int): redis的数据库序号，默认0。

        Returns:
            RedisManager.AsyncRedisClient: client实例。
        """
        # 每个数据库复用同一个Client，判断是否存在
        if db not in RedisManager._async_clients:
            # 添加一个指定db的client实例
            RedisManager._async_clients[db] = RedisManager.AsyncRedisClient(db)

        # 返回指定db的client实例
        return RedisManager._async_clients[db]
