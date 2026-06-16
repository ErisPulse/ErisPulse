# 平台特性說明 — Webhook 通用橋接適配器

本文檔詳細說明 Webhook 适配器的雙向橋接協議、欄位映射與實現特性。

## 總覽

Webhook 适配器是一個**協議級橋接器**，不綁定任何特定平台。它透過 HTTP 收發訊息，使任何能發起 HTTP 請求的系統都能接入 ErisPulse。

```
入站方向                                出站方向
────────                                ────────
外部系統                                ErisPulse 模組
   │                                       │
   │ POST JSON                             │ Send.Text(...)
   ▼                                       ▼
┌──────────────────────────────────────────────────┐
│              WebhookAdapter                       │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ 入站路由          │   │ 出站轉發          │    │
│  │ GET  (健康檢查)   │   │ client.post()    │    │
│  │ POST (接收事件)   │   │ → outgoing_url   │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
│           │                      │               │
│           ▼                      │               │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ WebhookConverter │   │ Send 類          │    │
│  │ JSON → OneBot12  │   │ 消息段 → JSON    │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
└───────────┼──────────────────────┼───────────────┘
            ▼                      │
     adapter.emit(event)    call_api("send_message")
            │                      │
            ▼                      │
       ErisPulse 事件系統 ◄────────┘
```

## 多帳戶模型

每個帳戶是一個獨立的橋接配置，互不干擾：

| 帳戶 | bot_id | callback_path | outgoing_url | secret |
|------|--------|---------------|--------------|--------|
| `default` | `webhook_bot` | `/webhook/default` | `https://a.com/recv` | `key1` |
| `discord` | `discord_bot` | `/webhook/discord` | `https://b.com/send` | `key2` |

每個帳戶啟動時獨立註冊路由、獨立 emit connect。

## 入站協議

### 1. 健康檢查（GET）

- **路徑**：`{callback_path}`
- **方法**：`GET`
- **鑑權**：無
- **回應**：

```json
{"status": "ok", "account": "default"}
```

### 2. 接收事件（POST）

- **路徑**：`{callback_path}`
- **方法**：`POST`
- **Content-Type**：`application/json`
- **鑑權**（配置 secret 時）：Header `X-Webhook-Secret` 或 Query `?secret=`

#### 請求 Body

```json
{
  "user_id": "u123",
  "user_nickname": "使用者名稱",
  "group_id": "群組ID（僅群組會話）",
  "detail_type": "private",
  "message": [
    {"type": "text", "data": {"text": "訊息內容"}}
  ],
  "raw": {}
}
```

| 欄位 | 必填 | 說明 |
|------|------|------|
| `user_id` | 是 | 發送者 ID |
| `user_nickname` | 否 | 發送者暱稱 |
| `group_id` | 否 | 群組/頻道 ID（群組會話時提供） |
| `detail_type` | 否 | 會話類型（`private`/`group`），預設用帳戶預設值 |
| `message` | 是 | OneBot12 消息段陣列 |
| `raw` | 否 | 原始資料，原樣存入 `webhook_raw` |

#### 回應

```json
{"status": "ok"}
```

錯誤回應帶 HTTP 狀態碼：

| 狀態碼 | 含義 |
|--------|------|
| 400 | 無效 JSON / body 非物件 |
| 401 | 鑑權失敗 |
| 404 | 未知帳戶 |
| 500 | 事件分發失敗 |

### 3. 欄位映射（入站 JSON → OneBot12 事件）

| 入站 JSON | OneBot12 事件欄位 | 說明 |
|-----------|-------------------|------|
| — | `id` | 自動產生 |
| — | `time` | 當前 Unix 時間戳（秒） |
| — | `type` | 固定 `message` |
| `detail_type` | `detail_type` | 預設用帳戶預設值 |
| — | `platform` | 固定 `webhook` |
| — | `self.platform` | 固定 `webhook` |
| — | `self.user_id` | 帳戶 `bot_id` |
| `user_id` | `user_id` | 傳遞 |
| `user_nickname` | `user_nickname` | 傳遞（可選） |
| `group_id` | `group_id` | 傳遞（可選） |
| `message` | `message` | 傳遞 |
| 完整 body | `webhook_raw` | 原始請求 |
| 帳戶名 | `webhook_account` | 產生事件的帳戶名 |
| `type` 或 `message` | `webhook_raw_type` | 原始事件類型 |

## 出站協議

### 1. 發送訊息

當模組調用 `Send.To(...).Text(...)` 等方法時，適配器向 `outgoing_url` 發起 POST：

- **方法**：`POST`
- **Content-Type**：`application/json`
- **鑑權 Header**（配置 secret 時）：`X-Webhook-Secret: {secret}`

#### 請求 Body

```json
{
  "target_type": "private",
  "target_id": "target_user_id",
  "account": "default",
  "message": [
    {"type": "text", "data": {"text": "訊息內容"}}
  ],
  "timestamp": 1700000000
}
```

| 欄位 | 說明 |
|------|------|
| `target_type` | 目標類型（來自 `Send.To(type, id)`），預設用帳戶預設值 |
| `target_id` | 目標 ID（來自 `Send.To`） |
| `account` | 發送帳戶名 |
| `message` | OneBot12 消息段陣列 |
| `timestamp` | 發送時間戳（秒） |

### 2. 回應標準化

適配器把出站目標返回的回應標準化為 ErisPulse 標準回應格式：

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "...", ...},
  "message_id": "...",
  "message": "",
  "webhook_raw": {}
}
```

從目標回應 JSON 的 `message_id` 欄位提取訊息 ID。若目標未返回 `message_id`，則為空字串。

請求失敗時返回錯誤回應（`status: "failed"`, `retcode: 33001`）。

## Send 方法

| 方法 | 說明 |
|------|------|
| `Text(text)` | 發送文字，封裝為 `[{"type":"text","data":{"text":text}}]` |
| `Image(file)` | 發送圖片，封裝為 `[{"type":"image","data":{"file":file}}]` |
| `Raw_ob12(message)` | 發送 OneBot12 原始消息段 |
| `Json(data)` | 原始 JSON 傳遞，封裝為 `[{"type":"json","data":{"raw":data}}]` |

`At` / `AtAll` / `Reply` 修飾器由框架基類提供，透過 `_apply_modifiers` 合併到消息段。

## 事件擴展方法（WebhookEventMixin）

| 方法 | 說明 |
|------|------|
| `get_raw_data()` | 取得原始請求 body（`webhook_raw`） |
| `get_detail_type()` | 取得會話類型 |
| `get_webhook_account()` | 取得產生該事件的帳戶名 |

## 特性矩陣

| 特性 | 支援情況 |
|------|----------|
| 多帳戶 | ✅ 每個帳戶獨立橋接 |
| 入站鑑權 | ✅ Header / Query 雙模式 |
| 健康檢查 | ✅ GET 返回狀態 |
| 出站鑑權 | ✅ Header 攜帶 secret |
| OneBot12 標準事件 | ✅ 完整標準欄位 |
| Meta 事件 | ✅ connect / disconnect |
| 路由發現 | ✅ 注冊到 `webhook` 命名空間 |
| WebSocket | ❌ 僅 HTTP |
| 媒體上傳 | ❌ 透過 URL 傳遞，不代傳二進位 |

## 注意事項

1. **單向出站**：若 `outgoing_url` 留空，該帳戶僅作入站接收，發送操作會返回錯誤
2. **密鑰安全**：`secret` 在配置中以密文儲存（metadata secret），傳輸建議使用 HTTPS
3. **路徑唯一**：多個帳戶的 `callback_path` 必須互不相同，避免路由衝突
4. **冪等性**：適配器不保證入站事件去重，外部系統應自行處理重試
5. **超時**：出站請求使用 ErisPulse 內建 `client`，繼承全域超時配置