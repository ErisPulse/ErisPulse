# Terminal 平台特性文件

TerminalAdapter 是命令行終端適配器——終端即聊天對話，用於本地快速調試模組邏輯。

---

## 文件資訊

- 對應模組版本: 1.2.2
- 維護者: ErisPulse
- 最後更新: 2026-11-10

## 基本資訊

- 平台簡介：將本地命令列當作聊天對話，stdin 輸入即訊息，模組回應直接列印到終端機
- 适配器名稱：TerminalAdapter
- 平台標識：`terminal`
- 單帳號設計（本地調試場景）
- 框架要求：軟依賴 `ErisPulse>=2.7.1`（執行時偵測提示，不強制）

## 配置說明

```toml
[Terminal]
bot_id = "terminal_bot"    # Bot 的用戶 ID
bot_name = "TerminalBot"   # Bot 昵稱
user_id = "terminal_user"  # 模擬用戶的 ID（與 Bot 對話的終端用戶）
user_name = "User"         # 模擬用戶暱稱
prompt = "> "              # 輸入提示符
reply_prefix = "[Bot] "    # Bot 回覆的行前綴（留空則不加前綴）
echo_input = false         # 是否回顯用戶輸入（管道輸入場景下開啟）
```

## v5 範式更新（1.1.0）

- **spawn_background 任務歸屬**：stdin 讀取迴圈改用 `runtime.spawn_background`
- **框架軟依賴**：運行時偵測 `ErisPulse>=2.7.1` 並提示；啟動輸出版本日誌

## 標準化對齊（1.2.2）

響應結構與錯誤碼遵循 [API 響應規範](../standards/api-response.md)。

### 消息事件补齐 message_id

stdin 消息事件补齐頂層標準 `message_id` 字段（uuid 生成），模組可穩定引用終端消息進行回覆/去重。

### Send 繼承 BaseAdapter.Send

`Send` 繼承框架 `BaseAdapter.Send`，**標準修飾器鏈（`At` / `AtAll` / `Reply` 等）生效**，修飾段與文字段一併渲染輸出；`node`（合併轉發）段降級為純文字原文輸出（內容不遺失）。

### 元動作补齐

標準元動作已补齐，返回標準響應：

| 動作 | data 內容 |
|------|----------|
| `get_status` | `enabled`（運行狀態）/ `boot_time`（啟動時間戳） |
| `get_version` | `impl`（TerminalAdapter）/ `version` / `onebot_version` |
| `get_supported_actions` | 支持的動作名列表 |

```python
from ErisPulse import sdk
terminal = sdk.adapter.get("terminal")

result = await terminal.Api.get_status()
result = await terminal.Api.get_version()
result = await terminal.Api.get_supported_actions()
result = await terminal.Api.get_self_info()    # user_id/user_name
result = await terminal.Api.get_user_info("terminal_user")
result = await terminal.Api.get_friend_list()
```

### delete_message 能力降級語義修正

終端無撤回能力：`delete_message` 從「返回成功」修正為**能力降級標準語義**——返回 `retcode=10002`（不支援的操作），模組可據此判定降級。

### 錯誤碼規範

| retcode | 含義 | 說明 |
|---------|------|------|
| 0 | 成功 | — |
| 10002 | 不支援 | 群組操作、消息撤回、未實現的標準動作 |

## 使用說明

```python
# 模組照常監聽訊息即可
from ErisPulse.Core.Event import message

@message.on_message()
async def handle(event):
    if event.get("platform") == "terminal":
        await event.reply("收到：" + event.get_text())
```

- 終端輸入的文本即使用者訊息，支援多行（以空行結束）
- 事件結構示例（stdin 消息）：

```json
{
  "id": "<uuid>",
  "time": 1700000000,
  "message_id": "<uuid>",
  "type": "message",
  "detail_type": "private",
  "platform": "terminal",
  "self": {"platform": "terminal", "user_id": "terminal_bot", "user_name": "TerminalBot"},
  "user_id": "terminal_user",
  "message": [{"type": "text", "data": {"text": "輸入內容"}}],
  "alt_message": "輸入內容",
  "terminal_raw": {"text": "輸入內容"},
  "terminal_raw_type": "stdin_line"
}
```

- 發送示例（修飾器鏈可用）：

```python
terminal = sdk.adapter.get("terminal")

await terminal.Send.To("private", "terminal_user").Text("Hello")
await terminal.Send.To("private", "terminal_user").At("terminal_user").Text("帶修飾器的訊息")
await terminal.Send.To("private", "terminal_user").Raw_ob12([
    {"type": "text", "data": {"text": "OneBot12 段"}}
])
```

- 適用於開發期快速驗證模組邏輯，無需接入真實平台