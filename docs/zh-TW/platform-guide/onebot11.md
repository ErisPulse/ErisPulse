# OneBot11平台特性文件

OneBot11Adapter 是基於 OneBot V11 協定構建的適配器。

---

## 文件資訊

- 對應模組版本： 4.6.2
- 維護者： ErisPulse
- 最後更新： 2026-11-10

## 基本資訊

- 平台簡介：OneBot 是一個聊天機器人應用介面標準
- 適配器名稱：OneBotAdapter
- 支援的協定/API版本：OneBot V11
- 多帳戶支援：預設多帳戶架構，支援同時配置和執行多個 OneBot 帳戶
- 配置鍵名：`OneBotAdapter`

## v5 範式更新（4.3.0 起）

本適配器已完成 v5 範式對齊（增量升級，API 相容）：

- **BaseConverter 繼承**：轉換器公共欄位（id/time/platform/self/raw）由框架 build_base_event 構建，按 OB11 欄位名稱（echo/time/self_id）覆蓋
- **spawn_background 任務歸屬**：Client 模式連線任務改用 Runtime.spawn_background（owner 歸屬，shutdown 自動回收）
- **框架軟依賴**：安裝適配器不再宣告 ErisPulse 硬依賴，避免 pip 解析時調整框架版本；執行時偵測 ErisPulse>=2.7.1 並在版本過低時輸出日誌提示
- **啟動版本日誌**：初始化時輸出 OneBotAdapter vX.Y.Z 已載入

已有能力（4.2.0 起支援）：多帳戶、Api DSL 標準動作映射（get_self_info→get_login_info 等）、Request DSL（好友/群組請求審核：event.approve() / event.reject()）、EventMixin、i18n。

4.3.1 起請求事件處理按規範實現，詳見下文[標準化對齊](#標準化對齊)章節。

---

## 標準Api動作（Api DSL）

適配器將 OneBot12 標準動作名稱自動映射到 OB11 動作名稱，模組可跨平台統一呼叫：

| OB12 標準動作 | OB11 動作 | 說明 |
|--------------|-----------|------|
| get_self_info | get_login_info | 欄位標準化 user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | 欄位標準化 |
| delete_message | delete_msg | 撤回訊息 |
| leave_group | set_group_leave | 退出群組 |
| get_friend_list | get_friend_list | 動作名稱一致，預設透傳 |
| get_group_info | get_group_info | 動作名稱一致，預設透傳 |
| upload_file | upload_group_file / upload_private_file | 擴充 group_id/user_id 可選參數，filetype 自動偵測類型路由 |

### 基本用法

```python
from ErisPulse import sdk
onebot = sdk.adapter.get("onebot11")

# 取得機器人資訊
result = await onebot.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# 撤回訊息
await onebot.Api.delete_message(message_id=123456)

# 上傳群組檔案（filetype 自動偵測類型路由到 upload_group_file）
result = await onebot.Api.upload_file(group_id=123456, file="/path/to/file.zip")

# 指定帳戶（多帳戶）
result = await onebot.Api.Using("main").get_self_info()

# 未映射的 OB11 動作透過 call() 逃生艙呼叫（NapCat/Lagrange 等擴充通用）
result = await onebot.Api.call("send_poke", group_id=123, user_id=456)
```

### OB11 協定擴充（NapCat/go-cqhttp/SnowLuma 通用）

高頻擴充動作已封裝為型別化方法（`OB11ExtensionApi` mixin），支援 IDE 補全：

```python
await onebot.Api.send_poke(user_id=789, group_id=123456)
await onebot.Api.set_msg_emoji_like(message_id=123, emoji_id="76")
await onebot.Api.mark_msg_as_read(group_id=123456)
result = await onebot.Api.get_group_msg_history(group_id=123456, count=20)
await onebot.Api.set_essence_msg(message_id=123)
result = await onebot.Api.ocr_image(image="https://example.com/img.png")
```

> 擴充動作直接用 OB11 動作名稱，不加平台前綴。少數未封裝的動作用 `Api.call("action_name", ...)` 呼叫。

### Send 查詢方法（已棄用）

以下 Send 方法仍可用但已標註棄用，推薦使用 Api DSL 替代：

| Send 方法（棄用） | Api DSL 替代 |
|------------------|-------------|
| `Send.GetLoginInfo()` | `Api.get_self_info()` |
| `Send.GetFriendList()` | `Api.get_friend_list()` |
| `Send.GetGroupInfo()` | `Api.get_group_info(group_id)` |
| `Send.GetGroupList()` | `Api.get_group_list()` |
| `Send.GetGroupMemberInfo(uid)` | `Api.get_group_member_info(gid, uid)` |
| `Send.GetGroupMemberList()` | `Api.get_group_member_list(gid)` |
| `Send.GetMsg(mid)` | `Api.call("get_msg", message_id=mid)` |
| `Send.GetForwardMsg(id)` | `Api.call("get_forward_msg", id=id)` |

## 標準化對齊

本節說明適配器與 ErisPulse 標準化規範對齊的行為。規範詳情參見 SDK 文件《請求操作規範》（`docs/zh-TW/standards/request-action-spec.md`）與《API 回應規範》（`docs/zh-TW/standards/api-response.md`）。

### 請求事件處理（4.3.1 起）

適配器按請求操作規範實現請求事件的接收與回應：

- **上下文留存**：事件入口將 `request_id` 映射到 `{request_type, sub_type, group_id, account, ts}` 並快取（TTL 3600 秒、上限 512 條，請求處理成功後清理），供後續 `accept()`/`reject()` 路由使用
- **端點路由優先順序**：`accept()`/`reject()` 的 kwargs 顯式傳參（`request_type`/`sub_type`/`group_id` 為保留名）> 事件留存上下文 > 回退好友端點（`set_friend_add_request`）並輸出 WARNING
- **群組邀請/加群請求**：`request_type == "group"` 時正確路由到 `set_group_add_request`（加群 `sub_type="add"`、邀請 `sub_type="invite"`）
- **棄用說明**：4.3.1 之前透過私有參數 `_request_type` 指定請求類型的方式已棄用，傳入會被忽略

### call_api 錯誤處理

- 帳戶未連線或連線已關閉時，`call_api` 不再拋出 `ConnectionError`，而是回傳標準失敗回應（`status="failed"`、`retcode=33001`）
- API 呼叫逾時同樣回傳標準失敗回應（`retcode=33001`）

### 帳戶欄位雙相容

- `call_api` 同時接受標準欄位 `account_id` 與舊欄位名稱 `_account_id`（標準名稱優先）；框架 ApiDSL 自動適配，模組程式碼推薦使用 `account_id`
- Send DSL 全方法讀取 `send_context`：事件鏈內自動使用目前事件來源帳戶，顯式 `Using()` 指定的帳戶優先

### 錯誤碼規範

| retcode | 含義 | 觸發情境 |
|---------|------|----------|
| 0 | 成功 | 動作執行成功 |
| 33001 | 網路錯誤 | 帳戶未連線、連線已關閉、API 呼叫逾時 |
| 10002 | 不支援的動作 | 呼叫未實現的動作 |
| 10003 | 參數錯誤 | 缺少必要參數 |

> 平台原始回應資料保留在 `onebot11_raw` 欄位。

---

## 支援的訊息發送類型

所有發送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# 使用預設帳戶發送
await onebot.Send.To("group", group_id).Text("Hello World!")

# 指定特定帳戶發送
await onebot.Send.Using("main").To("group", group_id).Text("來自主帳戶的訊息")

# 鏈式修飾：@使用者 + 回覆
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("回覆訊息")

# @全體成員
await onebot.Send.To("group", group_id).AtAll().Text("公告訊息")
```

### 基礎發送方法

- `.Text(text: str)`：發送純文字訊息。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：發送圖片（支援 URL、Base64 或 bytes）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：發送語音訊息。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：發送影片訊息。
- `.Face(id: Union[str, int])`：發送 QQ 表情。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：發送檔案（自動判斷類型）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式訊息（自動轉換為 OB11）。
- `.Recall(message_id: Union[str, int])`：撤回訊息。

### 群組操作方法

以下方法需透過 `To("group", group_id)` 指定目標群組，使用群組上下文執行操作：

- `.Kick(user_id, reject_add_request=False)`：踢出群組成員。
- `.Ban(user_id, duration=1800)`：禁言群組成員（秒），0 表示解禁。
- `.WholeBan(enable=True)`：開啟/關閉全員禁言。
- `.SetAdmin(user_id, enable=True)`：設定/取消群組管理員。
- `.SetCard(user_id, card="")`：設定群名片。
- `.SetGroupName(name)`：修改群組名稱。
- `.Leave(is_dismiss=False)`：退群（群主可解散）。
- `.SetTitle(user_id, title="")`：設定群組頭銜。
- `.SetPortrait(file)`：設定群組頭像。

### 查詢方法

- `.GetMsg(message_id)`：取得訊息內容。
- `.GetForwardMsg(id)`：取得合併轉發訊息。
- `.GetLoginInfo()`：取得目前登入帳號資訊。
- `.GetFriendList()`：取得好友列表。
- `.GetGroupInfo()`：取得群組資訊（需 `To("group", group_id)`）。
- `.GetGroupList()`：取得群組列表。
- `.GetGroupMemberInfo(user_id)`：取得群組成員資訊（需 `To("group", group_id)`）。
- `.GetGroupMemberList()`：取得群組成員列表（需 `To("group", group_id)`）。

### 好友操作方法

- `.Like(user_id, times=1)`：發送好友讚（最大 10 次）。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法回傳 `self`，支援鏈式呼叫，必須在最終發送方法前呼叫：

- `.At(user_id: Union[str, int], name: str = None)`：@指定使用者（可多次呼叫）。
- `.AtAll()`：@全體成員。
- `.Reply(message_id: Union[str, int])`：回覆指定訊息。

### 鏈式呼叫範例

```python
# 基礎發送
await onebot.Send.To("group", 123456).Text("Hello")

# @單個使用者
await onebot.Send.To("group", 123456).At(789012).Text("你好")

# @多個使用者
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("大家好")

# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# 點讚
await onebot.Send.Like(123456, times=10)

# 禁言群組成員
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# 解禁
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# 踢人
await onebot.Send.To("group", 123456).Kick(789012)

# 設定群組管理員
await onebot.Send.To("group", 123456).SetAdmin(789012)

# 修改群組名稱
await onebot.Send.To("group", 123456).SetGroupName("新群組名稱")

# 取得群組資訊
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# 指定帳戶操作
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### 不支援的類型處理

如果呼叫未定義的發送方法，適配器會回傳文字提示：
```python
# 呼叫不存在的方法
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# 實際發送： “[不支援的發送類型] 方法名稱： SomeUnsupportedMethod, 參數： [...]"
```

## 請求操作（Request DSL）

適配器提供請求操作 DSL，用於處理好友請求和群組請求（加群/邀請）的同意/拒絕操作。

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

# 指定帳戶操作
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

### 請求操作回傳值

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
| request_type: group | `group` | 群組請求 |
| meta_event_type: heartbeat | `heartbeat` | 心跳 |
| notice_type: group_upload | `group_file_upload` | 群組檔案上傳 |
| notice_type: group_admin | `group_admin_change` | 群組管理員變動 |
| notice_type: group_increase | `group_member_increase` | 群組成員增加 |
| notice_type: group_decrease | `group_member_decrease` | 群組成員減少 |
| notice_type: group_ban | `group_ban` | 群組禁言 |
| notice_type: friend_add | `friend_increase` | 好友新增 |
| notice_type: friend_delete | `friend_decrease` | 好友刪除 |
| notice_type: group_recall / friend_recall | `message_recall` | 訊息撤回 |

### 平台特有事件（onebot11_ 前綴）

| OB11 原始類型 | 轉換後 detail_type | 說明 |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot 實現生命週期 |
| notify + sub_type: honor | `onebot11_honor` | 群組榮譽變更 |
| notify + sub_type: poke | `onebot11_poke` | 戳一戳 |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | 群組紅包運氣王 |
| CQ 碼未知類型 | 訊息段 `onebot11_{type}` | 未識別的 CQ 碼 |

### 事件範例

```json
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

// 群組紅包運氣王（平台特有）
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

// CQ 碼擴充訊息段
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### 擴充欄位說明

- 所有特有欄位均以 `onebot11_` 前綴標識
- 保留原始事件資料在 `onebot11_raw` 欄位
- 保留原始事件類型在 `onebot11_raw_type` 欄位
- 訊息內容中的 CQ 碼會轉換為相應的訊息段（標準類型無前綴，未知類型加 `onebot11_` 前綴）
- 回覆訊息會新增 `reply` 類型的訊息段
- @訊息會新增 `mention` 類型的訊息段

## 事件擴充方法

OneBot11 適配器為事件物件註冊了以下平台專有方法，可在事件處理器中直接呼叫：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_event = event.get_raw_event()
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### 方法列表

| 方法 | 回傳類型 | 說明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 取得 OneBot11 完整原始事件資料 |
| `get_raw_self_id()` | `str` | 取得原始 self_id（Bot 的 QQ 號碼） |
| `get_sender_info()` | `dict` | 取得完整的發送者資訊（包含 nickname、role、level 等） |
| `get_sender_role()` | `str` | 取得發送者在群組內的角色（owner/admin/member） |
| `get_sender_level()` | `int` | 取得發送者等級 |
| `get_sender_title()` | `str` | 取得發送者群組頭銜 |
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
        await event.reply(f"你的頭銜是： {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "未知")
    level = event.get_sender_level()
    await event.reply(f"暱稱： {nickname}, 等級： {level}")
```

## 配置選項

OneBot11 適配器採用多帳戶架構，每個帳戶獨立配置。配置鍵名為 `OneBotAdapter`。

### 帳戶配置欄位

| 欄位 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `bot_id` | `str` | 是 | `""` | 機器人 QQ 號碼，用於標識帳戶 |
| `mode` | `str` | 否 | `"server"` | 執行模式：`"server"`（被動監聽）或 `"client"`（主動連線） |
| `url` | `str` | 否 | `"ws://127.0.0.1:3001"` | Client 模式的 WebSocket 位址 |
| `token` | `str` | 否 | `""` | 認證 Token（Client 模式連線 Token / Server 模式驗證 Token） |
| `server_path` | `str` | 否 | `"/"` | Server 模式的 WebSocket 路徑 |
| `enabled` | `bool` | 否 | `true` | 是否啟用該帳戶 |
| `name` | `str` | 否 | `""` | 帳戶備註名稱 |

### 內建預設值

- 重連間隔：30秒
- API呼叫逾時：30秒

### 配置範例

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

### 預設配置

如果未配置任何帳戶，適配器會自動建立：
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## 發送方法回傳值

所有發送方法均回傳一個 Task 物件，可以直接 await 取得發送結果。回傳結果遵循 ErisPulse 適配器標準化回傳規範：

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

### 多帳戶發送語法

```python
# 帳戶選擇方法
await onebot.Send.Using("main").To("group", 123456).Text("主帳戶訊息")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# 透過 bot_id 選擇帳戶
await onebot.Send.Using("123456789").To("group", 123456).Text("透過QQ號碼選擇")

# API呼叫方式
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### 帳戶解析優先順序

`call_api` 和 `Using()` 中 `account_id` 參數的解析優先順序：
1. 精確匹配帳戶名稱
2. 匹配 `bot_id` 欄位
3. 匹配帳戶的任意 `str` 類型欄位
4. 回退到第一個已啟用的帳戶

## 非同步處理機制

OneBot11 適配器採用非同步非阻塞設計，確保：
1. 訊息發送不會阻塞事件處理循環
2. 多個並行發送操作可以同時進行
3. API 回應能夠及時處理
4. WebSocket 連線保持活躍狀態
5. 多帳戶並行處理，每個帳戶獨立執行

## 錯誤處理

適配器提供完善的錯誤處理機制：
1. 網路連線異常自動重連（支援每個帳戶獨立重連，間隔30秒）
2. API 呼叫逾時處理（固定30秒逾時，逾時回傳 `retcode=33001` 標準失敗回應）
3. 帳戶未連線/連線已關閉時 `call_api` 回傳 `retcode=33001` 標準失敗回應，不再拋出 `ConnectionError`
4. 連線失敗時自動按間隔重試

## 事件處理增強

多帳戶模式下，所有事件都會自動新增帳戶資訊：
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... 其他事件欄位
}
```

適配器自動維護 `self_id → account_name` 映射，`event.reply()` 無需手動指定帳戶即可正確路由到來源帳戶。

## 管理介面

```python
# 取得所有帳戶資訊
accounts = onebot.accounts

# 檢查帳戶連線狀態
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# 動態啟用/停用帳戶（需要重新啟動適配器）
onebot.accounts["test"].enabled = False
```

## self_id 自動映射

適配器會自動建立 OneBot `self_id`（QQ號碼）到 `account_name` 的映射關係，用於事件回路由：

```python
# 適配器內部自動完成
# 當收到事件時，self.user_id 欄位填充為 bot_id
# 適配器自動記錄： self_id("123456789") → account_name("main")

# 因此 event.reply() 可以自動找到正確的帳戶發送訊息
@message.on_message()
async def handler(event):
    await event.reply("自動路由到正確的帳戶")
```