"""
ErisPulse 基础模块

提供平台适配器、模块、存储后端、路由和客户端的基类与抽象接口
"""

from .adapter import SendDSL, RequestDSL, BaseAdapter
from .module import BaseModule
from .storage import BaseStorage, BaseQueryBuilder
from .errors import (
    ErisPulseError,
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketError,
    WebSocketDisconnect,
)
from .websocket import WebSocketConnectionBase, WSMessage
from .router import HttpRequest, WebSocketConnection
from .client import BaseHttpClient, BaseHttpResponse, BaseClientWebSocket

__all__ = [
    "BaseAdapter",
    "SendDSL",
    "RequestDSL",
    "BaseModule",
    "BaseStorage",
    "BaseQueryBuilder",
    "HttpRequest",
    "WebSocketConnection",
    "WebSocketConnectionBase",
    "WSMessage",
    "WebSocketDisconnect",
    "BaseHttpClient",
    "BaseHttpResponse",
    "BaseClientWebSocket",
    "ErisPulseError",
    "ClientError",
    "ClientConnectionError",
    "ClientTimeoutError",
    "HTTPStatusError",
    "WebSocketError",
]
