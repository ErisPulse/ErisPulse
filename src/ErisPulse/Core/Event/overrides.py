"""
ErisPulse 事件覆写系统（overrides）

不改模块代码，按事件类型覆写任意事件处理器的触发条件与实现参数。
控制权完全交给用户：在处理器注册的**上层**（配置 ``ErisPulse.event.overrides``
或运行时 ``sdk.Event.overrides``）声明，事件管线在过滤链自动读取并执行。

事件类型遵循 OneBot12 标准：**meta** / **message** / **notice** / **request**；
**command** 为 ErisPulse 扩展类型。每个类型拥有各自的覆写规格：

===== ================ ==================================
类型   可覆写参数        说明
===== ================ ==================================
meta   detail_types     detail_type 白名单（connect 等）
notice detail_types      + pattern / regex
request detail_types     + pattern / regex
message pattern / regex  文本触发条件
command master 等参数    实现参数覆写 + acl 用户准入
acl    allow / deny      命令用户黑白名单（command 专属，按命令名 glob）
===== ================ ==================================

配置树（``ErisPulse.event.overrides``）：

.. code-block:: toml

    # message：覆写文本触发条件
    [ErisPulse.event.overrides.message.MyModule]
    pattern = "签到*"
    regex = "re:\\\\d+"

    # notice / request / meta：detail_type 白名单（条目支持精确 / glob / re: 正则）
    [ErisPulse.event.overrides.notice.MyModule]
    detail_types = ["group_increase"]
    [ErisPulse.event.overrides.meta.MyModule]
    detail_types = ["connect"]

    # command（扩展类型）：实现参数覆写（用户优先，可收紧或放开开发者默认）
    [ErisPulse.event.overrides.command.MyModule]
    hidden = true
    [ErisPulse.event.overrides.command.MyModule.restart]
    master = true
    aliases = ["rs"]

    # acl（command 专属）：用户黑白名单（用户标识 "platform:uid"）
    [ErisPulse.event.overrides.acl."roll*"]
    allow = ["onebot11:u_vip"]
    deny = ["onebot11:u_bad"]

    # ACL 兜底（false = 严格模式：无 ACL 即拒）
    acl_default_allow = true

覆写语义：

- **pattern / regex**（文本条件）：与代码内条件 AND；无文本的事件不受约束，直接放行
- **detail_types**：detail_type 白名单，未命中即不触发；事件缺 detail_type 时放行
- **command 参数**：与开发者声明深合并，本次覆写优先；覆写键 ``master`` 映射存储键 ``must_master``
- **acl**：``deny`` 命中 → 拒绝；``allow`` 非空且未命中 → 拒绝；未配置遵循 ``acl_default_allow``

匹配条目统一语法（见 :mod:`ErisPulse.Core.text_match`）：
**精确名** / **glob**（``*`` / ``?`` / ``[seq]``）/ **``re:`` 正则**，默认大小写不敏感。

{!--< tips >!--}
1. 通过 ``from ErisPulse.Core.Event import overrides`` 导入（``sdk.Event.overrides`` 同一模块）
2. 类型子命名空间：``overrides.message.set("My", pattern="签到*")`` /
   ``overrides.command.set("My", "roll", master=True)`` / ``overrides.acl.set("roll*", deny=[...])``
3. 每类型均有 ``set`` / ``get`` / ``delete`` 三件套；acl 额外提供 ``is_allowed`` 判定
{!--< /tips >!--}
"""

import copy

from ...runtime.context import current_owner
from ...runtime.frame_config import set_erispulse_section
from .. import text_match

# 类型规格注册表：每事件类型的可覆写参数白名单（新参数/新类型在此注册）
_TYPE_SPECS: dict[str, frozenset] = {
    "message": frozenset({"detail_types", "pattern", "regex"}),
    "notice": frozenset({"detail_types", "pattern", "regex"}),
    "request": frozenset({"detail_types", "pattern", "regex"}),
    "meta": frozenset({"detail_types"}),
}

# command（扩展类型）可覆写的实现参数
_COMMAND_PARAMS = frozenset({"master", "hidden", "aliases", "prefix", "help", "usage"})

# 顶层 acl 类别键
_ACL_SECTION = "acl"

# 内存分区缓存（随配置热更新整体重建）
_sections: dict[str, dict[str, dict]] = {t: {} for t in _TYPE_SPECS}
_command: dict[str, dict] = {}
_acl: dict[str, dict] = {}
_acl_default_allow: bool = True

# 运行时写入（persist=False）的调用方归属记录：路径键 → owner。
# persist=True 的写入属用户配置语义，不追踪也不清理；仅内存态运行时写入
# 在模块卸载时随 owner 兜底清理（unregister_by_owner）
_runtime_owner_records: dict[str, str] = {}


def _record_runtime_owner(path: str, persist: bool) -> None:
    """{!--< internal-use >!--} 记录（persist=False）或清除（persist=True）路径的调用方归属"""
    if persist:
        _runtime_owner_records.pop(path, None)
        return
    owner = current_owner.get()
    if owner is not None:
        _runtime_owner_records[path] = owner

# 配置校验告警去重（同一路径同一问题只告警一次）
_warned: set[str] = set()


def _warn_invalid(path: str, actual: str) -> None:
    """{!--< internal-use >!--} 输出配置格式告警（同一路径去重）"""
    key = f"event.overrides:{path}:{actual}"
    if key in _warned:
        return
    _warned.add(key)
    try:
        from ..i18n import i18n
        from ..logger import logger

        logger.warning(i18n.t("core.event.overrides_invalid", path=path, actual=actual))
    except Exception:
        pass


def _snapshot() -> dict:
    """{!--< internal-use >!--} 内存最终态快照（供持久化后重放，保证写后立读）"""
    snap: dict = {t: dict(sections) for t, sections in _sections.items()}
    snap["command"] = copy.deepcopy(_command)
    snap[_ACL_SECTION] = copy.deepcopy(_acl)
    snap["acl_default_allow"] = _acl_default_allow
    return snap


def _apply(tree: dict) -> None:
    """{!--< internal-use >!--} 校验并应用完整覆写配置树到内存（含格式校验）"""
    global _command, _acl, _acl_default_allow, _sections

    tree = tree if isinstance(tree, dict) else {}
    if not isinstance(tree, dict):
        _warn_invalid("event.overrides", type(tree).__name__)
        tree = {}

    new_sections: dict[str, dict[str, dict]] = {t: {} for t in _TYPE_SPECS}
    for type_name, spec in _TYPE_SPECS.items():
        section = tree.get(type_name)
        if section is None:
            continue
        if not isinstance(section, dict):
            _warn_invalid(f"event.overrides.{type_name}", type(section).__name__)
            continue
        for owner, params in section.items():
            if not isinstance(params, dict):
                _warn_invalid(f"event.overrides.{type_name}.{owner}", type(params).__name__)
                continue
            bad = [k for k in params if k not in spec]
            for bad_key in bad:
                _warn_invalid(f"event.overrides.{type_name}.{owner}.{bad_key}", "unknown param")
            cleaned = {k: v for k, v in params.items() if k in spec}
            if cleaned:
                new_sections[type_name][owner] = cleaned

    # command（扩展类型）：模块级标量参数 + 命令级子表
    new_command: dict[str, dict] = {}
    cmd_section = tree.get("command")
    if cmd_section is not None:
        if not isinstance(cmd_section, dict):
            _warn_invalid("event.overrides.command", type(cmd_section).__name__)
        else:
            for owner, cfg in cmd_section.items():
                if not isinstance(cfg, dict):
                    _warn_invalid(f"event.overrides.command.{owner}", type(cfg).__name__)
                    continue
                entry: dict = {}
                for key, value in cfg.items():
                    if isinstance(value, dict):
                        bad = [k for k in value if k not in _COMMAND_PARAMS]
                        for bad_key in bad:
                            _warn_invalid(f"event.overrides.command.{owner}.{key}.{bad_key}", "unknown param")
                        cleaned = {k: v for k, v in value.items() if k in _COMMAND_PARAMS}
                        if cleaned:
                            entry[key] = cleaned
                    elif key in _COMMAND_PARAMS:
                        entry[key] = value
                    else:
                        _warn_invalid(f"event.overrides.command.{owner}.{key}", "unknown param")
                if entry:
                    new_command[owner] = entry

    # acl（command 专属）：命令用户黑白名单
    new_acl: dict[str, dict] = {}
    acl_section = tree.get(_ACL_SECTION)
    if acl_section is not None:
        if not isinstance(acl_section, dict):
            _warn_invalid(f"event.overrides.{_ACL_SECTION}", type(acl_section).__name__)
        else:
            for cmd_name, cfg in acl_section.items():
                if not isinstance(cfg, dict):
                    _warn_invalid(f"event.overrides.{_ACL_SECTION}.{cmd_name}", type(cfg).__name__)
                    continue
                bad = [k for k in cfg if k not in ("allow", "deny")]
                for bad_key in bad:
                    _warn_invalid(f"event.overrides.{_ACL_SECTION}.{cmd_name}.{bad_key}", "unknown key")
                entry: dict = {}
                for key in ("allow", "deny"):
                    value = cfg.get(key)
                    if value is None:
                        continue
                    if isinstance(value, str):
                        value = [value]
                    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                        _warn_invalid(f"event.overrides.{_ACL_SECTION}.{cmd_name}.{key}", type(value).__name__)
                        continue
                    entry[key] = list(value)
                if entry:
                    new_acl[cmd_name] = entry

    # acl 兜底开关
    raw_default = tree.get("acl_default_allow", True)
    new_default = bool(raw_default)
    if not isinstance(raw_default, bool) and raw_default is not None:
        _warn_invalid("event.overrides.acl_default_allow", type(raw_default).__name__)

    _sections = new_sections
    _command = new_command
    _acl = new_acl
    _acl_default_allow = new_default


def _reload(_data: dict | None = None) -> None:
    """配置变更回调：从配置重建覆写缓存"""
    try:
        from ...runtime import get_event_config

        event_config = get_event_config() or {}
    except Exception:
        event_config = {}
    overrides_tree = (event_config.get("overrides") or {}) if isinstance(event_config, dict) else {}
    _apply(overrides_tree if isinstance(overrides_tree, dict) else {})


def _persist_section(section_key: str, value) -> None:
    """{!--< internal-use >!--} 持久化单个覆写分区，并以内存快照重放（写后立读）"""
    snapshot = _snapshot()
    set_erispulse_section(f"event.overrides.{section_key}" if section_key else "event.overrides", value)
    _apply(snapshot)


# ==================== 通用判定 ====================


def condition_for(event_type: str, owner: str):
    """
    {!--< internal-use >!--}
    获取某事件类型下某模块的覆写过滤条件（detail_types 白名单 + pattern/regex 文本条件）

    :param event_type: 事件类型（message / notice / request / meta）
    :param owner: 模块名
    :return: 事件条件函数，该类型未配置覆写时返回 None
    """
    params = _sections.get(event_type, {}).get(owner)
    if not isinstance(params, dict):
        return None

    detail_types = params.get("detail_types")
    pattern = params.get("pattern")
    regex = params.get("regex")

    dt_matcher = text_match.compile_entry_list(detail_types) if detail_types else None
    if isinstance(regex, str) and regex.startswith(text_match.REGEX_PREFIX):
        regex = regex[len(text_match.REGEX_PREFIX) :]
    text_matcher = text_match.compile_text_matcher(pattern, regex) if (pattern or regex) else None

    def _cond(event) -> bool:
        if dt_matcher is not None:
            dt = str(event.get("detail_type") or "")
            # detail_type 缺失的未知事件放行（避免误杀），非空则必须命中白名单
            if dt and not dt_matcher(dt):
                return False
        if text_matcher is not None:
            # 无文本事件不受文本条件约束（pattern 不会误杀 notice / meta）
            try:
                if not text_match.extract_text(event):
                    return True
            except Exception:
                pass
            return text_matcher(event)  # matcher 内部自行提取文本
        return True

    return _cond


def topology() -> dict:
    """
    获取事件覆写配置的结构化数据（便于 WebUI 展示拓扑树）

    :return: 按事件类型分组的覆写结构 + command / acl 类别
    """
    snap = _snapshot()
    snap.pop("acl_default_allow", None)
    return snap


def clear() -> None:
    """清空全部覆写配置（仅内存生效，不持久化）"""
    global _command, _acl
    for t in _sections:
        _sections[t] = {}
    _command = {}
    _acl = {}
    _runtime_owner_records.clear()


def _persist_all() -> None:
    """{!--< internal-use >!--} 全量持久化（acl_default_allow 标量需要整节写入）"""
    set_erispulse_section("event.overrides", _snapshot())


# ==================== 类型子命名空间 ====================


class _TypeNamespace:
    """
    {!--< internal-use >!--}
    标准事件类型的覆写命名空间（message / notice / request / meta）

    提供 ``set`` / ``get`` / ``delete`` 三件套；可覆写参数由 :data:`_TYPE_SPECS`
    规格约束（未知参数抛 ValueError，fail-fast）。
    """

    def __init__(self, type_name: str):
        self.type_name = type_name

    def _check(self, params: dict) -> dict:
        spec = _TYPE_SPECS[self.type_name]
        bad = [k for k in params if k not in spec]
        if bad:
            raise ValueError(
                f"unknown override params for {self.type_name}: {bad}, expected one of {sorted(spec)}"
            )
        cleaned: dict = {}
        for k, v in params.items():
            if v is None:
                continue
            if k == "regex" and isinstance(v, str) and not v.startswith(text_match.REGEX_PREFIX):
                v = text_match.REGEX_PREFIX + v  # regex 源码自动补 re: 前缀
            if k == "detail_types" and isinstance(v, str):
                v = [v]  # 单条目简写
            cleaned[k] = v
        return cleaned

    def set(self, module: str, *, persist: bool = True, **params) -> None:
        """
        覆写该模块在本事件类型的触发条件（整体替换语义）

        :param module: 模块名
        :param persist: 是否持久化到配置文件 (默认: True)
        :param params: 该类型的可覆写参数（``detail_types`` / ``pattern`` / ``regex``，
                       按类型规格而定）；全空参数 = 移除覆写

        :example:
        >>> overrides.message.set("ChatModule", pattern="闲聊*")
        >>> overrides.notice.set("MyModule", detail_types=["group_increase"])
        """
        cleaned = self._check(params)
        section = dict(_sections.get(self.type_name, {}))
        if cleaned:
            section[module] = cleaned
        else:
            section.pop(module, None)
        _sections[self.type_name] = section
        if persist:
            _persist_section(self.type_name, section)
        _record_runtime_owner(f"{self.type_name}:{module}", persist)

    def get(self, module: str, default=None):
        """
        读取该模块在本事件类型的覆写参数

        :param module: 模块名
        :param default: 未配置时返回值（默认 None）
        :return: 覆写参数字典或 default
        """
        cfg = _sections.get(self.type_name, {}).get(module)
        return copy.deepcopy(cfg) if cfg is not None else default

    def delete(self, module: str, persist: bool = True) -> bool:
        """
        移除该模块在本事件类型的覆写（恢复开发者声明的默认行为）

        :param module: 模块名
        :param persist: 是否持久化到配置文件 (默认: True)
        :return: 是否存在并被移除
        """
        section = _sections.get(self.type_name, {})
        if module not in section:
            return False
        section.pop(module, None)
        _sections[self.type_name] = section
        if persist:
            _persist_section(self.type_name, section)
        _runtime_owner_records.pop(f"{self.type_name}:{module}", None)
        return True


class _CommandNamespace:
    """
    command（扩展类型）的覆写命名空间

    实现参数覆写（master / hidden / aliases / prefix / help / usage，用户优先），
    支持模块级标量与命令级子表两种粒度（命令级优先）。
    """

    @staticmethod
    def _check(params: dict) -> dict:
        bad = [k for k in params if k not in _COMMAND_PARAMS]
        if bad:
            raise ValueError(
                f"unknown command override params: {bad}, expected one of {sorted(_COMMAND_PARAMS)}"
            )
        return {k: v for k, v in params.items() if v is not None}

    def set(self, owner: str, command_name: str | None = None, *, persist: bool = True, **params) -> None:
        """
        覆写命令实现参数（command 扩展类型，用户优先语义）

        覆写遵循**用户优先**：显式设置的参数直接生效（可收紧或放开开发者默认）。
        禁用统一走 acl deny，参数覆写不承载禁用语义。

        :param owner: 模块名
        :param command_name: 命令名；None 表示模块级覆写
        :param persist: 是否持久化到配置文件 (默认: True)
        :param params: 可覆写参数（master / hidden / aliases / prefix / help / usage）

        :example:
        >>> overrides.command.set("MyModule", "restart", master=True, hidden=True)
        >>> overrides.command.set("MyModule", hidden=True)   # 模块级
        """
        cleaned = self._check(params)
        entry = dict(_command.get(owner, {}))
        if command_name:
            # 整体替换该命令的子表（不继承旧值）
            if cleaned:
                entry[command_name] = cleaned
            else:
                entry.pop(command_name, None)
        # 模块级：替换标量参数，保留命令级子表
        elif cleaned:
            entry = {**cleaned, **{k: v for k, v in entry.items() if isinstance(v, dict)}}
        if entry:
            _command[owner] = entry
        else:
            _command.pop(owner, None)
        if persist:
            _persist_section("command", copy.deepcopy(_command))
        path = f"command:{owner}.{command_name}" if command_name else f"command:{owner}"
        _record_runtime_owner(path, persist)

    def get(self, owner: str, command_name: str | None = None, default=None) -> dict:
        """
        读取模块 / 命令的覆写参数（命令级优先合并）

        :param owner: 模块名
        :param command_name: 命令名；None 表示仅模块级参数
        :param default: 未配置时返回值（默认 {}）
        :return: 合并后的参数字典
        """
        module_cfg = _command.get(owner)
        if not isinstance(module_cfg, dict):
            return dict(default) if isinstance(default, dict) else {}
        result = {k: v for k, v in module_cfg.items() if not isinstance(v, dict)}
        if command_name:
            cmd_cfg = module_cfg.get(command_name)
            if isinstance(cmd_cfg, dict):
                result.update(cmd_cfg)
        return result

    def apply(self, owner: str, command_name: str, defaults: dict) -> dict:
        """
        {!--< internal-use >!--}
        把命令默认参数与覆写合并（覆写优先）

        覆写键 ``master`` 同步映射到命令存储键 ``must_master``（用户优先）。

        :param owner: 模块名
        :param command_name: 命令名
        :param defaults: 命令默认参数字典
        :return: 合并后的生效参数字典
        """
        merged = dict(defaults)
        override = self.get(owner, command_name)
        merged.update(override)
        if "master" in override:
            merged["must_master"] = bool(override["master"])
        return merged

    def delete(self, owner: str, command_name: str | None = None, persist: bool = True) -> bool:
        """
        移除模块 / 命令的覆写参数

        :param owner: 模块名
        :param command_name: 命令名；None 表示移除该模块全部覆写
        :param persist: 是否持久化到配置文件 (默认: True)
        :return: 是否有内容被移除
        """
        module_cfg = _command.get(owner)
        if not isinstance(module_cfg, dict):
            return False
        if command_name:
            if command_name not in module_cfg:
                return False
            module_cfg.pop(command_name, None)
            if not module_cfg:
                _command.pop(owner, None)
        else:
            _command.pop(owner, None)
        if persist:
            _persist_section("command", copy.deepcopy(_command))
        path = f"command:{owner}.{command_name}" if command_name else f"command:{owner}"
        _runtime_owner_records.pop(path, None)
        return True


class _AclNamespace:
    """
    acl 命名空间（command 扩展类型专属：命令用户黑白名单）

    按命令名组织（支持 glob / ``re:`` 正则，精确键优先），用户标识 ``platform:uid``。
    """

    def set(
        self,
        command_name: str,
        *,
        allow: str | list[str] | None = None,
        deny: str | list[str] | None = None,
        persist: bool = True,
    ) -> None:
        """
        设置命令的用户黑白名单

        :param command_name: 命令名（支持 glob / ``re:`` 正则）
        :param allow: 白名单（非空时仅名单内用户可执行）
        :param deny: 黑名单（deny 优先于 allow）
        :param persist: 是否持久化到配置文件 (默认: True)

        :example:
        >>> overrides.acl.set("roll*", allow=["onebot11:u_vip"])
        >>> overrides.acl.set("restart", deny="onebot11:u_bad")
        """
        if not command_name:
            raise ValueError("command_name is required")
        entry: dict = {}
        for key, value in (("allow", allow), ("deny", deny)):
            if value is None:
                continue
            if isinstance(value, str):
                value = [value]
            entry[key] = list(value)
        acl = dict(_acl)
        if entry:
            acl[command_name] = entry
        else:
            acl.pop(command_name, None)
        _acl.clear()
        _acl.update(acl)
        if persist:
            _persist_section(_ACL_SECTION, copy.deepcopy(_acl))
        _record_runtime_owner(f"{_ACL_SECTION}:{command_name}", persist)

    def match(self, command_name: str) -> dict | None:
        """
        {!--< internal-use >!--}
        获取命令的生效 ACL（精确键优先，未命中再按 glob / ``re:`` 匹配）

        :param command_name: 命令主名
        :return: {"allow": [...], "deny": [...]}，未配置时返回 None
        """
        exact = _acl.get(command_name)
        if isinstance(exact, dict):
            return exact
        for key, cfg in _acl.items():
            if text_match.compile_entry_matcher(str(key))(command_name):
                if isinstance(cfg, dict):
                    return cfg
        return None

    def get(self, command_name: str) -> dict[str, list[str]]:
        """
        查询命令当前的用户黑白名单

        :param command_name: 命令名（可含模式）
        :return: {"allow": [...], "deny": [...]}
        """
        cfg = self.match(command_name)
        return {
            "allow": list((cfg or {}).get("allow") or []),
            "deny": list((cfg or {}).get("deny") or []),
        }

    def delete(self, command_name: str, persist: bool = True) -> bool:
        """
        清除命令的用户黑白名单（恢复开发者默认权限逻辑）

        :param command_name: 命令名（可含模式）
        :param persist: 是否持久化到配置文件 (默认: True)
        :return: 是否存在并被清除
        """
        removed = False
        for key in list(_acl.keys()):
            if text_match.compile_entry_matcher(str(key))(command_name):
                _acl.pop(key, None)
                removed = True
        if removed and persist:
            _persist_section(_ACL_SECTION, copy.deepcopy(_acl))
        return removed

    def is_allowed(self, command_name: str, platform: str, user_id: str) -> bool:
        """
        判断用户对命令是否被 ACL 允许（判定链）

        ``deny`` 命中 → 拒绝；``allow`` 非空且未命中 → 拒绝；
        未配置 ACL 遵循 ``acl_default_allow``（false = 严格模式：无 ACL 即拒）。

        :param command_name: 命令主名
        :param platform: 用户所属平台
        :param user_id: 用户 ID
        :return: 是否允许执行
        """
        cfg = self.match(command_name)
        if cfg is None:
            return _acl_default_allow
        user_tag = f"{platform}:{user_id}"
        if user_tag in (cfg.get("deny") or []):
            return False
        allow_list = cfg.get("allow") or []
        return not (allow_list and user_tag not in allow_list)

    @property
    def default_allow(self) -> bool:
        """ACL 兜底开关（``event.overrides.acl_default_allow``）"""
        return _acl_default_allow

    def list_commands(self) -> list[str]:
        """
        列出已配置 ACL 的命令名（含 glob 模式键）

        :return: 命令名列表（排序）
        """
        return sorted(_acl.keys())


# 类型子命名空间实例（message / notice / request / meta / command / acl）
message: _TypeNamespace = _TypeNamespace("message")
notice: _TypeNamespace = _TypeNamespace("notice")
request: _TypeNamespace = _TypeNamespace("request")
meta: _TypeNamespace = _TypeNamespace("meta")
command: _CommandNamespace = _CommandNamespace()
acl: _AclNamespace = _AclNamespace()


def unregister_by_owner(caller: str) -> int:
    """
    兜底清理指定调用方在运行时（persist=False）写入的全部覆写

    仅清理内存态覆写；``persist=True`` 的写入属用户配置语义，不在此
    清理范围（随配置持久保留，需用户显式删除）。供模块卸载时调用，
    避免卸载后模块运行时写入的覆写残留生效。

    :param caller: 调用方（模块名 / 适配器平台名）
    :return: int 清理的覆写条目数量
    """
    paths = [p for p, o in _runtime_owner_records.items() if o == caller]
    removed = 0
    for path in paths:
        _runtime_owner_records.pop(path, None)
        kind, _, rest = path.partition(":")
        if kind in _TYPE_SPECS:
            if _sections.get(kind, {}).pop(rest, None) is not None:
                removed += 1
        elif kind == "command":
            module, _, cmd = rest.partition(".")
            module_cfg = _command.get(module)
            if not isinstance(module_cfg, dict):
                continue
            if cmd:
                if module_cfg.pop(cmd, None) is not None:
                    removed += 1
                    if not module_cfg:
                        _command.pop(module, None)
            elif _command.pop(module, None) is not None:
                removed += 1
        elif kind == _ACL_SECTION:
            if _acl.pop(rest, None) is not None:
                removed += 1
    return removed


# 订阅配置热更新：event 配置变更时自动重建覆写缓存
try:
    from .lifecycle import lifecycle

    lifecycle.register("config.updated", _reload)
    lifecycle.register("config.set", _reload)
except Exception:
    pass

# 初始加载
_reload()

__all__ = [
    "acl",
    "clear",
    "command",
    "condition_for",
    "message",
    "meta",
    "notice",
    "request",
    "topology",
    "unregister_by_owner",
]
