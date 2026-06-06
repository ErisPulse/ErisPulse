"""
ErisPulse WebSocket 共享基类

定义客户端和服务端 WebSocket 连接的统一抽象接口。
send/receive/iter 方法签名在两端保持一致，具体实现由子类提供。

{!--< tips >!--}
1. 客户端和服务端 WebSocket 共享相同的 send/receive/iter 接口
2. iter_text/iter_bytes/iter_json 自动在断开时停止迭代
3. 通过 on_disconnect/on_error 注册生命周期回调
{!--< /tips >!--}
"""

from __future__ import annotations

from typing import Any
from collections.abc import Callable

from .errors import WebSocketDisconnect


class WSMessage:
    """
    WebSocket 消息抽象

    统一的 WebSocket 消息类型，不依赖底层库的消息类型。
    用于客户端 WebSocket 的低级消息接收。

    :example:
    >>> async for msg in ws.iter_messages():
    ...     if msg.type == WSMessage.TEXT:
    ...         print(msg.data)
    ...     elif msg.type == WSMessage.CLOSE:
    ...         break
    """

    __slots__ = ("type", "data")

    TEXT = "text"
    BINARY = "binary"
    CLOSE = "close"
    ERROR = "error"

    def __init__(self, type: str, data: Any = None):
        """
        :param type: str 消息类型 (WSMessage.TEXT / BINARY / CLOSE / ERROR)
        :param data: Any 消息数据
        """
        self.type = type
        self.data = data

    def __repr__(self) -> str:
        return f"WSMessage(type={self.type!r}, data={self.data!r})"


class WebSocketConnectionBase:
    """
    WebSocket 连接共享基类

    定义客户端和服务端 WebSocket 连接的统一接口。
    send/receive 由子类实现，iter 方法提供基于 receive 的默认实现。

    {!--< tips >!--}
    1. 通过 .raw 属性可访问底层框架原生对象
    2. 服务端和客户端共享此基类，接口一致
    3. 使用 on_disconnect/on_error 注册生命周期回调
    {!--< /tips >!--}

    :example:
    >>> # 服务端和客户端共享相同的接口
    >>> await ws.send_text("Hello")
    >>> async for msg in ws.iter_text():
    ...     await ws.send_text(f"Echo: {msg}")
    """

    __slots__ = ("_ws", "_on_disconnect_handlers", "_on_error_handlers")

    def __init__(self, ws):
        """
        :param ws: object 底层框架 WebSocket 对象
        """
        self._ws = ws
        self._on_disconnect_handlers: list[Callable] = []
        self._on_error_handlers: list[Callable] = []

    # ---- Properties ----

    @property
    def url(self):
        """
        连接 URL

        :return: object URL 对象
        """
        return self._ws.url

    @property
    def headers(self):
        """
        请求头

        :return: object Headers 对象
        """
        return self._ws.headers

    @property
    def raw(self):
        """
        底层框架原生对象

        :return: object 原生 WebSocket 实例
        """
        return self._ws

    # ---- Send (abstract) ----

    async def send_text(self, data: str) -> None:
        """
        发送文本消息

        :param data: str 文本内容
        """
        raise NotImplementedError

    async def send_bytes(self, data: bytes) -> None:
        """
        发送二进制消息

        :param data: bytes 二进制内容
        """
        raise NotImplementedError

    async def send_json(self, data: Any, mode: str = "text") -> None:
        """
        发送 JSON 消息

        :param data: Any 要序列化的数据
        :param mode: str 发送模式 ("text" 或 "binary") (默认: "text")
        """
        raise NotImplementedError

    # ---- Receive (abstract) ----

    async def receive_text(self) -> str:
        """
        接收文本消息

        :return: str 文本内容
        :raises WebSocketDisconnect: 连接断开时
        """
        raise NotImplementedError

    async def receive_bytes(self) -> bytes:
        """
        接收二进制消息

        :return: bytes 二进制内容
        :raises WebSocketDisconnect: 连接断开时
        """
        raise NotImplementedError

    async def receive_json(self, mode: str = "text") -> Any:
        """
        接收 JSON 消息

        :param mode: str 接收模式 ("text" 或 "binary") (默认: "text")
        :return: Any 解析后的 JSON 数据
        :raises WebSocketDisconnect: 连接断开时
        """
        raise NotImplementedError

    # ---- Iterators (concrete) ----

    async def iter_text(self):
        """
        迭代文本消息直到断开

        :return: async generator 逐条返回文本消息
        """
        try:
            while True:
                yield await self.receive_text()
        except WebSocketDisconnect:
            pass

    async def iter_bytes(self):
        """
        迭代二进制消息直到断开

        :return: async generator 逐条返回二进制消息
        """
        try:
            while True:
                yield await self.receive_bytes()
        except WebSocketDisconnect:
            pass

    async def iter_json(self):
        """
        迭代 JSON 消息直到断开

        :return: async generator 逐条返回 JSON 数据
        """
        try:
            while True:
                yield await self.receive_json()
        except WebSocketDisconnect:
            pass

    # ---- Close (abstract) ----

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        """
        关闭 WebSocket 连接

        :param code: int 关闭码 (默认: 1000)
        :param reason: str | None 关闭原因 (可选)
        """
        raise NotImplementedError

    # ---- Lifecycle hooks ----

    def on_disconnect(self, handler: Callable | None = None):
        """
        注册断开连接回调

        可作为装饰器或直接调用。

        :param handler: Callable 断开连接时的回调函数，签名: (ws, reason="") -> None

        :example:
        >>> @ws.on_disconnect
        ... async def handle_disconnect(ws, reason="unknown"):
        ...     print(f"Disconnected: {reason}")
        """
        if handler is not None:
            self._on_disconnect_handlers.append(handler)
            return handler

        def decorator(func: Callable):
            self._on_disconnect_handlers.append(func)
            return func

        return decorator

    def on_error(self, handler: Callable | None = None):
        """
        注册错误回调

        :param handler: Callable 发生错误时的回调函数，签名: (ws, error="") -> None

        :example:
        >>> @ws.on_error
        ... async def handle_error(ws, error=""):
        ...     print(f"Error: {error}")
        """
        if handler is not None:
            self._on_error_handlers.append(handler)
            return handler

        def decorator(func: Callable):
            self._on_error_handlers.append(func)
            return func

        return decorator
