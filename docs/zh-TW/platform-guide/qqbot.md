# QQBot 平台特性文件

QQBotAdapter 是基於 QQ 官方機器人（QQ OpenAPI）協定建構的適配器，整合群聊、私聊、頻道等全場景功能，提供 OneBot12 標準事件、標準 API 動作與請求操作介面。

---

## 文件資訊

- 對應模組版本: 5.0.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：QQ官方機器人開發介面，支援群聊、私聊、頻道等多種場景
- 適配器名稱：QQBotAdapter
- 連接方式：**WebSocket 長連線**（預設）或 **Webhook HTTP 回調**（依帳戶設定，Ed25519 驗簽）
- 認證方式：appId + clientSecret 取得 access_token（7200秒，提前45秒自動刷新）
- API根地址：`https://api.bot.qq.com`（v5 起官方統一域名，sandbox 已廢棄）
- OneBot12相容：訊息收發、事件、**標準Api動作**、**請求操作**全面覆蓋
- 多帳戶：支援，`accounts` 下任意帳戶並行（可混合 websocket/webhook 模式）

## 配置說明

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # 全局：訂閱的事件 intents（JSON數組，支援事件名）

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # QQ機器人應用ID（必填）
secret = "YOUR_CLIENT_SECRET"        # QQ機器人客戶端密鑰（必填）
mode = "websocket"                   # 事件接收方式：websocket / webhook
bot_id = ""                          # 機器人ID（留空自動獲取；可手動填寫用於 Using() 定位）
gateway_url = ""                     # WebSocket網關地址（留空通過 /gateway/bot 動態獲取）
api_base_url = "https://api.bot.qq.com"  # API根地址（可自定義用於代理）
webhook_path = "/webhook"            # Webhook回調路徑（mode=webhook 時生效）
enabled = true
```

**v5 破壞性變更：**
- 官方統一使用 `api.bot.qq.com`，`sandbox` 配置廢棄（舊配置自動遷移並忽略）
- 舊版扁平配置（`[QQBot_Adapter]` 下直接寫 appid/secret）自動遷移到 `accounts.default`
- 框架為**軟依賴**：安裝適配器不會拉取框架版本；運行時檢測 `ErisPulse>=2.7.1` 並提示

**intents 說明（支援位序號或事件名）：**

| 位 | 事件名 | 說明 |
|----|--------|------|
| 0 | GUILDS | 頻道變更 |
| 1 | GUILD_MEMBERS | 頻道成員變更 |
| 9 | GUILD_MESSAGES | 頻道消息（私域） |
| 12 | DIRECT_MESSAGE | 頻道私信 |
| 24 | GROUP_MEMBER | 群成員變更（v5新增） |
| 25 | GROUP_AND_C2C_EVENT | 群@消息與私聊消息 |
| 26 | INTERACTION | 交互事件（按鈕等） |
| 27 | MESSAGE_AUDIT | 消息審核事件 |
| 30 | PUBLIC_GUILD_MESSAGES | 頻道消息（公域） |

## 消息發送

### 基礎發送

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")

# 群聊@消息（自動使用 <qqbot-at-user id="x" /> 格式）
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@你")

# 頻道消息（@ 自動使用 <@user_id> 格式）
await qqbot.Send.To("channel", channel_id).Text("頻道消息")

# 被動回覆（自動攜帶 msg_id，無需手動 Reply）
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("回覆內容")

# 富媒體（URL / 本地路徑 / 二進制；超過5MB自動分片上傳）
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")

# Markdown（原生 / 模板）
await qqbot.Send.To("group", gid).Markdown("# 標題\n- 列表")
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "通知"}])

# 鍵盤（自動置為 markdown 類型並附帶 bot_appid）
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("請選擇")

# 流式消息（單聊）
await qqbot.Send.To("user", openid).Stream("回答內容")

# 多賬戶
await qqbot.Send.Using("account2").To("group", gid).Text("來自第二個機器人")
```

## OneBot12 標準 API 動作

```python
result = await qqbot.Api.get_self_info()                     # 机器人信息
result = await qqbot.Api.get_group_info(group_openid)        # 群信息
result = await qqbot.Api.get_group_member_list(group_openid) # 群成员列表（自動分頁）
result = await qqbot.Api.get_guild_list()                    # 頻道列表
result = await qqbot.Api.get_channel_list(guild_id)          # 子頻道列表
await qqbot.Api.delete_message(message_id)                   # 撤回（自動按訊息來源路由端點）
result = await qqbot.Api.get_status()                        # 多帳戶運行狀態
result = await qqbot.Api.Using("account2").get_self_info()   # 指定帳戶
```

支援的標準動作：`get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`。不支援的動作返回 `retcode=10002`。

## 請求操作（入群申請審批）

`GROUP_JOIN_REQUEST` 事件轉換為 OneBot12 `request` 事件，支援標準化審批：

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join(event):
    if event.get("platform") == "qqbot":
        await event.approve()                  # 同意
        # await event.reject(comment="理由")   # 拒絕
```

`request_id` = 官方 `join_request_id`，適配器自動快取申請上下文並路由到 `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`。

## @機器人檢測機制（重要）

QQ官方的「被@」事實由事件名承載，且群消息 @ 標記為 `<@{群空間openid}>`（與 READY 返回的 bot_id **不在同一 id 体系**）。適配器自動處理：

1. **標記解析**：`<@openid>` 與 `<qqbot-at-user>` 兩種風格均解析為 mention 段（文本中無殘留）
2. **名稱歸一化**：`/users/@me` 返回的機器人名與 mentions 數組暱稱一致時，認定為@機器人，mention 段歸一化為 bot_id（原始 openid 保留在 `data.qqbot_openid`）
3. **openid 學習**：自動學習機器人在各群的 openid，用於「接收全部群消息」模式下的@識別
4. **注入保證**：`GROUP_AT_MESSAGE_CREATE` / `AT_MESSAGE_CREATE` 保證存在機器人 mention 段

因此 `on_at_message()` / `event.is_at_message()` 在 qqbot 平台可直接使用。開啟「接收全部群消息」權限後，@消息以 `GROUP_MESSAGE_CREATE` 推送（`GROUP_AT_MESSAGE_CREATE` 不再到達），適配器同樣能識別。

## 平台原生API方法族

適配器公開完整的QQ官方API（詳情請見適配器倉庫 platform-features.md）：

- **機器人**：`get_me()`、`reply_interaction()`
- **頻道**：`get_guilds/get_guild/mute_guild_all/roles管理/api_permission`
- **子頻道**：`get_channels/get_channel/create_channel/update_channel/delete_channel/pins`
- **頻道成員**：`get_guild_members/get_guild_member/mute/roles/kick`
- **權限/表態/日程/帖子/音頻**：全套方法
- **群管理**（部分接口僅限白名單機器人）：`get_group_members/get_group_bot_state/ blacklist/入群審批/禁言/審批策略`
- **菜單面板**：`get_custom_menu/update_custom_menu/指令面板CRUD`
- **富媒體**：`_upload_media`（URL/路徑/二進制，超過5MB自動分片）、`stream_message`（流式消息）

## WebSocket / Webhook 連線

### WebSocket 流程

1. appId + clientSecret 取得 access_token（提前 45 秒自動刷新，失敗重試 3 次）
2. 透過 `GET /gateway/bot` 動態取得網關位址（設定 `gateway_url` 時直接使用）
3. OP_HELLO → Identify/Resume → READY（取得 session_id 與 bot_id）→ 心跳循環
4. 斷線重連：最多 50 次，指數退避 `min(5 * 2^n, 300)` 秒；OP_RECONNECT 保留會話

### Webhook 模式

帳戶 `mode = "webhook"` 後透過 ErisPulse router 註冊 HTTP 路由：

- Ed25519 驗簽（種子 = secret 循環填滿至 32 位元組），驗證 `X-Signature-Ed25519` 對 `X-Signature-Timestamp + body`
- 自動處理 op=13 簽名驗證握手與 op=0 事件分發
- 依賴 `cryptography` 庫（隨適配器安裝）

## 錯誤碼說明

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 10001 | 參數缺失 |
| 10002 | 不支援的動作 |
| 10003 | 無法確定目標/帳戶 |
| 32000 | 請求逾時 |
| 33000 | 網路/API呼叫異常 |
| 34001 | 請求不存在或已過期（Request DSL） |
| 34100 | 媒體上傳失敗 |
| 34000+ | 平台業務錯誤（透傳官方 code） |

## 使用示例

### 處理群消息（@檢測）

```python
from ErisPulse.Core.Event import message

@message.on_at_message()
async def handle_at(event):
    if event.get("platform") != "qqbot":
        return
    text = event.get_text()
    if text == "簽到":
        await event.reply("已簽到")
```

### 處理互動事件

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") == "qqbot_interaction":
        await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
        button_id = event.get("qqbot_button_id", "")
        # 處理按鈕...
```

### 多帳號啟動

```toml
[QQBot_Adapter.accounts.bot_a]
appid = "A_APPID"
secret = "..."
enabled = true

[QQBot_Adapter.accounts.bot_b]
appid = "B_APPID"
secret = "..."
mode = "webhook"
enabled = true
```

兩個帳號並行啟動：bot_a 走 WebSocket，bot_b 走 Webhook，互不影響。