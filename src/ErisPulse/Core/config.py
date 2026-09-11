"""
ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能
添加内存缓存和延迟写入机制以提高性能
基于 tomlkit 实现注释保留写入：配置文件中的注释与键顺序在任何框架写入后均不丢失

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

import tomlkit
from tomlkit.exceptions import ParseError
from tomlkit.items import Table

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
        self._last_self_write_mtime: float = 0.0  # 框架自身最后一次刷盘的 mtime
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
                    with self._lock:
                        # _check_file_change 已能区分"框架自身刷盘"与"外部修改"：
                        # 自身刷盘的 mtime 与 _last_self_write_mtime 一致 → 返回 False
                        if not self._check_file_change():
                            continue
                        # 真正的外部修改：重载文件到缓存。
                        # 不清空 _dirty_keys、不取消 _write_timer —— 待写键会在
                        # 下次 _flush_config 时与外部内容合并（脏键优先），
                        # 避免丢失本进程尚未落盘的写入。
                        old_cache = self._cache.copy() if self._cache else {}
                        loaded = self._load_config()
                    # 仅在成功加载时广播变更，半成品/语法错误的 TOML
                    # 不再以空配置形式触发 config.updated
                    if loaded:
                        self._emit_config_updated(old_cache)
                except Exception as e:
                    # 监听异常不再静默吞掉，便于排查 watcher 故障
                    self._log_config_error(
                        i18n.t("core.config.watcher_error", error=e),
                        level="warning",
                    )

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

            # tomlkit 解析保留原文件注释与键顺序，迁移后内容与原文件一致
            with Path(old_config_path).open(encoding="utf-8") as f:
                old_doc = tomlkit.parse(f.read())

            with Path(self.CONFIG_FILE).open("w", encoding="utf-8") as f:
                f.write(tomlkit.dumps(old_doc))

            readme_content = f"""# 配置文件迁移说明

您的配置文件已从项目根目录迁移到 `config/` 目录。

## 迁移详情

- **旧位置**: `config.toml`
- **新位置**: `config/config.toml`

## 原配置内容

```toml
{tomlkit.dumps(old_doc)}
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

    def _load_config(self) -> bool:
        """
        从文件加载配置到缓存

        对加载失败按三种状态分别给出可操作的诊断信息：

        - 文件缺失：正常首次启动，静默使用空配置
        - TOML 语法错误：输出出错行号/列号与原因，保留上次有效缓存（不擦除）
        - 权限/其他错误：输出明确原因，保留上次有效缓存（不擦除）

        :return: bool 加载成功（含文件缺失）返回 True；解析/权限等错误返回 False

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        with self._lock:
            path = Path(self.CONFIG_FILE)
            if not path.exists():
                self._cache = {}
                self._cache_timestamp = time.time()
                return True

            try:
                with path.open(encoding="utf-8") as f:
                    config = tomlkit.parse(f.read()).unwrap()
            except ParseError as e:                # 态1：TOML 语法错误——给出行号/列号与原因，便于用户精确定位
                # 保留上次有效缓存，避免半成品 TOML 干扰运行中的进程
                self._log_config_error(
                    i18n.t(
                        "core.config.toml_malformed",
                        path=self.CONFIG_FILE,
                        line=getattr(e, "line", "?"),
                        col=getattr(e, "col", "?"),
                        reason=getattr(e, "msg", str(e)),
                    )
                )
                self._log_config_error(
                    i18n.t("core.config.using_defaults_warning"),
                    level="warning",
                )
                return False
            except PermissionError:
                # 态2：权限问题——明确告知，避免误以为是配置内容问题
                self._log_config_error(
                    i18n.t("core.config.permission_denied", path=self.CONFIG_FILE),
                )
                self._log_config_error(
                    i18n.t("core.config.using_defaults_warning"),
                    level="warning",
                )
                return False
            except Exception as e:
                # 态3：其他未知错误——保留原有通用提示
                self._log_config_error(i18n.t("core.config.load_failed", path=self.CONFIG_FILE, error=e))
                self._log_config_error(
                    i18n.t("core.config.using_defaults_warning"),
                    level="warning",
                )
                return False
            else:
                self._cache = config
                self._cache_timestamp = time.time()
                # 外部修改重载后，丢弃与新文件一致的待写键，
                # 避免陈旧的整棵/叶子脏键在下次 flush 时覆盖用户热更新
                self._drop_redundant_dirty_keys()
                if not self._cache:
                    self._log_config_error(
                        i18n.t("core.config.loaded_empty", path=self.CONFIG_FILE),
                        level="debug",
                    )
                return True

    def _drop_redundant_dirty_keys(self) -> None:
        """
        丢弃与新配置文件内容一致的待写键

        配置重载（外部修改）后，部分待写键的值可能已与文件一致，
        继续保留会在下次 flush 时用陈旧快照覆盖用户热更新。
        仅当待写值已反映在缓存（即文件）中时才丢弃；真正未落盘的写入仍保留。

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if not self._dirty_keys:
            return
        for key in list(self._dirty_keys):
            value = self._dirty_keys[key]
            current = self._cache
            found = True
            for k in key.split("."):
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    found = False
                    break
            if found and current == value:
                del self._dirty_keys[key]

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

    @staticmethod
    def _set_doc_path(doc: Any, keys: list[str], value: Any) -> None:
        """
        在 tomlkit 文档树中按点分路径写入值

        中间层节点缺失或非表时以空表替换（与 dict 语义一致）；
        叶子写入保留既有注释与顺序，新键追加至所在节末尾。

        :param doc: tomlkit 文档/表对象
        :param keys: 点分路径拆分后的键列表
        :param value: 待写入的值（plain dict 会转换为标准 table）

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        node = doc
        for k in keys[:-1]:
            child = node.get(k)
            if not isinstance(child, Table):
                node[k] = {}
                child = node[k]
            node = child
        node[keys[-1]] = value

    @staticmethod
    def _doc_to_plain_dict(doc: Any) -> dict[str, Any]:
        """
        将 tomlkit 文档转为 plain dict 缓存

        经 body 低层插入的条目不进入容器索引，直接 ``unwrap()`` 会丢失；
        渲染后重新解析可保证缓存与文件内容严格一致。

        :param doc: tomlkit 文档对象
        :return: dict 纯字典形式的配置内容

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        return tomlkit.parse(tomlkit.dumps(doc)).unwrap()

    def _flush_config(self) -> None:
        """
        将待写入的配置刷新到文件

        使用文件锁确保多线程环境下的原子性操作。
        基于 tomlkit 在解析出的文档树上做增量修改后整体回写，
        文件中已有的注释与键顺序不因框架写入而丢失或重排。

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
                            doc = tomlkit.parse(f.read())
                    else:
                        doc = tomlkit.document()

                    # 应用待写入的更改（注释保留：仅触碰脏键所在行，其余原样保留）
                    for key, value in self._dirty_keys.items():
                        self._set_doc_path(doc, key.split("."), value)

                    temp_file = self.CONFIG_FILE + ".tmp"
                    with Path(temp_file).open("w", encoding="utf-8") as f:
                        f.write(tomlkit.dumps(doc))

                    # 原子性重命名
                    if os.name == "nt":
                        if Path(self.CONFIG_FILE).exists():
                            Path(temp_file).replace(self.CONFIG_FILE)
                        else:
                            Path(temp_file).rename(self.CONFIG_FILE)
                    else:
                        Path(temp_file).rename(self.CONFIG_FILE)

                    # 更新缓存并清除待写入队列（转回 plain dict，保持缓存类型不变）
                    self._cache = self._doc_to_plain_dict(doc)
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
                        self._last_self_write_mtime = self._config_mtime
                    except OSError:
                        pass

                except ParseError as e:
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
                                    line=getattr(e, "line", "?"),
                                    col=getattr(e, "col", "?"),
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
                if self._load_config():
                    self._emit_config_updated(old_cache)
            else:
                self._load_config()

    def _check_file_change(self) -> bool:
        """
        检测配置文件是否被外部程序或用户手动编辑

        对比记录的 mtime 与当前文件 mtime，若不一致说明文件已被外部修改。
        若变化后的 mtime 与框架自身最后一次刷盘的 mtime（``_last_self_write_mtime``）
        一致，则判定为框架自身的写入而非外部修改，返回 False。

        :return: bool 文件是否被外部修改

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
                # 若 mtime 与框架自身最后一次刷盘一致，说明是 _flush_config 的
                # 写入，不算外部修改（避免 watcher 误触发重载）
                return current_mtime != self._last_self_write_mtime
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

            lifecycle.emit_sync(
                "config.updated",
                {
                    "old_config": old_config,
                    "new_config": self._cache,
                    "config_file": self.CONFIG_FILE,
                },
            )
        except Exception:
            pass

    # ==================== 配置读写 ====================

    def getConfig(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        支持点分隔符路径（如 ``"module.sub.key"``）。当存在待写入队列
        （延迟刷盘未落盘的 ``setConfig``）时，读取结果会**叠加待写值**，
        保证"写后立读"一致性：

        - 查询键精确命中待写队列 → 直接返回待写值
        - 待写键是查询键的祖先 → 在待写值子树内继续解析
        - 待写键是查询键的后代 → 以待写值深合并覆盖缓存子树

        :param key: str 配置键, 支持点分隔符如 "module.sub.key"
        :param default: Any 默认值 (默认: None)
        :return: Any 配置值

        :example:
        >>> value = sdk.config.getConfig("ErisPulse.server.port", 8000)
        """
        with self._lock:
            self._check_cache_validity()

            if not self._dirty_keys:
                return self._walk_cache(key, default)

            # ① 精确命中待写队列
            if key in self._dirty_keys:
                return self._dirty_keys[key]

            keys = key.split(".")

            # ② 待写键是查询键的祖先：取最长（最具体）的待写祖先，
            #    在其值子树内解析剩余路径
            dirty_ancestor: tuple[str, Any] | None = None
            for dirty_key, dirty_value in self._dirty_keys.items():
                if key.startswith(dirty_key + ".") and (
                    dirty_ancestor is None or len(dirty_key) > len(dirty_ancestor[0])
                ):
                    dirty_ancestor = (dirty_key, dirty_value)
            if dirty_ancestor is not None:
                node = dirty_ancestor[1]
                for rk in keys[len(dirty_ancestor[0].split(".")) :]:
                    if not isinstance(node, dict) or rk not in node:
                        return default
                    node = node[rk]
                value = node
            else:
                # ③ 常规缓存树查询
                value = self._walk_cache(key, default)

            # ④ 待写键是查询键的后代：以待写值深合并叠加（读-你-写一致性）
            overlay = self._dirty_overlay(keys)
            if overlay:
                if isinstance(value, dict):
                    return self._deep_merge(value, overlay)
                if value is default:
                    return overlay
            return value

    def _walk_cache(self, key: str, default: Any) -> Any:
        """
        {!--< internal-use >!--}
        在缓存树中按点分路径取值；路径缺失或中间节点非字典时返回 default

        :param key: 点分配置键
        :param default: 路径缺失时的默认值
        :return: 缓存中的值或 default
        """
        value: Any = self._cache
        for k in key.split("."):
            if not isinstance(value, dict) or k not in value:
                return default
            value = value[k]
        return value

    def _dirty_overlay(self, keys: list[str]) -> dict[str, Any]:
        """
        {!--< internal-use >!--}
        收集以待查键为前缀的待写键，构建叠加子树

        :param keys: 查询键的路径段列表
        :return: 叠加子树（无匹配时为空字典）
        """
        prefix = ".".join(keys) + "."
        overlay: dict[str, Any] = {}
        for dirty_key, dirty_value in self._dirty_keys.items():
            if not dirty_key.startswith(prefix):
                continue
            node = overlay
            for p in dirty_key[len(prefix) :].split(".")[:-1]:
                node = node.setdefault(p, {})
            node[dirty_key.rsplit(".", 1)[-1]] = dirty_value
        return overlay

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """
        {!--< internal-use >!--}
        深合并字典（override 优先，仅 dict 值递归合并）

        :param base: 基础字典（不修改原对象）
        :param override: 覆盖字典
        :return: 合并后的新字典
        """
        merged = dict(base)
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k] = ConfigManager._deep_merge(merged[k], v)
            else:
                merged[k] = v
        return merged

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
        return await loop.run_in_executor(None, lambda: self.setConfig(key, value, immediate))

    def setConfigTemplate(self, key: str, toml_text: str, immediate: bool = True) -> bool:
        """
        以带注释的 TOML 模板文本写入指定配置节

        用于适配器/模块首次生成配置模板：模板中的字段注释原样落盘。
        目标节已存在时不覆盖（由调用方保证仅在配置缺失时调用）；
        文件其余内容与注释不受影响。

        :param key: str 配置节键（支持点分路径，如 ``"MyAdapter"``）
        :param toml_text: str 模板 TOML 文本（仅键值与注释，不含节头）
        :param immediate: bool 是否立即写入磁盘 (默认: True)
        :return: bool 是否写入成功

        :example:
        >>> sdk.config.setConfigTemplate("MyAdapter", '# API 令牌\\ntoken = ""')
        """
        try:
            parsed = tomlkit.parse(toml_text)
        except ParseError as e:
            self._log_config_error(
                i18n.t(
                    "core.config.template_malformed",
                    key=key,
                    line=getattr(e, "line", "?"),
                    col=getattr(e, "col", "?"),
                    reason=getattr(e, "msg", str(e)),
                )
            )
            return False

        # 模板条目（含独立注释与空行）逐项搬运到新表，保留注释
        section = tomlkit.table()
        for item_key, item in parsed.body:
            section.value.body.append((item_key, item))

        with self._lock:
            with self._file_lock:
                try:
                    if Path(self.CONFIG_FILE).exists():
                        with Path(self.CONFIG_FILE).open(encoding="utf-8") as f:
                            doc = tomlkit.parse(f.read())
                    else:
                        doc = tomlkit.document()

                    # 定位父节点，目标节已存在则不覆盖
                    keys = key.split(".")
                    node = doc
                    exists = True
                    for k in keys:
                        child = node.get(k)
                        if not isinstance(child, Table):
                            exists = False
                            break
                        node = child
                    if exists:
                        return False

                    parent = doc
                    for k in keys[:-1]:
                        child = parent.get(k)
                        if not isinstance(child, Table):
                            parent[k] = {}
                            child = parent[k]
                        parent = child
                    parent[keys[-1]] = section

                    if not immediate:
                        self._cache = self._doc_to_plain_dict(doc)
                        self._cache_timestamp = time.time()
                        return True

                    temp_file = self.CONFIG_FILE + ".tmp"
                    with Path(temp_file).open("w", encoding="utf-8") as f:
                        f.write(tomlkit.dumps(doc))

                    # 原子性重命名
                    if os.name == "nt":
                        if Path(self.CONFIG_FILE).exists():
                            Path(temp_file).replace(self.CONFIG_FILE)
                        else:
                            Path(temp_file).rename(self.CONFIG_FILE)
                    else:
                        Path(temp_file).rename(self.CONFIG_FILE)

                    self._cache = self._doc_to_plain_dict(doc)
                    self._cache_timestamp = time.time()
                    # 写入成功 → 清除告警冷却标记（与 _flush_config 行为一致）
                    sentinel = self._malformed_sentinel_path
                    try:
                        if sentinel.exists():
                            sentinel.unlink()
                    except Exception:
                        pass

                    # 同步 mtime，避免文件监听任务把自身写入误判为外部修改
                    try:
                        self._config_mtime = Path(self.CONFIG_FILE).stat().st_mtime
                        self._last_self_write_mtime = self._config_mtime
                    except OSError:
                        pass

                    return True

                except ParseError as e:
                    self._log_config_error(
                        i18n.t(
                            "core.config.toml_malformed",
                            path=self.CONFIG_FILE,
                            line=getattr(e, "line", "?"),
                            col=getattr(e, "col", "?"),
                            reason=getattr(e, "msg", str(e)),
                        )
                    )
                    return False
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
                    return False

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


def json_safe(value: Any, _depth: int = 0) -> Any:
    """
    递归将任意结构转换为可直接 JSON 序列化的等价结构

    供 ``get_topology`` 等面向 WebUI 的聚合方法保证输出可序列化：
    dict / list / tuple / set 递归处理；类对象（``type``）取
    ``__name__``；其余不可序列化对象退化为 ``str()`` 表示。

    :param value: 任意值
    :param _depth: [internal-use] 递归深度保护
    :return: 可被 ``json.dumps`` 序列化的等价结构
    """
    if _depth > 12:
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): json_safe(v, _depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v, _depth + 1) for v in value]
    if isinstance(value, type):
        return getattr(value, "__name__", str(value))
    return str(value)


__all__ = ["ConfigManager", "config", "parse_bool_config", "json_safe"]
