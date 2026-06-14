"""
ErisPulse 核心模块

提供了一系列用于构建和管理应用的核心组件，包括适配器、模块、存储、配置、路由和生命周期管理等。
"""

from .lifecycle import lifecycle, LifecycleManager
from .adapter import adapter, AdapterManager
from .Bases import (
    BaseAdapter,
    BaseModule,
    SendDSL,
    RequestDSL,
    BaseStorage,
    BaseQueryBuilder,
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

from . import Event
from .Event.message_builder import MessageBuilder

env = storage

client = HttpClient()

__all__ = [
    "Event",  # 事件模块包
    "adapter",  # 适配器模块单例
    "AdapterManager",  # 适配器管理器类
    "BaseAdapter",  # 适配器基类
    "SendDSL",  # 发送消息 DSL 类
    "RequestDSL",  # 请求消息 DSL 类
    "MessageBuilder",  # 消息构建器类
    "module",  # 模块模块单例
    "ModuleManager",  # 模块管理器类
    "BaseModule",  # 模块基类
    "storage",  # 存储模块单例
    "StorageManager",  # 存储管理器类
    "BaseStorage",  # 存储基类
    "BaseQueryBuilder",  # 查询构建器基类
    "config",  # 配置模块单例
    "env",  # 配置管理器别名
    "ConfigManager",  # 配置管理器类
    "router",  # 路由模块单例
    "RouterManager",  # 路由管理器类
    "RouteGroup",  # 路由分组类
    "HttpRequest",  # HTTP 请求类
    "WebSocketConnection",  # WebSocket 连接类
    "WebSocketConnectionBase",  # WebSocket 连接基类
    "WSMessage",  # WebSocket 消息类
    "WebSocketDisconnect",  # WebSocket 断开连接异常类
    "HttpClient",  # HTTP 客户端类
    "HttpResponse",  # HTTP 响应类
    "ClientWebSocket",  # WebSocket 客户端类
    "client",  # HTTP 客户端别名
    "BaseHttpClient",  # HTTP 客户端基类
    "BaseHttpResponse",  # HTTP 响应基类
    "BaseClientWebSocket",  # WebSocket 客户端基类
    "ErisPulseError",  # ErisPulse 错误基类
    "ClientError",  # HTTP 错误基类
    "ClientConnectionError",  # HTTP 连接错误基类
    "ClientTimeoutError",  # HTTP 超时错误基类
    "HTTPStatusError",  # HTTP 状态错误基类
    "WebSocketError",  # WebSocket 错误基类
    "logger",  # 日志模块单例
    "Logger",  # 日志类
    "LoggerChild",  # 日志子类
    "lifecycle",  # 生命周期模块单例
    "LifecycleManager",  # 生命周期管理器类
    "i18n",  # 国际化模块单例
    "I18nManager",  # 国际化管理器类
]
