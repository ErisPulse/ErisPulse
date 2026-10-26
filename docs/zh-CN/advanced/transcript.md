# 会话收件箱（Transcript）

> [!TIP]
> **什么时候需要读这篇**：需要消息历史、对话恢复，或调整收件箱保留策略时。不需要则跳过，不影响其它功能的使用。


会话收件箱自动记录机器人收发的消息（按会话键 `platform:detail_type:target_id` 组织），
为对话恢复（`event.history`）、影子模块 diff、冷启动回放等提供历史数据。
本文档说明它的**存储模型、保留策略旋钮各保护什么**，以及运行时覆盖 API 与放开限制的真实代价。

> 改限制前请先读完「风险与审计」一节——每个旋钮都有它存在的理由。

## 工作原理

```
消息 ──append()──▶ 写缓冲（内存 deque，硬上限 4096 行）
                        │  每 1 秒批量落盘（单批 ≤64 行，单事务）
                        ▼
              storage 后端的 transcript 表（默认 sqlite）
                        │  每 ~32 条追加惰性触发一次保留清理
                        ▼
              ┌─ 按会话 FIFO 裁剪（max_per_session，默认 50 条）
              └─ 全局 TTL 删除（ttl_hours，默认 168 = 7 天）
```

三个层级的保护，各自防的是不同的风险：

| 旋钮 | 默认值 | 保护什么 | 关闭（=0）的后果 |
|------|--------|----------|------------------|
| 写缓冲上限 | 4096 行（常量，不可配） | **内存**：存储不可用期间的积压不撑爆 RAM | 不可关闭——这是内存防线 |
| 单条文本截断 | 2000 字符（常量，不可配） | 单条消息的内存/磁盘占用 | 不可关闭 |
| `max_per_session` | 50 条/会话 | **磁盘增长**：单会话历史无限堆积 | 该会话历史无限增长 |
| `ttl_hours` | 168（7 天） | **磁盘增长**：全部会话的长期堆积 | `transcript` 表无限增长 |

关键认知：**写缓冲有硬上限，所以放开保留策略不会直接撑爆内存**；
真正的风险在存储层与下游消费者（见下节）。

> [!TIP]
> **不需要会话记忆的应用可以整体关闭**：`ErisPulse.transcript.enabled = false`
> 即停止入站/出站消息的自动记录——不写内存缓冲也不写存储，省下常驻内存与持续的
> 存储层 IO。会话收件箱主要服务 AI 上下文注入与防复读两类需求，二者都不用的部署
> （如纯命令型机器人）建议关闭。

## 配置

```toml
[ErisPulse.transcript]
enabled = true          # 是否自动记录
max_per_session = 50    # 单会话保留条数（0 = 关闭该会话裁剪）
ttl_hours = 168.0       # 全局保留时长（小时，0 = 永不清理）
self_echo = "bot"       # 入站 bot 回声处理：bot / skip / user
```

环境变量覆盖同样生效：`ERISPULSE_TRANSCRIPT_MAX_PER_SESSION`、`ERISPULSE_TRANSCRIPT_TTL_HOURS`、
`ERISPULSE_TRANSCRIPT_SELF_ECHO`。
配置变更热生效（写缓冲落盘节奏内，最多延迟 ~1 秒）。

> [!TIP]
> **不需要会话记忆就关闭它**：收件箱唯一的消费方是对话恢复 / 影子 diff / 冷启动回放。
> 如果你的机器人（或部署的模块）完全不用这些能力，设置 `enabled = false`
> 即可省下收件箱的内存缓冲与后台批量落盘 IO——消息收发与命令处理完全不受影响。

## 消息归因（sender 与 meta）

所有查询接口（`get` / `recent` / `get_by_trace` / `event.history`）的每条记录
统一携带归因字段，用于区分"谁说的 / 哪个模块发的"：

| 字段 | 含义 |
|------|------|
| `sender` | 发送者标识：入站为 `user_id`，出站为 bot 账号 / 回声时的 `self.user_id` |
| `meta` | 记录时刻的元数据（白名单契约，非完整 raw event） |

`meta` 白名单：

- **入站**：`nickname`（事件时刻的昵称，事后反查拿到的是"现在的昵称"）、
  `self_id`（bot 账号）、`sub_type`、`message_id`；回声消息额外带 `self_echo: true`；
- **出站**：发送上下文（`platform` / `method` / `detail_type` / `target_id` /
  `bot_id` / `trace_id` / `preview`）与 `module`（发送归属模块，见下）。

旧版本记录（无 meta 列时期）的 `meta` 为 `{}`，调用方 `meta.get("nickname", "")`
自然降级；存储后端不支持 ALTER 时同样静默回退 `{}`。

### 出站归属（meta.module）

同一实例上多个模块都会发消息（聊天、管理、定时提醒）。出站记录的 `meta.module`
标识发送归属，取值优先级为 `current_owner > current_caller > ""`：

| 发送场景 | module 值 |
|----------|-----------|
| 模块代码经 `module.call` 被调用期间 | 目标模块名 |
| 模块的事件处理器内发送 | 注册该处理器的模块名（分发期自动注入） |
| 框架自身 / 无模块上下文 | `""` |

`message.sent` / `message.sending` 钩子载荷（send_ctx）同样携带 `module` 字段。

### 入站 bot 回声（self_echo）

部分平台/协议端会把 bot 自己发出的消息以 message 事件回显上报（如 OneBot v11 的
`report-self-message`、Telegram outgoing message）。框架在入站记录前按
`self.user_id == user_id` 识别回声，按 `self_echo` 配置处理：

| 取值 | 行为 |
|------|------|
| `"bot"`（默认） | 仍记录，但 `role="bot"`、`sender=self_id`、`meta.self_echo=true` |
| `"skip"` | 不记录（适配器同时会触发 `message.sent` 时天然有出站记录） |
| `"user"` | 记 `role="user"`（旧行为，兼容逃生口） |

不回显的平台（`self.user_id != user_id` 恒成立）行为与关闭本功能完全一致。

### 按会话过滤的 recent

```python
from ErisPulse import transcript

# 跨会话全局时间窗（冷启动回放语义，默认）
transcript.recent(3600)

# 限定单会话：服务端过滤，避免全局拉取后客户端逐条比对 session_key
transcript.recent(3600, session_key="onebot11:group:123")
```

`session_key=None` 保持跨会话语义；空串 `""` 等价不过滤（容错）。

## 运行时覆盖 API

需要在运行中动态调整（如临时为某个场景延长保留）时：

```python
from ErisPulse import transcript

# 覆盖（优先于配置；仅驻内存，重启后恢复配置值）
transcript.set_retention(max_per_session=500, ttl_hours=24 * 30)

# 查询生效值与来源
transcript.get_retention()
# {'max_per_session': 500, 'ttl_hours': 720.0, 'overridden': ['max_per_session', 'ttl_hours']}

# 恢复按配置生效
transcript.reset_retention()
```

- 传 `0` = 关闭对应策略（会打 warning 日志留痕）；负数抛 `ValueError`；
- 覆盖在下次保留清理时生效（惰性，最多延迟 ~32 条追加的节奏）；
- `transcript` 单例可从根包导入，也可 `sdk.transcript`。

## 风险与审计：放开限制前必读

关闭 `max_per_session` / `ttl_hours`（或大幅调大）后，`transcript` 表随消息量
**无限增长**。后果链：

1. **磁盘写满**——sqlite 单文件持续膨胀，磁盘耗尽后框架存储层不可用；
2. **查询退化**——`get()` / `recent()` / `get_by_trace()` 的扫描成本随表增长；
3. **下游内存压力（OOM 的真实来源）**——把历史整段载入内存的消费者
   （对话恢复带历史、面板全量拉取、你的业务代码 `get(session, n)` 取大 n）
   会随表增长吃掉内存，极端情况触发 OOM kill。

**放开前请自问三件事**：要多久的历史？要多大？谁来清理？
如果答案依赖"永远不删"，正确做法通常是外置归档（定期把旧数据搬到专用库），
而不是让收件箱无限保留。

审计手段（定期检查表规模）：

```python
# 经 ORM/SQL 构建器查行数与体积（sqlite 为例）
from ErisPulse import storage

row = storage.Table("transcript").raw_sql("SELECT COUNT(*) AS n FROM transcript")
```

```sql
-- 直接对 sqlite 文件查询（表体积）
SELECT COUNT(*) FROM transcript;
```

收到 `保留策略已被关闭` 的 warning 日志 = 有人以 0 关闭了策略，请确认是自己的操作。

## 与其它机制的边界

- **交互会话定时器 / wait_reply**：见 [交互会话系统](interaction.md)，与收件箱无关；
- **对话恢复的历史带回**：`resume(with_history=N)` 从收件箱取最近 N 条——
  收件箱被裁剪后能带回的历史随之变少（调大 `max_per_session` 可延长可恢复窗口）；
- **影子模块 diff**：依赖 `get_by_trace` 链路查询，TTL 过短的收件箱会缩短可 diff 窗口。

## 相关文档

- **消费收件箱历史的地方**：对话恢复 [Conversation](conversation.md)、事件级读取 [event.history](interaction.md#会话收件箱eventhistory)、影子 diff [影子模块与灰度转正](shadow.md)
- **审计表规模用到的存储接口** → [存储后端](storage-backends.md) 与 [SQL 查询构建器](sql-builder.md)
