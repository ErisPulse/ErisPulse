# Webhook 通用橋接適配器平台特性文件

WebhookAdapter 是一個協議級雙向橋接適配器，不綁定任何特定平台：入站將外部系統 POST 的 JSON 轉為 OneBot12 事件，出站將模組 Send 轉為 POST 到外部系統。

---

## 文件資訊

- 對應模組版本: 4.3.2
- 維護者: ErisPulse
- 最後更新: 2026-11-10

## 基本資訊

- 平台簡介：任意能發起 HTTP 請求的系統均可透過本適配器接入 ErisPulse
- 適配器名稱：WebhookAdapter
- 平台標識：`webhook`
- 多帳戶支援：每個帳戶是獨立的橋接配置（bot_id / callback_path / outgoing_url / secret）
- 框架要求：軟依賴 `ErisPulse>=2.7.1`（執行時偵測提示，不強制）

## 已對接平台能力

- **入站**：外部系統 POST 到 callback_path → 轉為 OneBot12 事件（json/text 段透傳）
- **出站**：模組 Send → POST 到 outgoing_url（雙橋接）
- **API**：橋接身份資訊與執行狀態（最小集）

## v5 範式更新（4.2.0）

- **Api DSL 最小集**：get_self_info/get_status/get_version/get_supported_actions
- **框架軟依賴**：執行時偵測 ErisPulse>=2.7.1 並提示；啟動輸出版本日誌
- 匯入路徑更新至 Core.Bases

## 標準化對齊（4.3.2）

回應結構與錯誤碼遵循 [API 回應規範](../standards/api-response.md)。

### 事件欄位

- **訊息事件補齊頂層 `message_id`**：優先透傳入站 body 的 `message_id`，缺失時以 uuid 兜底（避免下游按 message_id 去重/回覆時拿到空值）
- **事件注入 `self.account_id`**（帳戶名）：多帳戶場景下 `event.reply()` 自動路由到受理該事件的帳戶
- **`alt_message` 空字串兜底**：入站未提供時補空字串，保證標準欄位完整
- **JSON 段名改為 `webhook_json`**：未加平台前綴的裸 `json` 段統一歸一為 `webhook_json`（遵循平台擴展段命名規則）
- Converter 復用框架 `BaseConverter`（公共欄位由 `build_base_event` 統一建構）
- `get_self_info` 補齊標準欄位：`user_id`（帳戶 bot_id）/ `user_name` / `user_displayname`（`webhook:{帳戶名}`）

### 錯誤碼規範

| retcode | 含義 | 說明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | 網路錯誤 | 出站 POST 目標失敗（連線/逾時等） |
| 10003 | 參數錯誤 | 出站 URL 未配置、參數缺失等 |

### 帳戶與多帳戶

- `call_api` 支援雙相容帳戶欄位：`account_id`（標準名）/ `_account_id`（舊名），框架 ApiDSL（`Api.Using(...)`）自動適配
- `Send` 讀取 `send_context`（事件帳戶兜底）：從事件上下文呼叫 `Send` 時預設回落到來源帳戶

## 總覽

Webhook 適配器是一個**協議級橋接器**，不綁定任何特定平台。它透過 HTTP 收發訊息，使任何能發起 HTTP 請求的系統都能接入 ErisPulse。

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
│  │ JSON → OneBot12  │   │ 訊息段 → JSON    │    │
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

### 帳戶配置欄位

| 欄位 | 必填 | 說明 |
|------|------|------|
| `bot_id` | 否 | Bot 身份 ID（由此橋接表示） |
| `callback_path` | 否 | 入站回呼路徑（支援 `{account}` 佔位符） |
| `outgoing_url` | 否 | 出站目標 URL（模組發送訊息時 POST 到此地址） |
| `secret` | 否 | 鑑權金鑰（留空則停用驗證；配置面板中以密文儲存） |

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
  "message_id": "可選，透傳為事件 message_id（缺失時自動生成 uuid）",
  "alt_message": "可選，純文字備援",
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
| `detail_type` | 否 | 會話類型（`private`/`group`），未指定時使用帳戶預設 |
| `message_id` | 否 | 訊息 ID，透傳為事件頂層 `message_id`（缺失時 uuid 兜底） |
| `alt_message` | 否 | 純文字備援，缺失時空字串兜底 |
| `message` | 是 | OneBot12 訊息段陣列 |
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
| — | `id` | 自動生成 |
| — | `time` | 目前 Unix 時間戳（秒） |
| — | `type` | 固定 `message` |
| `detail_type` | `detail_type` | 未指定時使用帳戶預設值 |
| — | `platform` | 固定 `webhook` |
| — | `self.platform` | 固定 `webhook` |
| — | `self.user_id` | 帳戶 `bot_id` |
| — | `self.account_id` | 帳戶名（4.3.2 注入，多帳戶路由） |
| `user_id` | `user_id` | 透傳 |
| `user_nickname` | `user_nickname` | 透傳（可選） |
| `group_id` | `group_id` | 透傳（可選） |
| `message_id` | `message_id` | 透傳，缺失時 uuid 兜底（4.3.2） |
| `alt_message` | `alt_message` | 透傳，缺失時空字串兜底（4.3.2） |
| `message` | `message` | 透傳 |
| 完整 body | `webhook_raw` | 原始請求 |
| 帳戶名 | `webhook_account` | 產生事件的帳戶名 |
| `type` 或 `message` | `webhook_raw_type` | 原始事件類型 |

> 裸 `json` 段（`{"type": "json", ...}`）在入站/出站兩側均歸一為 `webhook_json` 段。

## 出站協議

### 1. 發送訊息

當模組呼叫 `Send.To(...).Text(...)` 等方法時，適配器向 `outgoing_url` 發起 POST：

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
| `target_type` | 目標類型（來自 `Send.To(type, id)`），未指定時使用帳戶預設 |
| `target_id` | 目標 ID（來自 `Send.To`） |
| `account` | 發送帳戶名 |
| `message` | OneBot12 訊息段陣列 |
| `timestamp` | 發送時間戳（秒） |

### 2. 回應標準化

適配器把出站目標回傳的回應標準化為 ErisPulse 標準回應格式：

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

從目標回應 JSON 的 `message_id` 欄位擷取訊息 ID。若目標未回傳 `message_id`，則為空字串。

請求失敗時回傳錯誤回應（`status: "failed"`, `retcode: 33001`）。

## Send 方法

| 方法 | 說明 |
|------|------|
| `Text(text)` | 發送文字，封裝為 `[{"type":"text","data":{"text":text}}]` |
| `Image(file)` | 發送圖片，封裝為 `[{"type":"image","data":{"file":file}}]` |
| `Raw_ob12(message)` | 發送 OneBot12 原始訊息段 |
| `Json(data)` | 原始 JSON 透傳，封裝為 `[{"type":"webhook_json","data":{"raw":data}}]` |

`At` / `AtAll` / `Reply` 修飾器由框架基底類別提供，透過 `_apply_modifiers` 合併到訊息段。

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
| 健康檢查 | ✅ GET 回傳狀態 |
| 出站鑑權 | ✅ Header 攜帶 secret |
| OneBot12 標準事件 | ✅ 完整標準欄位 |
| Meta 事件 | ✅ connect / disconnect |
| 路由發現 | ✅ 註冊到 `webhook` 命名空間 |
| WebSocket | ❌ 僅 HTTP |
| 媒體上傳 | ❌ 透過 URL 透傳，不代傳二進位 |

## 注意事項

1. **單向出站**：若 `outgoing_url` 留空，該帳戶僅作入站接收，發送操作會回傳錯誤（`retcode: 10003`）
2. **金鑰安全**：`secret` 在配置中以密文儲存（metadata secret），傳輸建議使用 HTTPS
3. **路徑唯一**：多個帳戶的 `callback_path` 必須互不相同，避免路由衝突
4. **冪等性**：適配器不保證入站事件去重，外部系統應自行處理重試
5. **逾時**：出站請求使用 ErisPulse 內建 `client`，繼承全域逾時配置