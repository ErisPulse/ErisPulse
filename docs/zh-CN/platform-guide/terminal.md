# Terminal 平台特性文档

TerminalAdapter 是命令行终端适配器——终端即聊天会话，用于本地快速调试模块逻辑。

---

## 文档信息

- 对应模块版本: 1.2.2
- 维护者: ErisPulse
- 最后更新: 2026-11-10

## 基本信息

- 平台简介：把本地命令行当聊天会话，stdin 输入即消息，模块回复直接打印到终端
- 适配器名称：TerminalAdapter
- 平台标识：`terminal`
- 单账户设计（本地调试场景）
- 框架要求：软依赖 `ErisPulse>=2.7.1`（运行时检测提示，不强制）

## 配置说明

```toml
[Terminal]
bot_id = "terminal_bot"    # Bot 的用户 ID
bot_name = "TerminalBot"   # Bot 昵称
user_id = "terminal_user"  # 模拟用户的 ID（与 Bot 对话的终端用户）
user_name = "User"         # 模拟用户昵称
prompt = "> "              # 输入提示符
reply_prefix = "[Bot] "    # Bot 回复的行前缀（留空则不加前缀）
echo_input = false         # 是否回显用户输入（管道输入场景下开启）
```

## v5 范式更新（1.1.0）

- **spawn_background 任务归属**：stdin 读取循环改用 `runtime.spawn_background`
- **框架软依赖**：运行时检测 `ErisPulse>=2.7.1` 并提示；启动输出版本日志

## 标准化对齐（1.2.2）

响应结构与错误码遵循 [API 响应规范](../standards/api-response.md)。

### 消息事件补齐 message_id

stdin 消息事件补齐顶层标准 `message_id` 字段（uuid 生成），模块可稳定引用终端消息进行回复/去重。

### Send 继承 BaseAdapter.Send

`Send` 继承框架 `BaseAdapter.Send`，**标准修饰器链（`At` / `AtAll` / `Reply` 等）生效**，修饰段与文本段一并渲染输出；`node`（合并转发）段降级为纯文本原文输出（内容不丢失）。

### 元动作补齐

标准元动作已补齐，返回标准响应：

| 动作 | data 内容 |
|------|----------|
| `get_status` | `enabled`（运行状态）/ `boot_time`（启动时间戳） |
| `get_version` | `impl`（TerminalAdapter）/ `version` / `onebot_version` |
| `get_supported_actions` | 支持的动作名列表 |

```python
from ErisPulse import sdk
terminal = sdk.adapter.get("terminal")

result = await terminal.Api.get_status()
result = await terminal.Api.get_version()
result = await terminal.Api.get_supported_actions()
result = await terminal.Api.get_self_info()    # user_id/user_name
result = await terminal.Api.get_user_info("terminal_user")
result = await terminal.Api.get_friend_list()
```

### delete_message 能力降级语义修正

终端无撤回能力：`delete_message` 从"返回成功"修正为**能力降级标准语义**——返回 `retcode=10002`（不支持的操作），模块可据此判定降级。

### 错误码规范

| retcode | 含义 | 说明 |
|---------|------|------|
| 0 | 成功 | — |
| 10002 | 不支持 | 群组操作、消息撤回、未实现的标准动作 |

## 使用说明

```python
# 模块照常监听消息即可
from ErisPulse.Core.Event import message

@message.on_message()
async def handle(event):
    if event.get("platform") == "terminal":
        await event.reply("收到：" + event.get_text())
```

- 终端输入的文本即用户消息，支持多行（以空行结束）
- 事件结构示例（stdin 消息）：

```json
{
  "id": "<uuid>",
  "time": 1700000000,
  "message_id": "<uuid>",
  "type": "message",
  "detail_type": "private",
  "platform": "terminal",
  "self": {"platform": "terminal", "user_id": "terminal_bot", "user_name": "TerminalBot"},
  "user_id": "terminal_user",
  "message": [{"type": "text", "data": {"text": "输入内容"}}],
  "alt_message": "输入内容",
  "terminal_raw": {"text": "输入内容"},
  "terminal_raw_type": "stdin_line"
}
```

- 发送示例（修饰器链可用）：

```python
terminal = sdk.adapter.get("terminal")

await terminal.Send.To("private", "terminal_user").Text("Hello")
await terminal.Send.To("private", "terminal_user").At("terminal_user").Text("带修饰器的消息")
await terminal.Send.To("private", "terminal_user").Raw_ob12([
    {"type": "text", "data": {"text": "OneBot12 段"}}
])
```

- 适用于开发期快速验证模块逻辑，无需接入真实平台
