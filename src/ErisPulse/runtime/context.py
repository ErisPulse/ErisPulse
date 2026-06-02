"""
ErisPulse 运行时上下文

提供 contextvars 基础设施，用于追踪事件处理器、路由等资源的归属者。
在模块/适配器加载期间设置当前 owner，使资源注册能自动标记来源，
从而支持按模块精确清理（热禁用、热重载）。

{!--< tips >!--}
使用方式::

    from ErisPulse.runtime.context import current_owner

    # 模块加载时
    token = current_owner.set("Dashboard")
    try:
        # ... 模块 __init__ / on_load 执行期间，注册的 handler 会自动打上 owner="Dashboard"
        pass
    finally:
        current_owner.reset(token)

    # handler 注册时读取
    owner = current_owner.get()  # 返回 "Dashboard" 或 None
{!--< /tips >!--}
"""

from contextvars import ContextVar
from typing import Any

#: 当前资源归属者（模块名或适配器平台名）。
#: 在模块/适配器加载期间由框架设置，事件处理器注册时读取。
#: 值为 None 表示当前不在任何模块/适配器的加载上下文中。
current_owner: ContextVar[str | None] = ContextVar("current_owner", default=None)

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

__all__ = ["current_owner", "handler_waits"]
