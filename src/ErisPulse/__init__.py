"""
ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能。
根命名空间聚合框架公共 API：管理器单例、基类、路由/连接/客户端类型、
错误族、ORM、事件处理器与运行时工具——主流库风格的根导入即推荐写法；
``ErisPulse.Core.*`` / ``ErisPulse.Core.Bases.*`` 等深路径永久保留兼容。

{!--< tips >!--}
1. 使用前请确保已正确安装所有依赖
2. 调用await sdk.init()进行初始化
3. 模块加载采用懒加载机制
4. 推荐根导入：``from ErisPulse import router, client, connections, WebSocketConnection``
{!--< /tips >!--}
"""

# ==================== 管理器单例 ====================
from .Core import (
    adapter,
    client,
    config,
    connections,
    env,
    i18n,
    lifecycle,
    logger,
    master,
    module,
    ownership,
    router,
    scope,
    storage,
    transcript,
)

# ==================== 管理器类 ====================
from .Core import (
    AdapterManager,
    BroadcastResult,
    ConfigManager,
    ConnectionManager,
    I18nManager,
    LifecycleManager,
    Logger,
    LoggerChild,
    MasterManager,
    MasterProvider,
    ModuleManager,
    OwnershipManager,
    RouteGroup,
    RouterManager,
    ScopeManager,
    StorageManager,
    TranscriptManager,
    ShadowLedger,
    ShadowManager,
    ShadowOverlay,
    shadow_ledger,
    shadow_manager,
)

# ==================== 路由 / 连接 / 客户端类型 ====================
from .Core import (
    Client,
    ClientWebSocket,
    Depends,
    HttpClient,
    HttpResponse,
    HttpRequest,
    SseEmitter,
    WSMessage,
    WebSocketConnection,
    WebSocketConnectionBase,
    WebSocketDisconnect,
    respond,
)

# ==================== 基类与 DSL ====================
from .Core import (
    ApiDSL,
    BaseAdapter,
    BaseModule,
    ModuleMeta,
    RequestDSL,
    SendBuilder,
    SendContext,
    SendDSL,
    BatchContext,
)
from .Core.Bases import (
    BaseClient,
    BaseClientWebSocket,
    BaseConverter,
    BaseHttpClient,
    BaseHttpResponse,
)

# ==================== 错误族 ====================
from .Core import (
    ClientConnectionError,
    ClientError,
    ClientTimeoutError,
    ConnectionNotFoundError,
    ConnectionPermissionError,
    ConnectionRegistryError,
    ErisPulseError,
    HTTPStatusError,
    InteractionCancelled,
    InteractionError,
    ModuleCallError,
    ModuleCallTimeoutError,
    ModuleError,
    ModuleNotAvailableError,
    ServiceNotProvidedError,
    SessionOccupiedError,
    ShadowError,
    ShadowPromoteError,
    ShadowSourceError,
    ShadowStateError,
    StorageError,
    StorageUnreachableError,
    StrictModeError,
    WebSocketError,
)

# ==================== ORM / 存储 ====================
from .Core import (
    AlterTableBuilder,
    BaseQueryBuilder,
    BaseStorage,
    ColumnExpr,
    Condition,
    Field,
    KVQueryBuilder,
    Model,
    BaseModel,
    QuerySet,
    SQLDialect,
    SQLQueryBuilder,
    SQLStorageBase,
    relationship,
)
from .Core.Bases import AsyncBridge

# ==================== 配置 / i18n Schema ====================
from .Core.Bases import (
    AdapterConfig,
    BaseConfig,
    BaseI18n,
    BotAccountConfig,
    I18nConfig,
    I18nKey,
    key,
)

# ==================== 事件处理 ====================
from .Core import Event, MessageBuilder
from .Core import compile_entry_matcher, compile_text_matcher, extract_text
from .Core.Event import (
    Conversation,
    RECEIVE_TYPES,
    SEND_TYPES,
    ReceiveType,
    SendType,
    clear_custom_types,
    command,
    convert_to_receive_type,
    convert_to_send_type,
    final_verdict,
    format_dispatch_trace,
    get_dispatch_trace,
    get_id_field,
    get_platform_event_methods,
    get_receive_type,
    get_send_type_and_target_id,
    get_send_types,
    get_standard_types,
    get_target_id,
    infer_receive_type,
    interaction,
    is_standard_type,
    is_valid_send_type,
    message,
    meta,
    notice,
    register_custom_type,
    register_event_method,
    register_event_mixin,
    request,
    start_dispatch_trace,
    trace_step,
    unregister_custom_type,
    unregister_custom_types_by_owner,
    unregister_event_method,
    unregister_event_methods_by_owner,
    unregister_platform_event_methods,
)

# ==================== 运行时工具 ====================
from .runtime import run_main_loop, spawn_later, spawn_thread

# 导入懒加载模块类
from .loaders.module import LazyModule

# 导入实际的SDK对象与 SDK 类型（供模块 __init__ 注解 sdk: SDK = None 使用）
from .sdk import SDK, sdk

# ==================== 版本信息 ====================

__author__ = "ErisPulse"


def __getattr__(name: str):
    """
    惰性解析 ``__version__``（首次访问时经包元数据读取）

    :param name: 属性名
    :return: 属性值
    :raises AttributeError: 未知属性时抛出

    {!--< internal-use >!--}
    避免在 ``import ErisPulse`` 时为读取版本号而加载 importlib.metadata
    及其依赖链（email/zipfile/asyncio 等，冷启动约数十毫秒）
    {!--< /internal-use >!--}
    """
    if name == "__version__":
        global __version__
        import importlib.metadata

        try:
            __version__ = importlib.metadata.version("ErisPulse")
        except importlib.metadata.PackageNotFoundError:
            __version__ = "UnknownVersion"
        return __version__
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# 向后兼容性导出
init = sdk.init
init_sync = sdk.init_sync
init_task = sdk.init_task
load_module = sdk.load_module
run = sdk.run
restart = sdk.restart
uninit = sdk.uninit

# 导出列表
__all__ = [
    # SDK 与兼容函数
    "SDK",
    "LazyModule",
    "__author__",
    "__version__",
    "init",
    "init_sync",
    "init_task",
    "load_module",
    "restart",
    "run",
    "sdk",
    "uninit",
    # 管理器单例
    "adapter",
    "client",
    "config",
    "connections",
    "env",
    "i18n",
    "lifecycle",
    "logger",
    "master",
    "module",
    "ownership",
    "router",
    "scope",
    "storage",
    "transcript",
    # 管理器类
    "AdapterManager",
    "BroadcastResult",
    "ConfigManager",
    "ConnectionManager",
    "I18nManager",
    "LifecycleManager",
    "Logger",
    "LoggerChild",
    "MasterManager",
    "MasterProvider",
    "ModuleManager",
    "OwnershipManager",
    "RouteGroup",
    "RouterManager",
    "ScopeManager",
    "ShadowLedger",
    "ShadowManager",
    "ShadowOverlay",
    "StorageManager",
    "TranscriptManager",
    "shadow_ledger",
    "shadow_manager",
    # 路由 / 连接 / 客户端类型
    "Client",
    "ClientWebSocket",
    "Depends",
    "HttpClient",
    "HttpResponse",
    "HttpRequest",
    "SseEmitter",
    "WSMessage",
    "WebSocketConnection",
    "WebSocketConnectionBase",
    "WebSocketDisconnect",
    "respond",
    # 基类与 DSL
    "ApiDSL",
    "BaseAdapter",
    "BaseClient",
    "BaseClientWebSocket",
    "BaseConverter",
    "BaseHttpClient",
    "BaseHttpResponse",
    "BaseModule",
    "BatchContext",
    "ModuleMeta",
    "RequestDSL",
    "SendBuilder",
    "SendContext",
    "SendDSL",
    # 错误族
    "ClientConnectionError",
    "ClientError",
    "ClientTimeoutError",
    "ConnectionNotFoundError",
    "ConnectionPermissionError",
    "ConnectionRegistryError",
    "ErisPulseError",
    "HTTPStatusError",
    "InteractionCancelled",
    "InteractionError",
    "ModuleCallError",
    "ModuleCallTimeoutError",
    "ModuleError",
    "ModuleNotAvailableError",
    "ServiceNotProvidedError",
    "SessionOccupiedError",
    "ShadowError",
    "ShadowPromoteError",
    "ShadowSourceError",
    "ShadowStateError",
    "StorageError",
    "StorageUnreachableError",
    "StrictModeError",
    "WebSocketError",
    # ORM / 存储
    "AlterTableBuilder",
    "AsyncBridge",
    "BaseModel",
    "BaseQueryBuilder",
    "BaseStorage",
    "ColumnExpr",
    "Condition",
    "Field",
    "KVQueryBuilder",
    "Model",
    "QuerySet",
    "SQLDialect",
    "SQLQueryBuilder",
    "SQLStorageBase",
    "relationship",
    # 配置 / i18n Schema
    "AdapterConfig",
    "BaseConfig",
    "BaseI18n",
    "BotAccountConfig",
    "I18nConfig",
    "I18nKey",
    "key",
    # 事件处理
    "Event",
    "MessageBuilder",
    "Conversation",
    "RECEIVE_TYPES",
    "SEND_TYPES",
    "ReceiveType",
    "SendType",
    "clear_custom_types",
    "command",
    "convert_to_receive_type",
    "convert_to_send_type",
    "final_verdict",
    "format_dispatch_trace",
    "get_dispatch_trace",
    "get_id_field",
    "get_platform_event_methods",
    "get_receive_type",
    "get_send_type_and_target_id",
    "get_send_types",
    "get_standard_types",
    "get_target_id",
    "infer_receive_type",
    "interaction",
    "is_standard_type",
    "is_valid_send_type",
    "message",
    "meta",
    "notice",
    "register_custom_type",
    "register_event_method",
    "register_event_mixin",
    "request",
    "start_dispatch_trace",
    "trace_step",
    "unregister_custom_type",
    "unregister_custom_types_by_owner",
    "unregister_event_method",
    "unregister_event_methods_by_owner",
    "unregister_platform_event_methods",
    # 匹配工具
    "compile_entry_matcher",
    "compile_text_matcher",
    "extract_text",
    # 运行时工具
    "run_main_loop",
    "spawn_later",
    "spawn_thread",
]
