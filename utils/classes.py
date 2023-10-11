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

from config import Configuration
from defines import *
from utils import logger
from .constants import Constants

CONFIG = Configuration()
OLTP_ENGINE = create_engine(CONFIG.oltp_uri, pool_size=150, pool_recycle=60)
OLTP_SESSION_FACTORY = scoped_session(sessionmaker(bind=OLTP_ENGINE))


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RedisManager(metaclass=Singleton):
    _CLIENTS = {}

    @staticmethod
    def get_client(db=0) -> redis.Redis:
        """
        Returns a Redis client for the specified database.

        Args:
            db (int): The database number.

        Returns:
            redis.Redis: The Redis client for the specified database.
        """
        # Check if the client for the specified database already exists
        if db not in RedisManager._CLIENTS:
            # Create a new Redis client and add it to the clients dictionary
            redis_config = {
                'host': CONFIG.redis_host,
                'port': CONFIG.redis_port,
                'password': CONFIG.redis_password,
                'decode_responses': True,
            }
            RedisManager._CLIENTS[db] = redis.Redis(connection_pool=redis.ConnectionPool(db=db, **redis_config))

        # Return the Redis client for the specified database
        return RedisManager._CLIENTS[db]


class KafkaManager(metaclass=Singleton):
    CONSUMERS = {}
    PRODUCERS = {}

    @staticmethod
    def get_consumer(*topic) -> Consumer:
        """
        Get or create a consumer for the specified topic.

        Args:
            topic: The name of the topic.

        Returns:
            The consumer object.
        """
        # Check if consumer already exists for the topic
        if topic not in KafkaManager.CONSUMERS:
            # Create a new consumer for the topic
            KafkaManager.CONSUMERS[topic] = Consumer(CONFIG.kafka_consumer_config)
            KafkaManager.CONSUMERS[topic].subscribe(list(topic))

        # Return the consumer for the topic
        return KafkaManager.CONSUMERS[topic]

    @staticmethod
    def get_producer(topic):
        """
        Get the producer object for the given topic.

        Args:
            topic (str): The name of the topic.

        Returns:
            Producer: The producer object.
        """
        # Check if the producer object for the given topic already exists.
        if topic not in KafkaManager.PRODUCERS:
            # Create a new producer object with the kafka_producer_config.
            KafkaManager.PRODUCERS[topic] = Producer(CONFIG.kafka_producer_config)

        # Return the producer object for the given topic.
        return KafkaManager.PRODUCERS[topic]

    @staticmethod
    def delivery_report(err, msg):
        """
        Callback function to get the status of a message when it is written to Kafka.

        Args:
            err (str): The error message, if any.
            msg (str): The message that was sent to Kafka.

        Returns:
            None

        """
        if err is not None:
            logger.error('Message delivery failed', err)

    @staticmethod
    def consume(topic, limit=None):
        """
        Consume data from a Kafka topic.

        Args:
            topic (str | tuple): The name of the topic to consume data from.
            limit (int, optional): The number of messages to consume in a batch.
                Default is None, which means consume a single message.

        Returns:
            list or dict: If `limit` is specified, returns a list of JSON-decoded messages.
                If `limit` is None, returns a single JSON-decoded message.

        """
        consumer = KafkaManager.get_consumer(topic)
        if limit:
            # Consume a batch of messages with a timeout. Return an empty list if no messages are received.
            msgs = consumer.consume(num_messages=limit, timeout=CONFIG.kafka_consumer_timeout)
            return [json.loads(msg.value().decode('utf-8')) for msg in msgs]
        else:
            # Continuously poll for messages. Return the first non-empty message received.
            while True:
                msg = consumer.poll(1.0)
                if msg is None or msg.error():
                    continue
                return json.loads(msg.value().decode('utf-8'))

    @staticmethod
    def produce(topic, data):
        """
        Produces data to a specified topic.

        Args:
            topic (str): The name of the topic.
            data (dict): The data to be sent.

        Returns:
            None
        """
        # Get the producer for the specified topic
        producer = KafkaManager.get_producer(topic)
        # Produce the data to the topic
        producer.produce(
            topic=topic,
            value=json.dumps(data, cls=JSONExtensionEncoder),
            callback=KafkaManager.delivery_report
        )
        # Poll the producer to ensure delivery
        producer.poll(0)


class DatabaseManager:
    def __init__(self):
        self.oltp = OLTP_SESSION_FACTORY()
        self.olap = Client.from_url(CONFIG.olap_uri)

    def __enter__(self):
        """
        Enter method for context manager.

        Returns:
            The context manager object itself.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Close the connections to the OLTP and OLAP databases when exiting the context.

        Args:
            exc_type (type): The type of the exception that occurred, if any.
            exc_value (Exception): The exception object that was raised, if any.
            traceback (traceback): The traceback object that contains information about the exception, if any.
        """
        self.oltp.close()  # Close the connection to the OLTP database
        self.olap.disconnect()  # Disconnect from the OLAP database


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
