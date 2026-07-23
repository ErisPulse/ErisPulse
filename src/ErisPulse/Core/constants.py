"""
ErisPulse 内部常量定义

集中管理框架中使用的硬编码常量，便于统一维护和修改。

{!--< tips >!--}
1. 修改常量前请仔细阅读注释，确认影响范围
2. 带"运行时行为"标注的常量修改后会直接影响运行时逻辑
3. 带"仅显示"标注的常量修改后仅影响显示/日志输出
4. 带"配置默认值"标注的常量只在首次写入配置时生效，已有配置不会被覆盖
{!--< /tips >!--}
"""

from typing import Final

# ==============================================================================
# 适配器重试策略
#
# 控制适配器启动失败后的重连行为。
# 使用位置: Core/adapter.py -> _run_adapter()
# ==============================================================================

# 逐次递增的重试等待时间（秒）。
# 列表索引对应重试次数（第1次等60秒，第2次等600秒...）。
# 超出列表长度后使用 ADAPTER_RETRY_FIXED_DELAY_SECS。
# 修改影响: 适配器启动失败后的重连速度。设为空列表则每次使用 fixed_delay。
ADAPTER_RETRY_BACKOFF_INTERVALS: Final[list] = [60, 10 * 60, 30 * 60, 60 * 60]

# 超出退避列表后的固定重试间隔（秒），默认 3 小时。
# 修改影响: 长时间连接失败时的重连频率。
ADAPTER_RETRY_FIXED_DELAY_SECS: Final[int] = 3 * 60 * 60

# ==============================================================================
# 路由服务器默认值
#
# 控制内置 HTTP/WebSocket 服务器的监听地址和行为。
# 使用位置: Core/router.py -> start(), stop(), _format_url_for_display()
# ==============================================================================

# 路由服务器默认监听地址。
# 修改影响: 服务器可访问范围。"0.0.0.0" 表示所有网卡，"127.0.0.1" 仅本机。
DEFAULT_SERVER_HOST: Final[str] = "0.0.0.0"

# 路由服务器默认监听端口。
# 修改影响: 客户端（如 SandboxAdapter WebUI）需要对应修改连接端口。
DEFAULT_SERVER_PORT: Final[int] = 8000

# 路由服务器关闭时的超时时间（秒）。
# 修改影响: Ctrl+C 后等待 uvicorn 关闭的耐心时间。超时后强制终止。
SERVER_SHUTDOWN_TIMEOUT_SECS: Final[float] = 5.0

# ==============================================================================
# 配置键模板
#
# TOML 配置文件中的键路径模板。用 .format() 拼接平台名/模块名。
# 使用位置: Core/adapter.py -> _config_register(), is_enabled(), enable(), disable(), list_items()
#            Core/module.py  -> _config_register(), is_enabled(), enable(), disable(), list_items()
# ==============================================================================

# 配置文件根键名。
# 修改影响: 整个 ErisPulse 配置树的顶层命名空间。已有配置文件不会自动迁移。
CONFIG_ROOT_KEY: Final[str] = "ErisPulse"

# 适配器启用状态的配置键前缀。
# 例如: ErisPulse.adapters.status.kook = true
# 修改影响: 适配器启用/禁用状态的读写路径。已有配置不会自动迁移。
CONFIG_KEY_ADAPTER_STATUS: Final[str] = "ErisPulse.adapters.status"
CONFIG_KEY_ADAPTER_STATUS_OF: Final[str] = "ErisPulse.adapters.status.{}"  # .format(platform)

# 模块启用状态的配置键前缀。
# 例如: ErisPulse.modules.status.Dashboard = true
# 修改影响: 模块启用/禁用状态的读写路径。
CONFIG_KEY_MODULES_STATUS: Final[str] = "ErisPulse.modules.status"
CONFIG_KEY_MODULE_STATUS_OF: Final[str] = "ErisPulse.modules.status.{}"  # .format(module_name)

# 路由 CORS 配置键。
# 修改影响: CORS 中间件配置的读取路径。
CONFIG_KEY_ROUTER_CORS: Final[str] = "ErisPulse.router.cors"

# 路由安全头配置键。
# 修改影响: 安全响应头配置的读取路径。
CONFIG_KEY_ROUTER_SECURITY: Final[str] = "ErisPulse.router.security"

# ==============================================================================
# 配置管理器
#
# 控制配置文件的读写行为和缓存策略。
# 使用位置: Core/config.py -> ConfigManager.__init__()
# ==============================================================================

# 默认配置文件路径（相对于工作目录）。
# 修改影响: 配置文件的读写位置。仅在 ConfigManager 未指定路径时生效。
DEFAULT_CONFIG_FILE_PATH: Final[str] = "config/config.toml"

# 配置缓存过期时间（秒）。
# 修改影响: 内存中缓存的配置值多久后重新从文件读取。设大减少磁盘IO，设小实时性更高。
CONFIG_CACHE_TIMEOUT_SECS: Final[int] = 60

# 配置延迟写入间隔（秒）。
# 修改影响: setConfig() 后多久才真正写入磁盘。设大减少磁盘写入频率，设小数据安全性更高。
CONFIG_WRITE_DELAY_SECS: Final[int] = 5

# ==============================================================================
# 日志系统
#
# 控制日志的输出格式、存储限制和级别。
# 使用位置: Core/logger.py -> Logger.__init__()
# ==============================================================================

# Python logging 模块的 logger 名称。
# 修改影响: 日志过滤时的 logger 名。第三方日志处理器需对应修改。
LOGGER_NAME: Final[str] = "ErisPulse"

# 内存中保留的最大日志条数。
# 修改影响: WebUI 日志查看器的历史深度。设大占用更多内存，设小丢失更多历史。
DEFAULT_LOG_MEMORY_LIMIT: Final[int] = 1000

# 日志初始级别（启动时默认值）。
# 运行时会被配置文件中的 ErisPulse.logger.level 覆盖。
# 修改影响: 仅影响未配置日志级别时的默认行为。
DEFAULT_LOG_LEVEL: Final[str] = "INFO"

# Rich 控制台日志的时间戳格式（strftime 语法）。
# 修改影响: 终端日志输出的时间显示样式。
LOG_TIME_FORMAT: Final[str] = "[%H:%M:%S]"

# Rich 日志配色主题。
# 键为 Rich 样式名（Theme key），值为 rich 样式字符串。
# 修改影响: 终端中各级别日志的显示颜色。
# 设计原则: 参考 Rust env_logger 风格，每种级别使用独立语义色。
LOG_RICH_THEME: Final[dict] = {
    "log.time": "dim",  # 时间戳
    "logging.level.trace": "dim",  # TRACE（最低可见度）
    "logging.level.debug": "white",  # DEBUG
    "logging.level.event": "cyan",  # EVENT
    "logging.level.info": "green",  # INFO
    "logging.level.warning": "yellow",  # WARNING
    "logging.level.error": "red",  # ERROR
    "logging.level.critical": "black on red",  # CRITICAL（红底黑字）
}

# ==============================================================================
# SQLite 存储引擎
#
# 控制 SQLite 数据库的性能和行为。
# 使用位置: Core/storage.py -> SQLiteKVStore._connect(), _init_db()
# ==============================================================================

# WAL (Write-Ahead Logging) 模式，允许读写并发。
# 修改影响: 设为 DELETE 模式可提升单线程写入性能，但会阻塞读操作。
SQLITE_JOURNAL_MODE: Final[str] = "PRAGMA journal_mode=WAL"

# 同步模式。NORMAL 在 WAL 模式下安全且更快。
# 修改影响: 设为 FULL 更安全（断电不丢数据），但写入更慢。
SQLITE_SYNCHRONOUS_MODE: Final[str] = "PRAGMA synchronous=NORMAL"

# KV 存储的默认表名。
# 修改影响: 数据库中的表名。已有数据库不会自动重命名。
DEFAULT_KV_TABLE_NAME: Final[str] = "config"

# 是否默认使用全局数据库（框架安装目录下的 data/config.db）。
# 配置默认值。True = 全局共享，False = 项目级（当前工作目录下 config/config.db）。
# 修改影响: 数据存储位置。
DEFAULT_USE_GLOBAL_DB: Final[bool] = False

# ==============================================================================
# 路由限流
#
# 控制路由限流（rate-limit）的默认参数。
# 使用位置: Core/router.py -> _parse_rate_limit()
# ==============================================================================

# 默认限流时间窗口（秒）。
# 修改影响: 限流计数器的统计周期。
DEFAULT_RATE_LIMIT_WINDOW_SECS: Final[int] = 60

# 默认限流窗口内最大请求数。
# 修改影响: 触发 429 响应的阈值。
DEFAULT_RATE_LIMIT_MAX_REQUESTS: Final[int] = 10

# 未指定 HTTP 方法时的默认值。
# 使用位置: Core/router.py -> register_http()
# 修改影响: 路由注册时的默认 HTTP 方法。
DEFAULT_HTTP_METHODS: Final[list] = ["POST"]

# WebSocket 路由是否默认自动接受连接。
# 使用位置: Core/router.py -> register_ws()
# 修改影响: 设为 False 则需在 handler 中手动 accept。
DEFAULT_WS_AUTO_ACCEPT: Final[bool] = True

# ==============================================================================
# CORS 中间件
#
# 控制跨域资源共享的默认策略。
# 使用位置: Core/router.py -> setup_cors(), _apply_config()
# ==============================================================================

# 默认允许的来源、方法、头。
# 修改影响: 未显式配置 CORS 时的跨域访问策略。["*"] 表示允许所有。
DEFAULT_CORS_ORIGINS: Final[list] = ["*"]
DEFAULT_CORS_METHODS: Final[list] = ["*"]
DEFAULT_CORS_HEADERS: Final[list] = ["*"]

# CORS 预检请求的缓存时间（秒）。
# 修改影响: 浏览器缓存 OPTIONS 响应的时长。设大减少预检请求，设小 CORS 变更更快生效。
DEFAULT_CORS_MAX_AGE_SECS: Final[int] = 600

# ==============================================================================
# 安全响应头
#
# 控制 HTTP 响应的默认安全头。
# 使用位置: Core/router.py -> setup_security_headers()
# ==============================================================================

# 默认安全头字典。
# 修改影响: 所有 HTTP 响应携带的安全头。可被 setup_security_headers(headers=...) 合并覆盖。
DEFAULT_SECURITY_HEADERS: Final[dict] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
}

# ==============================================================================
# WebSocket 关闭码
#
# RFC 6455 标准关闭码，用于 WebSocket 异常断开。
# 使用位置: Core/router.py -> websocket_endpoint(), _global_ws_handler()
# ==============================================================================

# 1008: 策略违规（如认证失败、路径非法）。
# 修改影响: 客户端收到此关闭码时的错误处理逻辑。
WS_CLOSE_POLICY_VIOLATION: Final[int] = 1008

# 1011: 服务器内部错误。
# 修改影响: 客户端收到此关闭码时的重连策略。
WS_CLOSE_INTERNAL_ERROR: Final[int] = 1011

# ==============================================================================
# 网络地址常量
#
# 用于 URL 显示格式化和本地 IP 发现。
# 使用位置: Core/router.py -> _format_url_for_display(), _discover_local_ips()
# ==============================================================================

# 通配符地址（监听所有网卡）。
WILDCARD_IPV4: Final[str] = "0.0.0.0"
WILDCARD_IPV6: Final[str] = "[::]"

# 当无法发现本地 IP 时的回退地址。
# 修改影响: 控制台显示的局域网访问地址。
FALLBACK_IPV4: Final[str] = "127.0.0.1"
FALLBACK_IPV6_HOST: Final[str] = "localhost"

# ==============================================================================
# 生命周期管理
#
# 控制框架初始化/反初始化的计时和事件来源标识。
# 使用位置: sdk.py -> init(), uninit()
#            Core/lifecycle.py -> submit_event()
# ==============================================================================

# 事件默认来源标识符。
# 修改影响: lifecycle.submit_event() 的 source 默认值。影响事件溯源。
DEFAULT_EVENT_SOURCE: Final[str] = "ErisPulse"

# 反初始化时等待事件处理完成的缓冲时间（秒）。
# 修改影响: 设大确保异步事件处理完成，设小加速关闭流程。过小可能丢失事件。
UNINIT_SETTLE_DELAY_SECS: Final[float] = 0.1

# 优雅关闭总超时时间（秒），超过此时间未完成则强制终止。
# 用于防止模块 on_unload() 卡死阻塞 Docker/容器重启。
# 0 表示不设超时（无限等待）。
# 修改影响: 设小可能导致模块 on_unload 被强制中断。设大可能导致容器关闭超时。
DEFAULT_UNINIT_TIMEOUT_SECS: Final[int] = 30

# 生命周期计时器名称（用于性能分析）。
# 修改影响: 生命周期事件中的计时器标识。仅影响日志和 WebUI 显示。
LIFECYCLE_TIMER_CORE_INIT: Final[str] = "core.init"
LIFECYCLE_TIMER_CORE_UNINIT: Final[str] = "core.uninit"

# ==============================================================================
# 命令系统默认值
#
# 控制命令解析和匹配的行为。
# 使用位置: Core/Event/command.py -> CommandHandler.__init__()
#            runtime/frame_config.py -> DEFAULT_ERISPULSE_CONFIG
# ==============================================================================

# 命令前缀字符。
# 配置默认值，可被 ErisPulse.event.command.prefix 覆盖。
# 修改影响: 用户触发命令的前缀。例如 "/" -> /help, "!" -> !help。
DEFAULT_COMMAND_PREFIX: Final[str] = "/"

# 命令是否区分大小写。
# 配置默认值，可被 ErisPulse.event.command.case_sensitive 覆盖。
# 修改影响: True 时 /Help 和 /help 是不同命令，False 时不区分。
DEFAULT_COMMAND_CASE_SENSITIVE: Final[bool] = True

# 是否允许前缀和命令名之间有空格。
# 配置默认值。True 时 "/ help" 等同于 "/help"。
DEFAULT_COMMAND_ALLOW_SPACE_PREFIX: Final[bool] = False

# 群聊中是否必须 @机器人 才触发命令。
# 配置默认值。True 时群消息中 /help 需要 @Bot /help 才生效，私聊不受影响。
DEFAULT_COMMAND_MUST_AT_BOT: Final[bool] = False

# 是否忽略自身发送的消息。
# 配置默认值。设为 False 会导致命令系统处理自己发出的消息（通常不期望）。
DEFAULT_MESSAGE_IGNORE_SELF: Final[bool] = True

# ==============================================================================
# 事件处理器默认值
#
# 控制事件处理器注册和等待回复的默认参数。
# 使用位置: Core/Event/base.py -> BaseEventHandler.register(), __call__()
#            Core/Event/command.py -> wait_reply()
#            Core/Event/wrapper.py -> Event 多个等待方法
# ==============================================================================

# 处理器默认优先级（数值越大越先执行）。
# 修改影响: 未指定 priority 的处理器的执行顺序。
DEFAULT_HANDLER_PRIORITY: Final[int] = 0

# 命令分发器优先级（远高于默认值，确保命令在消息处理器之前执行）。
# 修改影响: 命令 /xxx 总是优先于 on_message / on_group_message 等处理器触发。
DEFAULT_COMMAND_DISPATCHER_PRIORITY: Final[int] = 100

# 等待用户回复的默认超时时间（秒）。
# 使用位置: command.wait_reply(), Event.wait_reply(), Event.wait_for() 等 8 处。
# 修改影响: 所有等待用户交互的默认超时。设大用户有更多反应时间，设小释放资源更快。
DEFAULT_WAIT_TIMEOUT_SECS: Final[float] = 60.0

# 等待回复时的默认最大重试次数。
# 使用位置: Core/Event/wrapper.py -> Conversation 字段重试。
# 修改影响: 验证器拒绝回复后的重试次数。
DEFAULT_MAX_RETRIES: Final[int] = 3

# 事件处理器执行耗时警告阈值（秒）。
# 使用位置: Core/adapter.py -> emit() 中的 handler 执行监控。
# 修改影响: 当单个处理器执行超过此时间时记录 WARNING 日志。
HANDLER_SLOW_THRESHOLD_SECS: Final[float] = 1.0

# 平台标识的回退值。
# 当事件数据缺少 platform 字段时使用。
# 修改影响: 日志和事件处理中的平台标识显示。
UNKNOWN_PLATFORM: Final[str] = "unknown"

# ==============================================================================
# OneBot12 事件类型
#
# OB12 标准事件的 type 字段值。
# 使用位置: Core/Event/base.py, message.py, notice.py, request.py, meta.py
#            Core/Event/wrapper.py -> Event.is_message() 等类型判断方法
# ==============================================================================

# 消息事件（私聊、群聊等用户消息）。
EVENT_TYPE_MESSAGE: Final[str] = "message"

# 通知事件（好友变动、群成员变动等系统通知）。
EVENT_TYPE_NOTICE: Final[str] = "notice"

# 请求事件（好友请求、群邀请等需要确认的事件）。
EVENT_TYPE_REQUEST: Final[str] = "request"

# 元事件（连接、断开、心跳等适配器生命周期事件）。
EVENT_TYPE_META: Final[str] = "meta"

# ==============================================================================
# OneBot12 事件 detail_type
#
# OB12 标准事件的 detail_type 字段值。
# 用于事件处理器的条件过滤和类型判断。
# 使用位置: Core/Event/message.py  -> on_private_message(), on_group_message()
#            Core/Event/notice.py   -> on_friend_add(), on_group_increase() 等
#            Core/Event/request.py  -> on_friend_request(), on_group_request()
#            Core/Event/meta.py     -> on_connect(), on_disconnect(), on_heartbeat()
#            Core/Event/wrapper.py  -> Event.is_private(), is_group() 等方法
#            Core/Event/command.py  -> must_at_bot 检查
#            Core/Bases/adapter.py  -> Send.To() 私聊/群聊判断
# ==============================================================================

DETAIL_TYPE_PRIVATE: Final[str] = "private"  # 私聊消息
DETAIL_TYPE_USER: Final[str] = "user"  # 用户类型（用于 command.py 中与 "private" 同义检查）
DETAIL_TYPE_GROUP: Final[str] = "group"  # 群聊消息 / 群请求
DETAIL_TYPE_FRIEND: Final[str] = "friend"  # 好友请求
DETAIL_TYPE_FRIEND_INCREASE: Final[str] = "friend_increase"  # 好友添加通知
DETAIL_TYPE_FRIEND_DECREASE: Final[str] = "friend_decrease"  # 好友删除通知
DETAIL_TYPE_GROUP_MEMBER_INCREASE: Final[str] = "group_member_increase"  # 群成员增加通知
DETAIL_TYPE_GROUP_MEMBER_DECREASE: Final[str] = "group_member_decrease"  # 群成员减少通知
DETAIL_TYPE_CONNECT: Final[str] = "connect"  # 适配器连接上线（元事件）
DETAIL_TYPE_DISCONNECT: Final[str] = "disconnect"  # 适配器断开连接（元事件）
DETAIL_TYPE_HEARTBEAT: Final[str] = "heartbeat"  # 适配器心跳（元事件）

# ==============================================================================
# OneBot12 协议常量
#
# OB12 标准返回码和状态值。
# 使用位置: Core/Bases/adapter.py -> SendDSL._not_impl() 等错误响应
# ==============================================================================

# 方法未实现时的返回码。
RETCODE_NOT_IMPLEMENTED: Final[int] = 10002

# 失败状态标识。
STATUS_FAILED: Final[str] = "failed"

# 成功状态标识和返回码。
STATUS_OK: Final[str] = "ok"
RETCODE_OK: Final[int] = 0

# ==============================================================================
# 消息发送默认值
#
# 控制 SendDSL 的默认行为。
# 使用位置: Core/Bases/adapter.py -> SendDSL.ByMethod(), SendDSL._send()
#            Core/Event/wrapper.py -> Event._send_by_platform() 等
# ==============================================================================

# 默认发送方法名（OB12 消息段类型）。
# 修改影响: 未指定 method 时默认发送文本消息。
DEFAULT_SEND_METHOD: Final[str] = "Text"

# 文本类发送方法特征（大小写不敏感子串匹配）：方法名包含这些子串即为文本类，
# 选项文本可直接拼接到末尾。设计原则：只要不是明确的富媒体就合并。
# 使用位置: Core/Event/wrapper.py -> _is_text_method()
TEXT_METHOD_INDICATORS: Final[tuple[str, ...]] = ("text", "markdown", "md", "html", "h5")

# 默认发送目标类型（当无法从事件推断时的回退值）。
# 修改影响: Send.To() 未指定类型时的目标推断。
DEFAULT_SEND_TARGET_TYPE: Final[str] = "user"

# Conversation 存储键前缀（用于持久化会话上下文）。
# 修改影响: SQLite 中存储会话数据的键名格式。已有数据不会自动迁移。
CONVERSATION_KEY_PREFIX: Final[str] = "conversation"

# ==============================================================================
# 确认词汇集
#
# 用于 Event.confirm() 判断用户回复是"肯定"还是"否定"。
# 使用位置: Core/Event/wrapper.py -> _builtin_confirm()
# 修改影响: 用户用自然语言回复时的匹配结果。支持 zh/en/ja/ru 四种语言。
# ==============================================================================

CONFIRM_YES_WORDS: Final[frozenset] = frozenset(
    {
        # 中文
        "是", "确认", "确定", "好", "好的", "对", "嗯", "行", "同意",
        "没问题", "可以", "当然", "嗯嗯", "是的",
        # 英文
        "yes", "y", "ok", "okay", "true", "sure", "yeah", "yep",
        "confirm", "confirmed", "agree", "correct",
        # 日文
        "はい", "いいよ", "了解", "確定", "同意", "可能", "可能です",
        "もちろんです", "そう", "そうです",
        # 俄文
        "да", "конечно", "хорошо", "ок", "согласен", "верно",
        "подтвердить", "подтверждаю",
    }
)
CONFIRM_NO_WORDS: Final[frozenset] = frozenset(
    {
        # 中文
        "否", "取消", "不", "不要", "不行", "错", "不对", "别",
        "拒绝", "不可以", "算了", "不需要", "不是",
        # 英文
        "no", "n", "cancel", "false", "nope", "nah", "decline",
        "declined", "disagree", "incorrect", "wrong", "deny",
        # 日文
        "いいえ", "いや", "だめ", "無理", "却下", "不可",
        "キャンセル", "違う", "そうではない",
        # 俄文
        "нет", "отмена", "отказ", "невозможно", "нельзя",
        "не согласен", "неверно", "отклонить",
    }
)

# 各语言的代表性确认词，用于 confirm(hint=True) 时生成提示文本。
# 使用位置: Core/Event/wrapper.py -> _builtin_confirm()
CONFIRM_HINT_WORDS: Final[dict[str, tuple[str, str]]] = {
    "zh-CN": ("是", "否"),
    "zh-TW": ("是", "否"),
    "en": ("yes", "no"),
    "ja": ("はい", "いいえ"),
    "ru": ("да", "нет"),
}

# ==============================================================================
# 框架管理默认值
#
# 控制模块/适配器的注册和加载行为。
# 使用位置: Core/module.py  -> _config_register()
#            Core/adapter.py -> _config_register()
#            Core/Bases/module.py -> BaseModule.get_load_strategy()
# ==============================================================================

# 适配器注册时的默认启用状态。
# 配置默认值。True 表示新注册的适配器默认启用；改为 False 则需手动 enable()。
DEFAULT_ADAPTER_ENABLED: Final[bool] = True

# 模块注册时的默认启用状态。
# 配置默认值。True 表示新注册的模块默认启用；改为 False 则需手动 enable()。
DEFAULT_MODULE_ENABLED: Final[bool] = True

# 模块默认加载优先级（数值越大越先加载）。
# 使用位置: BaseModule.get_load_strategy() 返回值。
# 修改影响: 模块加载顺序。0 = 普通，正数 = 优先加载，负数 = 延后加载。
DEFAULT_MODULE_PRIORITY: Final[int] = 0

# 是否默认启用懒加载。
# 配置默认值，可被 ErisPulse.framework.enable_lazy_loading 覆盖。
# True 时模块在首次被访问时才加载，False 时框架启动时立即加载。
DEFAULT_LAZY_LOADING_ENABLED: Final[bool] = True

# 严格模式默认级别。
# 配置默认值，可被 ErisPulse.framework.strict_mode 覆盖。
# 0 = 宽松（违规仅警告，未继承基类的组件仍尝试加载）
# 1 = 严格-跳过（拒绝未继承基类的组件，继续启动其余）
# 2 = 严格-致命（收集所有违规后中止整个启动）
# 修改影响: 模块/适配器加载失败或不合规时的处理策略。
DEFAULT_STRICT_MODE: Final[int] = 0

# ==============================================================================
# 国际化 (i18n) 默认值
#
# 控制框架内置国际化模块的语言检测行为。
# 使用位置: Core/i18n/__init__.py -> _get_effective_language()
# ==============================================================================

# 默认语言代码。设为 "auto" 表示自动检测系统语言。
# 也可设为具体语言代码: "zh-CN", "zh-TW", "en", "ja", "ru"
# 配置默认值，可被 ErisPulse.i18n.language 覆盖。
# 修改影响: 框架所有内置文本的显示语言。
DEFAULT_I18N_LANGUAGE: Final[str] = "auto"

# ==============================================================================
# HTTP 客户端默认值
#
# 控制内置 HTTP 客户端的超时、重试和连接行为。
# 使用位置: Core/Bases/client.py -> HttpClient.__init__()
# ==============================================================================

# HTTP 客户端请求总超时（秒）。
# 修改影响: 超过此时间的请求将被中止。
DEFAULT_HTTP_CLIENT_TIMEOUT_SECS: Final[float] = 30.0

# HTTP 客户端连接超时（秒）。
# 修改影响: 建立 TCP 连接的最大等待时间。
DEFAULT_HTTP_CLIENT_CONNECT_TIMEOUT_SECS: Final[float] = 10.0

# HTTP 客户端默认最大重试次数。
# 修改影响: 请求失败后的自动重试次数。0 = 不重试。
DEFAULT_HTTP_CLIENT_MAX_RETRIES: Final[int] = 1

# HTTP 客户端重试间隔（秒）。
# 修改影响: 每次重试之间的等待时间。
DEFAULT_HTTP_CLIENT_RETRY_DELAY_SECS: Final[float] = 1.0

# HTTP 客户端默认 User-Agent。
# 修改影响: 所有出站 HTTP 请求的默认 User-Agent 头。
DEFAULT_HTTP_CLIENT_USER_AGENT: Final[str] = ""

# ==============================================================================
# WebSocket 客户端默认值
#
# 控制内置 WebSocket 客户端的心跳和连接行为。
# 使用位置: Core/client.py -> HttpClient.ws_connect()
# ==============================================================================

# WebSocket 客户端默认心跳间隔（秒）。
# 修改影响: 发送心跳 ping 的频率。None 表示不发送心跳。
DEFAULT_WS_CLIENT_HEARTBEAT_SECS: Final[float | None] = None

# WebSocket 客户端默认连接超时（秒）。
# 修改影响: 建立 WS 连接的最大等待时间。
DEFAULT_WS_CLIENT_CONNECT_TIMEOUT_SECS: Final[float] = 10.0

# ==============================================================================
# 存储嵌套键安全限制
#
# 控制点分隔嵌套键路径中数字段作为列表索引处理时的安全上限。
# 使用位置: Core/storage.py -> StorageManager._set_nested_value()
# ==============================================================================

# 嵌套键路径中允许作为列表索引的数字段最大值。
# 点分隔键路径的每一段本质上都是字典键；仅当容器本身已经是列表时，
# 才会按数组索引处理。超过此值的索引会被安全跳过，避免分配超大列表导致 OOM。
# 修改影响: 运行时行为。storage.set() 写入超大列表索引时的安全阈值。
STORAGE_MAX_LIST_INDEX: Final[int] = 10000

# ==============================================================================
# 性能优化与主动 GC
#
# 控制事件处理器并发上限、后台资源回收节奏和内存释放策略。
# 使用位置: Core/adapter.py -> emit(), shutdown()
#            Core/lifecycle.py -> register()
#            sdk.py -> _do_uninit()
# ==============================================================================

# 事件处理器最大并发 Task 数。
# 运行时行为。每个事件匹配的处理器在独立 Task 中执行，此值限制同时运行的 Task 数量。
# 修改影响: 设大提高并发吞吐但增加内存占用，设小限制资源消耗但可能降低事件处理速度。
DEFAULT_HANDLER_MAX_CONCURRENCY: Final[int] = 64

# 路由限流存储的自动清理间隔（秒）。
# 运行时行为。后台定期扫描 _rate_limit_store，清除过期的 IP 记录。
# 修改影响: 设大减少 CPU 开销但内存占用更久，设小更积极回收内存。
DEFAULT_RATE_LIMIT_CLEANUP_INTERVAL_SECS: Final[int] = 300

# 离线 Bot 信息的自动过期时间（秒）。
# 运行时行为。Bot 标记为 offline 后，经过此时间会被自动清除。
# 修改影响: 设大保留更多历史 Bot 信息，设小更快回收内存。0 表示不过期。
DEFAULT_OFFLINE_BOT_EXPIRY_SECS: Final[int] = 3600

# 主动 GC（垃圾回收）间隔（秒）。
# 运行时行为。SDK 初始化后启动定期 GC 后台任务，按此间隔触发 Python GC 和内部资源回收。
# 修改影响: 设大减少 CPU 中断但内存峰值更高，设小更频繁回收但增加开销。0 表示禁用。
DEFAULT_PROACTIVE_GC_INTERVAL_SECS: Final[int] = 300

# shutdown 时等待在途事件处理器完成的最长时间（秒）。
# 运行时行为。适配器关闭时取消所有 pending handler tasks 后等待它们退出的耐心时间。
# 修改影响: 设大确保处理器完整结束，设小加速关闭流程。
DEFAULT_HANDLER_DRAIN_TIMEOUT_SECS: Final[float] = 5.0

__all__ = [
    "ADAPTER_RETRY_BACKOFF_INTERVALS",
    "ADAPTER_RETRY_FIXED_DELAY_SECS",
    "CONFIG_CACHE_TIMEOUT_SECS",
    "CONFIG_KEY_ADAPTER_STATUS",
    "CONFIG_KEY_ADAPTER_STATUS_OF",
    "CONFIG_KEY_MODULES_STATUS",
    "CONFIG_KEY_MODULE_STATUS_OF",
    "CONFIG_KEY_ROUTER_CORS",
    "CONFIG_KEY_ROUTER_SECURITY",
    "CONFIG_ROOT_KEY",
    "CONFIG_WRITE_DELAY_SECS",
    "CONFIRM_HINT_WORDS",
    "CONFIRM_NO_WORDS",
    "CONFIRM_YES_WORDS",
    "CONVERSATION_KEY_PREFIX",
    "DEFAULT_ADAPTER_ENABLED",
    "DEFAULT_COMMAND_ALLOW_SPACE_PREFIX",
    "DEFAULT_COMMAND_CASE_SENSITIVE",
    "DEFAULT_COMMAND_DISPATCHER_PRIORITY",
    "DEFAULT_COMMAND_MUST_AT_BOT",
    "DEFAULT_COMMAND_PREFIX",
    "DEFAULT_CONFIG_FILE_PATH",
    "DEFAULT_CORS_HEADERS",
    "DEFAULT_CORS_MAX_AGE_SECS",
    "DEFAULT_CORS_METHODS",
    "DEFAULT_CORS_ORIGINS",
    "DEFAULT_EVENT_SOURCE",
    "DEFAULT_HANDLER_DRAIN_TIMEOUT_SECS",
    "DEFAULT_HANDLER_MAX_CONCURRENCY",
    "DEFAULT_HANDLER_PRIORITY",
    "DEFAULT_HTTP_CLIENT_CONNECT_TIMEOUT_SECS",
    "DEFAULT_HTTP_CLIENT_MAX_RETRIES",
    "DEFAULT_HTTP_CLIENT_RETRY_DELAY_SECS",
    "DEFAULT_HTTP_CLIENT_TIMEOUT_SECS",
    "DEFAULT_HTTP_CLIENT_USER_AGENT",
    "DEFAULT_HTTP_METHODS",
    "DEFAULT_I18N_LANGUAGE",
    "DEFAULT_KV_TABLE_NAME",
    "DEFAULT_LAZY_LOADING_ENABLED",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_LOG_MEMORY_LIMIT",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_MESSAGE_IGNORE_SELF",
    "DEFAULT_MODULE_ENABLED",
    "DEFAULT_MODULE_PRIORITY",
    "DEFAULT_OFFLINE_BOT_EXPIRY_SECS",
    "DEFAULT_PROACTIVE_GC_INTERVAL_SECS",
    "DEFAULT_RATE_LIMIT_CLEANUP_INTERVAL_SECS",
    "DEFAULT_RATE_LIMIT_MAX_REQUESTS",
    "DEFAULT_RATE_LIMIT_WINDOW_SECS",
    "DEFAULT_SECURITY_HEADERS",
    "DEFAULT_SEND_METHOD",
    "DEFAULT_SEND_TARGET_TYPE",
    "DEFAULT_SERVER_HOST",
    "DEFAULT_SERVER_PORT",
    "DEFAULT_STRICT_MODE",
    "DEFAULT_UNINIT_TIMEOUT_SECS",
    "DEFAULT_USE_GLOBAL_DB",
    "DEFAULT_WAIT_TIMEOUT_SECS",
    "DEFAULT_WS_AUTO_ACCEPT",
    "DEFAULT_WS_CLIENT_CONNECT_TIMEOUT_SECS",
    "DEFAULT_WS_CLIENT_HEARTBEAT_SECS",
    "DETAIL_TYPE_CONNECT",
    "DETAIL_TYPE_DISCONNECT",
    "DETAIL_TYPE_FRIEND",
    "DETAIL_TYPE_FRIEND_DECREASE",
    "DETAIL_TYPE_FRIEND_INCREASE",
    "DETAIL_TYPE_GROUP",
    "DETAIL_TYPE_GROUP_MEMBER_DECREASE",
    "DETAIL_TYPE_GROUP_MEMBER_INCREASE",
    "DETAIL_TYPE_HEARTBEAT",
    "DETAIL_TYPE_PRIVATE",
    "DETAIL_TYPE_USER",
    "EVENT_TYPE_MESSAGE",
    "EVENT_TYPE_META",
    "EVENT_TYPE_NOTICE",
    "EVENT_TYPE_REQUEST",
    "FALLBACK_IPV4",
    "FALLBACK_IPV6_HOST",
    "HANDLER_SLOW_THRESHOLD_SECS",
    "LIFECYCLE_TIMER_CORE_INIT",
    "LIFECYCLE_TIMER_CORE_UNINIT",
    "LOGGER_NAME",
    "LOG_RICH_THEME",
    "LOG_TIME_FORMAT",
    "RETCODE_NOT_IMPLEMENTED",
    "RETCODE_OK",
    "SERVER_SHUTDOWN_TIMEOUT_SECS",
    "SQLITE_JOURNAL_MODE",
    "SQLITE_SYNCHRONOUS_MODE",
    "STATUS_FAILED",
    "STATUS_OK",
    "STORAGE_MAX_LIST_INDEX",
    "TEXT_METHOD_INDICATORS",
    "UNINIT_SETTLE_DELAY_SECS",
    "UNKNOWN_PLATFORM",
    "WILDCARD_IPV4",
    "WILDCARD_IPV6",
    "WS_CLOSE_INTERNAL_ERROR",
    "WS_CLOSE_POLICY_VIOLATION",
]
