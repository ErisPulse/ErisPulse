"""
ErisPulse 连接注册表（连接池）

把"连接"从模块私有物升级为框架级一等资源：服务端 WS/SSE 连接随路由
自动登记（namespace 维度），客户端出站 WS 连接随 ``client.ws_connect``
自动登记（owner 维度）。支持广播（按命名空间 / 分组 / id 过滤的集合推送）、
业务分组订阅（房间 / 租户 / 主题，命名完全由业务约定）与跨模块连接传递
（共享同一连接对象，关闭权归创建者 owner）。

{!--< tips >!--}
1. 服务端 ``@router.ws(...)`` handler 拿到的连接已自动登记，``ws.id`` 可查
2. ``connections.list(namespace=...)`` 查看某模块的连接池；``stats()`` 看全局
3. ``connections.broadcast(data, group=...)`` 向分组广播并返回成败明细
4. 跨模块 ``connections.get(id)`` 拿连接后可发送 / 分组，但 ``close`` 仅 owner 可调
5. 模块卸载时框架自动关闭并注销其名下全部连接（server/client/sse）
6. 从子线程调用本模块异步 API 请经 ``ErisPulse.run_main_loop`` 投递
{!--< /tips >!--}

:example:
>>> # handler 内加入分组；任意位置向分组广播
>>> @router.ws("MyModule", "/ws")
... async def handle(ws: WebSocketConnection):
...     ws.join_group("room:1")
...     async for msg in ws.iter_text():
...         await connections.broadcast({"echo": msg}, group="room:1")
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from ..runtime.context import current_caller, current_owner
from .Bases.errors import ConnectionNotFoundError
from .constants import (
    CONNECTION_ID_HEX_CHARS,
    DEFAULT_BROADCAST_CONCURRENCY,
    DEFAULT_BROADCAST_TIMEOUT_SECS,
    DEFAULT_CONNECTION_CLOSE_TIMEOUT_SECS,
    EVENT_CONNECTION_GROUP_JOINED,
    EVENT_CONNECTION_GROUP_LEFT,
    EVENT_CONNECTION_REGISTERED,
    EVENT_CONNECTION_UNREGISTERED,
)
from .lifecycle import lifecycle


@dataclass
class BroadcastResult:
    """
    广播结果

    :attribute total: 目标连接总数（排除前，含 id 指定但已不存在的连接）
    :attribute sent: 发送成功的连接 id 列表
    :attribute failed: 发送失败的 {连接 id: 异常对象}（含超时与已断开）
    :attribute excluded: 被 ``exclude`` 参数排除的连接 id 列表
    """

    total: int
    sent: list[str] = field(default_factory=list)
    failed: dict[str, BaseException] = field(default_factory=dict)
    excluded: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """
        是否全部送达

        :return: bool 无失败项时为 True
        """
        return not self.failed


class ConnectionManager:
    """
    连接注册表管理器

    维护框架级连接集合（服务端 WS / SSE / 客户端出站 WS）与业务分组索引。
    连接的登记 / 注销由框架在路由与客户端连接生命周期处自动完成；
    业务侧主要使用查询（``list`` / ``stats`` / ``get``）、分组
    （``assign`` / ``dismiss``）与广播（``broadcast``）。

    {!--< tips >!--}
    1. 归属与关闭权：连接 owner 拥有关闭权，其他模块仅可发送与分组
    2. 分组命名完全由业务约定，连接断开时自动退出全部分组
    3. 广播永不改变连接归属；跨模块点对点操作请用 ``get``
    {!--< /tips >!--}

    :example:
    >>> conns = connections.list(namespace="Dashboard")
    >>> result = await connections.broadcast({"type": "notify"}, namespace="Dashboard")
    >>> result.ok
    True
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # 连接 id -> 连接对象（WebSocketConnection / ClientWebSocket / SseEmitter，鸭子类型）
        self._by_id: dict[str, Any] = {}
        # 服务端命名空间（模块名/平台名）-> 连接 id 集合
        self._by_namespace: dict[str, set[str]] = {}
        # 归属 owner -> 连接 id 集合（客户端连接的主索引；服务端连接 owner==namespace）
        self._by_owner: dict[str, set[str]] = {}
        # 业务分组名 -> 连接 id 集合
        self._by_group: dict[str, set[str]] = {}

    # ---- 登记 / 注销（框架自动调用，业务一般无需直接使用）----

    def register(
        self,
        conn: Any,
        *,
        namespace: str = "",
        owner: str | None = None,
        kind: str = "",
        meta: dict[str, Any] | None = None,
    ) -> str:
        """
        登记连接并分配连接 id

        {!--< internal-use >!--}
        由 router（服务端 WS/SSE）与 client（出站 WS）在连接建立时自动调用；
        owner 缺省时从运行时上下文捕获（current_owner > current_caller）。
        {!--< /internal-use >!--}

        :param conn: 连接对象（需具备 id/owner/kind 等身份混入字段）
        :param namespace: str 服务端路由命名空间（客户端连接留空）
        :param owner: str 归属 owner（模块名 / 平台名），缺省时取当前上下文
        :param kind: str 连接种类（"server" / "client" / "sse"），缺省时读 conn.kind
        :param meta: dict | None 初始业务元数据
        :return: str 分配的连接 id
        """
        if not owner:
            owner = current_owner.get() or current_caller.get() or ""
        if not kind:
            kind = getattr(conn, "kind", "") or "server"
        conn._conn_owner = owner
        conn._conn_ns = namespace
        conn._conn_kind = kind
        conn._conn_registry = self  # join_group/leave_group 路由回本注册表
        if meta:
            conn._conn_meta.update(meta)

        prefix = namespace or owner or kind or "conn"
        conn._conn_id = f"{prefix}:{uuid.uuid4().hex[:CONNECTION_ID_HEX_CHARS]}"

        with self._lock:
            self._by_id[conn._conn_id] = conn
            if namespace:
                self._by_namespace.setdefault(namespace, set()).add(conn._conn_id)
            if owner:
                self._by_owner.setdefault(owner, set()).add(conn._conn_id)

        lifecycle.fire(
            EVENT_CONNECTION_REGISTERED,
            {
                "connection_id": conn._conn_id,
                "namespace": namespace,
                "owner": owner,
                "kind": kind,
            },
        )
        return conn._conn_id

    def unregister(self, conn: Any) -> bool:
        """
        注销连接（不主动关闭底层连接）

        连接断开 / 关闭后由框架自动调用；清除全部分组与索引。
        幂等：未登记的连接返回 False。

        {!--< internal-use >!--}
        由 router 断开路径、client 连接关闭与 SseEmitter.close 自动调用。
        {!--< /internal-use >!--}

        :param conn: 连接对象或连接 id
        :return: bool 是否实际注销
        """
        conn_id = conn if isinstance(conn, str) else getattr(conn, "id", "")
        if not conn_id:
            return False

        with self._lock:
            target = self._by_id.pop(conn_id, None)
            if target is None:
                return False
            namespace = target.namespace
            owner = target.owner
            groups = tuple(target.groups)
            if namespace and namespace in self._by_namespace:
                self._by_namespace[namespace].discard(conn_id)
                if not self._by_namespace[namespace]:
                    del self._by_namespace[namespace]
            if owner and owner in self._by_owner:
                self._by_owner[owner].discard(conn_id)
                if not self._by_owner[owner]:
                    del self._by_owner[owner]
            for group in groups:
                members = self._by_group.get(group)
                if members is not None:
                    members.discard(conn_id)
                    if not members:
                        del self._by_group[group]
            target._set_conn_groups(frozenset())

        lifecycle.fire(
            EVENT_CONNECTION_UNREGISTERED,
            {
                "connection_id": conn_id,
                "namespace": namespace,
                "owner": owner,
                "kind": target.kind,
                "groups": list(groups),
            },
        )
        return True

    # ---- 查询 ----

    def get(self, connection_id: str) -> Any:
        """
        按连接 id 获取连接（跨模块传递 / 复用的入口）

        返回连接本体：任何模块都可 ``send_json`` / 分组操作；
        ``close`` 仅连接 owner 可调（上下文不可归因时放行）。

        :param connection_id: str 连接 id
        :return: 连接对象（WebSocketConnection / ClientWebSocket / SseEmitter）
        :raises ConnectionNotFoundError: 连接不存在或已断开注销
        """
        with self._lock:
            target = self._by_id.get(connection_id)
        if target is None:
            raise ConnectionNotFoundError(connection_id)
        return target

    def list(
        self,
        *,
        namespace: str | None = None,
        owner: str | None = None,
        group: str | None = None,
        kind: str | None = None,
    ) -> list[Any]:
        """
        查询连接集合（各过滤条件之间为 AND）

        :param namespace: str | None 按服务端命名空间过滤（即"查看某模块连接池"）
        :param owner: str | None 按归属 owner 过滤
        :param group: str | None 按业务分组过滤
        :param kind: str | None 按连接种类过滤（"server" / "client" / "sse"）
        :return: list 连接对象快照列表

        :example:
        >>> connections.list(namespace="Dashboard")
        """
        with self._lock:
            if group is not None:
                ids = set(self._by_group.get(group, ()))
            elif namespace is not None:
                ids = set(self._by_namespace.get(namespace, ()))
            elif owner is not None:
                ids = set(self._by_owner.get(owner, ()))
            else:
                ids = set(self._by_id.keys())

            result = []
            for conn_id in ids:
                target = self._by_id.get(conn_id)
                if target is None:
                    continue
                if namespace is not None and target.namespace != namespace:
                    continue
                if owner is not None and target.owner != owner:
                    continue
                if group is not None and group not in target.groups:
                    continue
                if kind is not None and target.kind != kind:
                    continue
                result.append(target)
        return result

    def stats(
        self,
        *,
        namespace: str | None = None,
        owner: str | None = None,
    ) -> dict[str, Any]:
        """
        连接池统计（各维度计数）

        :param namespace: str | None 先按命名空间过滤再统计
        :param owner: str | None 先按归属过滤再统计
        :return: dict 含 total / by_kind / by_namespace / by_owner / groups

        :example:
        >>> connections.stats()
        {'total': 3, 'by_kind': {'server': 2, 'sse': 1}, ...}
        """
        conns = self.list(namespace=namespace, owner=owner)
        by_kind: dict[str, int] = {}
        by_namespace: dict[str, int] = {}
        by_owner: dict[str, int] = {}
        groups: dict[str, int] = {}
        for target in conns:
            by_kind[target.kind] = by_kind.get(target.kind, 0) + 1
            if target.namespace:
                by_namespace[target.namespace] = by_namespace.get(target.namespace, 0) + 1
            if target.owner:
                by_owner[target.owner] = by_owner.get(target.owner, 0) + 1
            for group in target.groups:
                groups[group] = groups.get(group, 0) + 1
        return {
            "total": len(conns),
            "by_kind": by_kind,
            "by_namespace": by_namespace,
            "by_owner": by_owner,
            "groups": groups,
        }

    def __len__(self) -> int:
        with self._lock:
            return len(self._by_id)

    def counts(self) -> dict[str, int]:
        """
        {!--< internal-use >!--}
        供 ownership.counts() 审计的登记簿计数
        """
        with self._lock:
            return {
                "connections": len(self._by_id),
                "connection_groups": len(self._by_group),
            }

    # ---- 分组 ----

    def assign(self, connection_id: str, *groups: str) -> None:
        """
        将连接加入业务分组（管理侧被动分配）

        与连接侧 ``conn.join_group(...)`` 等价；分组命名完全由业务约定。
        连接断开时自动退出全部分组。

        :param connection_id: str 连接 id
        :param groups: str 一个或多个分组名
        :raises ConnectionNotFoundError: 连接不存在或已断开
        """
        if not groups:
            return
        with self._lock:
            target = self._by_id.get(connection_id)
            if target is None:
                raise ConnectionNotFoundError(connection_id)
            merged = set(target.groups)
            for group in groups:
                merged.add(group)
                self._by_group.setdefault(group, set()).add(connection_id)
            target._set_conn_groups(frozenset(merged))

        for group in groups:
            lifecycle.fire(
                EVENT_CONNECTION_GROUP_JOINED,
                {"connection_id": connection_id, "group": group},
            )

    def dismiss(self, connection_id: str, *groups: str) -> None:
        """
        将连接移出业务分组

        :param connection_id: str 连接 id
        :param groups: str 一个或多个分组名；不传则退出全部分组
        :raises ConnectionNotFoundError: 连接不存在或已断开
        """
        with self._lock:
            target = self._by_id.get(connection_id)
            if target is None:
                raise ConnectionNotFoundError(connection_id)
            current = set(target.groups)
            leaving = tuple(current) if not groups else tuple(g for g in groups if g in current)
            for group in leaving:
                members = self._by_group.get(group)
                if members is not None:
                    members.discard(connection_id)
                    if not members:
                        del self._by_group[group]
            target._set_conn_groups(frozenset(current.difference(leaving)))

        for group in leaving:
            lifecycle.fire(
                EVENT_CONNECTION_GROUP_LEFT,
                {"connection_id": connection_id, "group": group},
            )

    # ---- 广播 ----

    async def broadcast(
        self,
        data: Any,
        *,
        namespace: str | None = None,
        owner: str | None = None,
        group: str | None = None,
        kind: str | None = None,
        ids: list[str] | set[str] | tuple[str, ...] | None = None,
        exclude: list[str] | set[str] | tuple[str, ...] | None = None,
        timeout: float = DEFAULT_BROADCAST_TIMEOUT_SECS,
        concurrency: int = DEFAULT_BROADCAST_CONCURRENCY,
        raise_on_error: bool = False,
    ) -> BroadcastResult:
        """
        向过滤出的连接集合广播消息

        目标集合 = 各过滤条件（namespace / owner / group / kind）的交集；
        传入 ``ids`` 时以其为候选基准（过滤条件仍生效），``exclude`` 最后剔除。
        每条连接独立计时（``timeout`` 为单条超时而非总时长），单条失败不影响
        其他连接；WS 连接走 ``send_json``，SSE 连接走 ``send``。

        :param data: Any 广播数据（SSE 连接上非 str 数据自动 JSON 序列化）
        :param namespace: str | None 按服务端命名空间过滤
        :param owner: str | None 按归属 owner 过滤
        :param group: str | None 按业务分组过滤
        :param kind: str | None 按连接种类过滤
        :param ids: 候选连接 id 集合（缺省为过滤条件命中的全部连接）
        :param exclude: 需要排除的连接 id 集合
        :param timeout: float 单条连接的发送超时秒数 (默认: 10.0)
        :param concurrency: int 最大并发发送数 (默认: 64)
        :param raise_on_error: bool 存在失败项时在全部发送完成后抛出首个异常
        :return: BroadcastResult 成败明细
        :raises Exception: raise_on_error=True 且存在失败项时抛出首个错误

        :example:
        >>> result = await connections.broadcast(
        ...     {"type": "kick", "reason": "full"}, group="room:1", exclude={"room:1:ab12cd34"}
        ... )
        >>> if not result.ok:
        ...     logger.warning(f"广播部分失败: {result.failed}")
        """
        exclude_set = set(exclude or ())
        with self._lock:
            if ids is not None:
                candidates = [self._by_id[cid] for cid in ids if cid in self._by_id]
                # ids 指定但已不存在的连接计入 failed，让业务知道全貌
                missing = [cid for cid in ids if cid not in self._by_id]
            else:
                candidates = self.list(namespace=namespace, owner=owner, group=group, kind=kind)
                missing = []
            excluded_ids = sorted(conn.id for conn in candidates if conn.id in exclude_set)
            targets = [conn for conn in candidates if conn.id not in exclude_set]

        result = BroadcastResult(total=len(candidates) + len(missing))
        result.excluded = excluded_ids
        for cid in missing:
            result.failed[cid] = ConnectionNotFoundError(cid)

        if not targets:
            if raise_on_error and result.failed:
                raise next(iter(result.failed.values()))
            return result

        semaphore = asyncio.Semaphore(max(1, concurrency))

        async def _send(conn: Any) -> None:
            async with semaphore:
                try:
                    if conn.kind == "sse":
                        await asyncio.wait_for(conn.send(data), timeout=timeout)
                    else:
                        await asyncio.wait_for(conn.send_json(data), timeout=timeout)
                    result.sent.append(conn.id)
                except BaseException as exc:  # 单条失败需明细而非中断广播
                    result.failed[conn.id] = exc

        await asyncio.gather(*(_send(conn) for conn in targets))

        if raise_on_error and result.failed:
            raise next(iter(result.failed.values()))
        return result

    # ---- 关闭 / 回收 ----

    async def close(self, connection_id: str, *, force: bool = False) -> bool:
        """
        关闭并注销指定连接

        :param connection_id: str 连接 id
        :param force: bool 跳过归属权限校验（框架回收路径使用）
        :return: bool 连接是否存在（存在则已发起关闭）
        :raises ConnectionPermissionError: 非 owner 关闭且未 force 时
        """
        conn = self.get(connection_id)
        await conn.close(force=force)
        self.unregister(conn)
        return True

    async def close_owner(self, owner: str) -> int:
        """
        关闭并注销指定 owner 名下的全部连接

        模块卸载 / 适配器关闭链由框架自动调用：服务端 WS/SSE 与客户端出站
        连接一并回收（server 连接的 owner 即其注册模块名）。

        :param owner: 归属者（模块名 / 平台名）
        :return: int 发起关闭的连接数
        """
        with self._lock:
            conn_ids = list(self._by_owner.get(owner, ()))
            conns = [self._by_id[cid] for cid in conn_ids if cid in self._by_id]

        closed = 0
        for conn in conns:
            try:
                await asyncio.wait_for(
                    conn.close(force=True),
                    timeout=DEFAULT_CONNECTION_CLOSE_TIMEOUT_SECS,
                )
            except Exception:
                pass  # 单条关闭失败不阻塞回收链；连接随后由底层自行收尾
            self.unregister(conn)
            closed += 1
        return closed

    def clear(self, *, kind: str | None = None) -> int:
        """
        注销登记（不关闭底层连接）

        服务器停止 / 管理器重置时由框架调用：连接随底层服务终止，
        仅需清空登记簿防止悬挂条目。

        {!--< internal-use >!--}
        {!--< /internal-use >!--}

        :param kind: str | None 仅注销指定种类（如 "server"）；None 清空全部
        :return: int 注销的连接数
        """
        with self._lock:
            stale = [
                conn for conn in self._by_id.values() if kind is None or conn.kind == kind
            ]
            for conn in stale:
                self.unregister(conn)
        return len(stale)


# 连接注册表单例：``from ErisPulse import connections`` 获取；模块间共享同一注册表。
connections: ConnectionManager = ConnectionManager()

__all__ = [
    "BroadcastResult",
    "ConnectionManager",
    "connections",
]
