"""
ErisPulse 适配器发现器

专门用于发现和查找 ErisPulse 适配器的 entry-points

{!--< tips >!--}
1. 查找 erispulse.adapter 组的 entry-points
2. 支持缓存机制，避免重复查询
3. 提供便捷的查询接口
{!--< /tips >!--}
"""

from typing import List, Optional, Any, Dict
from .bases.finder import BaseFinder


class AdapterFinder(BaseFinder):
    """
    适配器发现器
    
    负责发现 ErisPulse 适配器的 entry-points
    
    {!--< tips >!--}
    使用方式：
    >>> finder = AdapterFinder()
    >>> # 查找所有适配器
    >>> adapters = finder.find_all()
    >>> # 按名称查找
    >>> adapter = finder.find_by_name("my_adapter")
    >>> # 获取适配器映射
    >>> adapter_map = finder.get_entry_point_map()
    >>> # 检查适配器是否存在
    >>> if "my_adapter" in finder:
    ...     print("适配器存在")
    {!--< /tips >!--}
    """
    
    def _get_entry_point_group(self) -> str:
        """
        获取 entry-point 组名
        
        :return: "erispulse.adapter"
        """
        return "erispulse.adapter"
    
    def get_all_names(self) -> List[str]:
        """
        获取所有适配器名称
        
        :return: 适配器名称列表
        """
        return list(self.get_entry_point_map().keys())
    
    def get_all_packages(self) -> List[str]:
        """
        获取所有适配器所属的 PyPI 包名
        
        :return: PyPI 包名列表
        """
        packages = set()
        for entry in self.find_all():
            if hasattr(entry, 'dist') and entry.dist:
                packages.add(entry.dist.name)
        return list(packages)
    
    def get_package_for_adapter(self, adapter_name: str) -> Optional[str]:
        """
        获取指定适配器所属的 PyPI 包名
        
        :param adapter_name: 适配器名称
        :return: PyPI 包名，未找到返回 None
        """
        entry = self.find_by_name(adapter_name)
        if entry and hasattr(entry, 'dist') and entry.dist:
            return entry.dist.name
        return None
    
    def get_adapter_info(self, adapter_name: str) -> Optional[Dict[str, Any]]:
        """
        获取适配器的完整信息
        
        :param adapter_name: 适配器名称
        :return: 适配器信息字典，未找到返回 None
        
        :return:
            Dict: {
                "name": 适配器名称,
                "package": PyPI 包名,
                "version": 版本号,
                "entry_point": entry-point 对象
            }
        """
        entry = self.find_by_name(adapter_name)
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
    
    def get_adapters_by_package(self, package_name: str) -> List[str]:
        """
        获取指定 PyPI 包下的所有适配器名称
        
        :param package_name: PyPI 包名
        :return: 适配器名称列表
        """
        adapters = []
        for entry in self.find_all():
            if hasattr(entry, 'dist') and entry.dist:
                if entry.dist.name == package_name:
                    adapters.append(entry.name)
        return adapters
