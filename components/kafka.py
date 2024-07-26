import orjson
from confluent_kafka import Consumer
from confluent_kafka import KafkaError
from confluent_kafka import Producer
from confluent_kafka import TopicPartition

from .functions import orjson_dump_extend
from components import logger
from config import CONFIG


class KafkaManager:
    """
    Kafka管理器
    """

    _PRODUCER = Producer(CONFIG.kafka_producer_config)
    _QUEUE_SIZE = 0
    _QUEUE_LIMIT = CONFIG.kafka_producer_queue_size // 2

    @staticmethod
    def get_consumer(*topic, partition=None, config=None):
        """
        创建一个消费者（返回的消费者已完成指定*topic的订阅）。
        PS: 位置参数为需要订阅的topic名称，其他参数请使用关键字指定

        Args:
            topic: 消费的主题。
            partition (int): 指定监听的分区。
            config (dict): 消费者配置，默认使用CONFIG中的默认值。

        Returns:
            Consumer: 消费者实例。
        """
        if not config:
            config = CONFIG.kafka_consumer_config
        else:
            config = CONFIG.kafka_consumer_config.update(config)
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
        logger.debug(f"Kafka Sent:{msg.value()}")
        if err is not None:
            logger.error("Kafka发送失败", err)

    @staticmethod
    def consume(*topic, consumer=None, limit=None, need_load=True, timeout=None):
        """
        消费指定主题的数据。
        PS: 位置参数为需要订阅的topic名称，其他参数请使用关键字指定

        Args:
            topic: 需要消费的主题。
            consumer (Consumer | None): 默认为None时会自动创建一个消费者，并在方法结束调用后取消订阅并关闭自动创建的消费者对象。
            limit (int | None): 批处理中要使用的消息数。默认值为None，表示每次返回单个消息。
            need_load (bool | None): 是否返回JSON解码消息, 默认为True会对订阅到的消息进行json.load。
            timeout (int | None): 超时时长，默认使用CONFIG.kafka_consumer_timeout。

        Yields:
            list | dict | str: 如果指定了“limit”，则返回JSON解码消息的列表。

        Raises:
            ValueError: 当kafka发生错误时抛出异常。
        """

        def load(item):
            try:
                return orjson.loads(item.value())
            except Exception as e:
                logger.error(f"Kafka消费失败，无法解析消息：{item.value()}: {e=}")

        if flag := consumer is None:
            consumer = KafkaManager.get_consumer(*topic)
        try:
            if limit:
                # 批量消费
                while True:
                    if msgs := consumer.consume(num_messages=limit, timeout=timeout or CONFIG.kafka_consumer_timeout):
                        if msgs[0].error():
                            if msgs[0].error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                                logger.warning(f"Kafka消费失败，{topic=}不存在")
                                continue
                            raise ValueError(msgs[0].error())
                        offset = msgs[0].offset()
                        partition_id = msgs[0].partition()
                        topic = msgs[0].topic()
                        logger.debug(f"{topic=}:{partition_id=}, {offset=}")
                        yield [load(x) for x in msgs if x] if need_load else [x.value() for x in msgs if x]
                    else:
                        if timeout is not None:
                            # 指定了超时时间到时间没数据给调用方返回None
                            yield None
                        else:
                            # 没指定超时时长则一直等到有数据
                            continue
            else:
                # 持续轮询，返回收到的第一条非空消息
                while True:
                    if msg := consumer.poll(timeout or 1.0):
                        if msg.error():
                            if msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                                logger.warning(f"Kafka消费失败，{topic=}不存在")
                                continue
                            raise ValueError(msg.error())
                        yield load(msg) if need_load else msg.value()
                    else:
                        if timeout is not None:
                            # 指定了超时时间到时间没数据给调用方返回None
                            yield None
                        else:
                            # 没指定超时时长则一直等到有数据
                            continue
        except Exception as ex:
            logger.error(ex)
            # 不是函数内创建的消费者不进行取消订阅以及关闭操作
            if flag:
                consumer.unsubscribe()
                consumer.close()
            raise ex

    @classmethod
    def produce(cls, topic, data, **kwargs):
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
                value = orjson.dumps(value, default=orjson_dump_extend)
            cls._PRODUCER.produce(
                topic=topic,
                value=value,
                callback=cls.delivery_report,
                **kwargs,
            )
            cls._QUEUE_SIZE += 1
            if cls._QUEUE_SIZE >= cls._QUEUE_LIMIT:
                cls._PRODUCER.flush()
                cls._QUEUE_SIZE = 0

        if isinstance(data, list):
            for item in data:
                produce_data(item)
        else:
            produce_data(data)
            tmp = cls._PRODUCER.poll(0)
            cls._QUEUE_SIZE -= tmp
            logger.debug(f"Kafka 处理的事件数：{tmp}")
