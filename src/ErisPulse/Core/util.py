"""
ErisPulse 工具函数集合

提供常用工具函数，包括拓扑排序、缓存装饰器、异步执行等实用功能。

{!--< tips >!--}
1. 使用@cache装饰器缓存函数结果
2. 使用@run_in_executor在独立线程中运行同步函数
3. 使用@retry实现自动重试机制
{!--< /tips >!--}
"""

import time
import asyncio
import functools
import traceback
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
from typing import List, Dict, Type, Callable, Any, Optional, Set

executor = ThreadPoolExecutor()

class Util:
    """
    工具函数集合
    
    提供各种实用功能，简化开发流程
    
    {!--< tips >!--}
    1. 拓扑排序用于解决依赖关系
    2. 装饰器简化常见模式实现
    3. 异步执行提升性能
    {!--< /tips >!--}
    """
    
    def topological_sort(self, elements: List[str], dependencies: Dict[str, List[str]], error: Type[Exception]) -> List[str]:
        """
        拓扑排序依赖关系
        
        :param elements: 元素列表
        :param dependencies: 依赖关系字典
        :param error: 错误类型(当发现循环依赖时抛出)
        :return: 排序后的元素列表
        
        :raises error: 当发现循环依赖时抛出
        
        :example:
        >>> sorted_modules = util.topological_sort(
        >>>     modules, 
        >>>     dependencies,
        >>>     raiserr.CycleDependencyError
        >>> )
        """
        graph = defaultdict(list)
        in_degree = {element: 0 for element in elements}
        for element, deps in dependencies.items():
            for dep in deps:
                graph[dep].append(element)
                in_degree[element] += 1
        queue = deque([element for element in elements if in_degree[element] == 0])
        sorted_list = []
        while queue:
            node = queue.popleft()
            sorted_list.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(sorted_list) != len(elements):
            from . import logger
            logger.error(f"依赖导入错误: {elements} vs  {sorted_list} | 发生了循环依赖")
        return sorted_list

    def show_topology(self) -> str:
        """
        可视化模块依赖关系
        
        :return: 依赖关系字符串表示
        
        :example:
        >>> print(util.show_topology())
        """
        from . import env, raiserr
        dep_data = env.get('module_dependencies')
        if not dep_data:
            return "未找到模块依赖关系数据，请先运行sdk.init()"
            
        sorted_modules = self.topological_sort(
            dep_data['modules'], 
            dep_data['dependencies'], 
            raiserr.CycleDependencyError
        )
        
        tree = {}
        for module in sorted_modules:
            tree[module] = dep_data['dependencies'].get(module, [])
        
        result = ["模块拓扑关系表:"]
        for i, module in enumerate(sorted_modules, 1):
            deps = dep_data['dependencies'].get(module, [])
            indent = "  " * (len(deps) if deps else 0)
            result.append(f"{i}. {indent}{module}")
            if deps:
                result.append(f"   {indent}└└─ 依赖: {', '.join(deps)}")
        
        return "\n".join(result)

    def ExecAsync(self, async_func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        异步执行函数
        
        :param async_func: 异步函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 函数执行结果
        
        :example:
        >>> result = util.ExecAsync(my_async_func, arg1, arg2)
        """
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(executor, lambda: asyncio.run(async_func(*args, **kwargs)))

    def cache(self, func: Callable) -> Callable:
        """
        缓存装饰器
        
        :param func: 被装饰函数
        :return: 装饰后的函数
        
        :example:
        >>> @util.cache
        >>> def expensive_operation(param):
        >>>     return heavy_computation(param)
        """
        cache_dict = {}
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key not in cache_dict:
                cache_dict[key] = func(*args, **kwargs)
            return cache_dict[key]
        return wrapper

    def run_in_executor(self, func: Callable) -> Callable:
        """
        在独立线程中执行同步函数的装饰器
        
        :param func: 被装饰的同步函数
        :return: 可等待的协程函数
        
        :example:
        >>> @util.run_in_executor
        >>> def blocking_io():
        >>>     # 执行阻塞IO操作
        >>>     return result
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
            except Exception as e:
                from . import logger, raiserr
                logger.error(f"线程内发生未处理异常:\n{''.join(traceback.format_exc())}")
                raiserr.CaughtExternalError(
                    f"检测到线程内异常，请优先使用 sdk.raiserr 抛出错误。\n原始异常: {type(e).__name__}: {e}"
                )
        return wrapper

    def retry(self, max_attempts: int = 3, delay: int = 1) -> Callable:
        """
        自动重试装饰器
        
        :param max_attempts: 最大重试次数 (默认: 3)
        :param delay: 重试间隔(秒) (默认: 1)
        :return: 装饰器函数
        
        :example:
        >>> @util.retry(max_attempts=5, delay=2)
        >>> def unreliable_operation():
        >>>     # 可能失败的操作
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                attempts = 0
                while attempts < max_attempts:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        attempts += 1
                        if attempts == max_attempts:
                            raise
                        time.sleep(delay)
            return wrapper
        return decorator


util = Util()
