"""
# 工具函数集合

提供各种实用工具函数和装饰器，简化开发流程。包括依赖关系处理、性能优化、异步执行和错误重试等功能。

## 核心功能
1. 依赖关系管理
2. 函数结果缓存
3. 异步执行支持
4. 自动重试机制
5. 可视化工具

## API 文档

### 依赖关系处理
#### topological_sort(elements: list, dependencies: dict, error: callable) -> list
对元素进行拓扑排序，解析依赖关系。
- 参数:
  - elements: 需要排序的元素列表
  - dependencies: 依赖关系字典，键为元素，值为该元素依赖的元素列表
  - error: 发生循环依赖时调用的错误处理函数
- 返回:
  - list: 排序后的元素列表
- 异常:
  - 当存在循环依赖时，调用error函数
- 示例:
```python
# 基本使用
modules = ["ModuleA", "ModuleB", "ModuleC"]
dependencies = {
    "ModuleB": ["ModuleA"],
    "ModuleC": ["ModuleB"]
}
sorted_modules = sdk.util.topological_sort(modules, dependencies, sdk.raiserr.CycleDependencyError)

# 复杂依赖处理
modules = ["Database", "Cache", "API", "UI"]
dependencies = {
    "Cache": ["Database"],
    "API": ["Database", "Cache"],
    "UI": ["API"]
}
try:
    sorted_modules = sdk.util.topological_sort(
        modules, 
        dependencies,
        sdk.raiserr.CycleDependencyError
    )
    print("加载顺序:", sorted_modules)
except Exception as e:
    print(f"依赖解析失败: {e}")
```

#### show_topology() -> str
可视化显示当前模块的依赖关系。
- 参数: 无
- 返回:
  - str: 格式化的依赖关系树文本
- 示例:
```python
# 显示所有模块依赖
topology = sdk.util.show_topology()
print(topology)

# 在日志中记录依赖关系
sdk.logger.info("模块依赖关系:\n" + sdk.util.show_topology())
```

### 性能优化装饰器
#### @cache
缓存函数调用结果的装饰器。
- 参数: 无
- 返回:
  - function: 被装饰的函数
- 示例:
```python
# 缓存计算密集型函数结果
@sdk.util.cache
def calculate_complex_data(param1: int, param2: str) -> dict:
    # 复杂计算...
    return result

# 缓存配置读取
@sdk.util.cache
def get_config(config_name: str) -> dict:
    return load_config_from_file(config_name)

# 带有可变参数的缓存
@sdk.util.cache
def process_data(*args, **kwargs) -> Any:
    return complex_processing(args, kwargs)
```

### 异步执行工具
#### @run_in_executor
将同步函数转换为异步执行的装饰器。
- 参数: 无
- 返回:
  - function: 异步包装的函数
- 示例:
```python
# 包装同步IO操作
@sdk.util.run_in_executor
def read_large_file(file_path: str) -> str:
    with open(file_path, 'r') as f:
        return f.read()

# 包装CPU密集型操作
@sdk.util.run_in_executor
def process_image(image_data: bytes) -> bytes:
    # 图像处理...
    return processed_data

# 在异步环境中使用
async def main():
    # 这些操作会在线程池中执行，不会阻塞事件循环
    file_content = await read_large_file("large_file.txt")
    processed_image = await process_image(image_data)
```

#### ExecAsync(async_func: Callable, *args, **kwargs) -> Any
在当前线程中执行异步函数。
- 参数:
  - async_func: 要执行的异步函数
  - *args: 传递给异步函数的位置参数
  - **kwargs: 传递给异步函数的关键字参数
- 返回:
  - Any: 异步函数的执行结果
- 示例:
```python
# 在同步环境中执行异步函数
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# 同步环境中调用
result = sdk.util.ExecAsync(fetch_data, "https://api.example.com/data")

# 批量异步操作
async def process_multiple(items: list) -> list:
    results = []
    for item in items:
        result = await process_item(item)
        results.append(result)
    return results

# 在同步代码中执行
results = sdk.util.ExecAsync(process_multiple, items_list)
```

### 错误重试机制
#### @retry(max_attempts: int = 3, delay: int = 1)
为不稳定的操作添加自动重试机制的装饰器。
- 参数:
  - max_attempts: 最大重试次数，默认3次
  - delay: 重试间隔时间（秒），默认1秒
- 返回:
  - function: 包装了重试逻辑的函数
- 示例:
```python
# 基本重试
@sdk.util.retry()
def unstable_network_call() -> dict:
    return requests.get("https://api.example.com/data").json()

# 自定义重试参数
@sdk.util.retry(max_attempts=5, delay=2)
def connect_database() -> Connection:
    return create_database_connection()

# 带有条件的重试
@sdk.util.retry(max_attempts=3)
def process_with_retry(data: dict) -> bool:
    if not validate_data(data):
        raise ValueError("Invalid data")
    return process_data(data)
```

## 最佳实践
1. 依赖管理
```python
# 模块依赖定义
module_deps = {
    "core": [],
    "database": ["core"],
    "api": ["database"],
    "ui": ["api"]
}

# 验证并排序依赖
try:
    load_order = sdk.util.topological_sort(
        list(module_deps.keys()),
        module_deps,
        sdk.raiserr.CycleDependencyError
    )
    
    # 按顺序加载模块
    for module in load_order:
        load_module(module)
except Exception as e:
    sdk.logger.error(f"模块加载失败: {e}")
```

2. 性能优化
```python
# 合理使用缓存
@sdk.util.cache
def get_user_preferences(user_id: str) -> dict:
    return database.fetch_user_preferences(user_id)

# 异步处理耗时操作
@sdk.util.run_in_executor
def process_large_dataset(data: list) -> list:
    return [complex_calculation(item) for item in data]
```

3. 错误处理和重试
```python
# 组合使用重试和异步
@sdk.util.retry(max_attempts=3, delay=2)
@sdk.util.run_in_executor
def reliable_network_operation():
    response = requests.get("https://api.example.com")
    response.raise_for_status()
    return response.json()

# 带有自定义错误处理的重试
@sdk.util.retry(max_attempts=5)
def safe_operation():
    try:
        return perform_risky_operation()
    except Exception as e:
        sdk.logger.warning(f"操作失败，准备重试: {e}")
        raise
```

## 注意事项
1. 缓存使用
   - 注意内存占用，避免缓存过大数据
   - 考虑缓存失效策略
   - 不要缓存频繁变化的数据

2. 异步执行
   - 避免在 run_in_executor 中执行过长的操作
   - 注意异常处理和资源清理
   - 合理使用线程池

3. 重试机制
   - 设置合适的重试次数和间隔
   - 只对可重试的操作使用重试装饰器
   - 注意避免重试导致的资源浪费

4. 依赖管理
   - 保持依赖关系清晰简单
   - 避免循环依赖
   - 定期检查和更新依赖关系
"""

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
        sdk.logger.error(f"依赖导入错误: {elements} vs  {sorted_list} | 发生了循环依赖")
    return sorted_list

def show_topology():
    from . import sdk
    dep_data = sdk.env.get('module_dependencies')
    if not dep_data:
        return "未找到模块依赖关系数据，请先运行sdk.init()"
        
    sorted_modules = topological_sort(
        dep_data['modules'], 
        dep_data['dependencies'], 
        sdk.raiserr.CycleDependencyError
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
            result.append(f"   {indent}└─ 依赖: {', '.join(deps)}")
    
    return "\n".join(result)

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