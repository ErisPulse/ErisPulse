"""
ErisPulse 运行时上下文

提供 contextvars 基础设施，用于追踪事件处理器、路由等资源的归属者。
在模块/适配器加载期间设置当前 owner，使资源注册能自动标记来源，
从而支持按模块精确清理（热禁用、热重载）。

{!--< tips >!--}
使用方式::

    from ErisPulse.runtime.context import owner_scope, get_current_owner
    # 或通过 SDK：sdk.context.owner_scope(...) / sdk.context.get_current_owner()

    # 在指定 owner 上下文下执行代码块（自动复位）
    with owner_scope("Dashboard"):
        # 注册的 handler 会自动打上 owner="Dashboard"
        pass

    # 读取当前 owner
    owner = get_current_owner()  # 返回 "Dashboard" 或 None
{!--< /tips >!--}
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

#: 当前资源归属者（模块名或适配器平台名）。
#: 在模块/适配器加载期间由框架设置，事件处理器注册时读取。
#: 值为 None 表示当前不在任何模块/适配器的加载上下文中。
current_owner: ContextVar[str | None] = ContextVar("current_owner", default=None)

#: 当前跨模块调用的调用方身份（模块名或适配器平台名）。
#:
#: 生命周期
#:   由 ``Core/module.py:ModuleManager.call`` 在执行目标模块方法期间注入：
#:   调用发生时捕获 ``current_owner``（即调用方），目标方法执行期间
#:   ``current_owner`` 归因到目标模块（日志/出站发送归属谁的代码归因谁），
#:   而 ``current_caller`` 保留调用方身份，供被调方识别"谁在调用我"。
#:
#: 用途
#:   工具模块（定时任务 / 注册表等）经 ``module.call`` 被调用时，
#:   通过 ``get_current_caller()`` 获取调用来源模块，为托管资源正确记名
#:   （``on_cleanup`` 在 owner 上下文缺失时同样回退读取此值）。
current_caller: ContextVar[str | None] = ContextVar("current_caller", default=None)

#: 当前 handler / Task 执行期间累计的 wait_reply 调用记录。
#:
#: 生命周期
#:   由 ``Core/adapter.py:_dispatch_handler_task`` 在 Task 入口初始化为空 list，
#:   由 ``Core/Event/base.py:_invoke_handler`` 在每个 handler 入口切换为局部 list（结束后回填外层），
#:   由 ``Core/Event/command.py:wait_reply`` 在每次等待用户回复时追加一条记录。
#:
#: 记录格式
#:   ``{"owner": str|None, "duration": float, "wait_key": str}``
#:
#: 用途
#:   slow-log 判定时读取此列表，将其中累计的 ``duration`` 从总耗时中扣除，
#:   避免"等待用户回复"被误报为慢处理器。
handler_waits: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "handler_waits", default=None
)

#: 当前事件的处理链路追踪 ID（trace-id）。
#:
#: 生命周期
#:   由 ``Core/adapter.py:emit`` 在事件入站时从 ``event["id"]`` 取得（缺失则生成），
#:   随事件分发复制到各 handler Task 的上下文；
#:   出站发送（``Core/Bases/adapter.py`` Send 钩子）与 lifecycle 钩子数据自动携带。
#:
#: 用途
#:   一条消息被多个模块接力处理时，入站 → 处理 → 出站全链路可用同一 ID 串联
#:   （日志、send_ctx、lifecycle data 中的 ``trace_id`` 字段）。
current_trace_id: ContextVar[str | None] = ContextVar("current_trace_id", default=None)

#: 消息回执账本（message transaction）。
#:
#: 生命周期
#:   由 ``Event.message_tx()`` 上下文管理器置为空 list，
#:   由 ``Core/Bases/adapter.py`` Send 钩子在每次成功发送（响应含非空
#:   ``message_id``）时追加一条回执，``message_tx`` 退出异常时逆序撤回。
#:
#: 记录格式
#:   ``{"platform": str, "bot_id": str, "message_id": str, "trace_id": str|None}``
#:
#: 用途
#:   消息事务：handler 中途失败时自动撤回本次事务内已发送的消息
#:   （能力感知：适配器未实现 delete_message 时跳过）。
send_receipts: ContextVar[list[dict[str, str]] | None] = ContextVar(
    "send_receipts", default=None
)


@contextmanager
def owner_scope(owner: str | None):
    """
    在指定 owner 上下文下执行代码块（退出时自动复位 current_owner）

    模块/适配器在非加载场景下注册资源（命令/事件处理器/路由/生命周期钩子）时，
    可用本上下文管理器让资源自动归属到指定 owner，从而被作用域过滤与按 owner 清理识别。
    比手写 ``token = current_owner.set(...); try/finally: reset`` 更简洁安全。

    :param owner: 资源归属者（模块名或适配器平台名），None 表示清除当前 owner

    :example:
    >>> with owner_scope("MyModule"):
    ...     @command("hello")
    ...     async def hello(event): ...
    """
    token = current_owner.set(owner)
    try:
        yield
    finally:
        current_owner.reset(token)


def get_current_owner() -> str | None:
    """
    获取当前资源归属者（模块名或适配器平台名）

    在事件处理器 / 命令 / 钩子执行期间，框架已注入对应模块或适配器的 owner，
    可用于日志归因、权限判断等。

    :return: 当前 owner，不在任何加载/执行上下文时返回 None

    :example:
    >>> owner = get_current_owner()
    """
    return current_owner.get()


def get_current_caller() -> str | None:
    """
    获取当前跨模块调用的调用方身份（模块名或适配器平台名）

    经 ``sdk.module.call()`` 被调用期间，``current_owner`` 已归因到目标
    模块（自己的代码归属自己），而调用方身份保留在本上下文中——被调方
    可据此识别"谁在调用我"。直接属性访问（``sdk.Cron.once(...)``）不经
    此上下文，此时调用方身份即 ``get_current_owner()``。

    :return: 调用方身份，非 ``module.call`` 调用链或框架层调用时返回 None

    :example:
    >>> caller = get_current_caller()  # "OrderModule" 或 None
    """
    return current_caller.get()


def get_handler_waits() -> list[dict[str, Any]] | None:
    """
    获取当前 handler 的 wait_reply 调用记录（slow-log 归因用）

    :return: 记录列表或 None（不在 handler / Task 上下文内）
    """
    return handler_waits.get()


def get_current_trace_id() -> str | None:
    """
    获取当前事件处理链路的追踪 ID（trace-id）

    在事件分发 / handler 执行 / 出站发送期间可读取，用于跨模块日志关联；
    不在事件处理上下文内（如后台定时任务）返回 None。

    :return: 当前 trace-id 或 None

    :example:
    >>> trace_id = get_current_trace_id()
    """
    return current_trace_id.get()


def get_send_receipts() -> list[dict[str, str]] | None:
    """
    获取当前消息事务的回执账本

    仅在 ``Event.message_tx()`` 事务内返回非 None；
    可用于查看本次事务已发送了哪些消息。

    :return: 回执记录列表或 None（不在事务内）

    :example:
    >>> receipts = get_send_receipts()
    """
    return send_receipts.get()


__all__ = [
    "current_caller",
    "current_owner",
    "current_trace_id",
    "get_current_caller",
    "get_current_owner",
    "get_current_trace_id",
    "get_handler_waits",
    "get_send_receipts",
    "handler_waits",
    "owner_scope",
    "send_receipts",
]
