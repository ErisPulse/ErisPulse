---
name: erispulse-shadow-transcript
description: "适用于：新旧版本灰度对照（shadow）、消息收件箱与行为追踪（transcript）。覆盖场景：需要灰度发布——新版本并行试运行、行为对比与转正回滚时。需要消息历史、对话恢复，或调整收件箱保留策略时。"
---

# ErisPulse 影子灰度与消息追踪

本技能由 ErisPulse 文档自动构建（generate-skills.py）。
仓库：https://github.com/ErisPulse/ErisPulse
各节末尾标注了来源文档路径，需要最新内容请以仓库 docs/zh-CN/ 为准。

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 影子模块: 29-59 行
- 快速上手: 61-87 行
- 五道隔离闸: 89-99 行
- 诚实边界（拦不住的）: 101-110 行
- 转正与回滚: 112-121 行
- 消息追踪: 123-137 行
- 工作原理: 139-168 行
- 配置: 170-187 行
- 消息归因（sender 与 meta）: 189-248 行
- 运行时覆盖 API: 250-270 行
- 风险与审计：放开限制前必读: 272-301 行
- 与其它机制的边界: 303-309 行

## 影子模块

> 来源: `docs/zh-CN/advanced/shadow.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/advanced/shadow.md）

# 影子模块与灰度转正

> [!TIP]
> **什么时候需要读这篇**：需要灰度发布——新版本并行试运行、行为对比与转正回滚时。不需要则跳过，不影响其它功能的使用。

> **读完你会知道**：影子模块的五道隔离闸、行为 diff 的对齐方式、
> `promote` 转正与失败回滚流程，以及框架拦不住的诚实边界。
>
> **本篇不涉及**：普通模块的热重载与归属清理通用机制
> （见[归属权（owner）系统](ownership.md)）。


影子 = 同一模块的**新版本**，以独立 owner（如 `roll_shadow`）与线上旧版
并存试运行：它收到真实事件的**副本**、其出站被**拦截记账**而非真正发出——
在 `shadow_diff` 里对比两个版本的行为，确认无害后 `promote` 一键转正，
`dismiss` 随时放弃。**模块代码零改动，全程运行时 API 驱动**：与
`load / unload / reload` 同类的运维动作，Dashboard / 自定义管理模块直接
调用，没有任何配置项要写。

{!--< tips >!--}
1. 启动：``await sdk.module.shadow_start("roll", source="路径/到/v2")``
   ——新版代码以独立 owner（默认取路径名）与旧版并存
2. 影子不参与真实分发与依赖图：同名命令进影子目录、路由只登记不挂载、
   生命周期广播静默、`module.call` 与依赖解析仍指向 v1
3. 转正永远由人确认：``await sdk.module.promote_shadow("roll")``，失败
   自动回滚旧实例继续服务；``dismiss_shadow`` 随时放弃
{!--< /tips >!--}

## 快速上手

```python
# v2 代码：普通模块写法，零影子感知（任意目录，如 downloads/roll_v2/）
```

```python
# 线上机器人里（Dashboard / 管理模块调用），一行启动灰度：
await sdk.module.shadow_start("roll", source="downloads/roll_v2")
# → 影子以独立 owner "roll_v2" 与 v1 并存，出站被拦截记账

# 试运行期间对比行为：
report = sdk.module.shadow_diff("roll")
# {"shadow_owner": "roll_v2", "count": 3, "aligned": [...]}
```

- **v1 实际发送**：来自收件箱（transcript）的 bot 时间线
- **v2 意向发送**：影子账本（出站闸记录的"想发什么"）
- 两者按 `trace_id` 对齐——同一条消息，两个版本各自为什么触发/没触发、
  想发什么/实际发了什么，一目了然

确认无误后转正：

```python
await sdk.module.promote_shadow("roll")   # 转正，失败自动回滚 v1
await sdk.module.dismiss_shadow("roll")   # 或：放弃影子
```

## 五道隔离闸

| 闸 | 机制 |
|----|------|
| 事件副本 | 影子处理器收到事件的**独立副本**（带 `shadow` 标记）——影子的改写 / 认领 / 停止传播只作用于副本，不影响原事件链 |
| 出站闸门 | 影子的 `Send` DSL 与 `Api` 调用全部拦截记账（成功形状假响应），不真正发出——影子不会重复回复 |
| 存储覆盖层 | 影子的 KV 写进入内存覆盖层并丢弃落库；读先查覆盖层、未命中透传真库（灰度对着真实数据跑）；删除记墓碑 |
| 路由屏蔽 | 影子的 HTTP/WS/SSE 路由只登记不挂载；同名命令进影子命令目录、平台事件方法注入禁止 |
| 生命周期静默 | 影子不广播自身的生命周期事件、不参与生态依赖图（`module.call` 与依赖解析仍指向 v1，避免半成品被依赖） |

配置继承：影子默认**继承原模块的配置节**（否则灰度失真），转正后配置原地生效。

## 诚实边界（拦不住的）

- 走框架的发送 / API / KV 存储 / 统一 HTTP 客户端**全部拦得住**；
  模块绕过框架裸起 `aiohttp`、开线程写外部系统——框架拦不住
- **ORM 读写不在覆盖层语义内**（按行 overlay 无法在 SQL 层干净实现）——
  影子期间建议避免依赖 ORM 写隔离
- **影子源为本地路径**：新版代码以路径导入、独立 owner 装载；同一 PyPI 包
  在同解释器内受 `sys.modules` 单键限制，无法新旧两版本并存
- 泄漏审计器（`sdk.module.audit`）可见影子资源归属；绕过框架的副作用
  至少不会无声

## 转正与回滚

`promote` 流程：快照当前版本（含级联依赖者）→ 完全卸载 → 影子以真名注册
加载 → 任一步失败自动回滚、旧实例继续服务（尽力而为语义：`on_unload` 已
执行的副作用不可撤销，回滚后旧实例处于已收尾态）。转正成功的影子资源被
回收、绑定解除；原模块配置节原地生效。

**持久化提醒**：promote 是运行时切换——重启后仍以 v2 运行，需要把新版本
**持久化安装**（`pip install -U` 新版本 / 替换插件文件）。运行时切换不会
替你完成包管理。

## 消息追踪

> 来源: `docs/zh-CN/advanced/transcript.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/advanced/transcript.md）

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
