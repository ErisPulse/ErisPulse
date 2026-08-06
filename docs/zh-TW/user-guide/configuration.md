# 配置文件說明  
> 本文件將介紹框架的配置文件。若有第三方模組需要設定，請參考模組的文件。

ErisPulse 使用 TOML 格式的配置文件 `config/config.toml` 來管理專案設定。

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 配置檔位置

配置檔位於專案根目錄的 `config/` 資料夾中：

```
project/
├── config/
│   └── config.toml
├── main.py
```

7. **重要：路徑替換規則**
   - 將文件連結中的 `docs/zh-TW/` 替換為 `docs/zh-TW/`
   - 例如：`docs/zh-TW/quick-start.md` 應改為 `docs/zh-TW/quick-start.md`
   - 對於指向非目前語言版本文件的連結（如 `README.xx.md` 形式的連結），保持原樣不要修改
   - 這確保連結指向正確語言的文件版本

## 配置載入錯誤處理

框架在載入 `config.toml` 時會區分三種錯誤狀態，並提供**可操作的診斷資訊**，而不是靜默回退到預設配置：

| 錯誤狀態 | 觸發條件 | 框架行為 |
|---------|---------|---------|
| 檔案缺失 | `config.toml` 不存在 | 正常首次啟動，靜默使用空配置（不發出警告） |
| TOML 語法錯誤 | 檔案存在但格式非法（如少了引號、括號未閉合） | 輸出**出錯行號/列號與原因**，並提示已回退預設配置 |
| 權限/其他錯誤 | 無讀取權限、IO 錯誤等 | 輸出**明確原因**，並提示已回退預設配置 |

例如，當你不慎把配置寫成了 `port = 8000`（缺少引號的字串）時，日誌會輸出類似：

```
[ERROR] [Config] 配置檔案 config/config.toml 語法錯誤（第 3 行 第 1 列）: ...
[WARNING] [Config] 配置檔案讀取失敗。繼續使用上次有效配置執行，本次檔案修改未生效——請修復後重新載入或重啟
```

這樣你可以在**預設 INFO 級別**下立刻定位問題，而不會困惑「為什麼我修改的配置沒生效」。

> **執行中改壞配置檔案？** 如果你在機器人執行期間手動編輯 `config.toml` 引入了語法錯誤，框架在下次寫入（合併配置）時會輸出「配置檔案已損壞（語法錯誤，第 X 行），無法合併寫入——請先修復配置檔案後重啟」，而不是令人困惑的「寫入失敗」。待寫入的配置項目會被保留，不會遺失。

## 環境變數覆蓋

框架支援使用環境變數**覆蓋** `ErisPulse.*` 配置項目（適合 Docker / 容器化 / CI 部署，無需修改 `config.toml`）。

命名規則：將點分路徑 `ErisPulse.<section>.<key>` 改為全大寫、`.` 替換為 `_`，並加上 `ERISPULSE_` 前綴：

| 配置項 | 環境變數 | 示例值 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `false` |

行為說明：
- **優先級最高**：環境變數覆蓋「配置檔案」與「預設值」，並按原值類型自動轉換（`bool` / `int` / `float` / 逗號分隔的 `list` / 字串）
- **不持久化**：覆蓋只在執行期生效，不會寫回 `config.toml`
- **支援熱更新**：執行中修改環境變數後，配合配置監聽的重載即可生效

```bash
# Docker 部署示例：不修改 config.toml，直接覆蓋端口
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 註：`ErisPulse.server.port` 這類框架配置走 `get_server_config()` 等 API 讀取，均受環境變數覆蓋影響。

## 配置熱更新

從 2.7.0 開始，框架對配置熱更新做了**系統化支援**。外部修改 `config.toml` 後（後台 watcher 每 5 秒偵測一次），或程式碼呼叫 `setConfig()` 後，各元件自動回應：

| 元件 | 支援熱更新的設定 | 行為 |
|------|----------------|------|
| **日誌 Logger** | `logger.level` / `log_files` / `memory_limit` / `format` | 自動重新套用（帶變更偵測） |
| **命令系統 CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 下一條訊息即生效 |
| **適配器併發** | `framework.handler_max_concurrency` | 失效快取信號量，按新值重建 |
| **主動 GC** | `framework.proactive_gc_interval` | 每輪重讀，支援執行時調整/停用 |
| **主人系統 Master** | `master.users` | 每次 `is_master()` 檢查即時讀取，無需重新啟動 |
| **模組/適配器設定** | 各自的設定項目 | 觸發 `on_config_update(old, new)` 回呼 |

**需重新啟動的設定**（無法安全熱切換，變更時會輸出告警「需重新啟動程序後生效」）：

| 設定 | 原因 |
|------|------|
| `router.cors.*` / `router.security.*` | 中間件在服務啟動時寫入 FastAPI，執行時無法安全熱切換 |
| `storage.use_global_db` | SQLite 檔案句柄已在執行時開啟，切換路徑不安全 |

> **中途編輯儲存出錯？** 若編輯 `config.toml` 時出現瞬間語法錯誤，框架會**保留上次有效設定**並輸出診斷日誌，不會把空設定廣播給各元件（避免 `on_config_update` 收到空值誤回退預設）。

[**English**](docs/zh-TW/quick-start.md)

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

[**English**](docs/zh-TW/quick-start.md) | [**简体中文**](docs/zh-TW/quick-start.md)

## 伺服器設定

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聽位址，0.0.0.0 表示所有介面 |
| port | integer | 8000 | 監聽埠號 |
| ssl_certfile | string | 空 | SSL 證書檔案路徑 |
| ssl_keyfile | string | 空 | SSL 私鑰檔案路徑 |

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

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
| format | string | rich | 日誌輸出格式：`rich`（彩色，預設）、`plain`（純文本無顏色，適合日誌採集/管道重定向）、`json`（JSON 結構化，適合 ELK 等） |
| log_files | array | 空 | 日誌輸出檔案清單 |
| memory_limit | integer | 1000 | 在記憶體中保存的日誌條數 |

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

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

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | 是否啟用模組懶加載 |
| uninit_timeout | integer | 30 | 優雅關閉的總超時時間（秒），超過後強制終止。0 表示不設超時 |
| strict_mode | integer | 0 | 嚴格模式級別，見下方「嚴格模式」說明 |

### 嚴格模式

嚴格模式控制模組/適配器在加載階段不合規或失敗時的處理策略。現代模組/適配器都應繼承對應的基類（`BaseModule`/`BaseAdapter`），未繼承基類的組件會影響框架的上下文系統與兜底清理，可能導致資源洩漏。

> **2.5.2 變更**：默認級別從 `1`（跳過）調整為 `0`（寬鬆），以減少新用戶初次使用時遇到的加載問題。未繼承基類的組件將以 WARNING 提示並嘗試加載，而非直接拒絕。如需恢復旧行為，請顯式設定 `strict_mode = 1`。

| 級別 | 名稱 | 行為 |
|------|------|------|
| 0 | 寬鬆（默認） | 違規僅警告，未繼承基類的組件仍會嘗試加載（相容舊組件） |
| 1 | 嚴格-跳過 | 拒絕未繼承基類的組件並跳過，其餘正常啟動 |
| 2 | 嚴格-致命 | 收集所有違規後統一報告並中止整個啟動 |

各級別下，「加載/註冊/初始化階段報錯」這類組件自身崩潰始終會被跳過；區別在於：

- **0 → 1**：唯一行為變化是「未繼承基類」從「仍加載」變為「跳過」。
- **1 → 2**：所有違規（未繼承基類、加載失敗、註冊失敗、初始化失敗等）升級為致命，會在啟動檢查點收集後一次性輸出違規清單並中止。

#### 豁免清單

如果某些組件確實暫時無法遷移（例如依賴的舊模組），可以將其加入豁免清單，被列名的組件即使不合規也會按寬鬆模式對待，繼續加載：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> 當某個組件被嚴格模式拒絕時，日誌會明確提示如何恢復加載（加入豁免清單或調低級別）。

## 儲存設定

```toml
[ErisPulse.storage]
use_global_db = false
```

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| use_global_db | boolean | false | 是否使用全域資料庫（包內）而非專案資料庫。`true` 時所有專案共用 ErisPulse 包內的 SQLite 資料庫；`false`（預設）時每個專案使用 `config/` 目錄下獨立的資料庫 |

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 事件配置

### 命令配置

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| 配置項 | 類型 | 默認值 | 說明 |
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

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 是否忽略機器人自己的消息 |

## 國際化配置

```toml
[ErisPulse.i18n]
language = "auto"
```

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| language | string | auto | 框架內置文本的顯示語言。設為 `auto` 自動檢測系統語言，也可設為具體代碼：`zh-CN`、`zh-TW`、`en`、`ja`、`ru` |

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

## 模組配置

每個模組可以在配置檔中定義自己的設定：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

在模組中讀取和寫入設定：

```python
from ErisPulse import sdk

# 讀取設定
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 運行時寫入設定（延遲儲存）
sdk.config.setConfig("MyModule.timeout", 60)

# 立即儲存到檔案
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` 預設採用延遲寫入（約每 5 秒批量儲存到檔案），設定 `immediate=True` 可立即持久化。設定變更會觸發 `config.set` 生命週期事件。

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 下一步

- [CLI 命令參考](cli-reference.md) - 了解所有命令行命令
- [開發者指南](../developer-guide/) - 學習開發自訂模組