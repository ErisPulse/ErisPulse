# OneBot11 平台特性文件

OneBot11Adapter 是基於 OneBot V11 協議建構的適配器。

---

## 文件資訊

- 對應模組版本: 4.0.0
- 維護者: ErisPulse

## 基本資料

- 平台簡介：OneBot 是一個聊天機器人應用程式介面標準
- 適配器名稱：OneBotAdapter
- 支援的協定/API版本：OneBot V11
- 多帳號支援：預設多帳號架構，支援同時設定和執行多個 OneBot 帳號
- 配置鍵名：`OneBotAdapter`

## 支援的訊息傳送類型

所有傳送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# 使用預設帳號傳送
await onebot.Send.To("group", group_id).Text("Hello World!")

# 指定特定帳號傳送
await onebot.Send.Using("main").To("group", group_id).Text("來自主帳號的訊息")

# 鏈式修飾：@使用者 + 回覆
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("回覆訊息")

# @全體成員
await onebot.Send.To("group", group_id).AtAll().Text("公告訊息")
```

### 基礎傳送方法

- `.Text(text: str)`：傳送純文字訊息。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：傳送圖片（支援 URL、Base64 或 bytes）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：傳送語音訊息。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：傳送視訊訊息。
- `.Face(id: Union[str, int])`：傳送 QQ 表情。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：傳送檔案（自動判斷類型）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：傳送 OneBot12 格式訊息（自動轉換為 OB11）。
- `.Recall(message_id: Union[str, int])`：撤回訊息。

### 群操作方法

以下方法需透過 `To("group", group_id)` 指定目標群，使用群上下文執行操作：

- `.Kick(user_id, reject_add_request=False)`：踢出群成員。
- `.Ban(user_id, duration=1800)`：禁言群成員（秒），0 表示解禁。
- `.WholeBan(enable=True)`：開啟/關閉全體禁言。
- `.SetAdmin(user_id, enable=True)`：設定/取消群管理員。
- `.SetCard(user_id, card="")`：設定群名片。
- `.SetGroupName(name)`：修改群名稱。
- `.Leave(is_dismiss=False)`：退群（群主可解散）。
- `.SetTitle(user_id, title="")`：設定群頭銜。
- `.SetPortrait(file)`：設定群頭像。

### 查詢方法

- `.GetMsg(message_id)`：獲取訊息內容。
- `.GetForwardMsg(id)`：獲取合併轉發訊息。
- `.GetLoginInfo()`：獲取當前登入號資訊。
- `.GetFriendList()`：獲取好友列表。
- `.GetGroupInfo()`：獲取群資訊（需 `To("group", group_id)`）。
- `.GetGroupList()`：獲取群列表。
- `.GetGroupMemberInfo(user_id)`：獲取群成員資訊（需 `To("group", group_id)`）。
- `.GetGroupMemberList()`：獲取群成員列表（需 `To("group", group_id)`）。

### 好友操作方法

- `.Like(user_id, times=1)`：發送好友讚（最大 10 次）。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法傳回 `self`，支援鏈式呼叫，必須在最終傳送方法前呼叫：

- `.At(user_id: Union[str, int], name: str = None)`：@指定使用者（可多次呼叫）。
- `.AtAll()`：@全體成員。
- `.Reply(message_id: Union[str, int])`：回覆指定訊息。

### 鏈式呼叫範例

```python
# 基礎傳送
await onebot.Send.To("group", 123456).Text("Hello")

# @單個使用者
await onebot.Send.To("group", 123456).At(789012).Text("你好")

# @多個使用者
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("大家好")

# 傳送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# 點讚
await onebot.Send.Like(123456, times=10)

# 禁言群成員
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# 解禁
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# 踢人
await onebot.Send.To("group", 123456).Kick(789012)

# 設定群管理員
await onebot.Send.To("group", 123456).SetAdmin(789012)

# 修改群名
await onebot.Send.To("group", 123456).SetGroupName("新群名")

# 獲取群資訊
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# 指定帳號操作
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### 不支援的類型處理

如果呼叫未定義的傳送方法，適配器會傳回文字提示：
```python
# 呼叫不存在的方法
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# 實際發送: "[不支援的傳送類型] 方法名: SomeUnsupportedMethod, 參數: [...]"
```

## 請求操作（Request DSL）

適配器提供請求操作 DSL，用於處理好友請求和群請求（加群/邀請）的同意/拒絕操作。

### Event 快捷方法

請求事件支援 `event.approve()` 和 `event.reject()` 快捷方法，內部自動呼叫 Request DSL：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

@request.on_group_request()
async def handle_group_request(event):
    group_id = event.get("group_id")
    await event.approve()
```

### 手動呼叫 Request DSL

```python
# 同意請求
await onebot.Request("flag_string").accept()

# 拒絕請求
await onebot.Request("flag_string").reject()

# 指定帳號操作
await onebot.Request("flag_string").Using("main").accept()
```

### 完整範例

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # 方式一：使用 Event 快捷方法
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # 方式二：使用 Request DSL
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### 請求操作傳回值

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}
```

## 事件類型映射

### 標準 OB12 映射

| OB11 原始類型 | 轉換後 detail_type | 說明 |
|--------------|-------------------|------|
| message_type: private | `private` | 私聊訊息 |
| message_type: group | `group` | 群聊訊息 |
| request_type: friend | `friend` | 好友請求 |
| request_type: group | `group` | 群請求 |
| meta_event_type: heartbeat | `heartbeat` | 心跳 |
| notice_type: group_upload | `group_file_upload` | 群檔案上傳 |
| notice_type: group_admin | `group_admin_change` | 群管理員變動 |
| notice_type: group_increase | `group_member_increase` | 群成員增加 |
| notice_type: group_decrease | `group_member_decrease` | 群成員減少 |
| notice_type: group_ban | `group_ban` | 群禁言 |
| notice_type: friend_add | `friend_increase` | 好友新增 |
| notice_type: friend_delete | `friend_decrease` | 好友刪除 |
| notice_type: group_recall / friend_recall | `message_recall` | 訊息撤回 |

### 平台特有事件（onebot11_ 前綴）

| OB11 原始類型 | 轉換後 detail_type | 說明 |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot 實現生命週期 |
| notify + sub_type: honor | `onebot11_honor` | 群榮譽變更 |
| notify + sub_type: poke | `onebot11_poke` | 戳一戳 |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | 群紅包運氣王 |
| CQ 碼未知類型 | 消息段 `onebot11_{type}` | 未識別的 CQ 碼 |

### 事件範例

```python
// 好友請求
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "請加好友",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// 心跳
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// 生命週期（平台特有）
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// 戳一戳（平台特有）
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 群紅包運氣王（平台特有）
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 榮譽變更（平台特有）
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// CQ 碼擴展消息段
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### 擴展欄位說明

- 所有特有欄位均以 `onebot11_` 前綴標識
- 保留原始事件資料在 `onebot11_raw` 欄位
- 保留原始事件類型在 `onebot11_raw_type` 欄位
- 訊息內容中的 CQ 碼會轉換為相應的訊息段（標準類型無前綴，未知類型加 `onebot11_` 前綴）
- 回覆訊息會新增 `reply` 類型的訊息段
- @訊息會新增 `mention` 類型的訊息段

## 事件擴展方法

OneBot11 適配器為事件物件註冊了以下平台專有方法，可在事件處理器中直接呼叫：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### 方法列表

| 方法 | 回傳類型 | 說明 |
|------|----------|------|
| `get_raw_self_id()` | `str` | 獲取原始 self_id（Bot 的 QQ 號） |
| `get_sender_info()` | `dict` | 獲取完整的發送者資訊（包含 nickname、role、level 等） |
| `get_sender_role()` | `str` | 獲取發送者在群內的角色（owner/admin/member） |
| `get_sender_level()` | `int` | 獲取發送者等級 |
| `get_sender_title()` | `str` | 獲取發送者群頭銜 |
| `is_system_message()` | `bool` | 判斷是否為系統訊息（sub_type == "system"） |

### 使用範例

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("管理員好！")

    title = event.get_sender_title()
    if title:
        await event.reply(f"你的頭銜是: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "未知")
    level = event.get_sender_level()
    await event.reply(f"暱稱: {nickname}, 等級: {level}")
```

## 設定選項

OneBot11 適配器採用多帳號架構，每個帳號獨立設定。設定鍵名為 `OneBotAdapter`。

### 帳號設定欄位

| 欄位 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `bot_id` | `str` | 是 | `""` | 機器人 QQ 號，用於標識帳號 |
| `mode` | `str` | 否 | `"server"` | 運行模式：`"server"`（被動監聽）或 `"client"`（主動連接） |
| `url` | `str` | 否 | `"ws://127.0.0.1:3001"` | Client 模式的 WebSocket 位址 |
| `token` | `str` | 否 | `""` | 認證 Token（Client 模式連線 Token / Server 模式驗證 Token） |
| `server_path` | `str` | 否 | `"/"` | Server 模式的 WebSocket 路徑 |
| `enabled` | `bool` | 否 | `true` | 是否啟用該帳號 |
| `name` | `str` | 否 | `""` | 帳號備註名稱 |

### 內建預設值

- 重連間隔：30 秒
- API 呼叫逾時：30 秒

### 設定範例

```toml
[OneBotAdapter.accounts.main]
bot_id = "123456789"
mode = "server"
server_path = "/onebot-main"
token = "main_token"
enabled = true

[OneBotAdapter.accounts.backup]
bot_id = "987654321"
mode = "client"
url = "ws://127.0.0.1:3002"
token = "backup_token"
enabled = true

[OneBotAdapter.accounts.test]
bot_id = "111222333"
mode = "client"
url = "ws://127.0.0.1:3003"
enabled = false
```

### 預設設定

如果未設定任何帳號，適配器會自動建立：
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## 傳送方法傳回值

所有傳送方法均傳回一個 Task 物件，可以直接 await 取得傳送結果。傳回結果遵循 ErisPulse 適配器標準化傳回規範：

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "onebot11_raw": {...}
}
```

### 多帳號傳送語法

```python
# 帳號選擇方法
await onebot.Send.Using("main").To("group", 123456).Text("主帳號訊息")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# 透過 bot_id 選擇帳號
await onebot.Send.Using("123456789").To("group", 123456).Text("透過QQ號選擇")

# API呼叫方式
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### 帳號解析優先級

`call_api` 和 `Using()` 中 `account_id` 參數的解析優先級：
1. 精確匹配帳號名稱
2. 匹配 `bot_id` 欄位
3. 匹配帳號的任意 `str` 類型欄位
4. 回退到第一個已啟用的帳號

## 非同步處理機制

OneBot11 適配器採用非同步非阻塞設計，確保：
1. 訊息傳送不會阻擋事件處理循環
2. 多個併發傳送操作可以同時進行
3. API 回應能夠及時處理
4. WebSocket 連線保持活躍狀態
5. 多帳號併發處理，每個帳號獨立運行

## 錯誤處理

適配器提供完善的錯誤處理機制：
1. 網路連線異常自動重連（支援每個帳號獨立重連，間隔 30 秒）
2. API 呼叫逾時處理（固定 30 秒逾時）
3. 連線失敗時自動按間隔重試

## 事件處理增強

多帳號模式下，所有事件都會自動新增帳號資訊：
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... 其他事件欄位
}
```

適配器自動維護 `self_id → account_name` 映射，`event.reply()` 無需手動指定帳號即可正確路由到來源帳號。

## 管理介面

```python
# 取得所有帳號資訊
accounts = onebot.accounts

# 檢查帳號連線狀態
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# 動態啟用/禁用帳號（需要重啟適配器）
onebot.accounts["test"].enabled = False
```

## self_id 自動映射

適配器會自動建立 OneBot `self_id`（QQ號）到 `account_name` 的映射關係，用於事件回路由：

```python
// 適配器內部自動完成
// 當收到事件時，self.user_id 欄位填補為 bot_id
// 適配器自動記錄: self_id("123456789") → account_name("main")

// 因此 event.reply() 可以自動找到正確的帳號傳送訊息
@message.on_message()
async def handler(event):
    await event.reply("自動路由到正確的帳號")