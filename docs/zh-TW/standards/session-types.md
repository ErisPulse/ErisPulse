# ErisPulse 會話類型標準

本文檔定義了 ErisPulse 支援的會話類型標準，包括接收事件類型和發送目標類型。



## 1. 核心概念

### 1.1 接收類型 && 發送類型

ErisPulse 區分兩種會話類型：

- **接收類型（Receive Type）**：用於接收的事件的 `detail_type` 欄位
- **發送類型（Send Type）**：用於發送訊息時 `Send.To()` 方法的目標類型

### 1.2 類型映射關係

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
- `private` 是接收時的類型，發送時必須使用 `user`
- `group`、`channel`、`guild`、`thread` 在接收和發送時類型相同
- 系統會自動進行類型轉換，無需手動處理(代表著你可以直接使用獲得的接收類型進行發送)，但實際上，你無需考慮這些，Event的包裝類的存在，你可以直接使用event.reply()方法，而無需考慮類型轉換

7. **重要：路徑替換規則**
   - 將文件連結中的 `docs/zh-TW/` 替換為 `docs/zh-TW/`
   - 例如：`docs/zh-TW/quick-start.md` 應改為 `docs/zh-TW/quick-start.md`
   - 對於指向非當前語言版本文件的連結（如 `README.xx.md` 形式的連結），保持原樣不要修改
   - 這確保了連結指向正確語言的文件版本

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
- **說明**：群聊訊息，包括各種形式的群組（例如 Telegram supergroup）
- **ID 欄位**：`group_id`
- **適用平台**：所有支援群聊的平台

#### user
- **接收類型**：`user`
- **發送類型**：`user`
- **說明**：使用者類型，某些平台（例如 Telegram）將私聊表示為 user 而非 private
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
- **說明**：話題/子頻道訊息，用於社群中的子討論區
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

## 4. 自訂類型擴展

### 4.1 註冊自訂類型

適配器可以註冊自訂會話類型：

```python
from ErisPulse.Core.Event import register_custom_type

# 注冊自訂類型
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

### 4.3 取消註冊自訂類型

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")

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

### 5.2 使用示例

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

## 6. API 使用範例

### 6.1 發送訊息

```python
from ErisPulse import adapter

# 發送給使用者
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# 發送給群組
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# 自動轉換 private → user（不推薦，可能會有相容性問題）
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# 內部自動轉換為: Send.To("user", "789") # 直接使用user作為會話類型是更優的選擇
```

### 6.2 事件回覆

```python
from ErisPulse.Core.Event import Event

# Event.reply() 自動處理類型轉換
await event.reply("回覆內容")
# 內部自動使用正確的發送類型
```

### 6.3 命令處理

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # 系統自動處理會話類型
    # 無需手動判斷 group_id 還是 user_id
    await event.reply("命令執行成功")

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

1. **使用標準映射**：盡可能映射到標準類型，而非創建新類型
2. **正確轉換**：確保接收類型和發送類型的映射關係正確
3. **保留原始數據**：在 `{platform}_raw` 中保留原始事件類型
4. **文檔說明**：在適配器文檔中說明類型映射關係

### 7.2 模組開發者

1. **使用工具方法**：使用 `get_send_type_and_target_id()` 等工具方法
2. **避免硬編碼**：不要寫 `if group_id else "private"` 這樣的程式碼
3. **考慮所有類型**：程式碼要支援所有標準類型，不僅是 private/group
4. **靈活設計**：使用事件包裝器的方法，而非直接存取欄位

### 7.3 類型推斷

- **優先使用 detail_type**：如果有明確欄位，不進行推斷
- **合理使用推斷**：只在沒有明確類型時使用
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

- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範  
- [發送方法規範](send-method-spec.md) - Send 類的方法命名和參數規範  
- [適配器開發指南](../developer-guide/adapters/) - 適配器開發完整指南