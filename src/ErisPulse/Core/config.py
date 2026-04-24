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
from typing import Any, TypeAlias

ConfigValue: TypeAlias = Any
ConfigKey: TypeAlias = str


class ConfigManager:
    def __init__(self, config_file: str = "config/config.toml"):
        self.CONFIG_FILE: str = config_file
        self._cache: dict[str, Any] = {}  # 内存缓存
        self._dirty_keys: dict[str, Any] = {}  # 待写入的键值对
        self._cache_timestamp = 0  # 缓存时间戳
        self._cache_timeout = 60  # 缓存超时时间（秒）
        self._write_delay = 5  # 写入延迟（秒）
        self._write_timer: threading.Timer | None = None  # 写入定时器
        self._lock = threading.RLock()  # 线程安全锁
        self._file_lock = threading.RLock()  # 文件操作锁，确保原子性
        self._migrate_config()  # 迁移旧配置文件
        self._load_config()  # 初始化时加载配置

    def _migrate_config(self) -> None:
        """
        迁移旧配置文件到新位置
        从项目根目录的 config.toml 迁移到 config/config.toml
        """
        old_config_path = "config.toml"

        # 检查旧配置文件是否存在
        if not os.path.exists(old_config_path):
            return

        # 检查新位置是否已有配置文件
        if os.path.exists(self.CONFIG_FILE):
            # 新位置已有配置文件，不进行迁移
            return

        try:
            # 确保目标目录存在
            config_dir = os.path.dirname(self.CONFIG_FILE)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            # 读取旧配置文件
            with open(old_config_path, "r", encoding="utf-8") as f:
                old_config = toml.load(f)

            # 写入新配置文件
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                toml.dump(old_config, f)

            # 创建 config.readme.md 文件，包含迁移说明和配置内容
            readme_content = f"""# 配置文件迁移说明

您的配置文件已从项目根目录迁移到 `config/` 目录。

## 迁移详情

- **旧位置**: `config.toml`
- **新位置**: `config/config.toml`

## 原配置内容

``toml
{toml.dumps(old_config)}
```

## 注意事项

- 新的配置文件位于 `config/config.toml`
- 当您理解本迁移说明后，可删除本文件
- 如需修改配置，请编辑 `config/config.toml`
"""

            with open("config.readme.md", "w", encoding="utf-8") as f:
                f.write(readme_content)

            # 删除旧配置文件
            os.remove(old_config_path)

        except Exception as e:
            from .logger import logger

            logger.warning(f"配置文件迁移失败: {e}")

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

    def _sort_config_dict(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """
        递归地对配置字典进行排序，确保同一模块的配置项排列在一起
        :param config_dict: 待排序的配置字典
        :return: 排序后的配置字典
        """
        if not isinstance(config_dict, dict):
            return config_dict

        # 按 key 排序
        sorted_dict = {}
        for key in sorted(config_dict.keys()):
            value = config_dict[key]
            # 递归处理嵌套字典
            if isinstance(value, dict):
                sorted_dict[key] = self._sort_config_dict(value)
            else:
                sorted_dict[key] = value

        return sorted_dict

    def _flush_config(self) -> None:
        """
        将待写入的配置刷新到文件
        
        使用文件锁确保多线程环境下的原子性操作
        """
        with self._lock:
            if not self._dirty_keys:
                return  # 没有需要写入的内容

            with self._file_lock:  # 确保文件操作原子性
                try:
                    # 从文件读取完整配置
                    if os.path.exists(self.CONFIG_FILE):
                        with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                            config = toml.load(f)
                    else:
                        config = {}

                    # 应用待写入的更改
                    for key, value in self._dirty_keys.items():
                        keys = key.split(".")
                        current = config
                        for k in keys[:-1]:
                            if k not in current:
                                current[k] = {}
                            current = current[k]
                        current[keys[-1]] = value

                    # 对配置字典进行排序，确保同一模块的配置项排列在一起
                    sorted_config = self._sort_config_dict(config)

                    # 写入临时文件，确保原子性
                    temp_file = self.CONFIG_FILE + ".tmp"
                    with open(temp_file, "w", encoding="utf-8") as f:
                        toml.dump(sorted_config, f)

                    # 原子性重命名（跨平台兼容）
                    if os.name == 'nt':  # Windows
                        if os.path.exists(self.CONFIG_FILE):
                            os.replace(temp_file, self.CONFIG_FILE)
                        else:
                            os.rename(temp_file, self.CONFIG_FILE)
                    else:  # Unix/Linux/macOS
                        os.rename(temp_file, self.CONFIG_FILE)

                    # 更新缓存并清除待写入队列
                    self._cache = sorted_config
                    self._cache_timestamp = time.time()
                    self._dirty_keys.clear()

                except Exception as e:
                    from .logger import logger

                    logger.error(f"写入配置文件 {self.CONFIG_FILE} 失败: {e}")
                    # 清理临时文件
                    temp_file = self.CONFIG_FILE + ".tmp"
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except Exception:
                            pass

    def _schedule_write(self) -> None:
        """
        安排延迟写入
        
        线程安全：使用锁保护 Timer 的取消和创建
        """
        with self._lock:
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
            keys = key.split(".")
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


config: ConfigManager = ConfigManager()


def parse_bool_config(value: Any) -> bool:
    """
    解析配置中的布尔值

    :param value: 配置值（可以是 bool, int, str 等）
    :return: 解析后的布尔值

    支持的值：
    - True: True, 1, "true", "True", "1", "yes", "Yes", "on", "On"
    - False: False, 0, "false", "False", "0", "no", "No", "off", "Off"
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value != 0

    if isinstance(value, str):
        normalized = value.lower().strip()
        return normalized in ("true", "1", "yes", "on")

    # 其他类型尝试转换为布尔值
    return bool(value)


__all__ = ["config", "parse_bool_config"]
