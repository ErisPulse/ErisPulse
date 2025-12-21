"""
ErisPulse 基础模块

提供核心基类定义，包括适配器和模块基类
"""

from .adapter import SendDSL, BaseAdapter
from .module import BaseModule

__all__ = [
    "BaseAdapter",
    "SendDSL",
    "BaseModule"
]
