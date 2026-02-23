"""
ErisPulse 基础模块

提供平台适配器以及模块的基类
"""

from .adapter import SendDSL, BaseAdapter
from .module import BaseModule

__all__ = [
    "BaseAdapter",
    "SendDSL",
    "BaseModule"
]
