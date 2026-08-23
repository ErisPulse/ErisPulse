"""
ErisPulse 作用域系统

提供模块与适配器 Bot / 平台 / 会话之间的绑定能力，控制"某个 Bot 只能使用哪些模块"。
默认情况下所有模块对所有 Bot 开放；仅在配置了绑定后才开始过滤，完全向后兼容，
模块与适配器无需任何改动即可适配作用域。

作用域配置位于 ``ErisPulse.scope``，支持三级绑定：

1. **平台级**（作用于该平台所有 Bot / 会话）：
   ``ErisPulse.scope.platforms.<platform>.modules / blocked``
2. **Bot 级**（作用于该 Bot 的所有会话）：
   ``ErisPulse.scope.bots.<platform>.<bot_id>.modules / blocked``
3. **会话级**（最具体，作用于某个群 / 频道 / 私聊）：
   ``ErisPulse.scope.sessions.<platform>.<session_id>.modules / blocked``

解析优先级：**会话级 > Bot 级 > 平台级**。模块名匹配**大小写不敏感**。

语义：
- ``modules``（白名单）非空时，只有列出的模块允许使用
- ``blocked``（黑名单）中的模块被禁用
- 两者均未配置时，遵循 ``default_allow``（默认允许全部；设为 false 则隐式拒绝）
- 被作用域禁用的模块收到消息时静默忽略，不回复提示

{!--< tips >!--}
1. 通过 ``from ErisPulse.Core import scope`` 导入单例
2. ``scope.is_allowed(platform, bot_id, module, session_id)`` 判断模块是否可用
3. ``scope.bind()`` 默认替换绑定，``merge=True`` 可合并
4. ``scope.get_stats()`` 查看过滤统计（调试被静默忽略的模块）
5. ``scope.default_allow`` 设为 false 可开启"隐式拒绝"严格模式
{!--< /tips >!--}
"""

from collections import OrderedDict

from ..runtime.frame_config import update_erispulse_config

# 三个绑定桶：platforms / bots / sessions
_BUCKET_PLATFORMS = "platforms"
_BUCKET_BOTS = "bots"
_BUCKET_SESSIONS = "sessions"

# 默认 LRU 缓存大小
DEFAULT_CACHE_SIZE = 1024


class ScopeManager:
    """
    作用域管理器（单例）

    从配置读取模块-Bot/平台/会话绑定，并支持运行时增删。
    判断逻辑：会话级绑定优先于 Bot 级，Bot 级优先于平台级，均未配置时遵循 default_allow。
    """

    def __init__(self, cache_size: int = DEFAULT_CACHE_SIZE):
        self._cache_size = max(1, int(cache_size))
        # 内存中的绑定缓存（随配置热更新重建）
        self._bindings: dict[str, dict] = {
            _BUCKET_PLATFORMS: {},
            _BUCKET_BOTS: {},
            _BUCKET_SESSIONS: {},
        }
        self._default_allow: bool = True
        self._stats: dict[str, int] = {
            "is_allowed_calls": 0,
            "filtered_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        # is_allowed 的 LRU 结果缓存：(platform, bot_id, session_id, module) -> bool
        self._cache: OrderedDict[tuple, bool] = OrderedDict()
        self._load_bindings()
        # 订阅配置热更新：scope 配置变更时自动重建绑定缓存
        try:
            from .lifecycle import lifecycle

            lifecycle.register("config.updated", self._on_config_updated)
            lifecycle.register("config.set", self._on_config_updated)
        except Exception:
            pass

    # ==================== 配置加载与热更新 ====================

    def _load_bindings(self) -> None:
        """{!--< internal-use >!--} 从配置加载绑定缓存"""
        try:
            from ..runtime import get_config

            scope_config = get_config("scope") or {}
        except Exception:
            scope_config = {}
        self._default_allow = bool(scope_config.get("default_allow", True))
        platforms = scope_config.get(_BUCKET_PLATFORMS) or {}
        bots = scope_config.get(_BUCKET_BOTS) or {}
        sessions = scope_config.get(_BUCKET_SESSIONS) or {}
        self._bindings = {
            _BUCKET_PLATFORMS: dict(platforms) if isinstance(platforms, dict) else {},
            _BUCKET_BOTS: dict(bots) if isinstance(bots, dict) else {},
            _BUCKET_SESSIONS: dict(sessions) if isinstance(sessions, dict) else {},
        }
        self._invalidate_cache()

    def _on_config_updated(self, _data: dict) -> None:
        """配置变更回调：重建绑定缓存"""
        self._load_bindings()

    def _invalidate_cache(self) -> None:
        """{!--< internal-use >!--} 清空 LRU 结果缓存"""
        self._cache.clear()

    # ==================== 核心判断 ====================

    @staticmethod
    def _normalize(cfg: dict) -> tuple[set[str], set[str]]:
        """
        {!--< internal-use >!--}
        归一化绑定配置为 (白名单集合, 黑名单集合)

        模块名统一转小写，实现大小写不敏感匹配。

        :param cfg: 绑定配置字典（可含 modules / blocked 字段）
        :return: (modules 集合, blocked 集合)
        """
        modules = cfg.get("modules") or []
        blocked = cfg.get("blocked") or []
        if isinstance(modules, str):
            modules = [modules]
        if isinstance(blocked, str):
            blocked = [blocked]
        return {str(m).lower() for m in modules}, {str(b).lower() for b in blocked}

    def _get_binding(
        self, platform: str, bot_id: str | None, session_id: str | None
    ) -> tuple[set[str], set[str]] | None:
        """
        {!--< internal-use >!--}
        获取平台 / Bot / 会话的生效绑定

        解析优先级：会话级 > Bot 级 > 平台级；均不存在时返回 None。

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 表示不匹配 Bot 级
        :param session_id: 会话 ID（群 / 频道 / 私聊），None 表示不匹配会话级
        :return: (allow, blocked) 或 None
        """
        if session_id:
            sessions = self._bindings.get(_BUCKET_SESSIONS, {})
            plat_sessions = sessions.get(platform)
            if isinstance(plat_sessions, dict):
                session_cfg = plat_sessions.get(session_id)
                if isinstance(session_cfg, dict):
                    return self._normalize(session_cfg)
        if bot_id:
            bots = self._bindings.get(_BUCKET_BOTS, {})
            plat_bots = bots.get(platform)
            if isinstance(plat_bots, dict):
                bot_cfg = plat_bots.get(bot_id)
                if isinstance(bot_cfg, dict):
                    return self._normalize(bot_cfg)
        platforms = self._bindings.get(_BUCKET_PLATFORMS, {})
        plat_cfg = platforms.get(platform)
        if isinstance(plat_cfg, dict):
            return self._normalize(plat_cfg)
        return None

    def is_allowed(
        self,
        platform: str,
        bot_id: str | None,
        module_name: str | None,
        session_id: str | None = None,
    ) -> bool:
        """
        判断模块是否允许在指定 Bot / 会话使用

        模块名匹配大小写不敏感。结果带 LRU 缓存，配置变更 / bind / unbind 时自动失效。
        无绑定（默认）时遵循 ``default_allow``（默认允许全部）；模块名为空（框架层资源）始终放行。

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 表示不匹配 Bot 级绑定
        :param module_name: 模块名称
        :param session_id: 会话 ID（群 / 频道 / 私聊），None 表示不匹配会话级绑定
        :return: 是否允许

        :example:
        >>> from ErisPulse.Core import scope
        >>> scope.is_allowed("onebot11", "123456", "Chat")
        True
        >>> scope.is_allowed("onebot11", "123456", "Chat", "group_9")
        True
        """
        if not module_name:
            return True
        self._stats["is_allowed_calls"] += 1

        platform = str(platform or "")
        bot_id = str(bot_id) if bot_id else None
        session_id = str(session_id) if session_id else None
        module_key = str(module_name).lower()

        cache_key = (platform, bot_id, session_id, module_key)
        cached = self._cache.get(cache_key)
        if cached is not None:
            self._stats["cache_hits"] += 1
            return cached
        self._stats["cache_misses"] += 1

        allowed = self._compute_allowed(platform, bot_id, session_id, module_key)
        self._put_cache(cache_key, allowed)
        if not allowed:
            self._stats["filtered_count"] += 1
            # TRACE 级别记录被过滤的模块（缓存命中不重复记录，不污染生产日志）
            from .i18n import i18n

            self._logger_trace(i18n.t("core.scope.denied", module=module_name))
        return allowed

    def _compute_allowed(
        self, platform: str, bot_id: str | None, session_id: str | None, module_key: str
    ) -> bool:
        """{!--< internal-use >!--} 计算模块是否允许（无缓存）"""
        binding = self._get_binding(platform, bot_id, session_id)
        if binding is None:
            return self._default_allow
        allow, blocked = binding
        if blocked and module_key in blocked:
            return False
        if allow:
            return module_key in allow
        return self._default_allow

    def _put_cache(self, key: tuple, value: bool) -> None:
        """{!--< internal-use >!--} 写入 LRU 缓存（超过容量时淘汰最旧）"""
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    @staticmethod
    def bot_id_from_event(event: dict) -> str:
        """
        从事件数据提取 Bot 标识

        :param event: 事件数据（dict 或 Event 包装对象）
        :return: Bot 标识（account_id 优先，回退 user_id），无法识别时返回空字符串
        """
        try:
            self_info = event.get("self") or {}
        except Exception:
            return ""
        if isinstance(self_info, dict):
            return str(self_info.get("account_id") or self_info.get("user_id") or "")
        return ""

    @staticmethod
    def session_id_from_event(event: dict) -> str:
        """
        从事件数据提取会话标识（群 / 频道 / 私聊的目标 ID）

        :param event: 事件数据（dict 或 Event 包装对象）
        :return: 会话 ID（如 group_id / channel_id / user_id），无法识别时返回空字符串
        """
        try:
            # 函数内导入避免 Core 初始化阶段的循环依赖
            from .Event.session_type import get_send_type_and_target_id

            _send_type, target_id = get_send_type_and_target_id(event)
            return str(target_id or "")
        except Exception:
            return ""

    # ==================== 运行时增删 ====================

    def get(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
    ) -> dict | None:
        """
        获取平台 / Bot / 会话的生效绑定

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 表示不匹配 Bot 级
        :param session_id: 会话 ID，None 表示不匹配会话级
        :return: {"modules": [...], "blocked": [...]}，无绑定时返回 None

        :example:
        >>> scope.get("onebot11", "123456")
        {"modules": ["Chat"], "blocked": []}
        >>> scope.get("onebot11", "123456", "group_9")
        {"modules": ["Chat"], "blocked": []}
        """
        binding = self._get_binding(
            platform or "", bot_id or None, session_id or None
        )
        if binding is None:
            return None
        allow, blocked = binding
        return {"modules": sorted(allow), "blocked": sorted(blocked)}

    def bind(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        *,
        modules: list[str] | None = None,
        blocked: list[str] | None = None,
        persist: bool = True,
        merge: bool = False,
    ) -> None:
        """
        绑定模块作用域

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 且 session_id 为空时表示平台级绑定
        :param session_id: 会话 ID（群 / 频道 / 私聊）。指定时绑定到该会话；
                           否则有 bot_id 时绑定到该 Bot；否则绑定到平台级
        :param modules: 白名单模块列表，None / 空列表表示不限制
        :param blocked: 黑名单模块列表，None / 空列表表示不限制
        :param persist: 是否持久化到配置文件 (默认: True)
                         为 False 时仅本次运行生效，重启后失效
        :param merge: 是否**合并**而非替换现有绑定（默认 False）。
                      merge=True 时，新模块并入现有白名单、新禁用并入现有黑名单；
                      merge=False（默认）时整体替换。

        :example:
        >>> scope.bind("onebot11", "123456", modules=["Chat"])
        >>> scope.bind("onebot11", "123456", "group_9", modules=["Chat"])  # 会话级
        >>> scope.bind("onebot11", blocked=["Danger"])  # 平台级黑名单
        >>> scope.bind("onebot11", "123456", [], [], persist=False)  # 仅运行时
        >>> scope.bind("onebot11", "123456", modules=["Music"], merge=True)  # 追加
        """
        binding = {
            "modules": list(modules or []),
            "blocked": list(blocked or []),
        }

        bucket, key = self._resolve_target(platform, bot_id, session_id)

        if merge:
            existing = self._raw_get(bucket, platform, key)
            if existing:
                existing_modules = {str(m) for m in existing.get("modules", [])}
                existing_blocked = {str(b) for b in existing.get("blocked", [])}
                existing_modules.update(str(m) for m in binding["modules"])
                existing_blocked.update(str(b) for b in binding["blocked"])
                binding = {
                    "modules": sorted(existing_modules),
                    "blocked": sorted(existing_blocked),
                }

        if not persist:
            section = self._bindings.setdefault(bucket, {})
            if bucket == _BUCKET_PLATFORMS:
                section[platform] = binding
            else:
                section.setdefault(platform, {})[key] = binding
            self._invalidate_cache()
            return

        current = self._raw_bindings()
        section = current.setdefault(bucket, {})
        if bucket == _BUCKET_PLATFORMS:
            section[platform] = binding
        else:
            section.setdefault(platform, {})[key] = binding
        update_erispulse_config({"scope": current})
        self._invalidate_cache()

    def unbind(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        persist: bool = True,
    ) -> bool:
        """
        移除平台 / Bot / 会话的作用域绑定（恢复为允许全部模块）

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 且 session_id 为空时表示移除平台级绑定
        :param session_id: 会话 ID。指定时移除会话级绑定；否则有 bot_id 时移除 Bot 级
        :param persist: 是否持久化移除 (默认: True)
        :return: 是否成功移除（不存在则返回 False）

        :example:
        >>> scope.unbind("onebot11", "123456")
        True
        >>> scope.unbind("onebot11", "123456", "group_9")  # 移除会话级绑定
        True
        """
        bucket, key = self._resolve_target(platform, bot_id, session_id)

        current = self._raw_bindings()
        if bucket == _BUCKET_PLATFORMS:
            platforms = current.get(_BUCKET_PLATFORMS, {})
            if platform not in platforms:
                return False
            del platforms[platform]
        else:
            section = current.get(bucket, {})
            plat = section.get(platform)
            if not isinstance(plat, dict) or key not in plat:
                return False
            del plat[key]
            if not plat:
                del section[platform]
        if persist:
            update_erispulse_config({"scope": current})
        else:
            self._load_bindings()
        self._invalidate_cache()
        return True

    def list_bindings(self) -> dict:
        """
        列出全部作用域绑定（含原始配置）

        :return: {"platforms": {...}, "bots": {...}, "sessions": {...}} 结构

        :example:
        >>> scope.list_bindings()
        {"platforms": {"onebot11": {"modules": ["Chat"]}}, "bots": {}, "sessions": {}}
        """
        return self._raw_bindings()

    def clear(self) -> None:
        """清空所有作用域绑定（运行时生效，不持久化）"""
        self._bindings = {
            _BUCKET_PLATFORMS: {},
            _BUCKET_BOTS: {},
            _BUCKET_SESSIONS: {},
        }
        self._invalidate_cache()

    # ==================== 统计与拓扑 ====================

    def get_stats(self) -> dict[str, int]:
        """
        获取作用域运行统计（便于调试被静默忽略的模块）

        统计项：``is_allowed_calls``（判断次数）、``filtered_count``（被过滤次数）、
        ``cache_hits`` / ``cache_misses``（LRU 缓存命中/未命中）。

        :return: 统计字典

        :example:
        >>> scope.get_stats()
        {"is_allowed_calls": 10, "filtered_count": 3, "cache_hits": 5, "cache_misses": 5}
        """
        return dict(self._stats)

    def reset_stats(self) -> None:
        """重置作用域运行统计"""
        for key in self._stats:
            self._stats[key] = 0

    def get_topology(self) -> dict:
        """
        获取作用域绑定的结构化数据（便于 WebUI 展示拓扑树）

        :return: {"platforms": {...}, "bots": {...}, "sessions": {...}}

        :example:
        >>> scope.get_topology()
        {"platforms": {"onebot11": {"modules": [...], "blocked": [...]}},
         "bots": {"onebot11": {"123456": {"modules": [...], "blocked": [...]}}},
         "sessions": {"onebot11": {"group_9": {"modules": [...], "blocked": [...]}}}}
        """
        return self._raw_bindings()

    # ==================== 工具方法 ====================

    def _raw_get(self, bucket: str, platform: str, key: str) -> dict | None:
        """{!--< internal-use >!--} 读取指定绑定（供 merge 使用，浅拷贝）"""
        section = self._bindings.get(bucket, {})
        if bucket == _BUCKET_PLATFORMS:
            cfg = section.get(platform)
        else:
            plat = section.get(platform)
            cfg = plat.get(key) if isinstance(plat, dict) else None
        return dict(cfg) if isinstance(cfg, dict) else None

    def _resolve_target(
        self, platform: str, bot_id: str | None, session_id: str | None
    ) -> tuple[str, str]:
        """
        {!--< internal-use >!--}
        根据参数解析目标绑定桶与键

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID
        :param session_id: 会话 ID
        :return: (bucket, key) 元组
        """
        if session_id:
            return _BUCKET_SESSIONS, str(session_id)
        if bot_id:
            return _BUCKET_BOTS, str(bot_id)
        return _BUCKET_PLATFORMS, platform

    @staticmethod
    def _logger_trace(message: str) -> None:
        """{!--< internal-use >!--} 输出 TRACE 日志（logger 未就绪时静默）"""
        try:
            from .logger import logger

            logger.trace(message)
        except (ImportError, AttributeError):
            pass

    def _raw_bindings(self) -> dict:
        """{!--< internal-use >!--} 读取当前绑定缓存（深拷贝，避免外部篡改）"""
        import copy

        return copy.deepcopy(self._bindings)

    def __repr__(self) -> str:
        platforms = list(self._bindings.get(_BUCKET_PLATFORMS, {}).keys())
        bots = list(self._bindings.get(_BUCKET_BOTS, {}).keys())
        sessions = list(self._bindings.get(_BUCKET_SESSIONS, {}).keys())
        return (
            f"<ScopeManager platforms={platforms} "
            f"bots={bots} sessions={sessions} default_allow={self._default_allow}>"
        )


# 模块级单例
scope: ScopeManager = ScopeManager()

__all__ = [
    "DEFAULT_CACHE_SIZE",
    "ScopeManager",
    "scope",
]
