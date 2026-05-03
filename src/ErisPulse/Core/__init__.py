"""
ErisPulse 核心模块

提供了一系列用于构建和管理应用的核心组件，包括适配器、模块、存储、配置、路由和生命周期管理等。
"""

from .lifecycle import lifecycle, LifecycleManager
from .adapter import adapter, AdapterManager
from .Bases import BaseAdapter, BaseModule, SendDSL, BaseStorage, BaseQueryBuilder
from .storage import storage, StorageManager
from .logger import logger, Logger, LoggerChild
from .module import module, ModuleManager
from .router import router, RouterManager
from .config import config, ConfigManager
from . import Event
from .Event.message_builder import MessageBuilder

env = storage       # 存储管理器别名

__all__ = [
    'Event',            # 事件模块包

    'adapter',          # 适配器模块单例
    'AdapterManager',   # 适配器管理器类
    'BaseAdapter',      # 适配器基类
    'SendDSL',          # 发送DSL类
    'MessageBuilder',   # 消息构建器类

    'module',           # 模块模块单例
    'ModuleManager',    # 模块管理器类
    'BaseModule',       # 模块基类

    'storage',          # 存储模块单例
    'StorageManager',   # 存储管理器类
    'BaseStorage',      # 存储后端抽象基类
    'BaseQueryBuilder', # 查询构建器抽象基类
    'config',           # 配置模块单例
    'env',              # 配置管理器别名
    'ConfigManager',    # 配置管理器类

    'router',           # 路由模块单例
    'RouterManager',    # 路由管理器类

    'logger',           # 日志模块单例
    'Logger',           # 日志类
    'LoggerChild',      # 日志子类
    'lifecycle',        # 生命周期模块单例
    'LifecycleManager', # 生命周期管理器类
]
