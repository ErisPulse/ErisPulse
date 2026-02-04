"""
ErisPulse 基础发现器

定义发现器的抽象基类，提供通用的发现器接口和结构

{!--< tips >!--}
1. 所有具体发现器应继承自 BaseFinder
2. 子类需实现 _get_entry_point_group 方法
3. 支持缓存机制，避免重复查询
{!--< /tips >!--}
"""

import importlib.metadata
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Iterator
from ...Core.logger import logger


class BaseFinder(ABC):
    """
    基础发现器抽象类
    
    提供通用的发现器接口和缓存功能
    
    {!--< tips >!--}
    子类需要实现：
    - _get_entry_point_group: 返回 entry-point 组名
    {!--< /tips >!--}
    
    {!--< internal-use >!--}
    此类仅供内部使用，不应直接实例化
    {!--< /internal-use >!--}
    """
    
    def __init__(self):
        """初始化基础发现器"""
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[float] = None
        self._cache_expiry: int = 60  # 缓存有效期60秒
    
    @abstractmethod
    def _get_entry_point_group(self) -> str:
        """
        获取 entry-point 组名
        
        :return: entry-point 组名
        
        {!--< internal-use >!--}
        子类必须实现此方法
        {!--< /internal-use >!--}
        """
        pass
    
    def _get_entry_points(self) -> List[Any]:
        """
        获取所有 entry-points
        
        :return: entry-point 对象列表
        
        {!--< internal-use >!--}
        内部方法，使用缓存机制获取 entry-points
        {!--< /internal-use >!--}
        """
        import time
        
        group_name = self._get_entry_point_group()
        
        # 检查缓存
        if self._cache is not None and self._cache_time is not None:
            if time.time() - self._cache_time < self._cache_expiry:
                return list(self._cache.values())
        
        logger.debug(f"正在从 entry-points 查找 {group_name}...")
        
        try:
            # 加载 entry-points
            entry_points = importlib.metadata.entry_points()
            
            if hasattr(entry_points, 'select'):
                entries = list(entry_points.select(group=group_name))
            else:
                entries = list(entry_points.get(group_name, []))  # type: ignore[attr-defined]
            
            # 更新缓存
            self._cache = {entry.name: entry for entry in entries}
            self._cache_time = time.time()
            
            logger.debug(f"找到 {len(entries)} 个 {group_name} entry-points")
            
            return entries
            
        except Exception as e:
            logger.error(f"查找 {group_name} entry-points 失败: {e}")
            return []
    
    def find_all(self) -> List[Any]:
        """
        查找所有 entry-points
        
        :return: entry-point 对象列表
        """
        return self._get_entry_points()
    
    def find_by_name(self, name: str) -> Optional[Any]:
        """
        按名称查找 entry-point
        
        :param name: entry-point 名称
        :return: entry-point 对象，未找到返回 None
        """
        # 确保缓存已加载
        if self._cache is None:
            self._get_entry_points()
        
        return self._cache.get(name) if self._cache else None
    
    def get_entry_point_map(self) -> Dict[str, Any]:
        """
        获取 entry-point 映射字典
        
        :return: {name: entry_point} 字典
        """
        # 确保缓存已加载
        if self._cache is None:
            self._get_entry_points()
        
        return self._cache.copy() if self._cache else {}
    
    def get_group_name(self) -> str:
        """
        获取 entry-point 组名
        
        :return: entry-point 组名
        """
        return self._get_entry_point_group()
    
    def clear_cache(self) -> None:
        """
        清除缓存
        
        {!--< tips >!--}
        当安装/卸载包后调用此方法清除缓存
        {!--< /tips >!--}
        """
        self._cache = None
        self._cache_time = None
        logger.debug("发现器缓存已清除")
    
    def set_cache_expiry(self, expiry: int) -> None:
        """
        设置缓存过期时间
        
        :param expiry: 过期时间（秒）
        
        {!--< internal-use >!--}
        内部方法，用于调整缓存策略
        {!--< /internal-use >!--}
        """
        self._cache_expiry = expiry
    
    def __iter__(self) -> Iterator[Any]:
        """
        迭代器接口
        
        :return: entry-point 迭代器
        """
        return iter(self._get_entry_points())
    
    def __len__(self) -> int:
        """
        返回 entry-point 数量
        
        :return: entry-point 数量
        """
        return len(self._get_entry_points())
    
    def __contains__(self, name: str) -> bool:
        """
        检查 entry-point 是否存在
        
        :param name: entry-point 名称
        :return: 是否存在
        """
        return self.find_by_name(name) is not None
    
    def __repr__(self) -> str:
        """
        返回发现器的字符串表示
        
        :return: 字符串表示
        """
        return f"{self.__class__.__name__}(group='{self._get_entry_point_group()}')"
