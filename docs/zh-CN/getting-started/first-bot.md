# 创建第一个机器人

本指南将带你从零开始创建一个简单的 ErisPulse 机器人。

## 第一步：创建项目

使用 CLI 工具初始化项目：

```bash
# 交互式初始化
epsdk init

# 或者快速初始化
epsdk init -q -n my_first_bot
```

按照提示完成配置，建议选择：
- 项目名称：my_first_bot
- 日志级别：INFO
- 服务器：默认配置
- 适配器：选择你需要的平台（如 Yunhu）

## 第二步：查看项目结构

初始化后的项目结构：

```
my_first_bot/
├── config/
│   └── config.toml
├── main.py
└── requirements.txt
```

## 第三步：编写第一个命令

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
    print("正在初始化 ErisPulse...")
    # 运行 SDK 并且维持运行
    await sdk.run(keep_running=True)
    print("ErisPulse 初始化完成！")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 逐阶段手动控制

`sdk.init()` 内部自动完成了环境准备 → 适配器发现与启动 → 模块发现与初始化 → 路由启动。你也可以手动控制每个阶段，适合需要插入自定义逻辑的场景。

#### 完整手动启动

```python
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command
from ErisPulse.runtime import get_erispulse_config, setup_exception_handling

@command("hello", help="问候")
async def hello(event):
    await event.reply("你好！")

async def main():
    # ── 1. 环境准备 ──
    # 加载 TOML 配置文件、设置全局异常处理器
    get_erispulse_config()
    setup_exception_handling()

    # ── 2. 注册适配器 ──
    # 每种平台需要注册一个适配器类
    # 实际开发中通常由 pip install 的包自动注册（通过 entry_points）
    # from MyAdapter import MyPlatformAdapter
    # sdk.adapter.register("myplatform", MyPlatformAdapter)

    # ── 3. 启动适配器 ──
    # 异步启动所有已注册的平台适配器，建立与平台的连接
    await sdk.adapter.startup()

    # ── 4. 注册并加载模块 ──
    # 注册模块类后，调用 load() 会创建实例并触发 on_load()
    # from MyModule import MyModuleClass
    # sdk.module.register("MyModule", MyModuleClass)
    # await sdk.module.load("MyModule")

    # ── 5. 启动路由服务器 ──
    # FastAPI 服务器，提供 HTTP / WebSocket 路由
    # 如需自定义端口，直接传入 host 和 port
    await sdk.router.start(host="0.0.0.0", port=8000)

    # ── 6. 保持运行 ──
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 混合模式：init() 前后插入逻辑

大多数情况下，在 `sdk.init()` 前后插入自定义逻辑即可：

```python
async def main():
    # init 前的自定义操作
    # sdk.adapter.register("custom", CustomAdapter)

    if not await sdk.init():
        sdk.logger.error("初始化失败")
        return

    # init 后适配器和模块已就绪，可执行额外操作
    # await sdk.load_module("LazyModule")        # 强制加载懒加载模块
    # await sdk.adapter.startup("new_platform")  # 启动新注册的适配器

    await asyncio.Event().wait()
```

#### 运行时动态管理

```python
async def main():
    if not await sdk.init():
        return

    # 注册新适配器并启动
    sdk.adapter.register("dynamic", DynamicAdapter)
    await sdk.adapter.startup("dynamic")

    # 注册新模块并加载
    sdk.module.register("DynamicModule", DynamicModuleClass)
    await sdk.module.load("DynamicModule")
    # 现在可以通过 sdk.DynamicModule 访问

    # 查询状态
    print("运行中的适配器:", sdk.adapter.list_running())
    print("已加载的模块:", sdk.module.list_loaded())

    await asyncio.Event().wait()
```

#### 清理

```python
# 关闭指定适配器
await sdk.adapter.shutdown("yunhu")

# 卸载指定模块
await sdk.module.unload("MyModule")

# 停止路由服务器
await sdk.router.stop()

# 完整清理（关闭适配器 → 卸载模块 → 停路由 → 清事件 → 清缓存）
await sdk.uninit()
```

| 阶段 | 方法 | 说明 |
|------|------|------|
| 环境准备 | `get_erispulse_config()` + `setup_exception_handling()` | 加载配置、设置异常处理 |
| 注册适配器 | `sdk.adapter.register(platform, class)` | 注册平台适配器类 |
| 启动适配器 | `await sdk.adapter.startup()` | 异步启动已注册的适配器 |
| 注册模块 | `sdk.module.register(name, class)` | 注册模块类 |
| 加载模块 | `await sdk.module.load(name)` | 实例化模块并触发 `on_load()` |
| 启动路由 | `await sdk.router.start(host, port)` | 启动 FastAPI HTTP/WebSocket 服务器 |
| 保持运行 | `await asyncio.Event().wait()` | 阻塞等待，防止进程退出 |
| 清理 | `await sdk.adapter.shutdown()` / `await sdk.module.unload()` / `await sdk.uninit()` | 关闭适配器、卸载模块、清理资源 |

## 第四步：运行机器人

```bash
# 普通运行
epsdk run main.py

# 开发模式（支持热重载）
epsdk run main.py --reload
```

## 第五步：测试机器人

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
- 消息内容
- 发送者信息
- 平台信息
- 等等...

### 发送回复

```python
await event.reply("回复内容")
```

`event.reply()` 是一个便捷方法，用于向发送者发送消息。

## 扩展：添加更多功能

### 添加消息监听

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    """监听所有消息"""
    text = event.get_text()
    if "你好" in text:
        await event.reply("你好！")
```

### 添加通知监听

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    """监听好友添加事件"""
    user_id = event.get_user_id()
    await event.reply(f"欢迎添加我为好友！你的 ID 是 {user_id}")
```

### 使用存储系统

```python
# 获取计数器
count = sdk.storage.get("hello_count", 0)

# 增加计数
count += 1
sdk.storage.set("hello_count", count)

await event.reply(f"这是第 {count} 次调用 hello 命令")
```

## 常见问题

### 命令没有响应？

1. 检查适配器是否正确配置
2. 查看日志输出，确认是否有错误
3. 确认命令前缀是否正确（默认是 `/`）

### 如何修改命令前缀？

在 `config.toml` 中添加：

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### 如何支持多平台？

代码会自动适配所有已加载的平台适配器。只需确保你的逻辑兼容即可：

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("你好！来自云湖")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
```

## 下一步

- [基础概念](basic-concepts.md) - 深入了解 ErisPulse 的核心概念
- [事件处理入门](event-handling.md) - 学习处理各类事件
- [常见任务示例](common-tasks.md) - 掌握更多实用功能