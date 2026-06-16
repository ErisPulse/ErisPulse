# 雲湖平台特性文件

YunhuAdapter 是基於雲湖協議建構的適配器，整合了所有雲湖功能模組，提供統一的事件處理和訊息操作介面。

---

## 文件資訊

- 對應模組版本: 4.0.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：雲湖（Yunhu）是一個企業級即時通訊平台
- 適配器名稱：YunhuAdapter
- 多帳號支援：支援透過 bot_id 識別並設定多個雲湖機器人帳號
- 鏈式修飾支援：支援 `.Reply()` 等鏈式修飾方法
- OneBot12 相容：支援傳送 OneBot12 格式訊息

## 支援的訊息傳送類型

所有傳送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

支援的傳送類型包括：
- `.Text(text: str)`：傳送純文字訊息。
- `.Html(html: str)`：傳送 HTML 格式訊息。
- `.Markdown(markdown: str)`：傳送 Markdown 格式訊息。
- `.A2UI(text: str)`：傳送 A2UI 格式訊息。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`：傳送圖片訊息，支援流式上傳和自訂檔名。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`：傳送影片訊息，支援流式上傳和自訂檔名。
- `.File(file: bytes, stream: bool = False, filename: str = None)`：傳送檔案訊息，支援流式上傳和自訂檔名。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：批量傳送訊息。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：編輯既有訊息。
- `.Recall(msg_id: str)`：撤回訊息。
- `.Board(scope: str, content: str, **kwargs)`：發布公告看板，scope 支援 `local` 和 `global`。
- `.DismissBoard(scope: str, **kwargs)`：撤銷公告看板。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：傳送流式訊息。

### 群組管理方法

所有群組管理方法需要透過鏈式語法指定群組，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`：移除群成員。機器人需要 `允許移除群成員` 權限。
- `.Ban(user_id: str, duration: int = 600)`：使用者禁言。`duration` 為禁言時長（秒），0 為解禁，-1 為永久禁言。機器人需要 `允許禁言使用者` 權限。
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`：建立群標籤。`color` 格式為 #RRGGBB，`sort` 越小越靠前。機器人需要 `允許控制標籤組` 權限。
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`：修改群標籤。各參數可選，不傳則不修改。機器人需要 `允許控制標籤組` 權限。
- `.DeleteTag(tag: str)`：刪除群標籤。機器人需要 `允許控制標籤組` 權限。
- `.GetTagList()`：取得群標籤列表。傳回包含 `list` 陣列的回應資料。
- `.AddUserTag(user_id: str, tag: str)`：給使用者新增標籤。機器人需要 `允許控制標籤組` 權限。
- `.RemoveUserTag(user_id: str, tag: str)`：給使用者移除標籤。機器人需要 `允許控制標籤組` 權限。
- `.SetMsgTypeLimit(types: str)`：控制群內訊息類型。`types` 為訊息類型名稱，多個用逗號分隔（如 `"text,image,video"`），空字串表示不限制。機器人需要 `允許修改群資訊` 權限。

### 訊息查詢方法

取得指定會話（使用者/群）的歷史訊息列表，需要透過鏈式語法指定目標，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`：取得會話歷史訊息。傳回包含 `list` 陣列和 `total` 總數的回應資料。
  - `message_id`：訊息 ID（可選）。不填時配合 `before` 傳回最近的 N 條訊息。
  - `before`：傳回指定訊息 ID 前 N 條。
  - `after`：傳回指定訊息 ID 後 N 條。
  - > **注意：** `before` 和 `after` 至少需指定一個且大於 0，否則伺服器不會傳回任何訊息。

Board board_type 支援以下類型：
- `local`：指定使用者看板
- `global`：全域看板

### 按鈕參數說明

`buttons` 參數是一個巢狀列表，表示按鈕的佈局和功能。每個按鈕物件包含以下欄位：

| 欄位         | 類型   | 是否必填 | 說明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | 按鈕上的文字                                                         |
| `actionType` | int    | 是       | 動作類型：<br>`1`: 跳轉 URL<br>`2`: 複製<br>`3`: 點擊回報            |
| `url`        | string | 否       | 當 `actionType=1` 時使用，表示跳轉的目標 URL                         |
| `value`      | string | 否       | 當 `actionType=2` 時，該值會複製到剪貼簿<br>當 `actionType=3` 時，該值會傳送給訂閱端 |

範例：
```python
buttons = [
    [
        {"text": "複製", "actionType": 2, "value": "xxxx"},
        {"text": "點擊跳轉", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "回報事件", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("帶按鈕的訊息")
```
> **注意：**
> - 只有使用者點擊了**按鈕回報事件**的按鈕才會收到推播，**複製**和**跳轉 URL** 均無法收到推播。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法回傳 `self`，支援鏈式呼叫，必須在最終傳送方法前呼叫：

- `.Reply(message_id: str)`：回覆指定訊息。
- `.At(user_id: str)`：@指定使用者。
- `.AtAll()`：@所有人。
- `.Buttons(buttons: List)`：新增按鈕。

### 鏈式呼叫範例

```python
# 基礎傳送
await yunhu.Send.To("user", user_id).Text("Hello")

# 回覆訊息
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("回覆訊息")

# 回覆 + 按鈕
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("帶回覆和按鈕的訊息")
```

### 群組管理範例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 移除群成員
await yunhu.Send.To("group", group_id).Kick(user_id)

# 使用者禁言（10分鐘）
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# 解除禁言
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# 永久禁言
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# 建立群標籤
await yunhu.Send.To("group", group_id).CreateTag("VIP使用者", color="#FF5733", desc="VIP會員")

# 修改群標籤
await yunhu.Send.To("group", group_id).EditTag("VIP使用者", new_tag="SVIP使用者", color="#33C4FF")

# 刪除群標籤
await yunhu.Send.To("group", group_id).DeleteTag("VIP使用者")

# 取得群標籤列表
result = await yunhu.Send.To("group", group_id).GetTagList()

# 給使用者新增標籤
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP使用者")

# 移除使用者標籤
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP使用者")

# 設定訊息類型限制
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# 取消訊息類型限制
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### 訊息查詢範例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 取得群最近10條訊息（共傳回10條）
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# 取得群中指定訊息 ID 前10條（共傳回11條）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# 取得群中指定訊息 ID 前後各10條（共傳回21條）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# 取得使用者會話歷史訊息
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12 訊息支援

適配器支援傳送 OneBot12 格式的訊息，便於跨平台訊息相容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：傳送 OneBot12 格式訊息。

```python
# 傳送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 傳送方法回傳值

所有傳送方法均回傳一個 Task 物件，可以直接 await 取得傳送結果。回傳結果遵循 ErisPulse 適配器標準化回傳規範：

```python
{
    "status": "ok",           // 執行狀態
    "retcode": 0,             // 回傳碼
    "data": {...},            // 回應資料
    "self": {...},            // 自身資訊（包含 bot_id）
    "message_id": "123456",   // 訊息 ID
    "message": "",            // 錯誤訊息
    "yunhu_raw": {...}        // 原始回應資料
}
```

## 特有事件類型

需要 platform=="yunhu" 檢測再使用本平台特性

### 核心差異點

1. 特有事件類型：
    - 表單（如表單指令）：yunhu_form
    - 表情包/貼紙訊息段：yunhu_expression
    - 按鈕點擊：yunhu_button_click
    - A2UI 按鈕點擊：yunhu_a2ui_button
    - 機器人設定：yunhu_bot_setting
    - 快捷選單：yunhu_shortcut_menu
2. 擴充欄位：
    - 所有特有欄位均以 yunhu_ 前綴識別
    - 保留原始資料在 yunhu_raw 欄位
    - 私聊中 self.user_id 表示機器人 ID

### 特殊欄位範例

```python
# 表單指令
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "表單指令名",
    "id": "指令 ID",
    "form": {
      "欄位 ID1": {
        "id": "欄位 ID1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "欄位標籤",
        "value": "欄位值"
      }
    }
  }
}

# 按鈕事件
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "點擊按鈕的使用者 ID",
  "user_nickname": "使用者暱稱",
  "message_id": "訊息 ID",
  "yunhu_button": {
    "id": "按鈕 ID（可能為空）",
    "value": "按鈕值"
  }
}

# A2UI按鈕事件
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "操作使用者 ID",
  "user_nickname": "使用者暱稱",
  "message_id": "訊息 ID",
  "yunhu_a2ui": {
    "recv_id": "接收者 ID",
    "recv_type": "接收者類型",
    "action_name": "操作名稱",
    "source_component_id": "來源組件 ID",
    "form_context": {},
    "interaction_json": "交互資料 JSON 字串"
  }
}

### 按鈕點擊事件處理範例

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """處理雲湖通知事件

    使用通用的 on_notice() 裝飾器來處理所有通知事件，
    然後通過 detail_type 區分不同類型的通知
    event.reply() 會自動通過雲湖平台回覆
    """
    # 檢查是否是按鈕點擊事件
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"使用者 {user_nickname}({user_id}) 點擊了按鈕: {button_value}")

        # 使用 event.reply() 自動回覆（會根據平台自動選擇正確的傳送方式）
        if button_value == "confirm":
            await event.reply("你點擊了確認按鈕！")
        elif button_value == "cancel":
            await event.reply("操作已取消")
        else:
            await event.reply(f"收到你的選擇: {button_value}")

    # 處理快捷選單事件
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"觸發了快捷選單: {menu_id}")

    # 處理機器人設定變更
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"設定已更新: {settings}")

    # 處理 A2UI 按鈕事件
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI 操作: {action_name}, 表單資料: {form_context}")
```

### 使用鏈式呼叫傳送帶按鈕訊息

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "確認", "actionType": 3, "value": "confirm"},
        {"text": "取消", "actionType": 3, "value": "cancel"},
        {"text": "查看詳情", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# 傳送帶按鈕的訊息到群組
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("請確認以下操作")

# 傳送帶按鈕的訊息到使用者私聊
await yunhu.Send.To("user", "789").Buttons(buttons).Text("請選擇你的偏好設定")
```

### 傳送 A2UI 訊息

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# 傳送 A2UI 訊息
await yunhu.Send.To("user", user_id).A2UI("A2UI 交互卡片內容")
```

# 機器人設定
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "群組 ID（可能為空）",
  "user_nickname": "使用者暱稱",
  "yunhu_setting": {
    "設定項 ID": {
      "id": "設定項 ID",
      "type": "input/radio/checkbox/select/switch",
      "value": "設定值"
    }
  }
}

# 快捷選單
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "觸發選單的使用者 ID",
  "user_nickname": "使用者暱稱",
  "group_id": "群組 ID（如果是群聊）",
  "yunhu_menu": {
    "id": "選單 ID",
    "type": "選單類型（整數）",
    "action": "選單動作（整數）"
  }
}
```

## 擴充欄位說明

- 所有特有欄位均以 `yunhu_` 前綴識別，避免與標準欄位衝突
- 保留原始資料在 `yunhu_raw` 欄位，便於存取雲湖平台的完整原始資料
- `self.user_id` 表示機器人 ID（從設定中的 bot_id 取得）
- 表單指令透過 `yunhu_command` 欄位提供結構化資料
- 按鈕點擊事件透過 `yunhu_button` 欄位提供按鈕相關資訊
- A2UI 按鈕事件透過 `yunhu_a2ui` 欄位提供 A2UI 交互相關資訊
- 機器人設定變更透過 `yunhu_setting` 欄位提供設定項資料
- 快捷選單操作透過 `yunhu_menu` 欄位提供選單相關資訊
- 表情包/貼紙訊息透過 `yunhu_expression` 訊息段提供貼紙資料（sticker_id、貼紙包 ID、圖片尺寸等）

### 表情包/貼紙訊息段 (yunhu_expression)

當使用者傳送表情包或貼紙時，訊息段類型為 `yunhu_expression`：

```json
{
  "type": "yunhu_expression",
  "data": {
    "sticker_id": "35154",
    "sticker_pack_id": "1670",
    "expression_id": "0",
    "image_name": "sticker/fabb9077f2ba302402ea871cab3686ad7a3fc52c.gif",
    "width": 500,
    "height": 500
  }
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `sticker_id` | string | 貼紙唯一識別 |
| `sticker_pack_id` | string | 貼紙包 ID |
| `expression_id` | string | 表情 ID |
| `image_name` | string | 表情圖片檔案路徑 |
| `width` | int | 圖片寬度（可選） |
| `height` | int | 圖片高度（可選） |

使用範例：
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"收到表情包: sticker_id={data['sticker_id']}, 包ID={data['sticker_pack_id']}")
```

---

## 多機器人設定

### 設定說明

雲湖適配器支援同時設定和執行多個雲湖機器人帳號。

```toml
# config.toml
[Yunhu_Adapter.bots.bot1]
bot_id = "30535459"  # 機器人 ID（必填）
token = "your_bot1_token"  # 機器人 token（必填）
webhook_path = "/webhook/bot1"  # Webhook 路徑（可選，預設為 "/webhook"）
enabled = true  # 是否啟用（可選，預設為 true）

[Yunhu_Adapter.bots.bot2]
bot_id = "12345678"  # 第二個機器人的 ID
token = "your_bot2_token"  # 第二個機器人的 token
webhook_path = "/webhook/bot2"  # 獨立的 webhook 路徑
enabled = true
```

**設定項說明：**
- `bot_id`：機器人的唯一識別 ID（必填），用於識別是哪個機器人觸發的事件
- `token`：雲湖平台提供的 API token（必填）
- `webhook_path`：接收雲湖事件的 HTTP 路徑（可選，預設為 "/webhook"）
- `enabled`：是否啟用該 bot（可選，預設為 true）

**重要提示：**
1. 雲湖平台的事件中不包含機器人 ID，因此必須在設定中明確指定 `bot_id`
2. 每個 bot 都應該有獨立的 `webhook_path`，以便接收各自的 webhook 事件
3. 在雲湖平台設定 webhook 時，請為每個 bot 設定對應的 URL，例如：
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### 使用 Send DSL 指定機器人

可以透過 `Using()` 方法指定使用哪個 bot 傳送訊息。此方法支援兩種參數：
- **帳號名稱**：設定中的 bot 名稱（如 `bot1`, `bot2`）
- `bot_id`：設定中的 `bot_id` 值

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 使用帳號名稱傳送訊息
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# 使用 bot_id 傳送訊息（自動匹配對應帳號）
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# 不指定時使用第一個啟用的 bot
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **提示：** 使用 `bot_id` 時，系統會自動尋找設定中匹配的帳號。這在處理事件回覆時特別有用，可以直接使用 `event["self"]["user_id"]` 來回覆同一帳號。

### 事件中的機器人識別

接收到的事件會自動包含對應的 `bot_id` 資訊：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # 取得觸發事件的機器人 ID
        bot_id = event["self"]["user_id"]
        print(f"訊息來自 Bot: {bot_id}")
        
        # 使用相同 bot 回覆訊息
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("回覆訊息")
```

### 日誌資訊

適配器會在日誌中自動包含 `bot_id` 資訊，便於除錯和追蹤：

```
[INFO] [yunhu] [bot:30535459] 收到來自使用者 user123 的私聊訊息
[INFO] [yunhu] [bot:12345678] 消息傳送成功，message_id: abc123
```

### 管理介面

```python
# 取得所有帳號資訊
bots = yunhu.bots

# 檢查帳號是否啟用
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# 動態啟用/禁用帳號（需要重啟適配器）
yunhu.bots["bot1"].enabled = False
```

### 舊設定相容

系統會自動相容舊格式的設定，但建議遷移到新設定格式以獲得更好的多 bot 支援。