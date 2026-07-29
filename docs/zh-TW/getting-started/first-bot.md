# 創建第一個機器人

本指南在 [5 分鐘快速開始](../quick-start.md) 的基礎上，帶你編寫第一個命令處理器並理解運行機制。

> 如果你還沒有安裝好 ErisPulse、初始化項目，請先完成 [快速開始](../quick-start.md) 的「安裝」「初始化項目」「運行項目」三步。

## 第一步：編寫第一個命令

打開 `main.py`，編寫一個簡單的命令處理器：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="發送問候訊息")
async def hello_handler(event):
    """處理 hello 命令"""
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！我是 ErisPulse 機器人。")

@command("ping", help="測試機器人是否在線")
async def ping_handler(event):
    """處理 ping 命令"""
    await event.reply("Pong！機器人運行正常。")

async def main():
    """主入口函數"""
    print("正在啟動 ErisPulse...")
    
    # keep_running=True（預設）：框架阻塞維持運行，直到收到關閉訊號（如 Ctrl+C）
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### `keep_running` 參數

`sdk.run(keep_running)` 控制框架是否阻塞維持運行：

- **`keep_running=True`（預設）**：`run()` 會一直阻塞，直到收到關閉訊號（如 Ctrl+C），適合純 bot 應用。
- **`keep_running=False`**：`run()` 初始化完成後立即返回，**框架並不會卸載**——已啟動的適配器/模塊仍作為背景任務繼續處理訊息事件，你可以接著執行自己的邏輯，直到事件循環結束框架才隨之關閉。例如：

```python
async def main():
    await sdk.run(keep_running=False)   # 初始化後立即返回
    # 框架已在背景運行，這裡可以繼續做別的事
    while True:
        await asyncio.sleep(3600)
        print("每小時檢查一次")
```

> 除了 `run()` 的兩種模式，還有 `init()`/`uninit()` 手動控制生命週期、單獨啟停適配器/路由等更精細的方式，見 [啟動流程與手動控制](../advanced/startup.md)。

## 第二步：運行機器人

```bash
# 普通運行
epsdk run main.py

# 開發模式（支援熱重載）
epsdk run main.py --reload
```

## 第三步：測試機器人

在你的聊天平台中發送命令：

```
/hello
```

你應該會收到機器人的回覆。

## 程式碼說明

### 命令裝飾器

```python
@command("hello", help="發送問候訊息")
```

- `hello`：命令名稱，使用者透過 `/hello` 調用
- `help`：命令幫助說明，在 `/help` 命令中顯示

### 事件參數

```python
async def hello_handler(event):
```

`event` 參數是一個 Event 物件，包含：
- 消息內容：`event.get_text()`
- 發送者資訊：`event.get_user_id()`、`event.get_user_nickname()`
- 平台資訊：`event.get_platform()`
- 群組資訊：`event.get_group_id()`
- 原始資料：`event.get_raw()`

> 完整的 Event 物件方法請參考 [Event 包裝類詳解](../developer-guide/modules/event-wrapper.md)。

### 發送回覆

```python
await event.reply("回覆內容")
```

`event.reply()` 是一個便捷方法，用於向發送者發送訊息。

## 擴展：添加更多功能

ErisPulse 提供了豐富的事件處理和資料處理能力：

- **訊息監聽**：使用 `@message.on_message()` 監聽各類訊息 → [事件處理入門](event-handling.md)
- **通知監聽**：使用 `@notice.on_friend_add()` 等監聽系統通知 → [事件處理入門](event-handling.md)
- **資料儲存**：使用 `sdk.storage.get/set` 持久化資料 → [常見任務示例](common-tasks.md)

## 常見問題

### 命令沒有回應？

1. 檢查適配器是否正確配置，確認 `config/config.toml` 中適配器的 `status` 為 `true`
2. 查看終端日誌輸出，確認是否有錯誤資訊（特別是 `ERROR` 級別日誌）
3. 確認命令前綴是否正確（預設是 `/`），可在設定檔中查看 `[ErisPulse.event.command]` 部分
4. 確認命令名稱拼寫正確，注意大小寫敏感性設定

### 如何修改命令前綴？

在 `config.toml` 中添加：

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### 如何支援多平台？

ErisPulse 使用 OneBot12 標準統一了不同平台的事件格式，`@command` 和 `@message` 註冊的處理器會自動接收所有平台的事件。透過 `event.get_platform()` 可以區分來源平台：

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("你好！來自雲湖")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("你好！")
```

> 更多多平台適配技巧請參考 [常見任務示例](common-tasks.md#多平台適配)。

## 下一步

- [基礎概念](basic-concepts.md) - 深入了解 ErisPulse 的核心概念
- [事件處理入門](event-handling.md) - 學習處理各類事件
- [常見任務示例](common-tasks.md) - 掌握更多實用功能