"""
ErisPulse 基础模块

提供平台适配器、模块、存储后端、路由和客户端的基类与抽象接口
"""

from .adapter import SendDSL, RequestDSL, BaseAdapter
from .send_rules import SendContext
from .send_builder import SendBuilder, BatchContext
from .module import BaseModule
from .storage import BaseStorage, BaseQueryBuilder
from .kv_builder import KVQueryBuilder
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
from .router import HttpRequest, WebSocketConnection, SseEmitter
from .client import BaseHttpClient, BaseHttpResponse, BaseClientWebSocket

__all__ = [
    "BaseAdapter",
    "BaseClientWebSocket",
    "BaseHttpClient",
    "BaseHttpResponse",
    "BaseModule",
    "BaseQueryBuilder",
    "BaseStorage",
    "BatchContext",
    "ClientConnectionError",
    "ClientError",
    "ClientTimeoutError",
    "ErisPulseError",
    "HTTPStatusError",
    "HttpRequest",
    "KVQueryBuilder",
    "RequestDSL",
    "SendBuilder",
    "SendContext",
    "SendDSL",
    "SseEmitter",
    "WSMessage",
    "WebSocketConnection",
    "WebSocketConnectionBase",
    "WebSocketDisconnect",
    "WebSocketError",
]
