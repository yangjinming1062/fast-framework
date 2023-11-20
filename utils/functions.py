"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : functions.py
Author      : jinming.yang
Description : 基础方法的定义实现
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import base64
import uuid
from functools import wraps
from time import time

from utils import logger


def exceptions(default=None):
    """
    装饰器: 异常捕获。

    Args:
        default (Any, optional): 当发生异常时返回的值。

    Returns:
        Any: 返回结果取决于执行的函数是否发生异常，如果发生异常则返回default的值，没有则返回函数本身的执行结果。
    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as ex:
                logger.exception(ex)
                return default

        return wrapper

    return decorator


def generate_key(*args, need_uuid=False):
    """
    根据输入的参数生成一个12个字符的key。

    Args:
        need_uuid (bool): 是否需要返回uuid格式的key，默认False返回短字符串。

    Returns:
        str | UUID: 生成的Key。
    """
    if args:
        source = '-'.join((str(x) for x in args))
        tmp = uuid.uuid5(uuid.NAMESPACE_DNS, source)
    else:
        tmp = uuid.uuid4()
    return tmp if need_uuid else tmp.hex[-12:]


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


def time_function(func):
    """
    装饰器：记录函数执行时间。

    Args:
        func (callable): 要测量的函数。

    Returns:
        callable
    """

    @wraps(func)
    def decorated(*args, **kwargs):
        start_time = time()
        result = func(*args, **kwargs)
        end_time = time()
        logger.info(f'{func.__name__} 耗时 {(end_time - start_time):.3f}s')
        return result

    return decorated
