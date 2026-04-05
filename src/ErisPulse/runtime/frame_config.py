"""
ErisPulse 框架配置管理模块

提供默认配置定义及配置完整性管理功能
"""

from typing import Dict, Any, Union, Optional

# 默认配置
DEFAULT_ERISPULSE_CONFIG = {
    "server": {              # 服务器配置
        "host": "0.0.0.0",      # 监听地址
        "port": 8000,           # 监听端口
        "ssl_certfile": None,   # SSL 证书文件路径
        "ssl_keyfile": None     # SSL 密钥文件路径
    },
    "logger": {              # 日志配置
        "level": "INFO",        # 日志级别
        "log_files": [],        # 日志文件列表
        "memory_limit": 1000    # 日志内存限制（条）
    },
    "storage":  {            # 存储配置
        "use_global_db": False, # 是否使用全局数据库
    },
    "modules": {},           # 模块配置（可以控制模块启用等）
    "adapters": {},          # 适配器配置（可以控制适配器启用等）
    "event": {               # 事件系统配置
        "message": {            # 消息事件配置
            "ignore_self": True,        # 是否忽略自身消息
                                        #    (会影响命令系统 - 因为命令系统是消息事件子处理器)
        },
        "command": {            # 命令系统配置
            "prefix": "/",              # 命令前缀
            "case_sensitive": True,     # 是否区分大小写
            "allow_space_prefix": False,# 是否允许前缀存在空格
            "must_at_bot": False,       # 是否必须@机器人触发
        },

    },
    "framework": {           # 框架配置
        "enable_lazy_loading": True     # 是否启用延迟加载
    }
}

def _get_config_service():
    from ..Core.config import config as global_config
    return global_config

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
    config_service = _get_config_service()
    
    # 获取现有配置
    current_config = config_service.getConfig("ErisPulse")
    
    # 如果完全没有配置，设置默认配置
    if current_config is None:
        config_service.setConfig("ErisPulse", DEFAULT_ERISPULSE_CONFIG)
        return DEFAULT_ERISPULSE_CONFIG
    
    # 检查并补全缺失的配置项
    complete_config = _ensure_erispulse_config_structure(current_config)
    
    # 如果配置有变化，更新到存储
    if current_config != complete_config:
        config_service.setConfig("ErisPulse", complete_config)
    
    return complete_config


def get_config(section: Optional[str] = None) -> Union[Dict[str, Any], Any]:
    """
    获取 ErisPulse 配置
    
    :param section: 配置部分名称（如 "server"、"logger" 等），None 表示获取完整配置
    :return: 配置字典或配置项
    """
    erispulse_config = get_erispulse_config()
    
    if section is None:
        return erispulse_config
    return erispulse_config.get(section, {})


def update_erispulse_config(new_config: Dict[str, Any]) -> bool:
    """
    更新 ErisPulse 配置，自动补全缺失的配置项
    
    :param new_config: 新的配置字典
    :return: 是否更新成功
    """
    config_service = _get_config_service()
    
    # 获取当前配置并合并新配置
    current = get_erispulse_config()
    merged = {**current, **new_config}
    
    # 确保合并后的配置结构完整
    complete_config = _ensure_erispulse_config_structure(merged)
    
    return config_service.setConfig("ErisPulse", complete_config)


def get_server_config() -> Dict[str, Any]:
    """
    获取服务器配置，确保结构完整
    
    :return: 服务器配置字典
    """
    return get_config("server")


def get_logger_config() -> Dict[str, Any]:
    """
    获取日志配置，确保结构完整
    
    :return: 日志配置字典
    """
    return get_config("logger")


def get_storage_config() -> Dict[str, Any]:
    """
    获取存储模块配置

    :return: 存储配置字典
    """
    return get_config("storage")


def get_event_config() -> Dict[str, Any]:
    """
    获取事件系统配置

    :return: 事件系统配置字典
    """
    return get_config("event")


def get_framework_config() -> Dict[str, Any]:
    """
    获取框架配置

    :return: 框架配置字典
    """
    return get_config("framework")


__all__ = [
    'DEFAULT_ERISPULSE_CONFIG',
    '_ensure_erispulse_config_structure',
    'get_erispulse_config',
    'get_config',
    'update_erispulse_config',
    'get_server_config',
    'get_logger_config',
    'get_storage_config',
    'get_event_config',
    'get_framework_config',
]
