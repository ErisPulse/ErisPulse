"""
ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能
"""
import os
import toml
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_file: str = "config.toml"):
        self.CONFIG_FILE = config_file

    def getConfig(self, key: str, default: Any = None) -> Any:
        """
        获取模块/适配器配置项
        :param key: 配置项的键(支持点分隔符如"module.sub.key")
        :param default: 默认值
        :return: 配置项的值
        """
        try:
            if not os.path.exists(self.CONFIG_FILE):
                return default
                
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                config = toml.load(f)
            
            # 支持点分隔符访问嵌套配置
            keys = key.split('.')
            value = config
            for k in keys:
                if k not in value:
                    return default
                value = value[k]
                
            return value
        except Exception as e:
            from . import logger
            logger.error(f"读取配置文件 {self.CONFIG_FILE} 失败: {e}")
            return default
    
    def setConfig(self, key: str, value: Any) -> bool:
        """
        设置模块/适配器配置
        :param key: 配置项键名(支持点分隔符如"module.sub.key")
        :param value: 配置项值
        :return: 操作是否成功
        """
        try:
            config = {}
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = toml.load(f)
            
            # 支持点分隔符设置嵌套配置
            keys = key.split('.')
            current = config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
            
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                toml.dump(config, f)
                
            return True
        except Exception as e:
            from . import logger
            logger.error(f"写入配置文件 {self.CONFIG_FILE} 失败: {e}")
            return False

config = ConfigManager()

# 默认配置
DEFAULT_CONFIG = {
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
    }
}

def _ensure_config_structure(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    确保配置结构完整，补全缺失的配置项
    
    :param config: 当前配置
    :return: 补全后的完整配置
    """
    merged_config = DEFAULT_CONFIG.copy()
    
    # 深度合并配置
    for section, default_values in DEFAULT_CONFIG.items():
        if section not in config:
            config[section] = default_values.copy()
            continue
            
        if not isinstance(config[section], dict):
            config[section] = default_values.copy()
            continue
            
        for key, default_value in default_values.items():
            if key not in config[section]:
                config[section][key] = default_value
                
    return config

def get_config() -> Dict[str, Any]:
    """
    获取当前配置，自动补全缺失的配置项并保存
    
    :return: 完整的配置字典
    """

    # 获取现有配置
    current_config = config.getConfig("ErisPulse")
    
    # 如果完全没有配置，设置默认配置
    if current_config is None:
        config.setConfig("ErisPulse", DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    # 检查并补全缺失的配置项
    complete_config = _ensure_config_structure(current_config)
    
    # 如果配置有变化，更新到存储
    if current_config != complete_config:
        config.setConfig("ErisPulse", complete_config)
    
    return complete_config

def update_config(new_config: Dict[str, Any]) -> bool:
    """
    更新配置，自动补全缺失的配置项
    
    :param new_config: 新的配置字典
    :return: 是否更新成功
    """
    # 获取当前配置并合并新配置
    current = get_config()
    merged = {**current, **new_config}
    
    # 确保合并后的配置结构完整
    complete_config = _ensure_config_structure(merged)
    
    return config.setConfig("ErisPulse", complete_config)

def get_server_config() -> Dict[str, Any]:
    """
    获取服务器配置，确保结构完整
    
    :return: 服务器配置字典
    """
    config = get_config()
    return config["server"]

def get_logger_config() -> Dict[str, Any]:
    """
    获取日志配置，确保结构完整
    
    :return: 日志配置字典
    """
    config = get_config()
    return config["logger"]