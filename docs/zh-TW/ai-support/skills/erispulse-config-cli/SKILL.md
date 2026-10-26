---
name: erispulse-config-cli
description: "适用于：配置声明式 schema、排查配置问题、使用 epsdk 命令行与部署。覆盖场景：- 連線參數變更後需重啟框架生效；連線池建立瞬時失敗會自動指數退避重試。忘記某個 `epsdk` 指令的參數、想把元件管理寫進腳本，或要控制 run / stop / restart 行為時查閱。日常只用 `init` / `install` / `run` 的話，記住一條就夠：`epsdk <指令> --help` 隨時可查參數說明，不需要通讀本文。**何時需要閱讀本文**：需要選擇一種安裝方式（pip / uv / Docker / ErisPulse-App 客戶端），或遇到安裝失敗需要排查時閱讀。只想快速運行，[5 分鐘快速入門](../quick-start.md) 已涵蓋最簡流程，不需要則跳過。機器人要長期掛著跑時——Docker 部署、systemd / Supervisor 程序守護、反向代理與 SSL、備份與升級都在這裡。本地開發除錯階段不需要則跳過。"
---

# ErisPulse 配置系统与 CLI 工具链

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 配置系统: 65-76 行
- 配置文件位置: 78-95 行
- 配置載入錯誤處理: 97-118 行
- 注釋保留與最小化落盤: 120-140 行
- 環境變數覆蓋: 142-196 行
- 配置熱更新: 198-266 行
- 配置讀取與刪除 API: 268-294 行
- 完整配置範例: 296-348 行
- 伺服器配置: 350-378 行
- 主人系統配置: 380-452 行
- 日誌設定: 454-502 行
- 框架設定: 504-575 行
- 存儲配置: 577-624 行
- 事件配置: 626-653 行
- 會話收件匣配置（transcript）: 655-672 行
- 國際化配置: 674-683 行
- 模組配置: 685-712 行
- 作用域配置（scope）: 714-762 行
- 統一事件覆寫配置（event.overrides）: 764-809 行
- CLI 参考: 811-824 行
- 套件管理命令: 826-833 行
- 臨床命令: 835-989 行
- 資訊查詢命令: 991-1054 行
- 配置命令: 1056-1107 行
- 運行控制命令: 1109-1207 行
- 專案管理命令: 1209-1319 行
- 語言命令: 1321-1356 行
- 類型存根命令: 1358-1397 行
- 全域參數: 1399-1412 行
- 環境診斷: 1414-1455 行
- 互動式安裝: 1457-1468 行
- 常見用法: 1470-1597 行
- 安装: 1599-1606 行
- 系統要求: 1608-1612 行
- 安裝方式: 1614-1689 行
- 專案初始化與模組安裝: 1691-1705 行
- 驗證安裝: 1707-1730 行
- 常見問題: 1732-1774 行
- 部署: 1776-1785 行
- Docker 部署（推薦）: 1787-1877 行
- Dashboard 管理面板: 1879-1905 行
- 程序監督與硬重啟: 1907-1916 行
- 健康檢查: 1918-1938 行
- 反向代理: 1940-1970 行
- 手動部署（pip）: 1972-2063 行
- 安全建議: 2065-2072 行
- 多實例部署: 2074-2080 行
- 更新與維護: 2082-2136 行

## 配置系统

> 来源: `docs/zh-TW/user-guide/configuration.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/user-guide/configuration.md）

# 配置文件說明

> [!NOTE]
> **L1 核心必讀**——首頁「閱讀路徑」中的五篇核心文件之一，模組開發必備。

> 這篇講框架自身的配置文件 `config/config.toml`：每個配置節管什麼、哪些支援熱更新、如何用環境變數覆蓋。第三方模組的配置項請參考模組自己的文件。

ErisPulse 使用 TOML 格式的配置文件 `config/config.toml` 來管理專案配置。

## 配置文件位置

配置文件位於專案根目錄的 `config/` 資料夾中：

```
project/
├── config/
│   └── config.toml
├── main.py
```

### 多實例提示與鎖檔案

框架啟動時會在專案根的執行狀態目錄 **`.erispulse/`** 下建立 `config.lock` 鎖檔案並持有到進程退出（用於偵測多實例共享配置目錄；2.10 及以前位於 `config/` 目錄的 `.erispulse_config.lock` 會在升級後首次啟動時自動清除）。如果日誌出現「偵測到配置檔案可能正被另一個 ErisPulse 實例同時使用」的告警，說明有**兩個以上的 ErisPulse 進程在寫同一份配置**（典型場景：多個容器掛載了同一個宿主機 `config/` 目錄）——併發寫入會互相覆蓋，請為每個實例使用獨立的配置目錄。

### 敏感配置不入庫

配置檔案含令牌（token / API key）等敏感資訊：框架初始化與 `epsdk init` 會自動在 `config/` 目錄生成 `.gitignore`（內容僅一行 `*`——**目錄內全部檔案不入版本庫，忽略檔案自身也在排除範圍內**）；已存在的 `.gitignore` 不會被覆蓋。`.erispulse/` 運行狀態目錄（實例鎖、CLI 運行狀態檔案）同屬機器本地狀態，專案範本的 `.gitignore` 已預設忽略。

## 配置載入錯誤處理

框架在載入 `config.toml` 時會區分三種錯誤狀態，並給出**可操作的診斷資訊**，而不是靜默回退到預設配置：

| 錯誤狀態 | 觸發條件 | 框架行為 |
|---------|---------|---------|
| 檔案遺失 | `config.toml` 不存在 | 正常首次啟動，靜默使用空配置（不發警告） |
| TOML 語法錯誤 | 檔案存在但格式非法（如少了引號、括號未閉合） | 輸出**出錯行號/列號與原因**，並**保留上次有效配置繼續運行**（本次檔案修改不生效） |
| 權限/其他錯誤 | 無讀權限、IO 錯誤等 | 輸出**明確原因**，並**保留上次有效配置繼續運行** |

> **注意"上次有效配置"≠ 預設配置**：檔案損壞時框架沿用**本次啟動前最後一份解析成功的配置**（運行中熱更新改壞檔案則沿用舊值），而不是把所有配置項重置為出廠預設。故障處置時不要假設「配置已被重置」。

例如，當你不慎把配置寫成了 `port = 8000`（少了引號的字串）時，日誌會輸出類似：

```
[ERROR] [Config] 配置檔案 config/config.toml 語法錯誤（第 3 行 第 1 列）: ...
[WARNING] [Config] 配置檔案讀取失敗。繼續使用上次有效配置運行，本次檔案修改未生效——請修復後重新載入或重啟
```

這樣你可以在**預設 INFO 級別**下立刻定位問題，而不會困惑「為什麼我改的配置沒生效」。

> **運行中改壞配置檔案？** 如果你在機器人運行期間手動編輯 `config.toml` 引入了語法錯誤，框架在下次寫入（合併配置）時會輸出「配置檔案已損壞（語法錯誤，第 X 行），無法合併寫入——請先修復配置檔案後重啟」，而不是令人困惑的「寫入失敗」。待寫入的配置項會被保留，不會遺失。

## 注釋保留與最小化落盤

config.toml 中的**注釋與鍵順序在框架寫入後完整保留**：無論是程式碼 `setConfig()`、
CLI 配置向導保存還是適配器/模組首次生成配置範本，框架都只改動涉及的鍵，
你寫的注釋、整理的順序不會被抹掉或重排（基於 tomlclass 無損 TOML 引擎，
未觸碰的內容逐字節保真，檔案原有的 CRLF/LF 行尾風格也不會被改變）。

框架對落盤內容保持克制：

- **框架預設配置不自動落盤**：`gc`、`scope`、`transcript` 等內建預設值僅駐記憶體，
  config.toml 只包含你顯式設定的鍵，保持最小化。完整可配置項參考專案內的
  `config/config.full.example`，按需複製到 config.toml 修改即可（未配置項一律走內建預設值，行為不變）
- **`config.full.example` 自動維護**：無論是否執行過 `epsdk init`，只要啟動框架
  （`epsdk run` / `main.py`），都會在 `config/config.full.example` 缺失時自動生成
  完整配置參考；檔案首行為框架自維護標記，生成器內容更新（如新增配置項、新裝
  組件）時啟動會刷新一次，刪除/改動首行即轉為手動接管、框架不再覆蓋
- **適配器/模組配置範本**：首次初始化時以帶注釋的範本落盤（字段描述即注釋）；
  聲明為 `example` 標誌的字段不落盤，僅記錄在 config.full.example 供參考
- **宣告式注釋回讀**：配置檔案裡的注釋本身就是文件——`ep doctor` 與配置校驗
  失敗提示會引用該字段在檔案中的注釋原文（即使你手動改過注釋，提示跟隨檔案
  現狀），報錯時無需再翻文件查找字段含義

## 環境變數覆蓋

框架支援用環境變數**覆蓋** `ErisPulse.*` 配置項（適合 Docker / 容器化 / CI 部署，無需修改 `config.toml`）。

命名規則：把點分路徑 `ErisPulse.<section>.<key>` 改為全大寫、`.` 替換為 `_`，並加上 `ERISPULSE_` 前綴：

| 配置項 | 環境變數 | 示例值 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

行為說明：
- **優先級最高**：環境變數覆蓋「配置檔案」與「預設值」，按原值類型自動轉換（`bool` / `int` / `float` / 逗號分隔的 `list` / 字串）
- **不持久化**：覆蓋只在運行期生效，不會寫回 `config.toml`
- **支援熱更新**：運行中修改環境變數後，配合配置監聽的重載即可生效

```bash
# Docker 部署示例：不修改 config.toml，直接覆蓋端口
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` 這類框架配置走 `get_server_config()` 等 API 讀取，均受環境變數覆蓋影響。

### 模組配置的環境變數綁定（2.9.0+）

模組自己的宣告式配置（`ConfigClass`）支援字段級環境變數綁定——在 `field(metadata=...)` 中聲明 `env`：

```python
@dataclass
class MyConfig(BaseConfig):
    api_key: str = field(default="", metadata={
        "description": "API 密鑰",
        "env": "MYMODULE_API_KEY",   # 環境變數綁定
    })
    retries: int = field(default=3, metadata={"env": "MYMODULE_RETRIES"})
```

行為說明：

- **優先級**：環境變數 > `config.toml` > 宣告預設值（配置檔案熱更新後同樣保持此優先級）
- **類型轉換**：環境變數值按字段註解自動轉換——`str` 原樣、`int` / `float` / `bool`（`true` / `1` / `yes` / `on`）自動轉換、`list` / `dict` 走 JSON 解析；轉換失敗時忽略該覆蓋（回退配置檔案 / 預設值）並輸出告警
- **宣告一處、處處生效**：配置讀取、熱更新、校驗使用同一管道；配置面板 Schema 會標註 `env` 名，`config.toml` 範本注釋也會提示可用的環境變數（範本不寫入環境變數的實際值，避免洩露）
- **完全相容**：未聲明 `env` 的字段行為不變；直接實例化 ConfigClass（不經框架配置管道）不受環境變數影響

```bash
# Docker 部署示例：不修改 config.toml，直接注入模組密鑰
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **配置類 vs 模型字段怎麼選？** 配置類管「模組怎麼運轉」（行為參數、熱更新），
> ORM 的 `Field()` 管「用戶產生了什麼資料」（資料庫表、查詢）。兩者共享同一套
> 約束詞表與校驗器引擎；對照表見
> [資料模型層 · 兩種宣告何時用哪個](../developer-guide/orm.md#兩種宣告何時用哪個)。

## 配置熱更新

從 2.7.0 起，框架對配置熱更新做了**系統化支援**。外部修改 `config.toml` 後（後台 watcher 每 5 秒檢測一次），或程式碼呼叫 `setConfig()` 後，各組件自動回應：

| 組件 | 支援熱更新的配置 | 行為 |
|------|----------------|------|
| **日誌 Logger** | `logger.level` / `log_files` / `log_dir`（含分段參數）/ `memory_limit` / `format` / `exclude_levels` | 自動重新應用（帶變更檢測） |
| **命令系統 CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 下一條訊息即生效 |
| **適配器併發** | `framework.handler_max_concurrency` | 失效快取信號量，按新值重建 |
| **主動 GC** | `framework.proactive_gc_*` | 配置變更即時重啟 GC 任務，支援運行時調整/禁用/重新啟用 |
| **主人系統 Master** | `master.users` | 每次 `is_master()` 檢查實時讀取，無需重啟 |
| **模組/適配器配置** | 各自的配置項 | 觸發 `on_config_update(old, new)` 回調 |

**需重啟的配置**（無法安全熱切換，變更時會輸出告警「需重啟進程後生效」）：

| 配置 | 原因 |
|------|------|
| `router.cors.*` / `router.security.*` | 中間件在服務啟動時寫入 FastAPI，運行時無法安全熱切換 |
| `storage.use_global_db` | SQLite 檔案句柄已在運行時打開，切換路徑不安全 |

> **中途編輯保存出錯？** 若編輯 `config.toml` 時出現瞬時語法錯誤，框架會**保留上次有效配置**並輸出診斷日誌，不會把空配置廣播給各組件（避免 `on_config_update` 收到空值誤回退預設）。

### 熱更新鏈路內部拆解

「改了配置，各組件怎麼知道的？」——背後是一條檢測 → 重載 → 廣播的鏈路：

```mermaid
flowchart TD
    A["外部編輯 config.toml"] --> B{"誰先發現？"}
    B -->|"後台 watcher 線程<br/>每 5 秒輪詢 mtime"| C["_check_file_change 判定變更"]
    B -->|"程式碼讀取配置時<br/>快取超 60 秒"| C
    C --> D["_load_config 重新解析 TOML"]
    D --> E{"解析成功？"}
    E -->|"否（語法錯誤）"| F["保留上次有效配置<br/>不廣播，打診斷日誌"]
    E -->|"是"| G["lifecycle.emit config.updated<br/>攜帶 old_config / new_config"]
    G --> H["各組件監聽者回應<br/>（logger / scope / 命令 / GC ...）"]
```

**兩條檢測路徑**（取其一即可，均能兜底）：

| 路徑 | 機制 | 觸發時機 |
|------|------|---------|
| 後台 watcher | daemon 線程 `config-watcher` 每 **5 秒** `wait` 輪詢檔案 `mtime` | 外部改檔案後最多 5 秒內 |
| 慢性檢測 | 任何 `getConfig()` 讀取時，若快取超過 **60 秒**則先查檔案 | 下次讀配置時 |

> **框架不會誤傷自己**：`setConfig()` 寫盤時會記錄「自身寫入的 mtime」，watcher 對比時把它排除，只把**外部編輯**視為變更。

**兩類配置變更事件：**

| 事件 | 觸發者 | 數據 | 典型場景 |
|------|--------|------|---------|
| `config.set` | 程式碼 / Dashboard 調 `setConfig()` | `{key, old_value, new_value}` | 單鍵寫入（範本生成、狀態記錄、運行時改配置） |
| `config.updated` | 外部編輯後 watcher/慢性檢測捕獲 | `{old_config, new_config, config_file}` | 手改 `config.toml` |

> `setConfig()` 預設**延遲 5 秒落盤**（合併多次寫入），`immediate=True` 立即寫。watcher 檢測到外部修改後只更新記憶體快取，**不會**把外部變更回寫檔案。

**自動回應方清單**（兩類事件通常會都訂閱，回應內容一致）：

| 組件 | 監聽 | 回應 |
|------|------|------|
| Logger | `config.set` + `config.updated` | 級別/檔案/目錄分段/記憶體上限/格式/屏蔽等級重新應用（帶變更檢測，無變化不動） |
| Scope | `config.updated` | 作用域綁定快取重建 |
| 命令系統 | `config.updated` | 前綴/大小寫/空格前綴/must_at_bot 解析參數刷新，下一條訊息生效 |
| 適配器併發 | `config.set` + `config.updated` | `handler_max_concurrency` 失效重建信號量 |
| 主動 GC | `config.set` + `config.updated` | `proactive_gc_*` 即時重啟 GC 後台任務 |
| 適配器 | 路由到 `on_config_update` | 各適配器 `on_config_update(old, new)` 回調 |
| 模組 | 路由到 `on_config_update` | 各模組 `on_config_update(old, new)` 回調 |
| 存儲 | `config.updated` | `use_global_db` 變更**僅告警**（需重啟） |
| 路由 | `config.updated` | `cors.*` / `security.*` 變更**僅告警**（需重啟） |

## 配置讀取與刪除 API

### getAllConfig：全量配置快照

替代直接讀取私有 `_cache`（外部讀私有屬性不受版本相容保護）：

```python
config = sdk.config.getAllConfig()     # 深拷貝快照，原地修改不受框架狀態影響
config["ErisPulse"]["server"]["port"]
```

視圖口徑與 `getConfig` 一致：未落盤的 `setConfig` / `delete` 均已反映，
與延遲刷盤後的檔案內容嚴格一致。

### delConfig：刪除配置鍵

`setConfig(key, None)` 只是置空、鍵仍保留在檔案中；`delConfig` 會把鍵從檔案中**移除**：

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # 延遲寫入
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # 立即落盤
```

- 支援點分路徑；鍵不存在時回傳 `False`
- 落盤走註解保留路徑，檔案其餘內容與順序不受影響
- 複用 `config.set` 事件廣播（`new_value=None`）：適配器 / 模組的
  `on_config_update` 等現有監聽方零改動即可感知刪除

## 完整配置範例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users 支援兩種寫法（二選一）：
#   全局主人（所有平台生效）：users = ["123456", "789012"]
#   按平台指定主人：users = { yunhu = ["123456"], telegram = ["789012"] }
users = {}

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
log_dir = ""
log_rotation = "size"
log_max_size_mb = 10
log_backup_count = 5
log_rotation_when = "midnight"
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
backend = "sqlite"
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
auto_start = true
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
# 容器 / 無檔案掛載場景可內聯 PEM 內容（優先級高於 certfile/keyfile 路徑）
# ssl_cert = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
# ssl_key = """-----BEGIN PRIVATE KEY-----
# ...
# -----END PRIVATE KEY-----"""
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聽位址，0.0.0.0 表示所有介面 |
| port | integer | 8000 | 監聽埠號 |
| auto_start | boolean | true | 是否在 `sdk.init()` 時自動啟動路由伺服器。設為 `false` 可跳過路由伺服器啟動（純事件/無 WebUI 場景） |
| ssl_certfile | string | 空 | SSL 證書檔案路徑 |
| ssl_keyfile | string | 空 | SSL 私鑰檔案路徑 |
| ssl_cert | string | 空 | **內聯 PEM 證書內容**（非路徑）。與 `ssl_key` 成對使用時優先於 `ssl_certfile`/`ssl_keyfile`；框架臨時落盤建構 SSL 上下文後立即刪除臨時檔案 |
| ssl_key | string | 空 | **內聯 PEM 私鑰內容**（非路徑），語義同上 |

> **埠口占用不是致命錯誤**：啟動時若檢測到 `port` 已被占用，框架會跳過路由伺服器啟動並告警，**適配器與模組照常運行**（僅 HTTP/WS/SSE 路由與 WebUI 不可用）。排查「機器人能跑但 WebUI 打不開」時先確認埠口。

## 主人系統配置

主人系統用於識別「框架主人」帳號（如 Bot 管理員）。`master.users` 支援兩種寫法：

```toml
[ErisPulse.master]
# 寫法一：全局主人（所有平台生效）
users = ["123456", "789012"]

# 寫法二：按平台指定主人（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| users | array / object | 空 | 主人帳號列表。`list` 形式為全局主人（所有平台生效）；`dict` 形式按平台指定（鍵為平台名，值為該平台的主人帳號列表） |

程式碼中透過 `master.is_master(event)` 或 `master.is_master(platform, user_id)` 檢查，每次呼叫實時讀取配置（支援熱更新，無需重啟）：

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("主人你好")
```

### 判定鏈與運行時增刪

主人判定鏈為 **配置主人 → 運行時記錄 → provider 鏈**：

```python
from ErisPulse.Core import master

master.is_master(event)                      # 從事件判定
master.is_master("yunhu", "123")             # 顯式判定
master.add("yunhu", "123")                   # 運行時新增（預設持久化；persist=False 僅記憶體）
master.remove("yunhu", "123")                # 移除（預設持久化）
master.list()                                # 匯總：{"global": [...], "<platform>": [...]}
```

### 自訂身份源（provider）

除配置外，還可註冊自訂身份源：`fn(platform, user_id) -> bool`，
內建身份源（配置 + 運行時記錄）未命中時依次嘗試，任一 provider 放行即認定為主人。
適合對接適配器管理員介面、資料庫角色等外部身份體系。

註冊入口 `master.provider` 支援裝飾器 / 函數式兩種寫法，
註銷統一走被註冊函數上的 `fn.unregister()`：

```python
from ErisPulse.Core import master

# 寫法一：裝飾器（常駐身份源，推薦）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自訂判定邏輯

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 不再需要時註銷

# 寫法二：函數式（模組載入期註冊 / 卸載期註銷）
fn = master.provider(admin_provider)
fn.unregister()
```

> provider 異常會被捕獲並跳過，不阻斷身份判定鏈。
> 綁定實例方法無法掛載 `unregister`，需要註冊/註銷配對的場景請用**模組級函數**。

### 用戶優先：主人生效範圍由用戶最終決定

命令的 `master=True` 只是**開發者預設**：用戶可在
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false`
覆寫緊縮或放開（見[統一事件覆寫配置](#統一事件覆寫配置eventoverrides)，用戶顯式配置即生效）。

## 日誌設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # 顯式日誌檔案清單（與 log_dir 互斥，優先級更高）
log_dir = ""                  # 日誌目錄（設定後自動分段輪替）
log_rotation = "size"         # 分段方式: "size" / "date" / "none"
log_max_size_mb = 10          # size 模式單檔案上限（MB）
log_backup_count = 5          # 保留的歷史日誌檔案數
log_rotation_when = "midnight"  # date 模式輪替週期: S/M/H/D/midnight
memory_limit = 1000             # 單模組記憶體日誌筆數上限（0 = 關閉記憶體日誌副本）
total_memory_limit = 5000       # 全部模組記憶體日誌總筆數上限（0 = 不限）
exclude_levels = ["EVENT"]
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| level | string | INFO | 日誌級別：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE 為最低級別，輸出框架內部詳細除錯資訊） |
| format | string | rich | 日誌輸出格式：`rich`（彩色，預設）、`plain`（純文字無顏色，適合日誌收集/管線重新導向）、`json`（JSON 結構化，適合 ELK 等） |
| log_files | array | 空 | 日誌輸出檔案清單（顯式路徑，不分段） |
| log_dir | string | 空 | 日誌輸出目錄（自動建立）。設定後寫入目錄內 `erispulse.log` 並按 `log_rotation` 自動分段；與 `log_files` 互斥，`log_files` 優先 |
| log_rotation | string | size | 分段方式：`size`（按大小）/ `date`（按時間）/ `none`（不分段） |
| log_max_size_mb | float | 10 | size 模式單檔案大小上限（MB），超過後輪替為 `.1`/`.2` 備份 |
| log_backup_count | integer | 5 | 保留的歷史日誌檔案數，超出的最舊備份自動刪除 |
| log_rotation_when | string | midnight | date 模式輪替週期：`S`/`M`/`H`/`D`/`midnight`（預設每天零點） |
| memory_limit | integer | 1000 | 單模組記憶體中保存的日誌筆數；`0` 表示關閉記憶體日誌副本（不再寫入記憶體，已有記錄保留） |
| total_memory_limit | integer | 5000 | 全部模組記憶體日誌總筆數上限；`0` 表示不限。超限時按輪替策略淘汰最舊記錄（優先削減筆數最多的模組佇列），與單模組 `memory_limit` 獨立生效 |
| exclude_levels | array | 空 | 屏蔽指定日誌等級。被屏蔽等級的日誌**完全丟棄**（不寫記憶體、不推送給 Dashboard 等訂閱器、不列印、不寫檔案）。支援熱更新 |

也可在程式碼中動態切換：

```python
from ErisPulse.Core import logger

# 按大小分段：單檔案 10MB，保留 5 份
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 按時間分段：每天零點輪替，保留 7 份
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` 及分段相關設定需要 ErisPulse **2.8.0+**。

> **隱私保護**：訊息收發內容以 **EVENT 等級**（數值 21）記錄。設定 `exclude_levels = ["EVENT"]` 即可讓後台（如 Dashboard 日誌面板）無法看到各群/私聊的訊息內容，同時不影響其它等級日誌。

> [!NOTE]
> `exclude_levels` 本特性需要 ErisPulse **2.8.0+**。

## 框架設定

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | 是否啟用模組懶載入 |
| uninit_timeout | integer | 30 | 優雅關閉的總逾時時間（秒），超過後強制終止。0 表示不設逾時 |
| strict_mode | integer | 0 | 嚴格模式層級，見下方「嚴格模式」說明 |
| handler_max_concurrency | integer | 64 | 事件處理器最大並發 Task 數，設大可提高吞吐但增加記憶體佔用 |
| handler_queue_max_pending | integer | 4096 | 事件洪峰入列背壓：單平台待處理 handler Task 數上限，超限時新事件的處理器 Task 直接捨棄並記錄 WARNING（捨棄計數可在 troubleshoot 排查中查看）；`0` 表示不限制 |
| offline_bot_expiry | integer | 3600 | 離線 Bot 記錄自動過期時間（秒），0 表示不過期 |
| plugins_dir | string / list | "plugins" | 本機插件資料夾（相對專案根目錄）；新增/刪除/修改插件檔案會被熱重載 watcher 自動發現 |
| watch_ignore_dirs | list | 內建清單 | 熱重載檔案監控忽略的目錄名稱（`.venv`/`.git`/`__pycache__` 等）；非空列表**整體取代**內建清單，`[]` 表示不忽略任何目錄 |
| watch_include_plugin_dirs | boolean | true | `epsdk run --reload` 是否將插件目錄交給插件熱重載 watcher 精確處理（單模組重載），並從全量監控中排除 |

### 主動 GC 設定

SDK 初始化完成後啟動主動 GC 背景任務，週期性執行 Python GC 與內部資源回收（離線 Bot 清理等）。全部參數均支援熱更新，變更時即時重啟任務。

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回收間隔（秒），支援小數。0 表示停用主動 GC |
| proactive_gc_generation | integer | 0 | 常規輪次回收分代（0/1/2，鉗制到 0..2）。注意 `gc.collect(2)` 等同於全量回收，預設 0 保持輕量；深度回收由 `proactive_gc_full_every` 週期性觸發 |
| proactive_gc_full_every | integer | 20 | 每 N 輪做一次全量回收，0 表示停用週期性全量。全量回收受 `proactive_gc_memory_growth_mb` 門檻約束 |
| proactive_gc_memory_growth_mb | integer | 32 | 全量回收的記憶體成長門檻（MB）：對比上次全量後的記憶體基準線（優先 tracemalloc，其次 RSS），僅當成長達到此值才執行全量回收。0 表示不設門檻 |
| proactive_gc_idle_only | boolean | false | 開啟後，事件洪峰（存在未完成的 pending handler）時本輪跳過 Python GC，避免停頓與訊息處理競爭；內部資源回收不受影響 |
| proactive_gc_gen0_min | integer | 500 | 常規輪次觸發回收的 gen0 垃圾量下限：`gc.get_count()[0]` 低於此值直接跳過（空轉輪次近乎零開銷）。0 表示始終回收 |

> **2.7.1 變更**：預設 `proactive_gc_generation` 由 `2` 調整為 `0`，預設 `proactive_gc_full_every` 由 `0` 調整為 `20`。此前 `generation=2` 意味著每輪都做最重的全量回收；新預設在保持回收覆蓋的同時顯著降低空轉開銷。明確設定的舊值仍按字面語意生效。

### 嚴格模式

嚴格模式控制模組/轉接器在載入階段不合規或失敗時的處理策略。現代模組/轉接器都應繼承對應的基底類別（`BaseModule`/`BaseAdapter`），未繼承基底類別的元件會影響框架的上下文系統與兜底清理，可能導致資源洩漏。

> **2.5.2 變更**：預設層級從 `1`（跳過）調整為 `0`（寬鬆），以減少新使用者初次使用時遇到的載入問題。未繼承基底類別的元件將以 WARNING 提示並嘗試載入，而非直接拒絕。如需恢復舊行為，請明確設定 `strict_mode = 1`。

| 層級 | 名稱 | 行為 |
|------|------|------|
| 0 | 寬鬆（預設） | 違規僅警告，未繼承基底類別的元件仍會嘗試載入（相容舊元件） |
| 1 | 嚴格-跳過 | 拒絕未繼承基底類別的元件並跳過，其餘正常啟動 |
| 2 | 嚴格-致命 | 收集所有違規後統一報告並中止整個啟動 |

各層級下，「載入/註冊/初始化階段報錯」這類元件自身崩潰始終會被跳過；區別在於：

- **0 → 1**：唯一行為變化是「未繼承基底類別」從「仍載入」變為「跳過」。
- **1 → 2**：所有違規（未繼承基底類別、載入失敗、註冊失敗、初始化失敗等）升級為致命，會在啟動檢查點收集後一次性輸出違規清單並中止。

#### 豁免清單

如果某些元件確實暫時無法遷移（例如依賴的舊模組），可以將其加入豁免清單，被列名的元件即使不合規也會按寬鬆模式對待，繼續載入：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> 當某個元件被嚴格模式拒絕時，日誌會明確提示如何恢復載入（加入豁免清單或調低層級）。

#### 與 CLI 的聯動

`epsdk run` 的啟動前自檢（設定檔可解析性、元件必填設定完整性）預設跟隨本設定：非 0 時檢查失敗即拒絕啟動，0 時僅警告繼續。也可以不改設定臨時切換：`epsdk run --strict` 本次將自檢與嚴格層級同時開啟（層級只升不降，經 `ERISPULSE_FRAMEWORK_STRICT_MODE` 環境變數傳導到執行程序），`--no-strict` 本次臨時壓到寬鬆並僅警告。

## 存儲配置

2.8.0 起存儲引擎支援三種異步後端，**API 完全一致、配置一鍵切換**：

| 後端 | 驅動 | 安裝 | 特點 |
|------|------|------|------|
| SQLite（預設） | aiosqlite | 開箱即用 | 零配置、單檔案、WAL 併發 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 已有 MySQL 基礎設施、多實例共享 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | 事務能力強、高併發 |

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite"（預設）/ "mysql" / "postgres"
use_global_db = false     # 僅 SQLite：使用包內全局資料庫 data/config.db

[ErisPulse.storage.mysql]      # backend = "mysql" 時生效
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
# charset = "utf8mb4"
# pool_min = 1
# pool_max = 10

[ErisPulse.storage.postgres]   # backend = "postgres" 時生效
host = "127.0.0.1"
port = 5432
user = "erispulse"
password = ""
database = "erispulse"
# pool_min = 1
# pool_max = 10
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| backend | string | sqlite | 存儲後端：`sqlite` / `mysql` / `postgres`，切換零程式碼改動 |
| use_global_db | boolean | false | 僅 SQLite：是否使用包內全局資料庫而非專案獨立資料庫 |
| storage.mysql.* | table | 見上 | MySQL 連線參數（host / port / user / password / database / charset / pool） |
| storage.postgres.* | table | 見上 | PostgreSQL 連線參數（host / port / user / password / database / pool） |

也支援環境變數覆蓋（Docker / 12-factor）：`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`。

> [!TIP]
> - 連線參數變更後需重啟框架生效；連線池建立瞬時失敗會自動指數退避重試
> - 切換後端前可用驗證腳本自檢：`python tests/devs/test_storage_backend_verify.py --backend mysql`
> - 事務 / 方言差異 / 自訂後端等完整說明見[存儲後端](../advanced/storage-backends.md)

## 事件配置

### 命令配置

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
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

## 會話收件匣配置（transcript）

```toml
[ErisPulse.transcript]
enabled = true
max_per_session = 50
ttl_hours = 168.0
self_echo = "bot"
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| enabled | boolean | true | 是否自動記錄入站/出站訊息（關閉後停止寫入，歷史仍可查詢） |
| max_per_session | int | 50 | 單會話保留條數（0 = 關閉該會話裁剪） |
| ttl_hours | float | 168.0 | 全域保留時長（小時，0 = 永不清理） |
| self_echo | string | bot | 入站 bot 回聲（`self.user_id == user_id`，如 OneBot `report-self-message`）處理：`bot` = 記為 bot 並標記 `meta.self_echo`；`skip` = 不記錄；`user` = 記為 user（舊行為） |

> 保留策略的風險與稽核見 [會話收件匣](../advanced/transcript.md)；歸因欄位（`sender` / `meta`）與出站歸屬（`meta.module`）同見該文檔。

## 國際化配置

```toml
[ErisPulse.i18n]
language = "auto"
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| language | string | auto | 框架內建文字的顯示語言。設為 `auto` 自動檢測系統語言，也可設為具體代碼：`zh-CN`、`zh-TW`、`en`、`ja`、`ru` |

## 模組配置

每個模組可以在配置檔案中定義自己的配置：

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

# 立即保存到檔案
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` 預設採用延遲寫入（約每 5 秒批量保存到檔案），設定 `immediate=True` 可立即持久化。配置變更會觸發 `config.set` 生命週期事件。

## 作用域配置（scope）

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

作用域宣告「**什麼範圍內生效**」——某平台 / Bot / 會話裡哪些模組可用（① 模組維度）、
某用戶 / 群 / Bot / 適配器的事件收不收（② 身份維度）、
模組能發起哪些出站呼叫（③ 出站維度）：

```toml
[ErisPulse.scope]
default_allow = true        # 全局兜底（false = 隱式拒絕嚴格模式；不受影響出站維度）
cache_size = 1024           # LRU 快取大小

# ① 模組維度（優先級：會話 > Bot > 平台；條目支援精確 / glob / re: 正則）
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# 子級綁定寫 merge = true 時與低優先級逐條目並集（預設整體覆蓋）
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② 身份維度（優先級：用戶 > 會話 > Bot > 適配器；每級只寫 allow 或 deny 之一）
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # 該平台所有事件在入口丟棄
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # 用戶鍵支援 glob / re: 正則
deny = ["u_bad", "spam_*"]

# ③ 出站維度（預設全允許；規則為內聯表，條目支援精確 / glob / re: 正則）
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # 全禁發送
api = { allow = ["get_*"] }               # 僅允許查詢類標準 API
request = { deny = true }                 # 禁止處理請求
```

| 配置項 | 類型 | 說明 |
|---------|------|------|
| `scope.default_allow` | boolean | 全局兜底：模組/身份未命中規則的放行/拒絕（`true`） |
| `scope.cache_size` | integer | LRU 快取大小（預設 1024） |
| `scope.platforms / bots / sessions` | table | ① 模組三級綁定：`{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② 身份四級綁定：`{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<動作>` | table | ③ 出站規則：`{allow=[...], deny=true|[...]}`（動作取 send / api / request） |

> 詳解與運行時 API（維度化 `sdk.scope.set_module()` / `set_identity()` /
> `set_action()`，判定 `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`，
> 以及字典式兜底 `get()` / `set()` / `delete()`）詳見[作用域（scope）](../advanced/scope.md)。

## 統一事件覆寫配置（event.overrides）

統一覆寫系統：按**事件類型**覆寫任意模組處理器的行為，不改模組程式碼。
OneBot12 標準類型（meta / message / notice / request）與擴展類型（command）
各自擁有專屬的可覆寫參數：

```toml
[ErisPulse.event.overrides]

# message：文本觸發條件（與程式碼內條件 AND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "閒聊*"

# notice / request / meta：detail_type 白名單（條目支援精確 / glob / re: 正則）
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command（擴展類型）：實現參數覆寫（用戶優先；禁用統一走 acl deny）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # 覆寫為僅框架主人（false 則放開開發者的主人限制）
hidden = true               # 幫助列表中隱藏
aliases = ["rs"]            # 生效別名

# acl（command 專屬）：命令用戶黑白名單（命令名支援 glob / re: 正則，精確鍵優先）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # 用戶標識 "platform:user_id"
deny = ["onebot11:u_bad"]

# ACL 兜底：未配置 ACL 的命令放行（`true`）/ 嚴格拒絕（`false`）
acl_default_allow = true
```

| 配置項 | 類型 | 說明 |
|---------|------|------|
| `event.overrides.message.<module>` | table | 文本條件：`{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | 模組級參數覆寫（`hidden = true` 等標量） |
| `event.overrides.command.<module>.<command>` | table | 命令級覆寫（命令級優先） |
| `event.overrides.acl.<命令名>` | table | 用戶黑白名單：`{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACL 兜底：未配置 ACL 的命令放行（`true`）/ 嚴格拒絕（`false`） |

> 運行時 API（`from ErisPulse.Core.Event import overrides` 後按類型子命名空間調用
> `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` 等，
> 或經 `sdk.Event.overrides` 訪問）
> 見 [事件處理入門 · 事件覆寫](../getting-started/event-handling.md#事件覆寫不改模組程式碼覆寫任意事件類型的行為)。

## CLI 参考

> 来源: `docs/zh-TW/user-guide/cli-reference.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/user-guide/cli-reference.md）

# CLI 指令參考

> [!TIP]
> **什麼時候需要讀這篇**：忘記某個 `epsdk` 指令的參數、想把元件管理寫進腳本，或要控制 run / stop / restart 行為時查閱。日常只用 `init` / `install` / `run` 的話，記住一條就夠：`epsdk <指令> --help` 隨時可查參數說明，不需要通讀本文。

`epsdk` 是 ErisPulse 的命令列工具：初始化專案、安裝 / 升級模組與適配器、互動式設定元件、執行與停止機器人、診斷環境，都在這一條指令下。

> **提示**：`epsdk`（不帶指令）的主說明按類別分組顯示：**專案**（init / create / run）、**元件管理**（install / uninstall / upgrade / list / list-remote / types）、**設定與診斷**（config / doctor / i18n）、**其他**（self-update / version）。

---

## 套件管理命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `install` | `i`, `add` | `[套件]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | 安裝模組/適配器 |
| `uninstall` | `rm`, `remove` | `<套件>... [--no-uv]` | 卸載模組/適配器 |
| `upgrade` | `up` | `[套件]... [--force/-f] [--pre] [--no-uv]` | 升級指定模組或全部 |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | 更新 SDK 本身 |

## 臨床命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose] [--fix]` | 臨床環境並輸出健康報告；`--fix` 嘗試自動修復 |

### install

安裝 ErisPulse 模組或適配器包。若不指定包名則進入互動式安裝介面。

**別名：** `i`, `add`

> **uv 項目聯動**（2.11.1+）：在 uv 管理的項目內（存在 `uv.lock` 或 `[tool.uv]`），
> `install` / `upgrade` / `uninstall` 自動改走 `uv add` / `uv remove`——依賴同步寫入
> `pyproject.toml` 與 `uv.lock`，`uv sync` 不再清掉 epsdk 裝的組件；失敗自動回退
> uv pip / pip 通道。`--user` 等 uv 不支援的參數直接走 pip。目標環境解析順序：
> `ERISPULSE_PYTHON` → `UV_PROJECT_ENVIRONMENT` → 項目 `.venv` → `UV_PYTHON` →
> `VIRTUAL_ENV` → 當前解釋器（`epsdk doctor` 可查看完整決策鏈）。

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[package]...` | | 要安裝的包名稱，可指定多個 |
| `--upgrade` | `-U` | 安裝時升級到最新版本 |
| `--pre` | | 允許安裝預發佈版本 |
| `--editable` | `-e` | 以可編輯模式安裝（需指定路徑） |
| `--user` | | 安裝到用戶 site-packages 目錄 |
| `--no-deps` | | 不安裝依賴 |
| `--target` | `-t` | 安裝到指定目錄 |
| `--index-url` | | 指定 PyPI 鏡像源地址 |
| `--extra-index-url` | | 頂外 PyPI 鏡像源地址（可多次指定） |
| `--no-cache-dir` | | 禁用快取 |
| `--requirement` | `-r` | 從 requirements 檔案安裝 |
| `--constraint` | `-c` | 從約束檔案安裝 |
| `--force-reinstall` | | 強制重新安裝 |
| `--ignore-installed` | | 忽略已安裝的包 |
| `--compile` | | 安裝後編譯 .pyc 檔案 |
| `--no-compile` | | 安裝後不編譯 .pyc 檔案 |
| `--prefix` | | 安裝到指定前綴目錄 |
| `--src` | | 可編輯安裝時使用的原始碼目錄 |
| `--config-settings` | | 傳遞給建構後端的配置（可多次指定） |
| `--no-binary` | | 限制不使用二進位包（格式如 `:all:`） |
| `--only-binary` | | 限制僅使用二進位包（格式如 `:all:`） |
| `--prefer-binary` | | 優先選擇二進位包 |
| `--build-isolation` | | 啟用建構隔離 |
| `--no-build-isolation` | | 禁用建構隔離 |
| `--upgrade-strategy` | | 升級策略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | 允許修改系統包管理器管理的 Python 包 |
| `--no-uv` | | 使用 pip 代替 uv |

**示例：**

```bash
# 安裝單個模組
epsdk install Weather

# 安裝多個模組
epsdk install Yunhu Weather

# 從鏡像源安裝並升級
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 可編輯模式安裝（開發模式）
epsdk install -e ./my-adapter
```

### uninstall

卸載已安裝的 ErisPulse 模組或適配器包。若不指定包名則進入互動式卸載介面。

**別名：** `rm`, `remove`

**參數：**

| 參數 | 說明 |
|------|------|
| `<package>...` | 要卸載的包名稱，可指定多個 |
| `--no-uv` | 使用 pip 代替 uv |

**示例：**

```bash
# 卸載單個模組
epsdk uninstall Weather

# 卸載多個模組
epsdk uninstall Yunhu Weather
```

### upgrade

升級已安裝的 ErisPulse 組件。不指定包名則互動式升級全部。

**別名：** `up`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[package]...` | | 要升級的包名稱，可指定多個 |
| `--force` | `-f` | 強制升級，跳過確認 |
| `--pre` | | 允許升級到預發佈版本 |
| `--no-uv` | | 使用 pip 代替 uv |

**示例：**

```bash
# 升級所有包
epsdk upgrade

# 升級指定包
epsdk upgrade Weather

# 強制升級（跳過確認）
epsdk upgrade -f
```

### self-update

更新 ErisPulse SDK 本身到最新版本。

**別名：** `su`, `update`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[version]` | | 指定要更新的目標版本號 |
| `--pre` | | 允許更新到預發佈版本 |
| `--force` | `-f` | 強制更新，跳過確認 |
| `--no-uv` | | 使用 pip 代替 uv |

**示例：**

```bash
# 更新到最新穩定版
epsdk self-update

# 更新到指定版本
epsdk self-update 1.2.3

# 允許預發佈版本
epsdk self-update --pre

# 強制更新
epsdk self-update -f
```

> [!NOTE]
> 透過 `uv tool install ErisPulse` 安裝時，本命令自動改走 `uv tool upgrade ErisPulse`（指定版本時為 `uv tool install ErisPulse==<版本> --force`），直接 pip 升級工具環境會被 uv 的清單還原抹掉。
> Windows 下更新在新控制台視窗中進行：當前 CLI 需先退出以解除工具環境檔案占用，視窗提示完成後重新打開終端即可。

---
[docs/zh-TW/quick-start.md](docs/zh-TW/quick-start.md)

## 資訊查詢命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | 列出已安裝的組件 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | 列出遠端可用的組件 |
| `version` | `ver` | | 顯示 SDK 與 Python 版本資訊（與 `-V` 等效） |

### list

列出已安裝的 ErisPulse 模組和適配器。

**別名：** `l`, `ls`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--type` | `-t` | 指定類型：`modules`、`adapters`、`all`（預設） |
| `--outdated` | `-o` | 僅顯示可升級的套件 |

**範例：**

```bash
# 列出所有已安裝的組件
epsdk list

# 只列出模組
epsdk list -t modules

# 只列出適配器
epsdk list -t adapters

# 只顯示可升級的套件
epsdk list -o
```

### list-remote

列出遠端倉庫中可用的 ErisPulse 模組和適配器。

**別名：** `lsr`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--type` | `-t` | 指定類型：`modules`、`adapters`、`all`（預設） |
| `--refresh` | `-r` | 強制刷新遠端套件列表快取 |

**範例：**

```bash
# 列出所有遠端可用組件
epsdk list-remote

# 只列出遠端模組
epsdk list-remote -t modules

# 強制刷新快取後列出
epsdk list-remote -r
```

---

## 配置命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l] [--json]` | 互動式配置適配器/模組的宣告式配置項目 |

### config

互動式填寫適配器/模組的宣告式配置項目。向導由適配器/模組宣告的配置類（`ConfigClass` / `AccountConfigClass`）驅動，自動生成表單並驗證，無需手寫 config.toml。

適配器額外支援多帳戶（bot 帳戶）管理：新增/編輯/刪除帳戶，以及啟用/禁用開關。

**別名：** `cfg`, `conf`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[name]` | | 目標名稱（適配器平台名或模組名），留空進入互動選擇 |
| `--list` | `-l` | 僅列出所有目標的配置狀態，不進入向導 |
| `--json` | | 以 JSON 輸出全部目標及其配置狀態（供 CI / 腳本消費），不進入向導 |

**範例：**

```bash
# 查看所有適配器/模組的配置狀態
epsdk config --list

# 以 JSON 輸出配置狀態（CI / 腳本消費）
epsdk config --json

# 互動選擇目標進行配置
epsdk config

# 直接配置指定適配器
epsdk config yunhu

# 直接配置指定模組
epsdk config MyModule
```

**說明：**

- 配置狀態分為四檔：`已就緒`（驗證通過）、`待完善`（必填項缺失或驗證失敗）、`未配置`（從未生成）、`無配置`（目標未宣告配置類）
- 字段值帶來源標註：已有配置顯示 `（目前:值）`，未配置時顯示 schema 預設值 `（預設:值）`；直接按回車即保留該值
- 密鑰類字段（宣告 `secret`）輸入時不回顯，按回車保留已設定的值
- 互動選擇模式下，單個向導結束後會回到選擇選單（狀態已刷新），可連續配置多個目標，留空退出
- 全局表單驗證失敗且放棄重新填寫時，本次向導中止且不寫入任何配置（避免產生"已啟用但配置不完整"的半成品狀態）
- 保存後立即寫入 `config/config.toml`，Dashboard 與運行中的 SDK 均可見；運行中的適配器如需應用新帳戶配置，重啟進程即可
- `epsdk install`（互動式安裝）與 `epsdk init` 安裝適配器成功後，若檢測到配置宣告會自動引導進入本向導；命令列直接指定套件名安裝時僅列印配置提示

---

## 運行控制命令

> [!TIP]
> `epsdk run` 會自動檢測並使用項目目錄下的 `.venv` 虛擬環境運行機器人
> （也可透過 `ERISPULSE_PYTHON` 環境變數顯式指定解釋器）。`epsdk install` /
> `uninstall` / `upgrade` / `list` 同樣作用於項目虛擬環境。

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload] [--strict/--no-strict]` | 運行指定腳本或 SDK |
| `stop` | — | `[--force] [--pid PID]` | 停止正在運行的實例（由 `epsdk run` 啟動） |
| `restart` | — | `[--force] [--pid PID]` | 重啟正在運行的實例（停止後按原參數重新啟動） |

### run

運行 ErisPulse 項目腳本或直接啟動 SDK。支援熱重載模式。

**別名：** `r`

**參數：**

| 參數 | 說明 |
|------|------|
| `[script]` | 要運行的腳本文件，不指定則運行 SDK |
| `--reload` | 啟用熱重載模式：監控文件變化自動觸發組件級代碼熱重載（無需整進程重啟）；預設忽略 `.venv`/`.git` 等目錄（可經 `ErisPulse.framework.watch_ignore_dirs` 配置），插件目錄交給插件熱重載 watcher 精確處理 |
| `--strict` / `--no-strict` | 臨時開啟 / 關閉嚴格模式（僅本次生效，不寫入配置）；缺省跟隨 `ErisPulse.framework.strict_mode` |

**示例：**

```bash
# 直接運行 SDK
epsdk run

# 運行指定腳本文件
epsdk run main.py

# 熱重載模式運行（文件變更自動觸發代碼級熱重載）
epsdk run main.py --reload

# SDK 熱重載模式
epsdk run --reload

# 臨時嚴格模式：啟動前自檢失敗即退出，框架嚴格級別本次提升為至少 1
epsdk run main.py --strict

# 臨時寬鬆模式（配置裡開了 strict_mode 但本次想先跑起來）
epsdk run main.py --no-strict
```

**啟動前自檢：** `run` 啟動前會快速檢查 `config/config.toml` 可解析性與已安裝組件的必填配置完整性，嚴格性預設跟隨 `ErisPulse.framework.strict_mode`（非 0 時檢查失敗即退出，0 時僅警告繼續）。配置文件缺失視為正常首次啟動，僅提示不判失敗。`--strict` 臨時開啟：預檢失敗即退出，同時框架嚴格級別本次提升為至少 1（跳過不合規組件，經 `ERISPULSE_FRAMEWORK_STRICT_MODE` 環境變數傳導到運行進程，不寫入配置文件）；`--no-strict` 反之臨時壓到寬鬆。自檢自身異常時自動跳過，不含網路探測，不會阻塞啟動。

> **`--reload` 的監督結構**（2.11.1 起）：`epsdk run --reload` 以「監督進程 + 重載 worker 子進程」運行。保存 `.py` 文件觸發的熱重載全部在 worker 內完成（互斥串行、風暴合併）；模組側語法錯誤會被整體預檢拒絕，舊實例繼續服務。`sdk.hard_restart()` 時 worker 以退出碼 42 退出，監督進程展示原因後自動重拉全新 worker——升級框架本體後新代碼即刻生效。

### stop

停止正在運行的 ErisPulse 實例（由 `epsdk run` 啟動、並在同一項目目錄下執行）。
`run` 啟動時會把監督進程 PID、當前框架子進程 PID 與原始啟動命令寫入
`.erispulse/runtime.json`，`stop` 據此定位實例。

**停止順序：** POSIX 下先向監督進程發 SIGINT（與 Ctrl+C 同款優雅收尾路徑——
finally 鏈自動終止框架子進程），超時逐級升級 SIGTERM / SIGKILL；Windows 無
進程信號語義，先終止框架子進程再終止監督進程（避免監督者把強殺誤判為崩潰
重新拉起）。

**參數：**

| 參數 | 說明 |
|------|------|
| `--force` | 跳過優雅停止，直接強制終止 |
| `--pid PID` | 直接指定目標進程 PID（覆蓋運行狀態文件，用於非標啟動方式） |

**示例：**

```bash
# 停止當前項目的運行實例
epsdk stop

# 強制終止
epsdk stop --force
```

### restart

重啟正在運行的 ErisPulse 實例：按 `stop` 的語義停止後，以狀態文件中記錄的
**原始啟動命令**重新啟動（前檯接管當前終端，新實例會寫入新的運行狀態文件）。

**參數：** 同 `stop`（`--force` / `--pid PID`）。

**示例：**

```bash
# 優雅重啟（pip 升級適配器/模組後讓代碼生效；運行中模組也可用
# sdk.reload_module / sdk.adapter.reload 代碼級熱重載，無需重啟）
epsdk restart
```

> [!NOTE]
> `python main.py` 等繞過 `epsdk run` 的啟動方式不會寫運行狀態文件——此類
> 進程請用系統工具管理，或用 `epsdk stop --pid <PID>` 指定 PID。

## 專案管理命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--adapter/-a <name>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | 初始化 ErisPulse 專案 |
| `create` | — | `{module,adapter,pack} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f] [--local]` | 建立模組/適配器腳手架；`pack` 將本地插件轉換為可發布專案 |

### init

初始化一個新的 ErisPulse 專案。支援互動式與快速模式，2.8.4 起生成 `pyproject.toml`（相依性清單）、可選建立專案 `.venv` 虛擬環境並安裝框架與適配器，並支援**指定任意目錄**。

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[path]` | | 目標路徑（可包含父目錄，如 `../apps/mybot`；純名稱等價 `--project-name`） |
| `--project-name` | `-n` | 專案名稱 |
| `--path` | | 專案父目錄（與 `-n` 組合指定建立位置） |
| `--adapter` | `-a` | 預選要安裝的適配器（可重複傳參或逗號分隔），傳入時跳過適配器詢問與選擇 |
| `--quick` | `-q` | 快速模式，跳過互動式向導（預設建立 `.venv` 並安裝相依性） |
| `--force` | `-f` | 強制覆蓋現有配置檔案 |
| `--here` | | 在當前目錄初始化，不建立子目錄 |
| `--no-uv` | | 使用 pip 代替 uv |
| `--no-venv` | | 跳過虛擬環境建立與相依性安裝 |

**範例：**

```bash
# 互動式初始化
epsdk init

# 快速初始化（當前目錄下建立 my_bot/，含 pyproject.toml + .venv）
epsdk init -q -n my_bot

# 快速初始化並預裝適配器（免互動，腳本 / CI 場景）
epsdk init -q -n my_bot --adapter yunhu,telegram

# 指定任意目錄初始化（../apps/mybot）
epsdk init ../apps/mybot

# 組合父目錄與專案名
epsdk init -n my_bot --path ../apps

# 強制覆蓋已有配置
epsdk init -f

# 在當前目錄初始化
epsdk init --here -n my_bot

# 只生成專案結構，不建立虛擬環境
epsdk init --no-venv -n my_bot
```

init 產物：`main.py`、`pyproject.toml`（相依性清單）、`config/config.toml` + `config.full.example`、`config/ssl/`、`logs/`、`.gitignore`、`README.md`；選擇建立虛擬環境時額外生成 `.venv` 並將 `erispulse` 與所選適配器安裝其中。

> [!NOTE]
> `.gitignore` 為分組式範本：Python 字節碼與建構產物、虛擬環境與 `.env`、工具快取、編輯器與系統檔案，並**整體排除 `config/` 與 `logs/` 運行時目錄**——`config.toml` 含適配器權杖等敏感資訊，不建議庫入；共享配置骨架請使用 `config.full.example`。

> [!WARNING]
> **不要使用 `uv run epsdk run` 運行機器人**。`uv run` 在無 `pyproject.toml` 的目錄執行時建立**一次性的隔離環境**——在其中透過 `epsdk install` 安裝的適配器不會持久化。請在專案目錄內使用 `epsdk run`（自動使用專案 `.venv`），或先激活虛擬環境再運行。

### create

建立 ErisPulse 模組或適配器的腳手架專案；`pack` 子命令將本地插件（`plugins/` 目錄）轉換為可發布的標準專案。

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `{module,adapter,pack}` | | 要建立的類型：`module` / `adapter` / `pack`（插件轉專案）|
| `--name` | `-n` | 專案名稱（PascalCase） |
| `--description` | `-d` | 專案描述 |
| `--author` | `-a` | 作者名稱 |
| `--email` | `-e` | 作者電子信箱 |
| `--homepage` | | 專案首頁 URL |
| `--output` | `-o` | 輸出目錄（預設當前目錄） |
| `--force` | `-f` | 強制覆蓋已存在的目錄 |
| `--local` | | 建立本地插件（`module` / `adapter` 可用）：生成 `plugins/<name>/` 包結構，免打包安裝 |

**範例：**

```bash
# 互動式建立（引導選擇類型和填寫資訊）
epsdk create

# 直接建立 Module 專案
epsdk create module -n MyModule

# 建立本地插件（放入專案 plugins/ 目錄，啟動時自動發現）
epsdk create module -n MyModule --local

# 建立本地適配器插件（同上，免打包開發）
epsdk create adapter -n MyAdapter --local

# 直接建立 Adapter 專案
epsdk create adapter -n MyAdapter

# 將本地插件轉換為可發布專案（互動選擇插件 → 補全元資訊 → 生成標準專案）
epsdk create pack

# 完整參數
epsdk create module -n MyModule -d "模組描述" -a "作者" -e "mail@example.com"

# 指定輸出目錄
epsdk create module -n MyModule -o ./projects

# 強制覆蓋已有目錄
epsdk create module -n MyModule -f
```

---

## 語言命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | 查看或切換 CLI 顯示語言 |

### i18n

查看目前 CLI 語言、列出支援的語言、切換顯示語言。若不指定參數則進入互動式選擇介面。

**別名：** `language`, `lang`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[lang]` | | 要切換的語言代碼（如 `zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | 列出所有支援的語言 |

**範例：**

```bash
# 互動式選擇語言
epsdk i18n

# 切換到英文
epsdk i18n en

# 切換到日文
epsdk i18n ja

# 列出所有支援的語言
epsdk i18n --list
```

---

## 類型存根命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | 生成類型存根檔案以啟用 IDE 補全 |

### types

掃描已安裝的 ErisPulse 模組和適配器，為它們生成 `.pyi` 類型存根檔案，從而在 IDE 中獲得準確的程式碼補全與類型檢查支援。

**別名：** `t`, `stub`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--output` | `-o` | 輸出路徑（預設當前目錄下的 `ep-stubs/`） |
| `--force` | | 強制覆蓋已存在的存根檔案 |
| `--adapters-only` | | 僅生成適配器的類型存根 |
| `--modules-only` | | 僅生成模組的類型存根 |

> **注意：** `--adapters-only` 與 `--modules-only` 互斥，同時指定時後者生效。

**範例：**

```bash
# 為所有已安裝的模組和適配器生成類型存根
epsdk types

# 僅生成適配器存根
epsdk types --adapters-only

# 輸出到指定目錄
epsdk types -o ./typings

# 強制覆蓋已有檔案
epsdk types --force
```

---

## 全域參數

以下參數適用於所有命令：

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--help` | `-h` | 顯示幫助資訊 |
| `--version` | `-V` | 顯示版本資訊 |
| `--verbose` | `-v` | 顯示詳細輸出（可疊加 `-vv`/`-vvv`） |
| `--no-color` | | 禁用彩色輸出（適合 CI / 日誌收集） |
| `--no-banner` | | 跳過啟動 Banner（腳本化呼叫 / CI 場景；非互動終端與 `ERISPULSE_NO_BANNER=1` 下自動靜默） |
| `--yes` | `-y` | 自動確認所有互動提示（非互動式運行） |

---

## 環境診斷

### doctor

> [!NOTE]  
> 此命令需要 ErisPulse **2.7.0+**。

診斷當前 CLI 運行環境，輸出健康報告。用於排查「為什麼裝不上 / 連不上」類問題。

| 參數 | 說明 |
|------|------|
| `--verbose` | 顯示詳細診斷資訊 |
| `--fix` | 診斷後嘗試自動修復可修復的問題 |

**檢查項目**：
- **Python**：解釋器版本與路徑
- **安裝後端**：使用 `uv` 還是 `pip`
- **目標解釋器**：套件實際安裝到的目標 Python 環境
- **配置檔案**：`config/config.toml` 是否存在
- **組件配置**：已安裝組件的宣告式配置完整性（「裝好了跑不起來」多因必填項缺失）
- **配置污染**（2.11.1+）：掃描歷史升級遺留的殘留鍵（舊版執行時綁定的影子狀態鍵、游離配置節），檢出即提示
- **PyPI 連通性**：能否存取 PyPI（並顯示發現的組件數）
- **系統代理**：是否檢測到代理

**自動修復（`--fix`）**：
- `config.toml` 缺失 → 按當前語言生成初始配置檔案（與 `init` 建項同源）
- 組件配置「待完善」→ 逐個拉起互動式配置向導補全必填項（非互動環境提示改用 `epsdk config <名稱>`）
- 配置污染殘留鍵 → 列明來源並經確認後刪除（tomlclass 無損路徑，註解與順序保真）
- Python 版本過低、PyPI 無法存取等需人工介入的問題 → 僅輸出行動建議

```bash
# 運行環境診斷
epsdk doctor

# 使用別名
epsdk diag

# 診斷並嘗試自動修復
epsdk doctor --fix
```

---

## 互動式安裝

執行 `epsdk install` 不指定套件名時進入互動式安裝：

```bash
epsdk install
```

互動介面提供：
1. 適配器選擇
2. 模組選擇
3. 自訂安裝

## 常見用法

### 安裝模組

```bash
# 安裝單個模組
epsdk install Weather

# 安裝多個模組
epsdk install Yunhu Weather

# 升級模組
epsdk install Weather -U
```

### 列出組件

```bash
# 列出所有組件
epsdk list

# 只列出適配器
epsdk list -t adapters

# 只列出可升級的組件
epsdk list -o

# 查看遠端可用組件
epsdk list-remote
```

### 卸載組件

```bash
# 卸載單個組件
epsdk uninstall Weather

# 卸載多個組件
epsdk uninstall Yunhu Weather
```

### 配置組件

```bash
# 查看配置狀態
epsdk config --list

# 互動選擇目標配置
epsdk config

# 配置指定適配器
epsdk config yunhu
```

### 升級組件

```bash
# 升級所有組件
epsdk upgrade

# 升級指定組件
epsdk upgrade Weather

# 強制升級
epsdk upgrade -f
```

### 運行專案

```bash
# 普通運行
epsdk run main.py

# 熱重載模式
epsdk run main.py --reload
```

### 切換語言

```bash
# 互動式選擇語言
epsdk i18n

# 直接切換到英文
epsdk i18n en

# 列出支援的語言
epsdk i18n --list
```

### 生成類型存根

```bash
# 生成所有類型存根
epsdk types

# 僅生成模組類型存根
epsdk types --modules-only
```

### 初始化專案

```bash
# 互動式初始化
epsdk init

# 快速初始化
epsdk init -q -n my_bot
```

### 建立腳手架

```bash
# 互動式建立（引導選擇類型和填寫資訊）
epsdk create

# 直接建立 Module 專案
epsdk create module -n MyModule

# 直接建立 Adapter 專案
epsdk create adapter -n MyAdapter

# 完整參數
epsdk create module -n MyModule -d "模組描述" -a "作者" -e "mail@example.com"

# 強制覆蓋已有目錄
epsdk create module -n MyModule -f
```

## 安装

> 来源: `docs/zh-TW/user-guide/installation.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/user-guide/installation.md）

# 安裝參考

> [!TIP]
> **何時需要閱讀本文**：需要選擇一種安裝方式（pip / uv / Docker / ErisPulse-App 客戶端），或遇到安裝失敗需要排查時閱讀。只想快速運行，[5 分鐘快速入門](../quick-start.md) 已涵蓋最簡流程，不需要則跳過。

## 系統要求

- Python 3.10 – 3.14（3.14t 自由線程 / 無 GIL 構建為實驗性支持，框架以實驗性 CI 冒煙持續監測，不作正式承諾）
- pip 或 uv（推薦）
- 足夠的磁盤空間（至少 100MB）

## 安裝方式

### 方式一：使用 pip 安裝

```bash
# 安裝 ErisPulse
pip install ErisPulse

# 升級到最新版本
pip install ErisPulse --upgrade
```

### 方式二：使用 uv 安裝（推薦）

uv 是一個更快的 Python 工具鏈，推薦用於開發環境。

#### 安裝 uv

```bash
# 使用 pip 安裝 uv
pip install uv

# 驗證安裝
uv --version
```

#### 建立虛擬環境

```bash
# 建立項目目錄
mkdir my_bot && cd my_bot

# 安裝 Python 3.12
uv python install 3.12

# 建立虛擬環境
uv venv
```

#### 激活虛擬環境

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 安裝 ErisPulse

```bash
# 安裝 ErisPulse
uv pip install ErisPulse --upgrade
```

### 方式三：使用 uv tool 安裝（全域 CLI，推薦）

只想把 `epsdk` 當全域命令列工具使用時，`uv tool install` 是最乾淨的方式——
epsdk 運行在獨立的工具環境中，不污染任何專案環境：

```bash
# 安裝（epsdk 立即可用，無需激活任何虛擬環境）
uv tool install ErisPulse

# 升級（或直接使用 epsdk self-update，會自動走此通道）
uv tool upgrade ErisPulse
```

> [!NOTE]
> 工具環境裡的 epsdk 在專案目錄內運行時會自動感知專案 `.venv`：
> `epsdk install` 將組件安裝進專案環境、`epsdk run` 使用專案環境運行機器人，
> 框架本體仍由工具環境提供，兩邊互不干擾。
>
> 一鍵安裝腳本（`get.erisdev.com/install.sh` / `install.ps1`）的選單中
> 同樣提供「全域 CLI 安裝（uv tool）」方式，會自動安裝 uv 並引導完成。

## 專案初始化與模組安裝

安裝完成後，專案初始化、模組安裝、運行的完整流程見 [5 分鐘快速入門](../quick-start.md)。

### 方式四：使用 ErisPulse-App 客戶端（免終端）

不想裝 Python 環境？[ErisPulse-App](../ecosystem/app-tw.md) 是官方全平台客戶端
（Android / Windows / Linux / macOS），**手機直接運行**，桌面版支援最小化到
系統托盤後台常駐；內建 Python 運行時與 ErisPulse SDK，無需終端與手動配置：

- 從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 按平台選擇下載
  （Android `online`/`offline` APK、Windows `setup.exe`/`zip`、Linux `tar.gz`、macOS `zip`）
- 在 App 內建立並啟動實例，透過原生介面管理適配器與模組、瀏覽模組商店

> 完整說明見 [ErisPulse-App 安裝與使用](../ecosystem/app-tw.md)。

## 驗證安裝

### 檢查安裝

```bash
# 檢查 ErisPulse 版本
epsdk --version
```

### 運行測試

```bash
# 運行專案
epsdk run main.py
```

如果看到類似的輸出說明安裝成功：

```
[INFO] 正在初始化 ErisPulse...
[INFO] 適配器已加載: Yunhu
[INFO] 模組已加載: MyModule
[INFO] ErisPulse 初始化完成
```

## 常見問題

### 安裝失敗

1. 檢查 Python 版本是否在支援範圍內（支援 3.10 – 3.14；3.14t 自由線程 / 無 GIL 構建為實驗性支持，不作正式承諾）
2. 嘗試使用 `uv pip install ErisPulse` 替代 `pip install`
3. 如果提示權限錯誤，嘗試 `pip install --user ErisPulse` 或使用虛擬環境
4. 如果在企業代理環境下遇到 SSL 證書錯誤，嘗試 `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. 確保網路連接正常，pip 源可存取

### 配置錯誤

1. 檢查 `config.toml` 語法是否正確（TOML 格式對縮進和引號敏感）
2. 確認所有必需的配置項都已填寫
3. 查看終端日誌獲取詳細錯誤資訊
4. 使用 `epsdk init` 重新生成配置檔案

### 模組安裝失敗

1. 確認模組名稱拼寫正確（大小寫敏感）
2. 檢查網路連接
3. 使用 `epsdk list-remote` 查看可用模組列表
4. 確認模組與你當前 SDK 版本相容

### Windows PowerShell 執行策略

如果 PowerShell 提示「無法載入檔案...在此系統上禁止執行腳本」：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debian/Ubuntu 虛擬環境建立失敗

如果安裝腳本提示「虛擬環境建立失敗」，且錯誤資訊包含 `ensurepip is not available`，是因為 Debian/Ubuntu 預設未安裝 `python3-venv`（系統 Python 的 `ensurepip` 被禁用）：

```bash
sudo apt install python3.13-venv   # 按實際 Python 版本安裝對應套件
# 或安裝通用元套件：
sudo apt install python3-venv
```

安裝後重新執行安裝腳本即可。新版安裝腳本在偵測到該問題時會主動詢問並嘗試自動安裝對應系統套件；也可以改用 uv（`uv venv` 不依賴 `ensurepip`）。

## 部署

> 来源: `docs/zh-TW/user-guide/deployment.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/user-guide/deployment.md）

# 部署指南

> [!TIP]
> **什麼時候需要讀這篇**：機器人要長期掛著跑時——Docker 部署、systemd / Supervisor 程序守護、反向代理與 SSL、備份與升級都在這裡。本地開發除錯階段不需要則跳過。

機器人開發完只是開始。這篇涵蓋把它穩定掛在伺服器上所需的三種部署方式（Docker / systemd / Supervisor），以及反向代理、安全強化與備份。

## Docker 部署（推薦）

ErisPulse 提供官方 Docker 映像，內建 ErisPulse 框架和 Dashboard 管理面板，支援 `linux/amd64` 和 `linux/arm64` 架構。

### 快速啟動

```bash
# 拉取映像
docker pull erispulse/erispulse:latest

# 下載 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 設定 Dashboard 登入權杖並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

啟動後存取 `http://localhost:8000/Dashboard`，使用設定的權杖作為密碼登入。

### 國內映像加速

如果 Docker Hub 無法存取，可以使用 GitHub Container Registry 拉取映像：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

使用 ghcr.io 映像時，需要修改 `docker-compose.yml` 中的 image：

```yaml
services:
  erispulse:
    image: ghcr.io/erispulse/erispulse:latest
```

### docker-compose.yml

```yaml
services:
  erispulse:
    image: erispulse/erispulse:${ERISPULSE_TAG:-latest}
    container_name: ${CONTAINER_NAME:-erispulse}
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
      # 持久化 Python 套件目錄
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - LANG=${LANG:-en_US.UTF-8}
      - ERISPULSE_LANG=${ERISPULSE_LANG:-}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    # 優雅停機由框架內訊號處理完成（SIGTERM），此處僅控制寬限時長
    stop_grace_period: 30s
    restart: on-failure:5
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

> 以上與儲存庫根目錄的 [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) 保持一致（儲存庫版本開頭另有映像加速與環境變數說明註解），推薦直接下載使用。

### 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard 連接埠映射 |
| `ERISPULSE_TAG` | `latest` | 映像 tag（如需鎖定版本可設為具體版本號） |
| `CONTAINER_NAME` | `erispulse` | 容器名稱（多實例部署時區分實例） |
| `ERISPULSE_DASHBOARD_TOKEN` | 自動產生 | Dashboard 登入權杖（強烈建議設定） |
| `TZ` | `Asia/Shanghai` | 時區 |
| `LANG` | `en_US.UTF-8` | 系統語言，自動偵測啟動介面語言 |
| `ERISPULSE_LANG` | 空 | 強制啟動介面語言：`zh` / `zh_TW` / `en` / `ja` / `ru`（覆寫 `LANG`） |

### 資料持久化

`./config` 目錄掛載了設定檔和資料庫，包含：

- `config/config.toml` — 設定檔
- `config/config.db` — SQLite 儲存資料庫
- `config/.packages` — Python site-packages 持久化卷，儲存框架、配接器和已安裝模組（首次啟動時由入口點從映像內建備份自動初始化，之後的模組安裝與框架熱更新均寫入此目錄）

> **框架升級（含 pre/rc）與映像自癒**：入口點會在每次容器啟動時做核心套件完整性自我檢查，
> 損壞時按「使用者已安裝版本優先」原則修復——持久卷內顯式安裝/升級的版本
> （如 Dashboard 安裝的 pre 版本）會從 PyPI **重裝同版本**，絕不靜默回退到
> 映像內建版本。因此 Dashboard 升級框架後，任意次容器重啟都應保持目標版本。

## Dashboard 管理面板

ErisPulse Docker 映像內建 Dashboard 模組，提供 Web 視覺化管理介面。

### 功能概覽

| 功能 | 說明 |
|------|------|
| 儀表板 | 系統概覽、CPU/記憶體監控、執行時長、事件統計 |
| 機器人管理 | 查看各平台機器人線上狀態和資訊 |
| 事件查看 | 即時事件流，支援按類型和平台篩選 |
| 日誌查看 | 按模組和層級篩選的日誌檢視器 |
| 模組管理 | 查看、載入、卸載已安裝的模組和配接器 |
| 模組商店 | 瀏覽遠端可用套件並一鍵安裝 |
| 設定編輯 | 線上編輯 `config.toml` |
| 儲存管理 | 瀏覽和編輯 Key-Value 儲存資料 |
| 備份 | 匯出/匯入設定和儲存資料 |
| 稽核日誌 | 記錄所有管理操作 |

### 透過 Dashboard 安裝模組

Dashboard 整合了模組商店功能，你可以：

1. **從商店安裝**：瀏覽遠端模組清單，選擇需要的模組一鍵安裝
2. **上傳本地套件**：直接上傳 `.whl` 或 `.zip` 檔案進行安裝，方便測試個人開發的模組

> **模組開發者的快速測試流程**：使用 Docker 部署後，在 Dashboard 中透過「上傳本地套件」功能直接上傳你建置的 `.whl` 檔案進行測試，無需手動操作容器。

## 程序監督與硬重啟

ErisPulse 的硬重啟（`sdk.hard_restart()`）依賴**外部監督者**在程序結束碼為 42 時重新拉起程序——SDK 自己不會拉起新程序。正式環境務必設定監督者，否則硬重啟後程序不會自動恢復：

- Docker：官方 compose 使用 `restart: on-failure:5`——非零結束碼即重啟（覆寫硬重啟的結束碼 42），連續 5 次上限防死循環；需要不限次數可自行改為 `unless-stopped`
- systemd：`Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord：將 42 加入可重啟結束碼
- 純 Python 自訂監督者：以迴圈 `Popen` + 偵測 `returncode == 42`

各監督者的完整設定範例與結束碼 42 契約說明見 [啟動流程 → 監督者指南](../advanced/startup.md#監督者指南)。

## 健康檢查

SDK 內建健康檢查端點：

```bash
# 健康檢查
curl http://localhost:8000/health
```

官方 docker-compose.yml 已內建以下健康檢查；自行撰寫 compose 檔案時可參考：

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

## 反向代理

如果需要透過 Nginx 等反向代理公開 Dashboard：

```nginx
server {
    listen 80;
    server_name bot.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket 支援（Dashboard 即時事件流需要）
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL 可使用 Let's Encrypt：

```bash
sudo certbot --nginx -d bot.example.com
```

## 手動部署（pip）

如果不使用 Docker，也可以手動部署。

### 正式環境設定

```toml
# config/config.toml

[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"
log_files = ["app.log"]
memory_limit = 5000

[ErisPulse.framework]
enable_lazy_loading = true
```

### systemd (Linux)

建立 `/etc/systemd/system/erispulse-bot.service`：

```ini
[Unit]
Description=ErisPulse Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/erispulse-bot
ExecStart=/opt/erispulse-bot/venv/bin/epsdk run main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

管理：

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

建立 `/etc/supervisor/conf.d/erispulse-bot.conf`：

```ini
[program:erispulse-bot]
command=/opt/erispulse-bot/venv/bin/python -m ErisPulse run main.py
directory=/opt/erispulse-bot
user=bot
autostart=true
autorestart=true
stderr_logfile=/var/log/erispulse-bot/err.log
stdout_logfile=/var/log/erispulse-bot/out.log
```

### uv tool 分離部署（CLI 與專案環境隔離）

`uv tool install` 會將 `epsdk` 安裝為**獨立的工具環境**，CLI 自身與專案依賴徹底隔離：升級 CLI 不會動到專案 `.venv`，專案依賴變動也不會影響 CLI。

```bash
# 1. 全域安裝 CLI（自動提供 epsdk / ep 指令）
uv tool install ErisPulse

# 2. 專案內只放機器人依賴（.venv 由 uv 管理）
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # 依需求追加配接器

# 3. 用 CLI 執行（自動偵測並使用專案 .venv 中的直譯器）
epsdk run main.py
```

行為要點：

- `epsdk run` 的目標直譯器解析順序：`ERISPULSE_PYTHON` 環境變數 → 專案 `.venv` → 當前直譯器；工具環境本身只承載 CLI，元件（配接器/模組）應裝進專案 `.venv`
- `epsdk install` / `uninstall` / `upgrade` / `list` 同樣作用於專案 `.venv`，不會污染工具環境
- 升級 CLI：`uv tool upgrade ErisPulse`（或直接 `epsdk self-update`，uv tool 環境下會自動改走 `uv tool upgrade`）；升級專案依賴：在專案目錄執行 `uv sync` / `uv add`，兩者互不影響
- 伺服器情境下工具環境由 uv 統一管理（`uv tool list` 查看、`uv tool upgrade --all` 批次升級），無需手動維護全域 pip 套件
- 若在無專案的目錄用 `uv run epsdk ...` 執行，會落入**一次性隔離環境**（安裝的元件不會持久化）；伺服器上請一律直接呼叫 `epsdk`，或先 `cd` 進專案目錄

## 安全建議

1. **設定 Dashboard 權杖**：使用強隨機權杖，不要使用預設值
2. **不要將連接埠公開到公網**：除非使用反向代理 + SSL，否則將 Dashboard 連接埠限制在內網
3. **保護資料目錄**：`config/` 目錄包含設定和資料庫，設定適當的檔案權限
4. **定期更新**：使用 `epsdk self-update` 或拉取最新 Docker 映像
5. **不要以 root 執行**：手動部署時建立專用使用者
6. **使用 Docker 重啟策略**：官方 compose 的 `restart: on-failure:5` 已確保異常結束（含硬重啟結束碼 42）後自動重啟

## 多實例部署

執行多個機器人實例時：

1. 每個實例使用獨立的專案目錄和 `docker-compose.yml`
2. 使用不同的連接埠號：`ERISPULSE_PORT=8001`
3. 使用不同的容器名稱：`container_name: erispulse-bot2`

## 更新與維護

### Docker 方式

```bash
# 拉取最新映像
docker compose pull

# 重啟以使用新映像
docker compose up -d
```

### pip 方式

```bash
epsdk self-update
epsdk upgrade
```

### uv tool 方式

```bash
# 升級 CLI 工具環境
uv tool upgrade ErisPulse

# 升級專案依賴（在專案目錄內執行）
uv sync
```

### 執行時熱重載伺服器設定

修改監聽位址 / 連接埠 / SSL 憑證後無需重啟程序，在任意協程中呼叫 `router.reload()`：

```python
await sdk.router.reload(port=9000)                                # 換連接埠
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # 熱更換憑證（憑證續期情境）
await sdk.router.reload(host="0.0.0.0", port=9000)                # 未指定的參數沿用當前設定
```

- 重用同一 FastAPI 應用程式，模組註冊的 HTTP / WebSocket / SSE 路由全部保留
- 先驗證新設定（憑證可建置、連接埠可用）再切換；失敗時以舊設定恢復服務並回傳 `False`，
  保證回傳 `False` = 舊服務保持可用
- 伺服器未執行時回傳 `False`（首次啟動請使用 `sdk.router.start()`）

### 備份

定期備份 `config/` 目錄：

```bash
# Docker 部署
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# 或在 Dashboard 中使用「備份」功能匯出
```
