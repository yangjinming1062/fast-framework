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

from clickhouse_driver import Client
from confluent_kafka import Consumer
from confluent_kafka import Producer
from redis import ConnectionPool
from redis import Redis
from redis.asyncio import ConnectionPool as AsyncConnectionPool
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import create_engine
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from defines import CONFIG
from defines import DBTypeEnum
from utils import logger
from .constants import Constants

OLTP_ENGINE = create_engine(CONFIG.oltp_uri, pool_size=150, pool_recycle=60)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RedisManager(metaclass=Singleton):
    """
    Redis管理器，使用get_client方法获取目标数据库的redis客户端
    """
    _async_clients = {}
    _clients = {}

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
            redis_config = {
                'host': CONFIG.redis_host,
                'port': CONFIG.redis_port,
                'password': CONFIG.redis_password,
                'decode_responses': True,
            }
            RedisManager._clients[db] = Redis(connection_pool=ConnectionPool(db=db, **redis_config))

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
            redis_config = {
                'host': CONFIG.redis_host,
                'port': CONFIG.redis_port,
                'password': CONFIG.redis_password,
                'decode_responses': True,
            }
            RedisManager._async_clients[db] = AsyncRedis(connection_pool=AsyncConnectionPool(db=db, **redis_config))

        # 返回指定db的client实例
        return RedisManager._async_clients[db]


class KafkaManager(metaclass=Singleton):
    """
    Kafka管理器，简化生成和消费的处理
    """
    _consumers = {}

    def __init__(self):
        self.producer = Producer(CONFIG.kafka_producer_config)

    @staticmethod
    def _get_consumer(*topic) -> Consumer:
        """
        创建一个消费者。

        Args:
            topic: 消费的主题都有哪些。

        Returns:
            Consumer: 消费者实例。
        """
        # 检查指定主题是否已经存在（这里topic其实是一个tuple）
        if topic not in KafkaManager._consumers:
            # 不存在则新建一个消费者
            KafkaManager._consumers[topic] = Consumer(CONFIG.kafka_consumer_config)
            KafkaManager._consumers[topic].subscribe(list(topic))

        # 返回消费者实例
        return KafkaManager._consumers[topic]

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
    def consume(*topic, limit=None, consumer=None, need_load=True):
        """
        消费指定主题的数据。

        Args:
            topic: 需要消费的主题。
            limit (int, optional): 批处理中要使用的消息数。默认值为None，表示使用单个消息。
            consumer (Consumer, optional): 默认为None可以使用config中的配置自动创建一个消费者，也可以指定特定的消费者来消费。
            need_load (bool, optional): 是否返回JSON解码消息, 默认为True会对订阅到的消息进行json.load。

        Returns:
            list: 如果指定了“limit”，则返回JSON解码消息的列表。

        Yields:
            dict | str: 如果“limit”为None，则以生成器的方式每次返回单个JSON解码消息。

        Raises:
            ValueError: 当kafka发生错误时抛出异常。
        """

        def load(msg):
            return json.loads(msg.value().decode('utf-8'))

        consumer = consumer or KafkaManager._get_consumer(topic)
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

    def _produce_data(self, topic, value):
        """
        单次发送指定主题的数据。

        Args:
            topic (str): 主题的名称。
            value (dict | str): 要发送的数据。

        Returns:
            None
        """
        if isinstance(value, dict):
            value = json.dumps(value, cls=JSONExtensionEncoder)
        self.producer.produce(topic=topic, value=value, callback=KafkaManager.delivery_report)

    def produce(self, topic, data):
        """
        生成指定主题的数据。

        Args:
            topic (str): 主题的名称。
            data (dict | list | str): 要发送的数据, 建议批量发送以提高效率。

        Returns:
            None
        """
        if isinstance(data, list):
            index = 1
            for item in data:
                if index >= CONFIG.kafka_producer_queue_size:
                    self.producer.poll(0)
                    index = 1
                self._produce_data(topic, item)
                index += 1
        else:
            self._produce_data(topic, data)
        # 确保交付
        self.producer.poll(0)


class DatabaseManager:
    """
    数据库管理，统一使用该类实例执行数据库操作
    """
    __slots__ = ('session', 'type', 'autocommit', 'inherit')
    session: Session | Client

    def __init__(self, session=None, session_type=DBTypeEnum.OLTP, autocommit=True):
        if session is None:
            self.inherit = False
            self.autocommit = autocommit
            self.type = session_type
            if session_type == DBTypeEnum.OLTP:
                self.session = Session(OLTP_ENGINE)
            elif session_type == DBTypeEnum.OLAP:
                self.session = Client.from_url(CONFIG.olap_uri)
        else:
            self.inherit = True
            self.autocommit = False
            self.session = session
            self.type = self.get_session_type(session)

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
            if self.type == DBTypeEnum.OLTP:
                self.session.rollback()
        self.close()

    def close(self):
        if self.type == DBTypeEnum.OLTP:
            if self.autocommit:
                self.session.commit()
            self.session.close()
        elif self.type == DBTypeEnum.OLAP:
            self.session.disconnect()

    @staticmethod
    def get_session_type(session):
        """
        获取session对象的数据库类型
        Args:
            session (Session | Client):数据库连接

        Returns:
            DBTypeEnum: 数据连接类型
        """
        return DBTypeEnum.OLAP if isinstance(session, Client) else DBTypeEnum.OLTP


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
