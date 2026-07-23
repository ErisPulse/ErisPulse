"""
ErisPulse HTTP 客户端抽象基类

定义 HTTP 客户端、响应和客户端 WebSocket 连接的抽象接口，
使模块和适配器无需直接依赖 aiohttp。
具体实现由 Core.client 模块提供（基于 aiohttp）。

{!--< tips >!--}
1. 支持 get / post / put / delete / patch / request 等常用方法
2. 支持 ws_connect 建立 WebSocket 连接
3. 自动记录请求日志和统计信息
4. 推荐所有模块和适配器使用此客户端发送 HTTP 请求和建立 WS 连接
{!--< /tips >!--}
"""

from __future__ import annotations

from typing import Any

from .errors import WebSocketDisconnect
from .websocket import WebSocketConnectionBase, WSMessage


class BaseHttpResponse:
    """
    HTTP 响应抽象基类

    定义统一的响应访问接口，具体实现由 Core.client.HttpResponse 提供。

    {!--< tips >!--}
    通过 .raw 属性可访问底层原生响应对象
    {!--< /tips >!--}

    :example:
    >>> resp = await sdk.client.get("https://httpbin.org/get")
    >>> print(resp.status)
    >>> data = await resp.json()
    """

    @property
    def status(self) -> int:
        """
        HTTP 状态码

        :return: int 状态码 (如 200, 404)
        """
        raise NotImplementedError

    @property
    def reason(self) -> str | None:
        """
        状态描述

        :return: str | None 状态原因短语
        """
        raise NotImplementedError

    @property
    def headers(self):
        """
        响应头

        :return: object 大小写不敏感的响应头映射
        """
        raise NotImplementedError

    @property
    def content_type(self) -> str | None:
        """
        Content-Type 值

        :return: str | None 内容类型
        """
        raise NotImplementedError

    @property
    def url(self):
        """
        响应 URL (可能因重定向而与请求 URL 不同)

        :return: object URL 对象
        """
        raise NotImplementedError

    @property
    def raw(self):
        """
        底层框架原生 Response 对象

        :return: object 原生响应实例
        """
        raise NotImplementedError

    async def read(self) -> bytes:
        """
        读取响应体原始字节

        :return: bytes 响应体内容
        """
        raise NotImplementedError

    async def text(self, encoding: str | None = None) -> str:
        """
        读取响应体为文本

        :param encoding: str | None 指定编码 (可选, 默认自动检测)
        :return: str 文本内容
        """
        raise NotImplementedError

    async def json(self, **kwargs) -> Any:
        """
        解析响应体为 JSON

        :param kwargs: 传递给解析器的额外参数
        :return: Any 解析后的数据
        """
        raise NotImplementedError


class BaseClientWebSocket(WebSocketConnectionBase):
    """
    客户端 WebSocket 连接抽象基类

    扩展 WebSocketConnectionBase，增加客户端特有的消息类型处理和连接状态。

    {!--< tips >!--}
    1. 通过 sdk.client.ws_connect() 获取实例
    2. 使用 receive() / iter_messages() 处理原始消息类型
    3. 使用 receive_text() / iter_text() 等高级方法自动过滤消息类型
    {!--< /tips >!--}

    :example:
    >>> ws = await sdk.client.ws_connect("wss://example.com/ws")
    >>> async for msg in ws.iter_messages():
    ...     if msg.type == WSMessage.TEXT:
    ...         await ws.send_text(f"Echo: {msg.data}")
    """

    __slots__ = ("_closed",)

    def __init__(self, ws):
        """
        :param ws: object 底层框架 WebSocket 对象
        """
        super().__init__(ws)
        self._closed = False

    @property
    def closed(self) -> bool:
        """
        连接是否已关闭

        :return: bool 是否已关闭
        """
        raise NotImplementedError

    async def receive(self) -> WSMessage:
        """
        接收原始消息

        :return: WSMessage 消息对象 (包含 type 和 data 属性)
        """
        raise NotImplementedError

    async def iter_messages(self):
        """
        迭代原始消息直到断开

        自动在收到 CLOSE 或 ERROR 消息时停止迭代。

        :return: async generator 逐条返回 WSMessage

        :example:
        >>> async for msg in ws.iter_messages():
        ...     if msg.type == WSMessage.TEXT:
        ...         print(msg.data)
        ...     elif msg.type == WSMessage.CLOSE:
        ...         break
        """
        try:
            while True:
                msg = await self.receive()
                if msg.type in (WSMessage.CLOSE, WSMessage.ERROR):
                    break
                yield msg
        except WebSocketDisconnect:
            pass


class BaseHttpClient:
    """
    HTTP 客户端抽象基类

    定义统一的异步 HTTP 请求和 WebSocket 连接接口，
    具体实现由 Core.client.HttpClient 提供。

    {!--< tips >!--}
    1. 通过 sdk.client 获取全局单例，也可自行实例化
    2. 使用 get/post/put/delete/patch 快捷方法或通用 request 方法
    3. 使用 ws_connect 建立 WebSocket 连接
    4. 推荐所有模块和适配器使用此客户端发送 HTTP 请求
    {!--< /tips >!--}

    :example:
    >>> resp = await sdk.client.get("https://httpbin.org/get")
    >>> data = await resp.json()
    >>>
    >>> ws = await sdk.client.ws_connect("wss://example.com/ws")
    >>> await ws.send_text("Hello")
    """

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        data: Any = None,
        json: Any = None,
        files: dict[str, Any] | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        **kwargs,
    ) -> BaseHttpResponse:
        """
        发送 HTTP 请求

        :param method: str HTTP 方法 (GET, POST, PUT, DELETE, PATCH 等)
        :param url: str 请求 URL
        :param params: dict[str, str] | None 查询参数 (可选)
        :param headers: dict[str, str] | None 额外请求头 (可选)
        :param data: Any 请求体 (表单或原始数据) (可选)
        :param json: Any JSON 请求体 (可选)
        :param files: dict[str, Any] | None 文件上传字段 (可选, 自动构建 multipart/form-data)
        :param timeout: float | None 本次请求超时 (秒) (可选, 覆盖默认值)
        :param max_retries: int | None 本次最大重试次数 (可选, 覆盖默认值)
        :param kwargs: 传递给底层请求的额外参数
        :return: BaseHttpResponse 响应对象
        """
        raise NotImplementedError

    async def ws_connect(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        heartbeat: float | None = None,
        **kwargs,
    ) -> BaseClientWebSocket:
        """
        建立 WebSocket 连接

        :param url: str WebSocket 服务器 URL
        :param headers: dict[str, str] | None 额外请求头 (可选)
        :param heartbeat: float | None 心跳间隔秒数 (可选)
        :param kwargs: 传递给底层 WS 连接的额外参数
        :return: BaseClientWebSocket WebSocket 连接对象

        :example:
        >>> ws = await sdk.client.ws_connect("wss://example.com/ws")
        >>> async for text in ws.iter_text():
        ...     await ws.send_text(f"Echo: {text}")
        """
        raise NotImplementedError

    async def get(self, url: str, **kwargs) -> BaseHttpResponse:
        """
        发送 GET 请求

        :param url: str 请求 URL
        :return: BaseHttpResponse 响应对象
        """
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> BaseHttpResponse:
        """
        发送 POST 请求

        :param url: str 请求 URL
        :return: BaseHttpResponse 响应对象
        """
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> BaseHttpResponse:
        """
        发送 PUT 请求

        :param url: str 请求 URL
        :return: BaseHttpResponse 响应对象
        """
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> BaseHttpResponse:
        """
        发送 DELETE 请求

        :param url: str 请求 URL
        :return: BaseHttpResponse 响应对象
        """
        return await self.request("DELETE", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> BaseHttpResponse:
        """
        发送 PATCH 请求

        :param url: str 请求 URL
        :return: BaseHttpResponse 响应对象
        """
        return await self.request("PATCH", url, **kwargs)

    async def close(self) -> None:
        """
        关闭客户端会话并释放资源
        """
        raise NotImplementedError

    @property
    def stats(self) -> dict[str, int]:
        """
        请求统计

        :return: dict[str, int] 统计数据
        """
        raise NotImplementedError

    def reset_stats(self) -> None:
        """
        重置统计数据
        """
        raise NotImplementedError


__all__ = [
    "BaseClientWebSocket",
    "BaseHttpClient",
    "BaseHttpResponse",
]
