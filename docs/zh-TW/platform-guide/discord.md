# Discord 平台特性文件

DiscordAdapter 是一個基於 Discord Gateway (WebSocket) 和 REST API v10 協議構建的適配器，整合了 Discord Bot 的核心功能，提供統一的事件處理和訊息操作介面。

---

## 文件資訊

- 對應模組版本: 4.0.0
- 維護者: ErisPulse
- Discord API 版本: v10

## 基本資訊

- 平台簡介：Discord 是一款廣受歡迎的社群通訊平台，支援伺服器、頻道、私信等多種會話形式，提供完善的 Bot 開發介面
- 適配器名稱：DiscordAdapter
- 多帳號支援：支援同時配置多個 Discord 機器人
- 連線方式：Gateway WebSocket（接收事件）+ REST API（發送訊息/呼叫介面）
- 認證方式：Bot Token（HTTP 標頭 `Authorization: Bot {token}`，Gateway IDENTIFY payload 携带 token）
- 鏈式修飾支援：支援 `.Reply()`、`.At()`、`.AtAll()` 等鏈式修飾方法
- OneBot12 相容：支援發送 OneBot12 格式訊息

## 設定說明

DiscordAdapter 支援多帳號配置，每個帳號對應一個獨立的 Discord Bot。

```toml
# config.toml

# 帳戶1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token（必填）
intents = 33281                 # Gateway Intents（選擇性，預設 33281）
enabled = true                  # 是否啟用（選擇性，預設 true）

# 帳戶2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**配置項目說明（每個帳號）：**

- `token`：Discord Bot Token（必填），從 [Discord Developer Portal](https://discord.com/developers/applications) 取得
- `intents`：Gateway Intents 位元遮罩（選擇性，預設 `33281`），決定 Bot 訂閱的事件類型
- `bot_id`：Bot 的使用者 ID（選擇性，執行時從 READY 事件自動取得，無需手動填寫）
- `enabled`：是否啟用該帳號（選擇性，預設 `true`）

### Gateway Intents

Intents 使用位元遮罩，計算方式為各 Intent 值按位或（`|`）：

| Intent | 位 | 值 | 說明 | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | 伺服器建立/刪除/更新、頻道、角色變更 | 否 |
| GUILD_MEMBERS | `1 << 1` | 2 | 成員加入/離開/更新 | 是 |
| GUILD_MESSAGES | `1 << 9` | 512 | 伺服器訊息收發 | 否 |
| MESSAGE_CONTENT | `1 << 15` | 32768 | 訊息內容（無此 Intent 時 content 為空） | 是 |

預設值 `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`。

> **注意**：Privileged Intents 需在 Discord Developer Portal → Bot → Privileged Gateway Intents 中開啟。如果 Bot 在超過 100 個伺服器中，還需透過 Discord 審核。

**API 環境：**
- Discord REST API 基礎位址：`https://discord.com/api/v10`
- Gateway WebSocket 位址：透過 `GET /gateway/bot` 動態取得，通常為 `wss://gateway.discord.gg/?v=10&encoding=json`

## 支援的訊息發送類型

所有發送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

支援的發送類型包括：
- `.Text(text: str)`：發送純文字訊息。
- `.Embed(embed: dict | list)`：發送 Embed 嵌入訊息，支援單個或多個 Embed。
- `.Image(file: bytes | str, filename: str = "image.png")`：發送圖片，支援二進位資料或 URL。
- `.File(file: bytes | str, filename: str = None)`：發送檔案，支援二進位資料或 URL。
- `.Reply(content: str, message_id: str)`：回覆指定訊息（便捷終端方法）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式訊息。
- `.Raw_json(json_str: str)`：發送任意 Discord API 請求 JSON。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支援鏈式呼叫，必須在最終發送方法前呼叫：

- `.Reply(message_id: str)`：回覆（引用）指定訊息，設定 `message_reference`。
- `.At(user_id: str)`：@指定使用者，轉換為 `<@user_id>`，可多次呼叫。
- `.AtAll()`：@所有人，轉換為 `@everyone`。

### 鏈式呼叫範例

```python
# 基礎發送
await discord.Send.To("group", channel_id).Text("Hello")

# 回覆訊息
await discord.Send.To("group", channel_id).Reply(msg_id).Text("回覆訊息")

# 便捷回覆（一步到位）
await discord.Send.To("group", channel_id).Reply("回覆內容", msg_id)

# @使用者
await discord.Send.To("group", channel_id).At("user_id").Text("你好")

# @多個使用者
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("多使用者@")

# @全體
await discord.Send.To("group", channel_id).AtAll().Text("公告")

# 組合使用
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合訊息")

# Embed 嵌入訊息
embed = {
    "title": "通知",
    "description": "這是一條嵌入訊息",
    "color": 5814783,
    "fields": [{"name": "欄位", "value": "值", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# 發送圖片
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### 私信發送

私信發送時，適配器會自動建立 DM 頻道：

```python
# 發送私信
await discord.Send.To("user", user_id).Text("私信內容")
await discord.Send.To("user", user_id).Embed(embed)
```

### 訊息操作

```python
# 撤回訊息
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12 格式
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## 發送方法返回值

所有發送方法均返回一個 Task 物件，可以直接 await 取得發送結果。返回結果遵循 ErisPulse 適配器標準化返回規範：

```python
{
    "status": "ok",           // 執行狀態: "ok" 或 "failed"
    "retcode": 0,             // 返回碼（0 為成功）
    "data": {...},            // Discord API 原始回應
    "message_id": "xxx",      // 訊息ID（發送訊息時）
    "message": "",            // 錯誤資訊
    "discord_raw": {...}      // 原始回應資料
}
```

### 錯誤碼說明

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 33001 | 網路錯誤（連線失敗、逾時等） |
| 34000 | Discord API 返回錯誤（權限不足、參數錯誤等） |

## 特有事件類型

需要 `platform == "discord"` 檢測再使用本平台特性。

### 核心差異點

1. **伺服器/頻道系統**：Discord 使用伺服器（Guild）和頻道（Channel）兩層結構，頻道是訊息的基本發送目標
2. **Gateway 事件**：所有事件透過 WebSocket Gateway 接收，使用 Opcode + Dispatch 機制
3. **Intents 訂閱**：透過位元遮罩訂閱事件類型，`MESSAGE_CONTENT` 需 Privileged 權限
4. **訊息段類型**：支援文字、圖片、檔案、影片、音訊、Embed、Sticker 等訊息段
5. **Mention 格式**：Discord 使用 `<@user_id>` 格式表示使用者提及

### 擴充欄位

所有特有欄位均以 `discord_` 前綴識別：
- `discord_raw`：原始 Discord 事件資料
- `discord_raw_type`：原始事件類型名（如 `MESSAGE_CREATE`）
- `discord_guild_id`：伺服器 ID
- `discord_channel_id`：頻道 ID

### detail_type 映射

| Discord 場景 | detail_type | 說明 |
|---|---|---|
| 頻道訊息 | `channel` | ErisPulse 擴充類型 |
| 私信（DM） | `private` | OneBot12 標準類型 |

### 事件類型映射

| Discord 事件 | OneBot12 type | detail_type | 說明 |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | 訊息建立 |
| MESSAGE_UPDATE | message | channel/private | 訊息編輯 |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | 訊息刪除 |
| GUILD_MEMBER_ADD | notice | group_member_increase | 成員加入 |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | 成員離開 |
| GUILD_MEMBER_UPDATE | notice | group_member_update | 成員資訊更新 |
| GUILD_ROLE_CREATE | notice | group_role_create | 角色建立 |
| GUILD_ROLE_DELETE | notice | group_role_delete | 角色刪除 |
| CHANNEL_CREATE | notice | channel_create | 頻道建立 |
| CHANNEL_DELETE | notice | channel_delete | 頻道刪除 |
| INTERACTION_CREATE | request | interaction | 交互（按鈕、命令等） |

### 特殊欄位範例

```python
# 頻道文字訊息
{
  "type": "message",
  "detail_type": "channel",
  "user_id": "發送者ID",
  "user_nickname": "使用者名",
  "group_id": "頻道ID",
  "message_id": "訊息ID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_guild_id": "伺服器ID",
  "discord_channel_id": "頻道ID",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# 私信訊息
{
  "type": "message",
  "detail_type": "private",
  "user_id": "發送者ID",
  "user_nickname": "使用者名",
  "message_id": "訊息ID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_channel_id": "DM頻道ID",
  "message": [
    {"type": "text", "data": {"text": "私信內容"}}
  ],
  "alt_message": "私信內容"
}

# 带 Embed 的訊息
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "discord_embed", "data": {"embed": {...}}}
  ],
  "alt_message": "[嵌入訊息]"
}

# 帶附件的訊息
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "看這張圖"}},
    {"type": "image", "data": {"file": "圖片URL", "url": "圖片URL", "file_name": "image.png"}}
  ],
  "alt_message": "看這張圖[圖片]"
}
```

### 訊息段類型

Discord 訊息內容根據 `content`、`attachments`、`embeds` 欄位自動轉換為對應訊息段：

| 來源 | 轉換類型 | 說明 |
|---|---|---|
| content 文字 | `text` | 純文字內容 |
| content `<@id>` | `mention` | 使用者提及 |
| content `<@&id>` | `discord_role_mention` | 角色提及 |
| content `<#id>` | `discord_channel_mention` | 頻道提及 |
| attachments (image/*) | `image` | 圖片附件 |
| attachments (video/*) | `video` | 影片附件 |
| attachments (audio/*) | `audio` | 音訊附件 |
| attachments (其他) | `file` | 檔案附件 |
| embeds | `discord_embed` | 嵌入訊息 |
| sticker_items | `discord_sticker` | 貼紙 |

### discord_embed 訊息段

```json
{
  "type": "discord_embed",
  "data": {
    "embed": {
      "title": "標題",
      "description": "描述",
      "color": 12345,
      "fields": [...],
      "image": {"url": "..."},
      "thumbnail": {"url": "..."},
      "footer": {"text": "..."}
    }
  }
}
```

## Gateway 連線

### 連線流程

1. 呼叫 `GET /gateway/bot` 取得 WebSocket 網關 URL
2. 連線到 `wss://gateway.discord.gg/?v=10&encoding=json`
3. 收到 opcode 10 HELLO：包含 `heartbeat_interval`
4. 發送 opcode 2 IDENTIFY：攜帶 token、intents、properties
5. 開始心跳循環：按 `heartbeat_interval` 定時發送 opcode 1 Heartbeat
6. 收到 opcode 0 Dispatch：事件分發（`t`=事件名, `s`=序號, `d`=資料）
7. 收到 opcode 11 Heartbeat ACK：心跳確認

### Opcode 說明

| Opcode | 名稱 | 方向 | 說明 |
|--------|------|------|------|
| 0 | Dispatch | 接收 | 事件分發（含 `t`、`s`、`d` 欄位） |
| 1 | Heartbeat | 發送/接收 | 心跳（攜帶最後 seq） |
| 2 | Identify | 發送 | 身份認證 |
| 6 | Resume | 發送 | 恢復會話 |
| 7 | Reconnect | 接收 | 伺服器要求重連 |
| 9 | Invalid Session | 接收 | 無效會話 |
| 10 | Hello | 接收 | 連線握手指 |（含 heartbeat_interval） |
| 11 | Heartbeat ACK | 接收 | 心跳確認 |

### 斷線重連與 RESUME

- 連線中斷後，適配器自動重試連線
- 如果之前有 `session_id`，優先嘗試 RESUME（opcode 6）恢復會話
- RESUME 攜帶 `token`、`session_id`、最後 `seq`，恢復後補發遺漏事件
- 收到 opcode 7（Reconnect）時，保持會話狀態並重連
- 收到 opcode 9（Invalid Session）且 `d=false` 時，清除會話並重新 IDENTIFY

### 心跳機制

- 收到 HELLO 後，等待 `heartbeat_interval * random()` 毫秒發送首次心跳
- 此後每隔 `heartbeat_interval` 毫秒發送一次心跳
- 心跳攜帶最後的 `seq` 值（opcode 1，`d: seq`）
- 若發送心跳後 `heartbeat_interval` 內未收到 ACK（opcode 11），視為連線異常並重連

## 使用範例

### 處理頻道訊息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

discord = sdk.adapter.get("discord")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "discord":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await discord.Send.To("group", channel_id).Text("Hello!")
```

### 處理私信

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "discord":
        return
    if not event.is_dm():
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await discord.Send.To("user", user_id).Text(f"你說了: {text}")
```

### 發送 Embed 訊息

```python
embed = {
    "title": "伺服器公告",
    "description": "歡迎使用 ErisPulse Discord 適配器",
    "color": 3447003,
    "fields": [
        {"name": "版本", "value": "4.0.0", "inline": True},
        {"name": "框架", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Powered by ErisPulse"},
    "timestamp": "2025-01-01T00:00:00.000Z",
}
await discord.Send.To("group", channel_id).Embed(embed)
```

### 使用 Discord 特有方法

```python
@message.on_message()
async def handle(event):
    if event.get("platform") != "discord":
        return

    channel_id = event.get_channel_id()
    guild_id = event.get_guild_id()
    is_dm = event.is_dm()
    embeds = event.get_embeds()
    attachments = event.get_attachments()

    if embeds:
        await discord.Send.To("group", channel_id).Text(
            f"收到 {len(embeds)} 個 Embed"
        )
```

### 處理交互事件

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return

    interaction = event.get_interaction_data()
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("按鈕已點擊！")