# 交互会话系统

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
  （或执行 `callback(event)`，支持同步 / 异步）
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
  `(下标, 回复事件)` → 未命中的等待自动取消；全部超时返回 `(None, None)`
- 命中的事件已被框架认领（`mark_processed`），不会被其他处理器重复消费

{!--< tips >!--}
`select` 与多线程 `asyncio.wait` 手工编排相比：期望未命中时自动清理、
命中事件自动认领、权限复查与归属清理全部生效——不需要自己管任何 Future。
{!--< /tips >!--}

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

每会话近期消息流的统一记录（用户 + 机器人双方），作为 AI 上下文、
防复读、行为分析类模块的**共享事实底座**——各模块不再各自存历史。

```python
messages = await event.history(20)   # 当前会话最近 20 条，时间升序
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- 自动记录：入站消息（role=user）+ 机器人出站文本（role=bot）
- 存储：独立 SQLite 表，保留策略 = 每会话上限（默认 50）+ 全局 TTL（默认 7 天）
- 配置：`ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- 管理器 API：`sdk.transcript.append() / get() / clear()`

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
- 定向事件（`emit_to`）与消息事务回执

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
