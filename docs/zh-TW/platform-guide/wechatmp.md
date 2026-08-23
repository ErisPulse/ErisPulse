# 微信公眾號 (WechatMp) 適配器 - 平台特性文件

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 基本資訊
- 模組名稱: `ErisPulse-WechatMpAdapter`
- 平台標識: `mp`（別名: `wechat_mp`）
- 模組版本: 4.1.0
- 維護者: ErisPulse
- 依賴: `cryptography`

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

## 支援的消息傳送類型

| 方法 | 說明 | 微信 API |
|------|------|---------|
| `Text(text)` | 發送文字 | 客服消息 `message/custom/send` |
| `Image(file)` | 發送圖片（自動上傳獲取 media_id） | 客服消息 + `media/upload` |
| `Voice(file)` | 發送語音（自動上傳獲取 media_id） | 客服消息 + `media/upload` |
| `Video(file, title, description)` | 發送影片（自動上傳獲取 media_id） | 客服消息 + `media/upload` |
| `Music(url, title, description, ...)` | 發送音樂 | 客服消息 |
| `News(articles)` | 發送圖文消息 | 客服消息 |
| `Template(template_id, data, url)` | 發送模板消息 | `message/template/send` |
| `Menu(head_content, list, tail_content)` | 發送選單消息 | 客服消息 `msgmenu` |
| `Raw_ob12(message)` | 發送 OneBot12 標準消息段 | - |

### 媒體文件說明
- 支援三種參數類型：
  - `str` URL（以 `http://` / `https://` 開頭）：自動下載後上傳
  - `str` 本地檔案路徑：自動讀取後上傳
  - `bytes` 二進位資料：直接上傳
  - `str` media_id：以 `media:` 前綴可直接重用已上傳的 media_id
- 上傳後獲得臨時素材 `media_id`，有效期 3 天

### 重要限制
- 客服消息只能在用戶與公眾號互動後 **48 小時內** 主動發送
- 超過 48 小時需使用模板消息（需用戶授權場景）
- 未認證服務號（`verified=false`）無法主動發送，只能被動回覆（見上方「認證服務號與被動回覆」）

## 事件類型

### 消息事件 (message)
所有使用者訊息均為 `detail_type: private`（公眾號 1v1 場景）。

| 微信 MsgType | 消息段類型 | 說明 |
|-------------|-----------|------|
| `text` | `text` | 文字訊息 |
| `image` | `image` | 圖片訊息 |
| `voice` | `voice` | 語音訊息（含語音辨識結果） |
| `video` | `video` | 影片訊息 |
| `shortvideo` | `video` | 小影片（標記 `mp_shortvideo`） |
| `location` | `location` | 地理位置訊息 |
| `link` | `text` | 鏈接訊息（轉為文字） |

### 通知事件 (notice)
事件透過 `mp_event` 欄位區分具體類型。

| 微信 Event | `mp_event` | 說明 |
|-----------|-----------|------|
| `subscribe` | `subscribe` | 關注公眾號 |
| `unsubscribe` | `unsubscribe` | 取消關注 |
| `SCAN` | `scan` | 掃描帶參數二維碼 |
| `LOCATION` | `location_report` | 上報地理位置 |
| `CLICK` | `menu_click` | 自訂選單點擊 |
| `VIEW` | `menu_view` | 選單跳轉連結 |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | 模板訊息發送結果 |
| `MASSSENDJOBFINISH` | `mass_send_finish` | 群發訊息發送結果 |

## 平台擴展欄位

事件物件中的微信特有欄位（`mp_` 前綴）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `mp_raw` | str | 原始 XML 數據 |
| `mp_raw_type` | str | 原始消息/事件類型 |
| `mp_msg_id` | str | 微信消息 ID |
| `mp_event` | str | 事件類型（僅事件通知） |
| `mp_event_key` | str | 事件 Key（選單點擊/掃描等） |
| `mp_to_user` | str | 接收方微信號（公眾號原始 ID） |
| `mp_from_user` | str | 發送方 OpenID |
| `mp_data` | dict | 解析後的 XML 字典數據 |

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 事件擴展方法

透過 `register_event_mixin("mp", ...)` 註冊後，在事件物件上可直接呼叫：

| 方法 | 返回值 | 說明 |
|------|--------|------|
| `get_openid()` | str | 發送者 OpenID |
| `get_msg_type()` | str | 微信原始消息類型 |
| `get_event()` | str | 事件類型（僅事件通知） |
| `get_content()` | str | 消息純文字內容 |
| `get_raw_xml()` | str | 原始 XML 數據 |

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 配置選項

### 多帳號配置

每個帳號對應一個公眾號：

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # 安全模式/兼容模式才需要（43位）
callback_path = "/mp/main"               # 回調路徑
verified = true                          # 是否為認證服務號（影響主動發送能力）
enable = true

[WechatMpAdapter.accounts.secondary]
appid = "wx0987654321fedcba"
appsecret = "another_app_secret"
token = "another_callback_token"
callback_path = "/mp/secondary"
enable = true
```

### 配置字段說明

| 字段 | 必填 | 說明 |
|------|------|------|
| `appid` | 是 | 公眾號 AppID |
| `appsecret` | 是 | 公眾號 AppSecret（secret） |
| `token` | 否 | 回調驗證 Token（建議填寫以啟用簽名驗證） |
| `encoding_aes_key` | 否 | 消息加解密密鑰（43位，安全模式必需） |
| `callback_path` | 否 | 回調路徑模板，預設 `/mp/{account}`，`{account}` 會被帳號名替換 |
| `verified` | 否 | 是否為**認證服務號**，預設 `true`（見下方說明） |
| `enable` | 否 | 是否啟用，預設 true |

### 認證服務號與被動回覆（verified）

- `verified = true`（預設，認證服務號）：可隨時使用**客服消息**主動推送（48 小時視窗內）與模板消息
- `verified = false`（未認證訂閱號）：
  - 客服消息 / 模板消息**只能在 webhook 被動回覆上下文中發送**（收到用戶消息後 15 秒內、一次回覆）——適配器會自動將發送截獲為被動回覆
  - 主動推送（如定時任務）返回 `retcode=34003` 錯誤

## 加密模式說明

微信公眾號提供三種訊息加解密模式：

| 模式 | 說明 | encoding_aes_key | 驗證欄位 |
|------|------|-----------------|---------|
| 明文模式 | XML 明文傳輸 | 不需要 | `signature` |
| 兼容模式 | 明文+密文同時存在 | 可選 | `signature` / `msg_signature` |
| 安全模式 | 全部加密 | 必需 | `msg_signature` |

本適配器自動處理：
- 明文模式：驗證 `signature`，直接解析 XML
- 安全/兼容模式：檢測 `Encrypt` 欄位，驗證 `msg_signature`，使用 AES-256-CBC 解密
- 解密依賴 `cryptography` 庫（已宣告在 dependencies 中）

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

## 回調路由

適配器為每個已啟用帳戶註冊兩個路由（GET + POST）：

- **GET**：微信伺服器接入驗證，驗證簽名後返回 `echostr`
- **POST**：接收使用者訊息和事件，驗證簽名→解密（如需）→轉換→emit

實際訪問路徑會自動添加模組前綴，例如註冊路徑 `/mp/main`，
實際訪問路徑為 `/mp_{account}_verify/mp/main` 和 `/mp_{account}_message/mp/main`。

## API 回應

所有 `call_api` 調用返回標準化響應：

- 成功：`status: "ok"`, `retcode: 0`
- 失敗：`status: "failed"`, `retcode: 34000+errcode`
- 始終包含 `mp_raw`（原始響應）、`message_id`

[**返回頂部**](docs/zh-TW/quick-start.md)