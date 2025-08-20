"""
ErisPulse 模块管理器

提供模块的注册、状态管理和依赖关系处理功能。支持模块的启用/禁用、版本控制和依赖解析。

{!--< tips >!--}
1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系
{!--< /tips >!--}
"""

from typing import Dict, Optional, Any

class ModuleRegistry:
    """
    ErisPulse 模块注册表
    
    管理所有模块的注册信息和启用状态
    
    {!--< tips >!--}
    1. 模块信息通过 set_module/get_module 管理
    2. 模块状态通过 set_module_status/get_module_status 控制
    3. 支持批量操作模块信息
    {!--< /tips >!--}
    """
    
    DEFAULT_MODULE_PREFIX = "erispulse.data.modules.info:"
    DEFAULT_STATUS_PREFIX = "erispulse.data.modules.status:"

    def __init__(self):
        from .storage import storage
        self.storage = storage
        self._ensure_prefixes()

    def _ensure_prefixes(self) -> None:
        """
        {!--< internal-use >!--}
        确保模块前缀配置存在
        """
        if not self.storage.get("erispulse.system.module_prefix"):
            self.storage.set("erispulse.system.module_prefix", self.DEFAULT_MODULE_PREFIX)
        if not self.storage.get("erispulse.system.status_prefix"):
            self.storage.set("erispulse.system.status_prefix", self.DEFAULT_STATUS_PREFIX)

    @property
    def module_prefix(self) -> str:
        """
        获取模块数据前缀
        
        :return: 模块数据前缀字符串
        """
        return self.storage.get("erispulse.system.module_prefix")

    @property
    def status_prefix(self) -> str:
        """
        获取模块状态前缀
        
        :return: 模块状态前缀字符串
        """
        return self.storage.get("erispulse.system.status_prefix")

    def set_module_status(self, module_name: str, status: bool) -> None:
        """
        设置模块启用状态
        
        :param module_name: [str] 模块名称
        :param status: [bool] 启用状态 (True=启用, False=禁用)
        
        :example:
        >>> # 启用模块
        >>> module_registry.set_module_status("MyModule", True)
        >>> # 禁用模块
        >>> module_registry.set_module_status("MyModule", False)
        """
        from .logger import logger
        self.storage.set(f"{self.status_prefix}{module_name}", bool(status))
        logger.debug(f"模块 {module_name} 状态已设置为 {status}")

    def get_module_status(self, module_name: str) -> bool:
        """
        获取模块启用状态
        
        :param module_name: [str] 模块名称
        :return: [bool] 模块是否启用
        
        :example:
        >>> if module_registry.get_module_status("MyModule"):
        >>>     print("模块已启用")
        """
        status = self.storage.get(f"{self.status_prefix}{module_name}", True)
        if isinstance(status, str):
            return status.lower() not in ('false', '0', 'no', 'off')
        return bool(status)

    def set_module(self, module_name: str, module_info: Dict[str, Any]) -> None:
        """
        注册或更新模块信息
        
        :param module_name: [str] 模块名称
        :param module_info: [Dict[str, Any]] 模块信息字典
            必须包含 version 和 description 字段
        
        :example:
        >>> module_registry.set_module("MyModule", {
        >>>     "version": "1.0.0",
        >>>     "description": "我的模块",
        >>>     "dependencies": [],
        >>>     "author": "开发者",
        >>>     "license": "MIT"
        >>> })
        """
        self.storage.set(f"{self.module_prefix}{module_name}", module_info)

    def get_module(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模块信息
        
        :param module_name: [str] 模块名称
        :return: [Optional[Dict[str, Any]]] 模块信息字典或None
        
        :example:
        >>> module_info = module_registry.get_module("MyModule")
        >>> if module_info:
        >>>     print(f"模块版本: {module_info.get('version')}")
        """
        return self.storage.get(f"{self.module_prefix}{module_name}")

    def set_all_modules(self, modules_info: Dict[str, Dict[str, Any]]) -> None:
        """
        批量设置模块信息
        
        :param modules_info: [Dict[str, Dict[str, Any]]] 模块信息字典
            格式: {模块名: 模块信息}
        
        :example:
        >>> module_registry.set_all_modules({
        >>>     "Module1": {"version": "1.0", "status": True},
        >>>     "Module2": {"version": "2.0", "status": False}
        >>> })
        """
        for module_name, module_info in modules_info.items():
            self.set_module(module_name, module_info)

    def get_all_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有已注册模块信息
        
        :return: [Dict[str, Dict[str, Any]]] 所有模块信息字典
        
        :example:
        >>> all_modules = module_registry.get_all_modules()
        >>> for name, info in all_modules.items():
        >>>     print(f"{name}: {info.get('status')}")
        """
        modules_info = {}
        all_keys = self.storage.get_all_keys()
        prefix_len = len(self.module_prefix)

        for key in all_keys:
            if key.startswith(self.module_prefix):
                module_name = key[prefix_len:]
                module_info = self.get_module(module_name)
                if module_info:
                    modules_info[module_name] = module_info
        return modules_info

    def update_module(self, module_name: str, module_info: Dict[str, Any]) -> None:
        """
        更新模块信息
        
        :param module_name: 模块名称
        :param module_info: 完整的模块信息字典
        """
        self.set_module(module_name, module_info)

    def remove_module(self, module_name: str) -> bool:
        """
        移除模块注册信息
        
        :param module_name: [str] 模块名称
        :return: [bool] 是否成功移除
        
        :example:
        >>> if module_registry.remove_module("OldModule"):
        >>>     print("模块已移除")
        """
        module_key = f"{self.module_prefix}{module_name}"
        status_key = f"{self.status_prefix}{module_name}"

        if self.storage.get(module_key) is not None:
            self.storage.delete(module_key)
            self.storage.delete(status_key)
            return True
        return False

    def update_prefixes(self, module_prefix: Optional[str] = None, status_prefix: Optional[str] = None) -> None:
        """
        更新模块存储前缀配置
        
        :param module_prefix: [Optional[str]] 模块数据前缀 (默认: "erispulse.data.modules.info:")
        :param status_prefix: [Optional[str]] 模块状态前缀 (默认: "erispulse.data.modules.status:")
        
        :example:
        >>> # 更新模块前缀
        >>> module_registry.update_prefixes(
        >>>     module_prefix="custom.module.data:",
        >>>     status_prefix="custom.module.status:"
        >>> )
        """
        if module_prefix:
            if not module_prefix.endswith(':'):
                module_prefix += ':'
            self.storage.set("erispulse.system.module_prefix", module_prefix)

        if status_prefix:
            if not status_prefix.endswith(':'):
                status_prefix += ':'
            self.storage.set("erispulse.system.status_prefix", status_prefix)


module_registry = ModuleRegistry()

__all__ = [
    "module_registry",
]
