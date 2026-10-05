"""
ErisPulse 会话收件箱（transcript）

提供每会话近期消息流的统一记录与查询，作为上下文记忆类模块
（AI 对话、防复读、行为分析等）的公共底座：

- **入站**：消息事件进入分发管线时自动记录（role="user"）；
- **出站**：机器人发送的文本类消息经 ``message.sent`` 钩子自动记录（role="bot"）；
- **存储**：独立 SQLite 表（经 storage），写入走内存缓冲 + 后台批量落盘
  （默认每 1 秒或满 64 条一事务提交），查询自动合并未落盘的缓冲行；
  每会话条数上限 + 全局 TTL 自动清理；
- **查询**：``event.history(n)`` 或 ``sdk.transcript.get(event, n)``。

{!--< tips >!--}
配置（``ErisPulse.transcript``）::

    [ErisPulse.transcript]
    enabled = true          # 是否启用（关闭后停止写入，历史仍可查询）
    max_per_session = 50    # 每会话保留的最大条数
    ttl_hours = 168         # 全局过期时间（小时），过期记录惰性清理

持久性说明：追加先进内存缓冲，由后台任务批量落盘（延迟至多
``TRANSCRIPT_FLUSH_INTERVAL_SECS`` 秒）；正常退出（``sdk.uninit`` / 进程
atexit）会强制刷盘。进程被硬崩溃 / 强杀时，最近一批未落盘记录（约 1 秒内）
可能丢失。

使用方式::

    from ErisPulse.Core import transcript

    # 查询当前会话最近 20 条消息（含用户与机器人）
    messages = await event.history(20)   # 或 transcript.get(event, 20)
    for m in messages:
        print(m["role"], m["text"])
{!--< /tips >!--}
"""

import asyncio
import atexit
import threading
import time
from collections import deque
from typing import Any

from .constants import (
    DEFAULT_TRANSCRIPT_ENABLED,
    DEFAULT_TRANSCRIPT_MAX_PER_SESSION,
    DEFAULT_TRANSCRIPT_TTL_HOURS,
    TRANSCRIPT_BUFFER_MAX_ROWS,
    TRANSCRIPT_EXIT_FLUSH_TIMEOUT_SECS,
    TRANSCRIPT_FLUSH_INTERVAL_SECS,
    TRANSCRIPT_FLUSH_MAX_BATCH,
    TRANSCRIPT_TABLE,
)
from .i18n import i18n
from .logger import logger
from .storage import storage

# 入站/出站文本预览的最大保留长度（字符）
TRANSCRIPT_TEXT_MAX_CHARS = 2000



_MODULE_RETENTION_INTERVAL = 32


class TranscriptManager:
    """
    会话收件箱管理器

    以 ``platform:detail_type:target_id`` 为会话键记录消息流，
    存储于独立 SQLite 表，支持条数上限与 TTL 双重保留策略。

    写入路径为"内存缓冲 + 后台批量落盘"：``append`` 仅入队（微秒级，
    不阻塞分发热路径），后台任务按条数 / 时间阈值批量事务提交；
    查询接口自动合并未落盘的缓冲行（同进程读你的写）。
    """

    # 保留策略：每 N 次追加触发一次过期清理
    _RETENTION_INTERVAL = _MODULE_RETENTION_INTERVAL
    # 退出兜底刷盘的看门狗上限（秒）：超时放弃，保证进程退出不被存储桥阻塞
    _exit_flush_timeout: float = TRANSCRIPT_EXIT_FLUSH_TIMEOUT_SECS

    def __init__(self):
        self._table_ready: bool = False
        self._append_count: int = 0
        self._attached: bool = False
        self._next_retention_at: int = self._RETENTION_INTERVAL
        # 批量落盘状态
        self._buffer: deque[dict[str, Any]] = deque()
        self._buffer_lock = threading.Lock()
        self._flusher_started: bool = False
        self._flushing: bool = False
        self._atexit_registered: bool = False
        self._hooks_registered: bool = False
        self._cfg_cache: dict[str, Any] | None = None

    # ==================== 配置 ====================

    def _config(self) -> dict[str, Any]:
        """{!--< internal-use >!--} 读取 transcript 配置节（轻量缓存，配置事件失效）"""
        if self._cfg_cache is not None:
            return self._cfg_cache
        try:
            from ..runtime.frame_config import get_erispulse_config

            cfg = get_erispulse_config().get("transcript", {})
            cfg = cfg if isinstance(cfg, dict) else {}
        except Exception:
            cfg = {}
        self._cfg_cache = cfg
        self._ensure_hooks()
        return cfg

    def _invalidate_config_cache(self, data: Any = None) -> None:
        """{!--< internal-use >!--} transcript 相关配置写入 / 配置重载时失效缓存"""
        try:
            key = data.get("key", "") if isinstance(data, dict) else ""
            if not key or key.startswith("ErisPulse.transcript"):
                self._cfg_cache = None
        except Exception:
            pass

    def _ensure_hooks(self) -> None:
        """{!--< internal-use >!--} 惰性注册配置失效监听与退出刷盘（各一次）"""
        if self._hooks_registered:
            return
        self._hooks_registered = True
        try:
            from .lifecycle import lifecycle

            lifecycle.on("config.set")(self._invalidate_config_cache)
            lifecycle.on("config.updated")(self._invalidate_config_cache)
        except Exception:
            pass
        if not self._atexit_registered:
            self._atexit_registered = True
            try:
                atexit.register(self._flush_on_exit)
            except Exception:
                pass

    def _flush_on_exit(self) -> None:
        """
        {!--< internal-use >!--}
        进程退出兜底：同步刷掉未落盘缓冲（镜像 config._flush_on_exit）

        以看门狗线程限时执行——解释器收尾阶段存储同步桥的后台线程可能已
        无法调度（自由线程构建下尤其如此），在 atexit 里直接走同步桥会
        永久阻塞、令进程退出挂死；超时即放弃（至多丢一批缓冲），保证
        退出必然完成。缓冲为空时刷盘立即返回，无任何开销。
        """
        def _run():
            try:
                self.flush()
            except Exception:
                pass

        watchdog = threading.Thread(
            target=_run, daemon=True, name="transcript-exit-flush"
        )
        watchdog.start()
        watchdog.join(timeout=self._exit_flush_timeout)

    @property
    def enabled(self) -> bool:
        """是否启用自动记录（ErisPulse.transcript.enabled）"""
        return bool(self._config().get("enabled", DEFAULT_TRANSCRIPT_ENABLED))

    # ==================== 会话键 ====================

    @staticmethod
    def session_key_from_event(event: Any) -> str:
        """
        从事件推导会话键（platform:detail_type:target_id）

        target 语义与交互会话等待键一致（复用 session_type 的目标推导，
        私聊为 user_id，群聊 / 频道等对应目标 ID）。

        :param event: 事件数据（Event 或 dict）
        :return: 会话键字符串
        """
        from .Event.session_type import get_target_id

        platform = str(event.get("platform") or "")
        detail_type = str(event.get("detail_type") or "")
        target_id = str(get_target_id(event, event.get("platform")) or "")
        return f"{platform}:{detail_type}:{target_id}"

    @staticmethod
    def _ctx_key(ctx: dict) -> str:
        """{!--< internal-use >!--} 从 message.sent 发送上下文推导会话键"""
        return (
            f"{ctx.get('platform') or ''}:{ctx.get('detail_type') or ''}:"
            f"{ctx.get('target_id') or ''}"
        )

    # ==================== 存储 ====================

    def _ensure_table(self) -> bool:
        """{!--< internal-use >!--} 惰性建表（含旧表 sender 列迁移）"""
        if self._table_ready:
            return True
        try:
            if not storage.HasTable(TRANSCRIPT_TABLE):
                storage.CreateTable(
                    TRANSCRIPT_TABLE,
                    {
                        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                        "session_key": "TEXT NOT NULL",
                        "event_id": "TEXT DEFAULT ''",
                        "role": "TEXT NOT NULL",
                        "sender": "TEXT DEFAULT ''",
                        "text": "TEXT DEFAULT ''",
                        "ts": "REAL NOT NULL",
                    },
                )
            else:
                self._migrate_add_sender()
            self._table_ready = True
            return True
        except Exception as e:
            logger.trace(i18n.t("core.transcript.table_failed", error=e))
            return False

    async def _aensure_table(self) -> bool:
        """{!--< internal-use >!--} 惰性建表（异步路径，flusher 使用）"""
        if self._table_ready:
            return True
        try:
            if not await storage.aHasTable(TRANSCRIPT_TABLE):
                await storage.aCreateTable(
                    TRANSCRIPT_TABLE,
                    {
                        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                        "session_key": "TEXT NOT NULL",
                        "event_id": "TEXT DEFAULT ''",
                        "role": "TEXT NOT NULL",
                        "sender": "TEXT DEFAULT ''",
                        "text": "TEXT DEFAULT ''",
                        "ts": "REAL NOT NULL",
                    },
                )
            else:
                await self._amigrate_add_sender()
            self._table_ready = True
            return True
        except Exception as e:
            logger.trace(i18n.t("core.transcript.table_failed", error=e))
            return False

    def _migrate_add_sender(self) -> None:
        """{!--< internal-use >!--} 旧表缺 sender 列时自动补列（2.8.0 新增）"""
        try:
            # 探测：sender 列可查询即无需迁移（避免 duplicate column 告警）
            storage.Table(TRANSCRIPT_TABLE).Select("sender").Limit(1).Execute()
            return
        except Exception:
            pass
        try:
            storage.AlterTable(TRANSCRIPT_TABLE).AddColumn("sender", "TEXT DEFAULT ''").Execute()
        except Exception:
            pass  # 后端不支持 ALTER——静默降级（sender 仅回放增强用）

    async def _amigrate_add_sender(self) -> None:
        """{!--< internal-use >!--} 异步路径的 sender 列迁移探测（列缺失时回退同步 ALTER）"""
        try:
            columns = await storage.aGetTableColumns(TRANSCRIPT_TABLE)
            if "sender" in columns:
                return
        except Exception:
            return  # 列探测不可用时保持原表结构，静默降级
        try:
            storage.AlterTable(TRANSCRIPT_TABLE).AddColumn("sender", "TEXT DEFAULT ''").Execute()
        except Exception:
            pass  # 后端不支持 ALTER——静默降级（sender 仅回放增强用）

    def _retention(self, session_key: str, max_per_session: int, ttl_hours: float) -> None:
        """{!--< internal-use >!--} 保留策略：每会话条数上限 + 全局 TTL（惰性触发，覆盖库与内存缓冲）"""
        try:
            # 内存缓冲同会话裁剪：保持最旧淘汰语义与库内一致
            with self._buffer_lock:
                if max_per_session > 0:
                    session_rows = [r for r in self._buffer if r.get("session_key") == session_key]
                    overflow = len(session_rows) - max_per_session
                    if overflow > 0:
                        drop_ids = {id(r) for r in session_rows[:overflow]}
                        self._buffer = deque(r for r in self._buffer if id(r) not in drop_ids)
            table = storage.Table(TRANSCRIPT_TABLE)
            # 派生表包裹 LIMIT 子查询：MySQL/MariaDB 不支持 IN 子查询内直接 LIMIT
            table.Delete().Where("session_key = ?", session_key).Where(
                "id NOT IN (SELECT id FROM (SELECT id FROM "
                + TRANSCRIPT_TABLE
                + " WHERE session_key = ? ORDER BY id DESC LIMIT ?) AS _keep)",
                session_key,
                max_per_session,
            ).Execute()
            if ttl_hours > 0:
                cutoff = time.time() - ttl_hours * 3600.0
                storage.Table(TRANSCRIPT_TABLE).Delete().Where("ts < ?", cutoff).Execute()
        except Exception as e:
            logger.trace(i18n.t("core.transcript.retention_failed", error=e))

    # ==================== 批量落盘 ====================

    def _ensure_flusher(self) -> None:
        """{!--< internal-use >!--} 首次在事件循环内追加时启动后台刷盘任务"""
        if self._flusher_started:
            return
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return  # 无运行中的循环（同步测试环境）：保持缓冲，由读合并 / 显式 flush 兜底
        with self._buffer_lock:
            if self._flusher_started:
                return
            self._flusher_started = True
        try:
            from ..runtime.tasks import spawn_background

            spawn_background(self._flush_loop(), owner="transcript")
        except Exception:
            with self._buffer_lock:
                self._flusher_started = False

    async def _flush_loop(self) -> None:
        """{!--< internal-use >!--} 周期刷盘循环：按时间阈值批量提交，积压时连续排空"""
        while True:
            await asyncio.sleep(TRANSCRIPT_FLUSH_INTERVAL_SECS)
            try:
                while True:
                    with self._buffer_lock:
                        pending = len(self._buffer)
                    if not pending:
                        break
                    if not await self._flush_async():
                        break  # 本轮失败（如存储冷却期），下个周期重试
            except asyncio.CancelledError:
                raise
            except Exception:
                pass

    def _take_batch(self) -> list[dict[str, Any]]:
        """{!--< internal-use >!--} 从缓冲头部取一批待落盘行"""
        with self._buffer_lock:
            n = min(len(self._buffer), TRANSCRIPT_FLUSH_MAX_BATCH)
            return [self._buffer.popleft() for _ in range(n)]

    async def _flush_async(self) -> bool:
        """
        {!--< internal-use >!--} 异步批量落盘一批缓冲行（单事务原子提交）

        :return: 是否成功（失败时批次已回插缓冲头部，等待下轮重试）
        """
        rows = self._take_batch()
        if not rows:
            return True
        try:
            if not await self._aensure_table():
                self._requeue(rows)
                return False
            async with storage.atransaction():
                await storage.Table(TRANSCRIPT_TABLE).InsertMulti(rows).aExecute()
        except asyncio.CancelledError:
            self._requeue(rows)
            raise
        except Exception as e:
            self._requeue(rows)
            logger.trace(i18n.t("core.transcript.append_failed", error=e))
            return False

        self._append_count += len(rows)
        while self._append_count >= self._next_retention_at:
            cfg = self._config()
            self._next_retention_at = self._append_count + self._RETENTION_INTERVAL
            self._retention(
                rows[-1]["session_key"],
                int(cfg.get("max_per_session", DEFAULT_TRANSCRIPT_MAX_PER_SESSION)),
                float(cfg.get("ttl_hours", DEFAULT_TRANSCRIPT_TTL_HOURS)),
            )
        return True

    def _requeue(self, rows: list[dict[str, Any]]) -> None:
        """{!--< internal-use >!--} 落盘失败 / 被取消时把批次回插缓冲头部（保证不丢）"""
        with self._buffer_lock:
            self._buffer.extendleft(reversed(rows))

    async def aflush(self) -> int:
        """
        异步刷掉当前全部未落盘缓冲（框架卸载时调用）

        :return: 实际落盘的记录数

        :example:
        >>> await transcript.aflush()
        """
        count = 0
        while True:
            with self._buffer_lock:
                pending = len(self._buffer)
            if not pending:
                break
            if not await self._flush_async():
                break
            count += min(pending, TRANSCRIPT_FLUSH_MAX_BATCH)
        return count

    def flush(self) -> int:
        """
        同步刷掉当前全部未落盘缓冲（进程退出兜底 / 手动调用）

        :return: 实际落盘的记录数

        :example:
        >>> transcript.flush()
        """
        if self._flushing:
            return 0
        self._flushing = True
        try:
            count = 0
            while True:
                rows = self._take_batch()
                if not rows:
                    break
                try:
                    if not self._ensure_table():
                        self._requeue(rows)
                        break
                    with storage.transaction():
                        storage.Table(TRANSCRIPT_TABLE).InsertMulti(rows).Execute()
                except Exception as e:
                    self._requeue(rows)
                    logger.trace(i18n.t("core.transcript.append_failed", error=e))
                    break
                count += len(rows)
            return count
        finally:
            self._flushing = False

    # ==================== 公共 API ====================

    def append(
        self,
        session: Any,
        role: str,
        text: str,
        event_id: str = "",
        sender: str = "",
    ) -> bool:
        """
        记录一条消息到会话收件箱

        仅入内存缓冲即返回（微秒级，不阻塞分发热路径）；由后台任务批量
        落盘（延迟至多 ``TRANSCRIPT_FLUSH_INTERVAL_SECS`` 秒），查询接口
        会自动合并未落盘的缓冲行。

        :param session: 事件数据（Event / dict，自动推导会话键）或会话键字符串
        :param role: 消息角色（"user" / "bot"）
        :param text: 消息文本（超长自动截断）
        :param event_id: 关联的事件 ID（可选）
        :param sender: 发送者标识（user_id，可选，回放时还原消息来源）
        :return: 是否接受（未启用时返回 False；缓冲超限时淘汰最旧行）

        :example:
        >>> transcript.append(event, "user", "你好")
        """
        if not self.enabled:
            return False

        key = session if isinstance(session, str) else self.session_key_from_event(session)
        if len(text) > TRANSCRIPT_TEXT_MAX_CHARS:
            text = text[:TRANSCRIPT_TEXT_MAX_CHARS]

        with self._buffer_lock:
            if len(self._buffer) >= TRANSCRIPT_BUFFER_MAX_ROWS:
                self._buffer.popleft()  # 存储不可用时的积压保护：淘汰最旧行
            self._buffer.append(
                {
                    "session_key": key,
                    "event_id": str(event_id or ""),
                    "role": role,
                    "sender": str(sender or ""),
                    "text": text,
                    "ts": time.time(),
                }
            )
        self._ensure_flusher()
        return True

    def _merged(
        self,
        rows: list[dict[str, Any]],
        *,
        session_key: str | None = None,
        event_id: str | None = None,
        since_ts: float | None = None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """
        {!--< internal-use >!--} 合并数据库行与未落盘缓冲行（read-your-writes）

        :param rows: 数据库查询结果（任意顺序）
        :param session_key: 会话键过滤（None 不过滤）
        :param event_id: 链路 ID 过滤（None 不过滤）
        :param since_ts: 时间下界过滤（None 不过滤）
        :param limit: 返回最新 ``limit`` 条（时间升序输出）
        """
        merged = list(rows)
        with self._buffer_lock:
            buffered = list(self._buffer)
        for r in buffered:
            if session_key is not None and r.get("session_key") != session_key:
                continue
            if event_id is not None and r.get("event_id") != event_id:
                continue
            if since_ts is not None and float(r.get("ts") or 0.0) <= since_ts:
                continue
            merged.append(r)
        merged.sort(key=lambda r: float(r.get("ts") or 0.0))
        if limit > 0 and len(merged) > limit:
            merged = merged[-limit:]
        return merged

    def get(self, session: Any, n: int = 20) -> list[dict[str, Any]]:
        """
        查询会话近期消息（按时间升序，含未落盘的缓冲行）

        :param session: 事件数据或会话键字符串
        :param n: 返回的最大条数
        :return: 消息列表，每条含 role / text / ts / event_id；无记录时返回空列表

        :example:
        >>> messages = transcript.get(event, 20)
        >>> for m in messages:
        ...     print(m["role"], ":", m["text"])
        """
        key = session if isinstance(session, str) else self.session_key_from_event(session)
        rows: list[dict[str, Any]] = []
        if self._ensure_table():
            try:
                result: Any = (
                    storage.Table(TRANSCRIPT_TABLE)
                    .Select("role", "text", "ts", "event_id", "session_key")
                    .Where("session_key = ?", key)
                    .OrderBy("ts", desc=True)
                    .Limit(max(1, int(n)))
                    .ToDict()
                    .Execute()
                )
                rows = result if isinstance(result, list) else []
            except Exception as e:
                logger.trace(i18n.t("core.transcript.get_failed", error=e))
                rows = []
        return [
            {
                "role": r.get("role", ""),
                "text": r.get("text", ""),
                "ts": r.get("ts", 0.0),
                "event_id": r.get("event_id", ""),
            }
            for r in self._merged(rows, session_key=key, limit=max(1, int(n)))
            if isinstance(r, dict)
        ]

    def recent(self, seconds: float, limit: int = 200) -> list[dict[str, Any]]:
        """
        查询全部会话中最近一段时间内的消息（跨会话，按时间升序，含未落盘缓冲行）

        冷启动回放（``get_load_strategy(replay=...)``）的数据源；
        每条记录额外携带 ``session_key``，用于还原消息来源会话。
        窗口内记录超过 ``limit`` 时返回最新的 ``limit`` 条。

        :param seconds: 回溯时长（秒）
        :param limit: 最大返回条数（防止模块冷启动被打爆）
        :return: 消息列表（role / text / ts / sender / session_key）

        :example:
        >>> transcript.recent(300)  # 最近 5 分钟
        """
        cutoff = time.time() - max(0.0, float(seconds))
        rows: list[dict[str, Any]] = []
        if self._ensure_table():
            try:
                result: Any = (
                    storage.Table(TRANSCRIPT_TABLE)
                    .Select("role", "text", "ts", "sender", "session_key")
                    .Where("ts > ?", cutoff)
                    .OrderBy("ts", desc=True)
                    .Limit(max(1, int(limit)))
                    .ToDict()
                    .Execute()
                )
                rows = result if isinstance(result, list) else []
            except Exception as e:
                logger.trace(i18n.t("core.transcript.get_failed", error=e))
                rows = []
        return [
            {
                "role": r.get("role", ""),
                "text": r.get("text", ""),
                "ts": r.get("ts", 0.0),
                "sender": r.get("sender", ""),
                "session_key": r.get("session_key", ""),
            }
            for r in self._merged(rows, since_ts=cutoff, limit=max(1, int(limit)))
            if isinstance(r, dict)
        ]

    def clear(self, session: Any) -> int:
        """
        清空指定会话的收件箱（同时清除未落盘缓冲中的该会话记录）

        :param session: 事件数据或会话键字符串
        :return: 删除的记录数

        :example:
        >>> transcript.clear(event)
        """
        key = session if isinstance(session, str) else self.session_key_from_event(session)
        buffered = 0
        with self._buffer_lock:
            remaining = deque()
            for r in self._buffer:
                if r.get("session_key") == key:
                    buffered += 1
                else:
                    remaining.append(r)
            self._buffer = remaining
        try:
            result = (
                storage.Table(TRANSCRIPT_TABLE)
                .Delete()
                .Where("session_key = ?", key)
                .Execute()
            )
            # Delete 链返回受影响行数 int；isinstance 守卫类型收窄
            db_deleted = int(result) if isinstance(result, int) and result else 0
        except Exception as e:
            logger.trace(i18n.t("core.transcript.clear_failed", error=e))
            db_deleted = 0
        return db_deleted + buffered

    # ==================== 出站自动记录 ====================

    def attach(self) -> bool:
        """
        挂接出站自动记录（message.sent 钩子，框架初始化时调用）

        重复调用安全；未启用时跳过注册（运行时改为启用需重启或重新 attach）。

        :return: 是否成功挂接
        """
        if self._attached:
            return True
        try:
            from .lifecycle import lifecycle

            lifecycle.register("message.sent", self._on_message_sent)
            self._attached = True
            return True
        except Exception as e:
            logger.trace(i18n.t("core.transcript.attach_failed", error=e))
            return False

    async def _on_message_sent(self, data: Any) -> None:
        """{!--< internal-use >!--} message.sent 钩子：记录机器人出站文本"""
        if not self.enabled or not isinstance(data, dict):
            return
        preview = data.get("preview")
        if not preview:
            return
        target_id = data.get("target_id") or ""
        if not target_id:
            return
        # event_id 落 trace_id：影子 diff（方向十一）按链路 ID 对齐
        # 影子意向发送与真实发送时间线
        self.append(
            self._ctx_key(data),
            "bot",
            str(preview),
            event_id=str(data.get("trace_id") or ""),
            sender=str(data.get("bot_id") or ""),
        )

    def get_by_trace(self, trace_id: str, limit: int = 20) -> "list[dict[str, Any]]":
        """
        按链路 ID 查询出站记录（影子模块 diff 对齐用，方向十一，含未落盘缓冲行）

        :param trace_id: 事件链路 ID（事件 ``id``）
        :param limit: 返回的最大条数
        :return: 消息列表（role / text / ts / event_id），时间升序

        :example:
        >>> transcript.get_by_trace("evt-abc123")
        """
        if not trace_id:
            return []
        rows: list[dict[str, Any]] = []
        if self._ensure_table():
            try:
                result: Any = (
                    storage.Table(TRANSCRIPT_TABLE)
                    .Select("role", "text", "ts", "event_id", "session_key")
                    .Where("event_id = ?", str(trace_id))
                    .OrderBy("ts", desc=True)
                    .Limit(max(1, int(limit)))
                    .ToDict()
                    .Execute()
                )
                rows = result if isinstance(result, list) else []
            except Exception as e:
                logger.trace(i18n.t("core.transcript.get_failed", error=e))
                rows = []
        return [
            {
                "role": r.get("role", ""),
                "text": r.get("text", ""),
                "ts": r.get("ts", 0.0),
                "event_id": r.get("event_id", ""),
            }
            for r in self._merged(rows, event_id=str(trace_id), limit=max(1, int(limit)))
            if isinstance(r, dict)
        ]


transcript: TranscriptManager = TranscriptManager()

__all__ = ["TranscriptManager", "transcript"]
