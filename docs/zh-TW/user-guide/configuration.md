# 配置文件說明  
> 這個文件將介紹框架的配置文件。如果有第三方模組需要配置，請參考模組的文件。

ErisPulse 使用 TOML 格式的配置文件 `config/config.toml` 來管理項目配置。

## 配置文件位置

配置文件位於項目根目錄的 `config/` 文件夾中：

```
project/
├── config/
│   └── config.toml
├── main.py
```

## 配置載入錯誤處理

框架在載入 `config.toml` 時會區分三種錯誤狀態，並提供**可操作的診斷資訊**，而不是靜默回退到預設配置：

| 錯誤狀態 | 觸發條件 | 框架行為 |
|---------|---------|---------|
| 文件缺失 | `config.toml` 不存在 | 正常首次啟動，靜默使用空配置（不發出警告） |
| TOML 語法錯誤 | 文件存在但格式非法（例如少了引號、括號未閉合） | 輸出**錯誤行號/列號與原因**，並提示已回退預設配置 |
| 權限/其他錯誤 | 無讀取權限、IO 錯誤等 | 輸出**明確原因**，並提示已回退預設配置 |

例如，當你不小心把配置寫成了 `port = 8000`（少了引號的字串）時，日誌會輸出類似：

```
[ERROR] [Config] 配置文件 config/config.toml 語法錯誤（第 3 行 第 1 列）: ...
[WARNING] [Config] 已回退到預設配置，您的自訂設定未生效——請修復後重啟
```

這樣你可以在**預設的 INFO 級別**下立刻定位問題，而不會困惑「為什麼我改的配置沒生效」。

> **運行中改壞配置文件？** 如果你在機器人運行期間手動編輯 `config.toml` 引入了語法錯誤，框架在下次寫入（合併配置）時會輸出「配置文件已損壞（語法錯誤，第 X 行），無法合併寫入——請先修復配置文件後重啟」，而不是令人困惑的「寫入失敗」。待寫入的配置項會被保留，不會丟失。

## 完整配置示例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
memory_limit = 1000

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true

[ErisPulse.i18n]
language = "auto"
```

## 伺服器配置

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聽位址，0.0.0.0 表示所有介面 |
| port | integer | 8000 | 監聽埠號 |
| ssl_certfile | string | 空 | SSL 證書檔路徑 |
| ssl_keyfile | string | 空 | SSL 私鑰檔路徑 |

## 日誌配置

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| level | string | INFO | 日誌等級：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE 為最低等級，輸出框架內部詳細除錯資訊） |
| format | string | rich | 日誌輸出格式，預設使用 rich 彩色輸出 |
| log_files | array | 空 | 日誌輸出檔案列表 |
| memory_limit | integer | 1000 | 內存中保存的日誌條數 |

## 框架配置

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | 是否啟用模組懶加載 |
| uninit_timeout | integer | 30 | 優雅關閉的總超時時間（秒），超過後強制終止。0 表示不設超時 |
| strict_mode | integer | 0 | 嚴格模式等級，見下方「嚴格模式」說明 |

### 嚴格模式

嚴格模式控制模組/適配器在加載階段不合規或失敗時的處理策略。現代模組/適配器都應繼承對應的基類（`BaseModule`/`BaseAdapter`），未繼承基類的元件會影響框架的上下文系統與兜底清理，可能導致資源洩漏。

> **2.5.2 變更**：預設等級從 `1`（跳過）調整為 `0`（寬鬆），以減少新用戶初次使用時遇到的加載問題。未繼承基類的元件將以 WARNING 提示並嘗試加載，而非直接拒絕。如需恢復舊行為，請顯式設置 `strict_mode = 1`。

| 等級 | 名稱 | 行為 |
|------|------|------|
| 0 | 寬鬆（預設） | 違規僅警告，未繼承基類的元件仍會嘗試加載（相容舊元件） |
| 1 | 嚴格-跳過 | 拒絕未繼承基類的元件並跳過，其餘正常啟動 |
| 2 | 嚴格-致命 | 收集所有違規後統一報告並中止整個啟動 |

各等級下，「加載/註冊/初始化階段報錯」這類元件自身崩潰始終會被跳過；區別在於：

- **0 → 1**：唯一行為變化是「未繼承基類」從「仍加載」變為「跳過」。
- **1 → 2**：所有違規（未繼承基類、加載失敗、註冊失敗、初始化失敗等）升級為致命，會在啟動檢查點收集後一次性輸出違規清單並中止。

#### 豁免清單

如果某些元件確實暫時無法遷移（例如依賴的舊模組），可以將其加入豁免清單，被列名的元件即使不合規也會按寬鬆模式對待，繼續加載：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> 當某個元件被嚴格模式拒絕時，日誌會明確提示如何恢復加載（加入豁免清單或調低等級）。

## 存儲配置

```toml
[ErisPulse.storage]
use_global_db = false
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| use_global_db | boolean | false | 是否使用全域資料庫（包內）而非項目資料庫。`true` 時所有項目共享 ErisPulse 包內的 SQLite 資料庫；`false`（預設）時每個項目使用 `config/` 目錄下獨立的資料庫 |

## 事件配置

### 命令配置

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| prefix | string | / | 命令前綴 |
| case_sensitive | boolean | true | 是否區分大小寫（`/Help` 與 `/help` 是否為不同命令） |
| allow_space_prefix | boolean | false | 是否允許空格作為前綴 |
| must_at_bot | boolean | false | 是否必須@機器人才能觸發命令（私聊不受限制） |

### 消息配置

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 是否忽略機器人自己的訊息 |

## 國際化配置

```toml
[ErisPulse.i18n]
language = "auto"
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| language | string | auto | 框架內建文本的顯示語言。設為 `auto` 自動檢測系統語言，也可設為具體代碼：`zh-CN`、`zh-TW`、`en`、`ja`、`ru` |

## 模組配置

每個模組可以在配置文件中定義自己的配置：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

在模組中讀取和寫入配置：

```python
from ErisPulse import sdk

# 讀取配置
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 運行時寫入配置（延遲保存）
sdk.config.setConfig("MyModule.timeout", 60)

# 立即保存到文件
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` 預設採用延遲寫入（約每 5 秒批量保存到文件），設置 `immediate=True` 可立即持久化。配置變更會觸發 `config.set` 生命週期事件。

## 下一步

- [CLI 命令參考](docs/zh-TW/cli-reference.md) - 了解所有命令列命令
- [開發者指南](docs/zh-TW/developer-guide/) - 學習開發自訂模組