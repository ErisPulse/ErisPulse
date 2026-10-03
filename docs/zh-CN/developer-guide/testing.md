# 模块测试（ErisPulse-Testing）

[ErisPulse-Testing](https://github.com/ErisPulse/ErisPulse-Testing) 是官方测试工具包（RFC EPRFC-2026-001 方向三）：
提供 `TestBot`、测试事件工厂、出站消息捕获与断言面，让模块测试像写普通 pytest 一样简单。

```bash
pip install ErisPulse-Testing
```

> 单向依赖框架的开发期工具，运行时零介入。真连适配器平台的冒烟测试请使用框架仓库的 `tests/devs/test_adapter.py`。

## 快速开始

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="今天已签到")
        async def daily(event):
            await event.reply("签到成功！")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "签到成功！"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("今天已签到")   # 第二次命中冷却
```

`TestBot` 推荐以 `async with` 使用：启动时注册 MockAdapter（捕获全部出站）、
关闭事件去重、应用配置覆写；退出时自动清理框架全局状态，用例之间互不污染。

配套 pytest fixtures（安装后自动可用）：

- `testbot`：function 级标准 TestBot（platform=`test`、前缀 `/`）
- `make_testbot(**kwargs)`：自定义参数工厂（`prefix` / `config` / `platform` / `bot_id` ...）

建议在测试项目配置 `asyncio_mode = "auto"`（`[tool.pytest.ini_options]`），
或给用例加 `@pytest.mark.asyncio`。

## 事件工厂

| 函数 | 说明 |
|------|------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | 消息事件；`group_id` 为空即私聊 |
| `create_command_event("roll 3", prefix="/")` | 命令消息（自动加前缀，已带前缀不重复） |
| `create_notice_event(type, ...)` | 通知事件（如 `friend_add`） |
| `create_request_event(type, ...)` | 请求事件（如好友申请） |
| `create_meta_event("connect", ...)` | meta 事件（connect 可让 Bot 上线） |

所有事件使用 uuid 唯一 `id`，天然避开框架的事件去重。

注意：合成事件**不含平台原始报文**（`event.get_raw()` 返回空 dict）。判断群聊 /
私聊等场景请用 `event.is_group_message()` / `event.get_detail_type()` /
`event.get_group_id()` 等访问器，不要读 raw。

## TestBot API

### 分发

```python
trace = await bot.dispatch(event)          # 分发并等待处理器落地，返回决策链
await bot.dispatch(event, drain=False)     # 交互首消息：不等待（wait_reply 处理器长驻）
await bot.send_message("你好")             # 消息分发快捷方式
await bot.reply_as("18", user_id="u1")     # 模拟 wait_reply 用户回复（自动等 waiter 就绪）
```

`dispatch()` 在 emit 后 gather 全部在途处理器 Task，返回即处理完成——**测试里不需要 sleep**。

### 出站断言

```python
bot.replies                # 全部出站（SentMessage 列表）
bot.last_reply.text        # 最近一条回复的文本
bot.replies_to("123")      # 按目标过滤
bot.clear_replies()        # 阶段间隔离断言
bot.assert_replied()                       # 存在出站
bot.assert_replied(contains="签到", to="123")
bot.assert_not_replied()                   # 无任何出站
bot.assert_reply_contains("签到成功")       # 存在包含指定文本的出站
await bot.wait_for_reply(timeout=2)        # 等待异步回复出现
```

`SentMessage` 字段：`text`（首个 text 段）、`segments`（完整消息段）、
`target_type` / `target_id` / `bot_id`（发送上下文）、`has_modifier("at")` 等。

### 模块加载

```python
await bot.load_module("MyModule")   # 已注册的模块名（需框架 sdk.init() 完成 entry-point 发现）
await bot.load_module(MyModule)     # 或 BaseModule 子类（自动 register + load，推荐）
await bot.unload_module("MyModule")
```

`on_load` 内注册的命令 / 事件处理器随模块归属，卸载时自动清理，可直接断言"卸载后命令失效"。
注意：字符串形式**不做 entry-point 扫描**（TestBot 不初始化框架发现流程）；测试软依赖
模块请直接传类对象（或自行 `module.register` 后传名字）。

### 依赖替换（需 EP>=2.9.0-dev）

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

替换的是命令注册表中 `Depends(get_session)` 声明引用的函数，with 退出自动还原。

### 配置覆写

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # 模块配置（self.cfg 可读）
})
```

经配置内存层注入，命令前缀等随热更新立即生效。两点注意：

1. **落盘**：覆写会随框架的延迟写盘策略（默认约 5 秒）落到 cwd 的
   `config/config.toml`——被测项目仓库请把 `config/` 加入 `.gitignore`；
2. **与模块运行时写回的冲突（已知限制）**：被测模块以整节写回配置
   （`self.cfg = ...`，如订阅列表）与这里的点分覆写并存时，存在 ConfigManager
   的读写一致性问题——模块整节读取可能看不到覆写值，覆写也可能在落盘时被
   整节写回覆盖（已在 ErisPulse 2.9.0-dev.2 修复，2.8.x 仍受影响）。涉及
   "运行时写回配置"的用例，在 2.8.x 上建议在 fixture 里以整节写回方式重置
   相关配置节。

## 分发决策链（排查"命令为什么没触发"；需 EP>=2.9.0-dev）

`dispatch()` 返回 `DispatchTrace`——本次分发经过的每个判定点的因果链：

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # 逐行因果说明（当前语言）
trace.command        # 命中的命令名（未命中为 None）
trace.steps("cooldown")  # 按阶段过滤判定记录

trace.assert_executed("daily")  # 断言执行（失败时附完整因果链）
trace.assert_rejected()         # 断言被权限类判定拒绝
trace.assert_dropped()          # 断言被静默丢弃（冷却等）
trace.assert_no_match()         # 断言未命中命令
```

判定覆盖：命令文本判定、命令命中（未命中附拼写建议）、作用域、用户 ACL、
主人检查、权限函数、冷却静默丢弃、参数解析、执行结果、中间件否决。

生产环境同样可用框架内置的 `ErisPulse.Core.Event.trace`（`start_dispatch_trace()` /
`format_dispatch_trace()`）采集与渲染决策链。
