# `ErisPulse.Core.di` 模块

---

## 模块概述


ErisPulse 依赖注入模块

为各处理器注入点（命令处理器 / 事件处理器 / 生命周期钩子 / 路由处理器）提供
统一的声明式依赖注入：

- 处理器参数以 ``Depends(dependency)`` 作为默认值声明依赖
- 注册期由 :func:`extract_depends` 提取声明（fail-fast：依赖不可调用直接抛 ValueError）
- 分发期由 :func:`resolve_depends` 解析：以上下文对象（注入点的第一参数，如
  ``Event`` / 生命周期 ``data`` / 路由 ``HttpRequest``）调用依赖函数，
  结果按参数名注入处理器
- 依赖函数支持同步与异步；同一注入点的所有依赖按声明顺序逐个解析

> **提示**
> 1. 依赖函数的第一个参数是注入点上下文对象——命令/事件场景为 ``Event``，
> 生命周期钩子为事件 ``data``，路由场景为 ``HttpRequest`` / ``SseEmitter``
> 2. ``args=`` / ``options=`` 参数声明与依赖注入参数重名时注册期抛 ValueError（fail-fast）
> 3. FastAPI 承载的 HTTP 路由请使用 FastAPI 原生 ``fastapi.Depends``（生态成熟、
> 支持请求级缓存）；ErisPulse.Core.Depends 覆盖框架自有分发链路

---

## 函数列表


### `extract_depends(func: Callable)`

注册期提取处理器签名中以 ``Depends(...)`` 为默认值的参数（fail-fast）

在处理器注册时调用一次（命令装饰器 / ``BaseEventHandler.register`` /
``lifecycle.register`` / 路由注册），分发期零反射开销。

- **func** (`处理器函数`): **返回值** (`参数名`): → Depends 声明（无依赖声明时为空 dict）
**异常**: `ValueError` - 依赖不可调用

**示例**:
```python
>>> extract_depends(admin)
{"db": Depends(dependency=<function get_db>)}
```

---


### `async resolve_depends(depends: dict[str, Depends], ctx: Any)`

分发期解析依赖：以上下文对象调用各依赖函数，返回处理器关键字参数

同步依赖直接调用；异步依赖依次 await。任一依赖抛出的异常原样向上
传播，由注入点的统一错误路径处理（与处理器自身异常同口径）。

请求级缓存（默认开启）：处于缓存作用域内（事件分发链）且声明
``use_cache=True`` 时，相同依赖函数只解析一次、结果在整次事件内共享；
``use_cache=False`` 或不在作用域内（lifecycle / 路由独立调用链）时
每次解析。

- **depends** (`:func:`extract_depends``): 的提取结果
- **ctx** (`注入点上下文对象（作为依赖函数第一参数）`): **返回值** (`参数名`): → 依赖函数返回值

---


### `async call_with_depends(func: Callable)`

以 Depends 注入调用模块生命周期方法（``on_load`` / ``on_unload`` 等）

供模块加载器调用：上下文对象为第一实参（事件数据 dict，如
``{"module_name": ...}``）。同步方法直接调用，async 方法 await；
依赖声明的解析失败原样向上传播（on_load 失败即加载失败，on_unload
失败由调用方记录日志）。

- **func** (`生命周期方法（绑定方法）`): - **args**: 透传的位置参数（第一参为上下文对象）
**返回值**: 方法返回值

---


### `call_with_depends_sync(func: Callable)`

同步上下文版本的 Depends 注入调用（``emit_sync`` / 同步 ``disable`` 等）

仅支持同步依赖；声明了异步依赖时抛 ``TypeError``（携带本地化原因），
由调用方决定跳过或降级。

- **func** (`生命周期方法（绑定方法）`): - **args**: 透传的位置参数（第一参为上下文对象）
**返回值** (`方法返回值`): **异常**: `TypeError` - 声明了异步依赖（同步上下文无法 await）

---


## 类列表


### `class Depends`

依赖声明标记（作为处理器参数默认值使用）

- **dependency** (`依赖函数（同步或异步），签名`): ``dependency(ctx)``——
    ``ctx`` 为注入点上下文对象（Event / data / HttpRequest 等），
    返回值按参数名注入处理器
- **use_cache** (`请求级缓存开关（默认开启）：同一次事件分发内，`): 相同依赖函数只解析一次、所有注入点共享结果（如数据库会话复用）；
    置 ``False`` 每次注入都重新解析

**示例**:
```python
>>> async def get_db(event):
...     return await sdk.module.call("DB", "get_session")
>>> @command("admin")
... async def admin(event, db=Depends(get_db)):
...     ...
```


#### 方法列表


##### `module(module_name: str, method: str)`

声明模块服务依赖（语法糖）：等价于在依赖函数内调用 ``sdk.module.call(...)``

- **module_name** (`目标模块名`): - **method**: 目标服务方法名（须在目标模块 get_meta().services 契约内）
- **args** (`透传给目标方法的固定位置参数`): - **kwargs**: 透传给目标方法的固定关键字参数
**返回值** (`Depends`): 声明（上下文对象被忽略——模块调用不依赖注入点上下文）

**示例**:
```python
>>> @command("admin")
... async def admin(event, db=Depends.module("DB", "get_session")):
...     ...
```

---

