"""
ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能
添加内存缓存和延迟写入机制以提高性能
"""

import os
import time
import toml
import threading
from typing import Any, Dict

class ConfigManager:
    def __init__(self, config_file: str = "config.toml"):
        self.CONFIG_FILE: str = config_file
        self._cache: Dict[str, Any] = {}  # 内存缓存
        self._dirty_keys: Dict[str, Any] = {}  # 待写入的键值对
        self._cache_timestamp = 0  # 缓存时间戳
        self._cache_timeout = 60  # 缓存超时时间（秒）
        self._write_delay = 5  # 写入延迟（秒）
        self._write_timer = None  # 写入定时器
        self._lock = threading.RLock()  # 线程安全锁
        self._load_config()  # 初始化时加载配置

    def _load_config(self) -> None:
        """
        从文件加载配置到缓存
        """
        with self._lock:
            try:
                if not os.path.exists(self.CONFIG_FILE):
                    self._cache = {}
                    self._cache_timestamp = time.time()
                    return

                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = toml.load(f)
                    self._cache = config
                    self._cache_timestamp = time.time()
            except Exception as e:
                from .logger import logger
                logger.error(f"加载配置文件 {self.CONFIG_FILE} 失败: {e}")
                self._cache = {}
                self._cache_timestamp = time.time()

    def _flush_config(self) -> None:
        """
        将待写入的配置刷新到文件
        """
        with self._lock:
            if not self._dirty_keys:
                return  # 没有需要写入的内容

            try:
                # 从文件读取完整配置
                if os.path.exists(self.CONFIG_FILE):
                    with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                        config = toml.load(f)
                else:
                    config = {}

                # 应用待写入的更改
                for key, value in self._dirty_keys.items():
                    keys = key.split('.')
                    current = config
                    for k in keys[:-1]:
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                    current[keys[-1]] = value

                # 写入文件
                with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                    toml.dump(config, f)

                # 更新缓存并清除待写入队列
                self._cache = config
                self._cache_timestamp = time.time()
                self._dirty_keys.clear()

            except Exception as e:
                from .logger import logger
                logger.error(f"写入配置文件 {self.CONFIG_FILE} 失败: {e}")

    def _schedule_write(self) -> None:
        """
        安排延迟写入
        """
        if self._write_timer:
            self._write_timer.cancel()
        
        self._write_timer = threading.Timer(self._write_delay, self._flush_config)
        self._write_timer.daemon = True
        self._write_timer.start()

    def _check_cache_validity(self) -> None:
        """
        检查缓存有效性，必要时重新加载
        """
        current_time = time.time()
        if current_time - self._cache_timestamp > self._cache_timeout:
            self._load_config()

    def getConfig(self, key: str, default: Any = None) -> Any:
        """
        获取模块/适配器配置项（优先从缓存获取）
        :param key: 配置项的键(支持点分隔符如"module.sub.key")
        :param default: 默认值
        :return: 配置项的值
        """
        with self._lock:
            self._check_cache_validity()

            # 优先检查待写入队列
            if key in self._dirty_keys:
                return self._dirty_keys[key]

            # 然后检查缓存
            keys = key.split('.')
            value = self._cache
            for k in keys:
                if k not in value:
                    return default
                value = value[k]

            return value

    def setConfig(self, key: str, value: Any, immediate: bool = False) -> bool:
        """
        设置模块/适配器配置（缓存+延迟写入）
        :param key: 配置项键名(支持点分隔符如"module.sub.key")
        :param value: 配置项值
        :param immediate: 是否立即写入磁盘（默认为False，延迟写入）
        :return: 操作是否成功
        """
        try:
            with self._lock:
                # 先更新待写入队列
                self._dirty_keys[key] = value
                
                if immediate:
                    # 立即写入磁盘
                    self._flush_config()
                else:
                    # 安排延迟写入
                    self._schedule_write()
                
            return True
        except Exception as e:
            from .logger import logger
            logger.error(f"设置配置项 {key} 失败: {e}")
            return False

    def force_save(self) -> None:
        """
        强制立即保存所有待写入的配置到磁盘
        """
        with self._lock:
            self._flush_config()

    def reload(self) -> None:
        """
        重新从磁盘加载配置，丢弃所有未保存的更改
        """
        with self._lock:
            if self._write_timer:
                self._write_timer.cancel()
            self._dirty_keys.clear()
            self._load_config()

config = ConfigManager()

__all__ = [
    "config"
]
