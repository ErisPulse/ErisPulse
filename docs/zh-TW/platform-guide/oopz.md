# Oopz 平台特性文檔

## 文件資訊

| 項目 | 內容 |
|---|---|
| 模組版本 | 0.1.0 |
| 平台標識 | `oopz` |
| 維護者 | ErisPulse 團隊 |
| 最後更新 | 2026-11-11 |

> ⚠️ Oopz 無官方機器人平台，本轉接器基於社群逆向協定以**使用者帳號身份**接入，非官方介面隨時可能失效，請使用小號。詳見 README 風險聲明。

## 基本資訊

- 適配器類別：`OopzAdapter`（entry-point `oopz`）
- 接入方式：WebSocket（`wss://ws.oopz.cn`）+ REST 閘道（`https://gateway.oopz.cn`），RSA 簽名請求標頭 + JWT
- 憑證：「帳密二選一」——`password`（手機號碼+密碼+用戶端私鑰，自動登入續期）或 `token`（uid/JWT/device_id/私鑰四件套）
- 多帳戶：支援（`[Oopz_Adapter.accounts.<name>]`），事件 `self.account_id` 標記來源
- 框架軟依賴：ErisPulse ≥ 2.7.1

## 會話模型

| ErisPulse 目標 | Oopz 概念 | 說明 |
|---|---|---|
| `Send.To("group", <頻道ID>)` | 頻道（channel） | 域由適配器經「channel→area 快取 + 已加入域掃描」自動解析 |
| `Send.To("user", <對方UID>)` | 私信會話 | 自動 `PATCH /client/v1/chat/v1/to` 開會話並快取 sessionId |
| `guild_id` 欄位 / guild 語義 | 域（area） | 域級操作走 `get_guild_*` 與 `oopz.*` 管理擴充 |

## 標準化對齊（0.1.0）

### 錯誤碼規範

| retcode | 含義 |
|---|---|
| 0 | 成功 |
| 10002 | 不支援的動作/訊息段降級（語音影片檔案傳送、upload_file、keyboard 等） |
| 10003 | 參數缺失/不合法（如頻道無法定位所屬域） |
| 33001 | 網路異常/限流（429 尊重 Retry-After 重試一次） |
| 34100 | 平台回傳失敗（原始回應在 `oopz_raw`） |
| 34005 | 帳戶未解析（未設定或未建立工作階段） |

### 回應結構

所有回應包含 `status / retcode / data / message_id / message / oopz_raw`；傳送回應的 `message_id` 取自平台回傳的 `messageId`；`data.self_info.user_id` 在 `get_self_info` 中回填。

### 事件欄位完備性

- 所有事件必備 `id / time / type / detail_type / sub_type / platform / self`，且 `oopz_raw` + `oopz_raw_type` 永遠存在
- 訊息事件頂層必帶 `message_id`；時間戳微秒字串統一歸一為秒
- 事件 `id` 以帳戶域去重（`<account>:<類型>:<平台ID>`）
- 未知事件轉為 `type="unknown"` + `warning`，不靜默丟棄
- 協定內部幀（握手/認證/心跳/訂閱）不產生平台事件

### 降級語義

- `voice/audio/video/file` 傳送段 → `retcode=10002`（平台僅支援圖片上傳），不拋出例外
- `guild` 傳送目標 → `retcode=10003`（請指定頻道）
- token 模式 JWT 失效 → `retcode=34100` 提示更新憑證；password 模式自動重新登入後重試一次

## 支援的訊息發送類型

| 方法 | 平台實作 |
|---|---|
| `Text` | 文字（text/content 雙寫） |
| `Image` | COS 簽名票上傳（僅圖片），文字佔位符 `![IMAGEw{w}h{h}]({fileKey})` + attachments |
| `At / AtAll / Reply` | `mentionList` / `isMentionAll` / `referenceMessageId` |
| `Important()` 修飾符 | `styleTags=["IMPORTANT"]` 公告樣式 |
| `Recall(messageId)` | `recallGim`（頻道）/ `recallIm`（私訊，僅撤回自己發的） |
| `Raw_ob12` | OneBot12 段 → 平台 payload（text/mention/mention_all/reply/image；其餘段降級 10002） |
| Voice/Video/File/Keyboard | 不支援 → 10002 |

## 標準 API 動作（ApiDSL）

### 支援的標準動作

`get_self_info`、`get_user_info`、`get_friend_list`、`get_group_info`（頻道+所屬域合併資訊）、`get_group_list`（已加入域的頻道扁平表）、`get_guild_info`、`get_guild_list`、`get_channel_list`、`get_guild_members`、`delete_message`（需 `channel_id` 或 `user_id` 上下文）、`get_file`（附件 URL → base64）、`leave_guild`、`get_status`、`get_version`、`get_supported_actions`

### 不支援的標準動作（retcode=10002）

`send_message`（走 Send DSL）、`upload_file`、`get_latest_events`、`set_group_name`、`set_group_admin`、`set_group_leave`、`set_group_card`、`leave_group`、`leave_channel`

### 平台擴充動作（oopz.*）

| 動作 | 必填參數 | 說明 |
|---|---|---|
| `oopz.create_channel` | `area_id, name` | 可選 `channel_type/group_id/secret/max_member` |
| `oopz.delete_channel` | `area_id, channel_id` | |
| `oopz.mute_member` / `oopz.unmute_member` | `area_id, user_id` | 禁言，`duration` 分鐘數自動吸附檔位（5分鐘/1小時/1天/3天/7天） |
| `oopz.mute_mic` / `oopz.unmute_mic` | `area_id, user_id` | 禁麥 |
| `oopz.kick_member` | `area_id, user_id` | 移出域 |
| `oopz.block_user` / `oopz.unblock_user` | `area_id, user_id` | 域黑名單 |
| `oopz.get_area_members` | `area_id` | 可選 `offset_start/offset_end` |
| `oopz.get_assignable_roles` | `area_id, target_id` | 可分配身分組 |
| `oopz.assign_role` / `oopz.revoke_role` | `area_id, target_id, role_id` | 內部讀全量角色後整體提交 |
| `oopz.react_message` / `oopz.unreact_message` | `message_id, channel_id, emoji` | 可選 `user_id`（私訊）/`area_id` |
| `oopz.get_reactions` | `message_id` | 可選 `message_ids`（≤50）/`user_id` |
| `oopz.get_reaction_persons` | `message_id, channel_id, emoji` | 回應者分頁 |
| `oopz.top_message` | `message_id, area_id, channel_id` | 置頂/取消（`cancel=True`） |
| `oopz.get_history_messages` | `area_id, channel_id` | 可選 `size`（預設 50） |
| `oopz.get_friend_requests` | — | 好友申請列表 |
| `oopz.respond_friend_request` | `target, friend_request_id, agree` | 審批（一般用 Request DSL） |

## 好友申請處理

- 事件：`request/friend`，`request_id` 為**無狀態複合鍵** `<target>:<friendRequestId>`
- `event.approve()` / `event.reject()` → POST `/client/v1/friendship/v1/response`
- 單端點同構，無需請求類型上下文留存表

## 發送方法返回值

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "14283..."},
  "message_id": "14283...",
  "message": "",
  "oopz_raw": {"messageId": "14283...", "timestamp": "..."}
}
```

## 特有事件類型

- 訊息事件擴充欄位：`oopz_area_id`、`guild_id`（頻道訊息）；`oopz_reference_message_id`（回覆）
- 通知擴充：`oopz_edited_text`、`oopz_emoji`、`oopz_reaction_type`、`oopz_persons`、`oopz_from_channel`、`oopz_channel_name`、`oopz_channel_type`、`oopz_area_name`、`oopz_role_id`、`oopz_role_name`、`oopz_ban_until`、`oopz_login_state`
- `EventMixin` 便捷方法：`get_raw_event()`、`get_area_id()`、`get_edited_text()`、`get_emoji()`、`get_reaction_type()`、`get_voice_persons()`