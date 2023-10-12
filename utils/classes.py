"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : classes.py
Author      : jinming.yang@qingteng.cn
Description : 工具类定义
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import base64
import json
from ipaddress import IPv4Address

import redis
from clickhouse_driver import Client
from confluent_kafka import Consumer
from confluent_kafka import Producer
from sqlalchemy import create_engine
from sqlalchemy.engine import Row
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from defines import *
from utils import logger
from .constants import Constants

OLTP_ENGINE = create_engine(CONFIG.oltp_uri, pool_size=150, pool_recycle=60)
OLTP_SESSION_FACTORY = scoped_session(sessionmaker(bind=OLTP_ENGINE))


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RedisManager(metaclass=Singleton):
    _clients = {}

    @staticmethod
    def get_client(db=0) -> redis.Redis:
        """
        获取Redis的client。

        Args:
            db (int): redis的数据库序号，默认0。

        Returns:
            redis.Redis: client实例。
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
            RedisManager._clients[db] = redis.Redis(connection_pool=redis.ConnectionPool(db=db, **redis_config))

        # 返回指定db的client实例
        return RedisManager._clients[db]


class KafkaManager(metaclass=Singleton):
    _consumers = {}
    _producers = {}

    @staticmethod
    def get_consumer(*topic) -> Consumer:
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
    def get_producer(topic):
        """
        创建一个生产者。

        Args:
            topic (str): 主题的名称。

        Returns:
            Producer: 生产者实例。
        """
        # 检查给定主题的生产者对象是否已经存在
        if topic not in KafkaManager._producers:
            # 创建一个新的生产者对象
            KafkaManager._producers[topic] = Producer(CONFIG.kafka_producer_config)

        # 返回给定主题的生产者对象
        return KafkaManager._producers[topic]

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
        if err is not None:
            logger.error('Kafka发生失败', err)

    @staticmethod
    def consume(*topic, limit=None):
        """
        消费指定主题的数据。

        Args:
            topic: 需要消费的主题。
            limit (int, optional): 批处理中要使用的消息数。默认值为None，表示使用单个消息。

        Returns:
            list or dict: 如果指定了“limit”，则返回JSON解码消息的列表。如果“limit”为None，则返回单个JSON解码消息。
        """
        consumer = KafkaManager.get_consumer(topic)
        if limit:
            # 批量消费
            msgs = consumer.consume(num_messages=limit, timeout=CONFIG.kafka_consumer_timeout)
            return [json.loads(msg.value().decode('utf-8')) for msg in msgs]
        else:
            # 持续轮询，返回收到的第一条非空消息
            while True:
                msg = consumer.poll(1.0)
                if msg is None or msg.error():
                    continue
                return json.loads(msg.value().decode('utf-8'))

    @staticmethod
    def produce(topic, data):
        """
        生成指定主题的数据。

        Args:
            topic (str): 主题的名称。
            data (dict): 要发送的数据。

        Returns:
            None
        """
        # 获取指定主题的生产者
        producer = KafkaManager.get_producer(topic)
        # 生成主题的数据
        producer.produce(
            topic=topic,
            value=json.dumps(data, cls=JSONExtensionEncoder),
            callback=KafkaManager.delivery_report
        )
        # 确保交付
        producer.poll(0)


class DatabaseManager:
    def __init__(self):
        self.oltp = OLTP_SESSION_FACTORY()
        self.olap = Client.from_url(CONFIG.olap_uri)

    def __enter__(self):
        """
        with的进入方法，返回一个上下文对象。

        Returns:
            数据管理器
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        当离开上下文时关闭数据库连接。

        Args:
            exc_type (type): The type of the exception that occurred, if any.
            exc_value (Exception): The exception object that was raised, if any.
            traceback (traceback): The traceback object that contains information about the exception, if any.
        """
        self.oltp.close()
        self.olap.disconnect()


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
        if isinstance(obj, ModelBase):
            return obj.json()
        if isinstance(obj, IPv4Address):
            return str(obj)
        if isinstance(obj, bytes):
            # 将bytes类型转为base64编码的字符串
            return base64.b64encode(obj).decode('utf-8')
        return json.JSONEncoder.default(self, obj)
