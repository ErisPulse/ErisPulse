# Sandbox 平台特性文件

SandboxAdapter 是 ErisPulse 內建的沙盒適配器，用於本地開發與模組除錯——無需真實平台即可模擬訊息收發。

---

## 文件資訊

- 對應模組版本: 4.2.3
- 維護者: ErisPulse
- 最後更新: 2026-11-10

## 基本資訊

- 平台簡介：本地沙盒環境，提供虛擬用戶/群組、Web 調試面板與訊息持久化
- 适配器名稱：SandboxAdapter
- 平台標識：`sandbox`
- 單帳戶設計（本地調試場景）
- 框架要求：軟依賴 `ErisPulse>=2.7.1`（執行時檢測提示，不強制）

## v5 範式更新（4.1.0）

- **Api DSL 最小集**：`get_self_info` / `get_status` / `get_version` / `get_supported_actions`
- **spawn_background 任務歸屬**：心跳任務改用 `runtime.spawn_background`
- **框架軟依賴**：執行時偵測 `ErisPulse>=2.7.1` 並提示
- 導入路徑更新至 `Core.Bases`（BaseConfig）

## 標準化對齊（4.2.3）

響應結構與錯誤碼遵循 [API 響應規範](../standards/api-response.md)。

### HTML 發送方法

- `.Html(html: str)`：發送 HTML 消息（經 html 通道渲染到 Web 面板）
- `.HTML(html: str)`：`.Html()` 的別名（與標準 Send 方法命名保持一致）

### 元動作（已標準）

標準元動作返回標準響應：

| 動作 | data 內容 |
|------|----------|
| `get_self_info` | `user_id`（配置的 `self_id`）/ `user_name`（`sandbox`） |
| `get_status` | `good`（運行狀態）/ `bots`（帳戶列表） |
| `get_version` | `impl`（ErisPulse-SandboxAdapter）/ `version` / `onebot_version` |
| `get_supported_actions` | 支持的動作名列表 |

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

result = await sandbox.Api.get_self_info()   # 沙盒機器人身份
result = await sandbox.Api.get_status()
result = await sandbox.Api.get_version()
result = await sandbox.Api.get_supported_actions()
```

### 請求事件處理（Request stub）

沙盒會合成 `type="request"` 事件（好友/群申請，`request_id` 透傳自模擬事件），模組可用標準方式審批（完整規範見 [請求操作規範](../standards/request-action-spec.md)）：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    await event.approve()   # 或 event.reject()
```

適配器側 Request DSL 為**模擬樁**：`accept()` / `reject()` 校驗 `request_id`（缺失時返回標準錯誤 `retcode=34001`，屬於請求操作族錯誤碼），校驗通過後模擬審批成功返回標準成功響應，便於下游聯調 `approve()` / `reject()` 流程。

### 錯誤碼規範

| retcode | 含義 | 說明 |
|---------|------|------|
| 0 | 成功 | — |
| 10002 | 不支援 | 平台無對應能力 |
| 10003 | 參數錯誤 | 缺少或無效參數 |
| 10006 | 無效訊息段資料 | `MergeForward` 節點無有效文字內容 |
| 34001 | 請求不存在 | `Request.accept()/reject()` 缺少 `request_id`（請求操作族） |

## 配置說明

```toml
[Sandbox]
self_id = "sandbox_bot"  # 沙盒機器人ID
enable = true            # 是否啟用
```

## 使用說明

- 沙盒提供虛擬用戶與群組，模組可像真實平台一樣收發訊息
- Web 調試面板可手動發送訊息觸發模組處理邏輯
- 訊息資料持久化儲存（`sdk.storage`），重啟後可恢復

## 支援的消息發送類型

所有發送方法均透過鏈式語法實現，例如：

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

await sandbox.Send.To("private", "user1").Text("Hello")
await sandbox.Send.To("group", "group1").Markdown("**加粗**")
```

支援的發送類型包括：

| 方法 | 說明 |
|------|------|
| `.Text(text)` | 發送文字訊息 |
| `.Image(file, summary=None)` | 發送圖片 |
| `.Face(face_id)` | 發送表情 |
| `.Record(file, magic=False)` | 發送語音 |
| `.Voice(file)` | 發送語音（audio 通道） |
| `.Video(file)` | 發送影片 |
| `.File(file, filename=None)` | 發送檔案 |
| `.Html(html)` / `.HTML(html)` | 發送 HTML 訊息（後者為別名） |
| `.Markdown(markdown)` | 發送 Markdown 訊息 |
| `.Json(json_data)` | 發送 JSON 卡片訊息 |
| `.Xml(xml_data)` | 發送 XML 卡片訊息 |
| `.Music(platform, id, title=None)` | 發送音樂訊息 |
| `.Share(url, title, content=None, image=None)` | 發送連結分享 |
| `.Location(lat, lon, title=None, content=None)` | 發送位置訊息 |
| `.Dice()` | 發送骰子 |
| `.Rps()` | 發送猜拳 |
| `.Poke(user_id, type="poke")` | 戳一戳 |
| `.Recall(message_id)` | 模擬撤回訊息 |
| `.MergeForward(nodes, title="合併聊天記錄")` | 發送合併轉發訊息（渲染為 `<details>` 折疊 HTML 卡片，html 通道發出），用於驗證模組的合併轉發邏輯 |
| `.Raw_ob12(message)` | 發送 OneBot12 原始訊息段（純 node 列表自動路由合併轉發，混合列表 node 段降級為純文字） |

`At` / `AtAll` / `Reply` 修飾器由框架 SendDSL 基類提供。