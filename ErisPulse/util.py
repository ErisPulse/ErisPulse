import time
import asyncio
import functools
import traceback
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque

executor = ThreadPoolExecutor()

def topological_sort(elements, dependencies, error):
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
        from . import sdk
        sdk.logger.error(f"Topological sort failed: {sorted_list} vs {elements}")
    return sorted_list

def ExecAsync(async_func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(executor, lambda: asyncio.run(async_func(*args, **kwargs)))

def cache(func):
    cache_dict = {}
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        if key not in cache_dict:
            cache_dict[key] = func(*args, **kwargs)
        return cache_dict[key]
    return wrapper

def run_in_executor(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        except Exception as e:
            from . import sdk
            sdk.logger.error(f"线程内发生未处理异常:\n{''.join(traceback.format_exc())}")
            sdk.raiserr.CaughtExternalError(
                f"检测到线程内异常，请优先使用 sdk.raiserr 抛出错误。\n原始异常: {type(e).__name__}: {e}"
            )
    return wrapper

def retry(max_attempts=3, delay=1):
    def decorator(func):
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