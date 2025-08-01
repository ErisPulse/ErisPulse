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
