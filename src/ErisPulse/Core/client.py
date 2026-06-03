"""
ErisPulse HTTP 客户端

基于 aiohttp 的统一 HTTP 客户端实现，提供完整的请求/响应抽象。
模块和适配器应优先使用此客户端发送 HTTP 请求，而非自行导入 aiohttp。

{!--< tips >!--}
1. 使用 sdk.client 获取全局客户端单例
2. 支持 get / post / put / delete / patch / request 等常用方法
3. 自动记录请求日志和统计信息
4. 推荐所有模块和适配器使用此客户端发送 HTTP 请求
{!--< /tips >!--}
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from .logger import logger
from .lifecycle import lifecycle
from .constants import (
    DEFAULT_HTTP_CLIENT_TIMEOUT_SECS,
    DEFAULT_HTTP_CLIENT_CONNECT_TIMEOUT_SECS,
    DEFAULT_HTTP_CLIENT_MAX_RETRIES,
    DEFAULT_HTTP_CLIENT_RETRY_DELAY_SECS,
    DEFAULT_HTTP_CLIENT_USER_AGENT,
)


class HttpResponse:
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

    __slots__ = ("_response", "_body", "_body_read")

    def __init__(self, response):
        """
        :param response: object 底层框架 Response 对象
        """
        self._response = response
        self._body: bytes | None = None
        self._body_read = False

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

    async def text(self, encoding: str | None = None) -> str:
        """
        读取响应体为文本

        :param encoding: str | None 指定编码 (可选, 默认自动检测)
        :return: str 文本内容
        """
        if encoding:
            body = await self.read()
            return body.decode(encoding)
        return await self._response.text()

    async def json(self, **kwargs) -> Any:
        """
        解析响应体为 JSON

        :param kwargs: 传递给 json.loads 的额外参数
        :return: Any 解析后的数据
        """
        return await self._response.json(**kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self._response.release()


class HttpClient:
    """
    HTTP 客户端 (基于 aiohttp)

    提供统一的异步 HTTP 请求接口，自动管理连接池和会话生命周期。
    所有请求自动记录日志和统计信息。

    {!--< tips >!--}
    1. 通过 sdk.client 获取全局单例，也可自行实例化
    2. 使用 get/post/put/delete/patch 快捷方法或通用 request 方法
    3. 支持自定义 headers、timeout、retry 等参数
    4. 所有请求自动通过 lifecycle 发送事件，可用于监控
    {!--< /tips >!--}

    :example:
    >>> resp = await sdk.client.get("https://httpbin.org/get")
    >>> data = await resp.json()
    >>>
    >>> resp = await sdk.client.post(
    ...     "https://httpbin.org/post",
    ...     json={"key": "value"},
    ...     headers={"Authorization": "Bearer token"},
    ... )
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
        self._timeout = timeout if timeout is not None else DEFAULT_HTTP_CLIENT_TIMEOUT_SECS
        self._connect_timeout = connect_timeout if connect_timeout is not None else DEFAULT_HTTP_CLIENT_CONNECT_TIMEOUT_SECS
        self._max_retries = max_retries if max_retries is not None else DEFAULT_HTTP_CLIENT_MAX_RETRIES
        self._retry_delay = retry_delay if retry_delay is not None else DEFAULT_HTTP_CLIENT_RETRY_DELAY_SECS
        self._default_headers = dict(headers or {})
        if user_agent or DEFAULT_HTTP_CLIENT_USER_AGENT:
            self._default_headers.setdefault("User-Agent", user_agent or DEFAULT_HTTP_CLIENT_USER_AGENT)
        self._session = None
        self._stats = {
            "total_requests": 0,
            "total_errors": 0,
            "total_bytes_sent": 0,
            "total_bytes_received": 0,
        }

    # ---- Session 管理 ----

    async def _get_session(self):
        """
        获取或创建 aiohttp 会话

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
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
        """
        关闭客户端会话并释放资源
        """
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

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

        :raises: aiohttp 相关异常或连接错误

        :example:
        >>> resp = await client.request("GET", "https://httpbin.org/get", params={"q": "test"})
        """
        retries = max_retries if max_retries is not None else self._max_retries
        import aiohttp

        last_exc = None
        for attempt in range(retries + 1):
            start = time.monotonic()
            try:
                session = await self._get_session()

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
                    elapsed = time.monotonic() - start

                    self._stats["total_requests"] += 1
                    await lifecycle.emit("client.request", {
                        "method": method,
                        "url": str(url),
                        "status": resp.status,
                        "elapsed": round(elapsed, 3),
                    })

                    if resp.status >= 400:
                        logger.debug(
                            f"[HttpClient] {method} {url} -> {resp.status} ({elapsed:.3f}s)"
                        )
                    else:
                        logger.debug(
                            f"[HttpClient] {method} {url} -> {resp.status} ({elapsed:.3f}s)"
                        )

                    return response

            except Exception as e:
                last_exc = e
                self._stats["total_errors"] += 1
                elapsed = time.monotonic() - start
                if attempt < retries:
                    logger.debug(
                        f"[HttpClient] {method} {url} 失败 (尝试 {attempt + 1}/{retries + 1}): {e}"
                    )
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error(
                        f"[HttpClient] {method} {url} 最终失败 ({elapsed:.3f}s): {e}"
                    )

        raise last_exc

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
        return await self.request("POST", url, data=data, json=json, headers=headers, **kwargs)

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
        return await self.request("PUT", url, data=data, json=json, headers=headers, **kwargs)

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
        return await self.request("PATCH", url, data=data, json=json, headers=headers, **kwargs)

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
