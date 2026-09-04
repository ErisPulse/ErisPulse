"""
ErisPulse 统一控制面（scope）

控制权完全交给用户：在模块 / 适配器 / 命令 / 处理器注册的**上层**（配置 ``ErisPulse.scope``
或运行时 ``sdk.scope``）统一声明"谁 / 什么 / 什么条件下，允许或禁止"，以及覆盖
模块 / 命令的默认实现参数。事件管线在每一级自动读取并执行。

本系统是 2.8.0 的权限/访问控制**唯一**入口，收敛了原有的：

- 模块维度（原作用域三级绑定）
- 身份维度（原事件准入 access：适配器 / Bot / 会话 / 用户）
- 命令维度（原命令权限 ACL：按命令的用户黑白名单）
- 处理器/文本维度（新增：按模块过滤消息文本）
- 实现参数覆盖（新增：覆盖模块/命令的 master / hidden / aliases / prefix 等）
- 出站动作维度（新增：禁止模块发起消息发送 / 标准 API 动作 / 请求操作）

配置树（``ErisPulse.scope``）：

.. code-block:: toml

    [ErisPulse.scope]
    default_allow = true          # 全局兜底（未命中任何规则时放行/拒绝）

    # ① 模块维度：哪些模块可用（优先级 会话 > Bot > 平台）
    [ErisPulse.scope.platforms.onebot11]
    modules = ["Chat", "Tool*"]   # 精确名 / glob / re:正则
    blocked = ["re:^Danger"]
    [ErisPulse.scope.bots.onebot11."123456"]
    modules = ["Chat"]
    [ErisPulse.scope.sessions.onebot11."789012345"]
    modules = ["Chat"]

    # ② 身份维度：谁的事件收不收（优先级 用户 > 会话 > Bot > 适配器）
    [ErisPulse.scope.identity.adapters.onebot11]
    deny = true
    [ErisPulse.scope.identity.bots.onebot11."123456"]
    deny = true
    [ErisPulse.scope.identity.sessions.onebot11."g_blocked"]
    deny = true
    [ErisPulse.scope.identity.users.onebot11]
    allow = ["u_admin"]
    deny = ["u_bad", "spam_*"]    # 支持 glob / re:正则

    # ③ 命令维度：谁能执行某命令（命令名支持 glob）
    [ErisPulse.scope.commands."roll*"]
    allow = ["onebot11:u_vip"]
    deny = ["onebot11:u_bad"]

    # ④ 处理器/文本维度：某模块的事件处理器按 pattern / regex 过滤
    [ErisPulse.scope.handlers.MyModule]
    pattern = "签到*"
    regex = "re:\\d+\\s*元"

    # ⑤ 实现参数覆盖：覆盖模块/命令的默认实现参数（禁用走命令 deny）
    [ErisPulse.scope.overrides.MyModule.restart]
    master = true   hidden = true   aliases = ["rs"]   prefix = "!"

    # ⑥ 出站动作维度：禁止模块发起出站动作（默认全允许，显式禁用才收紧）
    [ErisPulse.scope.actions.MyModule]
    send = false      # 禁止 MyModule 回复/主动发消息（Event.reply / Send DSL）
    api = false       # 禁止 MyModule 调用标准 API 动作（Api DSL / call_api）
    request = false   # 禁止 MyModule 对请求事件执行 accept/reject

匹配条目统一语法（见 :mod:`ErisPulse.Core.text_match`）：
**精确名** / **glob**（``*`` / ``?`` / ``[seq]``）/ **``re:`` 正则**，默认大小写不敏感。

{!--< tips >!--}
1. 通过 ``from ErisPulse.Core import scope`` 导入单例（``sdk.scope`` 同对象）
2. ``scope.is_allowed(platform, bot_id, module, session_id)`` 判断模块是否可用
3. ``scope.is_identity_allowed(...)`` 判断事件是否放行（原 access）
4. ``scope.allow_user("roll*", platform, uid)`` 命令 ACL（命令名支持 glob）
5. ``scope.override("MyModule", "restart", master=True)`` 覆盖实现参数
6. ``scope.set_action("MyModule", "send", False)`` 禁止模块回复/发消息
7. ``scope.get_stats()`` 查看过滤统计
{!--< /tips >!--}
"""

from collections import OrderedDict
from collections.abc import Callable

from ..runtime.frame_config import set_erispulse_section, update_erispulse_config
from . import text_match

# 模块维度桶：platforms / bots / sessions（优先级 会话 > Bot > 平台）
_BUCKET_PLATFORMS = "platforms"
_BUCKET_BOTS = "bots"
_BUCKET_SESSIONS = "sessions"

# 身份维度桶：adapters / bots / sessions / users（优先级 用户 > 会话 > Bot > 适配器）
_IDENTITY_ADAPTERS = "adapters"
_IDENTITY_BOTS = "bots"
_IDENTITY_SESSIONS = "sessions"
_IDENTITY_USERS = "users"

# 默认 LRU 缓存大小
DEFAULT_CACHE_SIZE = 1024

# ⑥ 出站动作维度：模块可禁用的动作集合
# "send"=消息发送（Event.reply / Send DSL）、"api"=标准 API 动作（Api DSL / call_api）、
# "request"=请求操作（Request DSL accept/reject）
_ACTION_NAMES = ("send", "api", "request")


def _is_identity_binding(binding) -> str | None:
    """
    {!--< internal-use >!--}
    读取身份绑定的策略（deny 优先于 allow）

    :param binding: 绑定字典（{"allow": true} 或 {"deny": true}）
    :return: "allow" / "deny"；未配置或格式非法时返回 None
    """
    if not isinstance(binding, dict):
        return None
    if binding.get("deny"):
        return "deny"
    if binding.get("allow"):
        return "allow"
    return None


class ScopeManager:
    """
    统一控制面管理器（单例）

    管理六维配置：模块（modules）/ 身份（identity）/ 命令（commands）/
    处理器（handlers）/ 覆盖（overrides）/ 出站动作（actions）。支持配置热更新、
    运行时增删、LRU 缓存与运行统计。
    """

    def __init__(self, cache_size: int = DEFAULT_CACHE_SIZE):
        self._cache_size = max(1, int(cache_size))
        # 内存中的绑定缓存（随配置热更新重建）
        self._bindings: dict[str, dict] = {
            _BUCKET_PLATFORMS: {},
            _BUCKET_BOTS: {},
            _BUCKET_SESSIONS: {},
            "identity": {
                _IDENTITY_ADAPTERS: {},
                _IDENTITY_BOTS: {},
                _IDENTITY_SESSIONS: {},
                _IDENTITY_USERS: {},
            },
            "commands": {},
            "handlers": {},
            "overrides": {},
            "actions": {},
        }
        self._default_allow: bool = True
        self._stats: dict[str, int] = {
            "module_calls": 0,
            "module_filtered": 0,
            "identity_checks": 0,
            "identity_denied": 0,
            "command_checks": 0,
            "command_denied": 0,
            "action_checks": 0,
            "action_denied": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        # is_allowed 的 LRU 结果缓存：(platform, bot_id, session_id, module) -> bool
        self._cache: OrderedDict[tuple, bool] = OrderedDict()
        # 身份判定 LRU：(platform, bot_id, session_id, user_id) -> bool
        self._identity_cache: OrderedDict[tuple, bool] = OrderedDict()
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
        identity = scope_config.get("identity") or {}
        commands = scope_config.get("commands") or {}
        handlers = scope_config.get("handlers") or {}
        overrides = scope_config.get("overrides") or {}
        actions = scope_config.get("actions") or {}

        self._bindings = {
            _BUCKET_PLATFORMS: dict(platforms) if isinstance(platforms, dict) else {},
            _BUCKET_BOTS: dict(bots) if isinstance(bots, dict) else {},
            _BUCKET_SESSIONS: dict(sessions) if isinstance(sessions, dict) else {},
            "identity": {
                _IDENTITY_ADAPTERS: dict(identity.get(_IDENTITY_ADAPTERS) or {}) if isinstance(identity, dict) else {},
                _IDENTITY_BOTS: dict(identity.get(_IDENTITY_BOTS) or {}) if isinstance(identity, dict) else {},
                _IDENTITY_SESSIONS: dict(identity.get(_IDENTITY_SESSIONS) or {}) if isinstance(identity, dict) else {},
                _IDENTITY_USERS: dict(identity.get(_IDENTITY_USERS) or {}) if isinstance(identity, dict) else {},
            },
            "commands": dict(commands) if isinstance(commands, dict) else {},
            "handlers": dict(handlers) if isinstance(handlers, dict) else {},
            "overrides": dict(overrides) if isinstance(overrides, dict) else {},
            "actions": dict(actions) if isinstance(actions, dict) else {},
        }
        self._invalidate_cache()

    def _on_config_updated(self, _data: dict) -> None:
        """配置变更回调：重建绑定缓存"""
        self._load_bindings()

    def _invalidate_cache(self) -> None:
        """{!--< internal-use >!--} 清空 LRU 结果缓存"""
        self._cache.clear()
        self._identity_cache.clear()

    # ==================== ① 模块维度 ====================

    @staticmethod
    def _normalize(cfg: dict) -> tuple[Callable[[str], bool] | None, Callable[[str], bool] | None]:
        """
        {!--< internal-use >!--}
        归一化绑定配置为 (modules 匹配器, blocked 匹配器)

        条目统一走 :func:`text_match.compile_entry_list`（精确 / glob / re: 正则，
        大小写不敏感）。空列表返回 None（不限制）。

        :param cfg: 绑定配置字典（可含 modules / blocked 字段）
        :return: (modules 匹配器, blocked 匹配器)
        """
        modules = cfg.get("modules") or []
        blocked = cfg.get("blocked") or []
        if isinstance(modules, str):
            modules = [modules]
        if isinstance(blocked, str):
            blocked = [blocked]
        return text_match.compile_entry_list(modules), text_match.compile_entry_list(blocked)

    def _get_binding(
        self, platform: str, bot_id: str | None, session_id: str | None
    ) -> tuple[Callable[[str], bool] | None, Callable[[str], bool] | None] | None:
        """
        {!--< internal-use >!--}
        获取平台 / Bot / 会话的生效模块绑定

        解析优先级：会话级 > Bot 级 > 平台级；均不存在时返回 None。

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 表示不匹配 Bot 级
        :param session_id: 会话 ID（群 / 频道 / 私聊），None 表示不匹配会话级
        :return: (modules 匹配器, blocked 匹配器) 或 None
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

        模块名匹配大小写不敏感，条目支持 glob / ``re:`` 正则。
        结果带 LRU 缓存，配置变更 / bind / unbind 时自动失效。
        无绑定（默认）时遵循 ``default_allow``；模块名为空（框架层资源）始终放行。

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
        self._stats["module_calls"] += 1

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
        self._put_cache(self._cache, cache_key, allowed)
        if not allowed:
            self._stats["module_filtered"] += 1
            from .i18n import i18n

            self._logger_trace(i18n.t("core.scope.denied", module=module_name))
        return allowed

    def _compute_allowed(self, platform: str, bot_id: str | None, session_id: str | None, module_key: str) -> bool:
        """{!--< internal-use >!--} 计算模块是否允许（无缓存）"""
        binding = self._get_binding(platform, bot_id, session_id)
        if binding is None:
            return self._default_allow
        modules, blocked = binding
        if blocked and blocked(module_key):
            return False
        if modules:
            return modules(module_key)
        return self._default_allow

    # ==================== ② 身份维度 ====================

    def _resolve_identity_policy(
        self,
        platform: str,
        bot_id: str | None,
        session_id: str | None,
        user_id: str | None,
    ) -> str | None:
        """
        {!--< internal-use >!--}
        按特异性解析生效的身份策略：用户级 > 会话级 > Bot 级 > 适配器级

        每个桶内：先精确命中，未命中再按 glob / ``re:`` 正则匹配该平台下全部条目。
        取第一个产生策略的桶。

        :return: "allow" / "deny"；均未配置绑定时返回 None
        """
        identity = self._bindings.get("identity", {})

        # 用户级
        if user_id:
            plat_users = identity.get(_IDENTITY_USERS, {}).get(platform)
            if isinstance(plat_users, dict):
                policy = _is_identity_binding(plat_users.get(str(user_id)))
                if policy:
                    return policy
                for key, binding in plat_users.items():
                    if text_match.compile_entry_matcher(str(key))(str(user_id)):
                        policy = _is_identity_binding(binding)
                        if policy:
                            return policy
        # 会话级
        if session_id:
            plat_sessions = identity.get(_IDENTITY_SESSIONS, {}).get(platform)
            if isinstance(plat_sessions, dict):
                policy = _is_identity_binding(plat_sessions.get(str(session_id)))
                if policy:
                    return policy
                for key, binding in plat_sessions.items():
                    if text_match.compile_entry_matcher(str(key))(str(session_id)):
                        policy = _is_identity_binding(binding)
                        if policy:
                            return policy
        # Bot 级
        if bot_id:
            plat_bots = identity.get(_IDENTITY_BOTS, {}).get(platform)
            if isinstance(plat_bots, dict):
                policy = _is_identity_binding(plat_bots.get(str(bot_id)))
                if policy:
                    return policy
                for key, binding in plat_bots.items():
                    if text_match.compile_entry_matcher(str(key))(str(bot_id)):
                        policy = _is_identity_binding(binding)
                        if policy:
                            return policy
        # 适配器级
        policy = _is_identity_binding(identity.get(_IDENTITY_ADAPTERS, {}).get(platform))
        if policy:
            return policy
        return None

    def is_identity_allowed(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> bool:
        """
        判断事件是否放行（身份维度，原事件准入）

        解析优先级：**用户级 > 会话级 > Bot 级 > 适配器级**，取最具体的
        已配置绑定；均未配置时遵循 ``default_allow``。
        被拒绝的事件应在分发入口**完全丢弃**（不进入任何处理器）。

        :param platform: 平台名称（适配器标识）
        :param bot_id: Bot 用户 ID，None 表示不匹配 Bot 级绑定
        :param session_id: 会话 ID（群 / 频道 / 私聊），None 表示不匹配会话级
        :param user_id: 用户 ID，None 表示不匹配用户级
        :return: 是否放行该事件

        :example:
        >>> scope.is_identity_allowed("onebot11", "123456", "group_9", "999")
        False
        """
        self._stats["identity_checks"] += 1
        platform = str(platform or "")
        bot_id = str(bot_id) if bot_id else None
        session_id = str(session_id) if session_id else None
        user_id = str(user_id) if user_id else None

        cache_key = (platform, bot_id, session_id, user_id)
        cached = self._identity_cache.get(cache_key)
        if cached is not None:
            return cached

        policy = self._resolve_identity_policy(platform, bot_id, session_id, user_id)
        if policy is None:
            result = self._default_allow
        else:
            result = policy == "allow"
        self._put_cache(self._identity_cache, cache_key, result)
        if not result:
            self._stats["identity_denied"] += 1
        return result

    def is_user_blocked(self, platform: str, user_id: str | None) -> bool:
        """
        检查用户是否被拉黑（身份维度 deny）

        :param platform: 平台名称
        :param user_id: 用户 ID
        :return: 是否被拉黑
        """
        if not user_id:
            return False
        return self._resolve_identity_policy(str(platform or ""), None, None, str(user_id)) == "deny"

    def get_blocked_users(self) -> dict[str, list[str]]:
        """
        获取所有被拉黑的用户（精确 deny 绑定）

        :return: ``{platform: [user_id, ...]}``（按平台分组、用户 ID 排序）
        """
        result: dict[str, list[str]] = {}
        identity = self._bindings.get("identity", {})
        for platform, plat_users in identity.get(_IDENTITY_USERS, {}).items():
            if not isinstance(plat_users, dict):
                continue
            blocked = sorted(uid for uid, cfg in plat_users.items() if _is_identity_binding(cfg) == "deny")
            if blocked:
                result[platform] = blocked
        return result

    # ==================== ③ 命令维度 ====================

    def _command_acl(self, command_name: str) -> dict | None:
        """
        {!--< internal-use >!--}
        获取命令的生效 ACL（按 glob / ``re:`` 匹配命令名）

        :param command_name: 命令主名
        :return: {"allow": [...], "deny": [...]}，未配置时返回 None
        """
        commands = self._bindings.get("commands", {})
        exact = commands.get(command_name)
        if isinstance(exact, dict):
            return exact
        for key, acl in commands.items():
            if text_match.compile_entry_matcher(str(key))(command_name):
                if isinstance(acl, dict):
                    return acl
        return None

    def is_command_allowed(self, command_name: str, platform: str, user_id: str) -> bool:
        """
        判断用户对命令是否被 ACL 允许

        判定顺序：deny 命中 → False；allow 非空且未命中 → False；
        allow 命中 → True；未配置 ACL 时遵循全局 ``default_allow``
        （false = 严格模式，命令未配置 ACL 即拒绝）。

        :param command_name: 命令主名
        :param platform: 用户所属平台
        :param user_id: 用户 ID
        :return: 是否允许执行
        """
        self._stats["command_checks"] += 1
        acl = self._command_acl(command_name)
        if acl is None:
            return self._default_allow
        user_tag = f"{platform}:{user_id}"
        if user_tag in (acl.get("deny") or []):
            self._stats["command_denied"] += 1
            return False
        allow_list = acl.get("allow") or []
        if allow_list and user_tag not in allow_list:
            self._stats["command_denied"] += 1
            return False
        return True

    # ==================== ④ 处理器/文本维度 ====================

    def handler_condition(self, owner: str) -> Callable | None:
        """
        {!--< internal-use >!--}
        获取模块的文本过滤条件（handlers 桶）

        :param owner: 模块名
        :return: 事件条件函数，未配置时返回 None
        """
        handlers = self._bindings.get("handlers", {})
        cfg = handlers.get(owner)
        if not isinstance(cfg, dict):
            return None
        pattern = cfg.get("pattern")
        regex = cfg.get("regex")
        # regex 配置带 "re:" 前缀时剥离
        if isinstance(regex, str) and regex.startswith(text_match.REGEX_PREFIX):
            regex = regex[len(text_match.REGEX_PREFIX) :]
        return text_match.compile_text_matcher(pattern, regex)

    # ==================== ⑤ 实现参数覆盖 ====================

    def get_override(self, owner: str, command_name: str | None = None) -> dict:
        """
        获取模块 / 命令的实现参数覆盖

        存储形态：``overrides.<module>`` 下标量值为模块级参数（如 ``hidden = true``），
        子表（dict 值）为命令级覆盖（如 ``overrides.<module>.<command>``）。

        :param owner: 模块名
        :param command_name: 命令名；None 表示仅模块级参数
        :return: 覆盖字典（模块级参数 + 命令级覆盖，命令级优先），未配置返回 {}
        """
        overrides = self._bindings.get("overrides", {})
        result: dict = {}
        module_cfg = overrides.get(owner)
        if isinstance(module_cfg, dict):
            for key, value in module_cfg.items():
                if isinstance(value, dict):
                    # 子表视为命令级覆盖
                    if command_name and key == command_name:
                        result.update(value)
                else:
                    result[key] = value
        return result

    def apply_override(self, owner: str, command_name: str, defaults: dict) -> dict:
        """
        {!--< internal-use >!--}
        把命令默认参数与覆盖合并（覆盖优先）

        覆盖键 ``master`` 会同步映射到命令存储键 ``must_master``：
        用户优先——用户在控制面显式配置 ``master = true/false`` 时直接生效
        （既可收紧也可放开开发者默认），未配置时保持开发者默认。

        :param owner: 模块名
        :param command_name: 命令名
        :param defaults: 命令默认参数字典
        :return: 合并后的参数字典
        """
        merged = dict(defaults)
        override = self.get_override(owner, command_name)
        merged.update(override)
        if "master" in override:
            merged["must_master"] = bool(override["master"])
        return merged

    # ==================== 通用工具 ====================

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

        直接按 ID 字段存在性提取（优先级 group > channel > guild > thread > user），
        不做会话类型推断：meta（connect / disconnect / heartbeat）等不含任何
        会话 ID 字段的事件会返回空字符串，不会触发 ``infer_receive_type`` 的
        兜底推断与日志。语义与原实现（经推断后取值）等价——原实现中缺少
        全部 ID 字段的事件同样返回空。

        :param event: 事件数据（dict 或 Event 包装对象）
        :return: 会话 ID（如 group_id / channel_id / user_id），无法识别时返回空字符串
        """
        try:
            for key in (
                "group_id",
                "channel_id",
                "guild_id",
                "thread_id",
                "user_id",
            ):
                value = event.get(key)
                if value:
                    return str(value)
        except Exception:
            pass
        return ""

    def _put_cache(self, cache: OrderedDict, key: tuple, value: bool) -> None:
        """{!--< internal-use >!--} 写入 LRU 缓存（超过容量时淘汰最旧）"""
        cache[key] = value
        cache.move_to_end(key)
        while len(cache) > self._cache_size:
            cache.popitem(last=False)

    # ==================== 运行时增删 ====================

    # ---- 模块维度 ----

    def get(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
    ) -> dict | None:
        """
        获取平台 / Bot / 会话的生效模块绑定（原始配置形态）

        解析优先级：会话级 > Bot 级 > 平台级。

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 表示不匹配 Bot 级
        :param session_id: 会话 ID，None 表示不匹配会话级
        :return: {"modules": [...], "blocked": [...]}，无绑定时返回 None

        :example:
        >>> scope.get("onebot11", "123456")
        {"modules": ["Chat"], "blocked": []}
        """
        if session_id:
            plat_sessions = self._bindings.get(_BUCKET_SESSIONS, {}).get(platform or "")
            if isinstance(plat_sessions, dict):
                cfg = plat_sessions.get(session_id)
                if isinstance(cfg, dict):
                    return dict(cfg)
        if bot_id:
            plat_bots = self._bindings.get(_BUCKET_BOTS, {}).get(platform or "")
            if isinstance(plat_bots, dict):
                cfg = plat_bots.get(bot_id)
                if isinstance(cfg, dict):
                    return dict(cfg)
        cfg = self._bindings.get(_BUCKET_PLATFORMS, {}).get(platform or "")
        return dict(cfg) if isinstance(cfg, dict) else None

    def bind_module(
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
        绑定模块作用域（① 模块维度）

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 且 session_id 为空时表示平台级绑定
        :param session_id: 会话 ID。指定时绑定到该会话；否则有 bot_id 时绑定到该 Bot；
                           否则绑定到平台级
        :param modules: 白名单模块条目列表（精确 / glob / ``re:`` 正则）
        :param blocked: 黑名单模块条目列表
        :param persist: 是否持久化到配置文件 (默认: True)
        :param merge: 是否**合并**而非替换现有绑定（默认 False）
        """
        binding = {
            "modules": list(modules or []),
            "blocked": list(blocked or []),
        }

        bucket, key = self._resolve_module_target(platform, bot_id, session_id)

        if merge:
            existing = self._raw_get(bucket, platform, key)
            if existing:
                existing_modules = [str(m) for m in existing.get("modules", [])]
                existing_blocked = [str(b) for b in existing.get("blocked", [])]
                for m in binding["modules"]:
                    if str(m) not in existing_modules:
                        existing_modules.append(str(m))
                for b in binding["blocked"]:
                    if str(b) not in existing_blocked:
                        existing_blocked.append(str(b))
                binding = {"modules": existing_modules, "blocked": existing_blocked}

        def _apply_memory() -> None:
            section = self._bindings.setdefault(bucket, {})
            if bucket == _BUCKET_PLATFORMS:
                section[platform] = binding
            else:
                section.setdefault(platform, {})[key] = binding
            self._invalidate_cache()

        if not persist:
            _apply_memory()
            return

        current = self._raw_bindings()
        section = current.setdefault(bucket, {})
        if bucket == _BUCKET_PLATFORMS:
            section[platform] = binding
        else:
            section.setdefault(platform, {})[key] = binding
        update_erispulse_config({"scope": current})
        _apply_memory()

    def unbind_module(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        persist: bool = True,
    ) -> bool:
        """
        移除模块作用域绑定（恢复为允许全部模块）

        :return: 是否成功移除（不存在则返回 False）
        """
        bucket, key = self._resolve_module_target(platform, bot_id, session_id)
        section = self._bindings.get(bucket, {})
        if bucket == _BUCKET_PLATFORMS:
            exists = platform in section
        else:
            plat = section.get(platform)
            exists = isinstance(plat, dict) and key in plat
        if not exists:
            return False

        if persist:
            current = self._raw_bindings()
            bucket_cfg = current.get(bucket, {})
            if bucket == _BUCKET_PLATFORMS:
                bucket_cfg.pop(platform, None)
            else:
                plat = bucket_cfg.get(platform)
                if isinstance(plat, dict):
                    plat.pop(key, None)
                    if not plat:
                        bucket_cfg.pop(platform, None)
            set_erispulse_section(f"scope.{bucket}", bucket_cfg)

        def _apply_memory() -> None:
            if bucket == _BUCKET_PLATFORMS:
                self._bindings[bucket].pop(platform, None)
            else:
                plat = self._bindings[bucket].get(platform)
                if isinstance(plat, dict):
                    plat.pop(key, None)
                    if not plat:
                        self._bindings[bucket].pop(platform, None)
            self._invalidate_cache()

        _apply_memory()
        return True

    # ---- 身份维度 ----

    def bind_identity(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        *,
        allow: bool | None = None,
        deny: bool | None = None,
        persist: bool = True,
    ) -> None:
        """
        绑定身份准入策略（② 身份维度，指定来源的事件放行 / 拒绝）

        绑定层级由参数决定：给定 ``user_id`` 绑定用户级；否则给定
        ``session_id`` 绑定会话级；否则给定 ``bot_id`` 绑定 Bot 级；
        否则绑定适配器级。``allow`` 与 ``deny`` 必须二选一（同时给定时以 ``deny`` 为准）。
        绑定键支持 glob / ``re:`` 正则（如 ``user_id="spam_*"``）。

        :example:
        >>> scope.bind_identity("onebot11", user_id="999", deny=True)
        >>> scope.bind_identity("onebot11", user_id="spam_*", deny=True)
        """
        if deny:
            binding: dict = {"deny": True}
        elif allow:
            binding = {"allow": True}
        else:
            from .i18n import i18n

            raise ValueError(i18n.t("core.scope.identity_policy_required"))
        bucket, key = self._resolve_identity_target(platform, bot_id, session_id, user_id)

        def _apply_memory() -> None:
            # 动态访问 self._bindings：持久化写入触发的 config.set 重载
            # 可能已整体重建绑定缓存，闭包捕获旧引用会写入孤儿字典
            section = self._bindings.setdefault("identity", {}).setdefault(bucket, {})
            if bucket == _IDENTITY_ADAPTERS:
                section[platform] = binding
            else:
                section.setdefault(platform, {})[key] = binding
            self._invalidate_cache()

        if not persist:
            _apply_memory()
            return

        current = self._raw_bindings()
        cur_identity = current.setdefault("identity", {})
        section = cur_identity.setdefault(bucket, {})
        if bucket == _IDENTITY_ADAPTERS:
            section[platform] = binding
        else:
            section.setdefault(platform, {})[key] = binding
        update_erispulse_config({"scope": current})
        _apply_memory()

    def unbind_identity(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        persist: bool = True,
    ) -> bool:
        """
        移除身份准入绑定（该来源恢复遵循 default_allow）

        :return: 是否成功移除（绑定不存在时返回 False）
        """
        bucket, key = self._resolve_identity_target(platform, bot_id, session_id, user_id)
        identity = self._bindings.get("identity", {})
        section = identity.get(bucket, {})
        if bucket == _IDENTITY_ADAPTERS:
            exists = platform in section
        else:
            plat = section.get(platform)
            exists = isinstance(plat, dict) and key in plat
        if not exists:
            return False

        if persist:
            current = self._raw_bindings()
            cur_identity = current.setdefault("identity", {})
            bucket_cfg = cur_identity.get(bucket, {})
            if bucket == _IDENTITY_ADAPTERS:
                bucket_cfg.pop(platform, None)
            else:
                plat = bucket_cfg.get(platform)
                if isinstance(plat, dict):
                    plat.pop(key, None)
                    if not plat:
                        bucket_cfg.pop(platform, None)
            set_erispulse_section("scope.identity", cur_identity)

        def _apply_memory() -> None:
            # 动态访问（同 bind_identity）：避免写入配置重载后的孤儿引用
            identity = self._bindings.setdefault("identity", {})
            if bucket == _IDENTITY_ADAPTERS:
                identity[bucket].pop(platform, None)
            else:
                plat = identity[bucket].get(platform)
                if isinstance(plat, dict):
                    plat.pop(key, None)
                    if not plat:
                        identity[bucket].pop(platform, None)
            self._invalidate_cache()

        _apply_memory()
        return True

    def block_user(self, platform: str, user_id: str, persist: bool = True) -> None:
        """
        拉黑用户：该用户的所有类型事件在分发入口被完全丢弃

        等价于 ``bind_identity(platform, user_id=user_id, deny=True)``。

        :param platform: 平台名称
        :param user_id: 用户 ID
        :param persist: 是否持久化到配置文件 (默认: True)
        """
        self.bind_identity(platform, user_id=user_id, deny=True, persist=persist)

    def unblock_user(self, platform: str, user_id: str, persist: bool = True) -> bool:
        """
        取消拉黑用户（移除该用户的准入绑定）

        :return: 是否成功移除（该用户本无绑定或绑定非 deny 时返回 False）
        """
        plat_users = self._bindings.get("identity", {}).get(_IDENTITY_USERS, {}).get(str(platform or ""))
        if not isinstance(plat_users, dict):
            return False
        if _is_identity_binding(plat_users.get(str(user_id))) != "deny":
            return False
        return self.unbind_identity(platform, user_id=str(user_id), persist=persist)

    # ---- 命令维度 ----

    def _acl_mutate(
        self,
        command_name: str,
        list_name: str,
        platform: str,
        user_id: str,
        *,
        remove: bool = False,
        persist: bool = True,
    ) -> None:
        """
        {!--< internal-use >!--}
        增删命令 ACL 名单成员

        :param command_name: 命令名（可含 glob / ``re:`` 模式）
        :param list_name: 名单名（"allow" / "deny"）
        :param platform: 用户所属平台
        :param user_id: 用户 ID
        :param remove: 是否移除（True 移除成员，False 追加成员）
        :param persist: 是否持久化
        """
        user_tag = f"{platform}:{user_id}"
        acl = self._bindings.setdefault("commands", {}).setdefault(command_name, {})

        if remove:
            members = acl.get(list_name) or []
            if user_tag in members:
                members.remove(user_tag)
            if members:
                acl[list_name] = members
            else:
                acl.pop(list_name, None)
            if not acl.get("allow") and not acl.get("deny"):
                self._bindings["commands"].pop(command_name, None)
        else:
            members = acl.setdefault(list_name, [])
            if user_tag not in members:
                members.append(user_tag)

        if persist:
            set_erispulse_section("scope.commands", self._bindings["commands"])

    def allow_user(self, command_name: str, platform: str, user_id: str, persist: bool = True) -> None:
        """
        将用户加入命令的 allow 名单（白名单非空时仅名单内用户可执行）

        命令名支持 glob / ``re:`` 正则。

        :example:
        >>> scope.allow_user("roll*", "onebot11", "123456")
        """
        self._acl_mutate(command_name, "allow", platform, user_id, persist=persist)

    def deny_user(self, command_name: str, platform: str, user_id: str, persist: bool = True) -> None:
        """
        将用户加入命令的 deny 名单（deny 优先于 allow 与默认权限）

        命令名支持 glob / ``re:`` 正则。

        :example:
        >>> scope.deny_user("roll*", "onebot11", "666")
        """
        self._acl_mutate(command_name, "deny", platform, user_id, persist=persist)

    def get_acl(self, command_name: str) -> dict[str, list[str]]:
        """
        查询命令当前的用户黑白名单

        :param command_name: 命令名（可含模式）
        :return: {"allow": [...], "deny": [...]}（用户标识 "platform:user_id"）
        """
        acl = self._command_acl(command_name)
        return {
            "allow": list((acl or {}).get("allow") or []),
            "deny": list((acl or {}).get("deny") or []),
        }

    def remove_acl(self, command_name: str, persist: bool = True) -> bool:
        """
        清除命令的用户黑白名单（恢复开发者默认权限逻辑）

        :param command_name: 命令名（可含模式）
        :param persist: 是否持久化
        :return: 是否存在并被清除
        """
        commands = self._bindings.get("commands", {})
        removed = False
        for key in list(commands.keys()):
            if text_match.compile_entry_matcher(str(key))(command_name):
                commands.pop(key, None)
                removed = True
        if removed and persist:
            set_erispulse_section("scope.commands", commands)
        return removed

    # ---- ⑥ 出站动作维度 ----

    def _action_cfg(self, owner: str) -> dict[str, bool] | None:
        """
        {!--< internal-use >!--}
        读取模块的出站动作配置

        :param owner: 模块名（owner），无 owner 时返回 None
        :return: 动作开关字典（{"send": bool, "api": bool, "request": bool}），未配置返回 None
        """
        if not owner:
            return None
        cfg = self._bindings.get("actions", {}).get(owner)
        return cfg if isinstance(cfg, dict) else None

    def is_action_allowed(self, owner: str, action: str) -> bool:
        """
        判断模块是否允许执行某类出站动作（⑥ 出站动作维度）

        判定语义：**默认允许**——未配置、或 owner 为空（框架层调用）均视为允许；
        仅当用户显式禁用（``scope.actions.<owner>.<action> = false``）才拒绝。
        与身份/命令维度的"默认允许兜底"不同，本维度是出站能力的收紧开关，
        空白即放行，声明式禁用。

        :param owner: 模块名（owner）
        :param action: 动作类型，取值 ``_ACTION_NAMES``（"send" / "api" / "request"）
        :return: 是否允许执行
        """
        self._stats["action_checks"] += 1
        cfg = self._action_cfg(owner)
        if cfg is None:
            return True
        allowed = cfg.get(action)
        if allowed is False:
            self._stats["action_denied"] += 1
            return False
        return True

    def set_action(self, owner: str, action: str, allowed: bool, persist: bool = True) -> None:
        """
        设置模块某类出站动作的允许/禁用（⑥ 出站动作维度）

        仅影响本模块从事件处理器（handler 执行期 owner 上下文）发起的出站调用。
        不影响框架层内部调用（owner 为空时恒放行）。

        :param owner: 模块名（owner）
        :param action: 动作类型（"send" / "api" / "request"）
        :param allowed: False 禁止该动作，True 允许
        :param persist: 是否持久化 (默认: True)

        :example:
        >>> scope.set_action("MyModule", "send", False)  # 禁止 MyModule 回复消息
        >>> scope.set_action("MyModule", "api", False)  # 禁止 MyModule 调用标准 API
        >>> scope.set_action("MyModule", "request", False)  # 禁止 MyModule 处理请求操作
        """
        if action not in _ACTION_NAMES:
            raise ValueError(f"unknown action: {action!r}, expected one of {_ACTION_NAMES}")
        if not owner:
            raise ValueError("owner is required to set action permission")
        actions = self._bindings.setdefault("actions", {})
        cfg = actions.setdefault(owner, {})
        cfg[action] = bool(allowed)
        if persist:
            set_erispulse_section("scope.actions", actions)

    def unset_action(self, owner: str, action: str | None = None, persist: bool = True) -> bool:
        """
        移除模块的出站动作限制（恢复默认允许）

        :param owner: 模块名
        :param action: 动作类型；None 表示移除该模块全部动作限制
        :param persist: 是否持久化
        :return: 是否有内容被移除
        """
        actions = self._bindings.get("actions", {})
        if owner not in actions:
            return False
        if action is None:
            del actions[owner]
        else:
            cfg = actions[owner]
            if action not in cfg:
                return False
            del cfg[action]
            if not cfg:
                del actions[owner]
        if persist:
            set_erispulse_section("scope.actions", actions)
        return True

    def get_action_rules(self, owner: str) -> dict[str, bool]:
        """
        查询模块当前的出站动作限制

        :param owner: 模块名
        :return: 动作开关字典（含默认允许的未配置项为 True）
        """
        cfg = self._action_cfg(owner)
        return {name: not (cfg is not None and cfg.get(name) is False) for name in _ACTION_NAMES}

    # ---- 处理器维度 ----

    def bind_handler(
        self,
        owner: str,
        pattern: str | None = None,
        regex: str | None = None,
        persist: bool = True,
    ) -> None:
        """
        绑定模块的文本过滤条件（④ 处理器维度）

        :param owner: 模块名
        :param pattern: glob 通配符，不匹配的消息不触发该模块处理器
        :param regex: 正则源码（可带 ``re:`` 前缀），与 pattern 同时给定时须都命中
        :param persist: 是否持久化 (默认: True)
        """
        cfg: dict = {}
        if pattern:
            cfg["pattern"] = pattern
        if regex:
            cfg["regex"] = regex if regex.startswith(text_match.REGEX_PREFIX) else text_match.REGEX_PREFIX + regex
        handlers = self._bindings.setdefault("handlers", {})
        if cfg:
            handlers[owner] = cfg
        else:
            handlers.pop(owner, None)

        if persist:
            set_erispulse_section("scope.handlers", handlers)

    def unbind_handler(self, owner: str, persist: bool = True) -> bool:
        """
        移除模块的文本过滤条件

        :return: 是否成功移除
        """
        handlers = self._bindings.get("handlers", {})
        if owner not in handlers:
            return False
        handlers.pop(owner, None)
        if persist:
            set_erispulse_section("scope.handlers", handlers)
        return True

    # ---- 覆盖维度 ----

    def override(
        self,
        owner: str,
        command_name: str | None = None,
        persist: bool = True,
        **params,
    ) -> None:
        """
        覆盖模块 / 命令的实现参数（⑤ 覆盖维度）

        覆盖遵循**用户优先**：显式设置的参数直接生效（可收紧也可放开开发者默认）。
        覆盖值只影响**实现参数**（master / hidden / aliases / prefix 等），
        不用于禁用——禁用统一走命令 deny（``deny_user`` / ``scope.commands``）。

        :param owner: 模块名
        :param command_name: 命令名；None 表示模块级覆盖
        :param persist: 是否持久化 (默认: True)
        :param params: 要覆盖的参数（如 ``master=True`` 收紧、``master=False`` 放开、``hidden=True``、``aliases=["rs"]``）

        :example:
        >>> scope.override("MyModule", "restart", master=True, hidden=True)
        """
        overrides = self._bindings.setdefault("overrides", {})
        module_cfg = overrides.setdefault(owner, {})
        if command_name:
            cmd_cfg = module_cfg.setdefault(command_name, {})
            cmd_cfg.update(params)
        else:
            module_cfg.update(params)

        if persist:
            set_erispulse_section("scope.overrides", overrides)

    def remove_override(self, owner: str, command_name: str | None = None, persist: bool = True) -> bool:
        """
        移除模块 / 命令的实现参数覆盖

        :return: 是否成功移除
        """
        overrides = self._bindings.get("overrides", {})
        module_cfg = overrides.get(owner)
        if not isinstance(module_cfg, dict):
            return False
        if command_name:
            if command_name not in module_cfg:
                return False
            module_cfg.pop(command_name, None)
            if not module_cfg:
                overrides.pop(owner, None)
        else:
            overrides.pop(owner, None)

        if persist:
            set_erispulse_section("scope.overrides", overrides)
        return True

    # ==================== 查询 / 统计 / 拓扑 ====================

    def list_bindings(self) -> dict:
        """
        列出全部控制面绑定（含出站动作维度）

        :return: {"platforms", "bots", "sessions", "identity", "commands",
                "handlers", "overrides", "actions"} 结构（深拷贝）
        """
        return self._raw_bindings()

    def clear(self) -> None:
        """清空所有控制面绑定（仅内存生效，不持久化）"""
        self._bindings = {
            _BUCKET_PLATFORMS: {},
            _BUCKET_BOTS: {},
            _BUCKET_SESSIONS: {},
            "identity": {
                _IDENTITY_ADAPTERS: {},
                _IDENTITY_BOTS: {},
                _IDENTITY_SESSIONS: {},
                _IDENTITY_USERS: {},
            },
            "commands": {},
            "handlers": {},
            "overrides": {},
            "actions": {},
        }
        self._invalidate_cache()

    def get_stats(self) -> dict[str, int]:
        """
        获取控制面运行统计

        统计项：``module_calls`` / ``module_filtered``（模块维度）、
        ``identity_checks`` / ``identity_denied``（身份维度）、
        ``command_checks`` / ``command_denied``（命令维度）、
        ``action_checks`` / ``action_denied``（出站动作维度）、
        ``cache_hits`` / ``cache_misses``（模块维度 LRU）。

        :return: 统计字典
        """
        return dict(self._stats)

    def reset_stats(self) -> None:
        """重置控制面运行统计"""
        for key in self._stats:
            self._stats[key] = 0

    def get_topology(self) -> dict:
        """
        获取控制面绑定的结构化数据（便于 WebUI 展示拓扑树）

        :return: 全维度绑定结构（模块 / 身份 / 命令 / 处理器 / 覆盖 / 出站动作）
        """
        return self._raw_bindings()

    # ==================== 工具方法 ====================

    def _raw_get(self, bucket: str, platform: str, key: str) -> dict | None:
        """{!--< internal-use >!--} 读取指定模块绑定（供 merge 使用，浅拷贝）"""
        section = self._bindings.get(bucket, {})
        if bucket == _BUCKET_PLATFORMS:
            cfg = section.get(platform)
        else:
            plat = section.get(platform)
            cfg = plat.get(key) if isinstance(plat, dict) else None
        return dict(cfg) if isinstance(cfg, dict) else None

    def _resolve_module_target(self, platform: str, bot_id: str | None, session_id: str | None) -> tuple[str, str]:
        """
        {!--< internal-use >!--}
        根据参数解析模块维度目标桶与键

        :return: (bucket, key) 元组
        """
        if session_id:
            return _BUCKET_SESSIONS, str(session_id)
        if bot_id:
            return _BUCKET_BOTS, str(bot_id)
        return _BUCKET_PLATFORMS, str(platform)

    def _resolve_identity_target(
        self,
        platform: str,
        bot_id: str | None,
        session_id: str | None,
        user_id: str | None,
    ) -> tuple[str, str]:
        """
        {!--< internal-use >!--}
        根据参数解析身份维度目标桶与键（用户级 > 会话级 > Bot 级 > 适配器级）

        :return: (bucket, key) 元组
        """
        if user_id:
            return _IDENTITY_USERS, str(user_id)
        if session_id:
            return _IDENTITY_SESSIONS, str(session_id)
        if bot_id:
            return _IDENTITY_BOTS, str(bot_id)
        return _IDENTITY_ADAPTERS, str(platform)

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
        commands = list(self._bindings.get("commands", {}).keys())
        return (
            f"<ScopeManager platforms={platforms} bots={bots} sessions={sessions} "
            f"commands={commands} default_allow={self._default_allow}>"
        )


# 模块级单例
scope: ScopeManager = ScopeManager()

__all__ = [
    "DEFAULT_CACHE_SIZE",
    "ScopeManager",
    "scope",
]
