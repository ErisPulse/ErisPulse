"""
ErisPulse 基础模块

提供平台适配器、模块、存储后端、路由和客户端的基类与抽象接口
"""

from .adapter import ApiDSL, SendDSL, RequestDSL, BaseAdapter
from .converter import BaseConverter
from .send_rules import SendContext
from .send_builder import SendBuilder, BatchContext
from .module import BaseModule, ModuleMeta
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

# 配置 / i18n Schema 类型
from .config_schema import (
    AdapterConfig,
    BaseConfig,
    BotAccountConfig,
)
from .i18n_schema import (
    BaseI18n,
    I18nKey,
    key,
)

__all__ = [
    # 配置 Schema 别名（= BaseConfig）
    "AdapterConfig",
    "ApiDSL",
    "BaseAdapter",
    "BaseClientWebSocket",
    "BaseConfig",
    "BaseConverter",
    "BaseHttpClient",
    "BaseHttpResponse",
    # i18n 键声明 Schema 基类（命名对齐 BaseConfig）
    "BaseI18n",
    "BaseModule",
    "BaseQueryBuilder",
    "BaseStorage",
    "BatchContext",
    "BotAccountConfig",
    "ClientConnectionError",
    "ClientError",
    "ClientTimeoutError",
    "ErisPulseError",
    "HTTPStatusError",
    "HttpRequest",
    # i18n 单键声明
    "I18nKey",
    "KVQueryBuilder",
    "ModuleMeta",
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
