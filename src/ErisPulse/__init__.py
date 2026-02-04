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
    Event,
    lifecycle,
    logger,
    exceptions,
    storage,
    env,
    config,
    adapter,
    AdapterFather,
    BaseAdapter,
    SendDSL,
    module,
    router,
    adapter_server,
)

# 导入实际的SDK对象
from .sdk import sdk

# 导入懒加载模块类
from .loaders.module import LazyModule

# 版本信息
__version__ = "UnknownVersion"
__author__ = "ErisPulse"

try:
    __version__ = importlib.metadata.version('ErisPulse')
except importlib.metadata.PackageNotFoundError:
    pass


# 导出SDK对象
__all__ = [
    "sdk",
    "__version__",
    "__author__",
    "LazyModule",
]
