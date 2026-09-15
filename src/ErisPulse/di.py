"""
ErisPulse 依赖注入

统一各处理器注入点（命令 / 事件 / 生命周期钩子 / 路由）的声明式依赖注入：

>>> from ErisPulse.di import Depends
>>> async def get_db(event):
...     return await sdk.module.call("DB", "get_session")
>>> @command("admin")
... async def admin(event, db=Depends(get_db)):
...     ...

{!--< tips >!--}
1. 依赖函数第一个参数是注入点上下文对象（Event / 生命周期 data / 路由 HttpRequest）
2. FastAPI 承载的 HTTP 路由请使用 FastAPI 原生 fastapi.Depends
{!--< /tips >!--}
"""

from .Core.di import Depends, extract_depends, resolve_depends

__all__ = ["Depends", "extract_depends", "resolve_depends"]
