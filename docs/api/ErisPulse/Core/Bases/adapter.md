# `ErisPulse.Core.Bases.adapter` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 适配器基础模块

提供适配器和消息发送DSL的基类实现

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 用于实现与不同平台的交互接口
2. 提供统一的消息发送DSL风格接口</p></div>

---

## 类列表

### `class SendDSL`

    消息发送DSL基类

用于实现 Send.To(...).Func(...) 风格的链式调用接口

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 子类应实现具体的消息发送方法(如Text, Image等)
2. 通过__getattr__实现动态方法调用</p></div>

    
#### 方法列表

##### `__init__(adapter: 'BaseAdapter', target_type: Optional[str] = None, target_id: Optional[str] = None, account_id: Optional[str] = None)`

    初始化DSL发送器

:param adapter: 所属适配器实例
:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:param _account_id: 发送账号(可选)

    ---
    
##### `To(target_type: str = None, target_id: Union[str, int] = None)`

    设置消息目标

:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:return: SendDSL实例

<details class='example'><summary>示例</summary>

```python
>>> adapter.Send.To("user", "123").Text("Hello")
>>> adapter.Send.To("123").Text("Hello")  # 简化形式
```
</details>

    ---
    
##### `Using(account_id: Union[str, int])`

    设置发送账号

:param _account_id: 发送账号
:return: SendDSL实例

<details class='example'><summary>示例</summary>

```python
>>> adapter.Send.Using("bot1").To("123").Text("Hello")
>>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序
```
</details>

    ---
    
### `class BaseAdapter`

    适配器基类

提供与外部平台交互的标准接口，子类必须实现必要方法

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 必须实现call_api, start和shutdown方法
2. 可以自定义Send类实现平台特定的消息发送逻辑
3. 通过on装饰器注册事件处理器
4. 支持OneBot12协议的事件处理</p></div>

    
#### 方法列表

##### async `async call_api(endpoint: str)`

    调用平台API的抽象方法

:param endpoint: API端点
:param params: API参数
:return: API调用结果
<dt>异常</dt><dd><code>NotImplementedError</code> 必须由子类实现</dd>

    ---
    
##### async `async start()`

    启动适配器的抽象方法

<dt>异常</dt><dd><code>NotImplementedError</code> 必须由子类实现</dd>

    ---
    
##### async `async shutdown()`

    关闭适配器的抽象方法

<dt>异常</dt><dd><code>NotImplementedError</code> 必须由子类实现</dd>

    ---
    
##### `send(target_type: str, target_id: str, message: Any)`

    发送消息的便捷方法，返回一个 asyncio Task

:param target_type: 目标类型
:param target_id: 目标ID
:param message: 消息内容
:param kwargs: 其他参数
    - method: 发送方法名(默认为"Text")
:return: asyncio.Task 对象，用户可以自主决定是否等待

<dt>异常</dt><dd><code>AttributeError</code> 当发送方法不存在时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> task = adapter.send("user", "123", "Hello")
>>> # 用户可以选择等待: result = await task
>>> # 或者不等待让其在后台执行
>>> await adapter.send("group", "456", "Hello", method="Markdown")  # 直接等待
```
</details>

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>