import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import CONFIG

# 存储已创建的logger实例，避免重复创建
_LOGGER_CACHE = {}
# 缓存锁，避免并发问题
_CACHE_LOCK = threading.Lock()


def get_logger(module: str = None, filename: str = None):
    """
    获取一个配置好的logger实例

    Args:
        module: 模块名称，将作为日志子目录
        filename: 文件名，将作为日志文件名

    Returns:
        一个配置好的logger实例

    示例:
        # 获取模块级别的logger（按级别分为info.log和error.log）
        logger = get_logger(module="core")
        logger.info("这条日志会记录到logs/core/info.log")

        # 获取文件级别的logger（所有级别记录到同一个文件）
        logger = get_logger(module="core", filename="scanner")
        logger.info("这条日志会记录到logs/core/scanner.log")
    """
    # 为新logger生成唯一名称
    logger_name = f"{module}_{filename}" if module and filename else module or filename or "root"

    # 先尝试从缓存获取
    with _CACHE_LOCK:
        if logger_name in _LOGGER_CACHE:
            return _LOGGER_CACHE[logger_name]

    # 创建全新的logger实例
    new_logger = logging.getLogger(logger_name)
    # 不继承父logger的处理器
    new_logger.propagate = False
    # 清除已有处理器
    new_logger.handlers = []
    # 设置默认级别
    new_logger.setLevel(CONFIG.log_level)

    # 确定日志目录
    if module:
        log_dir = Path(CONFIG.log_dir) / module
        log_dir.mkdir(parents=True, exist_ok=True)
    else:
        log_dir = Path(CONFIG.log_dir)
        if not log_dir.exists():
            log_dir.mkdir(parents=True)

    # 创建格式化器
    formatter = logging.Formatter(CONFIG.log_format, datefmt=CONFIG.log_date_format)

    # 如果提供了文件名，使用单一文件模式
    if filename:
        # 使用提供的文件名作为日志文件名
        # 创建轮转文件处理器
        file_handler = RotatingFileHandler(
            str(log_dir / f"{filename}.log"),
            maxBytes=CONFIG.log_max_bytes,
            backupCount=CONFIG.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        new_logger.addHandler(file_handler)
    else:
        # 使用分离文件模式（按照日志级别分开）
        # 配置INFO处理程序
        info_handler = RotatingFileHandler(
            str(log_dir / CONFIG.log_info_name),
            maxBytes=CONFIG.log_max_bytes,
            backupCount=CONFIG.log_backup_count,
            encoding="utf-8",
        )
        info_handler.setFormatter(formatter)
        info_handler.setLevel(CONFIG.log_level)
        # 只处理INFO和DEBUG级别
        info_handler.addFilter(lambda record: record.levelno <= logging.INFO)
        new_logger.addHandler(info_handler)

        # 配置ERROR处理程序
        error_handler = RotatingFileHandler(
            str(log_dir / CONFIG.log_error_name),
            maxBytes=CONFIG.log_max_bytes,
            backupCount=CONFIG.log_backup_count,
            encoding="utf-8",
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.WARNING)
        new_logger.addHandler(error_handler)

    # 如果需要控制台输出
    if CONFIG.log_stdout:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, CONFIG.log_level))
        new_logger.addHandler(console_handler)

    # 缓存logger
    with _CACHE_LOCK:
        _LOGGER_CACHE[logger_name] = new_logger

    return new_logger


# 默认日志记录器，用于utils模块内部
logger = get_logger()
