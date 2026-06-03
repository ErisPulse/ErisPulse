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

from typing import Any, Iterator, Iterable
from collections.abc import Callable


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


class WebSocketConnection:
    """
    WebSocket 连接抽象封装

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

    __slots__ = ("_ws", "_on_disconnect_handlers", "_on_error_handlers")

    def __init__(self, websocket):
        """
        :param websocket: object 底层框架 WebSocket 对象
        """
        self._ws = websocket
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
    def base_url(self):
        """
        基础 URL

        :return: object URL 对象
        """
        return self._ws.base_url

    @property
    def headers(self):
        """
        请求头

        :return: object Headers 对象
        """
        return self._ws.headers

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

    @property
    def raw(self):
        """
        底层框架原生 WebSocket 对象

        :return: object 原生 WebSocket 实例 (当前为 fastapi.WebSocket)
        """
        return self._ws

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

    async def iter_text(self):
        """
        迭代文本消息直到断开

        :return: async generator 逐条返回文本消息
        """
        async for msg in self._ws.iter_text():
            yield msg

    async def iter_bytes(self):
        """
        迭代二进制消息直到断开

        :return: async generator 逐条返回二进制消息
        """
        async for msg in self._ws.iter_bytes():
            yield msg

    async def iter_json(self):
        """
        迭代 JSON 消息直到断开

        :return: async generator 逐条返回 JSON 数据
        """
        async for msg in self._ws.iter_json():
            yield msg

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


class WebSocketDisconnect(Exception):
    """
    WebSocket 断开连接异常

    与 starlette.websockets.WebSocketDisconnect 完全兼容。
    模块可使用此类替代 fastapi.WebSocketDisconnect，无需直接依赖 FastAPI。

    :example:
    >>> from ErisPulse.Core.Bases.router import WebSocketDisconnect
    >>> try:
    ...     msg = await ws.receive_text()
    ... except WebSocketDisconnect as e:
    ...     print(f"Disconnected: code={e.code}")
    """

    def __init__(self, code: int = 1000, reason: str | None = None):
        """
        :param code: int 关闭码 (默认: 1000)
        :param reason: str | None 关闭原因 (可选)
        """
        self.code = code
        self.reason = reason or ""
        super().__init__(f"code={self.code}, reason={self.reason}")
