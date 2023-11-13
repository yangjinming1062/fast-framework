"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : classes.py
Author      : jinming.yang@qingteng.cn
Description : 工具类定义
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import base64
import json
from datetime import datetime
from enum import Enum
from ipaddress import IPv4Address
from ipaddress import IPv6Address

from confluent_kafka import Consumer
from confluent_kafka import Producer
from confluent_kafka import TopicPartition
from redis import ConnectionPool
from redis import Redis
from redis.asyncio import ConnectionPool as AsyncConnectionPool
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import create_engine
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session

from config import CONFIG
from utils import logger
from .constants import Constants

DB_ENGINE_CH = create_engine(CONFIG.clickhouse_uri, pool_size=150, pool_recycle=60)
DB_ENGINE_CH_ASYNC = create_async_engine(CONFIG.clickhouse_async_uri, pool_size=150, pool_recycle=60)
DB_ENGINE_PG = create_engine(CONFIG.postgres_uri, pool_size=150, pool_recycle=60)
DB_ENGINE_PG_ASYNC = create_async_engine(CONFIG.postgres_async_uri, pool_size=150, pool_recycle=60)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RedisManager:
    """
    Redis管理器，使用get_client方法获取目标数据库的redis客户端
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

        def delete_all(self):
            for key in self.keys():
                self.delete(key)

        def get_object(self, key, default=None):
            if value := self.get(key):
                return json.loads(value)
            else:
                return default

        def set_object(self, key, value, ex=None):
            if not isinstance(value, str):
                value = json.dumps(value)
            self.set(key, value, ex)

    class AsyncRedisClient(AsyncRedis):
        """
        封装对象操作的AsyncRedis客户端
        """

        def __init__(self, db):
            super().__init__(connection_pool=AsyncConnectionPool(db=db, **RedisManager.REDIS_CONFIG))

        async def delete_all(self):
            async for key in self.keys():
                await self.delete(key)

        async def get_object(self, key, default=None):
            if value := await self.get(key):
                return json.loads(value)
            else:
                return default

        async def set_object(self, key, value, ex=None):
            if not isinstance(value, str):
                value = json.dumps(value)
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


class KafkaManager:
    """
    Kafka管理器，简化生成和消费的处理
    """

    PRODUCER = Producer(CONFIG.kafka_producer_config)

    @staticmethod
    def get_consumer(*topic, group_name=None, partition=None):
        """
        创建一个消费者。

        Args:
            topic: 消费的主题都有哪些。
            group_name (str): 组名称，默认None时使用CONFIG中的默认值。
            partition (int): 指定监听的分区。

        Returns:
            Consumer: 消费者实例。
        """
        config = CONFIG.kafka_consumer_config
        if group_name:
            config['group.id'] = group_name
        consumer = Consumer(config)
        if partition is not None:
            consumer.assign([TopicPartition(t, partition) for t in topic])
        consumer.subscribe(list(topic))
        return consumer

    @staticmethod
    def delivery_report(err, msg):
        """
        回调函数，用于获取消息写入Kafka时的状态。

        Args:
            err (str): 错误消息（如果有）。
            msg (str): 发给Kafka的信息。

        Returns:
            None
        """
        logger.debug(f'Kafka Sent:{msg}')
        if err is not None:
            logger.error('Kafka发生失败', err)

    @staticmethod
    def consume(*topic, consumer=None, limit=None, need_load=True):
        """
        消费指定主题的数据。

        Args:
            topic: 需要消费的主题。
            consumer (Consumer, optional): 默认为None时会自动创建一个消费者，并在方法结束调用后取消订阅并关闭自动创建的消费者对象。
            limit (int, optional): 批处理中要使用的消息数。默认值为None，表示每次返回单个消息。
            need_load (bool, optional): 是否返回JSON解码消息, 默认为True会对订阅到的消息进行json.load。

        Returns:
            list | dict: 如果指定了“limit”，则返回JSON解码消息的列表。

        Yields:
            dict | str: 如果“limit”为None，则以生成器的方式每次返回单个JSON解码消息。

        Raises:
            ValueError: 当kafka发生错误时抛出异常。
        """

        def load(msg):
            return json.loads(msg.value().decode('utf-8'))

        if flag := consumer is None:
            consumer = KafkaManager.get_consumer(*topic)
        try:
            if limit:
                # 批量消费
                msgs = consumer.consume(num_messages=limit, timeout=CONFIG.kafka_consumer_timeout)
                return [load(msg) for msg in msgs] if need_load else [msg.value() for msg in msgs]
            else:
                # 持续轮询，返回收到的第一条非空消息
                while True:
                    msg = consumer.poll(1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        raise ValueError(msg.error())
                    yield load(msg) if need_load else msg.value()
        finally:
            # 不是函数内创建的消费者不进行取消订阅以及关闭操作
            if flag:
                consumer.unsubscribe()
                consumer.close()

    @staticmethod
    async def produce(topic, data):
        """
        生成指定主题的数据。

        Args:
            topic (str): 主题的名称。
            data (dict | list | str): 要发送的数据, 建议批量发送以提高效率。

        Returns:
            None
        """

        async def produce_data(value):
            """
            单次发送指定主题的数据。

            Args:
                value (dict | str): 要发送的数据。

            Returns:
                None
            """
            if isinstance(value, dict):
                value = json.dumps(value, cls=JSONExtensionEncoder)
            KafkaManager.PRODUCER.produce(topic=topic, value=value, callback=KafkaManager.delivery_report)

        if isinstance(data, list):
            index = 1
            for item in data:
                if index >= CONFIG.kafka_producer_queue_size:
                    KafkaManager.PRODUCER.poll(0)
                    index = 1
                await produce_data(item)
                index += 1
        else:
            await produce_data(data)
        # 确保交付
        KafkaManager.PRODUCER.poll(0)


class DatabaseManager:
    """
    数据库管理: 统一实现Postgres和ClickHouse的连接创建、关闭、提交回滚等逻辑
    """
    __slots__ = ('session', 'autocommit')
    session: Session | AsyncSession

    def __init__(self, db_engine, session=None):
        """

        Args:
            db_engine (Engine): DB_ENGINE_PG 或 DB_ENGINE_CH。
            session (Session | None): 默认None，如果传递了非None的数据库链接则复用该链接
        """
        if session is None:
            self.autocommit = True
            if db_engine in (DB_ENGINE_PG, DB_ENGINE_CH):
                self.session = Session(db_engine)
            else:
                self.session = AsyncSession(db_engine)
        else:
            self.autocommit = False
            self.session = session

    def __enter__(self):
        """
        with的进入方法，返回一个上下文对象。

        Returns:
            数据管理器
        """
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        """
        当离开上下文时关闭数据库连接。

        Args:
            exc_type (type): The type of the exception that occurred, if any.
            exc_value (Exception): The exception object that was raised, if any.
            traceback (traceback): The traceback object that contains information about the exception, if any.
        """
        if exc_value:
            self.session.rollback()
        if self.autocommit:
            self.session.commit()
        self.session.close()

    async def __aenter__(self):
        """
        async with的进入方法，返回一个上下文对象。

        Returns:
            数据管理器
        """
        return self.session

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        当离开上下文时关闭数据库连接。

        Args:
            exc_type (type): The type of the exception that occurred, if any.
            exc_value (Exception): The exception object that was raised, if any.
            traceback (traceback): The traceback object that contains information about the exception, if any.
        """
        if exc_value:
            await self.session.rollback()
        if self.autocommit:
            await self.session.commit()
        await self.session.close()


class JSONExtensionEncoder(json.JSONEncoder):
    """
    处理枚举等各种无法JSON序列化的类型
    """

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.name
        if isinstance(obj, datetime):
            return obj.strftime(Constants.DEFINE_DATE_FORMAT)
        if isinstance(obj, Row):
            return dict(obj._mapping)
        if isinstance(obj, (IPv4Address, IPv6Address)):
            return str(obj)
        if isinstance(obj, bytes):
            # 将bytes类型转为base64编码的字符串
            return base64.b64encode(obj).decode('utf-8')
        return json.JSONEncoder.default(self, obj)
