# OneBot12 平台特性文件

OneBot12Adapter 是基於 OneBot V12 協議所建構的適配器，作為 ErisPulse 框架的基準協議適配器。

---

## 文件資訊

- 對應模組版本: 4.0.0
- 維護者: ErisPulse
- 協定版本: OneBot V12

## 基本資訊

- 平台簡介：OneBot V12 是一個通用的聊天機器人應用介面標準，是ErisPulse框架的基線協議
- 適配器名稱：OneBot12Adapter
- 支援的協議/API版本：OneBot V12
- 多帳戶支援：完全多帳戶架構，支援同時設定和運行多個OneBot12帳戶

## 支援的消息發送類型

所有發送方法均透過鏈式語法實現，例如：

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# 使用預設帳戶發送
await onebot12.Send.To("group", group_id).Text("Hello World!")

# 指定特定帳戶發送
await onebot12.Send.To("group", group_id).Account("main").Text("來自主帳戶的消息")
```

### 大小寫不敏感調用

所有發送方法和鏈式修飾方法均支援大小寫不敏感調用，適配器會自動映射到正確的標準方法名：

```python
# 以下所有呼叫方式等價
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# 鏈式修飾方法同樣支援
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### 不支援的方法調用

當呼叫不存在的方法時，適配器會回傳友好的文字提示，而不是拋出例外：

```python
# 呼叫不支援的方法
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# 回傳的結果是發送的文本訊息
# 訊息內容: [不支援的發送類型] 方法名: UnsupportedMethod, 參數: [args[0]: 'test']
```

### 基礎訊息類型

- `.Text(text: str)`：發送純文字訊息
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：發送圖片訊息（支援URL、Base64或bytes）
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`：發送音訊訊息
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")`：發送語音訊息（Audio的別名，相容OneBot11）
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：發送影片訊息

### 鏈式修飾方法（返回self支援鏈式調用）

- `.At(user_id: Union[str, int])`：@使用者（可多次呼叫）
- `.AtAll()`：@全體成員
- `.Reply(message_id: Union[str, int])`：回覆訊息

### 原始訊息發送

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)`：發送OneBot12原始格式訊息（符合命名規範）

### 其他訊息類型

- `.Sticker(file_id: str)`：發送表情包/貼紙
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`：發送位置

### 管理功能

- `.Recall(message_id: Union[str, int])`：撤回訊息
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`：編輯訊息
- `.Raw(message_segments: List[Dict])`：發送原生OneBot12訊息段
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`：批量發送訊息

## OneBot12 標準事件

OneBot12 適配器完全遵循 OneBot12 標準，事件格式無需轉換，直接提交到框架。

### 新增特性：原始事件類型字段

符合 `standards/event-conversion.md` 規範，所有事件都會保留原始事件類型字段 `onebot12_raw_type`：

```python
{
    "id": "event-id",
    "type": "message",              # 事件類型
    "onebot12_raw_type": "message", # 原始事件類型（與type相同）
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}
```

### 消息事件 (Message Events)

```python
# 私聊消息
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}

# 群聊消息
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "group_id": "group-id",
    "message": [{"type": "text", "data": {"text": "Hello group"}}],
    "alt_message": "Hello group",
    "time": 1234567890
}
```

### 通知事件 (Notice Events)

```python
# 群成員增加
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_increase",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "approve",
    "time": 1234567890
}

# 群成員減少
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_decrease",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "leave",
    "time": 1234567890
}
```

### 請求事件 (Request Events)

```python
# 好友請求
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "申請消息",
    "flag": "request-flag",
    "time": 1234567890
}

# 群邀請請求
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "申請消息",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### 元事件 (Meta Events)

```python
# 生命週期事件
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# 心跳事件
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "heartbeat",
    "self": {"user_id": "bot-id"},
    "interval": 5000,
    "status": {"online": true},
    "time": 1234567890
}
```

## 配置選項

### 帳戶配置

每個帳戶獨立配置以下選項：

- `mode`: 該帳戶的運行模式 ("server" 或 "client")
- `server_path`: Server模式下的WebSocket路徑
- `server_token`: Server模式下的認證Token（可選）
- `client_url`: Client模式下要連接的WebSocket地址
- `client_token`: Client模式下的認證Token（可選）
- `enabled`: 是否啟用該帳戶
- `platform`: 平台標識，預設為 "onebot12"
- `implementation`: 實現標識，如 "go-cqhttp"（可選）

### 配置範例

```toml
[OneBotv12_Adapter.accounts.main]
mode = "server"
server_path = "/onebot12-main"
server_token = "main_token"
enabled = true
platform = "onebot12"
implementation = "go-cqhttp"

[OneBotv12_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true
platform = "onebot12"
implementation = "shinonome"

[OneBotv12_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### 預設配置

如果未配置任何帳戶，適配器會自動建立：

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## 發送方法返回值

### 消息發送方法
所有消息發送方法（如 `.Text()`, `.Image()`, `.Raw_ob12()` 等）均返回一個 `asyncio.Task` 對象，可以直接 await 獲取發送結果：

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### 鏈式修飾方法
所有鏈式修飾方法（如 `.At()`, `.AtAll()`, `.Reply()`）均返回 `self`，支援鏈式調用：

```python
# 組合使用多個修飾方法
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("文本")
```

## API 响應標準

適配器遵循 ErisPulse 標準化返回規範（`standards/api-response.md`）：

```python
# 成功響應
{
    "status": "ok",              # 必須：執行狀態
    "retcode": 0,                # 必須：返回碼（0 表示成功）
    "data": {                     # 必須：響應數據
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       # 必須：消息 ID（無則為空字串）
    "message": "",                # 必須：錯誤訊息（成功時為空）
    "echo": "1234",               # 可選：原樣返回請求中的 echo
    "onebot12_raw": {...}        # 可選：原始響應數據
}

# 失敗響應
{
    "status": "failed",           # 必須：執行狀態
    "retcode": 10003,            # 必須：返回碼（非 0 表示失敗）
    "data": None,                # 必須：失敗時為 null
    "message_id": "",            # 必須：失敗時為空字串
    "message": "缺少必要參數",    # 必須：錯誤描述
    "echo": "1234",              # 可選：原樣返回請求中的 echo
    "onebot12_raw": {...}        # 可選：原始響應數據
}
```

### 錯誤碼規範

遵循 OneBot12 標準錯誤碼：

- **0**: 成功
- **1xxxx**: 動作請求錯誤
- **2xxxx**: 動作處理器錯誤
- **3xxxx**: 動作執行錯誤（33001 為網路超時）

### 多帳號發送語法

```python
# 帳號選擇方法
await onebot12.Send.Using("main").To("group", 123456).Text("主帳號訊息")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API 調用方式
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## 異步處理機制

OneBot12 适配器采用异步非阻塞设计：

1. 消息发送不会阻塞事件处理循环  
2. 多个并发发送操作可以同时进行  
3. API 响应能够及时处理  
4. WebSocket 连接保持活跃状态  
5. 多账户并发处理，每个账户独立运行

## 錯誤處理

適配器提供完善的錯誤處理機制：

1. 網路連線異常自動重連（支援每個帳戶獨立重連，間隔30秒）
2. API呼叫逾時處理（固定30秒逾時）
3. 消息發送失敗自動重試（最多3次重試）
4. 不支援的方法呼叫會返回友善的文字提示

## 事件處理增強

多帳戶模式下，所有事件都會自動添加帳戶資訊：

```python
{
    "type": "message",
    "onebot12_raw_type": "message",  // 原始事件類型
    "detail_type": "private",
    "self": {"user_id": "123456"},  // 發送事件的帳戶ID（標準欄位）
    "platform": "onebot12",
    // ... 其他事件欄位
}
```

## 管理介面

```python
# 獲取所有帳戶資訊
accounts = onebot12.accounts

# 檢查帳戶連接狀態
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# 動態啟用/停用帳戶（需要重新啟動適配器）
onebot12.accounts["test"].enabled = False
```

## OneBot12 標準特性

### 消息段標準

OneBot12 使用標準化的消息段格式：

```python
# 文本消息段
{"type": "text", "data": {"text": "Hello"}}

# 圖片消息段
{"type": "image", "data": {"file_id": "image-id"}}

# 提及消息段
{"type": "mention", "data": {"user_id": "user-id", "user_name": "Username"}}

# 回覆消息段
{"type": "reply", "data": {"message_id": "msg-id"}}
```

### API 標準

遵循 OneBot12 標準 API 規範：

- `send_message`: 發送訊息
- `delete_message`: 撤回訊息
- `edit_message`: 編輯訊息
- `get_message`: 獲取訊息
- `get_self_info`: 獲取自身資訊
- `get_user_info`: 獲取使用者資訊
- `get_group_info`: 獲取群組資訊

## 最佳實踐

1. **配置管理**: 建議使用多帳戶配置，將不同用途的機器人分開管理  
2. **錯誤處理**: 始終檢查 API 調用的返回狀態  
3. **訊息發送**: 使用合適的訊息類型，避免發送不支援的訊息  
4. **連接監控**: 定期檢查連接狀態，確保服務可用性  
5. **效能優化**: 批量發送時使用 Batch 方法，減少網路開銷  
6. **方法呼叫**: 推薦使用標準的大駝峰命名（如 `.Text()`），但也支援小寫形式以兼容不同程式設計風格（這種方式可能會不相容舊版本）