# `ErisPulse/Core/util` 模块

ErisPulse 工具函数集合

提供常用工具函数，包括拓扑排序、缓存装饰器、异步执行等实用功能。

> **提示**：
1. 使用@cache装饰器缓存函数结果
2. 使用@run_in_executor在独立线程中运行同步函数
3. 使用@retry实现自动重试机制

## 类

### `Util`

工具函数集合

提供各种实用功能，简化开发流程

> **提示**：
1. 拓扑排序用于解决依赖关系
2. 装饰器简化常见模式实现
3. 异步执行提升性能


#### 方法

##### `ExecAsync`

异步执行函数

:param async_func: 异步函数
:param args: 位置参数
:param kwargs: 关键字参数
:return: 函数执行结果

:example:
>>> result = util.ExecAsync(my_async_func, arg1, arg2)


##### `cache`

缓存装饰器

:param func: 被装饰函数
:return: 装饰后的函数

:example:
>>> @util.cache
>>> def expensive_operation(param):
>>>     return heavy_computation(param)


##### `run_in_executor`

在独立线程中执行同步函数的装饰器

:param func: 被装饰的同步函数
:return: 可等待的协程函数

:example:
>>> @util.run_in_executor
>>> def blocking_io():
>>>     # 执行阻塞IO操作
>>>     return result


##### `retry`

自动重试装饰器

:param max_attempts: 最大重试次数 (默认: 3)
:param delay: 重试间隔(秒) (默认: 1)
:return: 装饰器函数

:example:
>>> @util.retry(max_attempts=5, delay=2)
>>> def unreliable_operation():
>>>     # 可能失败的操作

