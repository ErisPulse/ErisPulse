# QQBot平台特性文件

QQBotAdapter 是基於 QQ 官方機器人（QQ OpenAPI）協議構建的適配器，整合群聊、私聊、頻道等全場景功能，提供 OneBot12 標準事件、標準 Api 動作與請求操作介面。

---

## 文件資訊

- 對應模組版本: 5.3.3
- 維護者: ErisPulse
- 最後更新: 2026-11-10

## 基本資訊

- 平台簡介：QQ 官方機器人開發介面，支援群聊、私聊、頻道等多種場景
- 適配器名稱：QQBotAdapter
- 連接方式：**WebSocket 長連線**（預設）或 **Webhook HTTP 回調**（依帳戶設定，Ed25519 驗簽）
- 認證方式：appId + clientSecret 取得 access_token（7200s，提前45s自動刷新）
- API 根位址：`https://api.bot.qq.com`（v5 起官方統一域名，sandbox 已廢棄）
- OneBot12 兼容：訊息收發、事件、**標準Api 動作**、**請求操作**全面覆蓋
- 多帳戶：支援，`accounts` 下任意帳戶並行（可混合 websocket/webhook 模式）

## 配置說明

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # 全域：訂閱的事件 intents（JSON陣列，支援事件名）

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # QQ 機器人應用 ID（必填）
secret = "YOUR_CLIENT_SECRET"        # QQ 機器人客戶端密鑰（必填）
mode = "websocket"                   # 事件接收方式：websocket / webhook
bot_id = ""                          # 機器人 ID（留空自動獲取；可手動填寫用於 Using() 定位）
gateway_url = ""                     # WebSocket 網關位址（留空透過 /gateway/bot 動態獲取）
api_base_url = "https://api.bot.qq.com"  # API 根位址（可自訂用於代理）
access_token_url = ""                # 自訂 token 介面（留空使用官方介面）
webhook_path = "/webhook"            # Webhook 回調路徑（mode=webhook 時生效）
enabled = true
```

**v5 破壞性變更：**
- `sandbox` 字段已廢棄：官方統一使用 `api.bot.qq.com`，舊配置中的 sandbox 會自動遷移並忽略（列印警告）
- 舊版扁平配置（`[QQBot_Adapter]` 下直接寫 appid/secret）會自動遷移到 `accounts.default`
- 框架為**軟依賴**：安裝適配器不會拉取框架版本；執行時檢測 `ErisPulse>=2.7.1` 並提示

**intents 說明（支援位序號或事件名）：**

| 位 | 事件名 | 說明 |
|----|--------|------|
| 0 | GUILDS | 頻道變更 |
| 1 | GUILD_MEMBERS | 頻道成員變更 |
| 9 | GUILD_MESSAGES | 頻道訊息（私域需審核） |
| 10 | GUILD_MESSAGE_REACTIONS | 頻道訊息表態 |
| 12 | DIRECT_MESSAGE | 頻道私信 |
| 24 | GROUP_MEMBER | 群成員變更（**v5 新增**） |
| 25 | GROUP_AND_C2C_EVENT | 群@訊息與私聊訊息 |
| 26 | INTERACTION | 交互事件（按鈕等） |
| 27 | MESSAGE_AUDIT | 消息審核事件 |
| 28 | FORUMS_EVENT | 論壇事件（僅私域） |
| 29 | AUDIO_ACTION | 音頻操作 |
| 30 | PUBLIC_GUILD_MESSAGES | 頻道訊息（公域） |

```toml
# 兩種寫法等價
intents = "[0, 9, 12, 25, 26, 27]"
intents = '["GUILDS", "GUILD_MESSAGES", "DIRECT_MESSAGE", "GROUP_AND_C2C_EVENT", "INTERACTION", "MESSAGE_AUDIT"]'
```

## 標準化對齊

本節說明適配器與 ErisPulse 標準化規範對齊的行為。規範詳情參見 SDK 文件《請求操作規範》（`docs/zh-TW/standards/request-action-spec.md`）與《API 回應規範》（`docs/zh-TW/standards/api-response.md`）。

### 錯誤碼規範化（5.3.x）

- **平台錯誤統一 34100**：QQ 官方 API 回傳錯誤時回傳 `retcode=34100`，原始回應（含官方 `code`/`message`）保留在 `qqbot_raw` 字段（媒體上傳失敗同樣使用 34100）
- **超時 33001**：API 調用超時回傳 `retcode=33001`（原 32000 不再使用）
- **撤回上下文缺失 10003**：`delete_message` 未找到訊息歸屬上下文時回傳 `retcode=10003`（參數錯誤）
- **請求族保留 34001/34003**：請求不存在或已過期回傳 `34001`；請求上下文缺少路由參數回傳 `34003`

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 10001 | 參數缺失/端點為空 |
| 10002 | 不支援的動作 |
| 10003 | 無法確定發送目標/帳戶、撤回上下文缺失等參數錯誤 |
| 33000 | 網路/API 調用異常 |
| 33001 | 請求超時 |
| 34001 | 請求不存在或已過期（Request DSL） |
| 34003 | 請求上下文缺少路由參數（Request DSL） |
| 34100 | 平台業務錯誤（原始回應與官方 code 保留在 `qqbot_raw`） |

### 通知事件命名（5.3.x）

好友增刪通知事件統一為標準命名：

| 官方事件 | 轉換後 detail_type | 說明 |
|----------|-------------------|------|
| FRIEND_ADD | `friend_increase` | 好友新增（原 `friend_add` 已廢棄） |
| FRIEND_DEL | `friend_decrease` | 好友刪除（原 `friend_del` 已廢棄） |

### 請求上下文留存（5.3.2 起）

入群申請事件入口將 `request_id` 映射到申請上下文（群/申請人 openid）並快取（TTL 3600 秒、上限 512 條，請求處理成功後清除），執行審批時路由到 `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`。

### 擴展動作路由（5.3.x）

頻道成員權限查詢透過帶平台前綴的擴展動作提供：

```python
result = await qqbot.Api.call("qqbot.get_channel_member_permissions", channel_id="...", member_id="...")
```

### Stream 發送 read send_context

流式訊息（`.Stream()`）讀取 `send_context`：事件鏈內自動使用當前事件來源帳戶，顯式 `Using()` 指定的帳戶優先。

## 訊息發送

### 基礎發送

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

# 發送文字
await qqbot.Send.To("user", user_openid).Text("Hello World!")

# 群聊@訊息（自動使用 <qqbot-at-user id="x" /> 格式）
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@你")
await qqbot.Send.To("group", group_openid).AtAll().Text("公告")

# 頻道訊息（@ 自動使用 <@user_id> 格式）
await qqbot.Send.To("channel", channel_id).Text("頻道訊息")

# 頻道私信（先建立會話）
dms = await qqbot.create_dms(user_id, source_guild_id)
await qqbot.Send.To("dms", dms["data"]["guild_id"]).Text("私信")

# 回覆訊息（被動回覆，自動攜帶 msg_id）
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("回覆內容")

# 多帳戶（Using/Account 指定帳戶名或 bot_id）
await qqbot.Send.Using("account2").To("group", group_openid).Text("來自第二個機器人")
```

### 富媒體

```python
# URL / 本地路徑 / 二進制三態支援；超過5MB自動分片上傳
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")
await qqbot.Send.To("user", uid).Image("/path/to/local.png")
await qqbot.Send.To("user", uid).Voice(open("audio.mp3", "rb").read())
await qqbot.Send.To("user", uid).Video("https://example.com/v.mp4")
await qqbot.Send.To("user", uid).File(b"...", filename="doc.pdf")

# 頻道圖片走 multipart 直傳（file_image）
await qqbot.Send.To("channel", cid).Image(open("img.png", "rb").read())
```

`file_type` 映射：圖片=1、影片=2、語音=3、文件=4（按訊息段類型自動判定，`file` 段按副檔名推斷）。

### Markdown / Ark / Embed / Keyboard

```python
# 原生 Markdown
await qqbot.Send.To("group", gid).Markdown("# 标題\n- 列表項")

# 模板 Markdown
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "通知"}])
await qqbot.Send.To("user", uid).Markdown(custom_template_id="23456", kv=[...])

# Ark 模板
await qqbot.Send.To("user", uid).Ark(23, [{"key": "a", "value": "b"}])

# Embed（僅頻道/頻道私信）
await qqbot.Send.To("channel", cid).Embed({"title": "標題", "content": "內容"})

# 鍵盤（自動置為 markdown 類型並附帶 bot_appid）
keyboard = {"content": {"rows": [[{"label": "確認", "type": 2, "data": "ok"}]]}}
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("請選擇")

# 合併轉發（官方 md 無摺疊語法，渲染為引用列表；需原生 Markdown 權限，失敗自動回退純文字）
await qqbot.Send.To("group", gid).MergeForward(nodes)
```

### 流式訊息（v5 新增，單聊）

```python
# 一次性流式發送（input_state=10 直接完成）
await qqbot.Send.To("user", openid).Stream("回答內容")

# 多輪追加流式
r = await qqbot.stream_message(openid, "第一段", input_state=1, msg_id=被動msg_id)
stream_id = r["data"]["id"]
r = await qqbot.stream_message(openid, "第二段", stream_msg_id=stream_id, index=1, input_state=1)
r = await qqbot.stream_message(openid, "最後一段", stream_msg_id=stream_id, index=2, input_state=10)
```

### 撤回訊息

```python
# 標準 Api 動作：自動按訊息來源（群/私聊/頻道/私信）路由到對應撤回端點
await qqbot.Api.delete_message(message_id)
```

適配器自動登記收發訊息的歸屬目標，無需手動傳入 group_id/channel_id；上下文缺失時回傳 `retcode=10003`。

## OneBot12 標準Api 動作（v5 新增）

```python
# 機器人資訊
result = await qqbot.Api.get_self_info()

# 群管理
result = await qqbot.Api.get_group_info(group_openid)          # {group_id, group_name}
result = await qqbot.Api.get_group_member_list(group_openid)   # 自動分頁聚合
result = await qqbot.Api.get_group_member_info(group_openid, member_openid)

# 頻道
result = await qqbot.Api.get_guild_list()
result = await qqbot.Api.get_guild_info(guild_id)
result = await qqbot.Api.get_guild_member_list(guild_id)
result = await qqbot.Api.get_channel_list(guild_id)
result = await qqbot.Api.get_channel_info(guild_id, channel_id)
await qqbot.Api.set_channel_name(guild_id, channel_id, "新名稱")
await qqbot.Api.leave_channel(guild_id, channel_id)            # 刪除子頻道

# 元動作
result = await qqbot.Api.get_status()   # {"good": bool, "bots": [...]}
result = await qqbot.Api.get_version()  # {"impl": "ErisPulse-QQBotAdapter", "onebot_version": "12"}

# 多帳戶
result = await qqbot.Api.Using("account2").get_self_info()
```

支援的標準動作：`get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`。不支援的動作回傳 `retcode=10002`（如 `get_friend_list`，QQ 官方無對應介面）。

## 請求操作（Request DSL，v5 新增）

`GROUP_JOIN_REQUEST`（入群申請）事件轉換為一對一互動的 `request` 事件，支援標準化審批：

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join_request(event):
    if event.get("platform") != "qqbot":
        return
    # 自動審批通過
    result = await event.approve()
    # 或拒絕：await event.reject(comment="不符條件")
    # 或指定帳戶：await qqbot.Request(event["request_id"]).Using("account2").accept()
```

- `request_id` = 官方 `join_request_id`
- 適配器自動快取申請上下文（群/申請人 openid），執行時路由到 `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`
- 拒絕可附 `reject_reason`；上下文過期回傳 `retcode=34001`

也可以直接調用平台方法：

```python
await qqbot.approve_group_join(group_openid, member_openid, join_request_id, approve=True)
await qqbot.approve_group_join(group_openid, member_openid, approve=False, reject_reason="理由")
```

## 平台原生API 方法族

適配器暴露完整 QQ 官方 API（第一個參數多為目標 ID，`account_id` 可選指定帳戶）：

### 機器人 / 互動
`get_me()`、`reply_interaction(interaction_id, code=0)`

### 頻道（Guild）
`get_guilds()`、`get_guild(guild_id)`、`mute_guild_all(guild_id, mute_seconds)`、
`get_guild_roles` / `create_guild_role` / `update_guild_role` / `delete_guild_role`、
`get_guild_api_permission`、`demand_guild_api_permission(guild_id, channel_id, path, method, desc)`

### 子頻道（Channel）
`get_channels`、`get_channel`、`create_channel(guild_id, name, type=0, ...)`、`update_channel(channel_id, name=..., ...)`、`delete_channel`、
`get_channel_pins`、`pin_message`、`unpin_message`

### 頻道成員
`get_guild_members`、`get_guild_member`、`mute_guild_members`（批量/全頻道）、`mute_guild_member`、
`add_guild_member_role` / `remove_guild_member_role`、`kick_guild_member`

### 權限 / 公告 / 表態
`get_channel_role_permissions`、`update_channel_role_permissions`、`get_channel_member_permissions`（擴展動作 `qqbot.get_channel_member_permissions`）、`update_channel_member_permissions`、`create_announce`、
`add_reaction`、`delete_reaction`、`get_reaction_users`

### 日程 / 帖子 / 音頻
`get_schedules`、`get_schedule`、`create_schedule`、`update_schedule`、`delete_schedule`、
`get_threads`、`get_thread`、`publish_thread(channel_id, title, content, format=3)`、`delete_thread`、
`control_audio(channel_id, audio_url, text, status)`、`mic_online`、`mic_offline`

### 群管理（v2，**部分介面僅白名單機器人開放**）
```python
await qqbot.get_group_info_raw(group_openid)          # 群資訊
await qqbot.get_group_bot_state(group_openid)         # 機器人在群狀態
await qqbot.get_group_members(group_openid)           # 成員列表（含 next_cursor）
await qqbot.get_group_member(group_openid, member_openid)
await qqbot.batch_remove_group_members(group_openid, [member_openid], add_to_blacklist=False)
await qqbot.get_group_member_blacklist(group_openid)
await qqbot.update_group_member_blacklist(group_openid, "add", [member_openid])
await qqbot.get_group_join_requests(group_openid)     # 入群申請列表
await qqbot.approve_group_join(...)                   # 審批入群
await qqbot.get_group_restrict_setting(group_openid)  # 禁言設定
await qqbot.set_group_restrict(group_openid, [{"op": "add", "member_openid": "...", "mute_expire_at": 123}])
# 入群審批策略
await qqbot.get_join_approval_strategies()
await qqbot.create_join_approval_strategy(strategy_dict)
await qqbot.update_join_approval_strategy(strategy_id, **fields)
await qqbot.delete_join_approval_strategy(strategy_id)
await qqbot.execute_join_approval_strategy(strategy_id)
await qqbot.update_join_approval_strategy_whitelist(strategy_id, "add", [user_ids])
```

### 自訂選單 / 指令面板（v5 新增）
```python
# 全域自訂選單（僅 C2C 生效；子選單最多5項不可嵌套）
menu_items = [
    {"type": "send_message", "content": {"label": "幫助", "content": "/help"}},
    {"type": "link", "content": {"label": "官網", "content": "https://example.com"}},
]
await qqbot.update_custom_menu(menu_items)
result = await qqbot.get_custom_menu()

# 指令面板（scope: c2c/group/channel/dm；每機器人最多20個）
await qqbot.create_command_panel("c2c", [
    {"type": "command", "content": {"label": "查詢天氣", "content": "/weather"}},
    {"type": "link", "content": {"label": "更多", "content": "https://example.com"}},
], remark="面板備註", target_type="all")
await qqbot.get_command_panels("c2c")
await qqbot.get_command_panel(panel_id)
await qqbot.update_command_panel(panel_id, items)
await qqbot.delete_command_panel(panel_id)
await qqbot.update_command_panel_targets(panel_id, "add", user_openids=[...])
```

## WebSocket 連線

### 連線流程

1. appId + clientSecret 取得 access_token（`POST https://bots.qq.com/app/getAppAccessToken`）
2. 透過 `GET /gateway/bot` 動態取得網關位址（設定 `gateway_url` 時直接使用）
3. 收到 OP_HELLO（op=10），取得心跳間隔
4. 發送 OP_IDENTIFY（op=2）鑑權（intents 支援位運算組合）
5. 收到 READY，取得 session_id 與 bot_id，發送 connect meta 事件
6. 心跳循環（op=1）與事件分發（op=0）

### 斷線重連

- 最大重連 50 次，指數退避 `min(5 * 2^n, 300)` 秒
- 收到 OP_RECONNECT（op=7）保留會話（Resume）；OP_INVALID_SESSION（op=9）重新 Identify
- 收發正常時自動重置重連計數

### Token 管理

- access_token 有效期 7200 秒，**提前 45 秒自動刷新**（請求時懶惰檢查）
- 刷新失敗自動重試 3 次（遞增延遲）
- 請求頭：`Authorization: QQBot {token}` + **`X-Union-Appid: {appid}`**（v5 新增）

## Webhook 接入（v5 新增）

將帳戶 `mode` 設為 `webhook` 即可改用 HTTP 回調接收事件：

```toml
[QQBot_Adapter.accounts.mybot]
appid = "..."
secret = "..."
mode = "webhook"
webhook_path = "/webhook"    # 多 webhook 帳戶自動追加帳戶名避免衝突
```

- 適配器透過 ErisPulse router 註冊 HTTP 路由，啟動日誌會輸出完整回調位址
- **Ed25519 驗簽**：種子 = secret 循環填補至 32 位元組；驗證 `X-Signature-Ed25519` 對 `X-Signature-Timestamp + body` 的簽名
- 自動處理 op=13 簽名驗證握手（回調位址配置校驗）與 op=0 事件分發
- 依賴 `cryptography` 庫（已隨適配器安裝）

## 事件訂閱與 openid 體系

1. QQBot 使用 openid 體系而非QQ號，使用者/群標識均為 openid 字串
2. 群訊息預設僅在使用者@機器人時收到（`GROUP_AT_MESSAGE_CREATE`）
3. **接收全部群訊息**：需在 [QQ開放平台](https://q.qq.com/) 機器人管理後台開啟相應權限（無API可設定）；開通後非@群訊息以 `GROUP_MESSAGE_CREATE` 推送，適配器已完整支援轉換（標記 `qqbot_is_at_message=false`；若訊息中含@機器人標記則自動識別為@訊息）
4. **@檢測**：QQ 的"被@"由事件名承載，且群訊息 @ 標記為 `<@{群空間openid}>`（與 READY bot_id 不同 id 體系）。適配器自動解析兩種標記風格並注入/歸一化機器人 mention 段，保證 `on_at_message()`/`is_at_message()` 可用；同時自動學習機器人在各群的 openid，使"接收全部群訊息"模式下的 `GROUP_MESSAGE_CREATE` 中@訊息也能被識別（原始 openid 保留在 mention 段 `data.qqbot_openid`）
5. 被動回覆：群/私聊訊息需攜帶 `msg_id` 或 `event_id`，適配器自動快取並附加
6. `event_id` 不能與富媒體混發（官方限制），適配器自動降級處理
7. 發送可能觸發審核，結果透過 `qqbot_audit_pass` / `qqbot_audit_reject` 事件通知
8. 程式退出調用 `shutdown()` 釋放資源

## 使用範例

### 處理群訊息（@檢測）

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

### 處理按鈕互動

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("detail_type") != "qqbot_interaction":
        return
    button_id = event.get("qqbot_button_id")
    await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
    if button_id == "確認":
        await qqbot.Send.To("group", event.get("group_id")).Text("已確認")
```

### 多帳戶啟動

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

兩個帳戶並行啟動：bot_a 走 WebSocket，bot_b 走 Webhook，互不影響。