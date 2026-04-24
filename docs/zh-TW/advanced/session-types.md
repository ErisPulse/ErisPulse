# 會話類型系統

ErisPulse 會話類型系統負責定義和管理訊息的會話類型（私聊、群聊、頻道等），並提供接收類型與發送類型之間的自動轉換。

## 類型定義

### 接收類型

接收類型來自 OneBot12 事件中的 `detail_type` 欄位，表示事件的會話場景：

| 類型 | 說明 | ID 欄位 |
|------|------|---------|
| `private` | 私聊訊息 | `user_id` |
| `group` | 群聊訊息 | `group_id` |
| `channel` | 頻道訊息 | `channel_id` |
| `guild` | 服務器訊息 | `guild_id` |
| `thread` | 話題/子頻道訊息 | `thread_id` |
| `user` | 用戶訊息（擴展） | `user_id` |

### 發送類型

發送類型用於 `Send.To(type, id)` 中指定發送目標：

| 類型 | 說明 |
|------|------|
| `user` | 發送給用戶 |
| `group` | 發送到群組 |
| `channel` | 發送到頻道 |
| `guild` | 發送到服務器 |
| `thread` | 發送到話題 |

## 類型對應

接收類型和發送類型之間存在預設對應關係：

```
接收 (Receive)          發送 (Send)
─────────────          ──────────
private        ──→     user
group          ──→     group
channel        ──→     channel
guild          ──→     guild
thread         ──→     thread
user           ──→     user
```

關鍵區別：**接收時用 `private`，發送時用 `user`**。這是 OneBot12 標準的設計——事件描述的是"私聊場景"，而發送描述的是"用戶目標"。

## 自動推斷

當事件沒有明確的 `detail_type` 欄位時，系統會根據事件中存在的 ID 欄位自動推斷會話類型：

**優先級**：`group_id` > `channel_id` > `guild_id` > `thread_id` > `user_id`

```python
from ErisPulse.Core.Event.session_type import infer_receive_type

# 有 group_id → 推斷為 group
event1 = {"group_id": "123", "user_id": "456"}
print(infer_receive_type(event1))  # "group"

# 只有 user_id → 推斷為 private
event2 = {"user_id": "456"}
print(infer_receive_type(event2))  # "private"
```

## 核心 API

### 類型轉換

```python
from ErisPulse.Core.Event.session_type import (
    convert_to_send_type,
    convert_to_receive_type,
)

# 接收類型 → 發送類型
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# 發送類型 → 接收類型
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### ID 欄位查詢

```python
from ErisPulse.Core.Event.session_type import get_id_field, get_receive_type

# 根據類型獲取 ID 欄位名
get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

# 根據 ID 欄位獲取類型
get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 一步獲取發送資訊

```python
from ErisPulse.Core.Event.session_type import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# 直接用於 Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 獲取目標 ID

```python
from ErisPulse.Core.Event.session_type import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 自訂類型註冊

適配器可以為平台特有的會話類型註冊自訂對應：

```python
from ErisPulse.Core.Event.session_type import register_custom_type, unregister_custom_type

# 註冊自訂類型
register_custom_type(
    receive_type="thread_reply",     # 接收類型名
    send_type="thread",              # 對應的發送類型
    id_field="thread_reply_id",      # 對應的 ID 欄位
    platform="discord"               # 平台名稱（可選）
)

# 使用自訂類型
convert_to_send_type("thread_reply", platform="discord")  # → "thread"
get_id_field("thread_reply", platform="discord")          # → "thread_reply_id"

# 註銷自訂類型
unregister_custom_type("thread_reply", platform="discord")
```

> **指定 platform 時**，註冊的接收類型會加上平台前綴（如 `discord_thread_reply`），避免不同平台之間的類型衝突。

## 工具方法

```python
from ErisPulse.Core.Event.session_type import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

# 檢查是否為標準類型
is_standard_type("private")  # True
is_standard_type("custom_type")  # False

# 檢查發送類型是否有效
is_valid_send_type("user")  # True
is_valid_send_type("invalid")  # False

# 獲取所有標準類型
get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

# 清除自訂類型
clear_custom_types()                # 清除所有
clear_custom_types(platform="discord")  # 只清除指定平台的
```

## 相關文件

- [事件轉換標準](../standards/event-conversion.md) - 事件轉換規範
- [會話類型標準](../standards/session-types.md) - 會話類型正式定義
- [事件轉換器實現](../../developer-guide/adapters/converter.md) - Converter 開發指南