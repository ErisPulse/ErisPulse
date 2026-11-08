# 適配器標準化轉換規範

> [!TIP]
> **什麼時候需要閱讀本文**：當你在適配器中將平台原生事件轉換為 OneBot12 標準事件時——確認必須欄位、訊息段結構、擴展欄位命名（`{platform}_` 前綴）、會話類型推斷時對照本文。不需要則跳過。

## 1. 核心原則
1. 嚴格相容：所有標準欄位必須完全遵循 OneBot12 規範
2. 明確擴展：平台特有的功能必須添加 {platform}_ 前綴（例如 yunhu_form）
3. 數據完整：原始事件數據必須保留在 {platform}_raw 欄位中，原始事件類型必須保留在 {platform}_raw_type 欄位中
4. 時間統一：所有時間戳必須轉換為 10 位 Unix 時間戳（秒級）
5. 平台統一：platform 項命名必須與你在 ErisPulse 中註冊的名稱/別稱一致

## 2. 標準欄位要求

### 2.1 必須欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | string | 事件唯一識別碼 |
| time | integer | Unix時間戳（秒級） |
| type | string | 事件類型 |
| detail_type | string | 事件詳細類型（詳見[會話類型標準](session-types.md)） |
| sub_type | string | 事件子類型 |
| platform | string | 平台名稱 |
| self | object | 機器人自身資訊 |
| self.platform | string | 平台名稱 |
| self.user_id | string | 機器人使用者ID |

> **OneBot12 基線**：`self.platform` / `self.user_id` 與訊息事件的 `message_id` 均為 OneBot12 基線已定義的欄位，框架直接採用基線定義，不再引入自有擴充鍵（`self.account_id` 為限定擴充鍵，僅用於動態帳戶未取得 user_id 前的代位識別，見 §6）。

**detail_type 規範**：
- 必須使用 ErisPulse 標準會話類型（詳見 [會話類型標準](session-types.md)）
- 支援的類型：`private`, `group`, `user`, `channel`, `guild`, `thread`
- 配接器負責將平台原生類型映射到標準類型

### 2.2 訊息事件欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| message_id | string | 訊息ID（OneBot12 基線標準必選欄位，配接器必須產出事件頂層） |
| message | array | 訊息段陣列 |
| alt_message | string | 訊息段備用文字 |
| user_id | string | 使用者ID |
| user_nickname | string | 使用者暱稱（可選） |

### 2.3 通知事件欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| user_id | string | 使用者ID |
| user_nickname | string | 使用者暱稱（可選） |
| operator_id | string | 操作者ID（可選） |

### 2.4 請求事件欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| user_id | string | 使用者ID |
| user_nickname | string | 使用者暱稱（可選） |
| comment | string | 請求附言（可選） |
| request_id | string | 請求識別碼（**強烈推薦**，用於同意/拒絕請求操作） |

**`request_id` 欄位說明**：
- `request_id` 是請求事件的唯一操作識別碼，用於透過 `HandleRequest` DSL 執行同意/拒絕操作
- 配接器在轉換請求事件時，應將平台原生的請求識別映射到此欄位
- 如果平台本身沒有請求ID，配接器應產生一個唯一識別（如基於時間戳+使用者ID的雜湊）
- 當 `request_id` 缺失時，`event.approve()` / `event.reject()` 將拋出 `ValueError`

## 3. 事件格式示例

### 3.1 消息事件 (message)
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽獎 超級大獎"
      }
    }
  ],
  "alt_message": "抽獎 超級大獎",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽獎",
    "args": "超級大獎"
  }
}
```

### 3.2 通知事件 (notice)
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 請求事件 (request)
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "請加好友",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. 訊息段標準

### 4.1 標準訊息段

標準訊息段**不需要**平台前綴。

| 類型 | 說明 | data 欄位 |
|------|------|----------|
| `text` | 純文字 | `text: str` |
| `image` | 圖片 | `file`, `url: str` |
| `voice` | 語音（當場錄製的聲音，區別於 `audio`） | `file`, `url: str` |
| `audio` | 音訊（可直接播放的音樂檔案，區別於 `voice`） | `file`, `url: str` |
| `video` | 影片 | `file`, `url: str` |
| `file` | 檔案 | `file`, `url: str`, `filename: str` |
| `mention` | @使用者 | `user_id: str`, `user_name: str` |
| `mention_all` | @全體成員 | 無 data 欄位 |
| `reply` | 回覆 | `message_id: str`, `user_id: str`（回覆的原發送者，接收方向由適配器盡可能填入） |
| `location` | 位置 | `latitude: float`, `longitude: float`, `title: str`（可選）, `content: str`（可選） |
| `face` | 表情（ErisPulse 跨平台擴展段） | `id: str` |
| `keyboard` | 按鈕/行內鍵盤（ErisPulse 跨平台擴展段） | `rows: list[list[button]]`（見 4.1.1） |

> **與 OneBot12 基線的欄位映射**：媒體段（`image` / `voice` / `audio` / `video` / `file`）在 OneBot12 基線中為 `file_id: str`；本標準的 `file`（發送形態超集：URL / 本地路徑 / bytes）與 `url`（接收回鏈）由適配器雙向映射到平台的 `file_id` 資源。`face` / `keyboard` 為 OneBot12 基線之外的擴展段。

**媒體段 `file` 欄位格式**（發送方向，`image` / `audio` / `video` / `file` 通用）：

| 形態 | 範例 | 適配器要求 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/a.png` | **必須**接受 |
| 本地檔案路徑 | `/tmp/a.png`、`C:\tmp\a.png` | **必須**接受 |
| 二進位資料 | `bytes` | **必須**接受 |
| `file://` URI / Base64 / Data URI | `file:///tmp/a.png`、`data:image/png;base64,...` | **應當**接受 |

> 完整的媒體發送協議（形態判定順序、檔案名推導、能力降級階梯）見
> [發送方法規範 §2.1](send-method-spec.md#21-媒體訊息發送協議image--voice--video--file)。

**欄位方向語義**：

- `file`：**發送方向**的內容來源（上述形態）；**接收方向**由適配器填平台可取回的形態
  （通常為可下載 URL，或 `get_file` 類動作可用的資源標識）
- `url`：接收方向的平台回鏈（適配器轉換平台事件時盡可能填入，供模組直接取用）；發送方向可不填
- `filename`：`file` 段的檔案名（發送方向可選，預設時適配器按
  [發送方法規範 §2.1.3](send-method-spec.md) 的推導順序生成；接收方向**應當**填平台原始檔案名）

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard 按鈕/行內鍵盤段（跨平台通用）

按鈕/行內鍵盤在多個平台（Telegram / 雲湖 / QQBot / Kook / Discord 等）均有對應能力，
屬於**跨平台通用概念**，因此作為標準訊息段（無平台前綴）。適配器應將標準段轉換為
平台原生結構；平台原生擴展段（如 `telegram_inline_keyboard`）繼續保留透傳。

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "選項A", "type": "callback", "data": "vote:A"},
        {"label": "官網",   "type": "link",     "data": "https://example.com"}
      ]
    ]
  }
}
```

**欄位說明：**

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `rows` | 二維陣列 | 是 | 每個子陣列為一行按鈕 |
| `rows[][].label` | str | 是 | 按鈕顯示文字 |
| `rows[][].type` | str | 是 | `callback`（點擊回傳資料）/ `link`（跳轉URL） |
| `rows[][].data` | str | 是 | 回呼資料（type=callback）或跳轉地址（type=link） |
| `rows[][].*` | Any | 否 | 平台特有可選欄位（如 `web_app`、`menus`），適配器按能力映射或忽略 |

**適配器轉換參考**（完整映射與互動回呼事件標準見 [跨平台互動元件標準](standardization-guide.md)）：

| 平台 | 標準段 → 平台原生 |
|------|------------------|
| Telegram | `inline_keyboard`：`[{text, callback_data \| url}]` |
| 雲湖 | `buttons`：`[{label, action_type: 2=回呼 \| 1=跳轉, ...}]` |
| QQBot | `keyboard.content.rows`：`[{label, type: 2=回呼 \| 0=跳轉, data}]`（需 markdown 類型訊息） |
| Kook | 卡片 action-group 模組 |
| Discord | components：`action_row` + `buttons`（custom_id/url） |

### 4.2 平台擴展訊息段

平台特有的訊息段需要添加平台前綴：

```json
// 雲湖 - 表單
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "報名表"}}

// Telegram - 貼紙
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**擴展訊息段要求**：
1. **data 內部欄位不加前綴**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` 而非 `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **提供降級方案**：模組可能不識別擴展訊息段，適配器應在 `alt_message` 中提供文字替代
3. **文件完備**：每個擴展訊息段必須在適配器文件中說明 `type`、`data` 結構和使用場景

## 5. 未知事件處理

對於無法識別的事件類型，應產生警告事件：
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "不支援的事件類型: special_event",
  "alt_message": "此事件類型不受此系統支援。"
}
```
---

## 6. 擴充命名規範

### 6.1 欄位命名

**規則**：`{platform}_{field_name}`

```
平台前綴    欄位名            完整欄位名
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**要求**：
- `platform` 必須與配接器註冊時的平台名完全一致（區分大小寫）
- `field_name` 使用 `snake_case` 命名
- 禁止使用雙底線 `__` 開頭（Python 保留）
- 禁止與標準欄位同名（如 `type`、`time`、`message` 等）

### 6.2 訊息段類型命名

**規則**：`{platform}_{segment_type}`

標準訊息段類型（`text`、`image`、`audio`、`video`、`mention`、`reply` 等）**不得**添加平台前綴。只有平台特有的訊息段類型才需要添加前綴。

### 6.3 原始資料欄位命名

以下欄位名是**保留欄位**，所有配接器必須遵循：

| 保留欄位 | 類型 | 說明 |
|---------|------|------|
| `{platform}_raw` | `any` | 平台原始事件資料的完整副本 |
| `{platform}_raw_type` | `string` | 平台原始事件類型識別碼 |

**要求**：
- `{platform}_raw` 必須是原始資料的深層複製，而非參考
- `{platform}_raw_type` 必須是字串，即使平台使用數字類型也要轉換為字串
- 這兩個欄位在所有事件中**必須存在**（無法取得時為 `null` 和空字串 `""`）

### 6.4 平台特有欄位範例

```json
{
  "yunhu_command": {
    "name": "抽獎",
    "args": "超級大獎"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 巢狀擴充欄位

擴充欄位可以是簡單值，也可以是巢狀物件：

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**巢狀欄位要求**：
- 頂層鍵必須帶平台前綴
- 巢狀內部欄位**不添加**平台前綴
- 巢狀深度建議不超過 3 層

### 6.6 `self` 欄位擴充

`self` 物件的標準必選欄位（`platform`、`user_id`）見 §2.1，以下是 ErisPulse 擴充的可選欄位：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `self.user_name` | `string` | 機器人暱稱 |
| `self.avatar` | `string` | 機器人頭像 URL |
| `self.account_id` | `string` | **限定擴充鍵（帳戶名代位）**：動態注入的帳戶在尚未取得機器人 `user_id` 時，以帳戶名 / 帳戶識別碼代位填充，保證事件可歸屬；`self.user_id` 可用後必須優先填入。框架按 `account_id or user_id` 口徑相容兩者——帳戶名代位時 `reply()` 綁定經帳戶名匹配解析回正確帳戶 |

> **執行期邊界：事件必須始終攜帶 `self.user_id`（含綁定未建立的期間）**。連線層在綁定表回填、connect meta 到達之前收到的事件，同樣要注入已知識別碼：機器人 `user_id` 尚未取得時以帳戶名填充 `self.account_id` 代位（框架按 `account_id or user_id` 口徑解析，帳戶名可經帳戶名匹配路由回正確帳戶），已取得則優先填 `self.user_id`——框架在事件的任何階段都需要能判斷「這條事件來自哪個帳戶」。缺失時的後果是確定的：`event.reply()` 不注入帳戶、未指定帳戶的傳送回落第一個啟用帳戶，多帳戶配接器即表現為「從預設帳戶發出」。

> **Bot 狀態追蹤**：配接器透過傳送 `type: "meta"` 事件告知框架 Bot 的連線狀態。支援的 `detail_type`：`connect`（上線）、`heartbeat`（心跳）、`disconnect`（離線）。系統自動從中擷取 `self` 欄位的 Bot 元資訊進行狀態追蹤。此外，普通事件中的 `self` 欄位也會自動發現 Bot。詳見 [配接器系統 API - Bot 狀態管理](../api-reference/adapter-system.md)。

---

## 7. 會話類型擴展

ErisPulse 在 OneBot12 標準的 `private`、`group` 基礎上擴展了以下會話類型：

| 類型 | OneBot12 標準 | ErisPulse 擴展 | 說明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 一對一私聊 |
| `group` | ✅ | — | 群聊 |
| `user` | — | ✅ | 用戶類型（Telegram 等） |
| `channel` | — | ✅ | 頻道（廣播式） |
| `guild` | — | ✅ | 伺服器/社群 |
| `thread` | — | ✅ | 話題/子頻道 |

**適配器自訂類型擴展**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# 在適配器啟動時註冊
register_custom_type(
    receive_type="email",      # 接收事件中的 detail_type
    send_type="email",         # 發送時的目標類型
    id_field="email_id",       # 對應的 ID 欄位名
    platform="email"           # 平台標識
)
```

**自訂類型要求**：
- 必須在適配器 `start()` 時註冊，在 `shutdown()` 時註銷
- `receive_type` 不應與標準類型重名
- `id_field` 應遵循 `{目標}_id` 的命名模式

> 完整的會話類型定義和映射關係參見 [會話類型標準](session-types.md)。

## 8. 模組開發者指南

### 8.1 訪問擴展字段

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # 訪問標準字段
    text = event.get_text()
    user_id = event.get_user_id()

    # 訪問平台擴展字段 - 方法1：直接 get
    yunhu_command = event.get("yunhu_command")

    # 訪問平台擴展字段 - 方法2：點式訪問（Event 包裝類）
    # event.yunhu_command

    # 訪問原始數據
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # 判斷平台
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 處理擴展消息段

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 最佳實踐

1. **優先使用標準字段**：不要假設擴展字段一定存在
2. **平台判斷**：通過 `event.get_platform()` 判斷平台，而非通過擴展字段是否存在來推斷
3. **優雅降級**：無法處理擴展消息段時，使用 `alt_message` 作為兜底
4. **不要硬編碼前綴**：使用 `platform` 變量動態拼接

```python
# ✅ 推薦
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 不推薦
raw_data = event.get("yunhu_raw")
```

### 8.4 請求事件處理

模組開發者可以透過 `event.approve()` 和 `event.reject()` 對請求事件進行操作：

```python
from ErisPulse.Core.Event import request

# 好友請求：自動同意
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # 同意請求
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"已同意 {user_name} 的好友請求")
    else:
        print(f"同意好友請求失敗: {result.get('message')}")

# 群邀請：根據條件決定
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # 拒絕請求
    result = await event.reject(comment="暫不加入新群")
```

**透過適配器直接操作**（適用於非事件處理器場景）：

```python
from ErisPulse import adapter

# 透過 request_id 直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# 指定 Bot 賬號操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# 附帶備註
await adapter.myplatform.Request("req_abc123").accept(comment="歡迎")
```

## 9. notice / request 事件的會話類型推斷

### 9.1 問題背景

notice 事件和 request 事件的 `detail_type` 是**語義子類型**（如 `group_member_increase`、`friend_increase`），而不是會話類型（如 `group`、`private`）。

```
type        detail_type                  含義            會話類型
────        ───────────                  ────            ────────
message     group                        群聊訊息         group（detail_type 即會話類型）
message     private                      私聊訊息         private（detail_type 即會話類型）
notice      group_member_increase        群成員增加       group（需從 group_id 推斷）
notice      friend_increase              好友增加         private（需從 user_id 推斷）
request     friend                       好友請求         private（需從 user_id 推斷）
request     group                        群請求           group（detail_type 即會話類型）
```

### 9.2 推斷規則

`infer_receive_type()` 的推斷順序：

1. 如果 `detail_type` 是已知會話類型（`private`/`group`/`channel`/`guild`/`thread`/`user`），直接使用
2. 如果 `detail_type` 是自定義會話類型，直接使用
3. 否則（notice/request 的語義子類型），根據 ID 字段推斷：
   - 有 `group_id` → `"group"`
   - 有 `channel_id` → `"channel"`
   - 有 `guild_id` → `"guild"`
   - 有 `thread_id` → `"thread"`
   - 有 `user_id` → `"private"`

### 9.3 `event.reply()` 目標推斷

notice/request 事件中 `event.reply()` 的發送目標由會話類型推斷決定：

- 群通知事件（含 `group_id`）→ 回覆到**群**
- 好友通知事件（僅含 `user_id`）→ 回覆到**用戶私聊**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() 發送到群（group/group_789）
    await event.reply("歡迎入群！")

    # 如需通知管理員（私聊），顯式指定目標：
    await adapter.Send.To("user", "admin_id").Text(f"新成員 {user_id} 加入了 {group_id}")
```

### 9.4 適配器開發建議

確保 notice/request 事件中包含正確的 ID 字段：

| detail_type | 必須包含的 ID 字段 | 推斷的會話類型 |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend`（請求） | `user_id` | `private` |
| `group`（請求） | `group_id` | `group` |

## 10. 相關文件

**實作轉換器時的對照表**：
- [會話類型標準](session-types.md) - 會話類型的定義和對應關係
- [API 回應標準](api-response.md) - 適配器 API 回應格式的標準

**同一適配器的發送端**：
- [發送方法規範](send-method-spec.md) - Send 類的方法命名、參數規範及反向轉換的要求
- [API 動作標準](api-action-spec.md) - OneBot12 標準 API 動作的統一介面

**查詢各平台已知的擴展事件與訊息段**：
- [各平台特性文件](../platform-guide/README.md) - 您可以訪問此文件來了解各個平台的特性以及已知的擴展事件和訊息段等。