"""
ErisPulse 模块系统

提供标准化的模块注册、加载和管理功能，与适配器系统保持一致的设计模式
"""

import asyncio
from typing import Any, Dict, List, Type, Optional
from .logger import logger
from .config import config
from .Bases import BaseModule
from .lifecycle import lifecycle

class ModuleManager:
    """
    模块管理器
    
    提供标准化的模块注册、加载和管理功能，模仿适配器管理器的模式
    
    {!--< tips >!--}
    1. 使用register方法注册模块类
    2. 使用load/unload方法加载/卸载模块
    3. 通过get方法获取模块实例
    {!--< /tips >!--}
    """
    
    def __init__(self):
        # 模块存储
        self._modules: Dict[str, Any] = {}  # 已加载的模块实例
        self._module_classes: Dict[str, Type] = {}  # 模块类映射
        self._loaded_modules: set = set()  # 已加载的模块名称
        self._module_info: Dict[str, Dict] = {}  # 模块信息
        
    # ==================== 模块注册与管理 ====================
    
    def register(self, module_name: str, module_class: Type, module_info: Optional[Dict] = None) -> bool:
        """
        注册模块类
        
        :param module_name: 模块名称
        :param module_class: 模块类
        :param module_info: 模块信息
        :return: 是否注册成功
        
        :raises TypeError: 当模块类无效时抛出
            
        :example:
        >>> module.register("MyModule", MyModuleClass)
        """
        # 严格验证模块类，确保继承自BaseModule
        if not issubclass(module_class, BaseModule):
            warn_msg = f"模块 {module_name} 的类 {module_class.__name__} 没有继承自BaseModule，但我们仍会继续尝试加载这个模块，但请注意这可能引发其他问题"
            logger.warning(warn_msg)
            # error_msg = f"模块 {module_name} 的类 {module_class.__name__} 必须继承自BaseModule"
            # logger.error(error_msg)
            # raise TypeError(error_msg)
            
        # 验证模块名是否合法
        if not module_name or not isinstance(module_name, str):
            error_msg = "模块名称必须是非空字符串"
            logger.error(error_msg)
            raise TypeError(error_msg)
            
        # 检查模块名是否已存在
        if module_name in self._module_classes:
            logger.warning(f"模块 {module_name} 已存在，将覆盖原模块类")
            
        self._module_classes[module_name] = module_class
        if module_info:
            self._module_info[module_name] = module_info
            
        logger.info(f"模块 {module_name} 已注册")
        return True
    
    async def load(self, module_name: str) -> bool:
        """
        加载指定模块（标准化加载逻辑）
        
        :param module_name: 模块名称
        :return: 是否加载成功
            
        :example:
        >>> await module.load("MyModule")
        """
        # 检查模块是否已注册
        if module_name not in self._module_classes:
            logger.error(f"模块 {module_name} 未注册")
            return False
            
        # 检查模块是否已加载
        if module_name in self._loaded_modules:
            logger.info(f"模块 {module_name} 已加载")
            return True
            
        try:
            from .. import sdk
            import inspect
            
            # 创建模块实例
            module_class = self._module_classes[module_name]
            
            # 检查是否需要传入sdk参数
            init_signature = inspect.signature(module_class.__init__)
            params = init_signature.parameters
            
            if 'sdk' in params:
                instance = module_class(sdk)
            else:
                instance = module_class()
                
            # 设置模块信息
            if module_name in self._module_info:
                setattr(instance, "moduleInfo", self._module_info[module_name])
                
            # 调用模块的on_load卸载方法
            if hasattr(instance, 'on_load'):
                try:
                    if asyncio.iscoroutinefunction(instance.on_load):
                        await instance.on_load({"module_name": module_name})
                    else:
                        instance.on_load({"module_name": module_name})
                except Exception as e:
                    logger.error(f"模块 {module_name} on_load 方法执行失败: {e}")
                    return False
                    
            # 缓存模块实例
            self._modules[module_name] = instance
            self._loaded_modules.add(module_name)
            
            await lifecycle.submit_event(
                    "module_load",
                    data={
                        "module_name": module_name,
                        "success": True,
                    },
                    msg=f"模块 {module_name if module_name else 'All'} 加载成功",
                )
            logger.info(f"模块 {module_name} 加载成功")
            return True
            
        except Exception as e:
            await lifecycle.submit_event(
                    "module_load",
                    data={
                        "module_name": module_name,
                        "success": False,
                    },
                    msg=f"模块 {module_name if module_name else 'All'} 加载失败: {e}",
                )
            logger.error(f"加载模块 {module_name} 失败: {e}")
            return False
            
    async def unload(self, module_name: str = "Unknown") -> bool:
        """
        卸载指定模块或所有模块
        
        :param module_name: 模块名称，如果为None则卸载所有模块
        :return: 是否卸载成功
            
        :example:
        >>> await module.unload("MyModule")
        >>> await module.unload()  # 卸载所有模块
        """
        if module_name == "Unknown":
            # 卸载所有模块
            success = True
            for name in list(self._loaded_modules):
                if not await self._unload_single_module(name):
                    success = False
            return success
        else:
            success = await self._unload_single_module(module_name)
            
        await lifecycle.submit_event(
            "module.unload",
            msg=f"模块 {module_name if module_name else 'All'} 卸载完成" if success else f"模块 {module_name if module_name else 'All'} 卸载失败",
            data={
                "module_name": module_name if module_name else 'All',
                "success": success
            }
        )
        return success
    
    async def _unload_single_module(self, module_name: str) -> bool:
        """
        {!--< internal-use >!--}
        卸载单个模块
        
        :param module_name: 模块名称
        :return: 是否卸载成功
        """
        if module_name not in self._loaded_modules:
            logger.warning(f"模块 {module_name} 未加载")
            return False
            
        try:
            # 调用模块的on_unload卸载方法
            instance = self._modules[module_name]
            if hasattr(instance, 'on_unload'):
                try:
                    if asyncio.iscoroutinefunction(instance.on_unload):
                        await instance.on_unload({"module_name": module_name})
                    else:
                        instance.on_unload({"module_name": module_name})
                except Exception as e:
                    logger.error(f"模块 {module_name} on_unload 方法执行失败: {e}")
                    
            # 清理缓存
            del self._modules[module_name]
            self._loaded_modules.discard(module_name)
            
            logger.info(f"模块 {module_name} 卸载成功")
            return True
            
        except Exception as e:
            logger.error(f"卸载模块 {module_name} 失败: {e}")
            return False
            
    def get(self, module_name: str) -> Any:
        """
        获取模块实例
        
        :param module_name: 模块名称
        :return: 模块实例或None
            
        :example:
        >>> my_module = module.get("MyModule")
        """
        return self._modules.get(module_name)
        
    def exists(self, module_name: str) -> bool:
        """
        检查模块是否存在（在配置中注册）
        
        :param module_name: [str] 模块名称
        :return: [bool] 模块是否存在
        """
        module_statuses = config.getConfig("ErisPulse.modules.status", {})
        return module_name in module_statuses
    
    def is_loaded(self, module_name: str) -> bool:
        """
        检查模块是否已加载
        
        :param module_name: 模块名称
        :return: 模块是否已加载
            
        :example:
        >>> if module.is_loaded("MyModule"): ...
        """
        return module_name in self._loaded_modules
        
    def list_registered(self) -> List[str]:
        """
        列出所有已注册的模块
        
        :return: 模块名称列表
            
        :example:
        >>> registered = module.list_registered()
        """
        return list(self._module_classes.keys())
        
    def list_loaded(self) -> List[str]:
        """
        列出所有已加载的模块
        
        :return: 模块名称列表
            
        :example:
        >>> loaded = module.list_loaded()
        """
        return list(self._loaded_modules)
    
    # ==================== 模块配置管理 ====================
    
    def _config_register(self, module_name: str, enabled: bool = False) -> bool:
        """
        注册新模块信息
        
        :param module_name: [str] 模块名称
        :param enabled: [bool] 是否启用模块
        :return: [bool] 操作是否成功
        """
        if self.exists(module_name):
            return True
        
        # 模块不存在，进行注册
        config.setConfig(f"ErisPulse.modules.status.{module_name}", enabled)
        status = "启用" if enabled else "禁用"
        logger.info(f"模块 {module_name} 已注册并{status}")
        return True
    
    def is_enabled(self, module_name: str) -> bool:
        """
        检查模块是否启用
        
        :param module_name: [str] 模块名称
        :return: [bool] 模块是否启用
        """
        status = config.getConfig(f"ErisPulse.modules.status.{module_name}")
        
        if status is None:
            return False
        
        if isinstance(status, str):
            return status.lower() not in ('false', '0', 'no', 'off')
        
        return bool(status)
    
    def enable(self, module_name: str) -> bool:
        """
        启用模块
        
        :param module_name: [str] 模块名称
        :return: [bool] 操作是否成功
        """
        config.setConfig(f"ErisPulse.modules.status.{module_name}", True)
        logger.info(f"模块 {module_name} 已启用")
        return True
    
    def disable(self, module_name: str) -> bool:
        """
        禁用模块
        
        :param module_name: [str] 模块名称
        :return: [bool] 操作是否成功
        """
        config.setConfig(f"ErisPulse.modules.status.{module_name}", False)
        logger.info(f"模块 {module_name} 已禁用")
        
        if module_name in self._modules:
            del self._modules[module_name]
        self._loaded_modules.discard(module_name)
        return True
    
    def list_modules(self) -> Dict[str, bool]:
        """
        列出所有模块状态
        
        :return: [Dict[str, bool]] 模块状态字典
        """
        return config.getConfig("ErisPulse.modules.status", {})
    
    # ==================== 工具方法 ====================
    
    def __getattr__(self, module_name: str) -> Any:
        """
        通过属性访问获取模块实例
        
        :param module_name: [str] 模块名称
        :return: [Any] 模块实例
        :raises AttributeError: 当模块不存在或未启用时
        """
        module_instance = self.get(module_name)
        if module_instance is None:
            raise AttributeError(f"模块 {module_name} 不存在或未启用")
        return module_instance
    
    def __contains__(self, module_name: str) -> bool:
        """
        检查模块是否存在且处于启用状态
        
        :param module_name: [str] 模块名称
        :return: [bool] 模块是否存在且启用
        """
        return self.exists(module_name) and self.is_enabled(module_name)

module = ModuleManager()

__all__ = [
    "module"
]