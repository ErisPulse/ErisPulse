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
ADAPTER_RETRY_BACKOFF_INTERVALS = [60, 10 * 60, 30 * 60, 60 * 60]

# 超出退避列表后的固定重试间隔（秒），默认 3 小时。
# 修改影响: 长时间连接失败时的重连频率。
ADAPTER_RETRY_FIXED_DELAY_SECS = 3 * 60 * 60

# ==============================================================================
# 路由服务器默认值
#
# 控制内置 HTTP/WebSocket 服务器的监听地址和行为。
# 使用位置: Core/router.py -> start(), stop(), _format_url_for_display()
# ==============================================================================

# 路由服务器默认监听地址。
# 修改影响: 服务器可访问范围。"0.0.0.0" 表示所有网卡，"127.0.0.1" 仅本机。
DEFAULT_SERVER_HOST = "0.0.0.0"

# 路由服务器默认监听端口。
# 修改影响: 客户端（如 SandboxAdapter WebUI）需要对应修改连接端口。
DEFAULT_SERVER_PORT = 8000

# 路由服务器关闭时的超时时间（秒）。
# 修改影响: Ctrl+C 后等待 uvicorn 关闭的耐心时间。超时后强制终止。
SERVER_SHUTDOWN_TIMEOUT_SECS = 5.0

# ==============================================================================
# 配置键模板
#
# TOML 配置文件中的键路径模板。用 .format() 拼接平台名/模块名。
# 使用位置: Core/adapter.py -> _config_register(), is_enabled(), enable(), disable(), list_items()
#            Core/module.py  -> _config_register(), is_enabled(), enable(), disable(), list_items()
# ==============================================================================

# 配置文件根键名。
# 修改影响: 整个 ErisPulse 配置树的顶层命名空间。已有配置文件不会自动迁移。
CONFIG_ROOT_KEY = "ErisPulse"

# 适配器启用状态的配置键前缀。
# 例如: ErisPulse.adapters.status.kook = true
# 修改影响: 适配器启用/禁用状态的读写路径。已有配置不会自动迁移。
CONFIG_KEY_ADAPTER_STATUS = "ErisPulse.adapters.status"
CONFIG_KEY_ADAPTER_STATUS_OF = "ErisPulse.adapters.status.{}"  # .format(platform)

# 模块启用状态的配置键前缀。
# 例如: ErisPulse.modules.status.Dashboard = true
# 修改影响: 模块启用/禁用状态的读写路径。
CONFIG_KEY_MODULES_STATUS = "ErisPulse.modules.status"
CONFIG_KEY_MODULE_STATUS_OF = "ErisPulse.modules.status.{}"  # .format(module_name)

# 路由 CORS 配置键。
# 修改影响: CORS 中间件配置的读取路径。
CONFIG_KEY_ROUTER_CORS = "ErisPulse.router.cors"

# 路由安全头配置键。
# 修改影响: 安全响应头配置的读取路径。
CONFIG_KEY_ROUTER_SECURITY = "ErisPulse.router.security"

# ==============================================================================
# 配置管理器
#
# 控制配置文件的读写行为和缓存策略。
# 使用位置: Core/config.py -> ConfigManager.__init__()
# ==============================================================================

# 默认配置文件路径（相对于工作目录）。
# 修改影响: 配置文件的读写位置。仅在 ConfigManager 未指定路径时生效。
DEFAULT_CONFIG_FILE_PATH = "config/config.toml"

# 配置缓存过期时间（秒）。
# 修改影响: 内存中缓存的配置值多久后重新从文件读取。设大减少磁盘IO，设小实时性更高。
CONFIG_CACHE_TIMEOUT_SECS = 60

# 配置延迟写入间隔（秒）。
# 修改影响: setConfig() 后多久才真正写入磁盘。设大减少磁盘写入频率，设小数据安全性更高。
CONFIG_WRITE_DELAY_SECS = 5

# ==============================================================================
# 日志系统
#
# 控制日志的输出格式、存储限制和级别。
# 使用位置: Core/logger.py -> Logger.__init__()
# ==============================================================================

# Python logging 模块的 logger 名称。
# 修改影响: 日志过滤时的 logger 名。第三方日志处理器需对应修改。
LOGGER_NAME = "ErisPulse"

# 内存中保留的最大日志条数。
# 修改影响: WebUI 日志查看器的历史深度。设大占用更多内存，设小丢失更多历史。
DEFAULT_LOG_MEMORY_LIMIT = 1000

# 日志初始级别（启动时默认值）。
# 运行时会被配置文件中的 ErisPulse.logger.level 覆盖。
# 修改影响: 仅影响未配置日志级别时的默认行为。
DEFAULT_LOG_LEVEL = "INFO"

# Rich 控制台日志的时间戳格式（strftime 语法）。
# 修改影响: 终端日志输出的时间显示样式。
LOG_TIME_FORMAT = "[%H:%M:%S]"

# ==============================================================================
# SQLite 存储引擎
#
# 控制 SQLite 数据库的性能和行为。
# 使用位置: Core/storage.py -> SQLiteKVStore._connect(), _init_db()
# ==============================================================================

# WAL (Write-Ahead Logging) 模式，允许读写并发。
# 修改影响: 设为 DELETE 模式可提升单线程写入性能，但会阻塞读操作。
SQLITE_JOURNAL_MODE = "PRAGMA journal_mode=WAL"

# 同步模式。NORMAL 在 WAL 模式下安全且更快。
# 修改影响: 设为 FULL 更安全（断电不丢数据），但写入更慢。
SQLITE_SYNCHRONOUS_MODE = "PRAGMA synchronous=NORMAL"

# KV 存储的默认表名。
# 修改影响: 数据库中的表名。已有数据库不会自动重命名。
DEFAULT_KV_TABLE_NAME = "config"

# 是否默认使用全局数据库（框架安装目录下的 data/config.db）。
# 配置默认值。True = 全局共享，False = 项目级（当前工作目录下 config/config.db）。
# 修改影响: 数据存储位置。
DEFAULT_USE_GLOBAL_DB = False

# ==============================================================================
# 路由限流
#
# 控制路由限流（rate-limit）的默认参数。
# 使用位置: Core/router.py -> _parse_rate_limit()
# ==============================================================================

# 默认限流时间窗口（秒）。
# 修改影响: 限流计数器的统计周期。
DEFAULT_RATE_LIMIT_WINDOW_SECS = 60

# 默认限流窗口内最大请求数。
# 修改影响: 触发 429 响应的阈值。
DEFAULT_RATE_LIMIT_MAX_REQUESTS = 10

# 未指定 HTTP 方法时的默认值。
# 使用位置: Core/router.py -> register_http()
# 修改影响: 路由注册时的默认 HTTP 方法。
DEFAULT_HTTP_METHODS = ["POST"]

# WebSocket 路由是否默认自动接受连接。
# 使用位置: Core/router.py -> register_ws()
# 修改影响: 设为 False 则需在 handler 中手动 accept。
DEFAULT_WS_AUTO_ACCEPT = True

# ==============================================================================
# CORS 中间件
#
# 控制跨域资源共享的默认策略。
# 使用位置: Core/router.py -> setup_cors(), _apply_config()
# ==============================================================================

# 默认允许的来源、方法、头。
# 修改影响: 未显式配置 CORS 时的跨域访问策略。["*"] 表示允许所有。
DEFAULT_CORS_ORIGINS = ["*"]
DEFAULT_CORS_METHODS = ["*"]
DEFAULT_CORS_HEADERS = ["*"]

# CORS 预检请求的缓存时间（秒）。
# 修改影响: 浏览器缓存 OPTIONS 响应的时长。设大减少预检请求，设小 CORS 变更更快生效。
DEFAULT_CORS_MAX_AGE_SECS = 600

# ==============================================================================
# 安全响应头
#
# 控制 HTTP 响应的默认安全头。
# 使用位置: Core/router.py -> setup_security_headers()
# ==============================================================================

# 默认安全头字典。
# 修改影响: 所有 HTTP 响应携带的安全头。可被 setup_security_headers(headers=...) 合并覆盖。
DEFAULT_SECURITY_HEADERS = {
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
WS_CLOSE_POLICY_VIOLATION = 1008

# 1011: 服务器内部错误。
# 修改影响: 客户端收到此关闭码时的重连策略。
WS_CLOSE_INTERNAL_ERROR = 1011

# ==============================================================================
# 网络地址常量
#
# 用于 URL 显示格式化和本地 IP 发现。
# 使用位置: Core/router.py -> _format_url_for_display(), _discover_local_ips()
# ==============================================================================

# 通配符地址（监听所有网卡）。
WILDCARD_IPV4 = "0.0.0.0"
WILDCARD_IPV6 = "[::]"

# 当无法发现本地 IP 时的回退地址。
# 修改影响: 控制台显示的局域网访问地址。
FALLBACK_IPV4 = "127.0.0.1"
FALLBACK_IPV6_HOST = "localhost"

# ==============================================================================
# 生命周期管理
#
# 控制框架初始化/反初始化的计时和事件来源标识。
# 使用位置: sdk.py -> init(), uninit()
#            Core/lifecycle.py -> submit_event()
# ==============================================================================

# 事件默认来源标识符。
# 修改影响: lifecycle.submit_event() 的 source 默认值。影响事件溯源。
DEFAULT_EVENT_SOURCE = "ErisPulse"

# 反初始化时等待事件处理完成的缓冲时间（秒）。
# 修改影响: 设大确保异步事件处理完成，设小加速关闭流程。过小可能丢失事件。
UNINIT_SETTLE_DELAY_SECS = 0.1

# 生命周期计时器名称（用于性能分析）。
# 修改影响: 生命周期事件中的计时器标识。仅影响日志和 WebUI 显示。
LIFECYCLE_TIMER_CORE_INIT = "core.init"
LIFECYCLE_TIMER_CORE_UNINIT = "core.uninit"

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
DEFAULT_COMMAND_PREFIX = "/"

# 命令是否区分大小写。
# 配置默认值，可被 ErisPulse.event.command.case_sensitive 覆盖。
# 修改影响: True 时 /Help 和 /help 是不同命令，False 时不区分。
DEFAULT_COMMAND_CASE_SENSITIVE = True

# 是否允许前缀和命令名之间有空格。
# 配置默认值。True 时 "/ help" 等同于 "/help"。
DEFAULT_COMMAND_ALLOW_SPACE_PREFIX = False

# 群聊中是否必须 @机器人 才触发命令。
# 配置默认值。True 时群消息中 /help 需要 @Bot /help 才生效，私聊不受影响。
DEFAULT_COMMAND_MUST_AT_BOT = False

# 是否忽略自身发送的消息。
# 配置默认值。设为 False 会导致命令系统处理自己发出的消息（通常不期望）。
DEFAULT_MESSAGE_IGNORE_SELF = True

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
DEFAULT_HANDLER_PRIORITY = 0

# 等待用户回复的默认超时时间（秒）。
# 使用位置: command.wait_reply(), Event.wait_reply(), Event.wait_for() 等 8 处。
# 修改影响: 所有等待用户交互的默认超时。设大用户有更多反应时间，设小释放资源更快。
DEFAULT_WAIT_TIMEOUT_SECS = 60.0

# 等待回复时的默认最大重试次数。
# 使用位置: Core/Event/wrapper.py -> Conversation 字段重试。
# 修改影响: 验证器拒绝回复后的重试次数。
DEFAULT_MAX_RETRIES = 3

# 事件处理器执行耗时警告阈值（秒）。
# 使用位置: Core/adapter.py -> emit() 中的 handler 执行监控。
# 修改影响: 当单个处理器执行超过此时间时记录 WARNING 日志。
HANDLER_SLOW_THRESHOLD_SECS = 1.0

# 平台标识的回退值。
# 当事件数据缺少 platform 字段时使用。
# 修改影响: 日志和事件处理中的平台标识显示。
UNKNOWN_PLATFORM = "unknown"

# ==============================================================================
# OneBot12 事件类型
#
# OB12 标准事件的 type 字段值。
# 使用位置: Core/Event/base.py, message.py, notice.py, request.py, meta.py
#            Core/Event/wrapper.py -> Event.is_message() 等类型判断方法
# ==============================================================================

# 消息事件（私聊、群聊等用户消息）。
EVENT_TYPE_MESSAGE = "message"

# 通知事件（好友变动、群成员变动等系统通知）。
EVENT_TYPE_NOTICE = "notice"

# 请求事件（好友请求、群邀请等需要确认的事件）。
EVENT_TYPE_REQUEST = "request"

# 元事件（连接、断开、心跳等适配器生命周期事件）。
EVENT_TYPE_META = "meta"

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

DETAIL_TYPE_PRIVATE = "private"               # 私聊消息
DETAIL_TYPE_USER = "user"                     # 用户类型（用于 command.py 中与 "private" 同义检查）
DETAIL_TYPE_GROUP = "group"                   # 群聊消息 / 群请求
DETAIL_TYPE_FRIEND = "friend"                 # 好友请求
DETAIL_TYPE_FRIEND_INCREASE = "friend_increase"      # 好友添加通知
DETAIL_TYPE_FRIEND_DECREASE = "friend_decrease"      # 好友删除通知
DETAIL_TYPE_GROUP_MEMBER_INCREASE = "group_member_increase"  # 群成员增加通知
DETAIL_TYPE_GROUP_MEMBER_DECREASE = "group_member_decrease"  # 群成员减少通知
DETAIL_TYPE_CONNECT = "connect"               # 适配器连接上线（元事件）
DETAIL_TYPE_DISCONNECT = "disconnect"         # 适配器断开连接（元事件）
DETAIL_TYPE_HEARTBEAT = "heartbeat"           # 适配器心跳（元事件）

# ==============================================================================
# OneBot12 协议常量
#
# OB12 标准返回码和状态值。
# 使用位置: Core/Bases/adapter.py -> SendDSL._not_impl() 等错误响应
# ==============================================================================

# 方法未实现时的返回码。
RETCODE_NOT_IMPLEMENTED = 10002

# 失败状态标识。
STATUS_FAILED = "failed"

# 成功状态标识和返回码。
STATUS_OK = "ok"
RETCODE_OK = 0

# ==============================================================================
# 消息发送默认值
#
# 控制 SendDSL 的默认行为。
# 使用位置: Core/Bases/adapter.py -> SendDSL.ByMethod(), SendDSL._send()
#            Core/Event/wrapper.py -> Event._send_by_platform() 等
# ==============================================================================

# 默认发送方法名（OB12 消息段类型）。
# 修改影响: 未指定 method 时默认发送文本消息。
DEFAULT_SEND_METHOD = "Text"

# 默认发送目标类型（当无法从事件推断时的回退值）。
# 修改影响: Send.To() 未指定类型时的目标推断。
DEFAULT_SEND_TARGET_TYPE = "user"

# Conversation 存储键前缀（用于持久化会话上下文）。
# 修改影响: SQLite 中存储会话数据的键名格式。已有数据不会自动迁移。
CONVERSATION_KEY_PREFIX = "conversation"

# ==============================================================================
# 确认词汇集
#
# 用于 Conversation.confirm() 判断用户回复是"肯定"还是"否定"。
# 使用位置: Core/Event/wrapper.py -> Conversation.confirm()
# 修改影响: 用户用自然语言回复时的匹配结果。支持中英文。
# ==============================================================================

CONFIRM_YES_WORDS = frozenset({
    "是", "yes", "y", "确认", "确定", "好", "好的",
    "ok", "okay", "true", "对", "嗯", "行", "同意",
    "没问题", "可以", "当然", "嗯嗯", "是的",
})
CONFIRM_NO_WORDS = frozenset({
    "否", "no", "n", "取消", "不", "不要", "不行",
    "cancel", "false", "错", "不对", "别", "拒绝",
    "不可以", "算了", "不需要", "不是",
})

# ==============================================================================
# 框架管理默认值
#
# 控制模块/适配器的注册和加载行为。
# 使用位置: Core/module.py  -> _config_register()
#            Core/adapter.py -> _config_register()
#            Core/Bases/module.py -> BaseModule.get_load_strategy()
# ==============================================================================

# 适配器注册时的默认启用状态。
# 配置默认值。False 表示新注册的适配器默认禁用，需手动 enable()。
DEFAULT_ADAPTER_ENABLED = False

# 模块注册时的默认启用状态。
# 配置默认值。False 表示新注册的模块默认禁用，需手动 enable()。
DEFAULT_MODULE_ENABLED = False

# 模块默认加载优先级（数值越大越先加载）。
# 使用位置: BaseModule.get_load_strategy() 返回值。
# 修改影响: 模块加载顺序。0 = 普通，正数 = 优先加载，负数 = 延后加载。
DEFAULT_MODULE_PRIORITY = 0

# 是否默认启用懒加载。
# 配置默认值，可被 ErisPulse.framework.enable_lazy_loading 覆盖。
# True 时模块在首次被访问时才加载，False 时框架启动时立即加载。
DEFAULT_LAZY_LOADING_ENABLED = True

# ==============================================================================
# HTTP 客户端默认值
#
# 控制内置 HTTP 客户端的超时、重试和连接行为。
# 使用位置: Core/Bases/client.py -> HttpClient.__init__()
# ==============================================================================

# HTTP 客户端请求总超时（秒）。
# 修改影响: 超过此时间的请求将被中止。
DEFAULT_HTTP_CLIENT_TIMEOUT_SECS = 30.0

# HTTP 客户端连接超时（秒）。
# 修改影响: 建立 TCP 连接的最大等待时间。
DEFAULT_HTTP_CLIENT_CONNECT_TIMEOUT_SECS = 10.0

# HTTP 客户端默认最大重试次数。
# 修改影响: 请求失败后的自动重试次数。0 = 不重试。
DEFAULT_HTTP_CLIENT_MAX_RETRIES = 0

# HTTP 客户端重试间隔（秒）。
# 修改影响: 每次重试之间的等待时间。
DEFAULT_HTTP_CLIENT_RETRY_DELAY_SECS = 1.0

# HTTP 客户端默认 User-Agent。
# 修改影响: 所有出站 HTTP 请求的默认 User-Agent 头。
DEFAULT_HTTP_CLIENT_USER_AGENT = ""
