"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : functions.py
Author      : jinming.yang
Description : 基础方法的定义实现
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""

import base64
import logging
import uuid
from functools import wraps

from component import logger


def exceptions(default=None, log_level=logging.CRITICAL):
    """
    装饰器: 异常捕获。

    Args:
        default (Any | None): 当发生异常时返回的值。
        log_level: 默认CRITICAL

    Returns:
        Any: 返回结果取决于执行的函数是否发生异常，如果发生异常则返回default的值，没有则返回函数本身的执行结果。
    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as ex:
                if log_level == logging.CRITICAL:
                    logger.exception(ex)
                elif log_level == logging.ERROR:
                    logger.error(ex)
                elif log_level == logging.WARNING:
                    logger.warning(ex)
                elif log_level == logging.INFO:
                    logger.info(ex)
                elif log_level == logging.DEBUG:
                    logger.debug(ex)
                return default

        return wrapper

    return decorator


def generate_key(*args, key_len=24, need_uuid=False):
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
