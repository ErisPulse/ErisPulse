# `ErisPulse.Core.adapter` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 适配器系统

提供平台适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。

---

## 类列表

### `class AdapterManager`

    适配器管理器

管理多个平台适配器的注册、启动和关闭，提供与模块管理器一致的接口

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 通过register方法注册适配器
2. 通过startup方法启动适配器
3. 通过shutdown方法关闭所有适配器
4. 通过on装饰器注册OneBot12协议事件处理器</p></div>

    
#### 方法列表

##### `register(platform: str, adapter_class: Type[BaseAdapter], adapter_info: Optional[Dict] = None)`

    注册新的适配器类（标准化注册方法）

:param platform: 平台名称
:param adapter_class: 适配器类
:param adapter_info: 适配器信息
:return: 注册是否成功

<dt>异常</dt><dd><code>TypeError</code> 当适配器类无效时抛出</dd>

<details class='example'><summary>示例</summary>

```python
>>> adapter.register("MyPlatform", MyPlatformAdapter)
```
</details>

    ---
    
##### `_register_platform_attributes(platform: str, instance: BaseAdapter)`

    注册平台名称的多种大小写形式作为属性

:param platform: 平台名称
:param instance: 适配器实例

    ---
    
##### async `async startup(platforms = None)`

    启动指定的适配器

:param platforms: 要启动的平台列表，None表示所有平台

<dt>异常</dt><dd><code>ValueError</code> 当平台未注册时抛出</dd>

<details class='example'><summary>示例</summary>

```python
>>> # 启动所有适配器
>>> await adapter.startup()
>>> # 启动指定适配器
>>> await adapter.startup(["Platform1", "Platform2"])
```
</details>

    ---
    
##### async `async _run_adapter(adapter: BaseAdapter, platform: str)`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
运行适配器实例

:param adapter: 适配器实例
:param platform: 平台名称

    ---
    
##### async `async shutdown()`

    关闭所有适配器

    ---
    
##### `_config_register(platform: str, enabled: bool = False)`

    注册新平台适配器（仅当平台不存在时注册）

:param platform: 平台名称
<dt><code>enabled</code> <span class='type-hint'>bool</span></dt><dd>是否启用适配器</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 操作是否成功</dd>

    ---
    
##### `exists(platform: str)`

    检查平台是否存在

:param platform: 平台名称
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 平台是否存在</dd>

    ---
    
##### `is_enabled(platform: str)`

    检查平台适配器是否启用

:param platform: 平台名称
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 平台适配器是否启用</dd>

    ---
    
##### `enable(platform: str)`

    启用平台适配器

:param platform: 平台名称
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 操作是否成功</dd>

    ---
    
##### `disable(platform: str)`

    禁用平台适配器

:param platform: 平台名称
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 操作是否成功</dd>

    ---
    
##### `list_adapters()`

    列出所有平台适配器状态

<dt>返回值</dt><dd><span class='type-hint'>Dict[str, bool</span> ] 平台适配器状态字典</dd>

    ---
    
##### `on(event_type: str = '*')`

    OneBot12协议事件监听装饰器

:param event_type: OneBot12事件类型
:param raw: 是否监听原生事件
:param platform: 指定平台，None表示监听所有平台
:return: 装饰器函数

<details class='example'><summary>示例</summary>

```python
>>> # 监听OneBot12标准事件（所有平台）
>>> @sdk.adapter.on("message")
>>> async def handle_message(data):
>>>     print(f"收到OneBot12消息: {data}")
>>>
>>> # 监听特定平台的OneBot12标准事件
>>> @sdk.adapter.on("message", platform="onebot11")
>>> async def handle_onebot11_message(data):
>>>     print(f"收到OneBot11标准消息: {data}")
>>>
>>> # 监听平台原生事件
>>> @sdk.adapter.on("message", raw=True, platform="onebot11")
>>> async def handle_raw_message(data):
>>>     print(f"收到OneBot11原生事件: {data}")
>>>
>>> # 监听所有平台的原生事件
>>> @sdk.adapter.on("message", raw=True)
>>> async def handle_all_raw_message(data):
>>>     print(f"收到原生事件: {data}")
```
</details>

    ---
    
##### `middleware(func: Callable)`

    添加OneBot12中间件处理器

:param func: 中间件函数
:return: 中间件函数

<details class='example'><summary>示例</summary>

```python
>>> @sdk.adapter.middleware
>>> async def onebot_middleware(data):
>>>     print("处理OneBot12数据:", data)
>>>     return data
```
</details>

    ---
    
##### async `async emit(data: Any)`

    提交OneBot12协议事件到指定平台

:param data: 符合OneBot12标准的事件数据

<details class='example'><summary>示例</summary>

```python
>>> await sdk.adapter.emit({
>>>     "id": "123",
>>>     "time": 1620000000,
>>>     "type": "message",
>>>     "detail_type": "private",
>>>     "message": [{"type": "text", "data": {"text": "Hello"}}],
>>>     "platform": "myplatform",
>>>     "myplatform_raw": {...平台原生事件数据...},
>>>     "myplatform_raw_type": "text_message"
>>> })
```
</details>

    ---
    
##### `get(platform: str)`

    获取指定平台的适配器实例

:param platform: 平台名称
:return: 适配器实例或None

<details class='example'><summary>示例</summary>

```python
>>> adapter = adapter.get("MyPlatform")
```
</details>

    ---
    
##### `platforms()`

    获取所有已注册的平台列表

:return: 平台名称列表

<details class='example'><summary>示例</summary>

```python
>>> print("已注册平台:", adapter.platforms)
```
</details>

    ---
    
##### `__getattr__(platform: str)`

    通过属性访问获取适配器实例

:param platform: 平台名称
:return: 适配器实例
<dt>异常</dt><dd><code>AttributeError</code> 当平台不存在或未启用时</dd>

    ---
    
##### `__contains__(platform: str)`

    检查平台是否存在且处于启用状态

:param platform: 平台名称
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 平台是否存在且启用</dd>

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>