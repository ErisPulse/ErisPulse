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

import atexit
import os
import threading
import time
from pathlib import Path
from typing import Any, TypeAlias

import toml

from .constants import (
    CONFIG_CACHE_TIMEOUT_SECS,
    CONFIG_WRITE_DELAY_SECS,
    DEFAULT_CONFIG_FILE_PATH,
)
from .i18n import i18n

ConfigValue: TypeAlias = Any
ConfigKey: TypeAlias = str


class ConfigManager:
    def __init__(self, config_file: str = DEFAULT_CONFIG_FILE_PATH):
        """
        初始化配置管理器

        :param config_file: str 配置文件路径 (默认: "config/config.toml")
        """
        if not Path(config_file).is_absolute():
            config_file = str(Path(config_file).resolve())
        self.CONFIG_FILE: str = config_file
        self._cache: dict[str, Any] = {}  # 内存缓存
        self._dirty_keys: dict[str, Any] = {}  # 待写入的配置项
        self._cache_timestamp = 0  # 缓存时间戳
        self._cache_timeout = CONFIG_CACHE_TIMEOUT_SECS
        self._write_delay = CONFIG_WRITE_DELAY_SECS
        self._write_timer: threading.Timer | None = None  # 写入定时器
        self._lock = threading.RLock()  # 线程安全锁
        self._file_lock = threading.RLock()  # 文件操作锁
        self._atexit_registered = False  # atexit 钩子注册标记
        self._migrate_config()  # 迁移旧配置文件
        self._load_config()  # 初始化时加载配置
        self._watch_config_file()  # 记录配置文件 mtime 以便后续监听
        self._start_config_watcher()  # 启动后台文件变化监听
        self._register_atexit()

    _CONFIG_WATCH_INTERVAL: float = 5.0  # 配置文件监听轮询间隔（秒）
    _MALFORMED_WARN_COOLDOWN: float = 30.0  # flush 阶段语法错误告警冷却（秒）

    def _start_config_watcher(self) -> None:
        """
        启动后台线程定期检查配置文件变化

        当用户手动编辑 ``config.toml`` 时，后台线程检测到 mtime 变化后
        自动重载缓存并发射 ``config.updated`` 生命周期事件。

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        self._watcher_stop = threading.Event()

        def _watch_loop():
            while not self._watcher_stop.is_set():
                self._watcher_stop.wait(timeout=self._CONFIG_WATCH_INTERVAL)
                if self._watcher_stop.is_set():
                    break
                try:
                    if self._check_file_change():
                        # 文件被外部修改 → 取消待写入定时器并丢弃脏键，
                        # 避免 _flush_config 回写旧值覆盖用户编辑。
                        if self._write_timer:
                            self._write_timer.cancel()
                            self._write_timer = None
                        self._dirty_keys.clear()
                        with self._lock:
                            old_cache = self._cache.copy() if self._cache else {}
                        self._load_config()
                        self._emit_config_updated(old_cache)
                except Exception:
                    pass

        watcher = threading.Thread(target=_watch_loop, daemon=True, name="config-watcher")
        watcher.start()

    def _watch_config_file(self) -> None:
        """
        记录配置文件的当前 mtime，用于后续检测外部修改

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        self._config_mtime: float = 0
        try:
            config_path = Path(self.CONFIG_FILE)
            if config_path.exists():
                self._config_mtime = config_path.stat().st_mtime
        except OSError:
            pass

    def _migrate_config(self) -> None:
        """
        迁移旧配置文件到新位置

        从项目根目录的 config.toml 迁移到 config/config.toml

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        old_config_path = "config.toml"

        if not Path(old_config_path).exists():
            return

        if Path(self.CONFIG_FILE).exists():
            return

        try:
            config_dir = Path(self.CONFIG_FILE).parent
            if str(config_dir) and not config_dir.exists():
                config_dir.mkdir(parents=True, exist_ok=True)

            with Path(old_config_path).open(encoding="utf-8") as f:
                old_config = toml.load(f)

            with Path(self.CONFIG_FILE).open("w", encoding="utf-8") as f:
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

            with Path("config.readme.md").open("w", encoding="utf-8") as f:
                f.write(readme_content)

            Path(old_config_path).unlink()

        except Exception as e:
            try:
                from .logger import logger

                logger.warning(i18n.t("core.config.migrate_failed", error=e))
            except (ImportError, AttributeError):
                pass

    def _load_config(self) -> None:
        """
        从文件加载配置到缓存

        对加载失败按三种状态分别给出可操作的诊断信息：

        - 文件缺失：正常首次启动，静默使用空配置
        - TOML 语法错误：输出出错行号/列号与原因，并提示已回退默认配置
        - 权限/其他错误：输出明确原因，并提示已回退默认配置

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        with self._lock:
            path = Path(self.CONFIG_FILE)
            if not path.exists():
                self._cache = {}
                self._cache_timestamp = time.time()
                return

            try:
                with path.open(encoding="utf-8") as f:
                    config = toml.load(f)
            except toml.TomlDecodeError as e:
                # 态1：TOML 语法错误——给出行号/列号与原因，便于用户精确定位
                self._cache = {}
                self._cache_timestamp = time.time()
                self._log_config_error(
                    i18n.t(
                        "core.config.toml_malformed",
                        path=self.CONFIG_FILE,
                        line=getattr(e, "lineno", "?"),
                        col=getattr(e, "colno", "?"),
                        reason=getattr(e, "msg", str(e)),
                    )
                )
                self._log_config_error(
                    i18n.t("core.config.using_defaults_warning"),
                    level="warning",
                )
            except PermissionError:
                # 态2：权限问题——明确告知，避免误以为是配置内容问题
                self._cache = {}
                self._cache_timestamp = time.time()
                self._log_config_error(
                    i18n.t("core.config.permission_denied", path=self.CONFIG_FILE),
                )
                self._log_config_error(
                    i18n.t("core.config.using_defaults_warning"),
                    level="warning",
                )
            except Exception as e:
                # 态3：其他未知错误——保留原有通用提示
                self._cache = {}
                self._cache_timestamp = time.time()
                self._log_config_error(
                    i18n.t(
                        "core.config.load_failed", path=self.CONFIG_FILE, error=e
                    )
                )
                self._log_config_error(
                    i18n.t("core.config.using_defaults_warning"),
                    level="warning",
                )
            else:
                self._cache = config
                self._cache_timestamp = time.time()
                if not self._cache:
                    self._log_config_error(
                        i18n.t("core.config.loaded_empty", path=self.CONFIG_FILE),
                        level="debug",
                    )

    @staticmethod
    def _log_config_error(message: str, level: str = "error") -> None:
        """
        将配置加载诊断信息写入日志

        {!--< internal-use >!--}
        统一处理 logger 尚未就绪的早期场景，失败时静默忽略。
        {!--< /internal-use >!--}

        :param message: str 日志消息
        :param level: str 日志级别（``error``/``warning``/``debug``）
        """
        try:
            from .logger import logger

            getattr(logger, level, logger.error)(message)
        except (ImportError, AttributeError):
            pass

    @staticmethod
    def _sort_config_dict(config_dict: dict[str, Any]) -> dict[str, Any]:
        """
        递归地对配置字典按键排序

        :param config_dict: dict 待排序的配置字典
        :return: dict 排序后的配置字典

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        return {
            k: ConfigManager._sort_config_dict(v) if isinstance(v, dict) else v
            for k, v in sorted(config_dict.items())
        }

    @property
    def _malformed_sentinel_path(self) -> Path:
        """
        跨进程告警冷却哨兵文件路径

        位于配置文件同级目录下的隐藏文件，通过其 mtime 实现跨进程去重：
        无论 ``epsdk run`` 子进程、``python main.py`` 直跑、还是多实例场景，
        所有进程共享同一文件系统，自然协调告警频率。

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        return Path(self.CONFIG_FILE).parent / ".flush_malformed_cooldown"

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
                    if Path(self.CONFIG_FILE).exists():
                        with Path(self.CONFIG_FILE).open(encoding="utf-8") as f:
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
                    with Path(temp_file).open("w", encoding="utf-8") as f:
                        toml.dump(sorted_config, f)

                    # 原子性重命名
                    if os.name == "nt":
                        if Path(self.CONFIG_FILE).exists():
                            Path(temp_file).replace(self.CONFIG_FILE)
                        else:
                            Path(temp_file).rename(self.CONFIG_FILE)
                    else:
                        Path(temp_file).rename(self.CONFIG_FILE)

                    # 更新缓存并清除待写入队列
                    self._cache = sorted_config
                    self._cache_timestamp = time.time()
                    self._dirty_keys.clear()
                    # 写入成功 → 清除告警冷却标记，下次再损坏可立即告警
                    sentinel = self._malformed_sentinel_path
                    try:
                        if sentinel.exists():
                            sentinel.unlink()
                    except Exception:
                        pass

                    # 同步记录的 mtime，避免文件监听任务把框架自身的写入误判为外部修改，
                    # 从而重复触发 config.updated（与 config.set 路由重复调用 on_config_update）
                    try:
                        self._config_mtime = Path(self.CONFIG_FILE).stat().st_mtime
                    except OSError:
                        pass

                except toml.TomlDecodeError as e:
                    # 配置文件已损坏（语法错误）→ 无法安全地读取-合并-写入。
                    # 不清空 _dirty_keys，待用户修复文件后下次 flush 再写入。
                    # 去重：使用配置目录下的哨兵文件 mtime 做冷却。
                    # 这是跨进程的——无论 epsdk run 子进程、python main.py 直跑、
                    # 还是多实例场景，所有进程共享同一文件系统，自然协调。
                    should_warn = True
                    sentinel = self._malformed_sentinel_path
                    try:
                        if sentinel.exists():
                            if time.time() - sentinel.stat().st_mtime <= self._MALFORMED_WARN_COOLDOWN:
                                should_warn = False
                    except Exception:
                        pass

                    if should_warn:
                        try:
                            sentinel.touch()
                        except Exception:
                            pass
                        try:
                            from .logger import logger

                            logger.error(
                                i18n.t(
                                    "core.config.flush_malformed",
                                    path=self.CONFIG_FILE,
                                    line=getattr(e, "lineno", "?"),
                                    col=getattr(e, "colno", "?"),
                                    reason=getattr(e, "msg", str(e)),
                                )
                            )
                        except (ImportError, AttributeError):
                            pass
                    # 清理临时文件
                    temp_file = self.CONFIG_FILE + ".tmp"
                    if Path(temp_file).exists():
                        try:
                            Path(temp_file).unlink()
                        except Exception:
                            pass
                except Exception as e:
                    try:
                        from .logger import logger

                        logger.error(
                            i18n.t(
                                "core.config.write_failed",
                                path=self.CONFIG_FILE,
                                error=e,
                            )
                        )
                    except (ImportError, AttributeError):
                        pass
                    # 清理临时文件
                    temp_file = self.CONFIG_FILE + ".tmp"
                    if Path(temp_file).exists():
                        try:
                            Path(temp_file).unlink()
                        except Exception:
                            pass

    def _register_atexit(self) -> None:
        """
        注册 atexit 钩子，确保进程退出时未持久化的配置被 flush

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if not self._atexit_registered:
            atexit.register(self._flush_on_exit)
            self._atexit_registered = True

    def _flush_on_exit(self) -> None:
        """
        atexit 回调：进程退出时强制刷新所有脏配置，并清理哨兵文件

        {!--< internal-use >!--}
        哨兵文件（``.flush_malformed_cooldown``）是运行时跨进程去重的临时标记，
        {!--< /internal-use >!--}
        """
        try:
            if self._write_timer:
                self._write_timer.cancel()
            self._flush_config()
        except Exception:
            pass
        # 清理哨兵文件（无论 flush 成功与否）
        try:
            sentinel = self._malformed_sentinel_path
            if sentinel.exists():
                sentinel.unlink()
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

        同时检测配置文件是否被外部修改（手动编辑磁盘文件），
        若文件 mtime 变化则自动重载。更新内容会在下一次
        ``getConfig`` 调用时生效，无需重启程序。

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        current_time = time.time()
        if current_time - self._cache_timestamp > self._cache_timeout:
            if self._check_file_change():
                # 文件被外部修改，重载配置
                old_cache = self._cache.copy() if self._cache else {}
                self._load_config()
                self._emit_config_updated(old_cache)
            else:
                self._load_config()

    def _check_file_change(self) -> bool:
        """
        检测配置文件是否被外部程序或用户手动编辑

        对比记录的 mtime 与当前文件 mtime，若不一致说明文件已被外部修改。

        :return: bool 文件是否已变化

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        try:
            config_path = Path(self.CONFIG_FILE)
            if not config_path.exists():
                return False
            current_mtime = config_path.stat().st_mtime
            if current_mtime != self._config_mtime:
                self._config_mtime = current_mtime
                return True
        except OSError:
            pass
        return False

    def _emit_config_updated(self, old_config: dict[str, Any]) -> None:
        """
        发射 ``config.updated`` 生命周期事件，通知适配器/模块配置已变更

        用户手动编辑 ``config.toml`` 后，下一次 ``getConfig`` 调用会自动检测
        到文件变更并触发此事件。适配器通过 ``on_config_update(old, new)`` 响应。

        :param old_config: 变更前的配置快照

        {!--< internal-use >!--}
        """
        try:
            from .lifecycle import lifecycle

            lifecycle.emit_sync("config.updated", {
                "old_config": old_config,
                "new_config": self._cache,
                "config_file": self.CONFIG_FILE,
            })
        except Exception:
            pass

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
            from .logger import logger

            logger.trace(f"config.setConfig: key={key}")
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

                logger.error(i18n.t("core.config.set_failed", key=key, error=e))
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

    # ==================== 异步接口（通过线程池桥接） ====================

    async def agetConfig(self, key: str, default: Any = None) -> Any:
        """
        异步获取配置项

        :param key: str 配置键, 支持点分隔符
        :param default: Any 默认值
        :return: Any 配置值
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.getConfig, key, default)

    async def asetConfig(self, key: str, value: Any, immediate: bool = False) -> bool:
        """
        异步设置配置项

        :param key: str 配置键
        :param value: Any 配置值
        :param immediate: bool 是否立即写入磁盘
        :return: bool 操作是否成功
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.setConfig(key, value, immediate)
        )

    async def aforce_save(self) -> None:
        """
        异步强制保存所有待写入的配置到磁盘
        """
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.force_save)

    async def areload(self) -> None:
        """
        异步重新从磁盘加载配置
        """
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.reload)


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


__all__ = ["ConfigManager", "config", "parse_bool_config"]
