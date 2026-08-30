# 雲湖平台特性文件

YunhuAdapter 是基於雲湖協定建構的適配器，整合了所有雲湖功能模組，提供統一的事件處理和訊息操作介面。

---



## 文件資訊

- 對應模組版本: 4.3.0
- 維護者: ErisPulse



## 基本資訊

- 平台簡介：雲湖（Yunhu）是一個企業級即時通訊平台
- 適配器名稱：YunhuAdapter
- 多帳戶支援：支援透過 bot_id 來識別並設定多個雲湖機器人帳戶
- 鏈式修飾支援：支援 `.Reply()` 等鏈式修飾方法
- OneBot12 兼容：支援發送 OneBot12 格式訊息


## 支援的消息傳送類型

所有傳送方法皆透過鏈式語法實作，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

支援的傳送類型包括：
- `.Text(text: str)`：傳送純文字訊息。
- `.Html(html: str)`：傳送HTML格式訊息。
- `.Markdown(markdown: str)`：傳送Markdown格式訊息。
- `.A2UI(text: str)`：傳送A2UI格式訊息。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`：傳送圖片訊息，支援流式上傳和自訂檔名。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`：傳送影片訊息，支援流式上傳和自訂檔名。
- `.File(file: bytes, stream: bool = False, filename: str = None)`：傳送檔案訊息，支援流式上傳和自訂檔名。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：批量傳送訊息。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：編輯已有訊息。
- `.Recall(msg_id: str)`：撤回訊息。
- `.Board(content: str, content_type: str = "text")`：發布公告看板。作用域由 `To()` 推斷（指定目標=本地看板，未指定=全域看板）。鏈式修飾：`.Expire(duration)` 相對過期（秒）、`.ExpireAt(timestamp)` 絕對過期（秒級時間戳）、`.ForMember(member_id)` 群成員看板；**內容為空時自動轉為撤銷看板**。仍兼容舊式 `Board("local", "公告")` 显式 scope 寫法。
- `.DismissBoard()`：撤銷公告看板。作用域同樣由 `To()` 推斷，支援 `.ForMember(member_id)`；仍兼容舊式 `DismissBoard("local")` 寫法。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：傳送流式訊息。

### 群組管理方法

所有群組管理方法需要透過鏈式語法指定群組，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`：移除群成員。機器人需要`允許移除群成員`權限。
- `.Ban(user_id: str, duration: int = 600)`：用戶禁言。`duration`為禁言時長（秒），0為解禁，-1為永久禁言。機器人需要`允許禁言用戶`權限。
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`：建立群標籤。`color`格式為#RRGGBB，`sort`越小越靠前。機器人需要`允許控制標籤組`權限。
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`：修改群標籤。各參數可選，不傳則不修改。機器人需要`允許控制標籤組`權限。
- `.DeleteTag(tag: str)`：刪除群標籤。機器人需要`允許控制標籤組`權限。
- `.GetTagList()`：獲取群標籤列表。回傳包含`list`陣列的回應資料。
- `.AddUserTag(user_id: str, tag: str)`：給用戶添加標籤。機器人需要`允許控制標籤組`權限。
- `.RemoveUserTag(user_id: str, tag: str)`：給用戶移除標籤。機器人需要`允許控制標籤組`權限。
- `.SetMsgTypeLimit(types: str)`：控制群內訊息類型。`types`為訊息類型名稱，多個用逗號分隔（如`"text,image,video"`），空字串表示不限制。機器人需要`允許修改群資訊`權限。

### 訊息查詢方法

獲取指定會話（用戶/群）的歷史訊息列表，需要透過鏈式語法指定目標，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`：獲取會話歷史訊息。回傳包含`list`陣列和`total`總數的回應資料。
  - `message_id`：訊息ID（可選）。不填時配合`before`回傳最近的N條訊息。
  - `before`：回傳指定訊息ID前N條。
  - `after`：回傳指定訊息ID後N條。
  - > **注意：** `before` 和 `after` 至少需指定一個且大於0，否則伺服器不會回傳任何訊息。

Board 作用域由 `To()` 自動推斷：
- 指定 `To(target_type, target_id)` → 本地看板（指定用戶/群組）
- 未指定 `To()` → 全域看板

```python
# 本地看板（60 秒後相對過期）
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# 群成員看板（僅指定成員可見）
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("僅你可見")

# 絕對時間戳過期
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("指定時間過期")

# 全域看板
await yunhu.Send.Board("全域公告")

# 清空本地看板（內容為空 → 自動撤銷）
await yunhu.Send.To("group", group_id).Board("")
```

### 按鈕參數說明

`buttons` 參數是一個嵌套列表，表示按鈕的佈局和功能。每個按鈕物件包含以下欄位：

| 欄位         | 類型   | 是否必填 | 說明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | 按鈕上的文字                                                         |
| `actionType` | int    | 是       | 動作類型：<br>`1`: 跳轉 URL<br>`2`: 複製<br>`3`: 點擊回報            |
| `url`        | string | 否       | 當 `actionType=1` 時使用，表示跳轉的目標 URL                         |
| `value`      | string | 否       | 當 `actionType=2` 時，該值會複製到剪貼簿<br>當 `actionType=3` 時，該值會發送給訂閱端 |

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
> - 只有使用者點擊了**按鈕回報事件**的按鈕才會收到推送，**複製**和**跳轉URL**均無法收到推送。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法回傳 `self`，支援鏈式呼叫，必須在最終發送方法前呼叫：

- `.Reply(message_id: str)`：回覆指定訊息。
- `.At(user_id: str)`：@指定用戶。
- `.AtAll()`：@所有人。
- `.Buttons(buttons: List)`：添加按鈕。

### 鏈式呼叫範例

```python
# 基礎發送
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

# 用戶禁言（10分鐘）
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# 解除禁言
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# 永久禁言
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# 建立群標籤
await yunhu.Send.To("group", group_id).CreateTag("VIP用戶", color="#FF5733", desc="VIP會員")

# 修改群標籤
await yunhu.Send.To("group", group_id).EditTag("VIP用戶", new_tag="SVIP用戶", color="#33C4FF")

# 刪除群標籤
await yunhu.Send.To("group", group_id).DeleteTag("VIP用戶")

# 獲取群標籤列表
result = await yunhu.Send.To("group", group_id).GetTagList()

# 給用戶添加標籤
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP用戶")

# 移除用戶標籤
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP用戶")

# 設定訊息類型限制
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# 取消訊息類型限制
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### 訊息查詢範例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 獲取群最近10條訊息（共回傳10條）
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# 獲取群中指定訊息ID前10條（共回傳11條）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# 獲取群中指定訊息ID前後各10條（共回傳21條）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# 獲取用戶會話歷史訊息
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12訊息支援

適配器支援發送 OneBot12 格式的訊息，便於跨平台訊息相容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式訊息。

```python
# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)

## 標準 API 動作 (ApiDSL)

> [!NOTE]  
> 本特性需要 ErisPulse **2.7.0+** 且 YunhuAdapter **4.3.0+**。

除了 `Send` 串流發送，適配器還提供 `Api` 內部類，公開 OneBot12 標準 API 動作與雲湖平台擴展動作。所有方法回傳標準回應格式。

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 信息查詢（透過公開 Web API，無需驗證）
result = await yunhu.Api.get_self_info()              # 機器人自身資訊
result = await yunhu.Api.get_user_info("7058262")     # 任意使用者資訊
result = await yunhu.Api.get_group_info("635409929")  # 群組資訊

# 檔案操作
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# 撤回訊息（需額外提供 chat_id + chat_type）
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# 多帳戶：指定 Bot 帳號
info = await yunhu.Api.Using("bot1").get_self_info()
```

### 支援的標準動作

| 方法 | 說明 | 數據來源 |
|------|------|---------|
| `get_self_info()` | 機器人自身資訊 | 公開 Web API（bot-info） |
| `get_user_info(user_id)` | 使用者資訊（任意使用者可查） | 公開 Web API（user/homepage） |
| `get_group_info(group_id)` | 群組資訊 | 公開 Web API（group-info） |
| `upload_file(*, type, name, ...)` | 上傳檔案（自動判定 image/video/file） | Bot 開放 API |
| `get_file(file_id)` | 取得檔案（file_id 即 URL） | — |
| `delete_message(message_id, *, chat_id, chat_type)` | 撤回訊息 | Bot 開放 API（/bot/recall） |

> **注意**：`get_self_info` / `get_user_info` / `get_group_info` 透過**非官方公開 Web API**（chat-web-go.jwzhd.com）實現，這些介面無需驗證但非官方文件、可能隨平台更新變動；失敗時回傳標準錯誤回應。

### 不支援的標準動作

以下標準動作雲湖無對應 API，呼叫時回傳 `retcode=10002`（不支援的操作）：
- `get_friend_list`（Bot 開放 API 的「機器人使用者列表」尚在待上線狀態）
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### 平台擴展動作

透過 `Api.call("yunhu.xxx", **params)` 呼叫雲湖特有動作（參數採用 OB12 風格命名，適配器自動翻譯為雲湖欄位）：

| 擴展動作 | 說明 | 等價 Send 方法 |
|---------|------|---------------|
| `yunhu.recall` | 撤回訊息（msg_id, chat_id, chat_type） | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | 移除群組成員（group_id, user_id） | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | 禁言（group_id, user_id, duration） | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | 解除禁言（group_id, user_id） | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | 群組標籤 CRUD（group_id, ...） | `Send.To("group", g).CreateTag(...)` 等 |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | 給使用者添加/移除標籤 | `Send.To("group", g).AddUserTag(...)` 等 |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **成員頭銜語意別名**（標籤≈頭銜，內部映射到 tag.relate） | — |
| `yunhu.msg_type_limit` | 群組訊息類型限制（group_id, type） | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | 取得歷史訊息（chat_id, chat_type, message_id?, before?, after?） | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | 公開 bot-info 查詢（bot_id） | — |
| `yunhu.user_homepage` | 公開使用者主頁查詢（user_id） | — |

```python
# 平台擴展示例
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **標籤與頭銜**：雲湖的「標籤」語意等同 OneBot12 群組成員 `title`。`yunhu.set_member_title` 是 `yunhu.tag.relate` 的原生語意別名，二者內部映射到同一端點。群組訊息事件中發送者角色由 `senderUserLevel` 映射到標準 `role` 欄位（owner/admin/member）。

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 適配器標準化返回規範：

```python
{
    "status": "ok",           // 執行狀態
    "retcode": 0,             // 返回碼
    "data": {...},            // 响應數據
    "self": {...},            // 自身資訊（包含 bot_id）
    "message_id": "123456",   // 消息ID
    "message": "",            // 錯誤資訊
    "yunhu_raw": {...}        // 原始響應數據
}
```


## 特有事件類型

需要 platform=="yunhu" 檢測再使用本平台特性

### 核心差異點

1. 特有事件類型：
    - 表單（如表單指令）：yunhu_form
    - 表情包/貼紙訊息段：yunhu_expression
    - 按鈕點擊：yunhu_button_click
    - A2UI按鈕點擊：yunhu_a2ui_button
    - 機器人設定：yunhu_bot_setting
    - 快捷選單：yunhu_shortcut_menu
2. 標準欄位擴展（4.3.0+）：
    - 訊息事件新增標準 `role` 欄位（由雲湖 `senderUserLevel` 映射為 `owner`/`admin`/`member`）
    - 新增 `user_avatar` 欄位（發送者頭像 URL）
3. 擴展欄位：
    - 所有特有欄位均以yunhu_前綴標識
    - 保留原始資料在yunhu_raw欄位
    - 私聊中self.user_id表示機器人ID

### 特殊欄位示例

```python
# 表單命令
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "表單指令名",
    "id": "指令ID",
    "form": {
      "字段ID1": {
        "id": "字段ID1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "字段標籤",
        "value": "字段值"
      }
    }
  }
}

# 按鈕事件
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "點擊按鈕的用戶ID",
  "user_nickname": "用戶暱稱",
  "message_id": "訊息ID",
  "yunhu_button": {
    "id": "按鈕ID（可能為空）",
    "value": "按鈕值"
  }
}

# A2UI按鈕事件
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "操作用戶ID",
  "user_nickname": "用戶暱稱",
  "message_id": "訊息ID",
  "yunhu_a2ui": {
    "recv_id": "接收者ID",
    "recv_type": "接收者類型",
    "action_name": "操作名稱",
    "source_component_id": "來源組件ID",
    "form_context": {},
    "interaction_json": "互動資料JSON字串"
  }
}

### 按鈕點擊事件處理示例

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """處理雲湖通知事件

    使用通用的 on_notice() 裝飾器來處理所有通知事件，
    然後通過 detail_type 區分不同類型的通知
    event.reply() 會自動透過雲湖平台回覆
    """

# 檢查是否是按鈕點擊事件  
    if event.get("detail_type") == "yunhu_button_click":  
        user_id = event.get_user_id()  
        user_nickname = event.get_user_nickname()  
        button_value = event.get("yunhu_button", {}).get("value", "")  

        print(f"用戶 {user_nickname}({user_id}) 點擊了按鈕: {button_value}")

# 使用 event.reply() 自動回覆（會根據平台自動選擇正確的發送方式）  
        如果 button_value == "confirm":
            await event.reply("你點擊了確認按鈕！")
        elif button_value == "cancel":
            await event.reply("操作已取消")
        else:
            await event.reply(f"收到你的選擇: {button_value}")

# 處理快捷選單事件
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"觸發了快捷選單: {menu_id}")

[**返回上一頁**](../README.md)

# 處理機器人設定變更
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"設定已更新: {settings}")

7. **重要：路徑替換規則**
   - 將文件連結中的 `docs/zh-TW/` 替換為 `docs/zh-TW/`
   - 例如：`docs/zh-TW/quick-start.md` 應改為 `docs/zh-TW/quick-start.md`
   - 對於指向非當前語言版本文件的連結（如 `README.xx.md` 形式的連結），保持原樣不要修改
   - 這確保連結指向正確語言的文件版本

# 處理 A2UI 按鈕事件
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI 操作: {action_name}, 表單數據: {form_context}")
```

### 使用鏈式呼叫發送帶按鈕訊息

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "確認", "actionType": 3, "value": "confirm"},
        {"text": "取消", "actionType": 3, "value": "cancel"},
        {"text": "詳細檢視", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# 發送帶按鈕的消息到群組  
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("請確認以下操作")

# 發送帶按鈕的消息到用戶私聊  
await yunhu.Send.To("user", "789").Buttons(buttons).Text("請選擇你的偏好設置")  

### 發送A2UI消息  

```python  
from ErisPulse import sdk  

yunhu = sdk.adapter.get("yunhu")

# 發送A2UI訊息
await yunhu.Send.To("user", user_id).A2UI("A2UI互動卡片內容")
```

# 機器人設定
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "群組ID（可能為空）",
  "user_nickname": "用戶暱稱",
  "yunhu_setting": {
    "設定項ID": {
      "id": "設定項ID",
      "type": "input/radio/checkbox/select/switch",
      "value": "設定值"
    }
  }
}

# 快捷選單
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "觸發選單的用戶ID",
  "user_nickname": "用戶暱稱",
  "group_id": "群組ID（如果是群聊）",
  "yunhu_menu": {
    "id": "選單ID",
    "type": "選單類型(整數)",
    "action": "選單動作(整數)"
  }
}

## Event Mixin 擴展方法

適配器註冊了以下平台專有方法，僅在 `platform == "yunhu"` 時可用：

| 方法 | 返回類型 | 說明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 獲取雲湖原始事件數據（`yunhu_raw`） |
| `get_sender_level()` | `str` | 發送者雲湖原生等級（owner/administrator/member/unknown） |
| `get_sender_role()` | `str` | 發送者 OneBot12 標準 role（owner/admin/member） |
| `get_sender_title()` | `str` | 發送者頭銜（標準 `title` 欄位存取器，預留） |
| `get_sender_avatar()` | `str` | 發送者頭像 URL |
| `get_command()` | `dict` | 指令數據（僅指令消息事件，`yunhu_command`） |
| `get_button_value()` | `str` | 按鈕點擊事件的 value（`yunhu_button.value`） |
| `get_a2ui_action()` | `str` | A2UI 按鈕事件的 actionName |
| `get_a2ui_form_context()` | `dict` | A2UI 按鈕事件的表單上下文 |
| `get_menu_id()` | `str` | 快捷選單事件 ID（`yunhu_menu.id`） |
| `get_setting()` | `dict` | 機器人設定事件的設定數據（`yunhu_setting`） |
| `is_command_message()` | `bool` | 是否為指令消息 |
| `is_button_click()` | `bool` | 是否為按鈕點擊事件 |
| `is_a2ui_button()` | `bool` | 是否為 A2UI 按鈕事件 |

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    if event.get("platform") != "yunhu":
        return

    if event.is_button_click():
        value = event.get_button_value()
        await event.reply(f"你點擊了按鈕: {value}")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()

## 擴展欄位說明

- 所有獨有欄位均以 `yunhu_` 前綴標識，避免與標準欄位衝突
- 保留原始數據在 `yunhu_raw` 欄位，便於訪問雲湖平台的完整原始數據
- `self.user_id` 表示機器人ID（從配置中的bot_id獲取）
- 表單指令通過 `yunhu_command` 欄位提供結構化數據
- 按鈕點擊事件通過 `yunhu_button` 欄位提供按鈕相關資訊
- A2UI按鈕事件通過 `yunhu_a2ui` 欄位提供A2UI互動相關資訊
- 機器人設定變更通過 `yunhu_setting` 欄位提供設定項數據
- 快捷菜單操作通過 `yunhu_menu` 欄位提供菜單相關資訊
- 表情包/貼紙訊息通過 `yunhu_expression` 訊息段提供貼紙數據（sticker_id、貼紙包ID、圖片尺寸等）

### 表情包/貼紙訊息段 (yunhu_expression)

當使用者發送表情包或貼紙時，訊息段類型為 `yunhu_expression`：

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
| `sticker_id` | string | 貼紙唯一標識 |
| `sticker_pack_id` | string | 貼紙包ID |
| `expression_id` | string | 表情ID |
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

## 多Bot配置

### 配置說明

雲湖適配器支援同時配置和運行多個雲湖機器人帳戶。

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # 機器人token（必填）
mode = "ws"  # 接收模式（可選，預設為"ws"，可選值："ws"、"webhook"）
webhook_path = "/webhook/bot1"  # Webhook路徑（可選，預設為"/webhook"）
enabled = true  # 是否啟用（可選，預設為true）

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # 第二個機器人的token
webhook_path = "/webhook/bot2"  # 獨立的webhook路徑
enabled = true
```

**配置項說明：**
- `token`：雲湖平台提供的API token（必填）
- `mode`：接收模式（可選，預設為 `"ws"`，可選值 `"ws"`、`"webhook"`）
- `webhook_path`：接收雲湖事件的HTTP路徑（可選，預設為"/webhook"，僅 webhook 模式使用）
- `enabled`：是否啟用該帳戶（可選，預設為true）

**重要提示：**
1. 雲湖平台的機器人ID在**運行時自動檢測**，無需在配置中指定
2. webhook 模式下每個bot都應該有獨立的`webhook_path`，以便接收各自的webhook事件
3. 在雲湖平台配置webhook時，請為每個bot配置對應的URL，例如：
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### 使用Send DSL指定Bot

可以透過`Using()`方法指定使用哪個bot發送訊息。該方法支援兩種參數：
- **帳戶名**：配置中的 bot 名稱（如 `bot1`, `bot2`）
- **bot_id**：配置中的 `bot_id` 值

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 使用帳戶名發送訊息
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# 使用 bot_id 發送訊息（自動匹配對應帳戶）
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# 不指定時使用第一個啟用的bot
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **提示：** 使用 `bot_id` 時，系統會自動查找配置中匹配的帳戶。這在處理事件回覆時特別有用，可以直接使用 `event["self"]["user_id"]` 來回覆同一帳戶。

### 事件中的Bot標識

接收到的事件會自動包含對應的`bot_id`資訊：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # 獲取觸發事件的機器人ID
        bot_id = event["self"]["user_id"]
        print(f"訊息來自Bot: {bot_id}")
        
        # 使用相同bot回覆訊息
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
[INFO] [yunhu] [bot:12345678] 訊息發送成功，message_id: abc123
```

### 管理介面

```python
# 獲取所有帳戶資訊
bots = yunhu.bots

# 檢查帳戶是否啟用
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# 動態啟用/禁用帳戶（需要重啟適配器）
yunhu.bots["bot1"].enabled = False
```

### 舊配置相容

舊版 `[Yunhu_Adapter.bots.*]` 配置（含 `bot_id` 字段）會自動遷移至 `accounts` 格式（`bot_id` 已改為運行時自動檢測，配置中的值會被忽略）；建議盡快遷移至新格式。