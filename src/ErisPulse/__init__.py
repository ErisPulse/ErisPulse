"""
ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

{!--< tips >!--}
1. 使用前请确保已正确安装所有依赖
2. 调用await sdk.init()进行初始化
3. 模块加载采用懒加载机制
{!--< /tips >!--}
"""

# 导入核心模块
from .Core import (
    BaseAdapter,
    Event,
    SendDSL,
    SendContext,
    SendBuilder,
    BatchContext,
    adapter,
    config,
    env,
    i18n,
    lifecycle,
    logger,
    module,
    router,
    scope,
    storage,
)

# 导入懒加载模块类
from .loaders.module import LazyModule

# 导入实际的SDK对象与 SDK 类型（供模块 __init__ 注解 sdk: SDK = None 使用）
from .sdk import SDK, sdk

# ==================== 版本信息 ====================

__author__ = "ErisPulse"


def __getattr__(name: str):
    """
    惰性解析 ``__version__``（首次访问时经包元数据读取）

    :param name: 属性名
    :return: 属性值
    :raises AttributeError: 未知属性时抛出

    {!--< internal-use >!--}
    避免在 ``import ErisPulse`` 时为读取版本号而加载 importlib.metadata
    及其依赖链（email/zipfile/asyncio 等，冷启动约数十毫秒）
    {!--< /internal-use >!--}
    """
    if name == "__version__":
        global __version__
        import importlib.metadata

        try:
            __version__ = importlib.metadata.version("ErisPulse")
        except importlib.metadata.PackageNotFoundError:
            __version__ = "UnknownVersion"
        return __version__
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# 向后兼容性导出
init = sdk.init
init_sync = sdk.init_sync
init_task = sdk.init_task
load_module = sdk.load_module
run = sdk.run
restart = sdk.restart
uninit = sdk.uninit

# 导出列表
__all__ = [
    "SDK",
    "BaseAdapter",
    "BatchContext",
    "Event",
    "LazyModule",
    "SendBuilder",
    "SendContext",
    "SendDSL",
    "__author__",
    "__version__",
    "adapter",
    "config",
    "env",
    "i18n",
    "init",
    "init_sync",
    "init_task",
    "lifecycle",
    "load_module",
    "logger",
    "module",
    "restart",
    "router",
    "run",
    "scope",
    "sdk",
    "storage",
    "uninit",
]
