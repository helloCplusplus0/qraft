import os
import yaml
from typing import Dict, Any, Optional

from loguru import logger


def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config or {}
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}


def load_all_configs(config_dir: str) -> Dict[str, Dict[str, Any]]:
    """加载目录中的所有配置文件
    
    Args:
        config_dir: 配置目录路径
        
    Returns:
        配置字典，键为配置名
    """
    configs = {}
    
    try:
        for filename in os.listdir(config_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                config_path = os.path.join(config_dir, filename)
                config_name = os.path.splitext(filename)[0]
                configs[config_name] = load_config(config_path)
    except Exception as e:
        logger.error(f"Failed to load configs from {config_dir}: {e}")
    
    return configs


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """获取配置值
    
    Args:
        config: 配置字典
        key_path: 键路径，使用点号分隔
        default: 默认值
        
    Returns:
        配置值
    """
    keys = key_path.split(".")
    current = config
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """合并配置
    
    Args:
        base: 基础配置
        override: 覆盖配置
        
    Returns:
        合并后的配置
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result