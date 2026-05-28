"""
ErisPulse 基础模块

提供平台适配器、模块和存储后端的基类
"""

from .adapter import SendDSL, RequestDSL, BaseAdapter
from .module import BaseModule
from .storage import BaseStorage, BaseQueryBuilder

__all__ = [
    "BaseAdapter",
    "SendDSL",
    "RequestDSL",
    "BaseModule",
    "BaseStorage",
    "BaseQueryBuilder",
]
