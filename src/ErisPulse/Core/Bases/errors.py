"""
ErisPulse 异常体系

定义框架统一的异常层级，使模块和适配器无需直接依赖底层库的异常类型。
底层实现（如 aiohttp）的异常会在内部捕获并转换为对应的 ErisPulse 异常。

{!--< tips >!--}
1. 使用 ClientError 统一捕获所有 HTTP/WS 客户端请求异常
2. WebSocket 断开使用 WebSocketDisconnect，服务端和客户端通用
3. 底层库异常（aiohttp.ClientError 等）不会泄露到业务代码
{!--< /tips >!--}
"""

from __future__ import annotations


class ErisPulseError(Exception):
    """
    ErisPulse 基础异常

    所有 ErisPulse 自定义异常的基类。
    """



class ClientError(ErisPulseError):
    """
    客户端异常基类

    所有 HTTP/WS 客户端请求相关的异常基类。
    可用于统一捕获所有客户端错误。

    :example:
    >>> from ErisPulse.Core.Bases.errors import ClientError
    >>> try:
    ...     resp = await sdk.client.get("https://example.com")
    ... except ClientError as e:
    ...     print(f"请求失败: {e}")
    """




class ClientConnectionError(ClientError):
    """
    客户端连接异常

    DNS 解析失败、连接被拒绝、网络不可达等连接层错误。

    :example:
    >>> try:
    ...     resp = await sdk.client.get("https://unreachable.example.com")
    ... except ClientConnectionError:
    ...     print("无法连接到服务器")
    """



class ClientTimeoutError(ClientError):
    """
    客户端超时异常

    连接超时或请求超时。

    :example:
    >>> try:
    ...     resp = await sdk.client.get("https://slow.example.com", timeout=5)
    ... except ClientTimeoutError:
    ...     print("请求超时")
    """



class HTTPStatusError(ClientError):
    """
    HTTP 状态码异常

    服务器返回了错误的状态码 (4xx/5xx)。

    :param status: int HTTP 状态码
    :param message: str 错误消息

    :example:
    >>> try:
    ...     resp = await sdk.client.get("https://example.com/404")
    ... except HTTPStatusError as e:
    ...     print(f"状态码: {e.status}")
    """

    def __init__(self, status: int, message: str = ""):
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}" if message else f"HTTP {status}")


class WebSocketError(ErisPulseError):
    """
    WebSocket 异常基类

    WebSocket 连接、通信相关的异常。
    """


class StorageError(ErisPulseError):
    """
    存储异常基类

    所有存储后端相关的异常基类。
    """


class StorageUnreachableError(StorageError):
    """
    存储后端不可达

    后端连接池创建在自动重试耗尽后仍失败（数据库不可达 / 凭据错误 /
    网络隔离等）。框架保持运行，存储操作在冷却期内快速失败并自动重连。
    """


class InteractionError(ErisPulseError):
    """
    交互会话异常基类

    交互会话管理（等待回复 / 会话租约）相关的异常基类。
    可用于统一捕获所有交互会话错误。
    """



class ModuleError(ErisPulseError):
    """
    模块系统异常基类

    模块加载、调用与通信相关的异常基类。
    """



class ModuleCallError(ModuleError):
    """
    模块间调用异常基类

    ``module.call()`` 跨模块调用相关的异常基类，
    可用于统一捕获所有模块间调用错误。

    :attribute module: 目标模块名
    :attribute method: 目标方法名
    """

    def __init__(self, module: str = "", method: str = "", message: str = ""):
        self.module = module
        self.method = method
        super().__init__(message or f"{module}.{method}")


class ModuleNotAvailableError(ModuleCallError):
    """
    目标模块不可用

    调用的模块未注册 / 未启用 / 懒加载唤醒失败时抛出。
    """


class ServiceNotProvidedError(ModuleCallError):
    """
    服务未提供

    目标模块通过 ``provides`` 声明了服务白名单，
    调用了不在白名单中的方法（或试图调用私有方法）时抛出。
    """


class ModuleCallTimeoutError(ModuleCallError):
    """
    模块间调用超时

    目标方法在超时时限内未返回时抛出。
    """



class WebSocketDisconnect(WebSocketError):
    """
    WebSocket 断开连接异常

    与 starlette.websockets.WebSocketDisconnect 完全兼容。
    客户端和服务端 WebSocket 均可使用此异常表示连接断开。

    :param code: int 关闭码 (默认: 1000)
    :param reason: str | None 关闭原因 (可选)

    :example:
    >>> from ErisPulse.Core.Bases.errors import WebSocketDisconnect
    >>> try:
    ...     msg = await ws.receive_text()
    ... except WebSocketDisconnect as e:
    ...     print(f"断开: code={e.code}, reason={e.reason}")
    """

    def __init__(self, code: int = 1000, reason: str | None = None):
        self.code = code
        self.reason = reason or ""
        super().__init__(f"code={self.code}, reason={self.reason}")


__all__ = [
    "ClientConnectionError",
    "ClientError",
    "ClientTimeoutError",
    "ErisPulseError",
    "HTTPStatusError",
    "InteractionError",
    "ModuleCallError",
    "ModuleCallTimeoutError",
    "ModuleError",
    "ModuleNotAvailableError",
    "ServiceNotProvidedError",
    "WebSocketDisconnect",
    "WebSocketError",
]
