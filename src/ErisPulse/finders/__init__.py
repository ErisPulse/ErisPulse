"""
ErisPulse 发现器模块

提供模块、适配器和 CLI 扩展的发现功能

{!--< tips >!--}
1. 每个 Finder 专门负责一类资源的发现
2. 统一继承自 BaseFinder，接口一致
3. 支持缓存机制，避免重复查询
4. Loader 和 PackageManager 应使用这些 Finder 来发现资源
{!--< /tips >!--}
"""

from .bases.finder import BaseFinder
from .module import ModuleFinder
from .adapter import AdapterFinder
from .cli import CLIFinder

__all__ = [
    "BaseFinder",
    "ModuleFinder",
    "AdapterFinder",
    "CLIFinder",
]
