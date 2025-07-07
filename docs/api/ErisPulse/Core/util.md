# util

> 💡 **Note**: 1. 使用@cache装饰器缓存函数结果
2. 使用@run_in_executor在独立线程中运行同步函数
3. 使用@retry实现自动重试机制

ErisPulse 工具函数集合

提供常用工具函数，包括拓扑排序、缓存装饰器、异步执行等实用功能。


1. 使用@cache装饰器缓存函数结果
2. 使用@run_in_executor在独立线程中运行同步函数
3. 使用@retry实现自动重试机制


### `topological_sort(self, elements: List[str], dependencies: Dict[str, List[str]], error: Type[Exception]) -> List[str]`



**Description**  
拓扑排序依赖关系

**Parameters**  
- `self`
- `elements` (List[str]): 元素列表
- `dependencies` (Dict[str): 依赖关系字典
- `List[str]]`
- `error` (Type[Exception]): 错误类型(当发现循环依赖时抛出)

**Returns**

- Type: `List[str]`
- Description: 排序后的元素列表

**Raises**

- `error`: 当发现循环依赖时抛出

### `show_topology(self) -> str`



**Description**  
可视化模块依赖关系
        
        :return: 依赖关系字符串表示
        
        :example:
        >>> print(util.show_topology())

**Parameters**  
- `self`

**Returns**

- Type: `str`
- Description: 依赖关系字符串表示

### `ExecAsync(self, async_func: Callable, *args: Any, **kwargs: Any) -> Any`



**Description**  
异步执行函数

**Parameters**  
- `self`
- `async_func` (Callable): 异步函数
- `*args` (Any)
- `**kwargs` (Any)

**Returns**

- Type: `Any`
- Description: 函数执行结果

### `cache(self, func: Callable) -> Callable`



**Description**  
缓存装饰器

**Parameters**  
- `self`
- `func` (Callable): 被装饰函数

**Returns**

- Type: `Callable`
- Description: 装饰后的函数

### `wrapper(*args, **kwargs): key = (args, tuple(sorted(kwargs.items())))
            if key not in cache_dict: cache_dict[key] = func(*args, **kwargs)
            return cache_dict[key]
        return wrapper

    def run_in_executor(self, func: Callable) -> Callable`



**Description**  
在独立线程中执行同步函数的装饰器

**Parameters**  
- `*args, **kwargs)` (key) [optional, default: (args]
- `tuple(sorted(kwargs.items())))
            if key not in cache_dict` (cache_dict[key]) [optional, default: func(*args, **kwargs)
            return cache_dict[key]
        return wrapper

    def run_in_executor(self]
- `func` (Callable): 被装饰的同步函数

**Returns**

- Type: `Callable`
- Description: 可等待的协程函数

### `wrapper(*args, **kwargs): loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
            except Exception as e:
                from . import logger, raiserr
                logger.error(f"线程内发生未处理异常: \n{''.join(traceback.format_exc())}")
                raiserr.CaughtExternalError(
                    f"检测到线程内异常，请优先使用 sdk.raiserr 抛出错误。\n原始异常: {type(e).__name__}: {e}"
                )
        return wrapper

    def retry(self, max_attempts: int = 3, delay: int = 1) -> Callable`



**Description**  
自动重试装饰器

**Parameters**  
- `*args, **kwargs)` (loop) [optional, default: asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(None]
- `lambda` (func(*args, **kwargs))
            except Exception as e:
                from . import logger)
- `raiserr
                logger.error(f"线程内发生未处理异常` (\n{''.join(traceback.format_exc())}")
                raiserr.CaughtExternalError(
                    f"检测到线程内异常，请优先使用 sdk.raiserr 抛出错误。\n原始异常: {type(e).__name__}: {e}"
                )
        return wrapper

    def retry(self)
- `max_attempts` (int) [optional, default: 3]: 3)
- `delay` (int) [optional, default: 1]: 1)

**Returns**

- Type: `Callable`
- Description: 装饰器函数

