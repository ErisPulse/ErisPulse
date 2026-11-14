# 企業微信（WeCom）平台特性文件

WeComAdapter 是基於企業微信自建應用 API 建構的適配器，透過回呼接收訊息、應用訊息介面主動發送，並提供通訊錄與訊息卡片能力。

---

## 文件資訊

- 對應模組版本： 0.1.2
- 維護者： ErisPulse
- 最後更新： 2026-11-10

## 基本資訊

- 平台簡介：企業微信自建應用機器人，適用於企業內部通知、智能問答、辦公自動化等場景
- 適配器名稱：WeComAdapter
- 平台註冊名：`wecom`（別名 `wxwork`）
- 多帳戶支援：支援同時配置多個企業（每個帳戶對應一個 corpid + 應用）
- 連接方式：HTTP 回呼接收（企業微信後台配置接收訊息 URL）+ 主動 API 傳送
- 認證方式：corpid + secret 換取 access_token（自動更新）
- 回呼加解密：Token + EncodingAESKey（企業微信官方加解密協定）
- 會話類型映射：應用訊息 → `private`（成員私訊），應用群聊 → `group`
- 鏈式修飾支援：支援 `.Reply()` 等鏈式修飾方法
- OneBot12 相容：傳送支援 OneBot12 標準訊息段

## 標準化對齊（0.1.2）

本版本完成轉接器標準化對齊，回應結構與錯誤碼遵循 [API 回應規範](../standards/api-response.md)。

### 帳戶與多帳戶

- `call_api` 支援雙相容帳戶欄位：`account_id`（標準名稱）/ `_account_id`（舊名稱），框架 ApiDSL（`Api.Using(...)`）自動適配
- **`get_user_info` 等 6 個通訊錄 Api 方法（`get_user_info` / `get_department_list` / `get_department_users` / `get_user_by_mobile` / `userid_to_openid` / `openid_to_userid`）已修復 `Using()` 兜底**：帳戶未指定時回落至 `Api.Using(...)` 指定的帳戶，不再被忽略
- `Send` 讀取 `send_context`（事件帳戶兜底）：從事件上下文呼叫 `Send` 時預設回落至來源帳戶

### 標準欄位

- **訊息事件補齊頂層 `message_id`**（取企業微信 MsgId，缺失時以 uuid 兜底）
- **`get_user_info` 等查詢回傳標準化欄位**：`user_id` / `user_name` / `user_displayname`，原始資料保留於 `wecom_raw`
- **`get_self_info` 補齊 `user_displayname`**（`user_id` 為 corpid，`user_name` / `user_displayname` 為 `wecom:{帳戶名稱}`）
- Converter 重用框架 `BaseConverter`（共用欄位 id/time/platform/self/wecom_raw 由 `build_base_event` 統一建構）

### 錯誤碼規範

| retcode | 含義 | 說明 |
|---------|------|------|
| 0 | 成功 | — |
| 34100 | 平台失敗 | 企業微信回傳失敗（errcode != 0）；原始回應保留於 `wecom_raw` |
| 10003 | 參數錯誤 | 缺少或無效參數 |

## 設定說明

```toml
# config.toml
[WeComAdapter.accounts.default]
corpid = "YOUR_CORP_ID"        # 企業 ID（必填，企業微信後台-我的企業）
secret = "YOUR_APP_SECRET"     # 應用 Secret（必填，自建應用詳情頁）
agentid = 1000002              # 應用 AgentId（必填，自建應用詳情頁）
callback_enabled = true        # 啟用回調接收（預設 true；關閉後僅能主動發送）
token = "YOUR_CALLBACK_TOKEN"  # 回調驗證 Token（企業微信後台接收訊息設定）
encoding_aes_key = "YOUR_AES_KEY_43CHARS"  # 回調加解密金鑰（43 位）
callback_path = "/wecom/{account}"         # 回調路徑，支援 {account} 佔位符
enabled = true
```

**設定項說明（每個帳戶）：**

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `corpid` | string | 是 | 企業 ID |
| `secret` | string | 是 | 應用 Secret |
| `agentid` | int | 建議 | 應用 AgentID |
| `callback_enabled` | bool | 否 | 回調接收開關（預設開啟） |
| `token` | string | 否 | 回調驗證 Token |
| `encoding_aes_key` | string | 否 | 回調加解密金鑰（43 位） |
| `callback_path` | string | 否 | 回調路徑，支援 `{account}` 佔位符 |
| `enabled` | bool | 否 | 是否啟用（預設 true） |

- `corpid` / `secret` / `agentid`：從[企業微信管理後台](https://work.weixin.qq.com)的自建應用頁取得（前兩項必填）
- `callback_enabled`：回調接收開關（預設開啟）。**關閉後轉接器跳過回調路由註冊，僅保留主動發送能力**；面板中回調相關欄位隨之隱藏
- `token` / `encoding_aes_key`：回調訊息驗證與加解密，與企業微信後台「接收訊息」設定一致
- `callback_path`：回調接收路徑（預設 `/wecom/{帳戶名}`），企業微信後台需設定完整 URL：`http(s)://你的位址:連接埠/wecom/<帳戶名>`

**接收訊息前置條件**：企業微信後台 → 自建應用 → 「接收訊息」設定 API 接收，URL 填上述完整回調位址，Token 與 EncodingAESKey 與設定一致。**注意**：企業微信要求回調 URL 可公網存取（建議搭配反向代理）。

**API 環境**：
- API 基礎位址：`https://qyapi.weixin.qq.com/cgi-bin`
- access_token 自動取得與快取重新整理，無需手動管理

## 支援的訊息傳送類型

所有傳送方法均透過鏈式語法實現，例如：

```python
from ErisPulse import sdk
wecom = sdk.adapter.get("wecom")

# 基礎訊息（target_type: "user"=成員 "group"=應用群聊）
await wecom.Send.To("user", "zhangsan").Text("你好")
await wecom.Send.To("group", "group_chat_id").Markdown("**粗體**通知")

# 媒體（本地路徑 / bytes / URL；自動上傳臨時素材後傳送）
await wecom.Send.To("user", "zhangsan").Image("banner.png")
await wecom.Send.To("user", "zhangsan").Voice("voice.amr")
await wecom.Send.To("user", "zhangsan").Video("demo.mp4")
await wecom.Send.To("user", "zhangsan").File("report.pdf")

# 圖文與卡片
await wecom.Send.To("user", "zhangsan").News([
    {"title": "標題", "description": "摘要", "url": "https://...", "picurl": "https://.../img.png"},
])  # 最多 8 則

await wecom.Send.To("user", "zhangsan").TextCard(
    title="審批提醒",
    description="您有一筆待審批單據",
    url="https://oa.example.com/approval/1",
    btntxt="去處理",
)

await wecom.Send.To("user", "zhangsan").TemplateCard(
    card_type="text_notice",  # 企業微信卡片類型，其餘參數按官方卡片 JSON 透傳
    source={"icon_url": "...", "desc": "OA"},
    main_title={"title": "會議提醒"},
)

# 被動回覆：收到訊息的 event.reply() 直接回覆來源使用者

# 多帳戶指定帳戶傳送
await wecom.Send.To("user", "UserID", account_id="app2").Text("透過 app2 傳送")
```

### 基本傳送方法

| 方法 | 說明 | 參數 |
|------|------|------|
| `.Text(text)` | 傳送純文字訊息 | `text: str` |
| `.Markdown(content)` | 傳送 Markdown 訊息（應用訊息支援） | `content: str` |

### 媒體傳送方法

媒體方法支援 `bytes`（自動上傳取得 media_id）和 `str`（已上傳的 media_id 或路徑/URL）兩種輸入：

| 方法 | 說明 |
|------|------|
| `.Image(file, filename)` | 傳送圖片 |
| `.Voice(file, filename)` | 傳送語音（需 AMR 格式，企業微信限制） |
| `.Audio(file, filename)` | Voice 的別名 |
| `.Video(file, filename)` | 傳送影片 |
| `.File(file, filename)` | 傳送檔案 |

### 富文本卡片方法

| 方法 | 說明 |
|------|------|
| `.News(articles)` | 傳送圖文訊息（最多 8 則） |
| `.TextCard(title, description, url, btntxt)` | 傳送文字卡片 |
| `.TextCardMiniProgram(**kwargs)` | 傳送小程式通知卡片 |
| `.TemplateCard(card_type, **kwargs)` | 傳送範本卡片 |

### 原始訊息傳送

- `.Raw_ob12(message: List[Dict])`：傳送 OneBot12 標準格式訊息

### 鏈式修飾方法

| 方法 | 說明 |
|------|------|
| `.At(user_id)` | @指定使用者（由框架 SendDSL 基底類別實現） |
| `.AtAll()` | @全體成員（由框架 SendDSL 基底類別實現） |
| `.Reply(message_id)` | 回覆指定訊息（由框架 SendDSL 基底類別實現） |

### 傳送目標映射

| OB12 target_type | 企業微信目標欄位 | API 介面 |
|---|---|---|
| `user` / `private` | `touser` | `message/send` |
| `group` | `chatid` | `appchat/send` |

## 標準 API 動作

```python
info = await wecom.Api.get_self_info()          # 應用資訊（corpid/agentid）
status = await wecom.Api.get_status()           # 執行狀態
ver = await wecom.Api.get_version()             # 適配器版本

# 通訊錄（自動注入 access_token；0.1.2 起 Using() 兜底生效）
user = await wecom.Api.get_user_info("zhangsan")            # 成員詳情（姓名/部門/職務/頭像）
depts = await wecom.Api.get_department_list(0)              # 部門列表（0=根部門）
members = await wecom.Api.get_department_users(2)           # 部門成員列表
uid = await wecom.Api.get_user_by_mobile("13800000000")     # 手機號碼查詢 userid
openid = await wecom.Api.userid_to_openid("zhangsan")       # userid → openid（紅包/對外支付）
userid = await wecom.Api.openid_to_userid("oXXXX")          # openid → userid

# 多帳戶：指定企業帳戶
result = await wecom.Api.Using("corp2").get_user_info("lisi")

# 任意企業微信 API 直調（endpoint 相對 cgi-bin，自動帶 access_token）
result = await wecom.Api.call("message/send", touser="zhangsan", msgtype="text", agentid=1000002, text={"content": "hi"})
```

## 特有事件類型

需要 `platform == "wecom"` 偵測後再使用本平台特性。企業微信事件轉換遵循 OneBot12 標準，同時透過 `wecom_` 前綴提供平台擴充。

### 訊息事件 detail_type 映射

企業微信應用接收的訊息統一映射為 `private`（私訊）：

| 企業微信訊息 | OneBot12 type / detail_type |
|---|---|
| `text` | `message` / `private` |
| `image` | `message` / `private` |
| `voice` | `message` / `private` |
| `video` / `shortvideo` | `message` / `private` |
| `location` | `message` / `private` |
| `link` | `message` / `private` |

### 特有事件類型（notice）

| detail_type | 說明 |
|---|---|
| `wecom_subscribe` | 使用者關注 / 進入應用（subscribe / enter_agent） |
| `wecom_unsubscribe` | 使用者取消關注 |
| `wecom_location_report` | 上報地理位置 |
| `wecom_menu_click` | 點擊選單跳轉事件（click） |
| `wecom_menu_view` | 點擊選單連結跳轉（view） |
| `wecom_scancode` | 掃碼推事件 |
| `wecom_menu_photo` | 拍照/相簿事件 |

> 上報事件（訂閱/選單點擊等）轉換為 `request` / `notice` 類事件。

### 標準訊息段類型

轉換後的訊息段使用 OneBot12 標準格式：

| 訊息段類型 | 說明 | data 欄位 |
|---|---|---|
| `text` | 純文字 | `text` |
| `image` | 圖片 | `file`（PicUrl 或 MediaId），`url` |
| `audio` | 語音 | `file`（MediaId） |
| `video` | 影片 | `file`（MediaId），`thumbnail` |
| `location` | 位置 | `latitude`, `longitude`, `title` |
| `file` | 檔案/連結 | `file`, `filename`, `url` |

### 平台擴充訊息段

以 `wecom_` 前綴標識的擴充訊息段（傳送方向）：

| 訊息段類型 | 說明 | data 欄位 |
|---|---|---|
| `wecom_markdown` | Markdown 訊息 | `content` |
| `wecom_news` | 圖文訊息 | `articles`（list） |
| `wecom_textcard` | 文字卡片 | `title`, `description`, `url`, `btntxt` |
| `wecom_miniprogram_notice` | 小程式通知 | 原生欄位透傳 |
| `wecom_template_card` | 範本卡片 | `card_type` + 原生欄位 |

### 事件範例

#### 文字訊息

```python
{
  "id": "1234567890123456",
  "time": 1348831860,
  "type": "message",
  "detail_type": "private",
  "platform": "wecom",
  "self": {"platform": "wecom", "user_id": "Corpid"},
  "message_id": "1234567890123456",
  "user_id": "UserID",
  "user_nickname": "UserID",
  "message": [{"type": "text", "data": {"text": "訊息內容"}}],
  "alt_message": "訊息內容",
  "wecom_raw": {"MsgType": "text", "Content": "訊息內容", "...": "..."},
  "wecom_raw_type": "text",
  "wecom_agentid": "1000002",
  "wecom_corpid": "Corpid",
  "wecom_msg_id": "1234567890123456"
}
```

> **0.1.2 變化**：訊息事件補齊頂層 `message_id`（取企業微信 MsgId，缺失時以 uuid 兜底）。

#### 選單點擊事件

```python
{
  "type": "notice",
  "detail_type": "wecom_menu_click",
  "platform": "wecom",
  "user_id": "UserID",
  "wecom_event_key": "menu_key_1",
  "wecom_raw_type": "event"
}
```

## Event Mixin 擴充方法

適配器註冊了以下平台專有方法，僅在 `platform == "wecom"` 時可用：

| 方法 | 回傳類型 | 說明 |
|------|----------|------|
| `get_user_id()` | `str` | 獲取傳送者 UserID |
| `get_msg_type()` | `str` | 獲取企業微信訊息類型（text/image/...） |
| `get_content()` | `str` | 獲取訊息純文字內容 |
| `get_agentid()` | `str` | 獲取應用 AgentID |
| `get_corpid()` | `str` | 獲取企業 Corpid |
| `get_msg_id()` | `str` | 獲取訊息 MsgId |
| `get_raw_xml()` | `str` | 獲取解密後的原始 XML |
| `get_raw()` | `dict` | 獲取解析後的原始資料字典 |
| `get_event_key()` | `str` | 獲取選單事件的 EventKey |
| `get_media_id()` | `str` | 獲取媒體訊息的 MediaId |

### 使用範例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "wecom":
        return

    msg_type = event.get_msg_type()
    user_id = event.get_user_id()
    content = event.get_content()

    if msg_type == "text":
        await event.reply(f"收到: {content}")

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "wecom":
        return

    if event.get("detail_type") == "wecom_menu_click":
        key = event.get_event_key()
        await event.reply(f"你點擊了選單: {key}")
```

## 擴充欄位說明

- 所有特有欄位均以 `wecom_` 前綴標識
- 保留原始資料在 `wecom_raw` 欄位（解析後的字典）
- 保留解密後原始 XML 在 `wecom_raw_xml` 欄位
- 保留原始事件類型在 `wecom_raw_type` 欄位
- `wecom_corpid`：企業ID
- `wecom_agentid`：應用 AgentID
- `wecom_msg_id`：企業微信訊息 ID

## 認證與加解密

### access_token 管理

- 每個帳戶獨立快取 access_token
- 有效期 7200 秒，提前 5 分鐘自動重新整理
- token 失效（errcode 40014/42001）時自動清除快取並重試

### 訊息加解密

- 演算法：AES-256-CBC（PKCS7 填充）
- 金鑰：`base64decode(EncodingAESKey + "=")`（32位元組）
- IV：金鑰前 16 位元組
- 簽章：`sha1("".join(sorted([token, timestamp, nonce, encrypt])))`
- 相依套件：`cryptography`

## 注意事項

1. **回呼 URL 必須公網可達**：本機開發可用內網穿透；正式環境建議以 Nginx 反向代理到 ErisPulse router 埠
2. **主動傳送頻率**：受企業微信應用程式訊息介面限制（每應用程式每日量與企業規模相關），群發場景請用 `TaskCard`/`TemplateCard` 結合標籤
3. **access_token 有效性**：配接器自動重新整理；多實例部署同一 corpid+secret 時注意官方 token 互踢限制（建議由單一實例收發為宜）
4. **媒體檔案**：Voice 需 AMR 格式（企業微信限制）；大檔案走臨時素材介面（配接器自動處理）