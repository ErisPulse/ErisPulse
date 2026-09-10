"""
ErisPulse 作用域（scope）

控制权完全交给用户：在模块 / 适配器 / 处理器 / 出站调用注册的**上层**
（配置 ``ErisPulse.scope`` 或运行时 ``sdk.scope``）统一声明"**什么范围内生效**"。
事件管线在入口、处理器过滤与出站闸口自动读取并执行。

作用域按事件处理生命周期回答三个问题：

- 模块维度：某个上下文里哪些模块可用（平台 / Bot / 会话三级绑定）
- 身份维度：谁的事件收不收（适配器 / Bot / 会话 / 用户四级策略）
- 出站维度：模块能向外做什么（限制模块发起消息发送 / 标准 API 动作 / 请求操作）

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
    merge = true                  # 在平台级绑定基础上追加（默认整体覆盖）
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

    # ③ 出站维度：限制模块发起出站动作（默认全允许，显式收紧才禁）
    [ErisPulse.scope.actions.MyModule]
    send = { deny = true }                                   # 全禁发送
    send = { allow = ["Text", "Image*"], deny = ["File"] }   # 方法级细粒度
    api = { allow = ["get_*"] }                              # 仅允许查询类 API
    request = { deny = true }                                # 禁止处理请求

匹配条目统一语法（见 :mod:`ErisPulse.Core.text_match`）：
**精确名** / **glob**（``*`` / ``?`` / ``[seq]``）/ **``re:`` 正则**，默认大小写不敏感。

{!--< tips >!--}
1. 通过 ``from ErisPulse.Core import scope`` 导入单例（``sdk.scope`` 同对象）
2. 判定：``scope.is_allowed(...)`` / ``scope.is_identity_allowed(...)`` /
   ``scope.is_action_allowed(...)`` —— 对应 ①②④ 三个判定闸口
3. 读写：像字典一样用点分路径操作任意配置节 ——
   ``scope.get("platforms.onebot11")`` / ``scope.set("actions.My", {...})`` /
   ``scope.delete("actions.My.send")``，也支持 ``scope[key]`` / ``scope[key] = v`` / ``del scope[key]``
4. 事件处理器文本条件覆写见 :mod:`ErisPulse.Core.Event.overrides`；
   命令 ACL / 参数覆写见 :mod:`ErisPulse.Core.Event.command`
{!--< /tips >!--}
"""

import copy
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

from ..runtime.frame_config import set_erispulse_section, update_erispulse_config
from . import text_match
from .constants import CONFIG_ROOT_KEY
from .i18n import i18n

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

# ④ 出站维度：模块可限制的动作集合
# "send"=消息发送（Event.reply / Send DSL）、"api"=标准 API 动作（Api DSL / call_api）、
# "request"=请求操作（Request DSL accept/reject）、"call"=模块间调用（module.call）
_ACTION_NAMES = ("send", "api", "request", "call")

# 出站动作规则的合法键（其余键视为未知配置并告警）
_ACTION_RULE_KEYS = ("allow", "deny")

# get(path) 的哨兵：区分"节点不存在"与"节点值为 None"
_MISSING = object()


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


def _normalize_action_rule(rule) -> dict | None:
    """
    {!--< internal-use >!--}
    归一化出站动作规则

    合法输入形态：

    - ``True`` → ``{}``（无限制，等价未配置）
    - ``False`` → ``{"deny": True}``（全禁）
    - dict → 仅保留 ``allow``（字符串列表）与 ``deny``（布尔或字符串列表）键

    :param rule: 配置中的动作规则（bool / dict）
    :return: 规范化规则字典；allow / deny 类型非法时返回 None
    """
    if isinstance(rule, bool):
        return {} if rule else {"deny": True}
    if not isinstance(rule, dict):
        return None
    result: dict = {}
    allow = rule.get("allow")
    deny = rule.get("deny")
    if allow is not None:
        if isinstance(allow, str):
            allow = [allow]
        if not isinstance(allow, list) or not all(isinstance(entry, str) for entry in allow):
            return None
        result["allow"] = list(allow)
    if deny is not None:
        if isinstance(deny, str):
            deny = [deny]
        if isinstance(deny, bool):
            result["deny"] = deny
        elif isinstance(deny, list) and all(isinstance(entry, str) for entry in deny):
            result["deny"] = list(deny)
        else:
            return None
    return result


def _deep_merge(dst: dict, src: dict) -> None:
    """{!--< internal-use >!--} 把 src 深合并进 dst（原地修改）"""
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            _deep_merge(dst[key], value)
        else:
            dst[key] = value


# 运行时删除哨兵：persist=False 的 delete 在覆盖层中记录为删除标记，
# 配置树重建后重放时仍能保持"已删除"语义
_RUNTIME_DELETED = object()


class ScopeManager:
    """
    作用域管理器（单例）

    统一管理三维作用域配置（模块 / 身份 / 出站），配置即一棵
    ``ErisPulse.scope`` 字典树。API 面向原生字典风格收敛：

    - **判定**：:meth:`is_allowed` / :meth:`is_identity_allowed` /
      :meth:`is_action_allowed`（三个闸口的问询）
    - **读写**：:meth:`get` / :meth:`set` / :meth:`delete`（点分路径直达任意节，
      同时支持 ``scope[path]`` / ``scope[path] = value`` / ``del scope[path]``）
    - **全局**：:meth:`clear` / :meth:`stats` / :meth:`reset_stats` / :meth:`topology`

    支持配置热更新、LRU 缓存与运行统计。
    命令 ACL / 参数覆写由命令系统自持（``ErisPulse.event.command``）。
    """

    def __init__(self, cache_size: int = DEFAULT_CACHE_SIZE):
        self._cache_size = max(1, int(cache_size))
        # 统一配置树（随配置热更新整体重建）：
        # {platforms, bots, sessions, identity, actions}
        self._data: dict = {
            _BUCKET_PLATFORMS: {},
            _BUCKET_BOTS: {},
            _BUCKET_SESSIONS: {},
            "identity": {
                _IDENTITY_ADAPTERS: {},
                _IDENTITY_BOTS: {},
                _IDENTITY_SESSIONS: {},
                _IDENTITY_USERS: {},
            },
            "actions": {},
        }
        self._default_allow: bool = True
        self._stats: dict[str, int] = {
            "module_calls": 0,
            "module_filtered": 0,
            "identity_checks": 0,
            "identity_denied": 0,
            "action_checks": 0,
            "action_denied": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        # 模块判定 LRU：(platform, bot_id, session_id, module) -> bool
        self._cache: OrderedDict[tuple, bool] = OrderedDict()
        # 身份判定 LRU：(platform, bot_id, session_id, user_id) -> bool
        self._identity_cache: OrderedDict[tuple, bool] = OrderedDict()
        # 出站判定 LRU：(owner, action, name) -> bool
        self._action_cache: OrderedDict[tuple, bool] = OrderedDict()
        # 配置校验告警去重（同一路径同一问题只告警一次）
        self._warned: set[str] = set()
        # 运行时覆盖层：persist=False 的写入/删除记录于此（路径 → 值 / 删除哨兵）。
        # 配置树重建（_apply_tree）后按写入顺序重放，
        # 保证任意无关配置写入不会冲掉运行时绑定（Issue #432）
        self._runtime_overrides: dict[str, Any] = {}
        # 运行时写入归属：路径 → 调用方（模块卸载时兜底清理）
        self._runtime_owners: dict[str, str] = {}
        self._load_config()
        # 订阅配置热更新：scope 配置变更时自动重建配置树
        try:
            from .lifecycle import lifecycle

            lifecycle.register("config.updated", self._on_config_updated)
            lifecycle.register("config.set", self._on_config_updated)
        except Exception:
            pass

    # ==================== 配置加载与热更新 ====================

    def _warn_invalid(self, path: str, actual: str) -> None:
        """{!--< internal-use >!--} 输出配置格式告警（同一路径去重）"""
        key = f"scope:{path}:{actual}"
        if key in self._warned:
            return
        self._warned.add(key)
        try:
            from .i18n import i18n
            from .logger import logger

            logger.warning(i18n.t("core.scope.config_invalid", path=path, actual=actual))
        except Exception:
            pass

    def _validated_bucket(self, config: dict, key: str) -> dict:
        """{!--< internal-use >!--} 读取并校验一个 dict 型配置节（非法时告警并忽略）"""
        value = config.get(key)
        if value is None:
            return {}
        if not isinstance(value, dict):
            self._warn_invalid(f"scope.{key}", type(value).__name__)
            return {}
        return value

    def _load_config(self) -> None:
        """{!--< internal-use >!--} 从配置加载配置树（含格式校验）"""
        try:
            from ..runtime import get_config

            scope_config = get_config("scope") or {}
        except Exception:
            scope_config = {}
        self._apply_tree(scope_config if isinstance(scope_config, dict) else {})

    def _apply_tree(self, tree: dict) -> None:
        """{!--< internal-use >!--} 校验并应用配置树到内存（含格式校验）"""
        scope_config = tree if isinstance(tree, dict) else {}
        if not isinstance(tree, dict):
            self._warn_invalid("scope", type(tree).__name__)
        self._default_allow = bool(scope_config.get("default_allow", True))

        # 未知顶层键告警（常见于拼写错误，如 alow / defalut_allow）
        known_keys = {
            "default_allow",
            "cache_size",
            _BUCKET_PLATFORMS,
            _BUCKET_BOTS,
            _BUCKET_SESSIONS,
            "identity",
            "actions",
        }
        for key in scope_config:
            if key not in known_keys:
                self._warn_invalid(f"scope.{key}", "unknown key")

        platforms = self._validated_bucket(scope_config, _BUCKET_PLATFORMS)
        bots = self._validated_bucket(scope_config, _BUCKET_BOTS)
        sessions = self._validated_bucket(scope_config, _BUCKET_SESSIONS)
        identity = self._validated_bucket(scope_config, "identity")

        self._data = {
            _BUCKET_PLATFORMS: platforms,
            _BUCKET_BOTS: bots,
            _BUCKET_SESSIONS: sessions,
            "identity": {
                _IDENTITY_ADAPTERS: self._validated_bucket(identity, _IDENTITY_ADAPTERS),
                _IDENTITY_BOTS: self._validated_bucket(identity, _IDENTITY_BOTS),
                _IDENTITY_SESSIONS: self._validated_bucket(identity, _IDENTITY_SESSIONS),
                _IDENTITY_USERS: self._validated_bucket(identity, _IDENTITY_USERS),
            },
            "actions": self._validated_actions(scope_config),
        }
        # 重放运行时覆盖层：persist=False 的绑定在任意配置写入触发的
        # 树重建后保持有效（Issue #432）
        self._replay_runtime_overrides()
        self._invalidate_cache()

    def _replay_runtime_overrides(self) -> None:
        """{!--< internal-use >!--} 按写入顺序把运行时覆盖层重放到重建后的配置树"""
        for path, value in self._runtime_overrides.items():
            parts = self._split_path(path)
            if not parts:
                continue
            if value is _RUNTIME_DELETED:
                parent = self._node_at(".".join(parts[:-1])) if len(parts) > 1 else self._data
                if isinstance(parent, dict):
                    parent.pop(parts[-1], None)
                continue
            node = self._data
            for part in parts[:-1]:
                child = node.get(part)
                if not isinstance(child, dict):
                    child = {}
                    node[part] = child
                node = child
            last = parts[-1]
            if isinstance(value, dict) and isinstance(node.get(last), dict):
                _deep_merge(node[last], copy.deepcopy(value))
            else:
                node[last] = copy.deepcopy(value)

    def _record_runtime_owner(self, path: str) -> None:
        """{!--< internal-use >!--} 记录运行时写入的调用方归属（模块卸载时兜底清理）"""
        try:
            from ..runtime.context import current_owner

            owner = current_owner.get()
        except Exception:
            return
        if owner is not None:
            self._runtime_owners[path] = owner

    def _clear_runtime_overrides(self, prefix: str) -> None:
        """{!--< internal-use >!--} 清除某路径及其全部子路径的运行时覆盖记录"""
        prefix_dot = f"{prefix}."
        for known in [p for p in self._runtime_overrides if p == prefix or p.startswith(prefix_dot)]:
            self._runtime_overrides.pop(known, None)
            self._runtime_owners.pop(known, None)

    def unregister_by_owner(self, caller: str) -> int:
        """
        注销指定调用方的全部运行时（persist=False）作用域绑定

        仅清理内存态运行时写入；``persist=True`` 的写入属用户配置语义，
        在模块卸载时不受影响。由模块管理器在卸载时兜底调用，
        避免已卸载模块的运行时绑定残留生效。

        :param caller: 调用方模块名 / 适配器平台名
        :return: int 清理的绑定条目数
        """
        paths = [p for p, o in self._runtime_owners.items() if o == caller]
        removed = 0
        for path in paths:
            self._runtime_overrides.pop(path, None)
            self._runtime_owners.pop(path, None)
            parts = self._split_path(path)
            if not parts:
                continue
            if len(parts) > 1:
                parent = self._node_at(".".join(parts[:-1]))
            else:
                parent = self._data
            if isinstance(parent, dict) and parent.pop(parts[-1], None) is not None:
                removed += 1
        if removed:
            self._invalidate_cache()
        return removed

    def _validated_actions(self, scope_config: dict) -> dict:
        """{!--< internal-use >!--} 加载并校验出站动作规则"""
        actions_raw = self._validated_bucket(scope_config, "actions")
        actions: dict[str, dict] = {}
        for owner, rules in actions_raw.items():
            if not isinstance(rules, dict):
                self._warn_invalid(f"scope.actions.{owner}", type(rules).__name__)
                continue
            owner_rules: dict[str, dict] = {}
            for action, rule in rules.items():
                if action not in _ACTION_NAMES:
                    self._warn_invalid(
                        f"scope.actions.{owner}.{action}",
                        f"unknown action (expected one of {_ACTION_NAMES})",
                    )
                    continue
                unknown = [k for k in rule if k not in _ACTION_RULE_KEYS] if isinstance(rule, dict) else []
                for bad_key in unknown:
                    self._warn_invalid(f"scope.actions.{owner}.{action}.{bad_key}", "unknown key")
                normalized = _normalize_action_rule(rule)
                if normalized is None:
                    self._warn_invalid(f"scope.actions.{owner}.{action}", type(rule).__name__)
                    continue
                if normalized:
                    owner_rules[action] = normalized
            if owner_rules:
                actions[owner] = owner_rules
        return actions

    def _on_config_updated(self, data: dict) -> None:
        """
        配置变更回调：仅在 scope 配置实际变化时重建配置树

        - ``config.set``：按事件 key 过滤，只有整棵写入或
          ``ErisPulse.scope`` 子树内的写入才触发重建（无关模块写自己的
          配置不应冲掉运行时绑定/清空判定缓存）
        - ``config.updated``：对比新旧配置树的 scope 节，相同则跳过

        :param data: 事件载荷（config.set 含 key；config.updated 含 old_config/new_config）
        """
        try:
            if isinstance(data, dict) and data.get("key") is not None:
                key = str(data["key"])
                if key and key != CONFIG_ROOT_KEY and not key.startswith(f"{CONFIG_ROOT_KEY}.scope"):
                    return
                self._load_config()
                return

            if isinstance(data, dict) and ("old_config" in data or "new_config" in data):
                old_tree = data.get("old_config")
                new_tree = data.get("new_config")
                old_scope = old_tree.get(CONFIG_ROOT_KEY, {}).get("scope") if isinstance(old_tree, dict) else None
                new_scope = new_tree.get(CONFIG_ROOT_KEY, {}).get("scope") if isinstance(new_tree, dict) else None
                if old_scope == new_scope:
                    return
        except Exception:
            # 载荷结构异常时退回保守行为：整体重建
            pass
        self._load_config()

    def _invalidate_cache(self) -> None:
        """{!--< internal-use >!--} 清空 LRU 结果缓存"""
        self._cache.clear()
        self._identity_cache.clear()
        self._action_cache.clear()

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

    def _effective_module_cfg(self, platform: str, bot_id: str | None, session_id: str | None) -> dict | None:
        """
        {!--< internal-use >!--}
        沿"平台 → Bot → 会话"解析链计算生效的模块绑定

        默认语义为**整体覆盖**：高优先级绑定完整替换低优先级；
        子级绑定含 ``merge = true`` 时与低优先级**逐条目并集**
        （modules / blocked 各自取并集）。``merge`` 为控制键，不进入条目。

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 表示不匹配 Bot 级
        :param session_id: 会话 ID（群 / 频道 / 私聊），None 表示不匹配会话级
        :return: 生效绑定 {"modules": [...], "blocked": [...]}，无绑定时返回 None
        """
        chain: list[tuple[str, str]] = [(_BUCKET_PLATFORMS, platform)]
        if bot_id:
            chain.append((_BUCKET_BOTS, bot_id))
        if session_id:
            chain.append((_BUCKET_SESSIONS, session_id))

        platforms = self._data.get(_BUCKET_PLATFORMS, {})
        bots = self._data.get(_BUCKET_BOTS, {})
        sessions = self._data.get(_BUCKET_SESSIONS, {})

        result: dict | None = None
        for bucket, key in chain:
            if bucket == _BUCKET_PLATFORMS:
                cfg = platforms.get(platform)
            elif bucket == _BUCKET_BOTS:
                plat = bots.get(platform)
                cfg = plat.get(key) if isinstance(plat, dict) else None
            else:
                plat = sessions.get(platform)
                cfg = plat.get(key) if isinstance(plat, dict) else None
            if not isinstance(cfg, dict):
                continue
            modules = [str(m) for m in (cfg.get("modules") or [])]
            blocked = [str(b) for b in (cfg.get("blocked") or [])]
            if result is not None and bool(cfg.get("merge")):
                for m in modules:
                    if m not in result["modules"]:
                        result["modules"].append(m)
                for b in blocked:
                    if b not in result["blocked"]:
                        result["blocked"].append(b)
            else:
                result = {"modules": modules, "blocked": blocked}
        return result

    def _get_binding(
        self, platform: str, bot_id: str | None, session_id: str | None
    ) -> tuple[Callable[[str], bool] | None, Callable[[str], bool] | None] | None:
        """
        {!--< internal-use >!--}
        获取平台 / Bot / 会话的生效模块绑定（含 merge 链式合并）

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 表示不匹配 Bot 级
        :param session_id: 会话 ID（群 / 频道 / 私聊），None 表示不匹配会话级
        :return: (modules 匹配器, blocked 匹配器) 或 None
        """
        cfg = self._effective_module_cfg(platform, bot_id, session_id)
        if cfg is None:
            return None
        return self._normalize(cfg)

    def is_allowed(
        self,
        platform: str,
        bot_id: str | None,
        module_name: str | None,
        session_id: str | None = None,
    ) -> bool:
        """
        判断模块是否允许在指定 Bot / 会话使用（① 模块维度）

        模块名匹配大小写不敏感，条目支持 glob / ``re:`` 正则。
        结果带 LRU 缓存，配置变更 / set / delete 时自动失效。
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
        identity = self._data.get("identity", {})

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
        判断事件是否放行（② 身份维度：谁的事件收不收）

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

    # ==================== ③ 出站维度 ====================

    def is_action_allowed(self, owner: str, action: str, name: str | None = None) -> bool:
        """
        判断模块是否允许执行某类出站动作（④ 出站维度）

        判定语义：**默认允许**——未配置、或 owner 为空（框架层调用）均视为允许。
        规则判定顺序：``deny = true`` → 拒绝；``deny`` 列表命中 ``name`` → 拒绝；
        ``allow`` 列表非空且 ``name`` 未命中（或未提供）→ 拒绝；其余放行。
        结果带 LRU 缓存，配置变更 / set / delete 时自动失效。

        :param owner: 模块名（owner）
        :param action: 动作类型，取值 ``_ACTION_NAMES``（"send" / "api" / "request"）
        :param name: 具体调用名（send 传发送方法名如 "Text" / "Image"，
                     api 传标准动作名如 "get_group_info"；request 无需提供）
        :return: 是否允许执行

        :example:
        >>> scope.is_action_allowed("MyModule", "send")
        True
        >>> scope.is_action_allowed("MyModule", "send", name="Image")
        False
        """
        if not owner:
            return True
        if action not in _ACTION_NAMES:
            raise ValueError(
                i18n.t("core.scope.unknown_action", action=action, actions=", ".join(_ACTION_NAMES))
            )
        self._stats["action_checks"] += 1

        cache_key = (str(owner), action, str(name) if name else None)
        cached = self._action_cache.get(cache_key)
        if cached is not None:
            self._stats["cache_hits"] += 1
            return cached
        self._stats["cache_misses"] += 1

        allowed = self._compute_action_allowed(cache_key[0], action, cache_key[2])
        self._put_cache(self._action_cache, cache_key, allowed)
        if not allowed:
            self._stats["action_denied"] += 1
        return allowed

    def _compute_action_allowed(self, owner: str, action: str, name: str | None) -> bool:
        """{!--< internal-use >!--} 计算出站动作是否允许（无缓存）"""
        raw = self._data.get("actions", {}).get(owner, {}).get(action)
        rule = _normalize_action_rule(raw) if raw is not None else {}
        if not rule:
            return True
        deny = rule.get("deny")
        if deny is True:
            return False
        if isinstance(deny, list) and deny and name and text_match.compile_entry_list(deny)(name):
            return False
        allow = rule.get("allow")
        if isinstance(allow, list) and allow:
            if not name or not text_match.compile_entry_list(allow)(name):
                return False
        return True

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

    @staticmethod
    def _logger_trace(message: str) -> None:
        """{!--< internal-use >!--} 输出 TRACE 日志（logger 未就绪时静默）"""
        try:
            from .logger import logger

            logger.trace(message)
        except (ImportError, AttributeError):
            pass

    # ==================== 维度化便捷读写（参数签名，IDE 友好） ====================

    @staticmethod
    def _module_path(platform: str, bot_id: str | None, session_id: str | None) -> str:
        """{!--< internal-use >!--} 模块维度路径（会话 > Bot > 平台）"""
        if session_id:
            return f"{_BUCKET_SESSIONS}.{platform}.{session_id}"
        if bot_id:
            return f"{_BUCKET_BOTS}.{platform}.{bot_id}"
        return f"{_BUCKET_PLATFORMS}.{platform}"

    @staticmethod
    def _identity_path(platform: str, bot_id: str | None, session_id: str | None, user_id: str | None) -> str:
        """{!--< internal-use >!--} 身份维度路径（用户 > 会话 > Bot > 适配器）"""
        if user_id:
            return f"identity.{_IDENTITY_USERS}.{platform}.{user_id}"
        if session_id:
            return f"identity.{_IDENTITY_SESSIONS}.{platform}.{session_id}"
        if bot_id:
            return f"identity.{_IDENTITY_BOTS}.{platform}.{bot_id}"
        return f"identity.{_IDENTITY_ADAPTERS}.{platform}"

    # ---- ① 模块维度 ----

    def set_module(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        *,
        modules: list[str] | None = None,
        blocked: list[str] | None = None,
        merge: bool = False,
        persist: bool = True,
    ) -> None:
        """
        绑定模块作用域（① 模块维度）

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID，None 且 session_id 为空时绑定平台级
        :param session_id: 会话 ID（群 / 频道 / 私聊）。指定时绑定该会话；
                           否则有 bot_id 时绑定该 Bot；否则绑定平台级
        :param modules: 白名单模块条目（精确 / glob / ``re:`` 正则）
        :param blocked: 黑名单模块条目
        :param merge: True 时与该级现有绑定**逐条目并集**（modules / blocked 各自合并），
                      False 整体替换该节点（默认）
        :param persist: 是否持久化到配置文件 (默认: True)

        :example:
        >>> scope.set_module("onebot11", bot_id="123456", modules=["Chat", "Tool*"])
        >>> scope.set_module("onebot11", bot_id="123456", modules=["Music"], merge=True)
        """
        path = self._module_path(platform, bot_id, session_id)
        new_modules = [str(m) for m in (modules or [])]
        new_blocked = [str(b) for b in (blocked or [])]
        if merge:
            existing = self.get(path) or {}
            merged = list(existing.get("modules") or [])
            merged_blocked = list(existing.get("blocked") or [])
            merged += [m for m in new_modules if m not in merged]
            merged_blocked += [b for b in new_blocked if b not in merged_blocked]
            binding = {"modules": merged, "blocked": merged_blocked}
        else:
            binding = {"modules": new_modules, "blocked": new_blocked}
        self.set(path, binding, persist=persist)

    def get_module(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        default=None,
    ):
        """
        读取该层级原始模块绑定（不含 merge 跨级合并的最终生效结果，
        需判定生效性请用 :meth:`is_allowed`）

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID
        :param session_id: 会话 ID
        :param default: 无绑定时返回值（默认 None）
        :return: ``{"modules": [...], "blocked": [...]}`` 或 default
        """
        return self.get(self._module_path(platform, bot_id, session_id), default)

    def delete_module(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        persist: bool = True,
    ) -> bool:
        """
        移除该层级模块绑定（恢复 default_allow 兜底）

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID
        :param session_id: 会话 ID
        :param persist: 是否持久化到配置文件 (默认: True)
        :return: 是否存在并被删除
        """
        return self.delete(self._module_path(platform, bot_id, session_id), persist=persist)

    # ---- ② 身份维度 ----

    def set_identity(
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
        绑定身份准入策略（② 身份维度，层级由参数决定：用户 > 会话 > Bot > 适配器）

        绑定键支持 glob / ``re:`` 正则（如 ``user_id="spam_*"``）。

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID
        :param session_id: 会话 ID
        :param user_id: 用户 ID
        :param allow: 放行该来源事件
        :param deny: 拒绝该来源事件（allow 与 deny 同时给定时以 deny 为准）
        :param persist: 是否持久化到配置文件 (默认: True)

        :example:
        >>> scope.set_identity("onebot11", user_id="u_bad", deny=True)   # 拉黑
        >>> scope.set_identity("onebot11", user_id="spam_*", deny=True)  # glob 批量拉黑
        >>> scope.set_identity("onebot11", session_id="g1", allow=True)  # 例外放行
        """
        if deny:
            binding: dict = {"deny": True}
        elif allow:
            binding = {"allow": True}
        else:
            from .i18n import i18n

            raise ValueError(i18n.t("core.scope.identity_policy_required"))
        self.set(self._identity_path(platform, bot_id, session_id, user_id), binding, persist=persist)

    def get_identity(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        default=None,
    ):
        """
        读取该来源的身份绑定（原始配置形态，含 glob 键不展开；
        需判定生效性请用 :meth:`is_identity_allowed`）

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID
        :param session_id: 会话 ID
        :param user_id: 用户 ID
        :param default: 无绑定时返回值（默认 None）
        :return: ``{"allow": True}`` / ``{"deny": True}`` 或 default
        """
        return self.get(self._identity_path(platform, bot_id, session_id, user_id), default)

    def delete_identity(
        self,
        platform: str,
        bot_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        persist: bool = True,
    ) -> bool:
        """
        移除该来源的身份绑定（恢复 default_allow 兜底）

        :param platform: 平台名称
        :param bot_id: Bot 用户 ID
        :param session_id: 会话 ID
        :param user_id: 用户 ID
        :param persist: 是否持久化到配置文件 (默认: True)
        :return: 是否存在并被删除
        """
        return self.delete(self._identity_path(platform, bot_id, session_id, user_id), persist=persist)

    # ---- ③ 出站维度 ----

    def set_action(
        self,
        module: str,
        action: str,
        *,
        allow: str | list[str] | None = None,
        deny: bool | str | list[str] | None = None,
        persist: bool = True,
    ) -> None:
        """
        设置模块某类出站动作的限制规则（③ 出站维度）

        仅影响本模块从事件处理器（handler 执行期 owner 上下文）发起的出站调用；
        框架层内部调用（owner 为空）恒放行。

        :param module: 模块名
        :param action: 动作类型（"send" / "api" / "request"）
        :param allow: 白名单条目（str 或 list；send 匹配发送方法名、api 匹配标准动作名）
        :param deny: 全禁（True）或黑名单条目（str / list）
        :param persist: 是否持久化到配置文件 (默认: True)

        :example:
        >>> scope.set_action("MyModule", "send", deny=True)                # 全禁发送
        >>> scope.set_action("MyModule", "send", allow=["Text"])           # 仅允许发文本
        >>> scope.set_action("MyModule", "api", deny=["set_*", "leave_*"]) # 禁管理类 API
        """
        if action not in _ACTION_NAMES:
            raise ValueError(
                i18n.t("core.scope.unknown_action", action=action, actions=", ".join(_ACTION_NAMES))
            )
        if not module:
            raise ValueError(i18n.t("core.scope.module_required"))
        rule: dict = {}
        if allow is not None:
            rule["allow"] = [allow] if isinstance(allow, str) else list(allow)
        if deny is not None:
            if isinstance(deny, bool):
                rule["deny"] = deny
            elif isinstance(deny, str):
                rule["deny"] = [deny]
            else:
                rule["deny"] = list(deny)
        path = f"actions.{module}.{action}"
        # 参数化方法为整体替换语义：本次调用描述该动作完整的限制规则
        # （先删后写，避免通用 set 的 dict 深合并残留旧的 deny / allow 键）
        self.delete(path, persist=False)
        if rule:
            self.set(path, rule, persist=persist)
        elif persist:
            from ..runtime.frame_config import set_erispulse_section as _ses

            _ses("scope.actions", self._data.get("actions", {}))

    def get_action(self, module: str, action: str, default=None):
        """
        读取模块某类出站动作的原始规则（bool 原样存储，判定层归一化）

        :param module: 模块名
        :param action: 动作类型
        :param default: 未配置时返回值（默认 None）
        :return: ``{"allow": [...], "deny": ...}`` / ``False`` 等原始形态或 default
        """
        return self.get(f"actions.{module}.{action}", default)

    def delete_action(self, module: str, action: str | None = None, persist: bool = True) -> bool:
        """
        移除模块的出站动作限制（恢复默认允许）

        :param module: 模块名
        :param action: 动作类型；None 表示移除该模块全部动作限制
        :param persist: 是否持久化到配置文件 (默认: True)
        :return: 是否有内容被移除
        """
        if action is None:
            return self.delete(f"actions.{module}", persist=persist)
        return self.delete(f"actions.{module}.{action}", persist=persist)

    # ==================== 字典式配置读写 ====================

    @staticmethod
    def _split_path(path: str) -> list[str]:
        """{!--< internal-use >!--} 点分路径切分为段（过滤空段）"""
        return [part for part in str(path).split(".") if part]

    def _node_at(self, path: str):
        """{!--< internal-use >!--} 按点分路径取节点（不存在返回 None）"""
        node = self._data
        for part in self._split_path(path):
            if not isinstance(node, dict):
                return None
            node = node.get(part)
        return node

    def get(self, path: str, default=None):
        """
        读取作用域配置树中任意节（深拷贝）

        :param path: 点分路径，如 ``"platforms.onebot11"``、``"identity.users.onebot11"``
                     （身份）、``"actions.MyModule"``（出站）；
                     空路径返回整棵树
        :param default: 节不存在时的返回值（默认 None）
        :return: 节的深拷贝；不存在时返回 ``default``

        :example:
        >>> scope.get("actions.MyModule.send", {})
        {"deny": True}
        """
        node = self._node_at(path)
        return copy.deepcopy(node) if node is not None else default

    def set(self, path: str, value, persist: bool = True) -> None:
        """
        写入作用域配置树中任意节（dict 深合并，标量直接覆盖）

        写入后判定缓存自动失效，配置即时生效。

        :param path: 点分路径，如 ``"bots.onebot11.123456"``（模块绑定）、
                     ``"identity.users.onebot11.u_bad"``（拉黑用户）、

                     ``"actions.MyModule.send"``（出站规则）
        :param value: 写入值（dict 时与现有值深合并，其余类型直接覆盖）
        :param persist: 是否持久化到配置文件 (默认: True)。
            ``persist=False`` 为运行时绑定：写入覆盖层，任意配置写入/重载
            均不会冲掉（但进程重启后丢失，且模块卸载时随调用方清理）

        :example:
        >>> scope.set("bots.onebot11.123456", {"modules": ["Chat"], "blocked": []})
        >>> scope.set("identity.users.onebot11.u_bad", {"deny": True})   # 拉黑用户
        >>> scope.set("actions.MyModule.send", {"deny": True})           # 全禁发送
        """
        parts = self._split_path(path)
        if not parts:
            raise ValueError(i18n.t("core.scope.path_required"))
        node = self._data
        for part in parts[:-1]:
            child = node.get(part)
            if not isinstance(child, dict):
                child = {}
                node[part] = child
            node = child
        last = parts[-1]
        if isinstance(value, dict) and isinstance(node.get(last), dict):
            _deep_merge(node[last], value)
        else:
            node[last] = value
        self._invalidate_cache()
        if persist:
            # 用户持久化语义：清除该路径的运行时覆盖记录（持久化值优先）
            self._clear_runtime_overrides(path)
            # 先快照内存最终态：持久化内部同步触发的热更新会以（延迟刷盘期的）
            # 旧配置重建配置树，写后用快照重放保证"写后立读"
            snapshot = copy.deepcopy(self._data)
            update_erispulse_config({"scope": snapshot})
            self._apply_tree(snapshot)
        else:
            # 运行时绑定：记录覆盖层，配置树重建后按序重放（不落盘）
            self._runtime_overrides[path] = copy.deepcopy(value)
            self._record_runtime_owner(path)

    def delete(self, path: str, persist: bool = True) -> bool:
        """
        删除作用域配置树中任意键（父节经整节替换持久化，支持级联清空空父节）

        :param path: 点分路径，如 ``"bots.onebot11.123456"``、
                     ``"identity.users.onebot11.u_bad"``、``"actions.MyModule.send"``
        :param persist: 是否持久化到配置文件 (默认: True)。
            ``persist=False`` 为运行时删除：覆盖层记录删除标记，
            任意配置写入/重载后仍保持"已删除"语义
        :return: 是否存在并被删除

        :example:
        >>> scope.delete("bots.onebot11.123456")       # 移除 Bot 绑定
        >>> scope.delete("identity.users.onebot11.u_bad")  # 取消拉黑
        >>> scope.delete("actions.MyModule")           # 解除模块全部出站限制
        """
        parts = self._split_path(path)
        if not parts:
            raise ValueError(i18n.t("core.scope.path_required"))
        parent = self._node_at(".".join(parts[:-1])) if len(parts) > 1 else self._data
        if not isinstance(parent, dict) or parts[-1] not in parent:
            return False
        del parent[parts[-1]]
        self._invalidate_cache()
        if persist:
            self._clear_runtime_overrides(path)
            parent_path = ".".join(parts[:-1])
            snapshot = copy.deepcopy(self._data)
            set_erispulse_section(f"scope.{parent_path}" if parent_path else "scope", parent)
            # 同 set：持久化内部热更新回读旧值后，用快照重放内存最终态
            self._apply_tree(snapshot)
        else:
            # 运行时删除：记录删除标记，配置树重建后重放删除
            self._runtime_overrides[path] = _RUNTIME_DELETED
            self._record_runtime_owner(path)
        return True

    def __getitem__(self, path: str):
        """``scope[path]``：等价 :meth:`get`，节点不存在时抛 KeyError"""
        node = self._node_at(path)
        if node is None:
            raise KeyError(path)
        return copy.deepcopy(node)

    def __setitem__(self, path: str, value) -> None:
        """``scope[path] = value``：等价 :meth:`set`（默认持久化）"""
        self.set(path, value)

    def __delitem__(self, path: str) -> None:
        """``del scope[path]``：等价 :meth:`delete`，不存在时抛 KeyError"""
        if not self.delete(path):
            raise KeyError(path)

    def __contains__(self, path: str) -> bool:
        """``path in scope``：判断配置树中是否存在该节点"""
        return self._node_at(path) is not None

    # ==================== 全局操作 ====================

    def clear(self) -> None:
        """清空所有作用域配置（仅内存生效，不持久化；含运行时覆盖层）"""
        self._data = {
            _BUCKET_PLATFORMS: {},
            _BUCKET_BOTS: {},
            _BUCKET_SESSIONS: {},
            "identity": {
                _IDENTITY_ADAPTERS: {},
                _IDENTITY_BOTS: {},
                _IDENTITY_SESSIONS: {},
                _IDENTITY_USERS: {},
            },
            "actions": {},
        }
        self._runtime_overrides.clear()
        self._runtime_owners.clear()
        self._invalidate_cache()

    def stats(self) -> dict[str, int]:
        """
        获取作用域运行统计

        统计项：``module_calls`` / ``module_filtered``（模块维度）、
        ``identity_checks`` / ``identity_denied``（身份维度）、
        ``action_checks`` / ``action_denied``（出站维度）、
        ``cache_hits`` / ``cache_misses``（LRU 缓存）。

        :return: 统计字典
        """
        return dict(self._stats)

    def reset_stats(self) -> None:
        """重置作用域运行统计"""
        for key in self._stats:
            self._stats[key] = 0

    def topology(self) -> dict:
        """
        获取作用域配置的结构化数据（便于 WebUI 展示拓扑树）

        等价于整棵配置树的深拷贝。

        :return: 全维度配置结构（模块 / 身份 / 文本 / 出站动作）
        """
        return copy.deepcopy(self._data)

    def __repr__(self) -> str:
        platforms = list(self._data.get(_BUCKET_PLATFORMS, {}).keys())
        bots = list(self._data.get(_BUCKET_BOTS, {}).keys())
        sessions = list(self._data.get(_BUCKET_SESSIONS, {}).keys())
        actions = list(self._data.get("actions", {}).keys())
        return (
            f"<ScopeManager platforms={platforms} bots={bots} sessions={sessions} "
            f"actions={actions} default_allow={self._default_allow}>"
        )


# 模块级单例
scope: ScopeManager = ScopeManager()

__all__ = [
    "DEFAULT_CACHE_SIZE",
    "ScopeManager",
    "scope",
]
