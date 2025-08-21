from typing import Any, Dict
from .logger import logger
from .config import config

class ModuleManager:
    """
    模块管理器
    
    提供便捷的模块访问接口，支持获取模块实例、检查模块状态等操作
    使用 config 模块存储模块状态
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
            
        # 模块是否启用
        if not self.is_enabled(module_name):
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
        module_statuses = config.getConfig("ErisPulse.modules.status", {})
        return module_name in module_statuses
    
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
        return True
    
    def _config_register(self, module_name: str, enabled: bool = False) -> bool:
        """
        注册新模块信息
        
        :param module_name: [str] 模块名称
        :param enabled: [bool] 是否启用模块
        :return: [bool] 操作是否成功
        """
        config.setConfig(f"ErisPulse.modules.status.{module_name}", enabled)
        status = "启用" if enabled else "禁用"
        logger.info(f"模块 {module_name} 已注册并{status}")
        return True
    
    def list_modules(self) -> Dict[str, bool]:
        """
        列出所有模块状态
        
        :return: [Dict[str, bool]] 模块状态字典
        """
        return config.getConfig("ErisPulse.modules.status", {})
    
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