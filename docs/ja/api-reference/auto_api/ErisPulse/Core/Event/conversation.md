# `ErisPulse.Core.Event.conversation` 模块

---

## 模块概述


ErisPulse 多轮对话上下文模块

提供 Conversation（多轮对话原语与检查点持久化）、消息事务（_MessageTx）
与对话恢复工厂注册表；由 ``ErisPulse.Core.Event.wrapper`` re-export，
既有导入路径（``ErisPulse.Core.Event.wrapper.Conversation`` 等）不变。

> **提示**
> 1. 通过 event.conversation() 方法创建对话上下文
> 2. 支持 say/wait/confirm/choose/collect 等对话原语与 branch/goto 分支跳转
> 3. 分支跳转自动保存检查点，重启后可 save()/resume() 或自动恢复

---

## 函数列表


### `_consume_task_exception(task: 'asyncio.Task')`

> **内部方法** 消费后台检查点任务的异常（防未检索告警）

---


### `async _rollback_receipts(receipts: list[dict[str, str]])`

> **内部方法**
逆序撤回消息事务账本中的消息（能力感知）

适配器未实现 ``delete_message``（Api 能力缺失）时跳过该条并记录 TRACE 日志；
单条撤回失败不中断后续撤回。

- **receipts**: 消息回执账本

---


### `_start_checkpoint_gc()`

> **内部方法** 惰性启动过期检查点周期清理（仅启动一次，失败静默）

---


### `async _checkpoint_gc_loop()`

> **内部方法** 周期清理循环（CONVERSATION_CHECKPOINT_GC_INTERVAL_SECS 间隔）

---


## 类列表


### `class _MessageTx`

> **内部方法**
消息事务上下文管理器（由 :meth:`Event.message_tx` 创建）

事务内所有出站发送自动记入回执账本；异常退出时逆序撤回已发送的消息
（适配器需实现 ``delete_message``，未实现时跳过）。正常退出不撤回。


### `class Conversation`

多轮对话上下文

提供在同一会话中进行多轮交互的便捷方法，支持分支跳转、上下文持久化

> **提示**
> 1. 通过 event.conversation() 方法创建
> 2. 超时后自动标记为非活跃状态
> 3. 支持链式调用 say() 方法
> 4. 支持 branch() 定义分支和 goto() 跳转
> 5. 支持 context 字典存储对话状态
> 6. 支持 save()/resume() 持久化到 storage


#### 方法列表


##### `__init__(event: 'Event', timeout: float = DEFAULT_WAIT_TIMEOUT_SECS)`

初始化对话上下文

- **event** (`Event`): - 事件对象
- **timeout** (`float`): - 默认超时时间(秒)（默认: 60.0）

---


##### `is_active()`

对话是否处于活跃状态

**返回值** (`bool`): - 是否活跃

---


##### `async say(content: str)`

发送消息

- **content** (`str`): - 消息内容
**返回值** (`Conversation`): - self（支持链式调用）

---


##### `async wait(prompt: str | None = None, timeout: float | None = None, method: str = DEFAULT_SEND_METHOD)`

等待用户回复

- **prompt** (`str`): - 提示消息（可选）
- **timeout** (`float`): - 超时时间(秒)，默认使用对话的超时设置
- **method** (`str`): - 发送方法（默认: "Text"）
**返回值** (`Event|None`): - 用户回复的事件, 超时返回 None

---


##### `async confirm(prompt: str | None = None)`

等待用户确认

- **prompt** (`str`): - 提示消息
**返回值** (`bool|None`): - True/False/None

---


##### `async choose(prompt: str, options: list[str])`

等待用户选择

- **prompt** (`str`): - 提示消息
- **options** (`list[str]`): - 选项列表
**返回值** (`int|None`): - 选中索引或 None

---


##### `async collect(fields: list[dict])`

多步骤收集信息

- **fields** (`list[dict]`): - 字段列表，支持 condition 字段:
    - condition: callable - 接收已收集数据 dict, 返回 bool 决定是否收集此字段
**返回值** (`dict|None`): - 收集到的数据字典或 None

---


##### `stop()`

结束对话

终态自动清除已保存的对话检查点。

---


##### `remind(delay: float, text: str | None = None)`

会话定时提醒（转发到当前对话事件的 ``Event.remind``）

delay 秒后无回复则发送提醒文本 / 执行回调；用户在会话回复后自动取消。

- **delay** (`延迟秒数`): - **text**: 到期发送的提醒文本（与 callback 二选一）
- **callback** (`到期执行的回调（接收当前`): Event 为参数）
**返回值** (`Reminder`): 句柄；超过单会话上限时返回 None

**示例**:
```python
>>> conv.remind(120, "还在考虑吗？需要帮助请输入「帮助」")
```

---


##### `escalate(delay: float, callback: Any)`

超时升级（转发到当前对话事件的 ``Event.escalate``，不被回复取消）

- **delay** (`延迟秒数`): - **callback**: 到期执行的回调（接收当前 Event 为参数）
**返回值** (`Reminder`): 句柄

---


##### `branch(name: str)`

注册分支处理器

- **name** (`str`): 分支名称
**返回值** (`Callable`): 装饰器

**示例**:
```python
>>> conv = event.conversation()
>>>
>>> @conv.branch("menu")
... async def menu_branch(conv, event):
...     await conv.say("1.饮品 2.主食")
...     resp = await conv.wait()
...     if resp and resp.get_text() == "1":
...         conv.goto("drink")
...
>>> @conv.branch("drink")
... async def drink_branch(conv, event):
...     await conv.say("请选择饮品")
...     resp = await conv.wait()
...     conv.context["drink"] = resp.get_text()
...     conv.goto("confirm")
...
>>> conv.start("menu")
```

---


##### `goto(branch_name: str, event: 'Event | None' = None)`

跳转到指定分支

- **branch_name** (`str`): 目标分支名称
- **event** (`Event`): 传递给分支的事件对象 (可选)

**异常**: `ValueError` - 当目标分支不存在时

**示例**:
```python
>>> conv.goto("drink")
```

---


##### `start(branch_name: str, event: 'Event | None' = None)`

启动对话，从指定分支开始

- **branch_name** (`str`): 起始分支名称
- **event** (`Event`): 初始事件对象 (可选)

**异常**: `ValueError` - 当起始分支不存在时

**示例**:
```python
>>> conv.start("menu")
```

---


##### `get_current_branch()`

获取当前分支名称

**返回值** (`str|None`): 当前分支名, 未在分支中时返回 None

---


##### `has_branch(name: str)`

检查分支是否存在

- **name** (`str`): 分支名称
**返回值** (`bool`): 是否存在

---


##### `_checkpoint_key(event: 'Event')`

> **内部方法**
生成对话检查点存储键（含 target 维度，避免同一用户多会话互覆）

- **event** (`事件对象`): **返回值**: 存储键（conversation:{platform}:{user_id}:{target_id}）

---


##### `_checkpoint_ttl()`

> **内部方法**
读取检查点过期时长（ErisPulse.interaction.checkpoint_ttl，秒）

**返回值**: 过期秒数

---


##### `_schedule_checkpoint()`

> **内部方法** 后台保存检查点（分支跳转自动触发，失败静默）

---


##### `_schedule_checkpoint_clear()`

> **内部方法** 后台清除检查点（对话终态自动触发，失败静默）

---


##### `async _checkpoint(save: bool)`

> **内部方法** 检查点写入/清除的统一异常兜底

---


##### `async save()`

保存对话状态到 storage（自动检查点）

分支跳转（goto/start）时框架自动调用；也可手动调用强制存档。
存储键含 target 维度（conversation:{platform}:{user_id}:{target_id}），
同一用户在不同会话中的对话互不覆盖。

**示例**:
```python
>>> await conv.save()

> **提示**
> 保存内容包括: 当前分支、上下文数据、活跃状态、存档时间。
> 超过 ``ErisPulse.interaction.checkpoint_ttl``（默认 24h）的存档在恢复时被丢弃。
```

---


##### `async resume(event: 'Event | None' = None, with_history: int = 10)`

从 storage 恢复对话状态（含会话接管与历史带回）

恢复流程：读取检查点（含 target 维度新键，旧格式自动迁移）→
**会话接管**（自动 acquire 会话租约，被其他模块占用时放弃恢复）→
落地上下文并从收件箱带回最近消息到 :attr:`recent_history`。

超过 checkpoint_ttl 的存档视为过期，丢弃并返回 False。

- **event** (`Event`): 新的事件对象 (可选, 不传则使用原事件)
- **with_history** (`恢复时从会话收件箱带回的最近消息条数（0`): 关闭）
**返回值** (`bool`): 是否恢复成功

**示例**:
```python
>>> conv = event.conversation()
>>> # ... 注册分支 ...
>>> if await conv.resume():
...     conv.goto(conv.get_current_branch())

> **提示**
> 需要在 resume() 之前先注册好所有分支；注册分支后也可使用
> :meth:`register_resume_handler` 声明恢复工厂，由框架在重启后
> 首条命中消息自动完成恢复。
```

---


##### `async clear_saved()`

清除保存的对话状态

同时清理含 target 的新键与旧格式键。

**示例**:
```python
>>> await conv.clear_saved()
```

---


##### `register_resume_handler(platform: str | None = None)`

注册对话恢复工厂（类装饰器方法，模块加载时调用）

框架在重启后收到该会话的首条消息时，若存在有效检查点，
会调用已注册的工厂重建 Conversation（模块需在工厂内重新注册所有分支），
随后自动 ``goto`` 到存档分支继续对话。

- **platform** (`仅匹配指定平台的事件；None`): 表示匹配所有平台
**返回值** (`装饰器`): 
**示例**:
```python
>>> @Conversation.register_resume_handler()
... def make_conversation(event) -> Conversation:
...     conv = event.conversation()
...     @conv.branch("menu")
...     async def menu(conv, event): ...
...     return conv
```

---


##### `async try_auto_resume(event: 'Event')`

> **内部方法**
尝试对当前消息事件自动恢复挂起的对话（框架在消息入口调用）

无已注册恢复工厂时立即返回（零开销路径）；存在有效检查点且
某工厂成功重建对话时，恢复上下文、认领事件并跳转到存档分支。

- **event** (`消息事件（Event`): 包装类）
**返回值**: 是否完成了自动恢复（事件已被消费）

---


##### `async _gc_expired_checkpoints()`

> **内部方法**
主动清理过期对话检查点（周期任务调用）

枚举 `conversation:` 前缀的全部存储键，按 `saved_at` 与
`ErisPulse.interaction.checkpoint_ttl` 判定过期并删除——补全
"仅在 resume 时惰性清理"的缺口，长期未恢复的存档不再永久驻留。

**返回值**: 清理的存档数量

---

