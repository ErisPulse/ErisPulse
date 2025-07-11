"""
ErisPulse 模块管理器

提供模块的注册、状态管理和依赖关系处理功能。支持模块的启用/禁用、版本控制和依赖解析。

{!--< tips >!--}
1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系
{!--< /tips >!--}
"""

import json
from typing import Dict, Optional, Any, List, Set, Tuple, Union, Type, FrozenSet

class ModuleManager:
    """
    模块管理器
    
    管理所有模块的注册、状态和依赖关系
    
    {!--< tips >!--}
    1. 通过set_module/get_module管理模块信息
    2. 通过set_module_status/get_module_status控制模块状态
    3. 通过set_all_modules/get_all_modules批量操作模块
    {!--< /tips >!--}
    """
    
    DEFAULT_MODULE_PREFIX = "erispulse.module.data:"
    DEFAULT_STATUS_PREFIX = "erispulse.module.status:"

    def __init__(self):
        from .env import env
        self.env = env
        self._ensure_prefixes()

    def _ensure_prefixes(self) -> None:
        """
        {!--< internal-use >!--}
        确保模块前缀配置存在
        """
        if not self.env.get("erispulse.system.module_prefix"):
            self.env.set("erispulse.system.module_prefix", self.DEFAULT_MODULE_PREFIX)
        if not self.env.get("erispulse.system.status_prefix"):
            self.env.set("erispulse.system.status_prefix", self.DEFAULT_STATUS_PREFIX)

    @property
    def module_prefix(self) -> str:
        """
        获取模块数据前缀
        
        :return: 模块数据前缀字符串
        """
        return self.env.get("erispulse.system.module_prefix")

    @property
    def status_prefix(self) -> str:
        """
        获取模块状态前缀
        
        :return: 模块状态前缀字符串
        """
        return self.env.get("erispulse.system.status_prefix")

    def set_module_status(self, module_name: str, status: bool) -> None:
        """
        设置模块启用状态
        
        :param module_name: 模块名称
        :param status: 启用状态
        
        :example:
        >>> # 启用模块
        >>> mods.set_module_status("MyModule", True)
        >>> # 禁用模块
        >>> mods.set_module_status("MyModule", False)
        """
        self.env.set(f"{self.status_prefix}{module_name}", bool(status))

        module_info = self.get_module(module_name)
        if module_info:
            module_info["status"] = bool(status)
            self.env.set(f"{self.module_prefix}{module_name}", module_info)

    def get_module_status(self, module_name: str) -> bool:
        """
        获取模块启用状态
        
        :param module_name: 模块名称
        :return: 模块是否启用
        
        :example:
        >>> if mods.get_module_status("MyModule"):
        >>>     print("模块已启用")
        """
        status = self.env.get(f"{self.status_prefix}{module_name}", True)
        if isinstance(status, str):
            return status.lower() == 'true'
        return bool(status)

    def set_module(self, module_name: str, module_info: Dict[str, Any]) -> None:
        """
        设置模块信息
        
        :param module_name: 模块名称
        :param module_info: 模块信息字典
        
        :example:
        >>> mods.set_module("MyModule", {
        >>>     "version": "1.0.0",
        >>>     "description": "我的模块",
        >>>     "status": True
        >>> })
        """
        self.env.set(f"{self.module_prefix}{module_name}", module_info)
        self.set_module_status(module_name, module_info.get('status', True))

    def get_module(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模块信息
        
        :param module_name: 模块名称
        :return: 模块信息字典或None
        
        :example:
        >>> module_info = mods.get_module("MyModule")
        >>> if module_info:
        >>>     print(f"模块版本: {module_info.get('version')}")
        """
        return self.env.get(f"{self.module_prefix}{module_name}")

    def set_all_modules(self, modules_info: Dict[str, Dict[str, Any]]) -> None:
        """
        批量设置多个模块信息
        
        :param modules_info: 模块信息字典
        
        :example:
        >>> mods.set_all_modules({
        >>>     "Module1": {"version": "1.0", "status": True},
        >>>     "Module2": {"version": "2.0", "status": False}
        >>> })
        """
        for module_name, module_info in modules_info.items():
            self.set_module(module_name, module_info)

    def get_all_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有模块信息
        
        :return: 模块信息字典
        
        :example:
        >>> all_modules = mods.get_all_modules()
        >>> for name, info in all_modules.items():
        >>>     print(f"{name}: {info.get('status')}")
        """
        modules_info = {}
        all_keys = self.env.get_all_keys()
        prefix_len = len(self.module_prefix)

        for key in all_keys:
            if key.startswith(self.module_prefix):
                module_name = key[prefix_len:]
                module_info = self.get_module(module_name)
                if module_info:
                    status = self.get_module_status(module_name)
                    module_info['status'] = bool(status)
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
        移除模块
        
        :param module_name: 模块名称
        :return: 是否成功移除
        
        :example:
        >>> if mods.remove_module("OldModule"):
        >>>     print("模块已移除")
        """
        module_key = f"{self.module_prefix}{module_name}"
        status_key = f"{self.status_prefix}{module_name}"

        if self.env.get(module_key) is not None:
            self.env.delete(module_key)
            self.env.delete(status_key)
            return True
        return False

    def update_prefixes(self, module_prefix: Optional[str] = None, status_prefix: Optional[str] = None) -> None:
        """
        更新模块前缀配置
        
        :param module_prefix: 新的模块数据前缀(可选)
        :param status_prefix: 新的模块状态前缀(可选)
        
        :example:
        >>> # 更新模块前缀
        >>> mods.update_prefixes(
        >>>     module_prefix="custom.module.data:",
        >>>     status_prefix="custom.module.status:"
        >>> )
        """
        if module_prefix:
            if not module_prefix.endswith(':'):
                module_prefix += ':'
            self.env.set("erispulse.system.module_prefix", module_prefix)

        if status_prefix:
            if not status_prefix.endswith(':'):
                status_prefix += ':'
            self.env.set("erispulse.system.status_prefix", status_prefix)


mods = ModuleManager()
