"""
ErisPulse HTTP/WS 客户端

基于 aiohttp 的统一 HTTP 和 WebSocket 客户端实现，提供完整的请求/响应/WS 抽象。
模块和适配器应优先使用此客户端发送 HTTP 请求和建立 WS 连接，而非自行导入 aiohttp。

底层 aiohttp 异常会在内部捕获并转换为 ErisPulse 异常体系，
确保业务代码不依赖任何特定 HTTP 库。

{!--< tips >!--}
1. 使用 sdk.client 获取全局客户端单例
2. 支持 get / post / put / delete / patch / request / ws_connect 等方法
3. aiohttp 异常自动转换为 ErisPulse 异常 (ClientError 体系)
4. 自动记录请求日志和统计信息
{!--< /tips >!--}
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from .Bases.client import BaseClientWebSocket, BaseHttpClient, BaseHttpResponse
from .Bases.errors import (
    ClientConnectionError,
    ClientError,
    ClientTimeoutError,
    WebSocketDisconnect,
    WebSocketError,
)
from .Bases.websocket import WSMessage
from .constants import (
    DEFAULT_HTTP_CLIENT_CONNECT_TIMEOUT_SECS,
    DEFAULT_HTTP_CLIENT_MAX_RETRIES,
    DEFAULT_HTTP_CLIENT_RETRY_DELAY_SECS,
    DEFAULT_HTTP_CLIENT_TIMEOUT_SECS,
    DEFAULT_HTTP_CLIENT_USER_AGENT,
)
from .i18n import i18n
from .lifecycle import lifecycle
from .logger import logger


def _convert_aiohttp_exception(exc: Exception) -> ClientError:
    import aiohttp

    if isinstance(exc, asyncio.TimeoutError):
        return ClientTimeoutError(str(exc))
    if isinstance(exc, aiohttp.ClientConnectorError):
        return ClientConnectionError(str(exc))
    if isinstance(exc, aiohttp.ClientConnectionError):
        return ClientConnectionError(str(exc))
    if isinstance(exc, aiohttp.ClientError):
        return ClientError(str(exc))
    return ClientError(str(exc))


class HttpResponse(BaseHttpResponse):
    """
    HTTP 响应封装

    提供与 aiohttp.ClientResponse 一致的访问接口。
    自动读取并缓存响应体，避免重复读取。

    {!--< tips >!--}
    通过 .raw 属性可访问底层原生响应对象
    {!--< /tips >!--}

    :example:
    >>> resp = await sdk.client.get("https://httpbin.org/get")
    >>> print(resp.status)
    >>> data = await resp.json()
    """

    __slots__ = ("_response", "_body", "_body_read", "_released")

    def __init__(self, response):
        """
        :param response: object 底层框架 Response 对象
        """
        self._response = response
        self._body: bytes | None = None
        self._body_read = False
        self._released = False

    @property
    def status(self) -> int:
        """
        HTTP 状态码

        :return: int 状态码 (如 200, 404)
        """
        return self._response.status

    @property
    def reason(self) -> str | None:
        """
        状态描述

        :return: str | None 状态原因短语
        """
        return self._response.reason

    @property
    def headers(self):
        """
        响应头

        :return: object 大小写不敏感的响应头映射
        """
        return self._response.headers

    @property
    def content_type(self) -> str | None:
        """
        Content-Type 值

        :return: str | None 内容类型
        """
        return self._response.content_type

    @property
    def charset(self) -> str | None:
        """
        字符编码

        :return: str | None 编码名称
        """
        return self._response.charset

    @property
    def url(self):
        """
        响应 URL (可能因重定向而与请求 URL 不同)

        :return: object URL 对象
        """
        return self._response.url

    @property
    def raw(self):
        """
        底层框架原生 Response 对象

        :return: object 原生响应实例 (当前为 aiohttp.ClientResponse)
        """
        return self._response

    async def read(self) -> bytes:
        """
        读取响应体原始字节 (自动缓存)

        :return: bytes 响应体内容
        """
        if not self._body_read:
            self._body = await self._response.read()
            self._body_read = True
        return self._body

    async def _eager_read(self):
        if not self._body_read:
            self._body = await self._response.read()
            self._body_read = True

    async def text(self, encoding: str | None = None) -> str:
        if encoding:
            body = await self.read()
            return body.decode(encoding)
        body = await self.read()
        return body.decode(self._response.get_encoding() or "utf-8")

    async def json(self, **kwargs) -> Any:
        import json as _json

        body = await self.read()
        return _json.loads(body, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        if not self._released:
            self._response.release()
            self._released = True


class ClientWebSocket(BaseClientWebSocket):
    """
    客户端 WebSocket 连接 (基于 aiohttp)

    封装 aiohttp.ClientWebSocketResponse，提供统一的 WebSocket 客户端接口。
    通过 sdk.client.ws_connect() 获取实例。

    {!--< tips >!--}
    1. 使用 iter_text/iter_bytes/iter_json 自动过滤消息类型
    2. 使用 receive/iter_messages 处理原始消息类型 (如 CLOSE/ERROR)
    3. 通过 .raw 属性可访问底层 aiohttp.ClientWebSocketResponse
    {!--< /tips >!--}

    :example:
    >>> ws = await sdk.client.ws_connect("wss://example.com/ws")
    >>> async for text in ws.iter_text():
    ...     await ws.send_text(f"Echo: {text}")
    """

    __slots__ = ("_recv_lock",)

    def __init__(self, ws):
        """
        :param ws: aiohttp.ClientWebSocketResponse 底层 aiohttp WS 对象
        """
        super().__init__(ws)
        self._recv_lock = asyncio.Lock()

    @property
    def closed(self) -> bool:
        """
        连接是否已关闭

        :return: bool 是否已关闭
        """
        return self._ws.closed

    # ---- Send ----

    async def send_text(self, data: str) -> None:
        """
        发送文本消息

        :param data: str 文本内容
        """
        if self._ws.closed:
            raise WebSocketError("WebSocket is closed")
        await self._ws.send_str(data)

    async def send_bytes(self, data: bytes) -> None:
        """
        发送二进制消息

        :param data: bytes 二进制内容
        """
        if self._ws.closed:
            raise WebSocketError("WebSocket is closed")
        await self._ws.send_bytes(data)

    async def send_json(self, data: Any, mode: str = "text") -> None:
        """
        发送 JSON 消息

        :param data: Any 要序列化的数据
        :param mode: str 发送模式 ("text" 或 "binary") (默认: "text")
        """
        if self._ws.closed:
            raise WebSocketError("WebSocket is closed")
        if mode == "binary":
            payload = json.dumps(data).encode("utf-8")
            await self._ws.send_bytes(payload)
        else:
            await self._ws.send_json(data)

    # ---- Receive ----

    def _convert_ws_msg(self, msg) -> WSMessage:
        """
        转换 aiohttp WSMessage 为 ErisPulse WSMessage

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        import aiohttp

        if msg.type == aiohttp.WSMsgType.TEXT:
            return WSMessage(WSMessage.TEXT, msg.data)
        elif msg.type == aiohttp.WSMsgType.BINARY:
            return WSMessage(WSMessage.BINARY, msg.data)
        elif msg.type in (
            aiohttp.WSMsgType.CLOSE,
            aiohttp.WSMsgType.CLOSING,
            aiohttp.WSMsgType.CLOSED,
        ):
            return WSMessage(WSMessage.CLOSE, msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            return WSMessage(WSMessage.ERROR, str(self._ws.exception()))
        else:
            return WSMessage("unknown", msg.data)

    async def receive(self) -> WSMessage:
        """
        接收原始消息

        :return: WSMessage 消息对象
        """
        async with self._recv_lock:
            msg = await self._ws.receive()
        return self._convert_ws_msg(msg)

    async def receive_text(self) -> str:
        """
        接收文本消息

        :return: str 文本内容
        :raises WebSocketDisconnect: 连接断开时
        :raises WebSocketError: 收到非文本消息时
        """
        import aiohttp

        async with self._recv_lock:
            msg = await self._ws.receive()
        if msg.type == aiohttp.WSMsgType.TEXT:
            return msg.data
        elif msg.type in (
            aiohttp.WSMsgType.CLOSE,
            aiohttp.WSMsgType.CLOSING,
            aiohttp.WSMsgType.CLOSED,
        ):
            code = msg.data if isinstance(msg.data, int) else 1000
            raise WebSocketDisconnect(code=code)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            raise WebSocketError(str(self._ws.exception()))
        else:
            raise WebSocketError(f"Unexpected message type: {msg.type}")

    async def receive_bytes(self) -> bytes:
        """
        接收二进制消息

        :return: bytes 二进制内容
        :raises WebSocketDisconnect: 连接断开时
        :raises WebSocketError: 收到非二进制消息时
        """
        import aiohttp

        async with self._recv_lock:
            msg = await self._ws.receive()
        if msg.type == aiohttp.WSMsgType.BINARY:
            return msg.data
        elif msg.type in (
            aiohttp.WSMsgType.CLOSE,
            aiohttp.WSMsgType.CLOSING,
            aiohttp.WSMsgType.CLOSED,
        ):
            code = msg.data if isinstance(msg.data, int) else 1000
            raise WebSocketDisconnect(code=code)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            raise WebSocketError(str(self._ws.exception()))
        else:
            raise WebSocketError(f"Unexpected message type: {msg.type}")

    async def receive_json(self, mode: str = "text") -> Any:
        """
        接收 JSON 消息

        :param mode: str 接收模式 ("text" 或 "binary") (默认: "text")
        :return: Any 解析后的 JSON 数据
        :raises WebSocketDisconnect: 连接断开时
        """
        if mode == "binary":
            data = await self.receive_bytes()
            return json.loads(data)
        text = await self.receive_text()
        return json.loads(text)

    # ---- Close ----

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        """
        关闭 WebSocket 连接

        :param code: int 关闭码 (默认: 1000)
        :param reason: str | None 关闭原因 (可选)
        """
        await self._ws.close(code=code, message=reason)
        self._closed = True


class HttpClient(BaseHttpClient):
    """
    HTTP/WS 客户端 (基于 aiohttp)

    提供统一的异步 HTTP 请求和 WebSocket 连接接口。
    自动管理连接池和会话生命周期，底层 aiohttp 异常自动转换为 ErisPulse 异常。

    {!--< tips >!--}
    1. 通过 sdk.client 获取全局单例，也可自行实例化
    2. 使用 get/post/put/delete/patch 快捷方法或通用 request 方法
    3. 使用 ws_connect 建立 WebSocket 连接
    4. 支持 ErisPulse 异常体系，业务代码不依赖 aiohttp
    5. 所有请求自动通过 lifecycle 发送事件，可用于监控
    {!--< /tips >!--}

    :example:
    >>> resp = await sdk.client.get("https://httpbin.org/get")
    >>> data = await resp.json()
    >>>
    >>> ws = await sdk.client.ws_connect("wss://example.com/ws")
    >>> await ws.send_text("Hello")
    """

    def __init__(
        self,
        *,
        timeout: float | None = None,
        connect_timeout: float | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        headers: dict[str, str] | None = None,
        user_agent: str | None = None,
    ):
        """
        :param timeout: float | None 请求总超时 (秒) (默认: 30)
        :param connect_timeout: float | None 连接超时 (秒) (默认: 10)
        :param max_retries: int 最大重试次数 (默认: 0)
        :param retry_delay: float 重试间隔 (秒) (默认: 1)
        :param headers: dict[str, str] 全局默认请求头 (可选)
        :param user_agent: str User-Agent 字符串 (可选)
        """
        self._timeout = (
            timeout if timeout is not None else DEFAULT_HTTP_CLIENT_TIMEOUT_SECS
        )
        self._connect_timeout = (
            connect_timeout
            if connect_timeout is not None
            else DEFAULT_HTTP_CLIENT_CONNECT_TIMEOUT_SECS
        )
        self._max_retries = (
            max_retries if max_retries is not None else DEFAULT_HTTP_CLIENT_MAX_RETRIES
        )
        self._retry_delay = (
            retry_delay
            if retry_delay is not None
            else DEFAULT_HTTP_CLIENT_RETRY_DELAY_SECS
        )
        self._default_headers = dict(headers or {})
        if user_agent or DEFAULT_HTTP_CLIENT_USER_AGENT:
            self._default_headers.setdefault(
                "User-Agent", user_agent or DEFAULT_HTTP_CLIENT_USER_AGENT
            )
        self._session = None
        self._ws_session = None
        self._session_lock = asyncio.Lock()
        self._stats = {
            "total_requests": 0,
            "total_errors": 0,
            "total_bytes_sent": 0,
            "total_bytes_received": 0,
        }

    # ---- Session 管理 ----

    async def _get_ws_session(self):
        async with self._session_lock:
            if self._ws_session is None or self._ws_session.closed:
                import aiohttp

                self._ws_session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(),
                    headers=self._default_headers or None,
                )
            return self._ws_session

    async def _drain_sessions(self):
        async with self._session_lock:
            old_session = self._session
            old_ws = self._ws_session
            self._session = None
            self._ws_session = None
        if old_session and not old_session.closed:
            try:
                await old_session.close()
            except Exception:
                pass
        if old_ws and not old_ws.closed:
            try:
                await old_ws.close()
            except Exception:
                pass

    async def _get_http_session(self):
        async with self._session_lock:
            if self._session is None or self._session.closed:
                import aiohttp

                timeout = aiohttp.ClientTimeout(
                    total=self._timeout,
                    connect=self._connect_timeout,
                )
                self._session = aiohttp.ClientSession(
                    timeout=timeout,
                    headers=self._default_headers,
                )
            return self._session

    async def close(self) -> None:
        async with self._session_lock:
            old_session = self._session
            old_ws = self._ws_session
            self._session = None
            self._ws_session = None
        if old_session and not old_session.closed:
            await old_session.close()
        if old_ws and not old_ws.closed:
            await old_ws.close()

    # ---- 核心请求方法 ----

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        data: Any = None,
        json: Any = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        **kwargs,
    ) -> HttpResponse:
        """
        发送 HTTP 请求

        :param method: str HTTP 方法 (GET, POST, PUT, DELETE, PATCH 等)
        :param url: str 请求 URL
        :param params: dict[str, str] | None 查询参数 (可选)
        :param headers: dict[str, str] | None 额外请求头 (可选)
        :param data: Any 请求体 (表单或原始数据) (可选)
        :param json: Any JSON 请求体 (可选)
        :param timeout: float | None 本次请求超时 (秒) (可选, 覆盖默认值)
        :param max_retries: int | None 本次最大重试次数 (可选, 覆盖默认值)
        :param kwargs: 传递给底层请求的额外参数
        :return: HttpResponse 响应对象

        :raises ClientConnectionError: 连接失败
        :raises ClientTimeoutError: 请求超时
        :raises ClientError: 其他客户端错误

        :example:
        >>> resp = await client.request("GET", "https://httpbin.org/get", params={"q": "test"})
        """
        import aiohttp

        retries = max_retries if max_retries is not None else self._max_retries

        last_exc: ClientError | None = None
        for attempt in range(retries + 1):
            start = time.monotonic()
            try:
                session = await self._get_http_session()

                request_timeout = None
                if timeout is not None:
                    request_timeout = aiohttp.ClientTimeout(
                        total=timeout,
                        connect=self._connect_timeout,
                    )

                async with session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    data=data,
                    json=json,
                    timeout=request_timeout,
                    **kwargs,
                ) as resp:
                    response = HttpResponse(resp)
                    await response._eager_read()
                    response._released = True
                    elapsed = time.monotonic() - start

                    self._stats["total_requests"] += 1
                    await lifecycle.emit(
                        "client.request.success",
                        {
                            "method": method,
                            "url": str(url),
                            "status": resp.status,
                            "elapsed": elapsed,
                        },
                    )

                    return response

            except asyncio.TimeoutError as e:
                last_exc = _convert_aiohttp_exception(e)
                self._stats["total_errors"] += 1
                elapsed = time.monotonic() - start
                if attempt < retries:
                    logger.debug(
                        i18n.t(
                            "core.client.timeout_retry",
                            method=method,
                            url=url,
                            attempt=attempt + 1,
                            total=retries + 1,
                        )
                    )
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error(
                        i18n.t(
                            "core.client.timeout_final",
                            method=method,
                            url=url,
                            elapsed=f"{elapsed:.3f}",
                        )
                    )
            except aiohttp.ClientConnectionError as e:
                last_exc = _convert_aiohttp_exception(e)
                self._stats["total_errors"] += 1
                elapsed = time.monotonic() - start
                if attempt < retries:
                    logger.debug(
                        i18n.t(
                            "core.client.conn_broken_retry",
                            method=method,
                            url=url,
                            attempt=attempt + 1,
                            total=retries + 1,
                        )
                    )
                    await self._drain_sessions()
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error(
                        i18n.t(
                            "core.client.conn_final_failed",
                            method=method,
                            url=url,
                            elapsed=f"{elapsed:.3f}",
                        )
                    )
            except aiohttp.ClientError as e:
                last_exc = _convert_aiohttp_exception(e)
                self._stats["total_errors"] += 1
                elapsed = time.monotonic() - start
                if attempt < retries:
                    logger.debug(
                        i18n.t(
                            "core.client.request_failed_retry",
                            method=method,
                            url=url,
                            attempt=attempt + 1,
                            total=retries + 1,
                            error=e,
                        )
                    )
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error(
                        i18n.t(
                            "core.client.request_final_failed",
                            method=method,
                            url=url,
                            elapsed=f"{elapsed:.3f}",
                            error=e,
                        )
                    )
            except ClientError:
                raise
            except Exception as e:
                last_exc = ClientError(str(e))
                self._stats["total_errors"] += 1
                elapsed = time.monotonic() - start
                if attempt < retries:
                    logger.debug(
                        i18n.t(
                            "core.client.request_failed_retry",
                            method=method,
                            url=url,
                            attempt=attempt + 1,
                            total=retries + 1,
                            error=e,
                        )
                    )
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error(
                        i18n.t(
                            "core.client.request_final_failed",
                            method=method,
                            url=url,
                            elapsed=f"{elapsed:.3f}",
                            error=e,
                        )
                    )

        raise last_exc

    # ---- WebSocket 连接 ----

    async def ws_connect(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        heartbeat: float | None = None,
        **kwargs,
    ) -> ClientWebSocket:
        """
        建立 WebSocket 连接

        :param url: str WebSocket 服务器 URL
        :param headers: dict[str, str] | None 额外请求头 (可选)
        :param heartbeat: float | None 心跳间隔秒数 (可选)
        :param kwargs: 传递给底层 ws_connect 的额外参数
        :return: ClientWebSocket WebSocket 连接对象

        :raises ClientConnectionError: 连接失败
        :raises ClientError: 其他客户端错误

        :example:
        >>> ws = await sdk.client.ws_connect("wss://example.com/ws", heartbeat=30)
        >>> async for text in ws.iter_text():
        ...     await ws.send_text(f"Echo: {text}")
        """
        import aiohttp

        try:
            session = await self._get_ws_session()
            ws = await session.ws_connect(
                url,
                headers=headers,
                heartbeat=heartbeat,
                **kwargs,
            )

            await lifecycle.emit(
                "client.ws.connect",
                {
                    "url": str(url),
                },
            )

            logger.debug(i18n.t("core.client.ws_connect", url=url))
            return ClientWebSocket(ws)

        except ClientError:
            raise
        except Exception as e:
            if isinstance(e, aiohttp.ClientError):
                raise _convert_aiohttp_exception(e) from e
            raise ClientError(str(e)) from e

    # ---- 快捷方法 ----

    async def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> HttpResponse:
        """
        发送 GET 请求

        :param url: str 请求 URL
        :param params: dict[str, str] | None 查询参数 (可选)
        :param headers: dict[str, str] | None 额外请求头 (可选)
        :return: HttpResponse 响应对象

        :example:
        >>> resp = await client.get("https://httpbin.org/get", params={"q": "test"})
        >>> data = await resp.json()
        """
        return await self.request("GET", url, params=params, headers=headers, **kwargs)

    async def post(
        self,
        url: str,
        *,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> HttpResponse:
        """
        发送 POST 请求

        :param url: str 请求 URL
        :param data: Any 请求体 (表单或原始数据) (可选)
        :param json: Any JSON 请求体 (可选)
        :param headers: dict[str, str] | None 额外请求头 (可选)
        :return: HttpResponse 响应对象

        :example:
        >>> resp = await client.post("https://httpbin.org/post", json={"key": "value"})
        """
        return await self.request(
            "POST", url, data=data, json=json, headers=headers, **kwargs
        )

    async def put(
        self,
        url: str,
        *,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> HttpResponse:
        """
        发送 PUT 请求

        :param url: str 请求 URL
        :param data: Any 请求体 (可选)
        :param json: Any JSON 请求体 (可选)
        :param headers: dict[str, str] | None 额外请求头 (可选)
        :return: HttpResponse 响应对象
        """
        return await self.request(
            "PUT", url, data=data, json=json, headers=headers, **kwargs
        )

    async def delete(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> HttpResponse:
        """
        发送 DELETE 请求

        :param url: str 请求 URL
        :param headers: dict[str, str] | None 额外请求头 (可选)
        :return: HttpResponse 响应对象
        """
        return await self.request("DELETE", url, headers=headers, **kwargs)

    async def patch(
        self,
        url: str,
        *,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> HttpResponse:
        """
        发送 PATCH 请求

        :param url: str 请求 URL
        :param data: Any 请求体 (可选)
        :param json: Any JSON 请求体 (可选)
        :param headers: dict[str, str] | None 额外请求头 (可选)
        :return: HttpResponse 响应对象
        """
        return await self.request(
            "PATCH", url, data=data, json=json, headers=headers, **kwargs
        )

    # ---- 统计 ----

    @property
    def stats(self) -> dict[str, int]:
        """
        请求统计

        :return: dict[str, int] 统计数据 (total_requests, total_errors 等)
        """
        return dict(self._stats)

    def reset_stats(self) -> None:
        """
        重置统计数据
        """
        self._stats = {
            "total_requests": 0,
            "total_errors": 0,
            "total_bytes_sent": 0,
            "total_bytes_received": 0,
        }

    # ---- 上下文管理 ----

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
