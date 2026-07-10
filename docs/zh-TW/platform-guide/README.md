# ErisPulse PlatformFeatures 文檔

> 基線協議：[OneBot12](https://12.onebot.dev/) 
> 
> 本文檔為**平台特定功能指南**，包含：
> - 各適配器支援的Send方法鏈式呼叫示例
> - 平台特有的事件/訊息格式說明
> 
> 通用使用方法請參考：
> - [基礎概念](../getting-started/basic-concepts.md)
> - [事件轉換標準](../standards/event-conversion.md)  
> - [API回應規範](../standards/api-response.md)

---

## 平台特定功能

此部分由各適配器開發者維護，用於說明該適配器與 OneBot12 標準的差異和擴展功能。請參考以下各平台的詳細文件：

- [維護說明](maintain-notes.md)

- [雲湖平台特性](yunhu.md)
- [雲湖用戶平台特性](yunhu_user.md)
- [Telegram平台特性](telegram.md)
- [OneBot11平台特性](onebot11.md)
- [OneBot12平台特性](onebot12.md)
- [郵件平台特性](email.md)
- [Kook(開黑啦)平台特性](kook.md)
- [Matrix平台特性](matrix.md)
- [QQ官方機器人平台特性](qqbot.md)
- [花楓咖啡館](ideaura.md)
- [Discord](discord.md)
- [Webhook協議橋](webhook.md)
- [微信公眾號](wechatmp.md)

> 此外還有 `sandbox` 適配器，但此適配器無需維護平台特性文件

---

## 通用介面

### Send 鏈式呼叫
所有適配器都支援以下標準呼叫方式：

> **注意：** 文件中的 `{AdapterName}` 需替換為實際適配器名稱（如 `yunhu`、`telegram`、`onebot11`、`email` 等）。

1. 指定類型和ID: `To(type,id).Func()`
   ```python
   # 獲取適配器實例
   my_adapter = adapter.get("{AdapterName}")
   
   # 發送訊息
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例如：
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. 僅指定ID: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例如：
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 指定發送帳號: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例如：
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼叫: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("廣播訊息")
   
   # 例如：
   email = adapter.get("email")
   await email.Send.Text("廣播訊息")
   ```

#### 異步發送與結果處理

Send DSL 的方法返回 `asyncio.Task` 物件，這意味著您可以選擇是否立即等待結果：

```python
# 獲取適配器實例
my_adapter = adapter.get("{AdapterName}")

# 不等待結果，訊息在背景發送
task = my_adapter.Send.To("user", "123").Text("Hello")

# 如果需要獲取發送結果，稍後可以等待
result = await task
```

#### 發送規則裝飾器

在實際開發中，經常需要：發送成功後才執行後續邏輯、失敗自動重試、超時取消、發送進度監控等。Send DSL 內建了一套發送規則裝飾器，透過鏈式方法附加規則：

| 方法 | 說明 |
|--------|------|
| `.Hook(callback)` | 發送成功後執行的回調（可多次呼叫） |
| `.Retry(times=1)` | 失敗自動重試 N 次（含首次共 N+1 次） |
| `.Timeout(seconds)` | 單次發送超時，超時取消（可與 Retry 叠加） |
| `.Defer(seconds)` | 延遲發送（進程內定時，不持久化） |
| `.OnProgress(callback)` | 各階段進度回調，傳入 SendContext |
| `.OnError(callback)` | 最終失敗時的錯誤回調（僅觸發一次） |

```python
yunhu = adapter.get("yunhu")

# 發送成功後才扣積分
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消費成功"))

# 失敗重試 + 超時取消 + 進度監控
def on_progress(ctx):
    print(f"階段: {ctx.stage}, 嘗試: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # 最多重試 3 次
        .Timeout(10)           # 每次超時 10 秒
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要通知"))
```

規則方法返回 `self`，必須放在發送方法（Text/Image 等）之前呼叫。`SendContext` 包含 `stage`（pending/sending/retrying/success/failed/timeout）、`attempt`、`elapsed`、`error`、`result` 等字段，便於監控。

#### 批量建構模式（Build）

一條鏈路中建構多個發送方法，最後統一執行。適用於「一口氣發多條訊息」的場景：

```python
yunhu = adapter.get("yunhu")

# 建構多條訊息，統一發送
results = await (yunhu.Send.To("user", "123")
                .Build()                     # 進入建構模式
                .Text("通知一")
                .Image("pic.jpg")
                .Text("通知二")
                .send_all())                 # 統一執行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` 默認**並行**執行（併發發送，效率高）。需要保證訊息到達順序時呼叫 `.Sequential()` 串行執行：

```python
# 串行執行（保證順序）+ 失敗重試
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # 按順序依次發送
       .Retry(2)                     # 失敗的條目各自重試
       .Text("第一條").Text("第二條")
       .send_all())
```

批量執行採用**失敗繼續**策略：某條失敗不會中斷其他條，失敗的條目自動重試。批量也支援整批的 `Hook`（全部成功後觸發）、`OnError`（有失敗時觸發）、`OnProgress`（進度回調）。

> 更詳細的規則與批量建構說明請參考 [SendDSL 詳解](../developer-guide/adapters/send-dsl.md)。

### 事件監聽
有三種事件監聽方式：

1. 平台原生事件監聽：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}原生事件: {data}")
   ```

2. OneBot12標準事件監聽：
   ```python
   from ErisPulse.Core import adapter, logger

   # 監聽OneBot12標準事件
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"收到標準事件: {data}")

   # 監聽特定平台的標準事件
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}標準事件: {data}")
   ```

3. Event模組監聽：
    `Event`的事件基於 `adapter.on()` 函數，因此`Event`提供的事件格式是一個OneBot12標準事件

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="發送問候訊息", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"收到訊息: {event}")
    async def notice_handler(event):
        logger.info(f"收到通知: {event}")
    async def request_handler(event):
        logger.info(f"收到請求: {event}")
    async def command_handler(event):
        logger.info(f"收到命令: {event}")
    ```

其中，最推薦的是使用 `Event` 模組進行事件處理，因為 `Event` 模組提供了豐富的事件類型，以及豐富的事件處理方法。

---

## 標準格式
為方便參考，這裡給出了簡單的事件格式，如果需要詳細資訊，請參考上方的連結。

> **注意：** 以下格式為基礎 OneBot12 標準格式，各適配器可能在此基礎上有擴展欄位。具體請參考各適配器的特定功能說明。

### 標準事件格式
所有適配器必須實現的事件轉換格式：
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### 標準回應格式
#### 訊息發送成功
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### 訊息發送失敗
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "缺少必要參數",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## 參考連結
ErisPulse 項目：
- [主庫](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu 適配器庫](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram 適配器庫](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot 適配器庫](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

相關官方文件：
- [OneBot V11 協議文件](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 官方文件](https://core.telegram.org/bots/api)
- [雲湖官方文件](https://www.yhchat.com/document/1-3)

## 參與貢獻

我們歡迎更多開發者參與編寫和維護適配器文件！請按照以下步驟提交貢獻：
1. Fork [ErisPuls](https://github.com/ErisPulse/ErisPulse) 倉庫。
2. 在 `docs/platform-features/` 目錄下建立一個 Markdown 檔案，並命名格式為 `<平台名稱>.md`。
3. 在本 `README.md` 檔案中新增對您貢獻的適配器的連結以及相關官方文件。
4. 提交 Pull Request。

感謝您的支持！