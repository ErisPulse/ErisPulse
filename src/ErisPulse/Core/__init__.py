from .lifecycle import lifecycle
from .adapter import adapter
from .base import BaseAdapter, SendDSL
from .storage import storage
from .logger import logger
from .module import module
from .router import router
from .config import config
from . import exceptions
from . import Event

# 兼容性别名定义
adapter_server  = router        # 路由管理器别名
env             = storage       # 存储管理器别名
AdapterFather   = BaseAdapter # 适配器基类别名

__all__ = [
    # 事件模块
    'Event',

    # 适配器相关
    'adapter',          # 适配器管理器
    'AdapterFather',    # 适配器基类
    'BaseAdapter',      # 适配器基类别名
    'SendDSL',          # DSL发送接口基类

    # 模块相关
    'module',           # 模块管理器
    
    # 存储和配置相关
    'storage',          # 存储管理器
    'config',           # 配置管理器
    'env',              # 配置管理器别名

    # 路由相关
    'router',           # 路由管理器
    'adapter_server',   # 路由管理器别名

    # 基础设施
    'logger',           # 日志管理器
    'exceptions',       # 异常处理模块
    'lifecycle'         # 生命周期管理器
]