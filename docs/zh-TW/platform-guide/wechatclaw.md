# 微信 ClawBot（WechatClaw）適配器 - 平台特性文件

## 基本資訊
- 模組名稱: `ErisPulse-WechatClaw`
- 平台標識: `wechatclaw`
- 模組版本: 0.1.0
- 維護者: wsu2059q
- 最後更新: 2026-11-17
- 依賴: `qrcode`、`pycryptodome`

## 平台定位

基於**騰訊官方 iLink Bot API**（微信 ClawBot 机器人通道）的微信個人號接入適配器：掃碼綁定、令牌自動寫回、長輪詢接收。官方合規渠道，非逆向協議；能力範圍以微信官方開放為準。

## 接入與綁定

- `token` 配置留空時，適配器啟動即列印登入二維碼（終端 ASCII 圖案 + 鏈接兜底），手機微信掃碼確認後完成綁定
- **Dashboard 面板掃碼**（推薦）：適配器向「新增帳戶嚮導」註冊「掃碼登入微信」擴展區，面板內直接掃碼綁定（對齊 bilibili 適配器的面板掃碼約定）
- 綁定成功後 `token` / `bot_user_id` / `base_url` 經框架無損 TOML 引擎自動寫回 `config.toml`（保留使用者註釋），重啟免重掃
- 令牌失效（長輪詢返回 401/403）時日誌明示「清除 token 重新掃碼」

### 掃碼登入端點（第三方前端可對接）

適配器隨啟動註冊 `POST /wechatclaw/qr/start` 與 `POST /wechatclaw/qr/poll`：

- `qr/start`：獲取二維碼，回傳 `{success, task_id, poll_token, qr_img}`（`qr_img` 為 SVG data URI）
- `qr/poll`：請求攜帶 `task_id` + `poll_token`（防未授權輪詢，缺失回傳 403），回傳 `{success, status}`，status ∈ `pending` / `scan` / `done` / `timeout`
- `done` 時憑證已自動寫入配置，回應附帶 `account`

## 標準化對齊

事件與響應遵循 [事件轉換標準](../standards/event-conversion.md) 與 [API 響應規範](../standards/api-response.md)。

- 消息事件頂層攜帶標準 `message_id`（取官方 message_id，缺失回退 client_id/seq）
- 事件 `id` 帶帳戶維度（`{bot_id}:{message_id}`），冪等去重與跨帳戶隔離由框架處理
- 發送返回標準響應：`status` / `retcode` / `data` / `message_id` / `message` + 頂層 `wechatclaw_raw`

### 消息事件

- 事件類型：`message` / `private`（官方通道為個人號私信，無群聊能力）
- 入站消息段：`text`、`image`、`voice`、`file`、`video`
- 媒體段不落地文件：攜帶 `wechatclaw_cdn`（CDN 描述 + 密鑰），經 `call_api("download_media")` 按需下載解密

### 上下文令牌與回覆

協議要求回覆攜帶 `context_token`（隨收到的消息下發）。適配器按用戶緩存最近上下文：

- 事件鏈內回覆（`event.reply()` / `Send.To("user", ...)`）自動攜帶該用戶上下文
- **主動私信**受協議限制：無會話上下文的用戶可能被平台拒絕（響應 errcode 反饋）

## 支援的消息發送類型

| 方法 | 說明 | 官方 API |
|------|------|---------|
| `Text(text)` | 發送文字（Markdown 自動降級為純文字） | `sendmessage` |
| `Image(file)` | 發送圖片（URL/路徑/base64:///bytes，自動加密上傳） | `getuploadurl` + CDN |
| `Video(file)` | 發送影片 | 同上 |
| `File(file)` | 發送檔案 | 同上 |
| `Voice(file)` | 發送語音（僅支援 SILK 編碼；其餘音訊會降級為檔案訊息） | 同上 |
| `Reply(message_id)` | 引用回覆（引用目標為該對話最近收到的一條訊息） | `sendmessage` + ref_msg |

> `mention` / `at` 段在個人號私信中無語義，發送時會靜默忽略。

## 扩展 API（call_api）

| 端點 | 參數 | 說明 |
|------|------|------|
| `download_media` | `media`（入站媒體段的 `wechatclaw_cdn`） | 下載並解密，`data.path` 返回本地路徑 |
| `send_typing` | `user_id`，可選 `status`（1=輸入中 2=取消） | 「正在輸入」狀態（需有效對話上下文） |

## 平台限制

- 僅私信（官方通道不開放群聊）
- 部分視頻訊息可能缺少解密密鑰（官方通道已知問題），此類媒體無法下載
- 語音要求 SILK 編碼（encode_type=6，24kHz）

## 配置參考

| 配置項 | 預設值 | 說明 |
|---|---|---|
| `token` | "" | 留空即掃碼登錄，綁定後自動寫回 |
| `bot_user_id` | "" | 官方賬號 ID，綁定後自動寫回 |
| `base_url` | 官方預設 | API 基址，綁定後可能自動更新 |
| `login_timeout` | 300 | 掃碼等待時長（秒） |
| `poll_interval` | 1.0 | 長輪詢批次間隔（秒，服務端單次掛起約 35 秒） |