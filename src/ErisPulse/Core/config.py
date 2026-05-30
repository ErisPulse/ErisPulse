"""
ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能
添加内存缓存和延迟写入机制以提高性能

{!--< tips >!--}
1. 使用 getConfig(key) / setConfig(key, value) 读写配置
2. 配置变更可通过生命周期钩子监听: @lifecycle.on("config.set")
{!--< /tips >!--}
"""

import os
import time
import toml
import threading
from typing import Any, TypeAlias
from .constants import DEFAULT_CONFIG_FILE_PATH, CONFIG_CACHE_TIMEOUT_SECS, CONFIG_WRITE_DELAY_SECS

ConfigValue: TypeAlias = Any
ConfigKey: TypeAlias = str


class ConfigManager:
    def __init__(self, config_file: str = DEFAULT_CONFIG_FILE_PATH):
        """
        初始化配置管理器

        :param config_file: str 配置文件路径 (默认: "config/config.toml")
        """
        if not os.path.isabs(config_file):
            config_file = os.path.abspath(config_file)
        self.CONFIG_FILE: str = config_file
        self._cache: dict[str, Any] = {}  # 内存缓存
        self._dirty_keys: dict[str, Any] = {}  # 待写入的配置项
        self._cache_timestamp = 0  # 缓存时间戳
        self._cache_timeout = CONFIG_CACHE_TIMEOUT_SECS
        self._write_delay = CONFIG_WRITE_DELAY_SECS
        self._write_timer: threading.Timer | None = None  # 写入定时器
        self._lock = threading.RLock()  # 线程安全锁
        self._file_lock = threading.RLock()  # 文件操作锁
        self._migrate_config()  # 迁移旧配置文件
        self._load_config()  # 初始化时加载配置

    def _migrate_config(self) -> None:
        """
        迁移旧配置文件到新位置

        从项目根目录的 config.toml 迁移到 config/config.toml

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        old_config_path = "config.toml"

        if not os.path.exists(old_config_path):
            return

        if os.path.exists(self.CONFIG_FILE):
            return

        try:
            config_dir = os.path.dirname(self.CONFIG_FILE)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            with open(old_config_path, "r", encoding="utf-8") as f:
                old_config = toml.load(f)

            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                toml.dump(old_config, f)

            readme_content = f"""# 配置文件迁移说明

您的配置文件已从项目根目录迁移到 `config/` 目录。

## 迁移详情

- **旧位置**: `config.toml`
- **新位置**: `config/config.toml`

## 原配置内容

```toml
{toml.dumps(old_config)}
```

## 注意事项

- 新的配置文件位于 `config/config.toml`
- 当您理解本迁移说明后，可删除本文件
- 如需修改配置，请编辑 `config/config.toml`
"""

            with open("config.readme.md", "w", encoding="utf-8") as f:
                f.write(readme_content)

            os.remove(old_config_path)

        except Exception as e:
            try:
                from .logger import logger
                logger.warning(f"配置文件迁移失败: {e}")
            except (ImportError, AttributeError):
                pass

    def _load_config(self) -> None:
        """
        从文件加载配置到缓存

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
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
                try:
                    from .logger import logger
                    logger.error(f"加载配置文件 {self.CONFIG_FILE} 失败: {e}")
                except (ImportError, AttributeError):
                    pass
                self._cache = {}
                self._cache_timestamp = time.time()

    def _sort_config_dict(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """
        递归地对配置字典进行排序

        :param config_dict: dict 待排序的配置字典
        :return: dict 排序后的配置字典

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if not isinstance(config_dict, dict):
            return config_dict

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

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        with self._lock:
            # 如果没有待写入的配置项
            if not self._dirty_keys:
                return

            with self._file_lock:
                try:
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

                    # 对配置进行排序
                    sorted_config = self._sort_config_dict(config)

                    temp_file = self.CONFIG_FILE + ".tmp"
                    with open(temp_file, "w", encoding="utf-8") as f:
                        toml.dump(sorted_config, f)

                    # 原子性重命名
                    if os.name == "nt":
                        if os.path.exists(self.CONFIG_FILE):
                            os.replace(temp_file, self.CONFIG_FILE)
                        else:
                            os.rename(temp_file, self.CONFIG_FILE)
                    else:
                        os.rename(temp_file, self.CONFIG_FILE)

                    # 更新缓存并清除待写入队列
                    self._cache = sorted_config
                    self._cache_timestamp = time.time()
                    self._dirty_keys.clear()

                except Exception as e:
                    try:
                        from .logger import logger
                        logger.error(f"写入配置文件 {self.CONFIG_FILE} 失败: {e}")
                    except (ImportError, AttributeError):
                        pass
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

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
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

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        current_time = time.time()
        if current_time - self._cache_timestamp > self._cache_timeout:
            self._load_config()

    # ==================== 配置读写 ====================

    def getConfig(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        :param key: str 配置键, 支持点分隔符如 "module.sub.key"
        :param default: Any 默认值 (默认: None)
        :return: Any 配置值

        :example:
        >>> value = sdk.config.getConfig("ErisPulse.server.port", 8000)
        """
        with self._lock:
            self._check_cache_validity()

            # 优先检查待写入队列
            if key in self._dirty_keys:
                value = self._dirty_keys[key]
            # 检查缓存
            else:
                keys = key.split(".")
                value = self._cache
                for k in keys:
                    if k not in value:
                        value = default
                        break
                    value = value[k]

        return value

    def setConfig(self, key: str, value: Any, immediate: bool = False) -> bool:
        """
        设置配置项

        :param key: str 配置键, 支持点分隔符如 "module.sub.key"
        :param value: Any 配置值
        :param immediate: bool 是否立即写入磁盘 (默认: False, 延迟写入)
        :return: bool 操作是否成功

        :example:
        >>> sdk.config.setConfig("ErisPulse.server.port", 9000)
        >>> sdk.config.setConfig("ErisPulse.server.port", 9000, immediate=True)
        """
        old_value = self.getConfig(key)

        try:
            with self._lock:
                self._dirty_keys[key] = value

                if immediate:
                    self._flush_config()
                else:
                    self._schedule_write()

            # 触发配置变更钩子
            from .lifecycle import lifecycle

            lifecycle.emit_sync(
                "config.set",
                {
                    "key": key,
                    "old_value": old_value,
                    "new_value": value,
                },
            )

            return True
        except Exception as e:
            try:
                from .logger import logger
                logger.error(f"设置配置项 {key} 失败: {e}")
            except (ImportError, AttributeError):
                pass
            return False

    def force_save(self) -> None:
        """
        强制立即保存所有待写入的配置到磁盘

        {!--< tips >!--}
        注意！除非您知道您在干什么，否则请勿直接强制保存！
        {!--< /tips >!--}
        """
        with self._lock:
            self._flush_config()

    def reload(self) -> None:
        """
        重新从磁盘加载配置，丢弃所有未保存的更改

        {!--< tips >!--}
        reload 时，未持久化的配置项会被丢弃，并重新从配置文件中加载
        {!--< /tips >!--}
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

    :param value: Any 配置值（可以是 bool, int, str 等）
    :return: bool 解析后的布尔值

    {!--< tips >!--}
    支持的值:
    - True: True, 1, "true", "True", "1", "yes", "Yes", "on", "On"
    - False: False, 0, "false", "False", "0", "no", "No", "off", "Off"
    {!--< /tips >!--}
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value != 0

    if isinstance(value, str):
        normalized = value.lower().strip()
        return normalized in ("true", "1", "yes", "on")

    return bool(value)


__all__ = ["config", "ConfigManager", "parse_bool_config"]
