---
name: erispulse-adapter-standards
description: "适用于：实现/评审适配器时需要对照的硬性技术规范。覆盖场景：當你開發新適配器，或要為某個平台新增能力、需要決定「進標準還是走 `{platform}_` 擴充」、命名怎麼起、平台差異怎麼處理時先讀本文。只是查某一領域的具體規範，可直接跳到 §2 標準地圖對應的文件。**何時需要閱讀本文**：當你在適配器中將平台原生會話映射到標準類型（private/group/channel/guild/thread），或在模組中不確定 `Send.To()` 應傳入什麼目標類型、想釐清 `event.reply()` 的自動轉換時對照本文。不需要則跳過。**什麼時候需要閱讀本文**：當你在適配器中將平台原生事件轉換為 OneBot12 標準事件時——確認必須欄位、訊息段結構、擴展欄位命名（`{platform}_` 前綴）、會話類型推斷時對照本文。不需要則跳過。當你在適配器中實現 Send 類別——方法命名、媒體參數（URL/路徑/bytes）的形態支援、`Raw_ob12` 反向轉換、合併轉發能力時對照本文。不需要則跳過。當你在適配器中實作 Api DSL 標準動作（get_user_info / delete_message 等），或在模組中跨平台呼叫這些標準動作、需要確認參數與 data 字段時對照本文。不需要則跳過。當你在轉接器中實作 `call_api` / Send / Request 的回傳值，需要確認回應結構與回傳碼是否符合 ErisPulse 標準，或排查某個 `retcode` 的含義時對照本文。不需要則跳過。**什麼時候需要閱讀本文**：當你的適配器需要處理好友請求/群邀請（轉換請求事件、實現 `accept`/`reject`），或模組中要用 `event.approve()` / `event.reject()` 審批請求時對照本文。不需要則跳過。"
---

# ErisPulse 适配器技术标准

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 标准化总纲

> 来源: `docs/zh-TW/standards/standardization-guide.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/standards/standardization-guide.md）

# 適配器標準化指南（總綱）

> [!TIP]
> **什麼時候需要讀這篇**：當你開發新適配器，或要為某個平台新增能力、需要決定「進標準還是走 `{platform}_` 擴充」、命名怎麼起、平台差異怎麼處理時先讀本文。只是查某一領域的具體規範，可直接跳到 §2 標準地圖對應的文件。

本文件是 ErisPulse 適配器標準化的**總綱**：確立跨平台標準化的原則、標準地圖、
差異處理模式、新能力進入標準的流程，並給出**互動元件標準**（按鈕/鍵盤、下拉選擇等）
與**互動回呼事件**的完整定義。任何適配器開發者在實作新功能時應**優先採用標準定義**，
使模組開發者用同一份程式碼在任意平台獲得一致的體驗——命名一致、參數一致、回傳一致。

---

## 1. 標準化原則

1. **命名一致**：同一概念在所有平台使用同一命名（如撤回統一 `delete_message`，
   按鈕段統一 `keyboard`），不因平台而異
2. **參數一致**：標準動作/段/方法的參數結構在所有平台保持一致；平台特有參數
   以**可選擴充參數**或**擴充欄位**提供，不污染標準簽名
3. **回傳一致**：所有 API/發送呼叫回傳標準回應結構（`status/retcode/data/message_id/message`），
   `data` 內的標準欄位（如 `user_id/user_name`）語義一致；平台原始資料放 `{platform}_raw`
4. **擴充有據**：平台特有能力按 `{platform}_` 前綴命名（段：`yunhu_form`；
   動作：`yunhu.board`；事件欄位：`qqbot_button_id`），明確標識非跨平台
5. **差異在適配器層吸收**：模組程式碼面向標準編程，平台差異由適配器轉換
   （參數映射、欄位標準化、能力降級），不要求模組寫平台分支
6. **能力降級不報錯**：平台不支援某標準能力時，優雅降級（回傳 `retcode=10002`、
   元件文字化進 `alt_message`），不擲出例外中斷模組邏輯

## 2. 標準地圖

| 領域 | 標準文件 | 涵蓋內容 |
|------|---------|---------|
| 事件轉換 | [事件轉換標準](event-conversion.md) | 事件結構、標準訊息段（text/image/mention/reply/keyboard 等）、平台擴充段規範 |
| 互動元件 | **本文件 §5** | 按鈕/鍵盤、下拉選擇、卡片、互動回呼事件標準欄位、修飾器約定、各平台映射 |
| API 動作 | [API 動作標準](api-action-spec.md) | OneBot12 標準動作（使用者/群組/頻道/訊息管理/元動作）的統一介面與 `ApiDSL` |
| 請求操作 | [請求操作規範](request-action-spec.md) | 請求事件欄位（request_id）與 Request DSL（approve/reject） |
| 發送方法 | [發送方法規範](send-method-spec.md) | Send 類別方法命名、參數、修飾器、反向轉換（OB12→平台） |
| 會話類型 | [會話類型標準](session-types.md) | user/group/channel/guild/dms 等會話類型定義與映射 |
| API 回應 | [API 回應標準](api-response.md) | 標準回應結構與 retcode 約定 |

## 3. 標準化工作流程（新能力如何進入標準）

```
平台特有能力（{platform}_ 前綴）
        │  ≥2 個平台出現同類能力
        ▼
識別共性（抽取通用概念與參數子集）
        │
        ▼
標準草案（命名 + 參數 + 回傳 + 各平台映射表）
        │  評審
        ▼
寫入本總綱/各領域標準文件 + 框架基類/適配器實作相容層
        │
        ▼
標準段/動作（無前綴）——模組可跨平台使用
```

**範例**：按鈕最初各平台獨立實作（`telegram_inline_keyboard` / 雲湖 buttons /
QQBot keyboard）→ 出現在 ≥3 個平台 → 抽取通用結構（`label/type/data` + rows）
→ 發布標準 `keyboard` 段 → 各適配器實作相容層（修飾器接受通用結構 + 標準段轉換 + 原生段透傳）。

### 3.1 命名規則

| 對象 | 規則 | 範例 |
|------|------|------|
| 標準訊息段 | 小寫，通用概念無前綴 | `keyboard`、`select`、`mention` |
| 平台擴充段 | `{platform}_` 前綴 | `telegram_sticker`、`yunhu_form` |
| 標準Api動作 | OB12 標準名（snake_case） | `get_group_info`、`delete_message` |
| 平台擴充動作 | `{platform}.` 前綴或協定通用名 | `yunhu.board`、`send_poke`（OB11 擴充） |
| 修飾器 | PascalCase，通用能力進框架基類 | `.Keyboard(rows)`、`.At(uid)` |
| 事件標準欄位 | 通用概念無前綴 | `interaction_id`、`button_data`、`request_id` |
| 事件平台欄位 | `{platform}_` 前綴 | `qqbot_event_id`、`telegram_chat_id` |

### 3.2 參數與回傳規則

- 標準參數在所有平台**同名同義**；單位/格式在標準文件中明確（如秒級時間戳、字串ID）
- 必填參數取各平台能力的**公共子集**；平台增強能力為可選參數
- 平台強約束（如 QQBot 富媒體不能與 event_id 混發）由適配器自動處理/降級，不暴露給模組
- 回傳 `data` 的標準欄位全平台一致；平台額外資訊放 `data` 內平台命名欄位或 `{platform}_raw`

## 4. 差異處理模式（適配器層）

| 模式 | 說明 | 範例 |
|------|------|------|
| **參數映射** | 標準參數 → 平台原生參數 | `delete_message(message_id)` → TG `deleteMessage(chat_id, message_id)`（登記表補全 chat_id） |
| **結構轉換** | 標準段 → 平台原生結構 | `keyboard` 段 → `inline_keyboard` / buttons / QQBot keyboard |
| **動作映射** | 標準動作名 → 平台動作名 | `get_self_info` → `get_login_info`（OB11） |
| **欄位標準化** | 平台回應 → 標準欄位 | `getMe()` → `{user_id, user_name, user_displayname}` |
| **合成標識** | 平台無原生標識時生成確定性ID | TG join request 無ID → `tjr_{chat}_{user}_{date}` |
| **能力降級** | 不支援時文字化/回傳10002 | Kook 無 keyboard → alt_message 文字化；`get_friend_list` → 10002 |
| **歸一化** | 平台髒資料 → 標準格式 | QQBot @標記 openid → bot_id（名稱歸一化） |
| **雙軌相容** | 標準結構與平台原生結構同時接受 | `.Keyboard()` 接受通用 rows 或原生結構 |

---

## 5. 互動元件標準

### 5.1 元件清單與狀態

| 元件 | 標準段 type | 狀態 | 已支援平台 |
|------|------------|------|-----------|
| 按鈕/鍵盤（keyboard） | `keyboard` | ✅ 已標準化 | Telegram / 雲湖 / QQBot |
| 下拉選擇（select） | `select` | 📋 預留（結構見 §5.4） | Discord / Telegram(bot) |
| 卡片（card） | `card` | 📋 預留（見 §5.5） | Kook / 雲湖 |
| 模態框（modal） | `modal` | 📋 預留 | Discord |

> 修飾器層級約定：通用互動元件的 Send 修飾器由**適配器 Send 類別實作**（框架基類
> 不內建），命名遵循 §5.2 約定，參數遵循本文件標準結構。

### 5.2 keyboard 按鈕/內聯鍵盤

#### 訊息段結構（發送方向）

標準 `keyboard` 段 = `rows` 二維陣列，每個按鈕為
`{"label": "顯示文字", "type": "callback" | "link", "data": "回呼資料或跳轉地址"}`，
另允許平台特有可選欄位（適配器按能力映射或忽略）。

> **結構定義權威**：完整的訊息段 JSON、欄位表與欄位語義見
> [事件轉換標準 §4.1.1 keyboard 按鈕/內聯鍵盤段](event-conversion.md#411-keyboard-按鈕內聯鍵盤段跨平台通用)，
> 本節不重複。

#### 各平台映射對照

| 平台 | 標準段 → 原生結構 | 原生結構參考 |
|------|------------------|-------------|
| Telegram | `reply_markup.inline_keyboard`：`[{text, callback_data \| url}]` | callback→`callback_data`（≤64位元組），link→`url` |
| 雲湖 | `content.buttons`：`[{label, action_type}]` | callback→`action_type:2` + `action` + `value`，link→`action_type:1` + `url` |
| QQBot | `keyboard.content.rows`：`[{label, type, data}]` | callback→`type:2` + `data`，link→`type:0` + `data`（訊息須為 markdown 類型） |
| Kook | 卡片 `action-group` 模組：`[{type, text, value, click}]` | callback→`click:return` + `value`，link→`click:link` + `url` |
| Discord | `components[].components`：`[{label, style, custom_id \| url}]` | callback→`style:1` + `custom_id`，link→`style:5` + `url` |

#### Send 修飾器（各適配器 Send 類別實作）

通用修飾器由**各適配器在自己的 Send 類別中實作**（不修改框架基類）：

- `.Keyboard(rows)`：標準命名，接受 §5.2 通用 rows 結構，內部生成標準 `keyboard`
  訊息段（或直接轉換為平台原生結構），由 `Raw_ob12` 統一處理
- `.Buttons(rows)`：可選語義別名，行為一致
- **向後相容**：偵測到平台原生結構時直接透傳（不報錯、不轉換）
- 平台原生擴充段（如 `telegram_inline_keyboard`）繼續透傳，不受影響

```python
# 同一份程式碼，任意平台（各適配器提供修飾器與轉換）
rows = [[{"label": "讚", "type": "callback", "data": "like:1"},
         {"label": "主頁", "type": "link", "data": "https://example.com"}]]
await adapter.Send.To("group", gid).Keyboard(rows).Text("請選擇")
```

> 適配器相容清單：QQBot / Telegram / 雲湖 已實作（修飾器 + 標準段轉換）；
> 新適配器按本文件實作即可（見 §7 Checklist）。

### 5.3 互動回呼事件（點擊按鈕之後）

使用者點擊按鈕後，平台推送的事件**必須**提供以下標準欄位（detail_type 可保留平台命名）：

| 標準欄位 | 類型 | 必填 | 說明 |
|---------|------|------|------|
| `interaction_id` | str | 是 | 本次互動的ID（可用於回應，如轉圈/提示） |
| `button_data` | str | 是 | 按鈕回傳資料（即 §5.2 的 `data`） |
| `button_label` | str | 否 | 按鈕顯示文字 |
| `user_id` | str | 是 | 點擊者 |
| `message_id` | str | 否 | 按鈕所在訊息 |
| `group_id` / `channel_id` | str | 否 | 來源會話 |

**detail_type 約定**：保留各平台現有命名（`qqbot_interaction` / `telegram_callback_query` /
`yunhu_a2ui_button` 等），但**標準欄位必須齊備**——模組用 `event.get("button_data")` 即可跨平台取值。

**Event 擴充方法建議**（適配器 EventMixin 提供）：

```python
def get_button_data(self) -> str: ...     # button_data
def get_interaction_id(self) -> str: ...  # interaction_id
```

**回應互動**（按平台能力）：`adapter.reply_interaction(interaction_id, code=0)`（QQBot）/
`answerCallbackQuery`（Telegram）等，命名跟隨平台方法族，不強制統一。

#### 各平台回呼事件映射

| 平台 | 原生事件 | detail_type | interaction_id 來源 | button_data 來源 |
|------|---------|-------------|--------------------|-----------------|
| Telegram | `callback_query` | `telegram_callback_query`（notice） | `callback_query.id` | `callback_query.data` |
| 雲湖 | 按鈕點擊事件 | `yunhu_button_click` / `yunhu_a2ui_button` | `buttonId` / `sourceComponentId` | `value` / `actionName` |
| QQBot | `INTERACTION_CREATE` | `qqbot_interaction` | `interaction.id` | `data.resolved.button_data` |
| Kook | 按鈕 點擊事件 | `kook_button_click` | `msg_id`+`value` | `value` |
| Discord | `INTERACTION_CREATE` | `discord_interaction` | `interaction.id` | `data.custom_id` |

### 5.4 select 下拉選擇（預留）

```json
{
  "type": "select",
  "data": {
    "placeholder": "請選擇",
    "options": [
      {"label": "選項A", "data": "opt:A"},
      {"label": "選項B", "data": "opt:B"}
    ],
    "min_values": 1,
    "max_values": 1
  }
}
```

回呼事件複用 §5.3 欄位（`button_data` = 所選 `data`，多選時為 JSON 陣列）。
首批實作平台：Discord（select menu）、Telegram（keyboard 切換）。未實作平台收到該段
應在 `alt_message` 中降級為文字清單。

### 5.5 card 卡片（預留，暫緩標準化）

卡片結構差異極大（Kook 全功能卡片模組 vs 雲湖 html vs QQ markdown+keyboard），
暫不做強標準。建議：

- 富文字卡片用 `text` + `keyboard` 組合表達（多數場景足夠）
- 平台全功能卡片繼續用 `{platform}_card` 擴充段（如 `kook_card`）
- 待出現 ≥2 個平台的同構卡片能力再評審提升

---

## 6. 未來候選（Roadmap）

以下能力已在 ≥2 平台出現或預期出現，按優先級推進標準化：

| 候選 | 涉及平台 | 優先級 | 備註 |
|------|---------|--------|------|
| select 下拉選擇 | Discord / Telegram | 高 | 結構草案見 §5.4 |
| 表態/表情回應（reactions） | QQBot / Telegram / Discord / Kook | 高 | 動作 + 事件兩側標準化 |
| 群管理動作（禁言/踢人/審批） | QQBot / 雲湖 / OB11 | 高 | 多數已實作為平台動作，待抽取標準簽名 |
| 公告/看板 | 雲湖 / Telegram / Discord | 中 | `set_announcement` 類動作 |
| 檔案資源模型（file_id 兩段式） | 各平台 | 低（暫緩） | 發送直傳 `SendDSL.File(file, filename)` 已是標準路徑（URL/路徑/bytes 直傳，見[發送方法規範 §2.1](send-method-spec.md)）；file_id 模型僅當後端天然具備時透傳，見 [API 動作標準 §3.5](api-action-spec.md) |
| 卡片 card | Kook / 雲湖 | 低 | 結構差異大，見 §5.5 |
| 表單 form | 雲湖 | 低 | 平台特有，保持 `{platform}_` 前綴 |
| 媒體轉碼/大小偵測 | 各平台 | 低 | 適配器內部實作，不對外標準化 |

## 7. 新適配器開發者的標準 Checklist

開發新適配器時，按此清單對照實作（★ 為必須，其餘建議）：

- [ ] ★ 事件轉換為 OneBot12 標準結構，繼承 `BaseConverter`
- [ ] ★ 標準訊息段收發支援（text/image/mention/reply/keyboard…；媒體段按
      [發送方法規範 §2.1](send-method-spec.md) 的形態分級與降級階梯處理）
- [ ] ★ 實作 `Raw_ob12`（含標準段 → 平台結構轉換；標準 `keyboard` 段必做）
- [ ] ★ 回傳標準回應結構（`make_response`/`make_error`）
- [ ] ★ 多帳戶：`AccountConfigClass(BotAccountConfig)` + `_resolve_account`
- [ ] ★ Send 類別繼承 `BaseAdapter.Send`，用 `_apply_modifiers`/`send_context`
- [ ] ☆ Api DSL：標準動作映射到平台API（見 API 動作標準）
- [ ] ☆ Request DSL：請求事件含 `request_id` + `accept/reject`
- [ ] ☆ 互動元件：`keyboard` 段轉換 + 互動回呼標準欄位 + `.Keyboard()`/`.Buttons()` 修飾器（適配器 Send 類別實作）
- [ ] ☆ EventMixin：`get_raw_event()` / `get_button_data()` 等平台擴充方法
- [ ] ☆ 生命週期任務用 `runtime.spawn_background`
- [ ] ☆ 設定讀取用 `self.cfg`
- [ ] ☆ 框架軟依賴：不宣告 ErisPulse 硬依賴 + 執行時版本偵測
- [ ] ☆ i18n：設定欄位與日誌多語言
- [ ] ☆ platform-guide 平台文件 + 適配器儲存庫 platform-features.md

## 8. 相關文件

- 各領域標準見 §2 標準地圖
- 框架內建適配器可作參考實作：QQBot（v5 範式全量）、OneBot11（Api DSL 映射）、雲湖（BaseConverter + Web API 擴充）

## 会话类型

> 来源: `docs/zh-TW/standards/session-types.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/standards/session-types.md）

# ErisPulse 會話類型標準

> [!TIP]
> **何時需要閱讀本文**：當你在適配器中將平台原生會話映射到標準類型（private/group/channel/guild/thread），或在模組中不確定 `Send.To()` 應傳入什麼目標類型、想釐清 `event.reply()` 的自動轉換時對照本文。不需要則跳過。

本文檔定義了 ErisPulse 支援的會話類型標準，包括接收事件類型和發送目標類型。

## 1. 核心概念

### 1.1 接收類型 && 發送類型

ErisPulse 區分兩種會話類型：

- **接收類型（Receive Type）**：用於接收的事件的 `detail_type` 欄位
- **發送類型（Send Type）**：用於發送訊息時 `Send.To()` 方法的目標類型

### 1.2 類型對應關係

```
接收類型 (detail_type)     發送類型 (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**關鍵點**：
- `private` 是接收時的類型，發送時的標準類型是 `user`
- `group`、`channel`、`guild`、`thread` 在接收和發送時類型相同
- **推薦路徑**：直接使用 `event.reply()`——自動完成類型轉換與目標推斷，無需手動處理（`private` → `user` 的自動轉換即在此發生）
- **手動發送時**：請直接傳發送類型（如 `Send.To("user", ...)`）；手動 `Send.To("private", ...)` 傳接收類型雖也能被自動轉換，但不推薦（見 §6.1）

## 2. 標準會話類型

### 2.1 OneBot12 標準類型

#### private
- **接收類型**：`private`
- **發送類型**：`user`
- **說明**：一對一私聊訊息
- **ID 欄位**：`user_id`
- **適用平台**：所有支援私聊的平台

#### group
- **接收類型**：`group`
- **發送類型**：`group`
- **說明**：群聊訊息，包括各種形式的群組（如 Telegram supergroup）
- **ID 欄位**：`group_id`
- **適用平台**：所有支援群聊的平台

#### user
- **接收類型**：`user`
- **發送類型**：`user`
- **說明**：使用者類型，某些平台（如 Telegram）將私聊表示為 user 而非 private
- **ID 欄位**：`user_id`
- **適用平台**：Telegram 等平台

### 2.2 ErisPulse 擴展類型

#### channel
- **接收類型**：`channel`
- **發送類型**：`channel`
- **說明**：頻道訊息，支援多個使用者的廣播式訊息
- **ID 欄位**：`channel_id`
- **適用平台**：Discord, Telegram, Line 等

#### guild
- **接收類型**：`guild`
- **發送類型**：`guild`
- **說明**：伺服器/社群訊息，通常用於 Discord Guild 級別的事件
- **ID 欄位**：`guild_id`
- **適用平台**：Discord 等

#### thread
- **接收類型**：`thread`
- **發送類型**：`thread`
- **說明**：主題/子頻道訊息，用於社群中的子討論區
- **ID 欄位**：`thread_id`
- **適用平台**：Discord Threads, Telegram Topics 等

## 3. 平台類型映射

### 3.1 映射原則

適配器負責將平台的原生類型映射到 ErisPulse 標準類型：

```
平台原生類型 → ErisPulse 標準類型 → 發送類型
```

### 3.2 常見平台映射示例

#### Telegram
```
Telegram 類型          ErisPulse 接收類型    發送類型
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group
supergroup             group                   group  # 映射到 group
channel                channel                 channel
```

#### Discord
```
Discord 類型          ErisPulse 接收類型    發送類型
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
OneBot11 類型        ErisPulse 接收類型    發送類型
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # 映射到 group
```

## 4. 自訂類型擴展

### 4.1 註冊自訂類型

適配器可以註冊自訂會話類型：

```python
from ErisPulse.Core.Event import register_custom_type

# 註冊自訂類型
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 使用自訂類型

註冊後，系統會自動處理該類型的轉換和推斷：

```python
# 自動推斷
receive_type = infer_receive_type(event, platform="MyPlatform")
# 返回: "my_custom_type"

# 轉換為發送類型
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# 返回: "custom"

# 獲取對應ID
target_id = get_target_id(event, platform="MyPlatform")
# 返回: event["custom_id"]
```

### 4.3 解除註冊自訂類型

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. 自動類型推斷

當事件沒有明確的 `detail_type` 欄位時，系統會根據存在的 ID 欄位自動推斷類型：

> [!NOTE]  
> **2.7.0+ 行為變更**：`detail_type` 只有在是**已知會話類型**（標準或自定義）時才直接採用。notice/request 事件的 `detail_type`（如 `group_member_increase`、`friend_increase`）是**語義子類型**而非會話類型，會轉而根據 ID 欄位推斷正確的會話類型。

### 5.1 推斷優先級

```
優先級（從高到低）：
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 使用範例

```python
# 事件只有 group_id
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# 返回: "group"（優先使用 group_id）

# 事件只有 user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# 返回: "private"

# notice 事件的 detail_type 是語義子類型，2.7.0+ 會從 ID 欄位推斷
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# 返回: "group"（而非 "group_member_increase"）
```

## 6. API 使用示例

### 6.1 發送訊息

```python
from ErisPulse import adapter

# 發送給使用者
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# 發送給群組
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# 自動轉換 private → user：手動傳遞接收類型屬不推薦寫法（可能有相容性問題）
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# 內部自動轉換為: Send.To("user", "789")
# 推薦做法：手動發送時直接用發送類型 user，或用 event.reply() 自動完成轉換（見 6.2）
```

### 6.2 事件回覆

```python
from ErisPulse.Core.Event import Event

# Event.reply() 自動處理類型轉換（推薦路徑）
await event.reply("回覆內容")
# 內部自動使用正確的發送類型（private → user 等轉換在此自動完成）
```

### 6.3 命令處理

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # 系統自動處理會話類型
    # 無需手動判斷 group_id 還是 user_id
    await event.reply("命令執行成功")
```

## 7. 核心 API 參考

### 7.1 類型轉換

```python
from ErisPulse.Core.Event import convert_to_send_type, convert_to_receive_type

# 接收類型 → 發送類型
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# 發送類型 → 接收類型
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### 7.2 ID 欄位查詢

```python
from ErisPulse.Core.Event import get_id_field, get_receive_type

get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 7.3 一步獲取發送資訊

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# 直接用於 Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 獲取目標 ID

```python
from ErisPulse.Core.Event import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 8. 工具方法

```python
from ErisPulse.Core.Event import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

is_standard_type("private")     # True
is_standard_type("custom_type") # False

is_valid_send_type("user")      # True
is_valid_send_type("invalid")   # False

get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

clear_custom_types()                # 清除所有
clear_custom_types(platform="discord")  # 只清除指定平台的
```

## 9. 最佳實踐

### 7.1 適配器開發者

1. **使用標準映射**：盡可能映射到標準類型，而不是創建新類型
2. **正確轉換**：確保接收類型和發送類型的映射關係正確
3. **保留原始數據**：在 `{platform}_raw` 中保留原始事件類型
4. **文檔說明**：在適配器文檔中說明類型映射關係

### 7.2 模塊開發者

1. **使用工具方法**：使用 `get_send_type_and_target_id()` 等工具方法
2. **避免硬編碼**：不要寫 `if group_id else "private"` 這樣的代碼
3. **考慮所有類型**：代碼要支持所有標準類型，不僅僅是 private/group
4. **靈活設計**：使用事件包裝器的方法，而不是直接訪問字段

### 7.3 類型推斷

- **優先使用 detail_type**：如果有明確字段，不進行推斷
- **合理使用推斷**：只有在沒有明確類型時才使用
- **注意優先級**：了解推斷優先級，避免意外結果

## 10. 常見問題

### Q1: 為什麼發送時 private 要轉換為 user？

A: 這是 OneBot12 標準的要求。`private` 是接收時的概念，發送時使用 `user` 更符合語義。

### Q2: 如何支援新的會話類型？

A: 透過 `register_custom_type()` 註冊自定義類型，或直接使用標準類型中的 `channel`、`guild` 等。

### Q3: 事件沒有 detail_type 怎麼辦？

A: 系統會根據存在的 ID 欄位自動推斷。優先級為：group > channel > guild > thread > user。

### Q4: 適配器如何映射 Telegram supergroup？

A: 在適配器的轉換邏輯中，將 `supergroup` 映射為標準的 `group` 類型。

### Q5: 郵箱等特殊平台如何處理？

A: 對於不通用或平台特有的類型，使用 `{platform}_raw` 和 `{platform}_raw_type` 保留原始數據，適配器自行處理。

## 11. 相關文件

**適配器側（映射與轉換）**：
- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範
- [發送方法規範](send-method-spec.md) - Send 類的方法命名和參數規範
- [適配器開發指南](../developer-guide/adapters/) - 適配器開發完整指南

**模組側（不想手動處理類型轉換）**：
- 使用 `event.reply()` 即可自動完成類型轉換與目標推斷，詳見 [Event 包裝類詳解](../developer-guide/modules/event-wrapper.md)

## 事件转换

> 来源: `docs/zh-TW/standards/event-conversion.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/standards/event-conversion.md）

# 適配器標準化轉換規範

> [!TIP]
> **什麼時候需要閱讀本文**：當你在適配器中將平台原生事件轉換為 OneBot12 標準事件時——確認必須欄位、訊息段結構、擴展欄位命名（`{platform}_` 前綴）、會話類型推斷時對照本文。不需要則跳過。

## 1. 核心原則
1. 嚴格相容：所有標準欄位必須完全遵循 OneBot12 規範
2. 明確擴展：平台特有的功能必須添加 {platform}_ 前綴（例如 yunhu_form）
3. 數據完整：原始事件數據必須保留在 {platform}_raw 欄位中，原始事件類型必須保留在 {platform}_raw_type 欄位中
4. 時間統一：所有時間戳必須轉換為 10 位 Unix 時間戳（秒級）
5. 平台統一：platform 項命名必須與你在 ErisPulse 中註冊的名稱/別稱一致

## 2. 標準字段要求

### 2.1 必須字段
| 字段 | 類型 | 說明 |
|------|------|------|
| id | string | 事件唯一標識符 |
| time | integer | Unix時間戳（秒級） |
| type | string | 事件類型 |
| detail_type | string | 事件詳細類型（詳見[會話類型標準](session-types.md)） |
| platform | string | 平台名稱 |
| self | object | 机器人自身資訊 |
| self.platform | string | 平台名稱 |
| self.user_id | string | 机器人用戶ID |

**detail_type 規範**：
- 必須使用 ErisPulse 標準會話類型（詳見 [會話類型標準](session-types.md)）
- 支援的類型：`private`, `group`, `user`, `channel`, `guild`, `thread`
- 适配器負責將平台原生類型映射到標準類型

### 2.2 消息事件字段
| 字段 | 類型 | 說明 |
|------|------|------|
| message | array | 消息段陣列 |
| alt_message | string | 消息段備用文字 |
| user_id | string | 用戶ID |
| user_nickname | string | 用戶暱稱（可選） |

### 2.3 通知事件字段
| 字段 | 類型 | 說明 |
|------|------|------|
| user_id | string | 用戶ID |
| user_nickname | string | 用戶暱稱（可選） |
| operator_id | string | 操作者ID（可選） |

### 2.4 請求事件字段
| 字段 | 類型 | 說明 |
|------|------|------|
| user_id | string | 用戶ID |
| user_nickname | string | 用戶暱稱（可選） |
| comment | string | 請求附言（可選） |
| request_id | string | 請求標識符（**強烈推薦**，用於同意/拒絕請求操作） |

**`request_id` 字段說明**：
- `request_id` 是請求事件的唯一操作標識符，用於透過 `HandleRequest` DSL 執行同意/拒絕操作
- 适配器在轉換請求事件時，應將平台原生的請求標識映射到此字段
- 如果平台本身沒有請求ID，适配器應產生一個唯一標識（例如基於時間戳+用戶ID的雜湊）
- 當 `request_id` 缺失時，`event.approve()` / `event.reject()` 將拋出 `ValueError`

## 3. 事件格式示例

### 3.1 消息事件 (message)
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽獎 超級大獎"
      }
    }
  ],
  "alt_message": "抽獎 超級大獎",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽獎",
    "args": "超級大獎"
  }
}
```

### 3.2 通知事件 (notice)
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 請求事件 (request)
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "請加好友",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. 消息段標準

### 4.1 標準消息段

標準消息段**不需要**平台前綴。

| 類型 | 說明 | data 字段 |
|------|------|----------|
| `text` | 純文本 | `text: str` |
| `image` | 圖片 | `file`, `url: str` |
| `audio` | 音頻 | `file`, `url: str` |
| `video` | 視頻 | `file`, `url: str` |
| `file` | 文件 | `file`, `url: str`, `filename: str` |
| `mention` | @用戶 | `user_id: str`, `user_name: str` |
| `reply` | 回覆 | `message_id: str` |
| `face` | 表情 | `id: str` |
| `location` | 位置 | `latitude: float`, `longitude: float` |
| `keyboard` | 按鈕/內聯鍵盤 | `rows: list[list[button]]`（見 4.1.1） |

**媒體段 `file` 字段格式**（發送方向，`image` / `audio` / `video` / `file` 通用）：

| 形態 | 示例 | 适配器要求 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/a.png` | **必須**接受 |
| 本地文件路徑 | `/tmp/a.png`、`C:\tmp\a.png` | **必須**接受 |
| 二進制數據 | `bytes` | **必須**接受 |
| `file://` URI / Base64 / Data URI | `file:///tmp/a.png`、`data:image/png;base64,...` | **應當**接受 |

> 完整的媒體發送協議（形態判定順序、文件名推導、能力降級階梯）見
> [發送方法規範 §2.1](send-method-spec.md#21-媒體消息發送協議image--voice--video--file)。

**字段方向語義**：

- `file`：**發送方向**的內容來源（上述形態）；**接收方向**由适配器填平台可取回的形態
  （通常為可下載 URL，或 `get_file` 類動作可用的資源標識）
- `url`：接收方向的平台回鏈（适配器轉換平台事件時盡可能填入，供模塊直接取用）；發送方向可不填
- `filename`：`file` 段的文件名（發送方向可選，缺省時适配器按
  [發送方法規範 §2.1.3](send-method-spec.md) 的推導順序生成；接收方向**應當**填平台原始文件名）

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard 按鈕/內聯鍵盤段（跨平台通用）

按鈕/內聯鍵盤在多個平台（Telegram / 云湖 / QQBot / Kook / Discord 等）均有對應能力，
屬於**跨平台通用概念**，因此作為標準消息段（無平台前綴）。适配器應將標準段轉換為
平台原生結構；平台原生擴展段（如 `telegram_inline_keyboard`）繼續保留透傳。

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "選項A", "type": "callback", "data": "vote:A"},
        {"label": "官網",   "type": "link",     "data": "https://example.com"}
      ]
    ]
  }
}
```

**字段說明：**

| 字段 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `rows` | 二維數組 | 是 | 每個子數組為一行按鈕 |
| `rows[][].label` | str | 是 | 按鈕顯示文本 |
| `rows[][].type` | str | 是 | `callback`（點擊回傳數據）/ `link`（跳轉URL） |
| `rows[][].data` | str | 是 | 回調數據（type=callback）或跳轉地址（type=link） |
| `rows[][].*` | Any | 否 | 平台特有可選字段（如 `web_app`、`menus`），适配器按能力映射或忽略 |

**适配器轉換參考**（完整映射與交互回調事件標準見 [跨平台交互組件標準](standardization-guide.md)）：

| 平台 | 標準段 → 平台原生 |
|------|------------------|
| Telegram | `inline_keyboard`：`[{text, callback_data \| url}]` |
| 云湖 | `buttons`：`[{label, action_type: 2=回調 \| 1=跳轉, ...}]` |
| QQBot | `keyboard.content.rows`：`[{label, type: 2=回調 \| 0=跳轉, data}]`（需 markdown 類型消息） |
| Kook | 卡片 action-group 模塊 |
| Discord | components：`action_row` + `buttons`（custom_id/url） |

### 4.2 平台擴展消息段

平台特有的消息段需要添加平台前綴：

```json
// 云湖 - 表單
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "報名表"}}

// Telegram - 貼紙
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**擴展消息段要求**：
1. **data 內部字段不加前綴**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` 而非 `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **提供降級方案**：模塊可能不識別擴展消息段，适配器應在 `alt_message` 中提供文本替代
3. **文檔完備**：每個擴展消息段必須在适配器文檔中說明 `type`、`data` 結構和使用場景

## 5. 未知事件處理

對於無法識別的事件類型，應產生警告事件：
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "不支援的事件類型: special_event",
  "alt_message": "此事件類型不受此系統支援。"
}
```
---

## 6. 擴展命名規範

### 6.1 欄位命名

**規則**：`{platform}_{field_name}`

```
平台前綴    欄位名            完整欄位名
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**要求**：
- `platform` 必須與適配器註冊時的平台名完全一致（大小寫敏感）
- `field_name` 使用 `snake_case` 命名
- 禁止使用雙下劃線 `__` 開頭（Python 保留）
- 禁止與標準欄位同名（如 `type`、`time`、`message` 等）

### 6.2 消息段類型命名

**規則**：`{platform}_{segment_type}`

標準消息段類型（`text`、`image`、`audio`、`video`、`mention`、`reply` 等）**不得**添加平台前綴。只有平台特有的消息段類型才需要添加前綴。

### 6.3 原始數據欄位命名

以下欄位名是**保留欄位**，所有適配器必須遵循：

| 保留欄位 | 類型 | 說明 |
|---------|------|------|
| `{platform}_raw` | `any` | 平台原始事件數據的完整副本 |
| `{platform}_raw_type` | `string` | 平台原始事件類型標識 |

**要求**：
- `{platform}_raw` 必須是原始數據的深拷貝，而非引用
- `{platform}_raw_type` 必須是字串，即使平台使用數字類型也要轉換為字串
- 這兩個欄位在所有事件中**必須存在**（無法獲取時為 `null` 和空字串 `""`）

### 6.4 平台特有欄位示例

```json
{
  "yunhu_command": {
    "name": "抽獎",
    "args": "超級大獎"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 嵌套擴展欄位

擴展欄位可以是簡單值，也可以是嵌套物件：

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**嵌套欄位要求**：
- 頂層鍵必須帶平台前綴
- 嵌套內部欄位**不添加**平台前綴
- 嵌套深度建議不超過 3 層

### 6.6 `self` 欄位擴展

`self` 物件的標準必選欄位（`platform`、`user_id`）見 §2.1，以下是 ErisPulse 擴展的可選欄位：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `self.user_name` | `string` | 機器人暱稱 |
| `self.avatar` | `string` | 機器人頭像 URL |
| `self.account_id` | `string` | 多帳戶模式下的帳戶標識 |

> **Bot 狀態追蹤**：適配器通過發送 `type: "meta"` 事件告知框架 Bot 的連接狀態。支援的 `detail_type`：`connect`（上線）、`heartbeat`（心跳）、`disconnect`（離線）。系統自動從中提取 `self` 欄位的 Bot 元資訊進行狀態追蹤。此外，普通事件中的 `self` 欄位也會自動發現 Bot。詳見 [適配器系統 API - Bot 狀態管理](../api-reference/adapter-system.md)。

## 7. 會話類型擴展

ErisPulse 在 OneBot12 標準的 `private`、`group` 基礎上擴展了以下會話類型：

| 類型 | OneBot12 標準 | ErisPulse 擴展 | 說明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 一對一私聊 |
| `group` | ✅ | — | 群聊 |
| `user` | — | ✅ | 用戶類型（Telegram 等） |
| `channel` | — | ✅ | 頻道（廣播式） |
| `guild` | — | ✅ | 伺服器/社群 |
| `thread` | — | ✅ | 話題/子頻道 |

**適配器自訂類型擴展**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# 在適配器啟動時註冊
register_custom_type(
    receive_type="email",      # 接收事件中的 detail_type
    send_type="email",         # 發送時的目標類型
    id_field="email_id",       # 對應的 ID 欄位名
    platform="email"           # 平台標識
)
```

**自訂類型要求**：
- 必須在適配器 `start()` 時註冊，在 `shutdown()` 時註銷
- `receive_type` 不應與標準類型重名
- `id_field` 應遵循 `{目標}_id` 的命名模式

> 完整的會話類型定義和映射關係參見 [會話類型標準](session-types.md)。

## 8. 模組開發者指南

### 8.1 訪問擴展字段

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # 訪問標準字段
    text = event.get_text()
    user_id = event.get_user_id()

    # 訪問平台擴展字段 - 方法1：直接 get
    yunhu_command = event.get("yunhu_command")

    # 訪問平台擴展字段 - 方法2：點式訪問（Event 包裝類）
    # event.yunhu_command

    # 訪問原始數據
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # 判斷平台
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 處理擴展消息段

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 最佳實踐

1. **優先使用標準字段**：不要假設擴展字段一定存在
2. **平台判斷**：通過 `event.get_platform()` 判斷平台，而非通過擴展字段是否存在來推斷
3. **優雅降級**：無法處理擴展消息段時，使用 `alt_message` 作為兜底
4. **不要硬編碼前綴**：使用 `platform` 變量動態拼接

```python
# ✅ 推薦
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 不推薦
raw_data = event.get("yunhu_raw")
```

### 8.4 請求事件處理

模組開發者可以透過 `event.approve()` 和 `event.reject()` 對請求事件進行操作：

```python
from ErisPulse.Core.Event import request

# 好友請求：自動同意
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # 同意請求
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"已同意 {user_name} 的好友請求")
    else:
        print(f"同意好友請求失敗: {result.get('message')}")

# 群邀請：根據條件決定
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # 拒絕請求
    result = await event.reject(comment="暫不加入新群")
```

**透過適配器直接操作**（適用於非事件處理器場景）：

```python
from ErisPulse import adapter

# 透過 request_id 直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# 指定 Bot 賬號操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# 附帶備註
await adapter.myplatform.Request("req_abc123").accept(comment="歡迎")
```

## 9. notice / request 事件的會話類型推斷

### 9.1 問題背景

notice 事件和 request 事件的 `detail_type` 是**語義子類型**（如 `group_member_increase`、`friend_increase`），而不是會話類型（如 `group`、`private`）。

```
type        detail_type                  含義            會話類型
────        ───────────                  ────            ────────
message     group                        群聊訊息         group（detail_type 即會話類型）
message     private                      私聊訊息         private（detail_type 即會話類型）
notice      group_member_increase        群成員增加       group（需從 group_id 推斷）
notice      friend_increase              好友增加         private（需從 user_id 推斷）
request     friend                       好友請求         private（需從 user_id 推斷）
request     group                        群請求           group（detail_type 即會話類型）
```

### 9.2 推斷規則

`infer_receive_type()` 的推斷順序：

1. 如果 `detail_type` 是已知會話類型（`private`/`group`/`channel`/`guild`/`thread`/`user`），直接使用
2. 如果 `detail_type` 是自定義會話類型，直接使用
3. 否則（notice/request 的語義子類型），根據 ID 字段推斷：
   - 有 `group_id` → `"group"`
   - 有 `channel_id` → `"channel"`
   - 有 `guild_id` → `"guild"`
   - 有 `thread_id` → `"thread"`
   - 有 `user_id` → `"private"`

### 9.3 `event.reply()` 目標推斷

notice/request 事件中 `event.reply()` 的發送目標由會話類型推斷決定：

- 群通知事件（含 `group_id`）→ 回覆到**群**
- 好友通知事件（僅含 `user_id`）→ 回覆到**用戶私聊**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() 發送到群（group/group_789）
    await event.reply("歡迎入群！")

    # 如需通知管理員（私聊），顯式指定目標：
    await adapter.Send.To("user", "admin_id").Text(f"新成員 {user_id} 加入了 {group_id}")
```

### 9.4 適配器開發建議

確保 notice/request 事件中包含正確的 ID 字段：

| detail_type | 必須包含的 ID 字段 | 推斷的會話類型 |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend`（請求） | `user_id` | `private` |
| `group`（請求） | `group_id` | `group` |

## 10. 相關文件

**實作轉換器時的對照表**：
- [會話類型標準](session-types.md) - 會話類型的定義和對應關係
- [API 回應標準](api-response.md) - 適配器 API 回應格式的標準

**同一適配器的發送端**：
- [發送方法規範](send-method-spec.md) - Send 類的方法命名、參數規範及反向轉換的要求
- [API 動作標準](api-action-spec.md) - OneBot12 標準 API 動作的統一介面

**查詢各平台已知的擴展事件與訊息段**：
- [各平台特性文件](../platform-guide/README.md) - 您可以訪問此文件來了解各個平台的特性以及已知的擴展事件和訊息段等。

## 发送方法规范

> 来源: `docs/zh-TW/standards/send-method-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/standards/send-method-spec.md）

# ErisPulse 發送方法規範

> [!TIP]
> **什麼時候需要讀這篇**：當你在適配器中實現 Send 類別——方法命名、媒體參數（URL/路徑/bytes）的形態支援、`Raw_ob12` 反向轉換、合併轉發能力時對照本文。不需要則跳過。

本文件定義了 ErisPulse 適配器中 Send 類別發送方法的命名規範、參數規範和反向轉換要求。

## 0. 關鍵詞約定

本文件中的 **必須（MUST）**、**應當（SHOULD）**、**可以（MAY）** 按以下語義解釋（參照 RFC 2119）：

| 關鍵詞 | 語義 | 違反後果 |
|--------|------|---------|
| **必須** | 強制要求，框架行為/跨平台一致性依賴它 | 適配器視為不符合標準，模組程式碼可能無法運作 |
| **應當** | 強烈建議；除非有充分理由，否則遵循 | 偏離時須在適配器文件中說明原因與替代行為 |
| **可以** | 可選項，按平台能力自行決定 | 無 |

## 1. 標準方法命名

所有發送方法使用 **大駝峰命名法**，首字母大寫。

### 1.1 標準發送方法

| 方法名 | 說明 | 參數類型 | 實現要求 |
|-------|------|---------|---------|
| `Text` | 發送文字訊息 | `str` | 必須 |
| `Image` | 發送圖片 | `str` \| `bytes` | 必須（基類已內建，見 §6.4） |
| `Voice` | 發送語音 | `str` \| `bytes` | 必須（基類已內建；平台不支援語音時按 §2.1.5 降級） |
| `Video` | 發送影片 | `str` \| `bytes` | 必須（基類已內建；平台不支援影片時按 §2.1.5 降級） |
| `File` | 發送檔案 | `str` \| `bytes`，`filename: str \| None = None` | 必須（基類已內建） |
| `At` | @使用者/群組 | `str` (user_id) | 修飾方法，按需 |
| `Face` | 發送表情 | `str` (emoji) | 可以 |
| `Reply` | 回覆訊息 | `str` (message_id) | 修飾方法，按需 |
| `Forward` | 轉發訊息 | `str` (message_id) | 可以 |
| `Markdown` | 發送 Markdown 訊息 | `str` | 可以 |
| `HTML` | 發送 HTML 訊息 | `str` | 可以 |
| `Card` | 發送卡片訊息 | `dict` | 可以 |

> 標準方法（`Text`/`Image`/`Voice`/`Video`/`File`）由基類 `SendDSL` 內建並預設委派 `Raw_ob12`，適配器**無需重複實現**即可獲得類型簽名；僅當平台需要特殊邏輯時才覆寫單一方法（見 §6.4）。

### 1.2 鏈式修飾方法

| 方法名 | 說明 | 參數類型 |
|-------|------|---------|
| `At` | @使用者（可多次呼叫） | `str` (user_id) |
| `AtAll` | @全體成員 | 無 |
| `Reply` | 回覆訊息 | `str` (message_id) |

### 1.3 協定方法

| 方法名 | 說明 | 是否必須 |
|-------|------|---------|
| `Raw_ob12` | 發送 OneBot12 格式訊息段 | 必須 |

**`Raw_ob12` 是必須實現的方法**。這是適配器的核心職責之一：接收 OneBot12 標準訊息段並將其轉換為平台原生 API 呼叫。`Raw_ob12` 是反向轉換（OneBot12 → 平台）的統一入口，確保模組可以不依賴平台特有方法，直接使用標準訊息段發送訊息。

**未覆寫 `Raw_ob12` 時的行為**：基類預設實現會記錄 **error 級別**日誌並回傳標準錯誤回應格式（`status: "failed"`, `retcode: 10002`），提示適配器開發者必須實現此方法。

### 1.4 建議的擴展命名約定

適配器如需支援發送非 OneBot12 格式的原始資料（如平台特定 JSON、XML 等），建議使用以下命名約定：

| 建議方法名 | 說明 |
|-----------|------|
| `Raw_json` | 發送任意 JSON 資料 |
| `Raw_xml` | 發送任意 XML 資料 |

**注意**：這些方法**不是**基類提供的預設方法，也不強制要求實現。它們僅作為命名約定，適配器可根據需要自行定義。如果適配器不支援這些格式，則無需定義。

**訊息建構器**：ErisPulse 提供了 `MessageBuilder` 工具類別，用於方便地建構 OneBot12 訊息段列表，配合 `Raw_ob12` 使用。詳見 [MessageBuilder 詳解](../advanced/message-builder.md)。

## 2. 參數規範詳解

### 2.1 媒體訊息發送協定（`Image` / `Voice` / `Video` / `File`）

本節是媒體發送的**統一協定標準**：模組以同一份程式碼呼叫四個媒體方法，適配器負責把
`file` 參數的各種形態轉換為平台原生上傳/發送行為。

#### 2.1.1 `file` 參數的合法形態

| 形態 | 範例 | 適配器要求 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **必須**接受 |
| 本機檔案路徑 | `/path/to/file.jpg`、`C:\path\to\file.jpg` | **必須**接受 |
| 二進位資料 | `b"\x89PNG..."` | **必須**接受 |
| `file://` URI | `file:///path/to/file.jpg` | **應當**接受（可轉為本機路徑處理） |
| Base64 字串 / Data URI | `iVBORw0KGgo=...`、`data:image/png;base64,...` | **應當**接受（與 OneBot12 生態慣例相容） |

> 適配器**必須**在三種必須形態上行為一致——模組無論傳 URL、路徑還是 bytes，
> 收到的都是同一條訊息。平台無法直接使用某形態時（如平台 API 不支援引用外部 URL），
> 由適配器自行下載/讀取後上傳，**不得**要求模組換形態重試。

#### 2.1.2 形態判定順序

適配器實現媒體參數處理時，**應當**按以下順序判定形態：

1. `bytes` 類型 → 直接上傳
2. 字串以 `http://` / `https://` 開頭 → 按 URL 處理（直接引用或下載後上傳，按平台能力）
3. 字串以 `file://` 開頭 → 剝離前綴按本機路徑處理
4. 其餘字串 → 按本機路徑處理（存在則讀取上傳；不存在則回傳標準錯誤回應）

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """形態判定與正規化（範例）"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # 平台不能引用 URL 時下載
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # 本機路徑
        return f.read()
```

#### 2.1.3 `File` 的檔案名稱語義

`File` 方法簽名：`File(file, filename=None)`（`filename` 為可選參數，基類已內建）。

檔案名稱**推導順序**（適配器在未顯式提供 `filename` 時按此生成）：

1. 顯式 `filename` 參數（最高優先）
2. URL 的 basename（如 `https://host/a/b/report.pdf` → `report.pdf`，須剝離 query string）
3. 本機路徑的 basename（如 `/tmp/data/backup.zip` → `backup.zip`）
4. 平台預設生成（如 `file_{timestamp}`；**應當**保留真實副檔名——副檔名影響平台側的
   類型識別與預覽行為）

> `Image` / `Voice` / `Video` 同樣**可以**接受 `filename`（經訊息段 `data.filename` 傳遞），
> 但僅 `File` 的檔案名稱有跨平台語義保證。

#### 2.1.4 平台限制的宣告義務

各平台對媒體的大小上限、格式（MIME）、時長（音訊/影片）等限制不同。適配器**應當**：

- 在適配器文件中宣告支援的媒體類型與限制範圍
- 超限或不支援的輸入回傳**標準錯誤回應**（`status: "failed"`；`retcode` 使用
  `10002` 或平台語義化錯誤碼，`message` 說明原因），**不得**拋出例外中斷模組邏輯

#### 2.1.5 能力降級階梯

平台不支援某個媒體**類型**時，按以下階梯降級（遵循總綱「能力降級不報錯」原則）：

| 情境 | 降級行為 |
|------|---------|
| `Voice` 不支援語音訊息 | **應當**按 `File`（或平台近緣形態）發送；無法表達時回傳 `retcode=10002` |
| `Video` 不支援影片訊息 | 同上 |
| 媒體類型完全不支援（無檔案能力） | 回傳 `retcode=10002`，`message` 註明不支援的資料類型 |
| 形態不支援（如無法處理 base64） | 回傳 `retcode=10002`，**可以**在 `message` 中提示模組改用 URL/bytes |

**禁止**的行為：靜默丟棄（無回傳）、拋出例外、要求模組撰寫平台分支處理。

### 2.2 @使用者參數規範

**方法：** `At`（修飾方法）

**參數：** `user_id` (`str`)

**要求：**
- `user_id` 應為字串類型的使用者識別碼
- 不同平台的 `user_id` 格式可能不同（數字、UUID、字串等）
- 適配器負責將 `user_id` 轉換為平台特定的格式
- 注意需要把真正的發送方法呼叫放在最後的位置

**範例：**
```python
# 單個 @ 使用者
Send.To("group", "g123").At("123456").Text("你好")

# 多個 @ 使用者（鏈式呼叫）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 回覆訊息參數規範

**方法：** `Reply`（修飾方法）

**參數：** `message_id` (`str`)

**要求：**
- `message_id` 應為字串類型的訊息識別碼
- 應為之前收到的訊息的 ID
- 某些平台可能不支援回覆功能，適配器應優雅降級

**範例：**
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

### 2.4 合併轉發能力（`MergeForward`，可選）

`MergeForward(nodes)` 是**可選的能力方法**：把多段內容打包為「合併轉發 / 富文本摺疊」形式發送，
由適配器按平台能力決定最佳呈現。與 §1.1 的 `Forward(from_chat_id, message_id)`（轉發**已有**訊息）
語義不同，二者並存。

> **標準背景**：OneBot12 核心標準沒有 node 訊息段，也沒有合併轉發 API——「訊息結點」是 OneBot v11
> 生態（go-cqhttp 擴展）的實現層概念，v12 把這類平台特有能力下放給擴展機制。ErisPulse 的落地方式
> 即擴展機制等價物：**不新增標準訊息段，而是可選能力方法 + `list_sends` 執行時探測**——實現了
> `MergeForward` 的適配器自動獲得能力，未實現的呼叫方自動回退普通文字，模組零改動。

**方法簽名：**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    發送合併轉發 / 富文本摺疊訊息

    :param nodes: 合併轉發節點陣列（go-cqhttp 擴展的 OneBot v11 節點格式）：
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # 展示用發送者 id
                    "nickname": "MyBot",     # 展示用發送者暱稱
                    "content": [            # 訊息段陣列，當前為 text 段
                        {"type": "text", "data": {"text": "【1/3】標題\n正文…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task，await 後回傳標準回應格式
    """
```

**實現要求：**

1. **平台有原生合併轉發**（OneBot11 系）：**必須**呼叫協定端專用端點
   （`send_group_forward_msg` / `send_private_forward_msg`）——NapCat 等實現會拒絕
   `send_msg` 攜帶的 node 段（retcode 1400）；專用端點失敗時**可以**回退 `send_msg` 直發 node 段
2. **平台無原生轉發但有富文本**（雲湖 / Telegram / Kook / Discord / Matrix 等）：
   **應當**將節點渲染為平台的富文本摺疊形態（HTML 摺疊卡 / Card / Embed / blockquote 列表），
   參考樣式與逐適配器任務清單見 `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`
3. **兩者皆無**：**不得**實現本方法（更不得回傳成功卻把 node 字典當純文字發出）——
   不實現時 `list_sends` 不含 `MergeForward`，呼叫方自動回退普通文字
4. **失敗語義**：回傳標準錯誤回應（`status: "failed"`）或拋出例外均可，呼叫方會回退純文字發送，內容不遺失
5. **不得**在 `MergeForward` 內部再呼叫 `Raw_ob12` 發送同樣的 nodes（OneBot11 的 `Raw_ob12`
   已內建純 node 段自動路由，會形成循環）
6. **出站 node 段解析**（全適配器約定）：各適配器的 `Raw_ob12` 段分發應註冊 `node` 段——
   純 node 列表自動路由到本適配器的合併轉發呈現（有 `MergeForward` 的平台等價於直接呼叫；
   無該方法的平台提取各節點文字以「暱稱: 正文」逐行**原文輸出**）；混合列表中 node 段的文字併入正文。
   任何適配器收到 node 段都不得靜默丟棄。

**平台實現形態（詳見 `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`）：**

- 原生端點：OneBot11、SnowLuma（三級回退：`send_group/private_forward_msg` 專用端點 → `upload_forward_msg`
  取 resid 發 forward 段 → 直發 node 段；SnowLuma API 全面向 NapCat 對齊，適配器可直接連接 NapCat 後端）
- 摺疊 HTML `<details>` 卡：雲湖（bot/使用者協定）、Email、Sandbox、Allons(Ideaura)
- 白名單 HTML / 引用區塊：Telegram（`<b>`+`<blockquote>`）、Matrix（blockquote 變體，白名單剝離 details/行內樣式）
- 平台卡片：Kook（Card header+section）、Discord（Embed fields）
- 官方 Markdown 引用列表：QQBot（官方 md 無摺疊語法，伺服器端驗證拒絕無效標籤 40034011）
- 不實現（node 段原文輸出降級）：OneBot12（標準無 node 段）、WeCom、Terminal、Webhook、WechatMp

**呼叫方探測範例：**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergeForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> 參考實現：`ErisPulse-OneBot11Adapter`（專用端點 → `send_msg` 回退）；渲染模板與各適配器任務清單見
> `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`。

## 3. 平台特有方法命名

**不建議**在 Send 類別中直接添加平台前綴方法。建議使用通用方法名或 `Raw_{協定}` 方法。

**不建議：**
```python
def YunhuForm(self, form_id: str):  # ❌ 不建議
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 不建議
    pass
```

**建議：**
```python
def Form(self, form_id: str):  # ✅ 通用方法名
    pass

def Sticker(self, sticker_id: str):  # ✅ 通用方法名
    pass

def Raw_ob12(self, message):  # ✅ 發送 OneBot12 格式
    pass
```

**擴展方法要求**：
- 方法名使用 PascalCase，不加平台前綴
- 必須回傳 `asyncio.Task` 物件
- 必須提供完整的類型註解和文件字串
- 參數設計應盡量與標準方法風格一致

## 4. 參數命名規範

| 參數名 | 說明 | 類型 |
|-------|------|------|
| `text` | 文字內容 | `str` |
| `file` | 媒體內容（URL / 路徑 / 二進位，見 §2.1.1） | `str` / `bytes` |
| `filename` | 檔案名稱（`File` 可選，見 §2.1.3） | `str` / `None` |
| `user_id` | 使用者 ID | `str` / `int` |
| `group_id` | 群組 ID | `str` / `int` |
| `message_id` | 訊息 ID | `str` |
| `data` | 資料物件（如卡片資料） | `dict` |

## 5. 回傳值規範

- **發送方法**（如 `Text`, `Image`）：必須回傳 `asyncio.Task` 物件
- **修飾方法**（如 `At`, `Reply`, `AtAll`）：必須回傳 `self` 以支援鏈式呼叫

---

## 6. 反向轉換規範（OneBot12 → 平台）

適配器不僅需要將平台原生事件轉換為 OneBot12 格式（正向轉換），還**必須**提供將 OneBot12 訊息段轉換回平台原生 API 呼叫的能力（反向轉換）。反向轉換的統一入口是 `Raw_ob12` 方法。

### 6.1 轉換模型

```
正向轉換（接收方向）                反向轉換（發送方向）
─────────────────                ─────────────────
平台原生事件                       OneBot12 訊息段列表
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12 標準事件                  平台原生 API 呼叫
（含 {platform}_raw）             （回傳標準回應格式）
```

**核心對稱性**：正向轉換保留原始資料在 `{platform}_raw` 中，反向轉換接受 OneBot12 標準格式並還原為平台呼叫。

### 6.2 `Raw_ob12` 實現規範

`Raw_ob12` 接收 OneBot12 標準訊息段列表，必須將其轉換為平台原生 API 呼叫。

**方法簽名**：

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    發送 OneBot12 標準訊息段

    :param message_segments: OneBot12 訊息段列表
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task，await 後回傳標準回應格式
    """
```

**實現要求**：

1. **必須處理所有標準訊息段類型**：至少支援 `text`、`image`、`audio`、`video`、`file`、`mention`、`reply`
2. **必須處理平台擴展訊息段**：對於 `{platform}_xxx` 類型的訊息段，轉換為平台對應的原生呼叫
3. **必須回傳標準回應格式**：遵循 [API 回應標準](api-response.md)
4. **不支援的訊息段應跳過並記錄警告**，不應拋出例外導致整條訊息發送失敗

### 6.3 訊息段轉換規則

#### 6.3.1 標準訊息段轉換

適配器必須實現以下標準訊息段的轉換：

| OneBot12 訊息段 | 轉換要求 |
|----------------|---------|
| `text` | 直接使用 `data.text` |
| `image` | `data.file` 按 §2.1 媒體協定處理（三必須形態 + 判定順序） |
| `audio` | 同 image 處理邏輯 |
| `video` | 同 image 處理邏輯 |
| `file` | 同 image 處理邏輯；檔案名稱按 §2.1.3 推導順序處理 `data.filename` |
| `mention` | 轉換為平台的 @使用者 機制（如 Telegram 的 `entities`，雲湖的 `at_uid`） |
| `reply` | 轉換為平台的回覆引用機制 |
| `face` | 轉換為平台的表情發送機制，不支援則跳過 |
| `location` | 轉換為平台的位置發送機制，不支援則跳過 |

#### 6.3.2 平台擴展訊息段轉換

對於帶平台前綴的訊息段，適配器應識別並轉換：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """將 OneBot12 訊息段轉換為平台原生格式"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # 平台擴展訊息段 → 平台原生呼叫
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 標準訊息段 → 平台等價操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知訊息段 → 記錄警告並跳過
            logger.warning(f"不支援的訊息段類型: {seg_type}")
```

#### 6.3.3 複合訊息段處理

一條訊息可能包含多個訊息段，適配器需要正確處理複合訊息：

```python
# 模組發送包含文字+圖片+@使用者 的訊息
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**處理策略**：
- **優先合併**：如果平台支援在一條訊息中同時包含文字、圖片、@等，應合併發送
- **退而拆分**：如果平台不支援合併，按順序拆分為多條訊息發送
- **保持順序**：訊息段的發送順序應與列表順序一致

### 6.4 `Raw_ob12` 與標準方法的關係

適配器的標準發送方法（`Text`、`Image` 等）**已由 `SendDSL` 基類內建實現並預設委派給 `Raw_ob12`**，適配器子類別無需重複實現：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """核心實現：OneBot12 訊息段 → 平台 API（必須實現）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File 已從基類繼承，自動委派 Raw_ob12
    # 如需平台特定邏輯，可覆寫單一方法：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**好處**：
- 轉換邏輯集中在 `Raw_ob12` 一處，減少重複程式碼
- 標準方法和 `Raw_ob12` 行為完全一致
- 模組無論使用 `Text()` 還是 `Raw_ob12()` 都能得到相同結果
- 基類提供類型簽名，IDE 能補全標準方法

### 6.5 實現範例

```python
class YunhuSend(SendDSL):
    """雲湖平台 Send 實現"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 訊息段 → 雲湖 API 呼叫"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """實際發送邏輯"""
        # 1. 解析修飾器狀態
        at_users = self._at_users or []
        reply_to = self._reply_to
        at_all = self._at_all
        
        # 2. 轉換訊息段
        yunhu_elements = []
        for seg in segments:
            seg_type = seg["type"]
            seg_data = seg["data"]
            
            if seg_type == "text":
                yunhu_elements.append({"type": "text", "content": seg_data["text"]})
            elif seg_type == "image":
                yunhu_elements.append({"type": "image", "url": seg_data["file"]})
            elif seg_type == "mention":
                at_users.append(seg_data["user_id"])
            elif seg_type == "reply":
                reply_to = seg_data["message_id"]
            elif seg_type == "yunhu_form":
                # 平台擴展訊息段
                yunhu_elements.append({"type": "form", "form_id": seg_data["form_id"]})
            else:
                logger.warning(f"雲湖不支援的訊息段: {seg_type}")
        
        # 3. 呼叫雲湖 API
        response = await self._call_yunhu_api(yunhu_elements, at_users, reply_to, at_all)
        
        # 4. 回傳標準回應格式
        return {
            "status": "ok" if response["code"] == 0 else "failed",
            "retcode": response["code"],
            "data": {"message_id": response.get("msg_id", ""), "time": int(time.time())},
            "message_id": response.get("msg_id", ""),
            "message": "",
            "yunhu_raw": response
        }
```

---

## 7. 方法發現

模組開發者可以透過 API 查詢適配器支援的發送方法（**不要**在模組中寫死某平台的方法
清單——各適配器的擴展方法隨版本演進，以執行時發現為準）：

```python
from ErisPulse import adapter

# 列出所有發送方法
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# 查看方法詳情
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "發送雲湖表單"
# }
```

---

## 9. 適配器開發注意事項

關於如何正確覆寫 `BaseAdapter`、`Send`、`Request` 的 `__init__`，詳見 [適配器開發入門 - `__init__` 注意事項](../developer-guide/adapters/getting-started.md#init-注意事項)。

---

---

## 10. 適配器實現檢查清單

### 發送方法
- [ ] 標準方法（`Text`, `Image` 等）已實現
- [ ] 回傳值均為 `asyncio.Task`
- [ ] 修飾方法（`At`, `Reply`, `AtAll`）回傳 `self`
- [ ] 平台擴展方法使用 PascalCase，無平台前綴
- [ ] 所有方法有完整的類型註解和文件字串

### 媒體發送協定
- [ ] `file` 參數**必須形態**全部支援：HTTP(S) URL / 本機路徑 / `bytes`（見 §2.1.1）
- [ ] 形態判定順序符合 §2.1.2（bytes → URL → `file://` → 路徑）
- [ ] `File` 的檔案名稱推導順序符合 §2.1.3（顯式 `filename` > URL basename > 路徑 basename > 平台預設）
- [ ] 平台的媒體限制（大小 / MIME / 時長）已在適配器文件宣告（§2.1.4）
- [ ] 不支援的媒體類型按 §2.1.5 降級階梯處理：近緣類型降級或回傳 `retcode=10002`，不拋例外、不靜默丟棄

### 合併轉發（可選，見 §2.4）
- [ ] 平台有原生合併轉發時，`MergeForward` 走協定專用端點，失敗回退 `send_msg`（OneBot11 系）
- [ ] 平台無原生轉發但有富文本時，`MergeForward` 渲染為平台摺疊形態（HTML 卡 / Card / Embed / blockquote）
- [ ] 兩者皆無時**不實現** `MergeForward`，不回傳成功卻發出 node 字典純文字
- [ ] `MergeForward` 內部不再呼叫 `Raw_ob12` 轉發同樣 nodes

### 反向轉換
- [ ] `Raw_ob12` **已實現**（必須，不可跳過）
- [ ] `Raw_ob12` 能處理所有標準訊息段（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）
- [ ] `Raw_ob12` 能處理平台擴展訊息段（`{platform}_xxx` 類型）
- [ ] 標準發送方法（`Text`, `Image` 等）內部委派給 `Raw_ob12`，而非獨立實現轉換邏輯
- [ ] 不支援的訊息段跳過並記錄警告，不拋出例外
- [ ] 複合訊息段正確處理（合併或按序拆分）

---

## 11. 訊息建構器——適配器側須知

`MessageBuilder` 是 ErisPulse 提供的 OneBot12 訊息段建構工具，供**模組側**建構訊息：
鏈式呼叫（或靜態快速建構）最終產出標準訊息段列表 `[{"type": ..., "data": ...}]`，
由呼叫方直接傳給 `Raw_ob12`。

**適配器側只需知道這一點**：`Raw_ob12` 接收到的就是這份產物——與手寫的訊息段列表
完全同構，按 §6.2 的段分發邏輯處理即可，無需感知它來自 MessageBuilder 還是字面值。

> 完整用法（雙模式機制、全部訊息段方法、`copy()` / `clear()` 工具方法與範例）見
> [MessageBuilder 詳解](../advanced/message-builder.md)，本篇不再重複。

---

## 12. 相關文件

**實現發送回傳值時配套對照**：
- [API 回應標準](api-response.md) - 適配器 API 回應格式標準

**同一適配器的其它側**：
- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範、擴展命名和訊息段標準
- [會話類型標準](session-types.md) - 會話類型定義和映射關係
- [請求操作規範](request-action-spec.md) - 請求事件欄位要求、HandleRequest DSL 及適配器實現要求

## API 动作规范

> 来源: `docs/zh-TW/standards/api-action-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/standards/api-action-spec.md）

# ErisPulse API 動作標準

> [!TIP]
> **什麼時候需要讀這篇**：當你在適配器中實作 Api DSL 標準動作（get_user_info / delete_message 等），或在模組中跨平台呼叫這些標準動作、需要確認參數與 data 字段時對照本文。不需要則跳過。

本文檔定義 ErisPulse 適配器中 **OneBot12 標準 API 動作**的統一介面規範，使模組開發者可以面向標準介面編程，由適配器負責映射到平台原生 API。

> **覆蓋範圍**：OneBot12 標準動作中，`ApiDSL` 提供使用者 / 群組 / 頻道（Guild）/
> 消息管理 / 元（Meta）常規介面的強類型方法（`send_message` 由
> `SendDSL.Raw_ob12` 承擔）。檔案資源動作（`upload_file` / `get_file` / 分片）僅作
> 降級透傳保留，見 §3.5 說明。平台擴展動作經 `Api.call("prefix.action", ...)`
> 逃生艙呼叫。動作參數與回傳結構以 OneBot12 規範（倉庫內 `onebot/specs/interface/`）為準。

## 1. 設計背景

在 ErisPulse 中，訊息段（訊息收發）和事件格式已經完全遵循 OneBot12 標準，但 **API 動作呼叫**（如獲取使用者資訊、獲取群列表、撤回訊息等）此前未統一——模組開發者必須為每個平台寫不同的 `call_api` 呼叫。

`ApiDSL` 透過提供強類型的標準動作方法，解決這一問題：

```
模組程式碼（跨平台統一）             適配器實作（平台特定）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  適配器 call_api / 覆蓋
adapter.Api.get_group_list()      →  適配器 call_api / 覆蓋
adapter.Api.delete_message("id")  →  適配器 call_api / 覆蓋
```

## 2. 三層 DSL 並行結構

ErisPulse 適配器有三個並行的 DSL 內部類，各司其職：

```
BaseAdapter
├── Send(SendDSL)       ← 消息發送（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← 請求操作（accept/reject）
└── Api(ApiDSL)          ← 標準 API 動作（使用者/群組/頻道/消息管理/檔案/元）★
```

| DSL | 職責 | 方法風格 | 回傳值 |
|-----|------|---------|--------|
| `Send` | 發送訊息 | 串流 + `asyncio.Task` | 標準回應 |
| `Request` | 處理請求事件 | `asyncio.Task` | 標準回應 |
| `Api` | 查詢/管理操作 | `async` 方法 | 標準回應 |

## 3. 標準動作列表

### 3.1 使用者相關

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | 無 | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | 無 | `list[get_user_info 回應]` |

### 3.2 群組相關

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | 無 | `list[get_group_info 回應]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info 回應]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | 無 |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | 無 |

### 3.3 消息管理

| 方法 | OB12 動作 | 參數 | 說明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | 撤回/刪除訊息 |

> **發送訊息**（`send_message`）由 `SendDSL` 的 `Raw_ob12` 處理，不在 `ApiDSL` 中重複。

### 3.4 頻道（Guild）相關

OneBot12 頻道體系分兩級：**頻道（guild）** 與 **子頻道（channel）**。

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | 無 | `list[get_guild_info 回應]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | 無 |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info 回應]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | 無 |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info 回應]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | 無 |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info 回應]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | 無 |

> 頻道體系與群組（group）彼此獨立：Discord / QQ 頻道 / Kook 等平台實作頻道介面，
> 傳統 QQ / 微信實作群組介面，兩者可同時存在或僅其一。

### 3.5 檔案資源操作

> [!WARNING]
> **檔案資源模型（file_id 兩段式）在 ErisPulse 屬"降級可用"**：
> ErisPulse 的檔案收發不走"先上傳拿 file_id 再引用"模型——模組發檔案用
> `SendDSL.File(file, filename)`（URL / 路徑 / 字節**發送時直傳**，見
> [發送方法規範](send-method-spec.md)）。
> 本節 `upload_file` / `get_file` / 分片動作依賴平台特有的 `file_id` 檔案資源
> 能力，**通用性不足**；僅當適配器後端天然具備該能力時才可透傳，框架內建
> 適配器**不實作也不建議實作**，呼叫時通常回傳 `retcode=10002`。
> 模組需要跨平台傳檔案時，請使用 `SendDSL.File`，勿依賴 file_id。
>
> **展望**：`file_id` 資源模型標準化到框架層是未來的方向，當前版本不提供。

整包傳輸（小檔案）：

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` 的 `type` 參數：
- `"url"`：透過 URL 上傳（需提供 `url`）
- `"path"`：透過本地路徑上傳（需提供 `path`）
- `"data"`：透過二進位資料上傳（需提供 `data`）

#### 3.5.1 分片傳輸（大檔案，屬上述降級範圍）

OneBot12 分片動作按 `stage` 區分階段。`ApiDSL` 將同一動作的三/兩階段拆分為獨立方法
（`offset` 為位元組偏移，`data` 在 JSON 中為 Base64）；下表僅為查閱保留，
適配器無需也不應強制實作：

**分片上傳三步**：`prepare` → `transfer`（循環逐片）→ `finish`

| 方法 | 對應 stage | 參數 | data 回傳 |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id`（傳輸期用） |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | 無 |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str`（整檔案校驗） | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**分片下載兩步**：`prepare` → `transfer`（循環取片）

| 方法 | 對應 stage | 參數 | data 回傳 |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data`（本次分片位元組） |

### 3.6 元（Meta）動作

元動作不針對具體帳號，無需 `Using()` 指定 Bot。

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | 事件物件陣列（不含元事件） |
| `get_supported_actions()` | `get_supported_actions` | 無 | `list[str]` 支援的動作名 |
| `get_status()` | `get_status` | 無 | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | 無 | `impl`, `version`, `onebot_version` |

### 3.7 通用擴展動作

| 方法 | 說明 |
|------|------|
| `call(action, **params)` | 平台擴展動作的逃生艙，遵循 OB12 擴展命名規則 `{prefix}.{action}` |

## 4. 使用方式

### 4.1 基本呼叫

```python
from ErisPulse import adapter

# 獲取使用者資訊（跨平台統一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"使用者名: {user_name}")

# 獲取群列表
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# 撤回訊息
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 指定 Bot 帳號（多帳戶模式）

```python
# 使用指定 Bot 帳號執行操作
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 平台擴展動作

```python
# 呼叫平台特有的擴展動作（建議使用 {prefix}.{action} 命名）
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 在事件處理器中使用

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # 獲取發送者詳細資訊
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"你好，{user_name}！")
```

## 5. 適配器實作

### 5.1 預設行為（零設定）

`ApiDSL` 的預設實作將標準動作名作為 `endpoint` 直接傳遞給 `adapter.call_api()`：

```python
# ApiDSL 預設實作等價於：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**適用場景**：當適配器的底層後端自身即遵循 OneBot12 標準動作協定時，
`call_api` 天然支援標準動作名（如直接對接遵循該協定的服務端）。

### 5.2 覆蓋標準方法（映射到平台原生 API）

適配器可覆蓋單個標準方法，將其映射到平台原生 API：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 標準 API 動作實作"""

        async def get_user_info(self, user_id: str) -> dict:
            # 映射到平台原生 API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                # 平台側錯誤：用 341xx～345xx 段自定義低三位（346xx 為框架保留，勿佔用）
                return self._adapter.make_error(retcode=34400, message="使用者不存在")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 未支援的動作

適配器未覆蓋的標準方法走預設實作（委派給 `call_api`）。如果 `call_api` 也不支援該動作，應回傳標準錯誤回應：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"不支援的動作: {endpoint}")
    # ... 平台 API 呼叫
```

模組開發者可透過回傳值的 `retcode` 判斷是否支援：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("該平台不支援獲取好友列表")
```

## 6. 回應格式

所有 `ApiDSL` 方法回傳標準 API 回應格式（詳見 [API 回應標準](api-response.md)）：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **注意**：資訊查詢類動作的 `message_id` 為空字串（僅訊息發送類動作才有 `message_id`）。

## 7. 與 SendDSL / RequestDSL 的關係

| 場景 | 使用 DSL | 範例 |
|------|---------|------|
| 發送訊息 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| 同意/拒絕請求 | `Request` | `adapter.Request("req_id").accept()` |
| 獲取使用者/群資訊 | `Api` | `adapter.Api.get_user_info("123")` |
| 撤回訊息 | `Api` | `adapter.Api.delete_message("msg_id")` |
| 退出群 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. 適配器實作檢查清單

### 標準動作
- [ ] `call_api` 能處理標準動作名（或覆蓋對應 `ApiDSL` 方法）
- [ ] 不支援的動作回傳 `retcode=10002`
- [ ] 回傳值遵循標準 API 回應格式
- [ ] `data` 字段包含 OB12 標準定義的字段
- [ ] 頻道平台需實作 `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] 元動作（`get_status` / `get_version` / `get_supported_actions`）建議實作
- [ ] **檔案收發用 `SendDSL.File`（直傳）**；檔案資源動作（upload_file/get_file/分片）**不強制實作**，僅當後端具備 `file_id` 資源能力時才需透傳

### 擴展動作
- [ ] 平台擴展動作使用 `{prefix}.{action}` 命名
- [ ] 擴展動作的參數和回應仍遵循 OB12 動作請求/回應結構

## 9. 相關文件

**實作 Api DSL 回傳值時配套對照**：
- [API 回應標準](api-response.md) - 適配器 API 回應格式標準

**同一適配器的其它 DSL**：
- [發送方法規範](send-method-spec.md) - Send 類的方法命名和參數規範
- [請求操作規範](request-action-spec.md) - Request DSL 的使用方式

**事件側配套**：
- [事件轉換標準](event-conversion.md) - 事件格式和訊息段標準

## API 响应规范

> 来源: `docs/zh-TW/standards/api-response.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/standards/api-response.md）

# ErisPulse 轉接器標準化回傳規範

> [!TIP]
> **什麼時候需要讀這篇**：當你在轉接器中實作 `call_api` / Send / Request 的回傳值，需要確認回應結構與回傳碼是否符合 ErisPulse 標準，或排查某個 `retcode` 的含義時對照本文。不需要則跳過。

## 1. 說明  
為什麼會有這個規範？

為了確保各平台發送介面回傳的統一性與 OneBot12 的相容性，ErisPulse 適配器在 API 回應格式上採用了 OneBot12 定義的消息發送回傳結構標準。

但 ErisPulse 的協定有一些特殊性定義：  
- 1. 基礎欄位中，`message_id` 是必須的，但 OneBot12 標準中沒有此欄位  
- 2. 回傳內容中需要添加 `{platform_name}_raw` 欄位，用於存放原始回應資料

## 2. 基礎返回結構  
所有動作回應必須包含以下基礎欄位：

| 欄位名 | 資料類型 | 必選 | 說明 |
|-------|---------|------|------|
| status | string | 是 | 執行狀態，必須是"ok"或"failed" |
| retcode | int64 | 是 | 返回碼，遵循OneBot12返回碼規則 |
| data | any | 是 | 回應資料，成功時包含請求結果，失敗時為null |
| message_id | string | 是 | 消息ID，用於標識消息，沒有則為空字串 |
| message | string | 是 | 錯誤資訊，成功時為空字串 |
| {platform_name}_raw | any | 否 | 原始回應資料 |

可選欄位：
| 欄位名 | 資料類型 | 必選 | 說明 |
|-------|---------|------|------|
| echo | string | 否 | 當請求中包含echo欄位時，原樣返回 |

## 3. 完整欄位規範

### 3.1 通用欄位

#### 成功回應範例
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": "1234",
        "time": 1632847927.599013
    },
    "message_id": "1234",
    "message": "",
    "echo": "1234",
    "telegram_raw": {...}
}
```

#### 失敗回應範例
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "缺少必要參數: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 回傳碼規範

#### 0 成功（OK）
- 0: 成功（OK）

#### 1xxxx 動作請求錯誤（Request Error）
| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 10001 | Bad Request | 無效的動作請求 |
| 10002 | Unsupported Action | 不支援的動作請求 |
| 10003 | Bad Param | 無效的動作請求參數 |
| 10004 | Unsupported Param | 不支援的動作請求參數 |
| 10005 | Unsupported Segment | 不支援的訊息段類型 |
| 10006 | Bad Segment Data | 無效的訊息段參數 |
| 10007 | Unsupported Segment Data | 不支援的訊息段參數 |
| 10101 | Who Am I | 未指定機器人帳號 |
| 10102 | Unknown Self | 未知的機器人帳號 |

#### 2xxxx 動作處理器錯誤（Handler Error）
| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 20001 | Bad Handler | 動作處理器實作錯誤 |
| 20002 | Internal Handler Error | 動作處理器執行時拋出例外 |

#### 3xxxx 動作執行錯誤（Execution Error）
| 錯誤碼範圍 | 錯誤類型 | 說明 |
|-----------|---------|------|
| 31xxx | Database Error | 資料庫錯誤 |
| 32xxx | Filesystem Error | 檔案系統錯誤 |
| 33xxx | Network Error | 網路錯誤 |
| 34xxx | Platform Error | 機器人平台錯誤 |
| 35xxx | Logic Error | 動作邏輯錯誤 |
| 36xxx | I Am Tired | 實現決定罷工 |

#### 保留錯誤段
- 4xxxx、5xxxx: 保留段，不應使用
- 6xxxx～9xxxx: 其他錯誤段，供實現自訂使用

## 4. 實現要求
1. 所有回應必須包含 status、retcode、data 和 message 欄位
2. 當請求中包含非空 echo 欄位時，回應必須包含相同值的 echo 欄位
3. 返回碼必須嚴格遵循 OneBot12 標準
4. 錯誤資訊 (message) 應當是人類可讀的描述

## 5. 擴展規範

ErisPulse 在 OneBot12 標準返回結構之上做了以下擴展：

### 5.1 `message_id` 必選欄位

OneBot12 標準中 `message_id` 位於 `data` 對象內部且非強制。ErisPulse 將其提升為頂層**必選**欄位：

- 無法獲取 `message_id` 時應設為空字串 `""`
- 確保 `message_id` 始終存在，模組無需做 null 檢查

### 5.2 `{platform}_raw` 原始回應欄位

回應值中應包含 `{platform}_raw` 欄位，存放平台原始回應資料的完整副本：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {"message_id": "1234", "time": 1632847927},
    "message_id": "1234",
    "message": "",
    "telegram_raw": {
        "ok": true,
        "result": {"message_id": 1234, "date": 1632847927, ...}
    }
}
```

**要求**：
- `{platform}_raw` 必須是原始回應的深拷貝，而非引用
- `platform` 必須與適配器註冊時的平台名完全一致（大小寫敏感）
- 原始回應中的錯誤資訊也應保留，便於除錯

### 5.3 框架擴展回應碼（34xxx 平台錯誤段的低三位自定義）

OneBot12 規範允許實現自定義 `3xxxx` 的低三位。`34xxx` 語義為 **Platform Error**
（機器人平台錯誤，如平台限制導致失敗）。`34xxx` 內部按職責分層使用：

| 低三位段 | 歸屬 | 用途 |
|---------|------|------|
| `340xx` | 適配器實現 | 請求操作族（Request Not Found / Already Handled / Not Supported / Permission Denied，見 request-action-spec §7） |
| `341xx`～`345xx` | 適配器實現 | 平台側權限 / 風控 / 帳號限制等錯誤（實現自定低三位，原始錯誤放 `{platform}_raw`） |
| `346xx` | **ErisPulse 框架（保留）** | 框架自身擋截與通用失敗，適配器/模組請勿占用 |
| `347xx`～`349xx` | 適配器實現 | 其它平台執行錯誤 |

ErisPulse 框架當前使用的 `346xx` 碼：

| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 34600 | SDK Failure | 框架通用失敗（`make_error()` 預設回傳碼） |
| 34601 | Action Denied | 出站動作被作用域禁用（`scope.actions`），呼叫未發起，直接回傳該回應 |

> 職責區分：`34601` 是**框架在呼叫前擋截**（模組根本沒資格發起動作）；
> `34004` / `34xxx` 平台碼是**動作已發出但平台拒絕**（如 Bot 無權限、被風控）。
> 模組判斷權限問題時同時檢查這兩種：先看 `34601`（自己模組被 scope 禁），
> 再看 `34xxx`（平台側限制）。

回傳結構為 §2 標準失敗回應：

```json
{
    "status": "failed",
    "retcode": 34601,
    "data": null,
    "message_id": "",
    "message": "action 'send' denied by scope.actions"
}
```

### 5.4 適配器實現檢查清單

- [ ] 包含 `status`, `retcode`, `data`, `message_id`, `message` 欄位
- [ ] 回傳碼遵循 OneBot12 規範（詳見 §3.2）
- [ ] `message_id` 始終存在（無法獲取時為空字串）
- [ ] `{platform}_raw` 包含平台原始回應資料

## 6. 注意事項
- 對於 3xxxx 錯誤碼，低三位可由實作自行定義
- 避免使用保留錯誤段(4xxxx、5xxxx)
- **`34600` / `34601` 為 ErisPulse 框架保留碼**（見 §5.3），適配器/模組避免使用
- 錯誤訊息應當簡潔明瞭，便於除錯

---

## 请求动作规范

> 来源: `docs/zh-TW/standards/request-action-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/standards/request-action-spec.md）

# ErisPulse 請求操作規範

> [!TIP]
> **什麼時候需要閱讀本文**：當你的適配器需要處理好友請求/群邀請（轉換請求事件、實現 `accept`/`reject`），或模組中要用 `event.approve()` / `event.reject()` 審批請求時對照本文。不需要則跳過。

本文檔定義了 ErisPulse 適配器中請求事件操作的標準化規範，包括請求事件的欄位要求、Request DSL 的使用方式和適配器實現要求。

## 1. 概述

請求事件（`type: "request"`）是 OneBot12 標準中定義的特殊事件類型，代表需要 Bot 做出決策的請求（如好友請求、群邀請等）。

與訊息事件不同，請求事件需要**雙向互動**：
1. **接收**：適配器將平台原生請求轉換為標準請求事件
2. **響應**：模組通過 `Request` DSL 或 `Event.approve()`/`Event.reject()` 執行操作

```
平台原生請求事件
    │
    ▼
Converter.convert()        ← 適配器實現（正向轉換）
    │
    ▼
標準請求事件 (含 request_id)
    │
    ├─→ 模組處理器 @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← 同意請求
    │       └─→ event.reject()      ← 拒絕請求
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← 適配器重寫
    │               │
    │               ▼
    │       平台 API 調用
    │
    └─→ 或直接透過適配器操作
            await adapter.Request("req_id").accept()
```

## 2. 請求事件字段要求

### 2.1 標準字段

請求事件除必須包含 OneBot12 標準字段外，還需包含以下字段：

| 字段 | 類型 | 必選 | 說明 |
|------|------|------|------|
| `request_id` | string | **強烈推薦** | 請求標識符，用於同意/拒絕操作 |
| `user_id` | string | 是 | 請求發起者ID |
| `user_nickname` | string | 否 | 請求發起者暱稱 |
| `comment` | string | 否 | 請求附言 |

### 2.2 `request_id` 字段

`request_id` 是請求操作的核心標識符：

- **用途**：標識一個可操作的請求，供 `Request` DSL 使用
- **生成規則**：
  - 優先使用平台原生的請求標識（如 OneBot11 的 `flag` 字段、Telegram 的 `chat_invite_link` 等）
  - 如果平台沒有原生請求ID，適配器應生成一個唯一標識（建議格式：`{platform}_{timestamp}_{user_id}`）
- **唯一性**：在同一平台範圍內應保持唯一
- **缺失行為**：當 `request_id` 缺失時，`event.approve()` / `event.reject()` 將拋出 `ValueError`

### 2.3 請求事件示例

```json
{
  "id": "evt_123456",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "請加好友",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 鏈式呼叫

`Request` 提供與 `Send` 風格一致的鏈式呼叫介面：

```python
# 基本用法
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# 指定 Bot 賬號
await adapter.Request("req_id").Using("bot1").accept()

# 附帶備註（透過 kwargs）
await adapter.Request("req_id").accept(comment="歡迎")
await adapter.Request("req_id").reject(comment="暫不添加")

# 組合使用
await adapter.Request("req_id").Using("bot1").accept(comment="歡迎")
```

### 3.2 方法列表

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `Using(account_id)` | 指定執行操作的 Bot 賬號 | `RequestDSL`（支援鏈式呼叫） |
| `accept(**kwargs)` | 同意請求 | `asyncio.Task`（await 後返回標準回應） |
| `reject(**kwargs)` | 拒絕請求 | `asyncio.Task`（await 後返回標準回應） |

### 3.3 回應值格式

操作返回標準 API 回應格式：

**成功**：
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**失敗**：
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "請求已過期或不存在"
}
```

**未實現**（適配器未重寫 `accept`/`reject`）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "平台 MyAdapter 未實現請求操作 (accept)"
}
```

## 4. Event 便捷方法

`Event` 包裝類提供了便捷方法，適合在請求事件處理器中使用：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # 檢查請求ID
    request_id = event.get_request_id()
    if not request_id:
        print("警告：請求事件缺少 request_id")
        return
    
    # 同意請求
    result = await event.approve()
    
    # 或拒絕請求
    # result = await event.reject(comment="暫不添加好友")
    
    # 檢查結果
    if result.get("status") == "ok":
        print("操作成功")
    else:
        print(f"操作失敗: {result.get('message')}")
```

### 4.1 Event 方法列表

| 方法 | 說明 | 回傳值 |
|------|------|--------|
| `get_request_id()` | 獲取請求ID | `str` |
| `approve(comment=None)` | 同意當前請求事件 | 標準回應格式 |
| `reject(comment=None)` | 拒絕當前請求事件 | 標準回應格式 |

## 5. 适配器實現要求

### 5.1 轉換器要求

適配器的轉換器在轉換請求事件時，**必須**正確設置 `request_id` 字段：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """轉換平台原生請求事件"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" 或 "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← 關鍵字段
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    從平台原生事件提取請求ID
    
    優先使用平台原生的請求標識，若無則生成唯一ID
    """
    # 優先使用平台原生ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # 兜底：生成唯一ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 內部類實現

適配器在 `Request` 內部類中重寫 `accept` 和 `reject` 即可：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform 請求操作實現"""
        
        def accept(self, **kwargs):
            """
            同意請求
            
            :param kwargs: 擴展參數，如 comment="備註"
            :return: asyncio.Task
            """
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=True,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"請求操作失敗: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """拒絕請求"""
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=False,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"請求操作失敗: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 平台不支援請求操作

如果平台本身不支援好友請求/群邀請操作（如某些平台自動處理請求），適配器可以：

1. **不重寫 `Request` 內部類**：使用基類預設實現，調用 `accept()`/`reject()` 時返回 `retcode=10002`
2. **在轉換時跳過 `request_id`**：不生成 `request_id`，讓 `event.approve()` 抛出 `ValueError`
3. **記錄日誌**：在 `accept`/`reject` 中記錄警告並返回適當錯誤碼

### 5.4 總結：Send 與 Request 並行

適配器有兩個並行的 DSL 內部類，各司其職：

```
BaseAdapter
├── Send(SendDSL)     ← 消息發送
│   ├── Raw_ob12()    ← 必須實現
│   ├── Text()        ← 推薦實現
│   └── Image()       ← 按需實現
│
└── Request(RequestDSL) ← 請求操作
    ├── accept()        ← 按需實現
    └── reject()        ← 按需實現
```

### 5.5 適配器 `__init__` 注意事項

重寫 `Request` 內部類的 `__init__` 時，必須透傳參數並調用 `super().__init__()`，詳見 [適配器開發入門 - `__init__` 注意事項](../developer-guide/adapters/getting-started.md#init-注意事項)（`Request` 同理，參數為 `adapter, request_id, account_id`）。

## 6. 适配器實現檢查清單

### 基礎要求
- [ ] 若重寫了 `__init__`，已調用 `super().__init__()`（確保 Send / Request 工廠初始化）

### 請求事件轉換
- [ ] 請求事件包含 `request_id` 字段（強烈推薦）
- [ ] `detail_type` 正確映射為 `"friend"` 或 `"group"`
- [ ] 保留平台原始數據在 `{platform}_raw` 字段中
- [ ] `request_id` 生成規則有文件說明

### 請求操作
- [ ] `Request` 內部類已實現（如平台支援請求操作）
- [ ] `accept()` 方法已實現
- [ ] `reject()` 方法已實現
- [ ] 操作返回標準 API 回應格式
- [ ] 不支援的操作返回 `retcode=10002`
- [ ] 網路錯誤返回 `retcode=33xxx`（遵循 API 回應標準）

## 7. 錯誤碼擴展

請求操作相關的**適配器實現層**推薦錯誤碼（遵循 [API 響應標準](api-response.md) §3.2，  
落在 `34xxx` 平台錯誤段的低三位自定義）：

| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 34001 | Request Not Found | 請求不存在或已過期 |
| 34002 | Request Already Handled | 請求已被處理 |
| 34003 | Request Not Supported | 平台不支援該類型的請求操作 |
| 34004 | Permission Denied | Bot 無權處理此請求（平台回傳） |

> **與框架碼的邊界**：以上 `340xx` 是**平台/適配器**回傳的請求處理失敗；  
> ErisPulse 框架在 `scope.actions` 禁用某模組的 request 動作時，**在呼叫適配器之前**  
> 直接回傳 `34601`（Action Denied，見 [API 響應標準 §5.3](api-response.md#53-框架擴展回傳碼34xxx-平台錯誤段的低三位自定義)），  
> 兩者互不替代：先過 `34601` 框架閘口，再落到平台層 `340xx` 錯誤。

## 8. 相關文件

**實現請求操作時配套對照**：
- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範（含 `request_id` 欄位要求）
- [API 回應標準](api-response.md) - 適配器 API 回應格式標準（操作回傳值與錯誤碼）

**同一適配器的其它 DSL**：
- [發送方法規範](send-method-spec.md) - Send 類的方法命名和參數規範
- [會話類型標準](session-types.md) - 會話類型定義和映射關係
