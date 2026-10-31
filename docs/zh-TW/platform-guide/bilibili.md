# Bilibili 平台特性文件

BilibiliAdapter 是基於 bilibili-api-python 的 B 站私信適配器，支援 Cookie / 掃碼雙登入與事件驅動的私信收發。

---

## 文件資訊

- 對應模組版本: 0.1.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：B 站私信機器人（無官方個人 Bot API，透過模擬登入使用 Web 私信介面）
- 适配器名稱：BilibiliAdapter
- 多賬戶支援：支援（每個賬戶一個 B 站帳號，獨立會話監聽）
- 連接方式：事件驅動會話監聽（bilibili-api `Session`）
- 認證方式：Cookie（SESSDATA / bili_jct / buvid3 / dedeuserid）或面板掃碼登入
- 鏈式修飾支援：支援 `.Reply()` 等鏈式修飾方法
- OneBot12 兼容：支援標準消息段（text / image）

## 配置說明

```toml
[BilibiliAdapter.accounts.default]
login_mode = "cookie"          # cookie=手動填寫憑證 / qrcode=面板掃碼（推薦）
sessdata = "YOUR_SESSDATA"     # cookie 模式必填
bili_jct = "YOUR_BILI_JCT"     # cookie 模式必填
buvid3 = "YOUR_BUVID3"         # 可選，降低風險概率
dedeuserid = "YOUR_UID"        # 可選，即帳號 UID
bot_id = ""                    # 留空登錄後自動獲取
enabled = true
```

**配置項說明（每個帳號）：**

- `login_mode`：登入方式。`cookie` 手動填寫憑證；`qrcode` 面板掃碼（推薦）。兩種模式的憑證最終都落在 sessdata/bili_jct 等欄位
- `sessdata` / `bili_jct`：登入狀態 Cookie（cookie 模式必填；面板中密碼形態顯示）
- `buvid3`：設備指紋 Cookie（可選），攜帶後可顯著降低風險概率
- `dedeuserid`：帳號 UID（可選），同時作為 `bot_id` 的預設來源
- `bot_id`：帳號 UID，留空則在登入後透過 `get_self_info` 自動獲取

**掃碼登入流程**：`login_mode = "qrcode"` 保存後，在 Dashboard → 組件配置 → 新增帳號嚮導中選擇「掃碼登入 B 站」→ B 站 APP 掃碼 → 手機確認 → 适配器輪詢登入狀態（scan → confirm → done），憑證自動寫入該帳號配置並生效。

> 适配器同時註冊 `POST /bilibili/qr/start`（獲取二維碼，返回圖片 URL + 會話令牌）與 `POST /bilibili/qr/poll`（輪詢登入狀態）端點，第三方前端也可直接對接。輪詢請求需攜帶 start 返回的 `poll_token`，防止未授權輪詢。

## 消息發送

所有發送方法返回 Task，await 後得到標準響應（見「返回值格式」）。

### 基礎發送

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# 文本私信（target 為對方 UID）
await bili.Send.To("user", "123456789").Text("Hello Bilibili!")

# 圖片私信（URL 或本地路徑，轉 B 站私信圖片）
await bili.Send.To("user", "123456789").Image("https://example.com/pic.jpg")
await bili.Send.To("user", "123456789").Image("./local.png")
```

### 鏈式修飾方法

```python
# 回覆指定消息（msg_key 來自收到消息的 message_id）
await bili.Send.To("user", "123456789").Reply("msg_key").Text("收到！")
```

### OneBot12 標準段發送

```python
message = [
    {"type": "text", "data": {"text": "第一行"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}},
]
await bili.Send.To("user", "123456789").Raw_ob12(message)
```

### 多帳號發送

```python
await bili.Send.Using("account2").To("user", "123456789").Text("來自第二個帳號")
```

### 支援與不支援的消息段

| 段 | 支援 | 說明 |
|----|------|------|
| `text` | 支援 | 拼接後通過 `send_msg`（TEXT）發送 |
| `image` | 支援 | `file` 為 URL / 本地路徑，通過 `send_msg`（PICTURE）發送 |
| `reply` | 部分支援 | 修飾器接受，B 站私信無引用展示，僅作發送上下文 |
| `mention` / `face` / `voice` / `video` / `file` 等 | 不支援 | 回傳 `retcode=10002` 並列出收到的段類型 |

## 標準 API 動作（Api）

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# 自身資訊（暱稱/頭像/UID）
result = await bili.Api.get_self_info()

# 用戶公開資訊（任意用戶，暱稱/頭像）
result = await bili.Api.get_user_info("123456789")

# 拉取指定會話的歷史訊息（begin_seqno 用於翻頁）
result = await bili.Api.get_session_msgs("123456789", begin_seqno=0)

# 狀態與版本
result = await bili.Api.get_status()
result = await bili.Api.get_version()

# 多帳號
result = await bili.Api.Using("account2").get_self_info()
```

### 支援的標準動作

| 方法 | 說明 | 資料來源 |
|------|------|---------|
| `get_self_info()` | 自身資訊（mid/name/face） | Web API（空間資訊） |
| `get_user_info(user_id)` | 用戶公開資訊（暱稱/頭像） | Web API（用戶資訊卡） |
| `get_session_msgs(talker_id, begin_seqno)` | 會話歷史訊息 | Web 私信接口（session_msgs） |
| `get_status()` | 適配器運行狀態 | 本地 |
| `get_version()` | 適配器版本 | 本地 |

### 不支援的標準動作

以下標準動作 B 站私信無對應能力，呼叫返回 `retcode=10002`：

- `get_friend_list` / `get_group_list` / `get_group_member_info`
- `delete_message`（B 站私信僅對方可撤回自己的訊息）
- `set_group_name` / `leave_group` 等群管理類

### 通用動作入口

```python
# send_message：文字與圖片段組合發送（等價於 Send 鏈）
result = await bili.call_api(
    "send_message",
    _account_id="default",
    target_id="123456789",
    message=[{"type": "text", "data": {"text": "hi"}}],
)
```

## 返回值格式

所有發送與 API 方法遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",              # ok / failed
    "retcode": 0,                # 0 成功；10002 不支援；10003 參數/目標錯誤；33100 B 站接口錯誤
    "data": {...},               # 响应数据（send_msg 原始返回）
    "self": {"platform": "bilibili", "user_id": "..."},
    "message_id": "123456",      # B 站 msg_key
    "message": "",               # 錯誤信息
    "bilibili_raw": {...}        # 原始响应
}
```

## 事件類型

需要 `platform == "bilibili"` 檢測再使用本平台特性。

### 事件映射

| B 站私信事件 | Adapter 事件 | 說明 |
|--------------|--------------|------|
| TEXT（文本消息） | message（text 段） | 常規私聊文本 |
| PICTURE（圖片消息） | message（image 段） | content.pictures → image 段（URL） |
| WITHDRAW（撤回） | 僅記錄日誌 | 對方撤回消息 |

### 事件欄位示例

```python
{
  "id": "uuid",
  "time": 1793277000,
  "type": "message",
  "detail_type": "private",
  "platform": "bilibili",
  "self": {"platform": "bilibili", "user_id": "10000", "user_name": "Bot 昵稱", "account_id": "default"},
  "user_id": "123456789",                  # 對方 UID（sender_uid）
  "user_nickname": "小王",                  # content.sender_name（可能缺失）
  "message": [{"type": "text", "data": {"text": "你好"}}],
  "alt_message": "你好",
  "bilibili_raw": {...},                   # B 站原始私信數據
  "bilibili_raw_type": "text"              # text / picture
}
```

### 擴展欄位說明

- 所有特有欄位均以 `bilibili_` 前綴標識（`bilibili_raw` / `bilibili_raw_type`）
- 接收圖片為 image 段，`data.file` 是 B 站圖床 URL
- `user_nickname` 來自消息 content 的 `sender_name`，部分消息類型可能缺失

## 注意事項

1. **B 站無官方個人 Bot API**：本適配器透過模擬登入使用 Web 私信介面，屬非官方用法，介面可能隨 B 站更新而變動
2. **風險控制**：高頻率/批量私信極易觸發風險控制（帳號私信功能被臨時禁言）。請務必在模組側做節流；`buvid3` 攜帶後可降低概率
3. **登入狀態失效**：Cookie 過期後適配器會記錄錯誤日誌，請重新掃碼或更新 Cookie；憑據面板中密碼以形態顯示
4. 個人對話限制：僅支援一對一私信；粉絲群聊暫不支援
5. 合規：請勿用於騷擾、營銷群發等違規用途，遵守 B 站社區規則