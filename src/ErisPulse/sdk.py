"""
ErisPulse SDK 主类

提供统一的 SDK 接口，整合所有核心模块和加载器

{!--< tips >!--}
example:
    >>> from ErisPulse import sdk
    >>> await sdk.init()
    >>> await sdk.adapter.startup()
{!--< /tips >!--}
"""

from typing import Any

# 导入核心模块
from .Core import Event
from .Core import lifecycle, logger, exceptions
from .Core import storage, env, config
from .Core import adapter, AdapterFather, BaseAdapter, SendDSL
from .Core import module
from .Core import router, adapter_server


class SDK:
    """
    ErisPulse SDK 主类
    
    整合所有核心模块和加载器，提供统一的初始化和管理接口
    
    {!--< tips >!--}
    SDK 提供以下核心属性：
    - Event: 事件系统
    - lifecycle: 生命周期管理器
    - logger: 日志管理器
    - exceptions: 异常处理模块
    - storage: 存储管理器
    - env: 存储管理器别名
    - config: 配置管理器
    - adapter: 适配器管理器
    - AdapterFather: 适配器基类别名
    - BaseAdapter: 适配器基类
    - SendDSL: DSL 发送接口基类
    - module: 模块管理器
    - router: 路由管理器
    - adapter_server: 路由管理器别名
    {!--< /tips >!--}
    """
    
    # ==================== 核心模块属性 ====================
    
    Event: Any
    """事件系统"""
    
    lifecycle: Any
    """生命周期管理器"""
    
    logger: Any
    """日志管理器"""
    
    exceptions: Any
    """异常处理模块"""
    
    storage: Any
    """存储管理器"""
    
    env: Any
    """存储管理器别名"""
    
    config: Any
    """配置管理器"""
    
    adapter: Any
    """适配器管理器"""
    
    AdapterFather: Any
    """适配器基类别名"""
    
    BaseAdapter: Any
    """适配器基类"""
    
    SendDSL: Any
    """DSL 发送接口基类"""
    
    module: Any
    """模块管理器"""
    
    router: Any
    """路由管理器"""
    
    adapter_server: Any
    """路由管理器别名"""
    
    def __init__(self):
        """
        初始化 SDK 实例
        
        挂载所有核心模块到 SDK 实例
        """
        # 挂载核心模块
        self.Event = Event
        self.lifecycle = lifecycle
        self.logger = logger
        self.exceptions = exceptions
        
        self.storage = storage
        self.env = env
        self.config = config
        
        self.adapter = adapter
        self.AdapterFather = AdapterFather
        self.BaseAdapter = BaseAdapter
        self.SendDSL = SendDSL
        
        self.module = module
        
        self.router = router
        self.adapter_server = adapter_server
        
        # 初始化协调器（在需要时创建）
        self._initializer: Any = None  # type: ignore
        self._initialized: bool = False
    
    def __getattribute__(self, name: str):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            self.logger.error(f"[SDK] 未找到属性 {name}, 您可能使用了错误的SDK注册对象")
            return None

    def __repr__(self) -> str:
        """
        返回 SDK 的字符串表示
        
        :return: str SDK 的字符串表示
        """
        return f"<ErisPulse SDK initialized={self._initialized}>"


# 创建全局 SDK 实例
sdk = SDK()

__all__ = [
    "SDK",
    "sdk"
]
