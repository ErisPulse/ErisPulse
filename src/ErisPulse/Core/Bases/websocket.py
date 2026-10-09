"""
ErisPulse WebSocket 共享基类

定义客户端和服务端 WebSocket 连接的统一抽象接口。
send/receive/iter 方法签名在两端保持一致，具体实现由子类提供。

{!--< tips >!--}
1. 客户端和服务端 WebSocket 共享相同的 send/receive/iter 接口
2. iter_text/iter_bytes/iter_json 自动在断开时停止迭代
3. 通过 on_disconnect/on_error 注册生命周期回调
4. 连接池身份（id/namespace/owner/groups）由 _ConnectionIdentity 混入提供
{!--< /tips >!--}
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

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

    __slots__ = ("data", "type")

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


class _ConnectionIdentity:
    """
    连接池身份混入

    提供连接在 ``ErisPulse.connections`` 注册表中登记后的身份信息
    （id / namespace / owner / kind / meta / groups）与业务分组操作。
    分组的真相源在 ConnectionManager，本混入仅持有只读快照；
    ``close`` 的关闭权归创建者 owner，跨模块共享时仅允许发送与分组操作。

    {!--< internal-use >!--}
    WebSocketConnectionBase（服务端/客户端 WS）与 SseEmitter 共用
    {!--< /internal-use >!--}
    """

    __slots__ = (
        "_conn_groups",
        "_conn_id",
        "_conn_kind",
        "_conn_meta",
        "_conn_ns",
        "_conn_owner",
        "_conn_registry",
    )

    def __init__(
        self,
        *,
        connection_id: str = "",
        namespace: str = "",
        owner: str = "",
        kind: str = "",
    ):
        """
        :param connection_id: str 连接池分配的连接 id（未登记时为空串）
        :param namespace: str 服务端路由命名空间（客户端连接为空）
        :param owner: str 归属 owner（模块名 / 平台名），拥有关闭权
        :param kind: str 连接种类（"server" / "client" / "sse"）
        """
        self._conn_id = connection_id
        self._conn_ns = namespace
        self._conn_owner = owner
        self._conn_kind = kind
        self._conn_meta: dict[str, Any] = {}
        self._conn_groups: frozenset[str] = frozenset()
        self._conn_registry: Any = None  # 登记时的 ConnectionManager（join/leave 的路由目标）

    # ---- Identity（连接池登记信息）----

    @property
    def id(self) -> str:
        """
        连接 id

        连接池分配的全局唯一标识，形如 ``"{namespace}:{hex}"``；
        未登记的连接为空串。

        :return: str 连接 id
        """
        return self._conn_id

    @property
    def namespace(self) -> str:
        """
        服务端路由命名空间（即注册路由的模块名 / 平台名）

        :return: str 命名空间，客户端出站连接为空串
        """
        return self._conn_ns

    @property
    def owner(self) -> str:
        """
        连接归属 owner（模块名 / 平台名）

        owner 拥有关闭权；模块卸载时其名下连接由框架统一关闭。

        :return: str 归属标识
        """
        return self._conn_owner

    @property
    def kind(self) -> str:
        """
        连接种类

        :return: str "server"（服务端 WS）/ "client"（客户端出站 WS）/ "sse"（SSE 长连接）
        """
        return self._conn_kind

    @property
    def meta(self) -> dict[str, Any]:
        """
        业务元数据（自由字典）

        业务可在连接存活期内写入任意标注（如用户身份、租户号），
        连接断开时随连接一并丢弃。

        :return: dict 元数据字典（原对象，非拷贝）
        """
        return self._conn_meta

    @property
    def groups(self) -> frozenset[str]:
        """
        当前加入的业务分组

        :return: frozenset 分组名集合（只读快照）
        """
        return self._conn_groups

    def _set_conn_groups(self, groups: frozenset[str]) -> None:
        """
        {!--< internal-use >!--}
        由连接池维护的分组快照回写（分组真相源在 ConnectionManager）
        """
        self._conn_groups = groups

    def join_group(self, *groups: str) -> None:
        """
        加入业务分组

        分组命名完全由业务约定（房间 / 租户 / 主题……），框架不约束格式；
        连接断开时自动退出全部分组。等价于 ``connections.assign(self.id, *groups)``。

        :param groups: str 一个或多个分组名

        :example:
        >>> @router.ws("MyModule", "/ws")
        ... async def handle(ws: WebSocketConnection):
        ...     ws.join_group("room:1")
        """
        registry = self._conn_registry
        if registry is None:
            from ..connections import connections

            registry = connections
        registry.assign(self._conn_id, *groups)

    def leave_group(self, *groups: str) -> None:
        """
        离开业务分组

        :param groups: str 一个或多个分组名
        """
        registry = self._conn_registry
        if registry is None:
            from ..connections import connections

            registry = connections
        registry.dismiss(self._conn_id, *groups)

    def _check_close_permission(self) -> None:
        """
        {!--< internal-use >!--}
        关闭权校验：运行时上下文可归因且 ≠ 连接 owner 时拒绝。

        上下文为空（框架内部路径 / 未归因的老代码）一律放行，保证向后兼容。
        """
        if not self._conn_owner:
            return
        from ...runtime.context import current_caller, current_owner

        actor = current_owner.get() or current_caller.get()
        if actor and actor != self._conn_owner:
            from .errors import ConnectionPermissionError

            raise ConnectionPermissionError(self._conn_id, self._conn_owner)


class WebSocketConnectionBase(_ConnectionIdentity):
    """
    WebSocket 连接共享基类

    定义客户端和服务端 WebSocket 连接的统一接口。
    send/receive 由子类实现，iter 方法提供基于 receive 的默认实现。

    {!--< tips >!--}
    1. 通过 .raw 属性可访问底层框架原生对象
    2. 服务端和客户端共享此基类，接口一致
    3. 使用 on_disconnect/on_error 注册生命周期回调
    4. close 默认校验归属权限，框架内部路径用 close(force=True) 绕过
    {!--< /tips >!--}

    :example:
    >>> # 服务端和客户端共享相同的接口
    >>> await ws.send_text("Hello")
    >>> async for msg in ws.iter_text():
    ...     await ws.send_text(f"Echo: {msg}")
    """

    __slots__ = ("_on_disconnect_handlers", "_on_error_handlers", "_ws")

    def __init__(
        self,
        ws,
        *,
        connection_id: str = "",
        namespace: str = "",
        owner: str = "",
        kind: str = "",
    ):
        """
        :param ws: object 底层框架 WebSocket 对象
        :param connection_id: str 连接池分配的连接 id（未登记时为空串）
        :param namespace: str 服务端路由命名空间（客户端连接为空）
        :param owner: str 归属 owner（模块名 / 平台名），拥有关闭权
        :param kind: str 连接种类（"server" / "client"）
        """
        super().__init__(
            connection_id=connection_id,
            namespace=namespace,
            owner=owner,
            kind=kind,
        )
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

    # ---- Close ----

    async def close(self, code: int = 1000, reason: str | None = None, *, force: bool = False) -> None:
        """
        关闭 WebSocket 连接（默认校验归属权限）

        非 owner 模块关闭他人连接时抛出
        :class:`~ErisPulse.Core.Bases.errors.ConnectionPermissionError`；
        运行时上下文为空（框架内部路径 / 未归因代码）时放行。

        :param code: int 关闭码 (默认: 1000)
        :param reason: str | None 关闭原因 (可选)
        :param force: bool 跳过权限校验（框架内部回收路径使用）
        :raises ConnectionPermissionError: 跨 owner 关闭且未 force 时
        """
        if not force:
            self._check_close_permission()
        await self._close(code, reason)

    async def _close(self, code: int = 1000, reason: str | None = None) -> None:
        """
        实际关闭动作（子类实现，绕过权限层）

        :param code: int 关闭码
        :param reason: str | None 关闭原因
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


__all__ = [
    "WSMessage",
    "WebSocketConnectionBase",
]
