# 交互会话系统

> [!TIP]
> **什么时候需要读这篇**：需要 wait_reply、多轮对话、定时提醒、会话互斥或链路追踪时。不需要则跳过，不影响其它功能的使用。

> **读完你会知道**：`wait_reply` 的全参数用法与取消原因、`.got()` 声明式多轮链、
> 会话定时器（remind / escalate）、多路等待（expect / select）与会话互斥租约。
>
> **本篇不涉及**：多轮对话的分支状态机与重启恢复（见[Conversation 多轮对话](conversation.md)）；
> 收件箱保留策略旋钮与运行时覆盖（见[会话收件箱](transcript.md)）。

> [!NOTE]
> 本章内容需要 ErisPulse **2.8.0+**。

ErisPulse 把"与用户的持续交互"做成了框架级基础设施：从一条 `wait_reply`，
到定时提醒、多路等待、会话互斥、重启恢复，全部由统一的
**交互会话管理器**（`Core/Event/interaction.py`，`sdk.interaction`）调度。

{!--< tips >!--}
本文覆盖的每一项能力都自带**归属（owner）**：交互等待、租约、定时器全部记录
注册时的模块名，模块卸载 / 适配器关闭时由框架自动清理，等待方立即得到通知
而非干等超时——这是归属权系统在交互维度的延伸（见 [归属权系统](ownership.md)）。
{!--< /tips >!--}

## 等待回复：wait_reply

**一句话**：挂起当前协程等目标用户的下一条消息，命中返回回复事件、超时或被取消返回 `None`，`pattern` / `regex` / `validator` 可过滤不合格回复。

`wait_reply` 是交互会话的基石——挂起当前协程，等待目标用户在下一条消息中"回复"。

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    reply = await event.wait_reply(prompt="请输入你的名字:", timeout=30)
    if reply is None:
        await event.reply("超时了")
        return
    await event.reply(f"你好，{reply.get_text()}！")
```

### 全参数一览

| 参数 | 说明 | 默认 |
|------|------|------|
| `prompt` | 挂起前发送的提示消息 | None |
| `timeout` | 等待超时（秒） | 60 |
| `pattern` | glob 过滤（`*` / `?` / `[seq]`），不匹配继续等待 | None |
| `regex` | 正则过滤（与 pattern 同时给定时须都匹配），不匹配继续等待 | None |
| `validator` | 校验函数（接收 Event，返回 bool），失败继续等待 | None |
| `callback` | 收到回复时的回调（替代返回值式的另一种写法） | None |
| `method` | prompt 的发送方法 | "Text" |
| `session` | **会话级等待**：同会话（群 / 频道）中任何人的回复均可命中 | False |

```python
# 只接受数字金额，否则继续等
reply = await event.wait_reply("请输入金额:", regex=r"\d+\s*元", timeout=30)

# 会话级等待：群协作场景，任何群友回答均可
reply = await event.wait_reply(session=True, prompt="哪位大佬帮忙答一下？")
```

### 等待与命令的边界（命令穿透）

等待期间收到**已注册命令**（如 `/cancel`）的消息时，默认放行给命令分发器执行、
不作为回复消费（配置项 `ErisPulse.event.wait_reply.cmdpass`，`True` 则反转——
消息一律作为回复）。判定文本口径与命令分发一致：`alt_message` 优先、
缺失时回退消息段拼接（2.10.1 起纯 message 段适配器同样生效）。

### 等待会在什么时候被取消

等待不再是"只能等超时"——以下情况会让等待**立即终止**（`wait_reply` 返回 `None`），
而不是让调用方干等到超时：

| 触发 | 取消原因（`InteractionCancelled.reason`） | 说明 |
|------|------|------|
| 归属模块被卸载 / 禁用 | `owner_unload` | 归属清理：谁注册的等待，谁消失时一并回收 |
| 适配器关闭 / 重启 | `platform_stop` | 该平台挂起的等待全部取消 |
| 同会话被新的等待 / 租约取代 | `conflict` | 见下方"会话仲裁" |
| 回复者被拉黑 / owner 模块被解绑 | `revoked` | 回复命中的**权限复查**：scope 身份维度 + 模块维度 |
| 用户回复命中 | —— | 正常路径，返回回复事件 |

底层异常为 `InteractionCancelled`（挂在 `InteractionError` 异常体系下），
`wait_reply` 已将其转换为返回 `None`；需要原因的调用方可直接使用
`sdk.interaction.register()` 低层 API。

### 回复命中的完整判定链

一条回复消息到达时，交互管理器按以下顺序判定（在命令匹配**之前**执行，
对话连续性优先——即使消息已被其他高优先级处理器认领，挂起的对话也能完成）：

```
会话键命中（精确 user 维度 → 会话级回退）
  → pattern / regex 文本过滤（不匹配继续等）
  → validator 校验（失败继续等）
  → 权限复查（scope 身份维度 + owner 模块维度，失败则终止等待）
  → 唤醒等待方 + 认领事件（mark_processed）
```

## 声明式多轮：`.got()` 链（2.11+）

`@command` 返回**多轮流控代理**，用 `.got()` 逐步声明收集步骤——步骤函数按
参数名接收已收集的值（含命令入口参数），类型跟随 `type=` / 注解自动解析。
底层编译到 Conversation：每步一个分支、跳转自动保存检查点，**重启后用户
回复会从存档步骤继续**（恢复工厂在装饰期自动注册，随模块卸载自动注销）。

```python
@command("weather")
async def weather(event):
    pass  # 入口：首个 .got 的 prompt 会自动发送，无需手动提问

@weather.got("city", prompt="请直接回复城市名")
async def weather_city(event, city: str):
    await event.reply(f"{city}：晴，25℃")

@weather.got("days", prompt="预报几天？", type=int, retry_prompt="请输入数字")
async def weather_days(event, city: str, days: int):
    await event.reply(f"{city} 未来 {days} 天……")
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `name` | 收集值名称（注入后续步骤函数的参数名；流程内唯一，重复声明注册期报错） |
| `prompt` | 进入该步骤时自动发送的提问 |
| `timeout` | 单步等待超时（秒数或 `"90s"` / `"1h30m"` 时长串，默认 60s） |
| `type` | 值类型（`int` / `float` / `str`…；解析失败自动重发 `retry_prompt`，最多 `max_retries` 次） |
| `validator` / `pattern` / `regex` | 回复过滤与校验（语义与 [`wait_reply`](#等待回复wait_reply) 一致） |
| `session` | 会话级等待（同会话任何人可命中） |
| `cmdpass` | 命令放行三态（默认 `/cancel` 等命令在等待期间照常执行） |

### 语义与边界

- **任一步超时 / 被打断 → 整条流程结束**并清除检查点（与 `wait_reply` 语义一致）；
  步骤函数内可随时 `event.reply(...)` 输出中间结果
- **同一用户同时只能有一条挂起交互**——第二个流程的等待会顶掉前一个
  （`InteractionCancelled("conflict")`）；需要互斥提示请配合
  [会话租约](#会话互斥acquire--hold--get_owner_of)
- 收集值仅存在于流程内；需要跨重启携带复杂状态的编排请直接使用
  [Conversation](conversation.md)（`context` + `branch/goto` + 手动检查点）
- `@command` 返回的是代理对象：调用行为、`__name__`、docstring、自定义属性
  与原函数完全一致；`command.unregister(代理)` 自动解包

## 会话定时器：remind / escalate

把"超时"从返回值变成可编排的原语。定时器挂在交互会话上，
随模块卸载 / 适配器关闭自动取消，单会话活跃 remind 上限 5 个。

### remind：没回复就提醒

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("工单已提交，处理结果会在这里通知")
    # 5 分钟无回复则温和催一次；用户任何回复都会自动取消它
    event.remind(300, "还在吗？有结果了会第一时间告诉你")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`：到期向当前会话发送 `text`
  （或执行 `callback(event)`，支持同步 / 异步）。**强制校验**：`text` 与
  `callback` 必须二选一（都不给抛 `ValueError`）
- 返回 `Reminder` 句柄：`reminder.cancel()` 手动取消、`reminder.expired` 查询状态
- 用户在该会话**回复后自动取消**——这正是"提醒"语义：
  提醒只在用户沉默时出现
- `Conversation` 内同样可用：`conv.remind(120, "还在考虑吗？")`

### escalate：到点必达的升级

```python
event.escalate(1800, lambda e: notify_master(f"工单 30 分钟未处理：{event.get_command_args()}"))
```

与 `remind` 的唯一区别：**不被用户回复取消**——升级动作（通知主人、转人工）
是"超时必达"承诺，仅手动 `cancel()` / 模块卸载 / 适配器关闭才取消。

| | `remind` | `escalate` |
|---|---|---|
| 到期行为 | 发文本 / 执行 callback | 执行 callback |
| 用户回复 | **自动取消** | 不受影响 |
| 归属清理（卸载 / 关平台） | 取消 | 取消 |
| 单会话上限 | 5 | 不限（随归属清理兜底） |

## 多路等待：expect + select

**一句话**：`expect` 只描述期望不注册等待，`select` 统一挂起多条期望，任一先命中即返回 `(下标, 回复事件)`，未命中的自动清理。

同时挂起多条期望，**先到先得**——典型场景：等管理员审批的同时等用户撤回、
多人协作投票。

```python
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒绝*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "搁置", session=True),
    timeout=60,
)
if which is None:
    await event.reply("60 秒内未收到任何审批结果")
elif which == 0:
    await event.reply("已同意")
elif which == 1:
    await event.reply("已拒绝")
```

- `event.expect(...)` 构造**期望描述**（不注册任何等待）：支持
  `pattern` / `regex` / `validator` / `user`（限定回复者）/ `session`（任何人可答）
- `event.select(*expectations, timeout=60)`：统一注册 → 任一命中即返回
  `(下标, 回复事件)` → 未命中的等待自动取消；全部超时返回 `(None, None)`。
  **强制校验**：至少传入一条 expectation，否则抛 `ValueError`
- 命中的事件已被框架认领（`mark_processed`），不会被其他处理器重复消费

{!--< tips >!--}
`select` 与多线程 `asyncio.wait` 手工编排相比：期望未命中时自动清理、
命中事件自动认领、权限复查与归属清理全部生效——不需要自己管任何 Future。
{!--< /tips >!--}

> [!NOTE]
> 2.10.1 起 `select` 为**聚合等待**：全部期望合并为单条目 + 自定义命中判定，
> 同键多路（如同一 user 挂两条不同 pattern）不再互相取消，任一路先命中即返回。
> 回复文本的判定口径为 `alt_message` 优先 + 消息段回退（与命令分发一致）。
>
> 边界说明：`event.wait_for(...)` 直挂在适配器事件总线上，**不经过**中间件与
> detail_type 条件过滤（身份准入由分发入口兜底）；需要完整管线的等待请用
> `wait_reply` / `select`。

## 会话互斥：acquire / hold / get_owner_of

归属权从"资源"走向"会话"——"这个用户当前正被谁占用"成为一等查询。

```python
# 查询：这个会话正被谁交互？（空闲返回 None）
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # 其他模块正在对话中，避免打扰

# 互斥租约：独占会话（deny 策略，被占用返回 None）
lease = sdk.interaction.acquire(event)          # 默认 TTL 1 小时，可传 ttl=
if lease is None:
    return  # 已被占用
try:
    ...  # 独占交互
finally:
    lease.release()
```

上下文管理器形式（获取失败抛 `SessionOccupiedError`）：

```python
with sdk.interaction.hold(event) as lease:
    ...  # 退出自动释放
```

租约支持 `renew(ttl)` 续期；TTL 惰性过期——过期的租约在下次访问时自动清理。

`Conversation.resume()` 恢复对话时框架会自动 acquire 租约（见
[Conversation 多轮对话](conversation.md)的"恢复即接管"）——
恢复的对话天然持有会话，其他模块不会插入。

## 会话收件箱：event.history

> 保留策略（7 天 / 条数上限）与运行时覆盖 API、风险与审计见[会话收件箱](transcript.md)专题。

每会话近期消息流的统一记录（用户 + 机器人双方），作为 AI 上下文、
防复读、行为分析类模块的**共享事实底座**——各模块不再各自存历史。

```python
messages = await event.history(20)   # 当前会话最近 20 条，时间升序
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- 自动记录：入站消息（role=user）+ 机器人出站文本（role=bot）
- 存储：独立 SQLite 表，保留策略 = 每会话上限（默认 50）+ 全局 TTL（默认 7 天）
- 写入方式：内存缓冲 + 后台批量落盘（延迟至多 1 秒），查询接口自动合并未落盘的缓冲行——同进程"读你的写"不受影响；正常退出（`sdk.uninit` / 进程退出）自动刷盘。**硬崩溃 / 强杀时最近约 1 秒的记录可能丢失**：该底座定位为近期上下文缓存，不适合作为审计级持久化
- 配置：`ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- 管理器 API：`sdk.transcript.append() / get() / clear()`，`aflush()` / `flush()` 手动刷盘

## 消息事务：message_tx

事务内的所有出站发送自动记账；**异常退出时逆序自动撤回**已发送的消息
（适配器未实现 `delete_message` 时跳过，账本仍正常记录）。

```python
async with event.message_tx():
    await event.reply("正在处理，请稍候")
    result = await do_something()          # 这里抛异常 →
    await event.reply(f"完成: {result}")   # 前面的"处理中"自动撤回
```

事务外发送不记账（零开销）；`get_send_receipts()` 可查看当前事务已发送的回执。

## 链路追踪：trace-id

每个入站事件自动获得追踪 ID（复用 `event["id"]`，缺失则生成），贯穿：

- handler 上下文（`get_current_trace_id()` 读取）
- 出站发送（`[Send]` 日志行附加 `[trace:...]`，`message.sending/sent` 钩子的 `trace_id` 字段）
- 生命周期钩子数据（dict 自动补 `_trace_id`）
- 定向事件（`lifecycle.emit(..., to=...)`）与消息事务回执

一条消息被多个模块接力处理时，全链路可用同一 ID 串联（日志 / 慢查询 / 审计）。

## 与其他系统的关系

- **归属权**：等待 / 租约 / 定时器全部记录 owner，卸载即回收（[归属权系统](ownership.md)）
- **作用域**：回复命中复查身份 + 模块维度；跨模块调用审计走出站维度（[作用域](scope.md)）
- **Conversation**：多轮对话是交互会话之上的分支状态机（[Conversation](conversation.md)），
  其等待同样享有本页全部取消 / 复查 / 归属语义

## 相关文档

- [Conversation 多轮对话](conversation.md) - 分支状态机、自动检查点与重启恢复
- [归属权（owner）系统](ownership.md) - 归属清理的全景与设计边界
- [作用域（scope）](scope.md) - 权限复查与出站审计的配置方式
- [模块间通信](module-communication.md) - 跨模块调用与定向事件
