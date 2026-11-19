# `ErisPulse.Core.Event.command_flow` 模块

---

## 模块概述


命令多轮流控语法糖（``.got()`` 链）

在 ``@command`` 装饰器之上提供 NoneBot ``@matcher.got()`` 风格的声明式多轮
对话：入口处理器之后按声明顺序逐步收集值，收集值按参数名注入后续步骤函数。
底层编译到 :class:`Conversation`——每步一个分支，分支跳转自动保存检查点，
重启后经 ``Conversation.try_auto_resume`` 从存档分支继续（恢复工厂由本模块
在装饰期自动注册，owner 归属与卸载注销继承 Conversation 既有机制）。

> **提示**
> 1. ``@command`` 返回 :class:`CommandFlow` 可调用代理（对原函数完全透明）
> 2. ``@flow.got("名字", prompt=...)`` 声明收集步骤，收集值按参数名注入步骤函数
> 3. 任一步超时 / 被打断 → 对话终态并清除检查点（与 wait_reply 语义一致）

---

## 类列表


### `class _Step`

**内部方法** 单步声明（.got() 的注册期快照）


### `class CommandFlow`

命令多轮流控代理（``@command`` 装饰器的返回值）

对原函数完全透明的可调用代理：调用行为与原处理器一致（命令分发器照常
执行入口处理器，属性访问 / ``__name__`` / docstring 全部转发），因此存量
代码零影响。额外提供 :meth:`got` 装饰器声明后续收集步骤——步骤按声明
顺序执行，收集值（含命令入口参数）按参数名注入步骤函数。

流程编译到 Conversation：每步一个分支（分支跳转自动存检查点），重启后
经自动注册的恢复工厂从存档分支继续（用户重新收到当前步骤的提问）。

**示例**:

```python
@command("weather")
async def weather(event):
    pass  # 入口：首个 .got 的 prompt 会自动发送，无需手动提问
@weather.got("city", prompt="请直接回复城市名")
async def weather_city(event, city: str):
    await event.reply(f"{city}：晴")
@weather.got("days", prompt="预报几天？", type=int)
async def weather_days(event, city: str, days: int):
    await event.reply(f"{city} 未来 {days} 天……")
```


#### 方法列表


##### `got(name: str, prompt: str | None = None, *, timeout: float | str = DEFAULT_WAIT_TIMEOUT_SECS, type: 'FlowValueType | None' = None, validator: Callable | None = None, pattern: str | None = None, regex: str | None = None, session: bool = False, cmdpass: bool | None = None, method: str = 'Text', retry_prompt: str | None = None, max_retries: int = 2) -> Callable`

声明一个收集步骤

步骤按声明顺序执行；收到回复后按 ``type`` / 校验器解析值，解析失败
自动重发 ``retry_prompt``（默认复用 ``prompt``）直至超过 ``max_retries``。
任一步超时或被抢断 → 整条流程结束并清除检查点。

- **name**: 收集值名称（注入后续步骤函数的参数名；须在流程内唯一）
- **prompt**: 提示消息（进入该步骤时自动发送）
- **timeout**: 单步等待超时（秒数或 ``"90s"`` / ``"1h30m"`` 时长串）
- **type**: 值类型（``int`` / ``float`` / ``str`` 等；None = 原始文本）
- **validator**: 额外校验器（接收回复 Event，返回真值才接受；与

    ``Event.wait_reply`` 的 validator 语义一致）
- **pattern** (`glob`): 通配符（回复不匹配时继续等待）
- **regex**: 正则（与 pattern 同时给定时须都匹配）
- **session**: 会话级等待（同会话任何人可命中）
- **cmdpass**: 命令放行三态（None = 跟随全局配置）
- **method**: 发送方法（默认 "Text"）
- **retry_prompt**: 解析失败时的重试提示（缺省复用 prompt）
- **max_retries**: 解析失败的最大重试次数

**返回值**: 原函数（装饰器语义，不改变被装饰对象）

---


##### `_mount_branches(conv: Any) -> None`

**内部方法** 把步骤链编译为 Conversation 分支

---


##### `async _collect_value(conv: Any, step: _Step, event: Any) -> Any`（staticmethod）

**内部方法** 单步收集（含类型解析与重试）；失败返回 _FLOW_ENDED

---


##### `_coerce(step: _Step, reply: Any) -> Any`（staticmethod）

**内部方法** 从回复事件提取文本并按步骤类型解析

---


##### `_bind(handler: Callable, collected: dict[str, Any]) -> dict[str, Any]`（staticmethod）

**内部方法** 收集值按参数名注入步骤函数（只传声明了的参数）

---


##### `_ensure_resume_factory() -> None`

**内部方法** 注册恢复工厂（幂等；装饰期调用，owner 归属当场捕获）

---


##### `_resume_factory(event: Any) -> Any`

**内部方法**
恢复工厂：检查点属于本流程时重建对话（重挂分支），否则返回 None 交给下一个工厂

---

