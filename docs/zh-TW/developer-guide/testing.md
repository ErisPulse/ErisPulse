# 模組測試（ErisPulse-Testing）

[ErisPulse-Testing](https://github.com/wsu2059q/ErisPulse-Testing) 是官方測試工具包（RFC EPRFC-2026-001 方向三）：
提供 `TestBot`、測試事件工廠、出站訊息捕獲與斷言介面，讓模組測試像寫普通 pytest 一樣簡單。

```bash
pip install ErisPulse-Testing
```

> 單向依賴框架的開發期工具，執行時零介入。真連適配器平台的冒煙測試請使用框架倉庫的 `tests/devs/test_adapter.py`。

## 快速開始

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="今天已簽到")
        async def daily(event):
            await event.reply("簽到成功！")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "簽到成功！"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("今天已簽到")   # 第二次命中冷卻
```

`TestBot` 推薦以 `async with` 使用：啟動時註冊 MockAdapter（捕獲全部出站）、
關閉事件去重、應用配置覆寫；退出時自動清理框架全域狀態，用例之間互不污染。

配套 pytest fixtures（安裝後自動可用）：

- `testbot`：function 級標準 TestBot（platform=`test`、前綴 `/`）
- `make_testbot(**kwargs)`：自定義參數工廠（`prefix` / `config` / `platform` / `bot_id` ...）

建議在測試專案配置 `asyncio_mode = "auto"`（`[tool.pytest.ini_options]`），
或給用例加 `@pytest.mark.asyncio`。

## 事件工廠

| 函數 | 說明 |
|------|------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | 消息事件；`group_id` 為空即為私聊 |
| `create_command_event("roll 3", prefix="/")` | 命令消息（自動加前綴，已帶前綴不重複） |
| `create_notice_event(type, ...)` | 通知事件（如 `friend_add`） |
| `create_request_event(type, ...)` | 請求事件（如好友申請） |
| `create_meta_event("connect", ...)` | meta 事件（connect 可讓 Bot 上線） |

所有事件使用 uuid 唯一 `id`，天然避開框架的事件去重。

## TestBot API

### 分發

```python
trace = await bot.dispatch(event)          # 分發並等待處理器落地，返回決策鏈
await bot.dispatch(event, drain=False)     # 交互首消息：不等待（wait_reply 處理器長駐）
await bot.send_message("你好")             # 消息分發快捷方式
await bot.reply_as("18", user_id="u1")     # 模擬 wait_reply 用戶回覆（自動等 waiter 就緒）
```

`dispatch()` 在 emit 後 gather 全部在途處理器 Task，返回即處理完成——**測試裡不需要 sleep**。

### 出站斷言

```python
bot.replies                # 全部出站（SentMessage 列表）
bot.last_reply.text        # 最近一條回覆的文本
bot.replies_to("123")      # 按目標過濾
bot.clear_replies()        # 階段間隔離斷言
bot.assert_replied()                       # 存在出站
bot.assert_replied(contains="簽到", to="123")
bot.assert_not_replied()                   # 無任何出站
bot.assert_reply_contains("簽到成功")       # 存在包含指定文本的出站
await bot.wait_for_reply(timeout=2)        # 等待異步回覆出現
```

`SentMessage` 字段：`text`（首個 text 段）、`segments`（完整消息段）、
`target_type` / `target_id` / `bot_id`（發送上下文）、`has_modifier("at")` 等。

### 模組加載

```python
await bot.load_module("MyModule")   # entry-point 已註冊的包名
await bot.load_module(MyModule)     # 或 BaseModule 子類（自動 register + load）
await bot.unload_module("MyModule")
```

`on_load` 內註冊的命令 / 事件處理器隨模組歸屬，卸載時自動清理，可直接斷言"卸載後命令失效"。

### 依賴替換

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

替換的是命令註冊表中 `Depends(get_session)` 聲明引用的函數，with 退出自動還原。

### 配置覆寫

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # 模組配置（self.cfg 可讀）
})
```

經配置記憶體層注入（不落盤），命令前綴等隨熱更新立即生效。

## 分發決策鏈（排查「命令為什麼沒觸發」）

`dispatch()` 返回 `DispatchTrace`——本次分發經過的每個判斷點的因果鏈：

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # 逐行因果說明（當前語言）
trace.command        # 命中的命令名（未命中為 None）
trace.steps("cooldown")  # 按階段過濾判定記錄

trace.assert_executed("daily")  # 斷言執行（失敗時附完整因果鏈）
trace.assert_rejected()         # 斷言被權限類判定拒絕
trace.assert_dropped()          # 斷言被靜默丟棄（冷卻等）
trace.assert_no_match()         # 斷言未命中命令
```

判定覆蓋：命令文本判定、命令命中（未命中附拼寫建議）、作用域、用戶 ACL、
主人檢查、權限函數、冷卻靜默丟棄、參數解析、執行結果、中間件否決。

生產環境同樣可用框架內建的 `ErisPulse.Core.Event.trace`（`start_dispatch_trace()` /
`format_dispatch_trace()`）採集與渲染決策鏈。