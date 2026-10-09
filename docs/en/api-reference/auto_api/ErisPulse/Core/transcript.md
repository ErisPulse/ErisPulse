# `ErisPulse.Core.transcript` 模块

---

## 模块概述


ErisPulse 会话收件箱（transcript）

提供每会话近期消息流的统一记录与查询，作为上下文记忆类模块
（AI 对话、防复读、行为分析等）的公共底座：

- **入站**：消息事件进入分发管线时自动记录（role="user"）；
- **出站**：机器人发送的文本类消息经 ``message.sent`` 钩子自动记录（role="bot"）；
- **存储**：独立 SQLite 表（经 storage），写入走内存缓冲 + 后台批量落盘

  （默认每 1 秒或满 64 条一事务提交），查询自动合并未落盘的缓冲行；
  每会话条数上限 + 全局 TTL 自动清理；
- **查询**：``event.history(n)`` 或 ``sdk.transcript.get(event, n)``。

> **提示**
> 配置（``ErisPulse.transcript``）:
> ```
> [ErisPulse.transcript]
> enabled = true          # 是否启用（关闭后停止写入，历史仍可查询）
> max_per_session = 50    # 每会话保留的最大条数
> ttl_hours = 168         # 全局过期时间（小时），过期记录惰性清理
> ```
>
> 持久性说明：追加先进内存缓冲，由后台任务批量落盘（延迟至多
> ``TRANSCRIPT_FLUSH_INTERVAL_SECS`` 秒）；正常退出（``sdk.uninit`` / 进程
> atexit）会强制刷盘。进程被硬崩溃 / 强杀时，最近一批未落盘记录（约 1 秒内）
> 可能丢失。
> 使用方式:
> ```
> from ErisPulse.Core import transcript
> 
> # 查询当前会话最近 20 条消息（含用户与机器人）
> messages = await event.history(20)   # 或 transcript.get(event, 20)
> for m in messages:
>     print(m["role"], m["text"])
> ```
>

---

## 类列表


### `class TranscriptManager`

会话收件箱管理器

以 ``platform:detail_type:target_id`` 为会话键记录消息流，
存储于独立 SQLite 表，支持条数上限与 TTL 双重保留策略。

写入路径为"内存缓冲 + 后台批量落盘"：``append`` 仅入队（微秒级，
不阻塞分发热路径），后台任务按条数 / 时间阈值批量事务提交；
查询接口自动合并未落盘的缓冲行（同进程读你的写）。


#### 方法列表


##### `_config() -> dict[str, Any]`

**内部方法** 读取 transcript 配置节（轻量缓存，配置事件失效）

---


##### `_invalidate_config_cache(data: Any = None) -> None`

**内部方法** transcript 相关配置写入 / 配置重载时失效缓存

---


##### `_ensure_hooks() -> None`

**内部方法** 惰性注册配置失效监听与退出刷盘（各一次）

---


##### `_flush_on_exit() -> None`

**内部方法**
进程退出兜底：同步刷掉未落盘缓冲（镜像 config._flush_on_exit）

以看门狗线程限时执行——解释器收尾阶段存储同步桥的后台线程可能已
无法调度（自由线程构建下尤其如此），在 atexit 里直接走同步桥会
永久阻塞、令进程退出挂死；超时即放弃（至多丢一批缓冲），保证
退出必然完成。缓冲为空时刷盘立即返回，无任何开销。

---


##### `enabled -> bool`（property）

是否启用自动记录（ErisPulse.transcript.enabled）

---


##### `set_retention(*, max_per_session: int | None = None, ttl_hours: float | None = None) -> None`

运行时覆盖保留策略（优先于 ``ErisPulse.transcript.*`` 配置）

覆盖仅驻内存、重启后失效（恢复配置值）。调大 / 关闭限制前请确认知悉：
``transcript`` 表会随消息量无限增长——磁盘写满、查询变慢，且把历史
整段载入内存的下游消费者（对话恢复 / 面板全量拉取）内存压力上升；
写缓冲有硬上限不受影响。详见 docs advanced/transcript.md 风险专节。

- **max_per_session** (`int | None`): 单会话保留条数；0 = 关闭该策略
- **ttl_hours** (`float | None`): 全局保留时长（小时）；0 = 关闭该策略

**异常**: `ValueError` - 传入负数时

**示例**:

```python
transcript.set_retention(max_per_session=500, ttl_hours=24 * 30)
```

---


##### `get_retention() -> dict[str, Any]`

查询当前生效的保留策略

**返回值** (`dict`): 含 ``max_per_session`` / ``ttl_hours`` 生效值与

         ``overridden``（被运行时覆盖的键列表）

**示例**:

```python
transcript.get_retention()
{'max_per_session': 500, 'ttl_hours': 168.0, 'overridden': ['max_per_session']}
```

---


##### `reset_retention() -> None`

清除运行时覆盖，恢复按 ``ErisPulse.transcript.*`` 配置生效

---


##### `_effective_retention() -> tuple[int, float]`

**内部方法** 生效保留策略：运行时覆盖优先，否则读配置

---


##### `session_key_from_event(event: Any) -> str`（staticmethod）

从事件推导会话键（platform:detail_type:target_id）

target 语义与交互会话等待键一致（复用 session_type 的目标推导，
私聊为 user_id，群聊 / 频道等对应目标 ID）。

- **event**: 事件数据（Event 或 dict）

**返回值**: 会话键字符串

---


##### `_ctx_key(ctx: dict) -> str`（staticmethod）

**内部方法** 从 message.sent 发送上下文推导会话键

---


##### `_ensure_table() -> bool`

**内部方法** 惰性建表（含旧表 sender 列迁移）

---


##### `async _aensure_table() -> bool`

**内部方法** 惰性建表（异步路径，flusher 使用）

---


##### `_migrate_add_sender() -> None`

**内部方法** 旧表缺 sender 列时自动补列（2.8.0 新增）

---


##### `async _amigrate_add_sender() -> None`

**内部方法** 异步路径的 sender 列迁移探测（列缺失时回退同步 ALTER）

---


##### `_retention(session_key: str, max_per_session: int, ttl_hours: float) -> None`

**内部方法** 保留策略：每会话条数上限 + 全局 TTL（惰性触发，覆盖库与内存缓冲）

---


##### `_ensure_flusher() -> None`

**内部方法** 首次在事件循环内追加时启动后台刷盘任务

---


##### `async _flush_loop() -> None`

**内部方法** 周期刷盘循环：按时间阈值批量提交，积压时连续排空

---


##### `_take_batch() -> list[dict[str, Any]]`

**内部方法** 从缓冲头部取一批待落盘行

---


##### `async _flush_async() -> bool`

**内部方法** 异步批量落盘一批缓冲行（单事务原子提交）

**返回值**: 是否成功（失败时批次已回插缓冲头部，等待下轮重试）

---


##### `_requeue(rows: list[dict[str, Any]]) -> None`

**内部方法** 落盘失败 / 被取消时把批次回插缓冲头部（保证不丢）

---


##### `async aflush() -> int`

异步刷掉当前全部未落盘缓冲（框架卸载时调用）

**返回值**: 实际落盘的记录数

**示例**:

```python
await transcript.aflush()
```

---


##### `flush() -> int`

同步刷掉当前全部未落盘缓冲（进程退出兜底 / 手动调用）

**返回值**: 实际落盘的记录数

**示例**:

```python
transcript.flush()
```

---


##### `append(session: Any, role: str, text: str, event_id: str = '', sender: str = '') -> bool`

记录一条消息到会话收件箱

仅入内存缓冲即返回（微秒级，不阻塞分发热路径）；由后台任务批量
落盘（延迟至多 ``TRANSCRIPT_FLUSH_INTERVAL_SECS`` 秒），查询接口
会自动合并未落盘的缓冲行。

- **session**: 事件数据（Event / dict，自动推导会话键）或会话键字符串
- **role**: 消息角色（"user" / "bot"）
- **text**: 消息文本（超长自动截断）
- **event_id**: 关联的事件 ID（可选）
- **sender**: 发送者标识（user_id，可选，回放时还原消息来源）

**返回值**: 是否接受（未启用时返回 False；缓冲超限时淘汰最旧行）

**示例**:

```python
transcript.append(event, "user", "你好")
```

---


##### `_merged(rows: list[dict[str, Any]], *, session_key: str | None = None, event_id: str | None = None, since_ts: float | None = None, limit: int) -> list[dict[str, Any]]`

**内部方法** 合并数据库行与未落盘缓冲行（read-your-writes）

- **rows**: 数据库查询结果（任意顺序）
- **session_key**: 会话键过滤（None 不过滤）
- **event_id**: 链路 ID 过滤（None 不过滤）
- **since_ts**: 时间下界过滤（None 不过滤）
- **limit**: 返回最新 ``limit`` 条（时间升序输出）

---


##### `get(session: Any, n: int = 20) -> list[dict[str, Any]]`

查询会话近期消息（按时间升序，含未落盘的缓冲行）

- **session**: 事件数据或会话键字符串
- **n**: 返回的最大条数

**返回值**: 消息列表，每条含 role / text / ts / event_id；无记录时返回空列表

**示例**:

```python
messages = transcript.get(event, 20)
for m in messages:
    print(m["role"], ":", m["text"])
```

---


##### `recent(seconds: float, limit: int = 200) -> list[dict[str, Any]]`

查询全部会话中最近一段时间内的消息（跨会话，按时间升序，含未落盘缓冲行）

冷启动回放（``get_load_strategy(replay=...)``）的数据源；
每条记录额外携带 ``session_key``，用于还原消息来源会话。
窗口内记录超过 ``limit`` 时返回最新的 ``limit`` 条。

- **seconds**: 回溯时长（秒）
- **limit**: 最大返回条数（防止模块冷启动被打爆）

**返回值**: 消息列表（role / text / ts / sender / session_key）

**示例**:

```python
transcript.recent(300)  # 最近 5 分钟
```

---


##### `clear(session: Any) -> int`

清空指定会话的收件箱（同时清除未落盘缓冲中的该会话记录）

- **session**: 事件数据或会话键字符串

**返回值**: 删除的记录数

**示例**:

```python
transcript.clear(event)
```

---


##### `attach() -> bool`

挂接出站自动记录（message.sent 钩子，框架初始化时调用）

重复调用安全；未启用时跳过注册（运行时改为启用需重启或重新 attach）。

**返回值**: 是否成功挂接

---


##### `async _on_message_sent(data: Any) -> None`

**内部方法** message.sent 钩子：记录机器人出站文本

---


##### `get_by_trace(trace_id: str, limit: int = 20) -> 'list[dict[str, Any]]'`

按链路 ID 查询出站记录（影子模块 diff 对齐用，方向十一，含未落盘缓冲行）

- **trace_id**: 事件链路 ID（事件 ``id``）
- **limit**: 返回的最大条数

**返回值**: 消息列表（role / text / ts / event_id），时间升序

**示例**:

```python
transcript.get_by_trace("evt-abc123")
```

---

