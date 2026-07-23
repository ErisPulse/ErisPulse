"""
ErisPulse 路由抽象基类

提供 HTTP 请求和 WebSocket 连接的服务端抽象接口，
使模块和适配器无需直接依赖 FastAPI/Starlette 即可处理网络请求。

当前实现基于 FastAPI/Starlette 封装，接口风格保持 FastAPI 一致，
未来可替换底层后端（如 aiohttp.web）而无需修改业务代码。

{!--< tips >!--}
1. 使用 HttpRequest 替代 fastapi.Request，接口完全兼容
2. 使用 WebSocketConnection 替代 fastapi.WebSocket，额外提供生命周期钩子
3. 通过 .raw 属性可访问底层原生对象（如需使用框架特有功能）
4. 路由注册 API (sdk.router.get/post/ws 等) 无需任何类型注解即可自动注入抽象类型
{!--< /tips >!--}
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

from .websocket import WebSocketConnectionBase


class HttpRequest:
    """
    HTTP 请求抽象封装

    完全兼容 starlette.requests.Request 的接口风格。
    模块可使用此类替代 fastapi.Request，无需直接依赖 FastAPI。

    {!--< tips >!--}
    通过 .raw 属性可访问底层框架原生 Request 对象
    {!--< /tips >!--}

    :example:
    >>> @sdk.router.get("MyModule", "/api/data")
    ... async def get_data(request: HttpRequest):
    ...     body = await request.json()
    ...     return {"method": request.method, "body": body}
    """

    __slots__ = ("_request",)

    def __init__(self, request):
        """
        :param request: object 底层框架 Request 对象
        """
        self._request = request

    # ---- Properties ----

    @property
    def method(self) -> str:
        """
        HTTP 方法

        :return: str HTTP 方法名 (GET, POST, PUT, DELETE 等)
        """
        return self._request.method

    @property
    def url(self):
        """
        完整请求 URL

        :return: object URL 对象 (支持 str() 转换)
        """
        return self._request.url

    @property
    def base_url(self):
        """
        基础 URL

        :return: object URL 对象
        """
        return self._request.base_url

    @property
    def headers(self):
        """
        请求头 (大小写不敏感)

        :return: object Headers 对象 (支持 .get(key) 和 in 操作符)
        """
        return self._request.headers

    @property
    def query_params(self):
        """
        查询参数

        :return: object QueryParams 对象 (支持 .get(key) 和 .items())
        """
        return self._request.query_params

    @property
    def path_params(self) -> dict[str, Any]:
        """
        路径参数

        :return: dict[str, Any] 路径参数字典
        """
        return self._request.path_params

    @property
    def cookies(self) -> dict[str, str]:
        """
        Cookie 字典

        :return: dict[str, str] Cookie 键值对
        """
        return self._request.cookies

    @property
    def client(self):
        """
        客户端地址

        :return: object | None 包含 .host 和 .port 属性的地址对象
        """
        return self._request.client

    @property
    def state(self):
        """
        请求级状态存储

        :return: object 状态对象 (支持属性读写)
        """
        return self._request.state

    @property
    def app(self):
        """
        ASGI 应用实例

        :return: object 应用实例
        """
        return self._request.app

    @property
    def session(self) -> dict[str, Any]:
        """
        会话数据

        :return: dict[str, Any] 会话数据 (需要 SessionMiddleware)

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        return self._request.session

    @property
    def auth(self) -> Any:
        """
        认证信息

        :return: Any 认证数据 (需要 AuthenticationMiddleware)

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        return self._request.auth

    @property
    def user(self) -> Any:
        """
        用户信息

        :return: Any 用户数据 (需要 AuthenticationMiddleware)

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        return self._request.user

    @property
    def raw(self):
        """
        底层框架原生 Request 对象

        :return: object 原生请求实例 (当前为 fastapi.Request)
        """
        return self._request

    # ---- Methods ----

    async def body(self) -> bytes:
        """
        读取请求体原始字节

        :return: bytes 请求体内容
        """
        return await self._request.body()

    async def json(self) -> Any:
        """
        解析请求体为 JSON

        :return: Any 解析后的 JSON 数据
        """
        return await self._request.json()

    async def form(self, **kwargs):
        """
        解析表单数据

        :param max_files: int 最大文件数 (默认: 1000)
        :param max_fields: int 最大字段数 (默认: 1000)
        :return: object FormData 对象
        """
        return await self._request.form(**kwargs)

    async def stream(self):
        """
        流式读取请求体

        :return: async generator 逐块返回请求体字节
        """
        return self._request.stream()

    async def close(self) -> None:
        """
        关闭请求资源
        """
        await self._request.close()

    async def is_disconnected(self) -> bool:
        """
        检查客户端是否已断开连接

        :return: bool 是否已断开
        """
        return await self._request.is_disconnected()

    def url_for(self, name: str, /, **path_params: Any):
        """
        根据路由名反向生成 URL

        :param name: str 路由名称
        :param path_params: Any 路径参数
        :return: object URL 对象
        """
        return self._request.url_for(name, **path_params)

    # ---- Mapping protocol ----

    def __getitem__(self, key: str) -> Any:
        return self._request[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._request)

    def __len__(self) -> int:
        return len(self._request)


class WebSocketConnection(WebSocketConnectionBase):
    """
    服务端 WebSocket 连接抽象封装

    完全兼容 starlette.websockets.WebSocket 的接口风格。
    模块可使用此类替代 fastapi.WebSocket，无需直接依赖 FastAPI。

    额外提供 on_disconnect / on_error 生命周期钩子，
    抽象化断开连接和异常处理，便于未来切换后端。

    {!--< tips >!--}
    1. 通过 .raw 属性可访问底层框架原生 WebSocket 对象
    2. 使用 @ws.on_disconnect 和 @ws.on_error 注册生命周期回调
    3. 所有 send/receive 方法与 fastapi.WebSocket 完全一致
    {!--< /tips >!--}

    :example:
    >>> @sdk.router.ws("MyModule", "/ws/chat")
    ... async def chat(ws: WebSocketConnection):
    ...     @ws.on_disconnect
    ...     async def on_close(ws, reason="unknown"):
    ...         print(f"Disconnected: {reason}")
    ...     async for msg in ws.iter_text():
    ...         await ws.send_text(f"Echo: {msg}")
    """

    __slots__ = ()

    def __init__(self, websocket):
        """
        :param websocket: object 底层框架 WebSocket 对象 (fastapi.WebSocket)
        """
        super().__init__(websocket)

    # ---- Server-specific properties ----

    @property
    def base_url(self):
        """
        基础 URL

        :return: object URL 对象
        """
        return self._ws.base_url

    @property
    def query_params(self):
        """
        查询参数

        :return: object QueryParams 对象
        """
        return self._ws.query_params

    @property
    def path_params(self) -> dict[str, Any]:
        """
        路径参数

        :return: dict[str, Any] 路径参数字典
        """
        return self._ws.path_params

    @property
    def cookies(self) -> dict[str, str]:
        """
        Cookie 字典

        :return: dict[str, str] Cookie 键值对
        """
        return self._ws.cookies

    @property
    def client(self):
        """
        客户端地址

        :return: object | None 包含 .host 和 .port 属性的地址对象
        """
        return self._ws.client

    @property
    def state(self):
        """
        连接级状态存储

        :return: object 状态对象
        """
        return self._ws.state

    @property
    def app(self):
        """
        ASGI 应用实例

        :return: object 应用实例
        """
        return self._ws.app

    @property
    def session(self) -> dict[str, Any]:
        """
        会话数据

        :return: dict[str, Any] 会话数据
        """
        return self._ws.session

    @property
    def auth(self) -> Any:
        """
        认证信息

        :return: Any 认证数据
        """
        return self._ws.auth

    @property
    def user(self) -> Any:
        """
        用户信息

        :return: Any 用户数据
        """
        return self._ws.user

    # ---- Connection lifecycle ----

    async def accept(
        self,
        subprotocol: str | None = None,
        headers: Iterable[tuple[bytes, bytes]] | None = None,
    ) -> None:
        """
        接受 WebSocket 连接

        :param subprotocol: str | None 子协议 (可选)
        :param headers: Iterable[tuple[bytes, bytes]] | None 额外响应头 (可选)
        """
        await self._ws.accept(subprotocol=subprotocol, headers=headers)

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        """
        关闭 WebSocket 连接

        :param code: int 关闭码 (默认: 1000)
        :param reason: str | None 关闭原因 (可选)
        """
        await self._ws.close(code=code, reason=reason)

    # ---- Receive ----

    async def receive_text(self) -> str:
        """
        接收文本消息

        :return: str 文本内容
        """
        return await self._ws.receive_text()

    async def receive_bytes(self) -> bytes:
        """
        接收二进制消息

        :return: bytes 二进制内容
        """
        return await self._ws.receive_bytes()

    async def receive_json(self, mode: str = "text") -> Any:
        """
        接收 JSON 消息

        :param mode: str 接收模式 ("text" 或 "binary") (默认: "text")
        :return: Any 解析后的 JSON 数据
        """
        return await self._ws.receive_json(mode=mode)

    # ---- Send ----

    async def send_text(self, data: str) -> None:
        """
        发送文本消息

        :param data: str 文本内容
        """
        await self._ws.send_text(data)

    async def send_bytes(self, data: bytes) -> None:
        """
        发送二进制消息

        :param data: bytes 二进制内容
        """
        await self._ws.send_bytes(data)

    async def send_json(self, data: Any, mode: str = "text") -> None:
        """
        发送 JSON 消息

        :param data: Any 要序列化的数据
        :param mode: str 发送模式 ("text" 或 "binary") (默认: "text")
        """
        await self._ws.send_json(data, mode=mode)

    # ---- Low-level ----

    async def receive(self):
        """
        低级 ASGI receive

        :return: dict ASGI 消息

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        return await self._ws.receive()

    async def send(self, message) -> None:
        """
        低级 ASGI send

        :param message: dict ASGI 消息

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        await self._ws.send(message)

    # ---- Mapping protocol ----

    def __getitem__(self, key: str) -> Any:
        return self._ws[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._ws)

    def __len__(self) -> int:
        return len(self._ws)


class SseEmitter:
    """
    SSE (Server-Sent Events) 事件发送器 — 服务器无关的 SSE 协议实现

    封装 SSE 协议的格式化细节，通过回调函数与服务器层解耦。
    无论底层是 FastAPI、aiohttp 还是其他 HTTP 框架，只需提供
    ``on_send`` 和 ``on_close`` 回调即可使用。

    自动生成事件 ID，支持自定义事件类型和重试间隔。

    {!--< tips >!--}
    1. 由框架自动创建，模块开发者只需在 handler 中接收 sse 参数
    2. ``send()`` 方法自动处理 JSON 序列化（非 str 数据转为 JSON）
    3. 通过 ``request`` 属性可访问客户端请求（query params、headers 等）
    4. 调用 ``close()`` 优雅关闭连接
    {!--< /tips >!--}

    :example:
    >>> @sdk.router.sse("MyModule", "/events")
    ... async def event_stream(sse: SseEmitter):
    ...     while True:
    ...         await sse.send({"msg": "hello"}, event="update")
    ...         await asyncio.sleep(1)
    """

    __slots__ = ("_closed", "_id_counter", "_on_close", "_on_send", "_request")

    def __init__(self, on_send, on_close=None, request=None):
        """
        :param on_send: 回调函数，接收格式化后的 SSE 文本并发送到底层传输层
        :param on_close: 可选回调函数，连接关闭时调用
        :param request: 可选，底层 HTTP 请求对象
        """
        self._on_send = on_send
        self._on_close = on_close
        self._request = request
        self._closed = False
        self._id_counter = 1

    @property
    def request(self):
        """
        底层 HTTP 请求对象

        可用于读取查询参数、请求头等客户端信息。
        在 FastAPI 环境下为 ``fastapi.Request`` 实例。

        :return: object 底层 Request 对象或 None
        """
        return self._request

    @property
    def closed(self) -> bool:
        """
        连接是否已关闭

        :return: bool
        """
        return self._closed

    async def send(
        self,
        data=None,
        event: str | None = None,
        id: str | None = None,
        retry: int | None = None,
    ) -> None:
        """
        发送一个 SSE 事件

        根据 SSE 协议自动格式化输出：
        - ``event:`` 行（指定事件类型）
        - ``id:`` 行（事件 ID，自动生成递增 ID）
        - ``retry:`` 行（客户端重连间隔，毫秒）
        - ``data:`` 行（事件数据，多行自动拆分）
        - 末尾双换行结束一个事件

        :param data: 事件数据。非 str 类型自动 JSON 序列化。为 None 时仅发送事件类型
        :param event: 可选事件类型名
        :param id: 可选事件 ID，不传则自动生成
        :param retry: 可选重试间隔（毫秒）

        :raises RuntimeError: 连接已关闭时抛出

        :example:
        >>> await sse.send({"msg": "hello"})
        >>> await sse.send("plain text", event="notice")
        >>> await sse.send({"error": "boom"}, event="error", id="err-1")
        """
        import json as _json

        if self._closed:
            raise RuntimeError("SSE connection is closed")

        payload_parts = []

        if event is not None:
            payload_parts.append(f"event: {event}")

        eid = id if id is not None else str(self._id_counter)
        payload_parts.append(f"id: {eid}")
        self._id_counter += 1

        if retry is not None:
            payload_parts.append(f"retry: {retry}")

        if data is not None:
            if not isinstance(data, str):
                data = _json.dumps(data, ensure_ascii=False)
            payload_parts.extend(
                f"data: {line}"
                for line in data.replace("\r\n", "\n").replace("\r", "\n").split("\n")
            )

        payload_parts.append("")
        payload = "\n".join(payload_parts) + "\n"

        await self._on_send(payload)

    async def close(self) -> None:
        """
        关闭 SSE 连接

        安全方法，可多次调用。第一次调用时触发 ``on_close`` 回调。
        """
        if self._closed:
            return
        self._closed = True
        if self._on_close is not None:
            await self._on_close()


__all__ = [
    "HttpRequest",
    "SseEmitter",
    "WebSocketConnection",
]
