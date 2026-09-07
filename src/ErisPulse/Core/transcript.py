"""
ErisPulse 会话收件箱（transcript）

提供每会话近期消息流的统一记录与查询，作为上下文记忆类模块
（AI 对话、防复读、行为分析等）的公共底座：

- **入站**：消息事件进入分发管线时自动记录（role="user"）；
- **出站**：机器人发送的文本类消息经 ``message.sent`` 钩子自动记录（role="bot"）；
- **存储**：独立 SQLite 表（经 storage），每会话条数上限 + 全局 TTL 自动清理；
- **查询**：``event.history(n)`` 或 ``sdk.transcript.get(event, n)``。

{!--< tips >!--}
配置（``ErisPulse.transcript``）::

    [ErisPulse.transcript]
    enabled = true          # 是否启用（关闭后停止写入，历史仍可查询）
    max_per_session = 50    # 每会话保留的最大条数
    ttl_hours = 168         # 全局过期时间（小时），过期记录惰性清理

使用方式::

    from ErisPulse.Core import transcript

    # 查询当前会话最近 20 条消息（含用户与机器人）
    messages = await event.history(20)   # 或 transcript.get(event, 20)
    for m in messages:
        print(m["role"], m["text"])
{!--< /tips >!--}
"""

import time
from typing import Any

from .constants import (
    DEFAULT_TRANSCRIPT_ENABLED,
    DEFAULT_TRANSCRIPT_MAX_PER_SESSION,
    DEFAULT_TRANSCRIPT_TTL_HOURS,
    TRANSCRIPT_TABLE,
)
from .i18n import i18n
from .logger import logger
from .storage import storage

# 入站/出站文本预览的最大保留长度（字符）
TRANSCRIPT_TEXT_MAX_CHARS = 2000

# 保留清理的触发间隔（每 N 次 append 执行一次，避免高频清理）
_RETENTION_INTERVAL = 32


class TranscriptManager:
    """
    会话收件箱管理器

    以 ``platform:detail_type:target_id`` 为会话键记录消息流，
    存储于独立 SQLite 表，支持条数上限与 TTL 双重保留策略。
    """

    def __init__(self):
        self._table_ready: bool = False
        self._append_count: int = 0
        self._attached: bool = False

    # ==================== 配置 ====================

    def _config(self) -> dict[str, Any]:
        """{!--< internal-use >!--} 读取 transcript 配置节"""
        try:
            from ..runtime.frame_config import get_erispulse_config

            cfg = get_erispulse_config().get("transcript", {})
            return cfg if isinstance(cfg, dict) else {}
        except Exception:
            return {}

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
        """{!--< internal-use >!--} 惰性建表"""
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
                        "text": "TEXT DEFAULT ''",
                        "ts": "REAL NOT NULL",
                    },
                )
            self._table_ready = True
            return True
        except Exception as e:
            logger.trace(i18n.t("core.transcript.table_failed", error=e))
            return False

    def _retention(self, session_key: str, max_per_session: int, ttl_hours: float) -> None:
        """{!--< internal-use >!--} 保留策略：每会话条数上限 + 全局 TTL（惰性触发）"""
        try:
            table = storage.Table(TRANSCRIPT_TABLE)
            table.Delete().Where("session_key = ?", session_key).Where(
                "id NOT IN (SELECT id FROM "
                + TRANSCRIPT_TABLE
                + " WHERE session_key = ? ORDER BY id DESC LIMIT ?)",
                session_key,
                max_per_session,
            ).Execute()
            if ttl_hours > 0:
                cutoff = time.time() - ttl_hours * 3600.0
                storage.Table(TRANSCRIPT_TABLE).Delete().Where("ts < ?", cutoff).Execute()
        except Exception as e:
            logger.trace(i18n.t("core.transcript.retention_failed", error=e))

    # ==================== 公共 API ====================

    def append(
        self,
        session: Any,
        role: str,
        text: str,
        event_id: str = "",
    ) -> bool:
        """
        记录一条消息到会话收件箱

        :param session: 事件数据（Event / dict，自动推导会话键）或会话键字符串
        :param role: 消息角色（"user" / "bot"）
        :param text: 消息文本（超长自动截断）
        :param event_id: 关联的事件 ID（可选）
        :return: 是否写入成功（未启用时返回 False）

        :example:
        >>> transcript.append(event, "user", "你好")
        """
        if not self.enabled:
            return False
        if not self._ensure_table():
            return False

        key = session if isinstance(session, str) else self.session_key_from_event(session)
        if len(text) > TRANSCRIPT_TEXT_MAX_CHARS:
            text = text[:TRANSCRIPT_TEXT_MAX_CHARS]
        ts = time.time()
        try:
            storage.Table(TRANSCRIPT_TABLE).Insert(
                {
                    "session_key": key,
                    "event_id": str(event_id or ""),
                    "role": role,
                    "text": text,
                    "ts": ts,
                }
            ).Execute()
        except Exception as e:
            logger.trace(i18n.t("core.transcript.append_failed", error=e))
            return False

        # 惰性保留清理
        self._append_count += 1
        if self._append_count % _RETENTION_INTERVAL == 0:
            cfg = self._config()
            self._retention(
                key,
                int(cfg.get("max_per_session", DEFAULT_TRANSCRIPT_MAX_PER_SESSION)),
                float(cfg.get("ttl_hours", DEFAULT_TRANSCRIPT_TTL_HOURS)),
            )
        return True

    def get(self, session: Any, n: int = 20) -> list[dict[str, Any]]:
        """
        查询会话近期消息（按时间升序）

        :param session: 事件数据或会话键字符串
        :param n: 返回的最大条数
        :return: 消息列表，每条含 role / text / ts / event_id；无记录时返回空列表

        :example:
        >>> messages = transcript.get(event, 20)
        >>> for m in messages:
        ...     print(m["role"], ":", m["text"])
        """
        if not self._ensure_table():
            return []
        key = session if isinstance(session, str) else self.session_key_from_event(session)
        try:
            rows = (
                storage.Table(TRANSCRIPT_TABLE)
                .Select("role", "text", "ts", "event_id")
                .Where("session_key = ?", key)
                .OrderBy("ts", desc=True)
                .Limit(max(1, int(n)))
                .ToDict()
                .Execute()
            )
            if not isinstance(rows, list):
                return []
            return [
                {
                    "role": r.get("role", ""),
                    "text": r.get("text", ""),
                    "ts": r.get("ts", 0.0),
                    "event_id": r.get("event_id", ""),
                }
                for r in reversed(rows)
                if isinstance(r, dict)
            ]
        except Exception as e:
            logger.trace(i18n.t("core.transcript.get_failed", error=e))
            return []

    def clear(self, session: Any) -> int:
        """
        清空指定会话的收件箱

        :param session: 事件数据或会话键字符串
        :return: 删除的记录数

        :example:
        >>> transcript.clear(event)
        """
        if not self._ensure_table():
            return 0
        key = session if isinstance(session, str) else self.session_key_from_event(session)
        try:
            result = (
                storage.Table(TRANSCRIPT_TABLE)
                .Delete()
                .Where("session_key = ?", key)
                .Execute()
            )
            return int(result) if result else 0
        except Exception as e:
            logger.trace(i18n.t("core.transcript.clear_failed", error=e))
            return 0

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
        self.append(self._ctx_key(data), "bot", str(preview))


transcript: TranscriptManager = TranscriptManager()

__all__ = ["TranscriptManager", "transcript"]
