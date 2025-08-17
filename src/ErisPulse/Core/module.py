"""
ErisPulse 模块管理模块

提供便捷的模块访问接口
"""

from typing import Any, Optional, Dict
from .module_registry import module_registry
from .logger import logger

class ModuleManager:
    """
    模块管理器
    
    提供便捷的模块访问接口，支持获取模块实例、检查模块状态等操作
    """
    
    def __init__(self):
        self._modules = {}
    
    def get(self, module_name: str) -> Any:
        """
        获取指定模块的实例
        
        :param module_name: [str] 模块名称
        :return: [Any] 模块实例或None
        """
        # 是否已缓存
        if module_name in self._modules:
            return self._modules[module_name]
            
        # 从模块注册表获取模块信息
        module_info = module_registry.get_module(module_name)
        if not module_info:
            logger.warning(f"模块 {module_name} 未注册")
            return None
            
        # 模块是否启用
        if not module_registry.get_module_status(module_name):
            logger.warning(f"模块 {module_name} 已禁用")
            return None
            
        try:
            from .. import sdk
            if hasattr(sdk, module_name):
                module_instance = getattr(sdk, module_name)
                self._modules[module_name] = module_instance
                return module_instance
            else:
                logger.warning(f"模块 {module_name} 实例未找到")
                return None
        except Exception as e:
            logger.error(f"获取模块 {module_name} 实例时出错: {e}")
            return None
    
    def exists(self, module_name: str) -> bool:
        """
        检查模块是否存在
        
        :param module_name: [str] 模块名称
        :return: [bool] 模块是否存在
        """
        return module_registry.get_module(module_name) is not None
    
    def is_enabled(self, module_name: str) -> bool:
        """
        检查模块是否启用
        
        :param module_name: [str] 模块名称
        :return: [bool] 模块是否启用
        """
        return module_registry.get_module_status(module_name)
    
    def enable(self, module_name: str) -> bool:
        """
        启用模块
        
        :param module_name: [str] 模块名称
        :return: [bool] 操作是否成功
        """
        if not self.exists(module_name):
            logger.error(f"模块 {module_name} 不存在")
            return False
            
        module_registry.set_module_status(module_name, True)
        logger.info(f"模块 {module_name} 已启用")
        return True
    
    def disable(self, module_name: str) -> bool:
        """
        禁用模块
        
        :param module_name: [str] 模块名称
        :return: [bool] 操作是否成功
        """
        if not self.exists(module_name):
            logger.error(f"模块 {module_name} 不存在")
            return False
            
        module_registry.set_module_status(module_name, False)
        logger.info(f"模块 {module_name} 已禁用")
        # 如果模块在缓存中，移除它
        if module_name in self._modules:
            del self._modules[module_name]
        return True
    
    def list_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有模块信息
        
        :return: [Dict[str, Dict[str, Any]]] 模块信息字典
        """
        return module_registry.get_all_modules()
    
    def get_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模块详细信息
        
        :param module_name: [str] 模块名称
        :return: [Optional[Dict[str, Any]]] 模块信息字典
        """
        return module_registry.get_module(module_name)
    
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