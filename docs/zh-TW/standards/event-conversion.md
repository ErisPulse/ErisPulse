# 適配器標準化轉換規範

## 1. 核心原則
1. 嚴格相容：所有標準欄位必須完全遵循 OneBot12 規範
2. 明確擴展：平台特有的功能必須添加 {platform}_ 前綴（例如 yunhu_form）
3. 數據完整：原始事件數據必須保留在 {platform}_raw 欄位中，原始事件類型必須保留在 {platform}_raw_type 欄位中
4. 時間統一：所有時間戳必須轉換為 10 位 Unix 時間戳（秒級）
5. 平台統一：platform 項命名必須與你在 ErisPulse 中註冊的名稱/別稱一致

## 2. 標準字段要求

### 2.1 必須字段
| 字段 | 類型 | 說明 |
|------|------|------|
| id | string | 事件唯一標識符 |
| time | integer | Unix時間戳（秒級） |
| type | string | 事件類型 |
| detail_type | string | 事件詳細類型（詳見[會話類型標準](session-types.md)） |
| platform | string | 平台名稱 |
| self | object | 机器人自身資訊 |
| self.platform | string | 平台名稱 |
| self.user_id | string | 机器人用戶ID |

**detail_type 規範**：
- 必須使用 ErisPulse 標準會話類型（詳見 [會話類型標準](session-types.md)）
- 支援的類型：`private`, `group`, `user`, `channel`, `guild`, `thread`
- 适配器負責將平台原生類型映射到標準類型

### 2.2 消息事件字段
| 字段 | 類型 | 說明 |
|------|------|------|
| message | array | 消息段陣列 |
| alt_message | string | 消息段備用文字 |
| user_id | string | 用戶ID |
| user_nickname | string | 用戶暱稱（可選） |

### 2.3 通知事件字段
| 字段 | 類型 | 說明 |
|------|------|------|
| user_id | string | 用戶ID |
| user_nickname | string | 用戶暱稱（可選） |
| operator_id | string | 操作者ID（可選） |

### 2.4 請求事件字段
| 字段 | 類型 | 說明 |
|------|------|------|
| user_id | string | 用戶ID |
| user_nickname | string | 用戶暱稱（可選） |
| comment | string | 請求附言（可選） |
| request_id | string | 請求標識符（**強烈推薦**，用於同意/拒絕請求操作） |

**`request_id` 字段說明**：
- `request_id` 是請求事件的唯一操作標識符，用於透過 `HandleRequest` DSL 執行同意/拒絕操作
- 适配器在轉換請求事件時，應將平台原生的請求標識映射到此字段
- 如果平台本身沒有請求ID，适配器應產生一個唯一標識（例如基於時間戳+用戶ID的雜湊）
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

## 4. 消息段標準

### 4.1 標準消息段

標準消息段**不需要**平台前綴。

| 類型 | 說明 | data 字段 |
|------|------|----------|
| `text` | 純文本 | `text: str` |
| `image` | 圖片 | `file: str/bytes`, `url: str` |
| `audio` | 音頻 | `file: str/bytes`, `url: str` |
| `video` | 視頻 | `file: str/bytes`, `url: str` |
| `file` | 文件 | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | @用戶 | `user_id: str`, `user_name: str` |
| `reply` | 回覆 | `message_id: str` |
| `face` | 表情 | `id: str` |
| `location` | 位置 | `latitude: float`, `longitude: float` |
| `keyboard` | 按鈕/內聯鍵盤 | `rows: list[list[button]]`（見 4.1.1） |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard 按鈕/內聯鍵盤段（跨平台通用）

按鈕/內聯鍵盤在多個平台（Telegram / 雲湖 / QQBot / Kook / Discord 等）均有對應能力，
屬於**跨平台通用概念**，因此作為標準消息段（無平台前綴）。適配器應將標準段轉換為
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

**字段說明：**

| 字段 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `rows` | 二維數組 | 是 | 每個子數組為一行按鈕 |
| `rows[][].label` | str | 是 | 按鈕顯示文本 |
| `rows[][].type` | str | 是 | `callback`（點擊回傳數據）/ `link`（跳轉URL） |
| `rows[][].data` | str | 是 | 回調數據（type=callback）或跳轉地址（type=link） |
| `rows[][].*` | Any | 否 | 平台特有可選字段（如 `web_app`、`menus`），適配器按能力映射或忽略 |

**適配器轉換參考**（完整映射與互動回調事件標準見 [跨平台互動組件標準](standardization-guide.md)）：

| 平台 | 標準段 → 平台原生 |
|------|------------------|
| Telegram | `inline_keyboard`：`[{text, callback_data \| url}]` |
| 雲湖 | `buttons`：`[{label, action_type: 2=回調 \| 1=跳轉, ...}]` |
| QQBot | `keyboard.content.rows`：`[{label, type: 2=回調 \| 0=跳轉, data}]`（需 markdown 類型消息） |
| Kook | 卡片 action-group 模塊 |
| Discord | components：`action_row` + `buttons`（custom_id/url） |

### 4.2 平台擴展消息段

平台特有的消息段需要添加平台前綴：

```json
// 雲湖 - 表單
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "報名表"}}

// Telegram - 貼紙
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**擴展消息段要求**：
1. **data 內部字段不加前綴**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` 而非 `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **提供降級方案**：模組可能不識別擴展消息段，適配器應在 `alt_message` 中提供文本替代
3. **文件完整**：每個擴展消息段必須在適配器文件中說明 `type`、`data` 結構和使用場景

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

## 6. 擴展命名規範

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
- `platform` 必須與適配器註冊時的平台名完全一致（大小寫敏感）
- `field_name` 使用 `snake_case` 命名
- 禁止使用雙下劃線 `__` 開頭（Python 保留）
- 禁止與標準欄位同名（如 `type`、`time`、`message` 等）

### 6.2 消息段類型命名

**規則**：`{platform}_{segment_type}`

標準消息段類型（`text`、`image`、`audio`、`video`、`mention`、`reply` 等）**不得**添加平台前綴。只有平台特有的消息段類型才需要添加前綴。

### 6.3 原始數據欄位命名

以下欄位名是**保留欄位**，所有適配器必須遵循：

| 保留欄位 | 類型 | 說明 |
|---------|------|------|
| `{platform}_raw` | `any` | 平台原始事件數據的完整副本 |
| `{platform}_raw_type` | `string` | 平台原始事件類型標識 |

**要求**：
- `{platform}_raw` 必須是原始數據的深拷貝，而非引用
- `{platform}_raw_type` 必須是字串，即使平台使用數字類型也要轉換為字串
- 這兩個欄位在所有事件中**必須存在**（無法獲取時為 `null` 和空字串 `""`）

### 6.4 平台特有欄位示例

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

### 6.5 嵌套擴展欄位

擴展欄位可以是簡單值，也可以是嵌套物件：

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

**嵌套欄位要求**：
- 頂層鍵必須帶平台前綴
- 嵌套內部欄位**不添加**平台前綴
- 嵌套深度建議不超過 3 層

### 6.6 `self` 欄位擴展

`self` 物件的標準必選欄位（`platform`、`user_id`）見 §2.1，以下是 ErisPulse 擴展的可選欄位：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `self.user_name` | `string` | 機器人暱稱 |
| `self.avatar` | `string` | 機器人頭像 URL |
| `self.account_id` | `string` | 多帳戶模式下的帳戶標識 |

> **Bot 狀態追蹤**：適配器通過發送 `type: "meta"` 事件告知框架 Bot 的連接狀態。支援的 `detail_type`：`connect`（上線）、`heartbeat`（心跳）、`disconnect`（離線）。系統自動從中提取 `self` 欄位的 Bot 元資訊進行狀態追蹤。此外，普通事件中的 `self` 欄位也會自動發現 Bot。詳見 [適配器系統 API - Bot 狀態管理](../api-reference/adapter-system.md)。

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

- [各平台特性文件](../platform-guide/README.md) - 您可以訪問此文件以了解各平台特性以及已知的擴展事件和消息段等。
- [會話類型標準](session-types.md) - 會話類型定義和映射關係
- [發送方法規範](send-method-spec.md) - Send 類的方法命名、參數規範及反向轉換要求
- [API 回應標準](api-response.md) - 適配器 API 回應格式標準
- [API 動作標準](api-action-spec.md) - OneBot12 標準 API 動作的統一介面