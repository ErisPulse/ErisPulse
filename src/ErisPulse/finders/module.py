"""
ErisPulse 模块发现器

专门用于发现和查找 ErisPulse 模块的 entry-points

{!--< tips >!--}
1. 查找 erispulse.module 组的 entry-points
2. 支持缓存机制，避免重复查询
3. 提供便捷的查询接口
{!--< /tips >!--}
"""

from typing import List, Optional, Any, Dict
from .bases.finder import BaseFinder


class ModuleFinder(BaseFinder):
    """
    模块发现器
    
    负责发现 ErisPulse 模块的 entry-points
    
    {!--< tips >!--}
    使用方式：
    >>> finder = ModuleFinder()
    >>> # 查找所有模块
    >>> modules = finder.find_all()
    >>> # 按名称查找
    >>> module = finder.find_by_name("my_module")
    >>> # 获取模块映射
    >>> module_map = finder.get_entry_point_map()
    >>> # 检查模块是否存在
    >>> if "my_module" in finder:
    ...     print("模块存在")
    {!--< /tips >!--}
    """
    
    def _get_entry_point_group(self) -> str:
        """
        获取 entry-point 组名
        
        :return: "erispulse.module"
        """
        return "erispulse.module"
    
    def get_all_names(self) -> List[str]:
        """
        获取所有模块名称
        
        :return: 模块名称列表
        """
        return list(self.get_entry_point_map().keys())
    
    def get_all_packages(self) -> List[str]:
        """
        获取所有模块所属的 PyPI 包名
        
        :return: PyPI 包名列表
        """
        packages = set()
        for entry in self.find_all():
            if hasattr(entry, 'dist') and entry.dist:
                packages.add(entry.dist.name)
        return list(packages)
    
    def get_package_for_module(self, module_name: str) -> Optional[str]:
        """
        获取指定模块所属的 PyPI 包名
        
        :param module_name: 模块名称
        :return: PyPI 包名，未找到返回 None
        """
        entry = self.find_by_name(module_name)
        if entry and hasattr(entry, 'dist') and entry.dist:
            return entry.dist.name
        return None
    
    def get_module_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模块的完整信息
        
        :param module_name: 模块名称
        :return: 模块信息字典，未找到返回 None
        
        :return:
            Dict: {
                "name": 模块名称,
                "package": PyPI 包名,
                "version": 版本号,
                "entry_point": entry-point 对象
            }
        """
        entry = self.find_by_name(module_name)
        if not entry:
            return None
        
        info = {
            "name": entry.name,
            "entry_point": entry
        }
        
        if hasattr(entry, 'dist') and entry.dist:
            info["package"] = entry.dist.name
            info["version"] = entry.dist.version
        
        return info
    
    def get_modules_by_package(self, package_name: str) -> List[str]:
        """
        获取指定 PyPI 包下的所有模块名称
        
        :param package_name: PyPI 包名
        :return: 模块名称列表
        """
        modules = []
        for entry in self.find_all():
            if hasattr(entry, 'dist') and entry.dist:
                if entry.dist.name == package_name:
                    modules.append(entry.name)
        return modules
