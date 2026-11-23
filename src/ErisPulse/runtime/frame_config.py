"""
ErisPulse 框架配置管理模块

提供默认配置定义及配置完整性管理功能
"""

import copy
import os
import threading
from typing import Any

from ..Core.constants import (
    CONFIG_ROOT_KEY,
    DEFAULT_COMMAND_ALLOW_SPACE_PREFIX,
    DEFAULT_COMMAND_BLOCK,
    DEFAULT_COMMAND_CASE_SENSITIVE,
    DEFAULT_COMMAND_MUST_AT_BOT,
    DEFAULT_COMMAND_PREFIX,
    DEFAULT_I18N_LANGUAGE,
    DEFAULT_INTERACTION_CHECKPOINT_TTL_SECS,
    DEFAULT_LOG_BACKUP_COUNT,
    DEFAULT_LOG_DIR,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_MAX_SIZE_MB,
    DEFAULT_LOG_MEMORY_LIMIT,
    DEFAULT_LOG_ROTATION,
    DEFAULT_LOG_ROTATION_WHEN,
    DEFAULT_LOG_TOTAL_MEMORY_LIMIT,
    DEFAULT_MESSAGE_IGNORE_SELF,
    DEFAULT_SERVER_AUTO_START,
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    DEFAULT_STORAGE_BACKEND,
    DEFAULT_STORAGE_MYSQL_CHARSET,
    DEFAULT_STORAGE_MYSQL_DATABASE,
    DEFAULT_STORAGE_MYSQL_HOST,
    DEFAULT_STORAGE_MYSQL_PASSWORD,
    DEFAULT_STORAGE_MYSQL_POOL_MAX,
    DEFAULT_STORAGE_MYSQL_POOL_MIN,
    DEFAULT_STORAGE_MYSQL_PORT,
    DEFAULT_STORAGE_MYSQL_USER,
    DEFAULT_STORAGE_PG_DATABASE,
    DEFAULT_STORAGE_PG_HOST,
    DEFAULT_STORAGE_PG_PASSWORD,
    DEFAULT_STORAGE_PG_POOL_MAX,
    DEFAULT_STORAGE_PG_POOL_MIN,
    DEFAULT_STORAGE_PG_PORT,
    DEFAULT_STORAGE_PG_USER,
    DEFAULT_TRANSCRIPT_ENABLED,
    DEFAULT_TRANSCRIPT_MAX_PER_SESSION,
    DEFAULT_TRANSCRIPT_SELF_ECHO,
    DEFAULT_TRANSCRIPT_TTL_HOURS,
    DEFAULT_USE_GLOBAL_DB,
    DEFAULT_WAIT_REPLY_BLOCK,
    DEFAULT_WAIT_REPLY_CMDPASS,
    SQLITE_BUSY_TIMEOUT_MS,
)

# 默认配置（framework 节唯一真相源：FrameworkConfig 声明折叠——
# 经 _framework_defaults 惰性折叠补填，避免 frame_config 顶层导入
# 触发 Bases 包全量装配；其余节为手写字面量，随 B1-3 逐节迁移）
DEFAULT_ERISPULSE_CONFIG = {
    "server": {
        "host": DEFAULT_SERVER_HOST,
        "port": DEFAULT_SERVER_PORT,
        "auto_start": DEFAULT_SERVER_AUTO_START,
        "ssl_certfile": None,
        "ssl_keyfile": None,
        # 内联 PEM 内容（优先于路径，适合容器/无文件系统场景）
        "ssl_cert": None,
        "ssl_key": None,
        # /metrics Prometheus 文本端点开关（默认关闭；环境变量
        # ERISPULSE_SERVER_METRICS_ENABLED 覆盖）
        "metrics_enabled": False,
    },
    "router": {
        # 限流键是否信任反向代理头（X-Forwarded-For 首地址）。
        # 仅在可信反向代理之后启用，直连暴露时启用可被伪造绕过限流
        "rate_limit_trust_proxy": False,
    },
    "logger": {
        "level": DEFAULT_LOG_LEVEL,
        "format": "rich",
        "log_files": [],
        # 日志目录模式（与 log_files 互斥，log_files 显式路径优先）：
        # 设置后日志自动写入该目录并支持自动分段
        "log_dir": DEFAULT_LOG_DIR,
        "log_rotation": DEFAULT_LOG_ROTATION,          # 分段方式: "size" | "date" | "none"
        "log_max_size_mb": DEFAULT_LOG_MAX_SIZE_MB,    # size 模式单文件上限（MB）
        "log_backup_count": DEFAULT_LOG_BACKUP_COUNT,  # 保留的历史日志文件数
        "log_rotation_when": DEFAULT_LOG_ROTATION_WHEN,  # date 模式轮转周期
        # 单模块内存日志条数上限；0 = 关闭内存日志副本（省内存，get_logs 恒为空）
        "memory_limit": DEFAULT_LOG_MEMORY_LIMIT,
        # 全部模块内存日志的总条数上限（超限轮转淘汰最旧记录）；0 = 不限
        "total_memory_limit": DEFAULT_LOG_TOTAL_MEMORY_LIMIT,
        # 屏蔽指定日志等级（如 ["EVENT"] 隐藏消息收发内容，用于隐私保护）
        "exclude_levels": [],
    },
    "storage": {
        # 存储后端："sqlite"（默认，零配置）/ "mysql" / "postgres"（需安装可选驱动）
        "backend": DEFAULT_STORAGE_BACKEND,
        "use_global_db": DEFAULT_USE_GLOBAL_DB,
        # SQLite 后端写锁等待上限（毫秒，PRAGMA busy_timeout）；
        # 应用于每连接 PRAGMA，已打开连接不随配置刷新（改动需重启生效）
        "sqlite": {
            "busy_timeout": SQLITE_BUSY_TIMEOUT_MS,
        },
        # MySQL 后端连接参数（backend = "mysql" 时生效），需 pip install ErisPulse[mysql]
        "mysql": {
            "host": DEFAULT_STORAGE_MYSQL_HOST,
            "port": DEFAULT_STORAGE_MYSQL_PORT,
            "user": DEFAULT_STORAGE_MYSQL_USER,
            "password": DEFAULT_STORAGE_MYSQL_PASSWORD,
            "database": DEFAULT_STORAGE_MYSQL_DATABASE,
            "charset": DEFAULT_STORAGE_MYSQL_CHARSET,
            "pool_min": DEFAULT_STORAGE_MYSQL_POOL_MIN,
            "pool_max": DEFAULT_STORAGE_MYSQL_POOL_MAX,
        },
        # PostgreSQL 后端连接参数（backend = "postgres" 时生效），需 pip install ErisPulse[postgres]
        "postgres": {
            "host": DEFAULT_STORAGE_PG_HOST,
            "port": DEFAULT_STORAGE_PG_PORT,
            "user": DEFAULT_STORAGE_PG_USER,
            "password": DEFAULT_STORAGE_PG_PASSWORD,
            "database": DEFAULT_STORAGE_PG_DATABASE,
            "pool_min": DEFAULT_STORAGE_PG_POOL_MIN,
            "pool_max": DEFAULT_STORAGE_PG_POOL_MAX,
        },
    },
    "modules": {},
    "adapters": {},
    "event": {
        # 统一事件覆写系统：按事件类型覆写处理器的触发条件与实现参数
        # （OneBot12 标准类型 meta / message / notice / request + ErisPulse 扩展类型 command）
        # 各类型可覆写参数：
        #   message: {pattern, regex}                    文本触发条件
        #   notice / request: {detail_types, pattern, regex}
        #   meta: {detail_types}
        #   command: {master, hidden, aliases, prefix, help, usage}（模块级标量 + 命令级子表）
        #   acl: {allow, deny}（命令用户黑白名单，command 专属，命令名支持 glob）
        "overrides": {
            "message": {},
            "notice": {},
            "request": {},
            "meta": {},
            "command": {},
            "acl": {},
            # ACL 兜底（false = 严格模式：无 ACL 即拒）
            "acl_default_allow": True,
        },
        "message": {
            "ignore_self": DEFAULT_MESSAGE_IGNORE_SELF,
        },
        "command": {
            # prefix 可以是字符串（单个前缀）或列表（多个前缀）
            "prefix": DEFAULT_COMMAND_PREFIX,
            "case_sensitive": DEFAULT_COMMAND_CASE_SENSITIVE,
            "allow_space_prefix": DEFAULT_COMMAND_ALLOW_SPACE_PREFIX,
            "must_at_bot": DEFAULT_COMMAND_MUST_AT_BOT,
            # 命令命中后是否阻断向低优先级处理器传播（认领不受影响）
            "block": DEFAULT_COMMAND_BLOCK,
        },
        "wait_reply": {
            # wait_reply 命中回复后是否阻断向低优先级处理器传播（认领不受影响）
            "block": DEFAULT_WAIT_REPLY_BLOCK,
            # 等待期间是否跳过命令匹配（False=命中已注册命令的消息放行给命令分发器执行）
            "cmdpass": DEFAULT_WAIT_REPLY_CMDPASS,
        },
    },
    # 框架主人系统配置
    # users 为 dict 时按平台指定: {"yunhu": ["123"], "telegram": ["456"]}
    # users 为 list 时为全局主人（所有平台生效）: ["123", "456"]
    "master": {
        "users": {},
    },
    "framework": {},
    "i18n": {
        "language": DEFAULT_I18N_LANGUAGE,
    },
    # 作用域系统（scope）：声明"什么范围内生效"——模块 / 身份 / 出站三维。
    # ① 模块维度（某个上下文里哪些模块可用，优先级 会话 > Bot > 平台）
    #    platforms.<platform> = {modules: [...], blocked: [...], merge: bool?}
    #    （modules/blocked 条目支持 glob / re: 正则；子级 merge = true 时与低优先级绑定并集，默认整体覆盖）
    #    bots.<platform>.<bot_id> / sessions.<platform>.<session_id> 同上
    # ② 身份维度（谁的事件收不收，优先级 用户 > 会话 > Bot > 适配器）
    #    identity.adapters.<platform> = {allow/deny: true}
    #    identity.bots.<platform>.<bot_id> / identity.sessions / identity.users 同上
    #    identity.users 的 key 支持 glob / re: 正则
    # ③ 出站维度（限制模块发起出站调用，默认全允许，显式收紧才禁）
    #    actions.<module>.<action> = {allow: [...], deny: true|[...]}
    #    （action 取 send / api / request；条目支持精确名 / glob / re: 正则）
    # default_allow = false 时模块/身份"隐式拒绝"（未命中即拒；不影响出站维度）。
    "scope": {
        "default_allow": True,
        "cache_size": 1024,
        "platforms": {},
        "bots": {},
        "sessions": {},
        "identity": {
            "adapters": {},
            "bots": {},
            "sessions": {},
            "users": {},
        },
        "actions": {},
    },
    # 交互会话（interaction）：wait_reply 等待表 / 会话租约 / 对话检查点的统一配置。
    # checkpoint_ttl: Conversation 自动检查点的过期秒数，重启恢复时超期的存档被丢弃。
    "interaction": {
        "checkpoint_ttl": DEFAULT_INTERACTION_CHECKPOINT_TTL_SECS,
    },
    # 会话收件箱（transcript）：每会话近期消息流的自动记录与查询。
    # enabled: 是否启用自动记录；max_per_session: 每会话保留条数上限；
    # ttl_hours: 全局过期时间（小时），过期记录惰性清理；
    # self_echo: 入站 bot 回声（self.user_id == user_id，如 OneBot
    #   report-self-message）处理——"bot"=记 role="bot"+meta.self_echo，
    #   "skip"=不记录，"user"=记 role="user"（旧行为）。
    "transcript": {
        "enabled": DEFAULT_TRANSCRIPT_ENABLED,
        "max_per_session": DEFAULT_TRANSCRIPT_MAX_PER_SESSION,
        "ttl_hours": DEFAULT_TRANSCRIPT_TTL_HOURS,
        "self_echo": DEFAULT_TRANSCRIPT_SELF_ECHO,
    },
}


def _get_config_service():
    from ..Core.config import config as global_config

    return global_config


_FRAMEWORK_DEFAULTS_CACHE: dict[str, Any] | None = None


def _framework_defaults() -> dict[str, Any]:
    """
    framework 节默认值（FrameworkConfig 声明折叠，结果缓存）

    惰性调用：声明模块自带折叠、零 Core 依赖，可安全用于 Core 装配窗口
    内的快照构建（Logger 构造期即读 logger 配置触发本路径）。
    """
    global _FRAMEWORK_DEFAULTS_CACHE
    if _FRAMEWORK_DEFAULTS_CACHE is None:
        from .frame_config_schema import framework_defaults

        _FRAMEWORK_DEFAULTS_CACHE = framework_defaults()
    return _FRAMEWORK_DEFAULTS_CACHE


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    深度合并两个字典，override 中的值覆盖 base 中的对应值

    :param base: 基础字典
    :param override: 覆盖字典
    :return: 合并后的新字典
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _iter_leaf_diff(
    old: dict[str, Any], new: dict[str, Any], prefix: str = ""
) -> list[tuple[str, Any]]:
    """
    递归比较两棵配置字典，返回新增或值变化的叶子键（点分路径）

    仅收集 new 中相对 old 发生变化的叶子，用于把整棵配置的持久化
    拆分为细粒度叶子写入，避免整棵覆盖导致用户热更新丢失。

    {!--< internal-use >!--}
    语义：只增改、不处理删除（本模块的合并语义仅新增/覆盖叶子值）。
    {!--< /internal-use >!--}

    :param old: 变更前的配置字典
    :param new: 变更后的配置字典
    :param prefix: 递归时的路径前缀
    :return: [(点分路径, 叶子值), ...]
    """
    diffs: list[tuple[str, Any]] = []
    for key, value in new.items():
        path = f"{prefix}.{key}" if prefix else key
        old_value = old.get(key) if isinstance(old, dict) else None
        if isinstance(value, dict):
            if isinstance(old_value, dict):
                diffs.extend(_iter_leaf_diff(old_value, value, path))
            else:
                # 旧值不存在或非 dict：递归收集新子树的全部叶子
                diffs.extend(_iter_leaf_diff({}, value, path))
        elif old_value != value:
            diffs.append((path, value))
    return diffs


def _ensure_erispulse_config_structure(config_dict: dict[str, Any]) -> dict[str, Any]:
    """
    确保 ErisPulse 配置结构完整，补全缺失的配置项

    :param config_dict: 当前配置
    :return: 补全后的完整配置
    """

    # 深度合并配置（framework 节以声明折叠为基线：导入期 DEFAULT 占位空表，
    # 折叠延迟到本函数——本函数运行时 Core 已完成装配）
    defaults_effective = dict(DEFAULT_ERISPULSE_CONFIG)
    defaults_effective["framework"] = _framework_defaults()
    for section, default_values in defaults_effective.items():
        if section not in config_dict:
            config_dict[section] = copy.deepcopy(default_values)
            continue

        if not isinstance(config_dict[section], dict):
            config_dict[section] = copy.deepcopy(default_values)
            continue

        for key, default_value in default_values.items():
            if key not in config_dict[section]:
                config_dict[section][key] = (
                    copy.deepcopy(default_value)
                    if isinstance(default_value, dict)
                    else default_value
                )

    return config_dict


def get_erispulse_config() -> dict[str, Any]:
    """
    获取 ErisPulse 框架配置，自动补全缺失的配置项

    默认配置仅在内存中合并返回，不写入配置文件——config.toml 保持最小化，
    只包含用户显式设置的键；完整可配置项参考项目内的 config.full.example。
    用户显式设置（手动编辑 / update_erispulse_config / set_erispulse_section）
    的键不受影响，优先级始终高于内置默认值。

    :return: 完整的 ErisPulse 配置字典（快照副本，修改不影响后续调用）
    """
    template = _get_merged_snapshot()
    # 每次返回快照副本（调用方可能就地修改返回值）；模板缓存免去重复的
    # 结构补全遍历——deepcopy 本身不可省（返回值须与模板隔离）。
    # 环境变量覆盖在副本上每调用应用（保持"运行期改 env 即生效"的原语义）
    result = copy.deepcopy(template)
    _apply_env_overrides(result, CONFIG_ROOT_KEY)
    return result


# 合并快照模板缓存（合并默认值 + 环境覆盖后的完整配置树）；返回值 deepcopy
# 于此模板。配置写入路径（update_erispulse_config / set_erispulse_section /
# 外部 setConfig）经 _invalidate_merged_snapshot 失效
_merged_snapshot: dict[str, Any] | None = None
_merged_snapshot_lock = threading.Lock()
# 构建时 getConfig 结果的浅指纹（对象身份 + 顶层/二级键数）：lifecycle 事件
# 失效之外的兜底——直接操纵 config 单例内部 _cache 的写路径（含测试）不被
# 事件覆盖，指纹变化即重建
_merged_snapshot_fingerprint: tuple | None = None


def _config_fingerprint(current: Any) -> tuple:
    """{!--< internal-use >!--} 配置树浅指纹（对象身份 + 顶层/二级键规模）"""
    if not isinstance(current, dict):
        return (id(current), 0, 0)
    sub = sum(
        len(v) if isinstance(v, dict) else 0 for v in current.values()
    )
    return (id(current), len(current), sub)


def _get_merged_snapshot() -> dict[str, Any]:
    """{!--< internal-use >!--} 取合并快照模板（指纹变化 / 无缓存时重建并登记失效订阅）"""
    global _merged_snapshot, _merged_snapshot_fingerprint
    config_service = _get_config_service()
    current = config_service.getConfig(CONFIG_ROOT_KEY)
    fingerprint = _config_fingerprint(current)
    snapshot = _merged_snapshot
    if snapshot is not None and fingerprint == _merged_snapshot_fingerprint:
        return snapshot
    with _merged_snapshot_lock:
        if _merged_snapshot is None or fingerprint != _merged_snapshot_fingerprint:
            _merged_snapshot = _build_merged_snapshot()
            _merged_snapshot_fingerprint = _config_fingerprint(
                config_service.getConfig(CONFIG_ROOT_KEY)
            )
            _subscribe_merged_snapshot_invalidation()
        return _merged_snapshot


def _build_merged_snapshot() -> dict[str, Any]:
    """{!--< internal-use >!--} 构建合并快照模板（默认值合并；env 覆盖在返回副本时应用）"""
    config_service = _get_config_service()

    # 获取现有配置（deepcopy 避免合并默认值时污染缓存）
    current_config = config_service.getConfig(CONFIG_ROOT_KEY)
    # framework 节声明折叠补填（导入期占位空表；B1-3 前仅本节走声明源）
    defaults_snapshot = copy.deepcopy(DEFAULT_ERISPULSE_CONFIG)
    defaults_snapshot["framework"] = copy.deepcopy(_framework_defaults())

    if current_config is None:
        result = defaults_snapshot
    elif isinstance(current_config, dict):
        result = _ensure_erispulse_config_structure(copy.deepcopy(current_config))
    else:
        result = defaults_snapshot

    return result


def _invalidate_merged_snapshot() -> None:
    """{!--< internal-use >!--} 配置变更时失效合并快照模板（下次调用重建）"""
    global _merged_snapshot
    with _merged_snapshot_lock:
        _merged_snapshot = None


def _subscribe_merged_snapshot_invalidation() -> None:
    """{!--< internal-use >!--}
    订阅配置变更事件失效快照模板（外部经 config.setConfig 写入框架节时，
    update/set_erispulse 系列函数之外的写路径由此兜底失效）
    """
    try:
        from ..Core.lifecycle import lifecycle as _lifecycle

        _lifecycle.register("config.set", lambda _data: _invalidate_merged_snapshot())
        _lifecycle.register("config.updated", lambda _data: _invalidate_merged_snapshot())
    except Exception:
        pass


def get_event_config_value(section: str, key: str, default: Any) -> Any:
    """
    读取 ``ErisPulse.event.<section>.<key>`` 单值（高频热点路径专用，无快照开销）

    :func:`get_event_config` 每次调用 deepcopy 整棵配置树——每条回复命中
    事件调用两次即制造 MB 级暂态垃圾；仅读单值的调用点用本入口直取。
    环境变量覆盖不适用于本入口（低频行为参数不提供 env 覆盖）。

    :param section: 事件配置子节名（如 ``"wait_reply"``）
    :param key: 键名（如 ``"cmdpass"``）
    :param default: 键缺失时的默认值
    :return: 配置值
    """
    config_service = _get_config_service()
    section_config = config_service.getConfig(f"{CONFIG_ROOT_KEY}.event.{section}")
    if isinstance(section_config, dict) and key in section_config:
        return section_config[key]
    section_default = DEFAULT_ERISPULSE_CONFIG.get("event", {}).get(section, {})
    if isinstance(section_default, dict) and key in section_default:
        return section_default[key]
    return default


def get_framework_value(key: str, default: Any) -> Any:
    """
    读取 ``ErisPulse.framework.<key>`` 单值（高频热点路径专用，无快照开销）

    :func:`get_erispulse_config` 每次调用合并整棵配置树——事务/慢处理器
    告警等逐调用读取点走本入口直取。声明默认值经 :func:`_framework_defaults`
    兜底，Core/constants 同名常量保留为直接引用方的兼容默认。

    :param key: framework 节键名（如 ``"txn_begin_timeout"``）
    :param default: 键缺失时的兜底值
    :return: 配置值
    """
    config_service = _get_config_service()
    section_config = config_service.getConfig(f"{CONFIG_ROOT_KEY}.framework")
    if isinstance(section_config, dict):
        node: Any = section_config
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                node = None
                break
            node = node[part]
        if node is not None:
            return node
    node = _framework_defaults()
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def _apply_env_overrides(config: dict[str, Any], root: str = CONFIG_ROOT_KEY) -> None:
    """
    {!--< internal-use >!--}
    递归对配置字典应用环境变量覆盖

    命名规则：``ErisPulse.server.port`` → ``ERISPULSE_SERVER_PORT``
    （将点路径大写、``.`` 替换为 ``_``）。仅覆盖叶子值，按原值类型做 coerce。
    """
    _apply_env_to_subtree(config, root)


def _apply_env_to_subtree(d: dict[str, Any], path: str) -> None:
    for key, val in list(d.items()):
        full_path = f"{path}.{key}"
        if isinstance(val, dict):
            _apply_env_to_subtree(val, full_path)
        else:
            env_name = full_path.upper().replace(".", "_")
            env_val = os.environ.get(env_name)
            if env_val is not None:
                d[key] = _coerce_env_value(val, env_val)


def _coerce_env_value(original: Any, env_str: str) -> Any:
    """按原值类型把环境变量字符串转换为对应 Python 类型"""
    s = env_str.strip()
    if isinstance(original, bool):
        return s.lower() in ("1", "true", "yes", "on")
    if isinstance(original, int) and not isinstance(original, bool):
        try:
            return int(s)
        except ValueError:
            return env_str
    if isinstance(original, float):
        try:
            return float(s)
        except ValueError:
            return env_str
    if isinstance(original, list):
        return [x.strip() for x in s.split(",")] if s else []
    return env_str


def get_config(section: str | None = None) -> dict[str, Any] | Any:
    """
    获取 ErisPulse 配置

    :param section: 配置部分名称（如 "server"、"logger" 等），None 表示获取完整配置
    :return: 配置字典或配置项
    """
    erispulse_config = get_erispulse_config()

    if section is None:
        return erispulse_config
    return erispulse_config.get(section, {})


def update_erispulse_config(new_config: dict[str, Any]) -> bool:
    """
    更新 ErisPulse 配置，自动补全缺失的配置项

    :param new_config: 新的配置字典
    :return: 是否更新成功
    """
    config_service = _get_config_service()

    # 基线使用缓存中的原始配置（不含环境变量覆盖），避免把环境覆盖持久化到文件
    current_raw = config_service.getConfig(CONFIG_ROOT_KEY)
    if not isinstance(current_raw, dict):
        current_raw = {}
    baseline = _ensure_erispulse_config_structure(copy.deepcopy(current_raw))

    # 获取当前配置并深合并新配置
    merged = _deep_merge(baseline, new_config)

    # 确保合并后的配置结构完整
    complete_config = _ensure_erispulse_config_structure(merged)

    # 仅按叶子键写入变化，避免整棵覆盖冲掉用户对其它子键的热更新
    for path, value in _iter_leaf_diff(baseline, complete_config):
        config_service.setConfig(f"{CONFIG_ROOT_KEY}.{path}", value)
    _invalidate_merged_snapshot()
    return True


def set_erispulse_section(path: str, value: Any) -> bool:
    """
    整节替换写入 ErisPulse 配置

    与 :func:`update_erispulse_config` 的深合并语义不同，本函数对目标子路径
    **整节替换**（支持删除子键，如移除绑定、黑名单移除等场景）。
    写入失败时抛出异常。

    :param path: 相对 ``ErisPulse`` 根的配置路径，如 ``"event.overrides.acl"``、``"scope"``
    :param value: 新的配置节内容（通常为 dict）
    :return: 是否写入成功

    :example:
    >>> set_erispulse_section("event.overrides.acl", {"roll*": {"allow": ["onebot11:123456"]}})
    """
    config_service = _get_config_service()
    result = config_service.setConfig(f"{CONFIG_ROOT_KEY}.{path}", value)
    _invalidate_merged_snapshot()
    return result


def get_server_config() -> dict[str, Any]:
    """
    获取服务器配置，确保结构完整

    :return: 服务器配置字典
    """
    return get_config("server")


def get_logger_config() -> dict[str, Any]:
    """
    获取日志配置，确保结构完整

    :return: 日志配置字典
    """
    return get_config("logger")


def get_storage_config() -> dict[str, Any]:
    """
    获取存储模块配置

    :return: 存储配置字典
    """
    return get_config("storage")


def get_event_config() -> dict[str, Any]:
    """
    获取事件系统配置

    :return: 事件系统配置字典
    """
    return get_config("event")


def get_framework_config() -> dict[str, Any]:
    """
    获取框架配置

    :return: 框架配置字典
    """
    return get_config("framework")


def get_i18n_config() -> dict[str, Any]:
    """
    获取国际化配置

    :return: 国际化配置字典
    """
    return get_config("i18n")


def get_master_config() -> dict[str, Any]:
    """
    获取框架主人系统配置

    :return: 框架主人配置字典
    """
    return get_config("master")


__all__ = [
    "DEFAULT_ERISPULSE_CONFIG",
    "get_config",
    "get_erispulse_config",
    "get_event_config",
    "get_event_config_value",
    "get_framework_config",
    "get_framework_value",
    "get_i18n_config",
    "get_logger_config",
    "get_master_config",
    "get_server_config",
    "get_storage_config",
    "set_erispulse_section",
    "update_erispulse_config",
]
