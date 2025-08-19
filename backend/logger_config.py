#!/usr/bin/env python3
"""
统一日志配置模块
避免重复的日志配置，提供项目统一的日志管理
"""

import logging
import os
from datetime import datetime

# 全局日志配置标志
_logging_configured = False

def setup_logging(module_name=None, log_level=logging.INFO):
    """
    设置统一的日志配置
    
    Args:
        module_name: 模块名称，用于创建特定的日志文件
        log_level: 日志级别，默认为INFO
    
    Returns:
        logger: 配置好的logger对象
    """
    global _logging_configured
    
    # 如果已经配置过全局日志，直接返回模块特定的logger
    if _logging_configured:
        return logging.getLogger(module_name or __name__)
    
    # 创建logs目录
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 主日志文件处理器
    main_log_file = os.path.join(logs_dir, 'crypto_system.log')
    file_handler = logging.FileHandler(main_log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 错误日志文件处理器
    error_log_file = os.path.join(logs_dir, 'crypto_errors.log')
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    _logging_configured = True
    
    # 返回模块特定的logger
    logger = logging.getLogger(module_name or __name__)
    logger.info(f"日志系统初始化完成 - 模块: {module_name or 'main'}")
    
    return logger

def get_logger(module_name):
    """
    获取模块特定的logger
    
    Args:
        module_name: 模块名称
    
    Returns:
        logger: logger对象
    """
    if not _logging_configured:
        return setup_logging(module_name)
    
    return logging.getLogger(module_name)

# 便捷函数
def get_crypto_logger(module_name):
    """
    获取加密货币项目专用的logger
    
    Args:
        module_name: 模块名称
    
    Returns:
        logger: 配置好的logger对象
    """
    return get_logger(f"crypto.{module_name}")