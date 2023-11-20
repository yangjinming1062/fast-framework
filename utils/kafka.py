"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : kafka.py
Author      : jinming.yang@qingteng.cn
Description : Kafka相关封装
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import json

from confluent_kafka import Consumer
from confluent_kafka import Producer
from confluent_kafka import TopicPartition

from configuration import CONFIG
from utils import logger
from .classes import JSONExtensionEncoder


class KafkaManager:
    """
    Kafka管理器
    """

    PRODUCER = Producer(CONFIG.kafka_producer_config)
    _QUEUE_SIZE = 0
    _QUEUE_LIMIT = CONFIG.kafka_producer_queue_size - 10

    @staticmethod
    def get_consumer(*topic, group_name=None, partition=None):
        """
        创建一个消费者（返回的消费者已完成指定*topic的订阅）。
        PS: 位置参数为需要订阅的topic名称，其他参数请使用关键字指定

        Args:
            topic: 消费的主题。
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
            msg (Message): 发给Kafka的信息。

        Returns:
            None
        """
        # logger.debug(f'Kafka Sent:{msg.value()}')
        if err is not None:
            logger.error('Kafka发生失败', err)

    @staticmethod
    def consume(*topic, consumer=None, limit=None, need_load=True):
        """
        消费指定主题的数据。
        PS: 位置参数为需要订阅的topic名称，其他参数请使用关键字指定

        Args:
            topic: 需要消费的主题。
            consumer (Consumer, optional): 默认为None时会自动创建一个消费者，并在方法结束调用后取消订阅并关闭自动创建的消费者对象。
            limit (int, optional): 批处理中要使用的消息数。默认值为None，表示每次返回单个消息。
            need_load (bool, optional): 是否返回JSON解码消息, 默认为True会对订阅到的消息进行json.load。

        Yields:
            list | dict | str: 如果指定了“limit”，则返回JSON解码消息的列表。

        Raises:
            ValueError: 当kafka发生错误时抛出异常。
        """

        def load(item):
            bytes_message = item.value()
            try:
                str_message = bytes_message.decode('utf-8', 'strict')
            except UnicodeDecodeError:
                str_message = bytes_message.decode('utf-8', 'replace')
            try:
                return json.loads(str_message)
            except Exception:
                logger.error(f'Kafka消费失败，无法解析消息：{str_message}')

        if flag := consumer is None:
            consumer = KafkaManager.get_consumer(*topic)
        try:
            if limit:
                # 批量消费
                while True:
                    if msgs := consumer.consume(num_messages=limit, timeout=CONFIG.kafka_consumer_timeout):
                        offset = msgs[0].offset()
                        partition_id = msgs[0].partition()
                        topic = msgs[0].topic()
                        logger.info(f'{topic=}:{partition_id=}, {offset=}')
                        yield [load(x) for x in msgs if x] if need_load else [x.value() for x in msgs if x]
            else:
                # 持续轮询，返回收到的第一条非空消息
                while True:
                    msg = consumer.poll(1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        raise ValueError(msg.error())
                    yield load(msg) if need_load else msg.value()
        except Exception as ex:
            logger.error(ex)
            # 不是函数内创建的消费者不进行取消订阅以及关闭操作
            if flag:
                consumer.unsubscribe()
                consumer.close()
            raise ex

    @staticmethod
    def produce(topic, data, **kwargs):
        """
        生成指定主题的数据。

        Args:
            topic (str): 主题的名称。
            data (dict | list | str): 要发送的数据, 建议批量发送以提高效率。

        Returns:
            None
        """

        def produce_data(value):
            """
            单次发送指定主题的数据。

            Args:
                value (dict | str): 要发送的数据。

            Returns:
                None
            """
            if isinstance(value, dict):
                value = json.dumps(value, cls=JSONExtensionEncoder)
            KafkaManager.PRODUCER.produce(topic=topic, value=value, callback=KafkaManager.delivery_report, **kwargs)
            KafkaManager._QUEUE_SIZE += 1
            if KafkaManager._QUEUE_SIZE >= KafkaManager._QUEUE_LIMIT:
                KafkaManager.PRODUCER.flush()
                KafkaManager._QUEUE_SIZE = 0

        if isinstance(data, list):
            for item in data:
                produce_data(item)
        else:
            produce_data(data)
            tmp = KafkaManager.PRODUCER.poll(0)
            KafkaManager._QUEUE_SIZE -= tmp
