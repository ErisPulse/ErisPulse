"""
ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能
添加内存缓存和延迟写入机制以提高性能
基于 tomlkit 实现注释保留写入：配置文件中的注释与键顺序在任何框架写入后均不丢失
配置写入采用"唯一临时文件 + fsync + 原子替换"（``os.replace``）：
进程被杀（OOM / SIGKILL）或断电时磁盘上的配置文件要么是完整旧内容、要么是完整新内容，
不会出现空文件或半写状态；临时文件名按进程唯一，多实例共享配置目录时不再互相争抢踩踏

{!--< tips >!--}
1. 使用 getConfig(key) / setConfig(key, value) 读写配置
2. 配置变更可通过生命周期钩子监听: @lifecycle.on("config.set")
{!--< /tips >!--}
"""

import atexit
import copy
import os
import tempfile
import threading
import time
import weakref
from pathlib import Path
from typing import Any, ClassVar, TypeAlias

import tomlkit
from tomlkit.exceptions import ParseError
from tomlkit.items import Table

from .constants import (
    CONFIG_CACHE_TIMEOUT_SECS,
    CONFIG_LOCK_FILE_NAME,
    CONFIG_WRITE_DELAY_SECS,
    CONFIG_WRITE_RETRY_DELAY_SECS,
    DEFAULT_CONFIG_FILE_PATH,
)
from .i18n import i18n

ConfigValue: TypeAlias = Any
ConfigKey: TypeAlias = str


class _DeletedValue:
    """
    ``delete()`` 在脏队列中的"待移除"标记

    与 ``setConfig(key, None)`` 的置空不同，此标记表示键将从文件中删除。
    脏队列的读路径会对值做深拷贝，标记必须在此过程中保持单例身份，
    供 ``is`` 判别。

    {!--< internal-use >!--}
    {!--< /internal-use >!--}
    """

    def __deepcopy__(self, memo):
        return self

    def __copy__(self):
        return self

    def __repr__(self):
        return "<DELETED>"


_DELETED = _DeletedValue()


class _FlushHandle:
    """
    {!--< internal-use >!--}
    ``_write_timer`` 兼容句柄

    延迟刷盘已由常驻 ``config-watcher`` 线程按 ``_flush_deadline`` 调度；
    本句柄仅为既有测试与退出路径保留 ``_write_timer`` 属性语义
    （"存在即有未落盘写入"），``cancel()`` 为幂等空操作。
    """

    __slots__ = ()

    def cancel(self) -> None:
        return None


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
        self._write_retry_delay = CONFIG_WRITE_RETRY_DELAY_SECS
        self._write_timer: _FlushHandle | None = None  # 写入定时器（兼容句柄，见 _schedule_write）
        self._flush_deadline: float | None = None  # 最近一次写入安排的刷盘时刻（time.monotonic）
        self._flush_wakeup = threading.Event()  # 常驻 watcher 线程的提前唤醒信号
        self._lock = threading.RLock()  # 线程安全锁
        self._file_lock = threading.RLock()  # 文件操作锁
        self._atexit_registered = False  # atexit 钩子注册标记
        self._last_self_write_mtime: float = 0.0  # 框架自身最后一次刷盘的 mtime
        self._migrate_config()  # 迁移旧配置文件
        self._acquire_instance_lock()  # 尝试独占配置目录（多实例共享检测，仅告警不阻塞）
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
                # 到期的延迟刷盘：setConfig 不再创建线程，统一由本线程
                # 睡到 deadline 后执行（_flush_config 内部持锁，线程安全）
                try:
                    with self._lock:
                        due = self._flush_deadline is not None and time.monotonic() >= self._flush_deadline
                    if due:
                        self._flush_config()
                        with self._lock:
                            if self._dirty_keys:
                                # 刷盘失败（_flush_config 失败时吞异常保留脏键）：
                                # 短退避重试，避免静默等到下一次用户写入才补写
                                self._flush_deadline = time.monotonic() + self._write_retry_delay
                            else:
                                self._flush_deadline = None

                    # 等待：刷盘 deadline 与轮询间隔取较小者；新写入会提前唤醒
                    with self._lock:
                        deadline = self._flush_deadline
                    wait = self._CONFIG_WATCH_INTERVAL
                    if deadline is not None:
                        wait = min(wait, max(0.0, deadline - time.monotonic()))
                    if self._flush_wakeup.wait(timeout=wait):
                        self._flush_wakeup.clear()
                    if self._watcher_stop.is_set():
                        break

                    with self._lock:
                        # _check_file_change 已能区分"框架自身刷盘"与"外部修改"：
                        # 自身刷盘的 mtime 与 _last_self_write_mtime 一致 → 返回 False
                        if not self._check_file_change():
                            continue
                        # 真正的外部修改：重载文件到缓存。
                        # 不清空 _dirty_keys、不清除 _flush_deadline —— 待写键会在
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
        ConfigManager._register_watcher_shutdown(self)

    # 注册了 watcher 的实例（弱引用，随实例回收）。自由线程构建（3.14t）下
    # threading._shutdown 会等待全部后台线程结束——多个测试/多实例泄漏的
    # watcher 若在收尾阶段仍参与 config._lock 竞争，会让进程退出挂死；
    # 经 threading._register_atexit（先于 join 执行，concurrent.futures 同款
    # 机制）统一发出停止信号，watcher 至多等一个轮询周期后自然退出。
    _active_watchers: ClassVar["weakref.WeakSet[ConfigManager]"] = weakref.WeakSet()
    _watcher_shutdown_hook_registered: ClassVar[bool] = False

    @classmethod
    def _register_watcher_shutdown(cls, manager: "ConfigManager") -> None:
        """{!--< internal-use >!--} 注册解释器关停时的 watcher 统一停止钩子（幂等）"""
        cls._active_watchers.add(manager)
        if cls._watcher_shutdown_hook_registered:
            return
        cls._watcher_shutdown_hook_registered = True
        try:
            from threading import _register_atexit

            def _stop_all_watchers() -> None:
                for m in list(cls._active_watchers):
                    try:
                        m._watcher_stop.set()
                        m._flush_wakeup.set()
                    except Exception:
                        pass

            _register_atexit(_stop_all_watchers)
        except Exception:
            pass

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
        # 相对 CONFIG_FILE 锚定（Windows 服务 / 计划任务的启动目录不定，
        # CWD 相对路径会让迁移行为漂移）：旧文件 = config/config.toml 同级的
        # config.toml，说明文件写在配置目录内
        old_config_path = str(Path(self.CONFIG_FILE).parent.parent / "config.toml")

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

            # 原子写入：避免"新文件半写 + 旧文件已删"窗口内中断导致配置丢失
            self._atomic_write_text(tomlkit.dumps(old_doc))

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

            with (Path(self.CONFIG_FILE).parent / "config.readme.md").open(
                "w", encoding="utf-8"
            ) as f:
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
            if value is _DELETED:
                # 待删除键：缓存中已不存在 → 删除已是既成事实，标记可丢弃
                if not found:
                    del self._dirty_keys[key]
                continue
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

    def _acquire_instance_lock(self) -> None:
        """
        尝试以独占方式锁定配置目录的实例锁文件，检测多实例共享配置目录

        锁文件位于配置文件同级目录（:data:`~.constants.CONFIG_LOCK_FILE_NAME`），
        进程持锁后全生命周期不释放，由 OS 在进程退出时自动归还——
        无需清理逻辑，进程被强杀也不会留下"幽灵锁"。
        锁被占用说明另一个 ErisPulse 实例正在使用同一配置目录，
        此时仅记录告警（并发写入可能互相覆盖），不阻塞框架启动。

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        self._instance_lock_fd: int | None = None
        lock_path = Path(self.CONFIG_FILE).parent / CONFIG_LOCK_FILE_NAME
        try:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
        except OSError:
            return  # 文件系统只读等场景：放弃检测，不影响框架启动
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._instance_lock_fd = fd
        except OSError:
            os.close(fd)
            self._log_config_error(
                i18n.t("core.config.multi_instance_detected", path=self.CONFIG_FILE),
                level="warning",
            )
        except Exception:
            # 平台不支持等异常场景：静默放弃检测，不影响框架启动
            os.close(fd)

    def _atomic_write_text(self, text: str) -> None:
        """
        原子写入配置文件（唯一临时文件 + fsync + ``os.replace``）

        旧实现使用固定名 ``<config>.tmp`` 并在 rename 前不落盘，存在两类丢文件场景：
        多实例共享配置目录时同名临时文件被对端 truncate / rename（ENOENT 争抢）；
        进程被杀或断电时 rename 元数据先于数据块落盘（ext4 延迟分配），留下空文件。
        现改为：同目录 ``mkstemp`` 生成进程唯一临时文件 → 写毕 ``flush + fsync``
        强制数据落盘 → ``os.replace`` 原子替换目标（POSIX / Windows 均原子）；
        POSIX 下额外 fsync 配置目录，尽力保证断电后替换结果不回退。

        :param text: str 待写入的完整文件内容
        :raises OSError: 临时文件创建、写入或替换失败时抛出，由调用方按写失败处理

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        config_path = Path(self.CONFIG_FILE)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_file = tempfile.mkstemp(
            dir=str(config_path.parent), prefix=config_path.name + ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
                f.flush()
                os.fsync(f.fileno())
            # 直接调用 os.replace（不走 Path.replace：旧版本 pathlib 经
            # _accessor 静态绑定，运行期替换 os.replace 不可观测）
            os.replace(temp_file, config_path)  # noqa: PTH105
        except BaseException:
            try:
                Path(temp_file).unlink()
            except OSError:
                pass
            raise
        if os.name == "posix":
            try:
                dir_fd = os.open(str(config_path.parent), os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except OSError:
                pass

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
    def _delete_doc_path(doc: Any, keys: list[str]) -> None:
        """
        在 tomlkit 文档树中按点分路径删除键

        中间层缺失或非表时视为已删除（幂等）；仅触碰目标键所在行，
        文件其余内容与注释保持不变。删除子表的最后一个键后，空表头
        原样保留（与后续重设同名键的行为兼容）。

        :param doc: tomlkit 文档/表对象
        :param keys: 点分路径拆分后的键列表

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        node = doc
        for k in keys[:-1]:
            child = node.get(k)
            if not isinstance(child, Table):
                return
            node = child
        try:
            del node[keys[-1]]
        except KeyError:
            pass

    @staticmethod
    def _toml_safe_value(value: Any) -> Any:
        """
        将待写入值转换为 TOML 可序列化形态

        TOML 没有 null：``setConfig`` 置空语义的 ``None`` 在落盘时等价于
        "键不存在"——标量 ``None`` 返回 ``None``（由调用方跳过该键），
        字典内的 ``None`` 叶子递归剔除（其余键值原样保留，不改变顺序之外
        的内容）。列表内的 ``None`` 属于数组元素，剔除会改变元素位置，
        保持原样交由单键隔离丢弃并告警。

        :param value: 待写入的值
        :return: 可直接交给 tomlkit 的值；标量 ``None`` 原样返回

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if not isinstance(value, dict):
            return value

        def _strip(node: dict[str, Any]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for k, v in node.items():
                if v is None:
                    continue
                result[k] = _strip(v) if isinstance(v, dict) else v
            return result

        return _strip(value)

    def _remove_cache_path(self, keys: list[str]) -> None:
        """
        从内存缓存中按点分路径移除键（delete 时的即时视图更新）

        仅移除目标键本身，不裁剪因此变空的祖先表——与落盘后
        ``_doc_to_plain_dict`` 的重建结果保持一致。

        :param keys: 点分路径拆分后的键列表

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        node = self._cache
        for k in keys[:-1]:
            if not isinstance(node, dict) or k not in node:
                return
            node = node[k]
        if isinstance(node, dict):
            node.pop(keys[-1], None)

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

                    # 应用待写入的更改（注释保留：仅触碰脏键所在行，其余原样保留）。
                    # 按键特异性排序：路径浅者（整节/祖先）先应用、深者（点分/后代）
                    # 后应用——同节点分写不被整节写吞掉（与 getConfig ①④的叠加
                    # 语义同口径）；sorted 稳定排序保持同深度内的写入时序
                    pending = sorted(self._dirty_keys.items(), key=lambda kv: kv[0].count("."))
                    failed_keys: list[tuple[str, Exception]] = []
                    for key, value in pending:
                        try:
                            if value is _DELETED:
                                self._delete_doc_path(doc, key.split("."))
                                continue
                            safe_value = self._toml_safe_value(value)
                            if safe_value is None:
                                # None（setConfig 置空语义）在 TOML 中等价于"键不存在"：
                                # 不落盘，直接出队（缓存中的置空视图由 default 语义承接）
                                self._dirty_keys.pop(key, None)
                                continue
                            self._set_doc_path(doc, key.split("."), safe_value)
                        except Exception as e:
                            # 单键不可序列化（如列表内含 None）：仅丢弃该键，
                            # 不阻塞其余待写键落盘（否则脏队列永不清空、无限重试刷屏）
                            failed_keys.append((key, e))
                            self._dirty_keys.pop(key, None)

                    if failed_keys:
                        try:
                            from .logger import logger

                            for key, e in failed_keys:
                                logger.error(
                                    i18n.t("core.config.set_failed", key=key, error=e)
                                )
                        except (ImportError, AttributeError):
                            pass

                    # 原子写入：唯一临时文件 + fsync + os.replace（多实例/断电安全）
                    self._atomic_write_text(tomlkit.dumps(doc))

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
                    # 临时文件清理由 _atomic_write_text 的 mkstemp 唯一命名 +
                    # 失败即删语义负责，此处无需（也不能）按旧固定名清理

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

        真实调度由常驻 ``config-watcher`` 线程承担（按 ``_flush_deadline``
        睡到到期后刷盘），避免每次写入创建/取消 ``threading.Timer``
        带来的线程创建开销（高频 setConfig 的热点）。
        ``_write_timer`` 保留为兼容句柄：既有测试与退出路径依赖其
        存在性与 ``cancel()`` 方法，语义为"存在即有未落盘写入"。

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        with self._lock:
            self._flush_deadline = time.monotonic() + self._write_delay
            if self._write_timer is None:
                self._write_timer = _FlushHandle()
            self._flush_wakeup.set()

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
        except Exception as e:
            # 广播失败留痕：订阅方的 config.updated 感知不到会静默失效
            try:
                from .logger import logger

                logger.debug(i18n.t("core.config.emit_failed", error=e))
            except (ImportError, AttributeError):
                pass

    # ==================== 配置读写 ====================

    def getConfig(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        支持点分隔符路径（如 ``"module.sub.key"``）。当存在待写入队列
        （延迟刷盘未落盘的 ``setConfig``）时，读取结果会**叠加待写值**，
        保证"写后立读"一致性（同节点分写优先于整节待写值可见，
        与 ``_flush_config`` 的特异性排序同口径）：

        - 查询键精确命中待写队列 → 叠加其后代待写值后返回
        - 待写键是查询键的祖先 → 在待写值子树内继续解析剩余路径
        - 待写键是查询键的后代 → 以待写值深合并覆盖缓存子树

        涉及待写值的返回值为隔离深拷贝：调用方原地修改返回的 dict
        不会改动待落盘状态。

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

            keys = key.split(".")

            # ① 精确命中待写队列：仍叠加后代待写值（点分写更具体，
            #    优先于整节待写值可见），并返回隔离拷贝
            if key in self._dirty_keys:
                value = self._dirty_keys[key]
                overlay = self._dirty_overlay(keys)
                if value is _DELETED:
                    # 待删除键：视图为空，但后代待写值（删后重设）仍可见
                    return copy.deepcopy(overlay) if overlay else default
                if overlay:
                    if isinstance(value, dict):
                        return copy.deepcopy(self._deep_merge(value, overlay))
                    # 非字典（标量）：flush 后该键将变为子表，直接返回叠加子树
                    return copy.deepcopy(overlay)
                return copy.deepcopy(value)

            # ② 待写键是查询键的祖先：取最长（最具体）的待写祖先，
            #    在其值子树内解析剩余路径
            dirty_ancestor: tuple[str, Any] | None = None
            for dirty_key, dirty_value in self._dirty_keys.items():
                if key.startswith(dirty_key + ".") and (
                    dirty_ancestor is None or len(dirty_key) > len(dirty_ancestor[0])
                ):
                    dirty_ancestor = (dirty_key, dirty_value)
            if dirty_ancestor is not None:
                if dirty_ancestor[1] is _DELETED:
                    # 查询键位于待删除子树内 → 视图已不存在
                    return default
                node = dirty_ancestor[1]
                for rk in keys[len(dirty_ancestor[0].split(".")) :]:
                    if not isinstance(node, dict) or rk not in node:
                        return default
                    node = node[rk]
                # 子树取自待写队列，同样返回隔离拷贝
                value = copy.deepcopy(node)
            else:
                # ③ 常规缓存树查询
                value = self._walk_cache(key, default)

            # ④ 待写键是查询键的后代：以待写值深合并叠加（读-你-写一致性）
            overlay = self._dirty_overlay(keys)
            if overlay:
                if isinstance(value, dict):
                    return copy.deepcopy(self._deep_merge(value, overlay))
                # 非字典（标量或键缺失）：flush 后该键将变为子表，直接返回
                # 叠加结果，避免刷盘前读到旧标量（写后立读不一致的边角）
                return copy.deepcopy(overlay)
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
            if dirty_value is _DELETED:
                # 待删除键不进入叠加视图（其缓存条目已在 delete 时移除）
                continue
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

    def getAllConfig(self) -> dict[str, Any]:
        """
        返回全量配置快照（深拷贝）

        替代直接读取私有 ``_cache``：返回值为隔离副本，调用方原地修改
        不影响框架配置状态。视图口径与 :meth:`getConfig` 一致——缓存 +
        待写队列按特异性排序重放（与 ``_flush_config`` 落盘结果严格一致，
        延迟的 ``setConfig`` / ``delConfig`` 均已反映，删除的键不出现）。

        :return: dict 全量配置快照

        :example:
        >>> config = sdk.config.getAllConfig()
        >>> config["ErisPulse"]["server"]["port"]
        """
        with self._lock:
            self._check_cache_validity()
            snapshot = copy.deepcopy(self._cache)

            # 按 flush 的特异性排序重放待写队列：路径浅者（整节/祖先）先
            # 应用、深者（点分/后代）后应用，删除标记移除对应路径——
            # 快照与落盘结果保持同一口径
            pending = sorted(self._dirty_keys.items(), key=lambda kv: kv[0].count("."))
            for key, value in pending:
                keys = key.split(".")
                if value is _DELETED:
                    node = snapshot
                    for k in keys[:-1]:
                        if not isinstance(node, dict) or k not in node:
                            break
                        node = node[k]
                    else:
                        if isinstance(node, dict):
                            node.pop(keys[-1], None)
                    continue
                node = snapshot
                for k in keys[:-1]:
                    child = node.get(k)
                    if not isinstance(child, dict):
                        child = {}
                        node[k] = child
                    node = child
                node[keys[-1]] = copy.deepcopy(value)

            return snapshot

    def delConfig(self, key: str, *, immediate: bool = False) -> bool:
        """
        删除配置键（支持点分隔符路径），按 setConfig 同样的脏队列语义落盘

        与 ``setConfig(key, None)`` 的"置空但键仍在"不同：delete 会把键
        从配置文件中移除。存在性按当前读取视图判定（缓存 + 待写叠加，
        与 :meth:`getConfig` 同口径——待写整节内的键、已删除的键均如实
        判定）。落盘走 tomlkit 增量修改路径，文件其余内容与注释不受
        影响；删除复用 ``config.set`` 事件广播（``new_value=None``），
        现有监听方（如适配器的 ``on_config_update``）零改动即可感知。

        :param key: str 配置键, 支持点分隔符如 "module.sub.key"
        :param immediate: bool 是否立即写入磁盘 (默认: False, 延迟写入)
        :return: bool 键是否存在（存在则已调度删除；不存在返回 False）

        :example:
        >>> sdk.config.delConfig("ErisPulse.modules.status.OldModule")
        >>> sdk.config.delConfig("OneBot.deprecated_key", immediate=True)
        """
        missing = object()
        try:
            with self._lock:
                old_value = self.getConfig(key, missing)
                if old_value is missing:
                    return False
                self._dirty_keys[key] = _DELETED
                self._remove_cache_path(key.split("."))

                if immediate:
                    self._flush_config()
                else:
                    self._schedule_write()

            from .lifecycle import lifecycle
            from .logger import logger

            logger.trace(f"config.delete: key={key}")
            lifecycle.emit_sync(
                "config.set",
                {
                    "key": key,
                    "old_value": old_value,
                    "new_value": None,
                },
            )
            return True
        except Exception as e:
            try:
                from .logger import logger

                logger.error(i18n.t("core.config.delete_failed", key=key, error=e))
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
            self._flush_deadline = None  # 待写项已排空，撤销 watcher 线程的到期刷盘
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

    async def agetAllConfig(self) -> dict[str, Any]:
        """
        异步返回全量配置快照

        :return: dict 全量配置快照（深拷贝）
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.getAllConfig)

    async def adelConfig(self, key: str, *, immediate: bool = False) -> bool:
        """
        异步删除配置键

        :param key: str 配置键, 支持点分隔符
        :param immediate: bool 是否立即写入磁盘
        :return: bool 键是否存在（存在则已调度删除）
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.delConfig(key, immediate=immediate))

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

                    # 原子写入：唯一临时文件 + fsync + os.replace（多实例/断电安全）
                    self._atomic_write_text(tomlkit.dumps(doc))

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
