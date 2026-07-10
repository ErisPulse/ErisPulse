# SendDSL 詳解

SendDSL 是 ErisPulse 适配器提供的鏈式調用風格的訊息發送介面。

## 基本調用方式

### 1. 指定類型和 ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. 僅指定 ID

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. 指定發送帳號

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. 組合使用

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## 方法鏈

```
Using/Account() → To() → [修飾方法] → [發送方法]
```

## 發送方法

所有發送方法必須返回 `asyncio.Task` 物件。

### 基本方法

| 方法名 | 說明 | 返回值 |
|--------|------|---------|
| `Text(text: str)` | 發送文本訊息 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 發送圖片 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 發送語音 | `asyncio.Task` |
| `Video(file: bytes \| str)` | 發送影片 | `asyncio.Task` |
| `File(file: bytes \| str)` | 發送檔案 | `asyncio.Task` |

### 協議方法

| 方法名 | 說明 | 返回值 | 是否必須 |
|--------|------|---------|---------|
| `Raw_ob12(message)` | 發送 OneBot12 格式訊息 | `asyncio.Task` | **必須實現** |

> **重要**：`Raw_ob12` 是適配器的核心方法，**必須實現**。它是反向轉換（OneBot12 → 平台）的統一入口。未實現時基類會記錄 error 日誌並返回標準錯誤響應（`status: "failed"`, `retcode: 10002`）。標準方法（`Text`、`Image` 等）內部應委託給 `Raw_ob12`。

## 修飾方法

修飾方法返回 `self` 以支援鏈式調用。

### At 方法

```python
# @單個用戶
await adapter.Send.To("group", "123").At("456").Text("你好")

# @多個用戶
await adapter.Send.To("group", "123").At("456").At("789").Text("你們好")
```

### AtAll 方法

```python
# @全體成員
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Reply 方法

```python
# 回覆訊息
await adapter.Send.To("group", "123").Reply("msg_id").Text("回覆內容")
```

### 組合修飾

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回覆@的訊息")
```

## 帳戶管理

### Using 方法

`Using()` 用於指定發送訊息的帳號。傳入的標識符會透過 `_resolve_account()` 按以下優先級匹配：

1. **帳號名** — 配置中的鍵名（如 `"default"`、`"bot1"`）
2. **運行時注入的 bot_id** — 從事件轉換時自動注入的標識符
3. **任意 str 字段** — 配置中其他字串字段
4. **兜底** — 第一個啟用的帳號

```python
# 使用帳號名
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# 使用 bot_id（即事件中的 self.user_id）
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Account 方法

`Account` 方法與 `Using` 等價：

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## 非同步處理

### 不等待結果

```python
# 訊息在後台發送
task = adapter.Send.To("user", "123").Text("Hello")

# 繼續執行其他操作
# ...
```

### 等待結果

```python
# 直接 await 獲取結果
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"發送結果: {result}")

# 先保存 Task，稍後等待
task = adapter.Send.To("user", "123").Text("Hello")
# ... 其他操作 ...
result = await task
```

## 發送規則系統

SendDSL 內建了一套發送規則裝飾器，透過鏈式方法附加規則，在最終發送時統一應用。規則覆蓋常見的生產場景：超時控制、失敗重試、成功回調、延遲發送、優先級丟棄、進度監控。

規則方法**返回 self**（與 At/AtAll/Reply 一樣），必須放在發送方法（Text/Image 等）之前調用。規則會隨 `To`/`Using`/`Account` 創建的新實例傳播。

### 規則方法一覽

| 方法 | 說明 |
|--------|------|
| `.Hook(callback)` | 發送成功後執行的回調（可多次調用，按順序執行） |
| `.Retry(times=1)` | 失敗自動重試 N 次（含首次共 N+1 次） |
| `.Timeout(seconds)` | 單次發送超時，超時取消當前嘗試（可與 Retry 叠加） |
| `.Defer(seconds=1.0)` | 延遲發送（進程內定時，不持久化） |
| `.Priority(level, drop_if_busy=False)` | 設置優先級；積壓時可丟棄 |
| `.OnProgress(callback)` | 各階段進度回調（傳入 `SendContext`） |
| `.OnError(callback)` | 最終失敗時的錯誤回調（僅觸發一次） |

### 發送成功後執行邏輯（Hook）

```python
# 同步回調
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"發送成功，訊息ID: {r['message_id']}"))
       .Text("你好"))

# 非同步回調
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("扣積分")
```

Hook 僅在發送最終成功（含重試成功）時執行；失敗、超時、取消不觸發。

### 失敗自動重試（Retry）

```python
# 首次失敗後重試 2 次，共 3 次嘗試
result = await adapter.Send.To("user", "123").Retry(2).Text("帶重試")
```

重試觸發條件：發送拋出異常、發送超時、發送返回 `status == "failed"` 的響應。

### 超時自動取消（Timeout）

```python
# 單次發送超過 10 秒則取消
await adapter.Send.To("user", "123").Timeout(10).Text("帶超時")

# 超時 + 重試：每次嘗試 10 秒，最多 3 次
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("超時重試")
```

### 進度監控（OnProgress / OnError）

```python
def on_progress(ctx):
    print(f"階段: {ctx.stage}, 嘗試: {ctx.attempt + 1}/{ctx.max_attempts}, 耗時: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  錯誤: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"發送給 {ctx.target_id} 失敗: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("監控"))
```

`SendContext` 包含的字段：`task_id`、`platform`、`method`、`target_type`、`target_id`、`bot_id`、`stage`、`attempt`、`max_attempts`、`started_at`、`finished_at`、`elapsed`、`error`、`result`、`extra`。

`stage` 可能的值：`pending`、`sending`、`retrying`、`success`、`failed`、`timeout`、`cancelled`、`dropped`。

### 延遲發送（Defer）

```python
# 5 秒後發送
await adapter.Send.To("user", "123").Defer(5).Text("遲到訊息")
```

> 注意：延遲為進程內定時，進程重啟會遺失，不提供持久化。

### 優先級與積壓丟棄（Priority）

```python
# 低優先級訊息，佇列積壓時自動丟棄
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("可放棄的通知"))
# 若被丟棄，result["status"] == "failed"
```

`drop_if_busy` 啟用後，當在途發送任務數超過閾值（預設 64）時直接放棄本次發送。可透過 `.PriorityThreshold(n)` 調整全域閾值。

### 規則組合與後台執行

```python
# 不阻塞主流程，規則照樣生效
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("發送成功！"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("你好"))

# 繼續執行其他操作
await handle_next_action()
```

### 規則傳播

規則隨 `To`/`Using`/`Account` 創建的新實例傳播，避免鏈式調用中規則遺失：

```python
# 規則在 To 之前設置，也會傳播到 To 創建的實例
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send 仍攜帶 Retry(3) 和 Timeout(10)
await send.Text("hi")
```

多個實例的規則相互獨立（hooks 列表深拷貝）。

## 批量建構模式（Build）

除單發模式外，SendDSL 還支援批量建構模式：一條鏈路中寫多個發送方法，最後統一執行。適用於「一口氣發多條訊息」的場景。

### 進入建構模式

在發送方法之前調用 `.Build()`，返回 `SendBuilder`。此後發送方法（Text/Image 等）不再立即執行，而是累積為發送意圖：

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # 進入建構模式
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # 統一執行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` 返回 `asyncio.Task`，await 後得到結果列表（按意圖順序）。

### 並行與串行

預設**並行**執行（並發發送，總耗時約等於最慢的一條）。需要保證訊息到達順序時調用 `.Sequential()`：

```python
# 串行：按順序依次發送
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("先發這個").Text("再發這個")
       .send_all())

# 並行（預設，可顯式調用）
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("並發1").Text("並發2")
       .send_all())
```

### 失敗繼續與重試

批量執行採用**失敗繼續**策略：某條失敗不會中斷其他條的發送。配合 `.Retry()` 時，失敗的條目會自動重試（重試作用於單條，不是重試整批）：

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # 每條各自重試 2 次
       .Text("可能失敗的").Image("也可能失敗的")
       .send_all())
```

### 整批規則與回調

規則統一作用於整批：

| 方法 | 說明 |
|--------|------|
| `.Timeout(seconds)` | 每條發送的單次超時 |
| `.Retry(times)` | 每條發送各自重試（失敗繼續） |
| `.Defer(seconds)` | 延遲整批發送 |
| `.Hook(callback)` | 整批全部成功後觸發，接收 `results` 列表 |
| `.OnError(callback)` | 批次存在失敗時觸發，接收 `BatchContext` |
| `.OnProgress(callback)` | 每條完成時觸發，接收 `BatchContext` |

```python
def on_progress(ctx):
    print(f"進度: {ctx.completed}/{ctx.total}, 成功 {ctx.succeeded}, 失敗 {ctx.failed}")

async def on_error(ctx):
    print(f"批次有 {ctx.failed} 條失敗")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("整批完成"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` 包含：`task_id`、`total`、`completed`、`succeeded`、`failed`、`stage`、`results`、`errors`、`elapsed`、`extra`。

`stage` 可能的值：`pending`、`sending`、`success`（全部成功）、`partial`（部分成功）、`failed`（全部失敗）。

### 裝飾器與規則的繼承

`.Build()` 之前的 At/AtAll/Reply 裝飾器和規則會繼承到整批，作用於每條訊息：

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # 繼承：每條訊息都 @789
       .Build()
       .Retry(2)                         # 繼承 + 追加：每條各自重試
       .Text("@你的通知")
       .Image("公告圖")
       .send_all())
```

進入 Build 後仍可追加裝飾器（作用於整批）：

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # 追加 @，作用於整批
       .Text("@多人")
       .send_all())
```

### 後台執行

與單發一樣，`.send_all()` 返回 Task，可不 await 讓其在後台執行：

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("批量發送完成"))
        .Text("a").Text("b")
        .send_all())

# 不阻塞主流程
await do_something_else()
```

## 命名規範

### PascalCase 命名

所有發送方法使用大駝峰命名法：

```python
# ✅ 正確
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ 錯誤
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### 平台特有方法

不推薦添加平台前綴方法：

```python
# ✅ 推薦
def Sticker(self, sticker_id: str):
    pass

# ❌ 不推薦
def TelegramSticker(self, sticker_id: str):
    pass
```

使用 `Raw` 方法替代：

```python
# ✅ 推薦
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ 不推薦
def TelegramSticker(self, ...):
    pass
```

## 返回值

### Task 物件

所有發送方法返回 `asyncio.Task`：

```python
import asyncio

def Text(self, text: str):
    return asyncio.create_task(
        self._adapter.call_api(
            endpoint="/send",
            content=text,
            recvId=self._target_id,
            recvType=self._target_type
        )
    )
```

### 標準化響應

`call_api` 應返回標準化響應。推薦使用 `make_response()` / `make_error()` 方法：

```python
async def call_api(self, endpoint: str, **params):
    try:
        result = await self._do_api_call(endpoint, **params)
        return self.make_response(
            data=result.get("data"),
            message_id=result.get("message_id", ""),
            raw=result,
        )
    except Exception as e:
        return self.make_error(message=str(e))
```

也支援手動構造（舊版方式仍然相容）：

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok" or "failed",
        "retcode": 0 or error_code,
        "data": {...},
        "message_id": "msg_id" or "",
        "message": "",
        "{platform}_raw": raw_response
    }
```

## 完整範例

### 基本使用

```python
from ErisPulse.Core import adapter

my_adapter = adapter.get("myplatform")

# 發送文本
await my_adapter.Send.To("user", "123").Text("Hello World!")

# 發送圖片
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# 發送檔案
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### 鏈式調用

```python
# @用戶 + 回覆
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回覆@的訊息")

# @全體 + 多個修飾
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告訊息")
```

### 原始訊息與訊息建構

`Raw_ob12` 是反向轉換的核心入口（接收 OB12 訊息段 → 平台 API 調用），`MessageBuilder` 是配合其使用的鏈式訊息段建構工具。

> 完整的 `Raw_ob12` 實現規範、`MessageBuilder` 用法及程式碼範例請參閱：
> - [發送方法規範 §6 反向轉換規範](../../standards/send-method-spec.md#6-反向轉換規範onebot12--平台)
> - [發送方法規範 §11 訊息建構器](../../standards/send-method-spec.md#11-訊息建構器-messagebuilder)

## 相關文件

- [適配器開發入門](getting-started.md) - 創建適配器
- [適配器核心概念](core-concepts.md) - 了解適配器架構
- [適配器最佳實踐](best-practices.md) - 開發高品質適配器
- [發送方法規範](../../standards/send-method-spec.md) - 發送方法完整規範