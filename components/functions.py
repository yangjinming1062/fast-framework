import base64
import inspect
import uuid
from functools import wraps

from sqlalchemy import Row

from .logger import logger
from config import CONSTANTS


def exceptions(default=None, log_level=5):
    """
    装饰器，用于捕获函数执行过程中的异常并返回默认值

    Args:
        default (Any | None): 当发生异常时返回的值。
        log_level (int): 默认ERROR, 除了1-5其他取值不进行日志记录。
            EXCEPTION = 5
            ERROR = 4
            WARNING = 3
            INFO = 2
            DEBUG = 1
            NOTSET = 0

    Returns:
        Any: 返回结果取决于执行的函数是否发生异常，如果发生异常则返回default的值，没有则返回函数本身的执行结果。
    """

    def decorator(function):
        @wraps(function)
        async def async_wrapper(*args, **kwargs):
            try:
                return await function(*args, **kwargs)
            except Exception as ex:
                if log_level == 5:
                    logger.exception(ex)
                elif log_level == 4:
                    logger.error(ex)
                elif log_level == 3:
                    logger.warning(ex)
                elif log_level == 2:
                    logger.info(ex)
                elif log_level == 1:
                    logger.debug(ex)
                return default

        @wraps(function)
        def sync_wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as ex:
                if log_level == 5:
                    logger.exception(ex)
                elif log_level == 4:
                    logger.error(ex)
                elif log_level == 3:
                    logger.warning(ex)
                elif log_level == 2:
                    logger.info(ex)
                elif log_level == 1:
                    logger.debug(ex)
                return default

        return async_wrapper if inspect.iscoroutinefunction(function) else sync_wrapper

    return decorator


def generate_key(*args, key_len=CONSTANTS.ID_LENGTH, need_uuid=False):
    """
    根据输入的参数生成一个唯一性标识。

    Args:
        key_len (int): 生成非UUID密钥时的字符个数（最多36个），默认24。
        need_uuid (bool): 是否需要返回uuid格式的key，默认False返回短字符串。

    Returns:
        str | UUID: 生成的Key。
    """
    if args:
        source = "-".join((str(x) for x in args))
        tmp = uuid.uuid5(uuid.NAMESPACE_DNS, source)
    else:
        tmp = uuid.uuid4()
    return tmp if need_uuid else tmp.hex[-key_len:]


def bytes_to_str(value):
    """
    bytes转成str。

    Args:
        value (bytes):

    Returns:
        str
    """
    return base64.b64encode(value).decode()


def str_to_bytes(value):
    """
    str转成bytes。

    Args:
        value (str):

    Returns:
        bytes
    """
    return base64.b64decode(value.encode())


def orjson_dump_extend(value):
    """
    拓展orjson的可序列类型
    """
    if isinstance(value, Row):
        return dict(value._mapping)
    if isinstance(value, bytes):
        # 将bytes类型转为base64编码的字符串
        return value.decode()
