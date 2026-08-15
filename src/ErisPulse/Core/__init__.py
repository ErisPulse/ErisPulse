"""
ErisPulse 核心模块

提供了一系列用于构建和管理应用的核心组件，包括适配器、模块、存储、配置、路由和生命周期管理等。
"""

from .lifecycle import lifecycle, LifecycleManager
from .adapter import adapter, AdapterManager
from .Bases import (
    BaseAdapter,
    BaseModule,
    ModuleMeta,
    ApiDSL,
    SendDSL,
    SendContext,
    SendBuilder,
    BatchContext,
    RequestDSL,
    BaseStorage,
    BaseQueryBuilder,
    KVQueryBuilder,
)
from .Bases import HttpRequest, WebSocketConnection, WebSocketConnectionBase, WSMessage
from .Bases import (
    WebSocketDisconnect,
    ErisPulseError,
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketError,
)
from .Bases import BaseHttpClient, BaseHttpResponse, BaseClientWebSocket
from .client import HttpClient, HttpResponse, ClientWebSocket
from .storage import storage, StorageManager
from .logger import logger, Logger, LoggerChild
from .module import module, ModuleManager
from .router import router, RouterManager, RouteGroup
from .config import config, ConfigManager
from .i18n import i18n, I18nManager
from .master import master, MasterManager
from .scope import scope, ScopeManager

from . import Event
from .Event.message_builder import MessageBuilder

env = storage

client = HttpClient()

__all__ = [
    "AdapterManager",  # 适配器管理器类
    "ApiDSL",  # 标准 API 动作 DSL 类
    "BaseAdapter",  # 适配器基类
    "BaseClientWebSocket",  # WebSocket 客户端基类
    "BaseHttpClient",  # HTTP 客户端基类
    "BaseHttpResponse",  # HTTP 响应基类
    "BaseModule",  # 模块基类
    "ModuleMeta",  # 模块介绍元信息声明类
    "BaseQueryBuilder",  # 查询构建器基类
    "BaseStorage",  # 存储基类
    "BatchContext",  # 批量发送上下文类
    "ClientConnectionError",  # HTTP 连接错误基类
    "ClientError",  # HTTP 错误基类
    "ClientTimeoutError",  # HTTP 超时错误基类
    "ClientWebSocket",  # WebSocket 客户端类
    "ConfigManager",  # 配置管理器类
    "ErisPulseError",  # ErisPulse 错误基类
    "Event",  # 事件模块包
    "HTTPStatusError",  # HTTP 状态错误基类
    "HttpClient",  # HTTP 客户端类
    "HttpRequest",  # HTTP 请求类
    "HttpResponse",  # HTTP 响应类
    "I18nManager",  # 国际化管理器类
    "KVQueryBuilder",  # KV 查询构建器
    "LifecycleManager",  # 生命周期管理器类
    "Logger",  # 日志类
    "LoggerChild",  # 日志子类
    "MasterManager",  # 框架主人管理器类
    "MessageBuilder",  # 消息构建器类
    "ModuleManager",  # 模块管理器类
    "RequestDSL",  # 请求消息 DSL 类
    "RouteGroup",  # 路由分组类
    "RouterManager",  # 路由管理器类
    "ScopeManager",  # 作用域管理器类
    "SendBuilder",  # 批量发送构建器类
    "SendContext",  # 发送任务实时上下文类
    "SendDSL",  # 发送消息 DSL 类
    "StorageManager",  # 存储管理器类
    "WSMessage",  # WebSocket 消息类
    "WebSocketConnection",  # WebSocket 连接类
    "WebSocketConnectionBase",  # WebSocket 连接基类
    "WebSocketDisconnect",  # WebSocket 断开连接异常类
    "WebSocketError",  # WebSocket 错误基类
    "adapter",  # 适配器模块单例
    "client",  # HTTP 客户端别名
    "config",  # 配置模块单例
    "env",  # 配置管理器别名
    "i18n",  # 国际化模块单例
    "lifecycle",  # 生命周期模块单例
    "logger",  # 日志模块单例
    "master",  # 框架主人模块单例
    "module",  # 模块模块单例
    "router",  # 路由模块单例
    "scope",  # 作用域模块单例
    "storage",  # 存储模块单例
]
