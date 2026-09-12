# Terminal 平台特性文档

TerminalAdapter 是命令行终端适配器——终端即聊天会话，用于本地快速调试模块逻辑。

---

## 文档信息

- 对应模块版本: 1.1.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：把本地命令行当聊天会话，stdin 输入即消息，模块回复直接打印到终端
- 适配器名称：TerminalAdapter
- 平台标识：`terminal`
- 单账户设计（本地调试场景）
- 框架要求：软依赖 `ErisPulse>=2.7.1`（运行时检测提示，不强制）

## 配置说明

```toml
[Terminal]
bot_id = "terminal_bot"   # 沙盒机器人ID
bot_name = "Terminal"     # 显示名称
```

## v5 范式更新（1.1.0）

- **spawn_background 任务归属**：stdin 读取循环改用 `runtime.spawn_background`
- **框架软依赖**：运行时检测 `ErisPulse>=2.7.1` 并提示；启动输出版本日志

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
- 适用于开发期快速验证模块逻辑，无需接入真实平台
