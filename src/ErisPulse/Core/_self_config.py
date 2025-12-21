"""
ErisPulse 框架配置管理

专门管理 ErisPulse 框架自身的配置项。
"""

from typing import Dict, Any
from .config import config

# 默认配置
DEFAULT_ERISPULSE_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "ssl_certfile": None,
        "ssl_keyfile": None
    },
    "logger": {
        "level": "INFO",
        "log_files": [],
        "memory_limit": 1000
    },
    "storage":  {
        "max_snapshot": 20
    },
    "modules": {},
    "adapters": {},
    "framework": {
        "enable_lazy_loading": True
    }
}

def _ensure_erispulse_config_structure(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    确保 ErisPulse 配置结构完整，补全缺失的配置项
    
    :param config_dict: 当前配置
    :return: 补全后的完整配置
    """
    
    # 深度合并配置
    for section, default_values in DEFAULT_ERISPULSE_CONFIG.items():
        if section not in config_dict:
            config_dict[section] = default_values.copy()
            continue
            
        if not isinstance(config_dict[section], dict):
            config_dict[section] = default_values.copy()
            continue
            
        for key, default_value in default_values.items():
            if key not in config_dict[section]:
                config_dict[section][key] = default_value
                
    return config_dict

def get_erispulse_config() -> Dict[str, Any]:
    """
    获取 ErisPulse 框架配置，自动补全缺失的配置项并保存
    
    :return: 完整的 ErisPulse 配置字典
    """
    # 获取现有配置
    current_config = config.getConfig("ErisPulse")
    
    # 如果完全没有配置，设置默认配置
    if current_config is None:
        config.setConfig("ErisPulse", DEFAULT_ERISPULSE_CONFIG)
        return DEFAULT_ERISPULSE_CONFIG
    
    # 检查并补全缺失的配置项
    complete_config = _ensure_erispulse_config_structure(current_config)
    
    # 如果配置有变化，更新到存储
    if current_config != complete_config:
        config.setConfig("ErisPulse", complete_config)
    
    return complete_config

def update_erispulse_config(new_config: Dict[str, Any]) -> bool:
    """
    更新 ErisPulse 配置，自动补全缺失的配置项
    
    :param new_config: 新的配置字典
    :return: 是否更新成功
    """
    # 获取当前配置并合并新配置
    current = get_erispulse_config()
    merged = {**current, **new_config}
    
    # 确保合并后的配置结构完整
    complete_config = _ensure_erispulse_config_structure(merged)
    
    return config.setConfig("ErisPulse", complete_config)

def get_server_config() -> Dict[str, Any]:
    """
    获取服务器配置，确保结构完整
    
    :return: 服务器配置字典
    """
    erispulse_config = get_erispulse_config()
    return erispulse_config["server"]

def get_logger_config() -> Dict[str, Any]:
    """
    获取日志配置，确保结构完整
    
    :return: 日志配置字典
    """
    erispulse_config = get_erispulse_config()
    return erispulse_config["logger"]

def get_storage_config() -> Dict[str, Any]:
    """
    获取存储模块配置

    :return: 存储配置字典
    """
    erispulse_config = get_erispulse_config()
    return erispulse_config["storage"]

def get_framework_config() -> Dict[str, Any]:
    """
    获取框架配置

    :return: 框架配置字典
    """
    erispulse_config = get_erispulse_config()
    return erispulse_config["framework"]