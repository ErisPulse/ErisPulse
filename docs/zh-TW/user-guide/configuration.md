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

從 2.7.0 開始，框架對配置熱更新做了**系統化支援**。外部修改 `config.toml` 後（背景 watcher 每 5 秒檢測一次），或程式碼呼叫 `setConfig()` 後，各元件自動回應：

| 元件 | 支援熱更新的配置 | 行為 |
|------|----------------|------|
| **日誌 Logger** | `logger.level` / `log_files` / `memory_limit` / `format` / `exclude_levels` | 自動重新套用（帶變更檢測） |
| **命令系統 CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 下一條訊息即生效 |
| **適配器併發** | `framework.handler_max_concurrency` | 失效快取信號量，按新值重建 |
| **主動 GC** | `framework.proactive_gc_*` | 配置變更即時重新啟動 GC 任務，支援執行時調整/停用/重新啟用 |
| **主人系統 Master** | `master.users` | 每次 `is_master()` 檢查即時讀取，無需重啟 |
| **模組/適配器配置** | 各自的配置項 | 觸發 `on_config_update(old, new)` 回呼 |

**需重啟的配置**（無法安全熱切換，變更時會輸出告警「需重啟程序後生效」）：

| 配置 | 原因 |
|------|------|
| `router.cors.*` / `router.security.*` | 中間件在服務啟動時寫入 FastAPI，執行時無法安全熱切換 |
| `storage.use_global_db` | SQLite 檔案句柄已在執行時開啟，切換路徑不安全 |

> **中途編輯儲存出錯？** 若編輯 `config.toml` 時出現瞬間語法錯誤，框架會**保留上次有效配置**並輸出診斷日誌，不會把空配置廣播給各元件（避免 `on_config_update` 收到空值誤回退預設）。

[**English**](docs/zh-TW/quick-start.md)

## 完整設定範例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users 支援兩種寫法（二選一）：
#   全域主人（所有平台生效）：users = ["123456", "789012"]
#   按平台指定主人：users = { yunhu = ["123456"], telegram = ["789012"] }
users = {}

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
memory_limit = 1000
exclude_levels = []

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

## 伺服器設定

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聽位址，0.0.0.0 表示所有介面 |
| port | integer | 8000 | 監聽埠號 |
| auto_start | boolean | true | 是否在 `sdk.init()` 時自動啟動路由伺服器。設為 `false` 可跳過路由伺服器啟動（純事件/無 WebUI 場景） |
| ssl_certfile | string | 空 | SSL 證書檔案路徑 |
| ssl_keyfile | string | 空 | SSL 私鑰檔案路徑 |

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 主人系統配置

主人系統用於識別「框架主人」帳號（如 Bot 管理員）。`master.users` 支援兩種寫法：

```toml
[ErisPulse.master]
# 寫法一：全域主人（所有平台生效）
users = ["123456", "789012"]

# 寫法二：按平台指定主人（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| users | array / object | 空 | 主人帳號列表。`list` 形式為全域主人（所有平台生效）；`dict` 形式按平台指定（鍵為平台名，值為該平台的主人帳號列表） |

程式碼中透過 `master.is_master(event)` 或 `master.is_master(platform, user_id)` 檢查，每次呼叫即時讀取設定（支援熱更新，無需重啟）：

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("主人你好")
```

7. **重要：路徑替換規則**
   - 將文件連結中的 `docs/zh-TW/` 替換為 `docs/zh-TW/`
   - 例如：`docs/zh-TW/quick-start.md` 應改為 `docs/zh-TW/quick-start.md`
   - 對於指向非目前語言版本文件的連結（如 `README.xx.md` 形式的連結），保持原樣不要修改
   - 這確保連結指向正確語言的文件版本

## 日誌配置

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
exclude_levels = ["EVENT"]
```

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| level | string | INFO | 日誌級別：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE 為最低級別，輸出框架內部詳細調試信息） |
| format | string | rich | 日誌輸出格式：`rich`（彩色，默認）、`plain`（純文本無顏色，適合日誌採集/管道重定向）、`json`（JSON 結構化，適合 ELK 等） |
| log_files | array | 空 | 日誌輸出檔案列表 |
| memory_limit | integer | 1000 | 內存中保存的日誌條數 |
| exclude_levels | array | 空 | 屏蔽指定日誌等級。被屏蔽等級的日誌**完全丟棄**（不寫內存、不推送到 Dashboard 等訂閱器、不列印、不寫檔案）。支援熱更新 |

> **隱私保護**：訊息收發內容以 **EVENT 等級**（數值 21）記錄。設定 `exclude_levels = ["EVENT"]` 即可讓後台（如 Dashboard 日誌面板）無法看到各群/私聊的訊息內容，同時不影響其它等級日誌。

> [!NOTE]
> `exclude_levels` 本特性需要 ErisPulse **2.8.0+**。

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
| strict_mode | integer | 0 | 嚴格模式等級，見下方「嚴格模式」說明 |
| handler_max_concurrency | integer | 64 | 事件處理器最大併發 Task 數，設大提高吞吐但增加記憶體佔用 |
| offline_bot_expiry | integer | 3600 | 離線 Bot 記錄自動過期時間（秒），0 表示不過期 |

### 主動 GC 配置

SDK 初始化完成後啟動主動 GC 後台任務，周期性執行 Python GC 與內部資源回收（離線 Bot 清理等）。全部參數均支援熱更新，變更時即時重啟任務。

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回收間隔（秒），支援小數。0 表示禁用主動 GC |
| proactive_gc_generation | integer | 0 | 常規輪次回收分代（0/1/2，钳制到 0..2）。注意 `gc.collect(2)` 等價於全量回收，默認 0 保持輕量；深度回收由 `proactive_gc_full_every` 周期性觸發 |
| proactive_gc_full_every | integer | 20 | 每 N 輪做一次全量回收，0 表示禁用周期性全量。全量回收受 `proactive_gc_memory_growth_mb` 門限約束 |
| proactive_gc_memory_growth_mb | integer | 32 | 全量回收的記憶體增長門限（MB）：對比上次全量後的記憶體基線（優先 tracemalloc，其次 RSS），僅當增長達到此值才執行全量回收。0 表示不設門限 |
| proactive_gc_idle_only | boolean | false | 開啟後，事件洪峰（存在未完成的 pending handler）時本轮跳過 Python GC，避免停頓與消息處理競爭；內部資源回收不受影響 |
| proactive_gc_gen0_min | integer | 500 | 常規輪次觸發回收的 gen0 垃圾量下限：`gc.get_count()[0]` 低於此值直接跳過（空轉輪次近乎零開銷）。0 表示始終回收 |

> **2.7.1 變更**：默認 `proactive_gc_generation` 由 `2` 調整為 `0`，默認 `proactive_gc_full_every` 由 `0` 調整為 `20`。此前 `generation=2` 意味著每輪都做最重的全量回收；新默認在保持回收覆蓋的同時顯著降低空轉開銷。顯式配置的舊值仍按字面語義生效。

### 嚴格模式

嚴格模式控制模組/適配器在加載階段不合規或失敗時的處理策略。現代模組/適配器都應繼承對應的基類（`BaseModule`/`BaseAdapter`），未繼承基類的組件會影響框架的上下文系統與兜底清理，可能導致資源洩漏。

> **2.5.2 變更**：默認等級從 `1`（跳過）調整為 `0`（寬鬆），以減少新用戶初次使用時遇到的加載問題。未繼承基類的組件將以 WARNING 提示並嘗試加載，而非直接拒絕。如需恢復旧行為，請顯式設置 `strict_mode = 1`。

| 等級 | 名稱 | 行為 |
|------|------|------|
| 0 | 寬鬆（默認） | 違規僅警告，未繼承基類的組件仍會嘗試加載（兼容舊組件） |
| 1 | 嚴格-跳過 | 拒絕未繼承基類的組件並跳過，其餘正常啟動 |
| 2 | 嚴格-致命 | 收集所有違規後統一報告並中止整個啟動 |

各等級下，「加載/註冊/初始化階段報錯」這類組件自身崩潰始終會被跳過；區別在於：

- **0 → 1**：唯一行為變化是「未繼承基類」從「仍加載」變為「跳過」。
- **1 → 2**：所有違規（未繼承基類、加載失敗、註冊失敗、初始化失敗等）升級為致命，會在啟動檢查點收集後一次性輸出違規清單並中止。

#### 豁免清單

如果某些組件確實暫時無法遷移（例如依賴的舊模組），可以將其加入豁免清單，被列名的組件即使不合規也會按寬鬆模式對待，繼續加載：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> 當某個組件被嚴格模式拒絕時，日誌會明確提示如何恢復加載（加入豁免清單或調低等級）。

## 儲存設定

```toml
[ErisPulse.storage]
use_global_db = false
```

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| use_global_db | boolean | false | 是否使用全域資料庫（包內）而非專案資料庫。`true` 時所有專案共用 ErisPulse 包內的 SQLite 資料庫；`false`（預設）時每個專案使用 `config/` 目錄下獨立的資料庫 |

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 事件設定

### 命令設定

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
```

| 設定項目 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| prefix | string | / | 命令前綴 |
| case_sensitive | boolean | true | 是否區分大小寫（`/Help` 與 `/help` 是否為不同命令） |
| allow_space_prefix | boolean | false | 是否允許空格作為前綴 |
| must_at_bot | boolean | false | 是否必須@機器人才能觸發命令（私聊不受限制） |

### 消息設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 是否忽略機器人自己的訊息 |

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

## 作用域配置

> [!NOTE]
> 此功能需要 ErisPulse **2.8.0+**。

模組作用域系統用於控制「某個 Bot 只能使用哪些模組」。預設情況下所有模組對所有 Bot 開放，僅在配置綁定後才開始過濾，模組與適配器**無需任何修改**即可適配。

```toml
[ErisPulse.scope]
default_allow = true        # 預設允許全部（false = 隱式拒絕嚴格模式）
cache_size = 1024           # is_allowed 的 LRU 快取大小
```

| 配置項 | 類型 | 說明 |
|---------|------|------|
| `scope.default_allow` | boolean | 預設允許全部模組（`true`）。`false` = 隱式拒絕嚴格模式，僅白名單內模組可用 |
| `scope.cache_size` | integer | `is_allowed` 的 LRU 快取大小（預設 1024） |
| `scope.platforms.<platform>.modules` | array | 平台級白名單：僅列出的模組允許使用（空 = 不限制） |
| `scope.platforms.<platform>.blocked` | array | 平台級黑名單：列出的模組禁用（空 = 不限制） |
| `scope.bots.<platform>.<bot_id>.modules` | array | Bot 級白名單，覆蓋平台級 |
| `scope.bots.<platform>.<bot_id>.blocked` | array | Bot 級黑名單，覆蓋平台級 |
| `scope.sessions.<platform>.<session_id>.modules` | array | 會話級白名單（群/頻道/私聊），優先級最高 |
| `scope.sessions.<platform>.<session_id>.blocked` | array | 會話級黑名單，優先級最高 |

> 解析優先級：**會話級 > Bot 級 > 平台級**。三級綁定的完整 TOML 範例、模組名大小寫不敏感、會話標識跨平台隔離、執行時 `sdk.scope.bind()` / `unbind()` 動態增刪（`merge=True` 可合併）等詳見[作用域系統](../advanced/scope.md)。

## 下一步

- [CLI 命令參考](cli-reference.md) - 了解所有命令行命令
- [開發者指南](../developer-guide/) - 學習開發自訂模組