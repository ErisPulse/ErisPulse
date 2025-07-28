# 📦 `ErisPulse.Core.util` 模块

<sup>自动生成于 2025-07-28 05:47:33</sup>

---

## 模块概述


ErisPulse 工具函数集合

提供常用工具函数，包括拓扑排序、缓存装饰器、异步执行等实用功能。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用@cache装饰器缓存函数结果
2. 使用@run_in_executor在独立线程中运行同步函数
3. 使用@retry实现自动重试机制</p></div>

---

## 🏛️ 类

### `class Util`

工具函数集合

提供各种实用功能，简化开发流程

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 拓扑排序用于解决依赖关系
2. 装饰器简化常见模式实现
3. 异步执行提升性能</p></div>


#### 🧰 方法

##### `ExecAsync(async_func: Callable)`

异步执行函数

:param async_func: 异步函数
:param args: 位置参数
:param kwargs: 关键字参数
:return: 函数执行结果

<details class='example'><summary>示例</summary>

```python
>>> result = util.ExecAsync(my_async_func, arg1, arg2)
```
</details>

---

##### `cache(func: Callable)`

缓存装饰器

:param func: 被装饰函数
:return: 装饰后的函数

<details class='example'><summary>示例</summary>

```python
>>> @util.cache
>>> def expensive_operation(param):
>>>     return heavy_computation(param)
```
</details>

---

##### `run_in_executor(func: Callable)`

在独立线程中执行同步函数的装饰器

:param func: 被装饰的同步函数
:return: 可等待的协程函数

<details class='example'><summary>示例</summary>

```python
>>> @util.run_in_executor
>>> def blocking_io():
>>>     # 执行阻塞IO操作
>>>     return result
```
</details>

---

##### `retry(max_attempts: int = 3, delay: int = 1)`

自动重试装饰器

:param max_attempts: 最大重试次数 (默认: 3)
:param delay: 重试间隔(秒) (默认: 1)
:return: 装饰器函数

<details class='example'><summary>示例</summary>

```python
>>> @util.retry(max_attempts=5, delay=2)
>>> def unreliable_operation():
>>>     # 可能失败的操作
```
</details>

---

<sub>文档最后更新于 2025-07-28 05:47:33</sub>