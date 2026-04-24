"""
ErisPulse 核心模块

提供了一系列用于构建和管理应用的核心组件，包括适配器、模块、存储、配置、路由和生命周期管理等。
"""

from .lifecycle import lifecycle, LifecycleManager
from .adapter import adapter, AdapterManager
from .Bases import BaseAdapter, BaseModule, SendDSL
from .storage import storage, StorageManager
from .logger import logger, Logger, LoggerChild
from .module import module, ModuleManager
from .router import router, RouterManager
from .config import config, ConfigManager
from . import Event
from .Event.message_builder import MessageBuilder

env             = storage       # 存储管理器别名

__all__ = [
    'Event',

    'adapter',
    'AdapterManager',
    'BaseAdapter',
    'SendDSL',
    'MessageBuilder',

    'module',
    'ModuleManager',
    'BaseModule',

    'storage',
    'StorageManager',
    'config',
    'env',              # 配置管理器别名
    'ConfigManager',

    'router',
    'RouterManager',

    'logger',
    'Logger',
    'LoggerChild',
    'lifecycle',
    'LifecycleManager',
]
