# 雲湖使用者平台特性文件

YunhuUserAdapter 是基於雲湖使用者帳戶協定構建的適配器，透過使用者信箱帳戶登入，使用 WebSocket 接收事件，提供統一的事件處理和訊息操作介面。

---

## 文件資訊

- 對應模組版本: 4.6.1
- 維護者: wsu2059
- 最後更新: 2026-11-10

## 基本資訊

- 平台簡介：雲湖（Yunhu）是一個企業級即時通訊平台，本適配器透過**使用者帳戶**（而非機器人帳戶）與之互動
- 適配器名稱：YunhuUserAdapter
- 多帳戶支援：支援透過帳戶名稱識別並設定多個使用者帳戶
- 鏈式修飾支援：支援 `.Reply()` 等鏈式修飾方法
- OneBot12 相容：支援發送 OneBot12 格式訊息
- 通訊方式：透過信箱登入取得 token，使用 WebSocket 接收事件，以 HTTP + Protobuf 協定發送訊息
- 會話類型：支援私聊（user）、群聊（group）、機器人會話（chat_type=3，4.6.1 起映射為 `private`）

## v5 範式更新（4.2.0）

- **BaseConverter 繼承**；**spawn_background 任務歸屬**（WS 監聽任務）
- **使用者 API 全集**（基於 yhchatAPI full.proto / v1 端點，protobuf over HTTP）：
  - 使用者：get_user / edit_nickname / edit_avatar
  - 好友：通訊錄 / 申請列表 / 申請 / 同意 / 忽略 / 刪除
  - 群組：群資訊 / 成員列表 / 建立 / 解散 / 邀請 / 移出 / 禁言 / 機器人列表
  - 會話：會話列表；訊息：列表 / 撤回 / 按鈕回報
- **框架軟依賴**：執行時偵測 ErisPulse>=2.7.1 並提示；啟動時輸出版本日誌

## 已對接平台功能清單

### 事件接收（WebSocket，protobuf 編碼）

| WS cmd | 事件 | 說明 |
|--------|------|------|
| `push_message` | `message` | 私聊/群聊/Bot 會話訊息（文字/HTML/Markdown/圖片/影片/語音/檔案/表情/表單/文章/貼圖/按鈕/A2UI） |
| `edit_message` | `notice` (`message_edit`) | 訊息編輯通知 |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | 超級檔案分享 |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | 機器人公告看板 |

### Api DSL 方法對照（ YunhuHTTPClient → 使用者 API v1 端點 ）

| 分類 | Api 方法 | 端點 | 說明 |
|------|---------|------|------|
| 帳戶 | `get_self_info()` | `/user/info` | 登入使用者資訊（暱稱/頭像/user_id） |
| 使用者 | `get_user(user_id)` | `/user/get-user` | 使用者詳細資訊 |
| 使用者 | `edit_nickname(nickname)` | `/user/edit-nickname` | 修改自己暱稱 |
| 使用者 | `edit_avatar(url)` | `/user/edit-avatar` | 修改自己頭像 |
| 好友 | `get_friend_address_book(md5)` | `/friend/address-book-list` | 通訊錄（游標分頁） |
| 好友 | `get_friend_requests()` | `/friend/request-list` | 好友/加群申請列表 |
| 好友 | `friend_apply(user_id, desc)` | `/friend/apply` | 申請加入好友 |
| 好友 | `friend_agree_apply(user_id)` | `/friend/agree-apply` | 同意好友申請 |
| 好友 | `friend_ignore_apply(user_id)` | `/friend/ignore-apply` | 忽略好友申請 |
| 好友 | `friend_delete(user_id)` | `/friend/delete-friend` | 刪除好友 |
| 群組 | `get_group_info(group_id)` | `/group/info` | 群組資訊 |
| 群組 | `get_group_member_list(group_id)` | `/group/list-member` | 群成員列表（支援關鍵字） |
| 群組 | `create_group(name, ...)` | `/group/create-group` | 建立群組 |
| 群組 | `dismiss_group(group_id)` | `/group/dismiss-group` | 解散群組 |
| 群組 | `group_invite(group_id, user_ids)` | `/group/invite` | 邀請進群 |
| 群組 | `group_remove_member(group_id, user_id)` | `/group/remove-member` | 移出群成員 |
| 群組 | `group_gag_member(group_id, user_id, 秒)` | `/group/gag-member` | 禁言群成員（0=解除） |
| 群組 | `get_group_bot_list(group_id)` | `/group/bot-list` | 群內機器人列表 |
| 會話 | `get_conversation_list(md5)` | `/conversation/list` | 會話列表（游標分頁） |
| 訊息 | `get_message_list(chat_id, chat_type, ...)` | `/msg/list-message` | 訊息列表（多種分頁變體見 HTTP 用戶端） |
| 訊息 | `delete_message(msg_id, chat_id, chat_type)` | `/msg/recall-msg` | 撤回訊息（批次撤回見 HTTP 用戶端） |
| 訊息 | `button_report(...)` | `/msg/button-report` | 按鈕點擊回報 |
| 元動作 | `get_status` / `get_version` / `get_supported_actions` | - | 執行狀態/版本/支援動作 |

### 尚未對接（端點已知，full.proto 訊息齊備，可按需擴充）

- 使用者：驗證碼登入、勳章、金豆記錄、綁定手機/信箱、通知設定、使用者資料存取
- 好友：免打擾（no-notify）、刪除申請記錄
- 群組：指令列表、分類、推薦、直播間、編輯群資訊/群暱稱/關鍵字、入群自動審核、群檔案限制、事件 SSE
- 會話：置頂/排序/刪除、免打擾
- 訊息：轉發、A2UI 提交、訊息列表圖片取得、檔案下載記錄
- 群標籤：list / relate / relate-cancel / create / edit / delete / members（端點 `/group-tag/*`）

> 擴充方式：在 `YunhuHTTPClient` 中按既有模式追加方法（`_proto_request` / `_json_request` 通用封裝），再於 `Api` 類別公開即可。端點與訊息定義參考 `yhchatAPI/src/api/v1/*.md` 與 `yhchatAPI/src/full.proto`。

### 使用者 API 範例

```python
from ErisPulse import sdk
yunhu_user = sdk.adapter.get("yunhu_user")

result = await yunhu_user.Api.get_self_info()
result = await yunhu_user.Api.get_friend_requests()          # 好友申請列表
await yunhu_user.Api.friend_agree_apply(user_id)             # 同意好友申請
result = await yunhu_user.Api.get_group_member_list(group_id)
result = await yunhu_user.Api.get_conversation_list()        # 會話列表
await yunhu_user.Api.delete_message(msg_id, chat_id, chat_type)  # 撤回
```

## 好友申請處理（4.6.0 新增）

雲湖使用者端 WebSocket **不推送好友申請事件**，適配器預設開啟輪詢拉取申請列表並合成標準請求事件（遵循 [請求操作規範](../standards/request-action-spec.md)）：

- **帳戶設定**：`poll_friend_requests = true`（預設開啟）、`poll_interval = 60`（輪詢間隔秒，最小 5 秒）；設為 `false` 可關閉輪詢
- **輪詢邏輯**：按間隔拉取 `/friend/request-list`，diff 出**新增申請**後合成標準 request 事件：
  - `type="request"`、`detail_type="friend"`
  - `request_id` = **申請方 user_id**
  - `user_nickname` / `comment` 來自申請資料，原始條目保留在 `yunhu_user_raw`
- **事件去重**：已處理的申請不會重複產出事件

### 模組端審核（事件方式）

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    if event.get("platform") != "yunhu_user":
        return

    applicant = event.get("user_id")
    nickname = event.get("user_nickname", "")
    comment = event.get("comment", "")
    print(f"好友申請: {nickname}({applicant}) 附言: {comment}")

    # 同意好友申請（accept = 同意好友）
    await event.approve()
    # 或忽略申請（reject = 忽略）
    # await event.reject()
```

### 直接呼叫適配器（Request DSL）

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# request_id 即申請方 user_id
await yunhu_user.Request("申請人user_id").accept()   # accept = 同意好友
await yunhu_user.Request("申請人user_id").reject()   # reject = 忽略申請

# 多帳戶：指定帳戶審核
await yunhu_user.Request("申請人user_id").Using("default").accept()
```

> `accept()` 內部呼叫 `/friend/agree-apply`，`reject()` 呼叫 `/friend/ignore-apply`；兩者均回傳標準回應（`status` / `retcode` / `message` / `yunhu_user_raw`）。

## 標準化對齊（4.6.1）

回應結構與錯誤碼遵循 [API 回應規範](../standards/api-response.md)。

### 標準回應

Api DSL 20 個方法統一回傳標準回應：`status` / `retcode` / `data` / `message_id` / `message`，平台原始資料同時位於 `data` 與頂層 `yunhu_user_raw`。`get_self_info` 的原始資料移至回應頂層 `yunhu_user_raw`。

### 錯誤碼規範

| retcode | 含義 | 說明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | 網路錯誤 | HTTP/WS 連線類異常 |
| 34100 | 平台失敗 | 雲湖使用者端回傳失敗；原始回應保留在 `yunhu_user_raw` |
| 10002 | 不支援 | 平台無對應能力的標準動作 |
| 10003 | 參數錯誤 | 缺少 request_id、無可用帳戶等 |

### 事件欄位修正

- **`chat_type=3`（機器人會話）映射為 `private`**（原 `"bot"` 非標準接收類型；原始 chat_type 保留在 `yunhu_user_raw`）
- **`edit_message` 事件 id 加上 `edit:` 前綴**：不再與 create 事件產生相同 id 而被下游去重吞掉
- **`message_id` 始終存在**：缺失時以空字串作為後備
- **事件 `time` 使用訊息自身的時間戳**（秒級），不再統一取適配器處理時刻

### 帳戶與多帳戶

- `call_api` 支援雙相容帳戶欄位：`account_id`（標準名）/ `_account_id`（舊名），框架 ApiDSL（`Api.Using(...)`）自動適配
- `Send` 讀取 `send_context`（以事件帳戶作為後備）：從事件上下文呼叫 `Send` 時預設回落至來源帳戶
- 事件回覆建議直接使用 `event.reply()`，自動路由至受理帳戶

---

## 支援的訊息發送類型

所有發送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

支援的發送類型包括：
- `.Text(text: str, buttons: Optional[List] = None)`：發送純文字訊息。
- `.Html(html: str, buttons: Optional[List] = None)`：發送 HTML 格式訊息。
- `.Markdown(markdown: str, buttons: Optional[List] = None)`：發送 Markdown 格式訊息。
- `.MergeForward(nodes, title="合併聊天記錄")`：發送合併轉發訊息（渲染為 `<details>` 摺疊 HTML 卡片，經 msg_type=8 HTML 通道發出）。
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`：發送圖片訊息，支援 URL、本機路徑或二進位資料。
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`：發送影片訊息，支援 URL、本機路徑或二進位資料。
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`：發送語音訊息，支援 URL、本機路徑或二進位資料，自動偵測音訊時長。
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`：`.Audio()` 的別名。
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`：發送檔案訊息，支援 URL、本機路徑或二進位資料。
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`：發送表情/貼圖訊息，支援貼圖 ID、貼圖 URL 或二進位圖片資料。
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`：發送 A2UI 訊息（訊息類型 14），A2UI JSON 資料會填入 text 欄位發送。
- `.Edit(msg_id: str, text: str, content_type: str = "text")`：編輯已有訊息。
- `.Recall(msg_id: str)`：撤回訊息。
- `.Raw_ob12(message: Union[List, Dict])`：發送 OneBot12 格式訊息。

### 媒體檔案處理

所有媒體類型（圖片、影片、音訊、檔案）支援以下輸入方式：
- **URL**：`"https://example.com/image.jpg"` — 自動下載後上傳
- **本機路徑**：`"/path/to/file.jpg"` — 自動讀取後上傳
- **二進位資料**：`open("file.jpg", "rb").read()` — 直接上傳

媒體檔案會自動上傳到七牛雲儲存，支援以下特性：
- 自動透過 `filetype` 函式庫偵測檔案類型和 MIME
- 自動計算檔案大小
- 語音檔案自動偵測時長（支援 MP3、MP4/M4A 格式）

### 按鈕參數說明

`buttons` 參數是一個巢狀列表，表示按鈕的佈局與功能。每個按鈕物件包含以下欄位：

| 欄位         | 類型   | 是否必填 | 說明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | 按鈕上的文字                                                         |
| `actionType` | int    | 是       | 動作類型：<br>`1`: 跳轉 URL<br>`2`: 複製<br>`3`: 點擊回報            |
| `url`        | string | 否       | 當 `actionType=1` 時使用，表示跳轉的目標 URL                         |
| `value`      | string | 否       | 當 `actionType=2` 時，該值會複製到剪貼簿<br>當 `actionType=3` 時，該值會發送給訂閱端 |

範例：
```python
buttons = [
    [
        {"text": "複製", "actionType": 2, "value": "xxxx"},
        {"text": "點擊跳轉", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "回報事件", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("帶按鈕的訊息")
```

### 鏈式修飾方法（可組合使用）

鏈式修飾方法回傳 `self`，支援鏈式呼叫，必須在最終發送方法前呼叫：

- `.Reply(message_id: str)`：回覆指定訊息。
- `.At(user_id: str)`：@指定使用者（文字形式 @user_id）。
- `.AtAll()`：@所有人（偽@全體，發送 @all 文字）。
- `.Buttons(buttons: List)`：加入按鈕。

> **注意：** 因為使用者帳戶較為特殊，即便不是管理員也可以 @全體，但這裡的 `AtAll()` 只會發送一個艾特全體的文字，是一個偽@全體。

### 鏈式呼叫範例

```python
# 基礎發送
await yunhu_user.Send.To("user", user_id).Text("Hello")

# 回覆訊息
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("回覆訊息")

# 回覆 + 按鈕
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("帶回覆和按鈕的訊息")

# 指定帳戶 + 回覆 + 按鈕
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("完整鏈式呼叫")
```

### OneBot12 訊息支援

適配器支援發送 OneBot12 格式的訊息，便於跨平台訊息相容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式訊息。

```python
# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 支援自動將混合訊息段分組處理：
- `text`、`mention` 類型可合併為一組發送
- `image`、`video`、`audio`、`file`、`face`、`markdown`、`html`、`a2ui` 等類型各自獨立成組
- `reply` 類型可附加到任何組

## 發送方法回傳值

所有發送方法均回傳一個 Task 物件，可以直接 await 取得發送結果。回傳結果遵循 ErisPulse 適配器標準化回傳規範：

```python
{
    "status": "ok",           // 執行狀態
    "retcode": 0,             // 回傳碼
    "data": {...},            // 回應資料
    "message_id": "123456",   // 訊息ID
    "message": "",            // 錯誤訊息
    "yunhu_user_raw": {...}   // 原始回應資料
}
```

## 特有事件類型

需要 `platform == "yunhu_user"` 偵測後再使用本平台特性

### 核心差異點

1. 特有事件類型：
    - 超級檔案分享：`yunhu_user_file_send`
    - 機器人公告看板：`yunhu_user_bot_board`
    - 訊息編輯通知：`message_edit`
    - 訊息刪除通知：`message_delete`（撤回）
2. 特有訊息段類型：
    - 表單訊息段：`yunhu_user_form`
    - 文章訊息段：`yunhu_user_post`
    - 貼圖訊息段：`yunhu_user_sticker`
    - 按鈕訊息段：`yunhu_user_button`
    - A2UI 訊息段：`a2ui`
3. 擴充欄位：
    - 所有特有欄位均以 `yunhu_user_` 前綴標示
    - 保留原始資料於 `yunhu_user_raw` 欄位
    - 原始事件類型記錄於 `yunhu_user_raw_type` 欄位
    - 私聊中 `self.user_id` 表示目前登入使用者ID

### 支援的原始事件類型

| 原始事件類型 | OneBot12 類型 | 說明 |
|-------------|--------------|------|
| `push_message` | `message` | 推送訊息（私聊、群聊、Bot 會話） |
| `edit_message` | `notice` (`message_edit`) | 訊息編輯事件 |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | 超級檔案分享事件 |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | 機器人公告看板事件 |

> 其他事件類型（如 `heartbeat_ack`、`draft_input`、`stream_message` 等）會被忽略。

### OneBot12 支援的 detail_type

| OneBot12 detail_type | 雲湖 chat_type | 說明 |
|---------------------|---------------|------|
| `private` | 1 | 私聊訊息 |
| `group` | 2 | 群聊訊息 |
| `private` | 3 | 機器人會話（4.6.1 起映射為 `private`，原 `"bot"` 非標準；原始 chat_type 保留在 `yunhu_user_raw`） |

### 訊息事件範例

```python
{
    "id": "event_id",
    "time": 1234567890,
    "type": "message",
    "detail_type": "group",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message": [
        {"type": "text", "data": {"text": "訊息內容"}}
    ],
    "alt_message": "訊息內容",
    "user_id": "sender_user_id",
    "user_nickname": "發送者暱稱",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### 訊息編輯通知範例

```python
{
    "type": "notice",
    "detail_type": "message_edit",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message_id": "msg_id",
    "user_id": "sender_user_id",
    "user_nickname": "發送者暱稱",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### 超級檔案分享事件範例

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_file_send",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "user_id": "send_user_id",
    "user_nickname": "",
    "yunhu_user_file_send": {
        "send_user_id": "發送者ID",
        "user_id": "接收使用者ID",
        "send_type": "發送類型",
        "data": "檔案資料"
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "file_send_message"
}
```

### 機器人公告看板事件範例

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_bot_board",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "bot_id": "bot_id",
    "bot_name": "機器人名稱",
    "yunhu_user_bot_board": {
        "bot_id": "bot_id",
        "chat_id": "chat_id",
        "chat_type": 1,
        "content": "公告內容",
        "content_type": 1,
        "last_update_time": 1234567890
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "bot_board_message"
}
```

### 事件處理範例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_yunhu_user_message(event):
    """處理雲湖使用者訊息"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"使用者 {user_nickname}({user_id}): {alt_message}")
    
    # 檢查訊息段中的特有類型
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"收到表單訊息: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"收到文章訊息: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"收到貼圖訊息: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"訊息包含按鈕: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"收到A2UI訊息: {a2ui_data}")
    
    # 使用 event.reply() 自動回覆
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """處理雲湖使用者通知事件"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"使用者 {user_nickname} 編輯了訊息 {message_id}")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"收到超級檔案分享: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"機器人 {bot_name} 發布了公告: {board_data.get('content', '')}")
```

## 擴充欄位說明

- 所有特有欄位均以 `yunhu_user_` 前綴標示，避免與標準欄位衝突
- 保留原始資料於 `yunhu_user_raw` 欄位，便於存取雲湖平台的完整原始資料
- 原始事件類型記錄於 `yunhu_user_raw_type` 欄位（如 `push_message`、`edit_message` 等）
- `self.user_id` 表示目前登入使用者ID（從登入回應中取得）
- 超級檔案分享透過 `yunhu_user_file_send` 欄位提供檔案分享資料
- 機器人公告看板透過 `yunhu_user_bot_board` 欄位提供公告資料

### 特有訊息段類型

#### 表單訊息段 (yunhu_user_form)

當 content_type 為 5 時，訊息段類型為 `yunhu_user_form`：

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "表單資料"
    }
}
```

#### 文章訊息段 (yunhu_user_post)

當 content_type 為 6 時，訊息段類型為 `yunhu_user_post`：

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "文章ID",
        "post_title": "文章標題",
        "post_content": "文章內容"
    }
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `post_id` | string | 文章唯一識別碼 |
| `post_title` | string | 文章標題 |
| `post_content` | string | 文章內容 |

#### 貼圖訊息段 (yunhu_user_sticker)

當 content_type 為 7 時，訊息段類型為 `yunhu_user_sticker`：

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "貼圖圖片URL"
    }
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `file_id` | string | 貼圖圖片URL |

#### 按鈕訊息段 (yunhu_user_button)

訊息中包含按鈕時，會附加 `yunhu_user_button` 訊息段：

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "按鈕文字", "actionType": 3, "value": "值"}]]
    }
}
```

#### A2UI 訊息段 (a2ui)

當 content_type 為 14 時，訊息段類型為 `a2ui`：

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSON資料"
    }
}
```

---

## 多帳戶設定

### 設定說明

YunhuUserAdapter 支援同時設定並執行多個使用者帳戶。

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket 重新連線間隔（秒）
ws_timeout = 70             # WebSocket 逾時時間（秒）

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # 使用者信箱（必填）
password = "password1"       # 使用者密碼（必填）
platform = "windows"         # 登入平台（選填，預設 windows）
device_id = ""               # 裝置ID（選填，留空則自動產生）
poll_friend_requests = true  # 輪詢好友申請（選填，預設 true）
poll_interval = 60           # 好友申請輪詢間隔（秒，選填，預設 60）
enabled = true               # 是否啟用（選填，預設為 true）

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**設定項目說明：**
- `email`：使用者信箱（必填），用於登入雲湖平台
- `password`：使用者密碼（必填）
- `platform`：登入平台標識（選填，預設為 `windows`），可選值：`windows`、`macos`、`linux`、`ios`、`android`
- `device_id`：裝置ID（選填，留空則自動產生），建議填寫固定值以保持會話一致性
- `poll_friend_requests`：是否輪詢好友申請（選填，預設 `true`；見「好友申請處理」）
- `poll_interval`：好友申請輪詢間隔（秒，選填，預設 60，最小 5）
- `enabled`：是否啟用該帳戶（選填，預設為 `true`）

**適配器層級設定：**
- `ws_reconnect_interval`：WebSocket 重新連線間隔（秒，預設 30）
- `ws_timeout`：WebSocket 逾時時間（秒，預設 70）

**重要提示：**
1. 適配器使用信箱登入方式取得 token，登入後透過 WebSocket 接收事件
2. WebSocket 連線中斷後會自動重新連線，最多重試 3 次
3. 建議為每個帳戶設定固定的 `device_id`，以保持會話一致性
4. 未修改的範本帳戶（預設信箱和密碼）會被自動跳過

### 使用 Send DSL 指定帳戶

可以透過 `Using()` 方法指定使用哪個帳戶發送訊息。該方法支援兩種參數：
- **帳戶名稱**：設定中的帳戶名稱（如 `default`、`account2`）
- **user_id**：登入後取得的使用者 ID

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# 使用帳戶名稱發送訊息
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# 使用 user_id 發送訊息（自動匹配對應帳戶）
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# 未指定時使用第一個啟用的帳戶
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **提示：** 使用 `user_id` 時，系統會自動尋找設定中匹配的帳戶。這在處理事件回覆時特別有用，可以直接使用 `event["self"]["user_id"]` 來回覆同一帳戶。

### 事件中的帳戶識別

接收到的事件會自動包含對應的使用者ID資訊：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # 取得目前登入使用者ID
        my_user_id = event["self"]["user_id"]
        print(f"訊息來自帳戶: {my_user_id}")
        
        # 使用相同帳戶回覆訊息
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("回覆訊息")
```

### 日誌資訊

適配器會在日誌中自動包含帳戶資訊，便於除錯與追蹤：

```
[INFO] 帳戶 default (user1@example.com) 登入成功，使用者ID: 12345678
[INFO] 帳戶 default WebSocket 監聽任務已啟動
[INFO] 帳戶 account2 (user2@example.com) 登入成功，使用者ID: 87654321
```

### 管理介面

```python
# 取得所有帳戶資訊
accounts = yunhu_user.accounts
# 回傳格式: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# 檢查帳戶是否啟用
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# 透過帳戶名稱取得 HTTP 用戶端
http_client = yunhu_user._get_http_client("default")

# 透過 user_id 尋找帳戶
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API 呼叫

適配器提供 `call_api` 方法，支援直接呼叫平台 API：

```python
# 發送訊息
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# 編輯訊息
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="新內容",
    content_type="text"
)

# 撤回訊息
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# 批次撤回訊息
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# 取得訊息列表
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# 取得訊息編輯記錄
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# 按鈕事件報告
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**支援的 API 端點：**

| 端點 | 說明 |
|------|------|
| `/send` | 發送訊息 |
| `/edit` | 編輯訊息 |
| `/recall` | 撤回訊息 |
| `/recall_batch` | 批次撤回訊息 |
| `/list` | 取得訊息列表 |
| `/list_by_seq` | 透過序列取得訊息 |
| `/list_by_mid_seq` | 透過訊息ID和序列取得訊息 |
| `/list_edit_record` | 取得訊息編輯記錄 |
| `/button_report` | 按鈕事件報告 |