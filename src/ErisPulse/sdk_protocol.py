"""
ErisPulse SDK Protocol 定义

提供 SDK 的类型接口定义，用于 IDE 类型提示和静态类型检查
"""

from typing import Protocol, runtime_checkable, Any, TypeVar
from typing_extensions import ParamSpec
import asyncio

# 导入核心模块类型
from .Core.Event import Event as EventType
from .Core.lifecycle import LifecycleManager
from .Core.logger import Logger
from .Core.storage import StorageManager
from .Core.config import ConfigManager
from .Core.adapter import AdapterManager
from .Core.module import ModuleManager
from .Core.router import RouterManager
from .Core.Bases.adapter import BaseAdapter, SendDSL

P = ParamSpec('P')
T = TypeVar('T')


@runtime_checkable
class SDKProtocol(Protocol):
    """
    SDK 对象的 Protocol 接口定义
    
    定义了 SDK 对象应该具有的所有属性和方法，用于类型检查
    """
    
    # ==================== 核心模块 ====================
    
    Event: type[EventType]
    """事件系统"""
    
    lifecycle: LifecycleManager
    """生命周期管理器"""
    
    logger: Logger
    """日志管理器"""
    
    exceptions: Any
    """异常处理模块"""
    
    storage: StorageManager
    """存储管理器"""
    
    env: StorageManager
    """存储管理器别名"""
    
    config: ConfigManager
    """配置管理器"""
    
    adapter: AdapterManager
    """适配器管理器"""
    
    AdapterFather: type[BaseAdapter]
    """适配器基类别名"""
    
    BaseAdapter: type[BaseAdapter]
    """适配器基类"""
    
    SendDSL: type[SendDSL]
    """DSL发送接口基类"""
    
    module: ModuleManager
    """模块管理器"""
    
    router: RouterManager
    """路由管理器"""
    
    adapter_server: RouterManager
    """路由管理器别名"""
    
    # ==================== 初始化方法 ====================
    
    async def init(self) -> bool:
        """
        SDK初始化入口
        
        :return: bool SDK初始化是否成功
        """
        ...
    
    def init_task(self) -> asyncio.Task:
        """
        SDK初始化入口，返回Task对象
        
        :return: asyncio.Task 初始化任务
        """
        ...
    
    async def load_module(self, module_name: str) -> bool:
        """
        手动加载指定模块
        
        :param module_name: str 要加载的模块名称
        :return: bool 加载是否成功
        """
        ...
    
    async def run(self, keep_running: bool = True) -> None:
        """
        无头模式运行ErisPulse
        
        :param keep_running: bool 是否保持运行
        """
        ...
    
    async def restart(self) -> bool:
        """
        SDK重新启动
        
        :return: bool 重新加载是否成功
        """
        ...
    
    async def uninit(self) -> bool:
        """
        SDK反初始化
        
        :return: bool 反初始化是否成功
        """
        ...


def check_sdk_compatible(obj: Any) -> bool:
    """
    检查对象是否符合 SDK Protocol
    
    :param obj: 要检查的对象
    :return: bool 是否符合协议
    """
    return isinstance(obj, SDKProtocol)


__all__ = [
    "SDKProtocol",
    "check_sdk_compatible"
]
