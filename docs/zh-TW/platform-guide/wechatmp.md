# 微信公眾號（WechatMp）適配器 - 平台特性文檔

## 基本信息資訊
- 模組名稱: `ErisPulse-WechatMpAdapter`
- 平台標識: `mp`（別名: `wechat_mp`）
- 模組版本: 4.0.0
- 維護者: ErisPulse
- 依賴: `cryptography`

## 支援的訊息發送類型

| 方法 | 說明 | 微信 API |
|------|------|---------|
| `Text(text)` | 發送文字 | 客服訊息 `message/custom/send` |
| `Image(file)` | 發送圖片（自動上傳獲取 media_id） | 客服訊息 + `media/upload` |
| `Voice(file)` | 發送語音（自動上傳獲取 media_id） | 客服訊息 + `media/upload` |
| `Video(file, title, description)` | 發送影片（自動上傳獲取 media_id） | 客服訊息 + `media/upload` |
| `Music(url, title, description, ...)` | 發送音樂 | 客服訊息 |
| `News(articles)` | 發送圖文訊息 | 客服訊息 |
| `Template(template_id, data, url)` | 發送模板訊息 | `message/template/send` |
| `Menu(head_content, list, tail_content)` | 發送選單訊息 | 客服訊息 `msgmenu` |
| `Raw_ob12(message)` | 發送 OneBot12 標準訊息段 | - |

### 媒體檔案說明
- 支援三種參數類型：
  - `str` URL（`http://` / `https://` 開頭）：自動下載後上傳
  - `str` 本地檔案路徑：自動讀取後上傳
  - `bytes` 二進位資料：直接上傳
  - `str` media_id：以 `media:` 前綴可直接複用已上傳的 media_id
- 上傳後獲得臨時素材 `media_id`，有效期 3 天

### 重要限制
- 客服訊息只能在使用者與公眾號互動後 **48 小時內** 主動發送
- 超過 48 小時需使用模板訊息（需使用者授權場景）

## 事件類型

### 訊息事件 (message)
所有使用者訊息均為 `detail_type: private`（公眾號 1v1 場景）。

| 微信 MsgType | 訊息段類型 | 說明 |
|-------------|-----------|------|
| `text` | `text` | 文字訊息 |
| `image` | `image` | 圖片訊息 |
| `voice` | `voice` | 語音訊息（含語音識別結果） |
| `video` | `video` | 影片訊息 |
| `shortvideo` | `video` | 小影片（標記 `mp_shortvideo`） |
| `location` | `location` | 地理位置訊息 |
| `link` | `text` | 連結訊息（轉為文字） |

### 通知事件 (notice)
事件透過 `mp_event` 欄位區分具體類型。

| 微信 Event | `mp_event` | 說明 |
|-----------|-----------|------|
| `subscribe` | `subscribe` | 關注公眾號 |
| `unsubscribe` | `unsubscribe` | 取消關注 |
| `SCAN` | `scan` | 掃描帶參數二維碼 |
| `LOCATION` | `location_report` | 報告地理位置 |
| `CLICK` | `menu_click` | 自訂選單點擊 |
| `VIEW` | `menu_view` | 選單跳轉連結 |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | 模板訊息發送結果 |
| `MASSSENDJOBFINISH` | `mass_send_finish` | 群發訊息發送結果 |

## 平台擴充欄位

事件物件中的微信特有欄位（`mp_` 前綴）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `mp_raw` | str | 原始 XML 資料 |
| `mp_raw_type` | str | 原始訊息/事件類型 |
| `mp_msg_id` | str | 微信訊息 ID |
| `mp_event` | str | 事件類型（僅事件通知） |
| `mp_event_key` | str | 事件 Key（選單點擊/掃碼等） |
| `mp_to_user` | str | 接收方微信號（公眾號原始ID） |
| `mp_from_user` | str | 發送方 OpenID |
| `mp_data` | dict | 解析後的 XML 字典資料 |

## 事件擴充方法

透過 `register_event_mixin("mp", ...)` 註冊，在事件物件上可直接呼叫：

| 方法 | 返回值 | 說明 |
|------|--------|------|
| `get_openid()` | str | 發送者 OpenID |
| `get_msg_type()` | str | 微信原始訊息類型 |
| `get_event()` | str | 事件類型（僅事件通知） |
| `get_content()` | str | 訊息純文字內容 |
| `get_raw_xml()` | str | 原始 XML 資料 |

## 設定選項

### 多帳號設定

每個帳號對應一個公眾號：

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # 安全模式/相容模式才需要（43位）
callback_path = "/mp/main"               # 回調路徑
enable = true

[WechatMpAdapter.accounts.secondary]
appid = "wx0987654321fedcba"
appsecret = "another_app_secret"
token = "another_callback_token"
callback_path = "/mp/secondary"
enable = true
```

### 設定欄位說明

| 欄位 | 必填 | 說明 |
|------|------|------|
| `appid` | 是 | 公眾號 AppID |
| `appsecret` | 是 | 公眾號 AppSecret（secret） |
| `token` | 否 | 回調驗證 Token（建議填寫以啟用簽名驗證） |
| `encoding_aes_key` | 否 | 訊息加解密密鑰（43位，安全模式必需） |
| `callback_path` | 否 | 回調路徑範本，預設 `/mp/{account}`，`{account}` 會被帳號名替換 |
| `enable` | 否 | 是否啟用，預設 true |

## 加密模式說明

微信公眾號提供三種訊息加解密模式：

| 模式 | 說明 | encoding_aes_key | 驗證欄位 |
|------|------|-----------------|---------|
| 明文模式 | XML 明文傳輸 | 不需要 | `signature` |
| 相容模式 | 明文+密文同時存在 | 可選 | `signature` / `msg_signature` |
| 安全模式 | 全部加密 | 必需 | `msg_signature` |

本適配器自動處理：
- 明文模式：驗證 `signature`，直接解析 XML
- 安全/相容模式：檢測 `Encrypt` 欄位，驗證 `msg_signature`，使用 AES-256-CBC 解密
- 解密依賴 `cryptography` 程式庫（已宣告在 dependencies 中）

## 回調路由

適配器為每個已啟用帳號註冊兩個路由（GET + POST）：

- **GET**：微信伺服器接入驗證，驗證簽名後返回 `echostr`
- **POST**：接收使用者訊息和事件，驗證簽名→解密（如需）→轉換→emit

實際訪問路徑會自動新增模組前綴，例如註冊路徑 `/mp/main`，
實際訪問路徑為 `/mp_{account}_verify/mp/main` 和 `/mp_{account}_message/mp/main`。

## API 回應

所有 `call_api` 呼叫返回標準化回應：

- 成功：`status: "ok"`, `retcode: 0`
- 失敗：`status: "failed"`, `retcode: 34000+errcode`
- 始終包含 `mp_raw`（原始回應）、`message_id`