import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

from loguru import logger


def setup_logging(config: Dict[str, Any] = None):
    """设置日志
    
    Args:
        config: 日志配置
    """
    if config is None:
        config = {}
    
    # 移除默认处理器
    logger.remove()
    
    # 获取日志级别
    log_level = config.get("level", "INFO").upper()
    
    # 获取日志格式
    log_format = config.get("format", "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # 获取日志目录
    log_dir = config.get("directory", "./logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 获取日志文件名
    log_file = config.get("file", "qraft_{time}.log")
    log_path = os.path.join(log_dir, log_file)
    
    # 获取日志轮转配置
    rotation = config.get("rotation", "100 MB")
    retention = config.get("retention", "7 days")
    compression = config.get("compression", "zip")
    
    # 添加控制台处理器
    logger.add(
        sys.stderr,
        level=log_level,
        format=log_format,
        colorize=True
    )
    
    # 添加文件处理器
    logger.add(
        log_path,
        level=log_level,
        format=log_format,
        rotation=rotation,
        retention=retention,
        compression=compression
    )
    
    # 添加JSON文件处理器
    json_log_path = os.path.join(log_dir, f"json_{log_file}")
    logger.add(
        json_log_path,
        level=log_level,
        format="{message}",
        rotation=rotation,
        retention=retention,
        compression=compression,
        serialize=True
    )
    
    logger.info("Logging initialized")


class JsonFormatter:
    """JSON格式化器，用于格式化日志为JSON"""
    
    @staticmethod
    def format(record: Dict[str, Any]) -> str:
        """格式化记录为JSON
        
        Args:
            record: 日志记录
            
        Returns:
            JSON字符串
        """
        log_data = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "name": record["name"],
            "function": record["function"],
            "line": record["line"],
            "process": record["process"].id,
            "thread": record["thread"].id
        }
        
        # 添加额外字段
        for key, value in record["extra"].items():
            log_data[key] = value
        
        # 添加异常信息
        if record["exception"]:
            log_data["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback
            }
        
        return json.dumps(log_data)