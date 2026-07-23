"""
ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

{!--< tips >!--}
1. 使用前请确保已正确安装所有依赖
2. 调用await sdk.init()进行初始化
3. 模块加载采用懒加载机制
{!--< /tips >!--}
"""

import importlib.metadata

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
    storage,
)

# 导入懒加载模块类
from .loaders.module import LazyModule

# 导入实际的SDK对象
from .sdk import sdk

# ==================== 版本信息 ====================

__version__ = "UnknownVersion"
__author__ = "ErisPulse"

try:
    __version__ = importlib.metadata.version("ErisPulse")
except importlib.metadata.PackageNotFoundError:
    pass


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
    "sdk",
    "storage",
    "uninit",
]
