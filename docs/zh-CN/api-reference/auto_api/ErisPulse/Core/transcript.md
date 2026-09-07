# `ErisPulse.Core.transcript` 模块

---

## 模块概述


ErisPulse 会话收件箱（transcript）

提供每会话近期消息流的统一记录与查询，作为上下文记忆类模块
（AI 对话、防复读、行为分析等）的公共底座：

- **入站**：消息事件进入分发管线时自动记录（role="user"）；
- **出站**：机器人发送的文本类消息经 ``message.sent`` 钩子自动记录（role="bot"）；
- **存储**：独立 SQLite 表（经 storage），每会话条数上限 + 全局 TTL 自动清理；
- **查询**：``event.history(n)`` 或 ``sdk.transcript.get(event, n)``。

> **提示**
> 配置（``ErisPulse.transcript``）::
> [ErisPulse.transcript]
> enabled = true          # 是否启用（关闭后停止写入，历史仍可查询）
> max_per_session = 50    # 每会话保留的最大条数
> ttl_hours = 168         # 全局过期时间（小时），过期记录惰性清理
> 使用方式::
> from ErisPulse.Core import transcript
> # 查询当前会话最近 20 条消息（含用户与机器人）
> messages = await event.history(20)   # 或 transcript.get(event, 20)
> for m in messages:
> print(m["role"], m["text"])

---

## 类列表


### `class TranscriptManager`

会话收件箱管理器

以 ``platform:detail_type:target_id`` 为会话键记录消息流，
存储于独立 SQLite 表，支持条数上限与 TTL 双重保留策略。


#### 方法列表


##### `_config()`

> **内部方法** 读取 transcript 配置节

---


##### `enabled()`

是否启用自动记录（ErisPulse.transcript.enabled）

---


##### `session_key_from_event(event: Any)`

从事件推导会话键（platform:detail_type:target_id）

target 语义与交互会话等待键一致（复用 session_type 的目标推导，
私聊为 user_id，群聊 / 频道等对应目标 ID）。

- **event** (`事件数据（Event`): 或 dict）
**返回值**: 会话键字符串

---


##### `_ctx_key(ctx: dict)`

> **内部方法** 从 message.sent 发送上下文推导会话键

---


##### `_ensure_table()`

> **内部方法** 惰性建表

---


##### `_retention(session_key: str, max_per_session: int, ttl_hours: float)`

> **内部方法** 保留策略：每会话条数上限 + 全局 TTL（惰性触发）

---


##### `append(session: Any, role: str, text: str, event_id: str = '')`

记录一条消息到会话收件箱

- **session** (`事件数据（Event`): / dict，自动推导会话键）或会话键字符串
- **role** (`消息角色（"user"`): / "bot"）
- **text** (`消息文本（超长自动截断）`): - **event_id**: 关联的事件 ID（可选）
**返回值** (`是否写入成功（未启用时返回`): False）

**示例**:
```python
>>> transcript.append(event, "user", "你好")
```

---


##### `get(session: Any, n: int = 20)`

查询会话近期消息（按时间升序）

- **session** (`事件数据或会话键字符串`): - **n**: 返回的最大条数
**返回值** (`消息列表，每条含`): role / text / ts / event_id；无记录时返回空列表

**示例**:
```python
>>> messages = transcript.get(event, 20)
>>> for m in messages:
...     print(m["role"], ":", m["text"])
```

---


##### `clear(session: Any)`

清空指定会话的收件箱

- **session** (`事件数据或会话键字符串`): **返回值** (`删除的记录数`): 
**示例**:
```python
>>> transcript.clear(event)
```

---


##### `attach()`

挂接出站自动记录（message.sent 钩子，框架初始化时调用）

重复调用安全；未启用时跳过注册（运行时改为启用需重启或重新 attach）。

**返回值**: 是否成功挂接

---


##### `async _on_message_sent(data: Any)`

> **内部方法** message.sent 钩子：记录机器人出站文本

---

