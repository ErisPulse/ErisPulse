from .lifecycle import lifecycle, LifecycleManager
from .adapter import adapter, AdapterManager
from .Bases import BaseAdapter, BaseModule, SendDSL
from .storage import storage, StorageManager
from .logger import logger, Logger, LoggerChild
from .module import module, ModuleManager
from .router import router, RouterManager
from .config import config, ConfigManager
from . import exceptions
from . import Event

# 兼容性别名定义
adapter_server  = router        # 路由管理器别名
env             = storage       # 存储管理器别名
AdapterFather   = BaseAdapter   # 适配器基类别名

__all__ = [
    # 事件模块
    'Event',

    # 适配器相关
    'adapter',          # 适配器管理器
    'AdapterManager',   # 适配器管理器类
    'AdapterFather',    # 适配器基类
    'BaseAdapter',      # 适配器基类别名
    'SendDSL',          # DSL发送接口基类

    # 模块相关
    'module',           # 模块管理器
    'ModuleManager',    # 模块管理器类
    'BaseModule',       # 模块基类
    
    # 存储和配置相关
    'storage',          # 存储管理器
    'StorageManager',   # 存储管理器类
    'config',           # 配置管理器
    'ConfigManager',    # 配置管理器类
    'env',              # 配置管理器别名

    # 路由相关
    'router',           # 路由管理器
    'RouterManager',    # 路由管理器类
    'adapter_server',   # 路由管理器别名

    # 基础设施
    'logger',           # 日志管理器
    'Logger',           # 日志管理器类
    'LoggerChild',      # 日志子管理器类
    'exceptions',       # 异常处理模块
    'lifecycle',        # 生命周期管理器
    'LifecycleManager', # 生命周期管理器类
]
