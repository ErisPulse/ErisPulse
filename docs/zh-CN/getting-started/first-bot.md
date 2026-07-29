# 创建第一个机器人

本指南在 [5 分钟快速开始](../quick-start.md) 的基础上，带你编写第一个命令处理器并理解运行机制。

> 如果你还没装好 ErisPulse、初始化项目，请先完成 [快速开始](../quick-start.md) 的「安装」「初始化项目」「运行项目」三步。

## 第一步：编写第一个命令

打开 `main.py`，编写一个简单的命令处理器：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="发送问候消息")
async def hello_handler(event):
    """处理 hello 命令"""
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！我是 ErisPulse 机器人。")

@command("ping", help="测试机器人是否在线")
async def ping_handler(event):
    """处理 ping 命令"""
    await event.reply("Pong！机器人运行正常。")

async def main():
    """主入口函数"""
    print("正在启动 ErisPulse...")
    
    # keep_running=True（默认）：框架阻塞维持运行，直到收到关闭信号（如 Ctrl+C）
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### `keep_running` 参数

`sdk.run(keep_running)` 控制框架是否阻塞维持运行：

- **`keep_running=True`（默认）**：`run()` 会一直阻塞，直到收到关闭信号（如 Ctrl+C），适合纯 bot 应用。
- **`keep_running=False`**：`run()` 初始化完成后立即返回，**框架并不会卸载**——已启动的适配器/模块仍作为后台任务继续处理消息事件，你可以接着执行自己的逻辑，直到事件循环结束框架才随之关闭。例如：

```python
async def main():
    await sdk.run(keep_running=False)   # 初始化后立即返回
    # 框架已在后台运行，这里可以继续做别的事
    while True:
        await asyncio.sleep(3600)
        print("每小时检查一次")
```

> 除了 `run()` 的两种模式，还有 `init()`/`uninit()` 手动控制生命周期、单独启停适配器/路由等更精细的方式，见 [启动流程与手动控制](../advanced/startup.md)。

## 第二步：运行机器人

```bash
# 普通运行
epsdk run main.py

# 开发模式（支持热重载）
epsdk run main.py --reload
```

## 第三步：测试机器人

在你的聊天平台中发送命令：

```
/hello
```

你应该会收到机器人的回复。

## 代码说明

### 命令装饰器

```python
@command("hello", help="发送问候消息")
```

- `hello`：命令名称，用户通过 `/hello` 调用
- `help`：命令帮助说明，在 `/help` 命令中显示

### 事件参数

```python
async def hello_handler(event):
```

`event` 参数是一个 Event 对象，包含：
- 消息内容：`event.get_text()`
- 发送者信息：`event.get_user_id()`、`event.get_user_nickname()`
- 平台信息：`event.get_platform()`
- 群组信息：`event.get_group_id()`
- 原始数据：`event.get_raw()`

> 完整的 Event 对象方法请参考 [Event 包装类详解](../developer-guide/modules/event-wrapper.md)。

### 发送回复

```python
await event.reply("回复内容")
```

`event.reply()` 是一个便捷方法，用于向发送者发送消息。

## 扩展：添加更多功能

ErisPulse 提供了丰富的事件处理和数据处理能力：

- **消息监听**：使用 `@message.on_message()` 监听各类消息 → [事件处理入门](event-handling.md)
- **通知监听**：使用 `@notice.on_friend_add()` 等监听系统通知 → [事件处理入门](event-handling.md)
- **数据存储**：使用 `sdk.storage.get/set` 持久化数据 → [常见任务示例](common-tasks.md)

## 常见问题

### 命令没有响应？

1. 检查适配器是否正确配置，确认 `config/config.toml` 中适配器的 `status` 为 `true`
2. 查看终端日志输出，确认是否有错误信息（特别是 `ERROR` 级别日志）
3. 确认命令前缀是否正确（默认是 `/`），可在配置文件中查看 `[ErisPulse.event.command]` 部分
4. 确认命令名称拼写正确，注意大小写敏感性设置

### 如何修改命令前缀？

在 `config.toml` 中添加：

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### 如何支持多平台？

ErisPulse 使用 OneBot12 标准统一了不同平台的事件格式，`@command` 和 `@message` 注册的处理器会自动接收所有平台的事件。通过 `event.get_platform()` 可以区分来源平台：

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("你好！来自云湖")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("你好！")
```

> 更多多平台适配技巧请参考 [常见任务示例](common-tasks.md#多平台适配)。

## 下一步

- [基础概念](basic-concepts.md) - 深入了解 ErisPulse 的核心概念
- [事件处理入门](event-handling.md) - 学习处理各类事件
- [常见任务示例](common-tasks.md) - 掌握更多实用功能