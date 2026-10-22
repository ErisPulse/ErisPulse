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

## 診斷命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose] [--fix]` | 診斷環境並輸出健康報告；`--fix` 嘗試自動修復 |

### install

安裝 ErisPulse 模組或適配器套件。若不指定套件名則進入互動式安裝介面。

**別名：** `i`, `add`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[套件]...` | | 要安裝的套件名稱，可指定多個 |
| `--upgrade` | `-U` | 安裝時升級到最新版本 |
| `--pre` | | 允許安裝預發布版本 |
| `--editable` | `-e` | 以可編輯模式安裝（需指定路徑） |
| `--user` | | 安裝到使用者 site-packages 目錄 |
| `--no-deps` | | 不安裝相依性 |
| `--target` | `-t` | 安裝到指定目錄 |
| `--index-url` | | 指定 PyPI 鏡像源位址 |
| `--extra-index-url` | | 額外 PyPI 鏡像源位址（可多次指定） |
| `--no-cache-dir` | | 禁用快取 |
| `--requirement` | `-r` | 從 requirements 檔案安裝 |
| `--constraint` | `-c` | 從約束檔案安裝 |
| `--force-reinstall` | | 強制重新安裝 |
| `--ignore-installed` | | 忽略已安裝的套件 |
| `--compile` | | 安裝後編譯 .pyc 檔案 |
| `--no-compile` | | 安裝後不編譯 .pyc 檔案 |
| `--prefix` | | 安裝到指定前綴目錄 |
| `--src` | | 可編輯安裝時使用的原始碼目錄 |
| `--config-settings` | | 傳遞給建構後端的配置（可多次指定） |
| `--no-binary` | | 限制不使用二進位套件（格式如 `:all:`） |
| `--only-binary` | | 限制僅使用二進位套件（格式如 `:all:`） |
| `--prefer-binary` | | 优先選擇二進位套件 |
| `--build-isolation` | | 啟用建構隔離 |
| `--no-build-isolation` | | 禁用建構隔離 |
| `--upgrade-strategy` | | 升級策略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | 允許修改系統套件管理器管理的 Python 套件 |
| `--no-uv` | | 使用 pip 代替 uv |

**範例：**

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

卸載已安裝的 ErisPulse 模組或適配器套件。若不指定套件名則進入互動式卸載介面。

**別名：** `rm`, `remove`

**參數：**

| 參數 | 說明 |
|------|------|
| `<套件>...` | 要卸載的套件名稱，可指定多個 |
| `--no-uv` | 使用 pip 代替 uv |

**範例：**

```bash
# 卸載單個模組
epsdk uninstall Weather

# 卸載多個模組
epsdk uninstall Yunhu Weather
```

### upgrade

升級已安裝的 ErisPulse 組件。不指定套件名則互動式升級全部。

**別名：** `up`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[套件]...` | | 要升級的套件名稱，可指定多個 |
| `--force` | `-f` | 強制升級，跳過確認 |
| `--pre` | | 允許升級到預發布版本 |
| `--no-uv` | | 使用 pip 代替 uv |

**範例：**

```bash
# 升級所有套件
epsdk upgrade

# 升級指定套件
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
| `--pre` | | 允許更新到預發布版本 |
| `--force` | `-f` | 強制更新，跳過確認 |
| `--no-uv` | | 使用 pip 代替 uv |

**範例：**

```bash
# 更新到最新穩定版
epsdk self-update

# 更新到指定版本
epsdk self-update 1.2.3

# 允許預發布版本
epsdk self-update --pre

# 強制更新
epsdk self-update -f
```

> [!NOTE]
> 透過 `uv tool install ErisPulse` 安裝時，本命令自動改走 `uv tool upgrade ErisPulse`（指定版本時為 `uv tool install ErisPulse==<版本> --force`），直接 pip 升級工具環境會被 uv 的清單還原抹掉。
> Windows 下更新在新控制台視窗中進行：當前 CLI 需先退出以解除工具環境檔案佔用，視窗提示完成後重新打開終端即可。

---

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
> （也可透過 `ERISPULSE_PYTHON` 環境變數明確指定解釋器）。`epsdk install` /  
> `uninstall` / `upgrade` / `list` 同樣作用於項目虛擬環境。

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload] [--strict/--no-strict]` | 運行指定腳本或 SDK |
| `stop` | — | `[--force] [--pid PID]` | 停止正在運行的實例（由 `epsdk run` 啟動） |
| `restart` | — | `[--force] [--pid PID]` | 重新啟動正在運行的實例（停止後按原參數重新啟動） |

### run

運行 ErisPulse 項目腳本或直接啟動 SDK。支援熱重載模式。

**別名：** `r`

**參數：**

| 參數 | 說明 |
|------|------|
| `[script]` | 要運行的腳本檔案，不指定則運行 SDK |
| `--reload` | 啟用熱重載模式，監控檔案變化自動觸發組件級程式碼熱重載（聯動熱重載系統，無需整進程重啟） |
| `--strict` / `--no-strict` | 臨時開啟 / 關閉嚴格模式（僅本次生效，不寫入設定）；預設遵循 `ErisPulse.framework.strict_mode` |

**範例：**

```bash
# 直接運行 SDK
epsdk run

# 運行指定腳本檔案
epsdk run main.py

# 熱重載模式運行（檔案變更自動觸發程式級熱重載）
epsdk run main.py --reload

# SDK 熱重載模式
epsdk run --reload

# 臨時嚴格模式：啟動前自檢失敗即退出，框架嚴格級別本次提升為至少 1
epsdk run main.py --strict

# 臨時寬鬆模式（設定裡開了 strict_mode 但本次想先跑起來）
epsdk run main.py --no-strict
```

**啟動前自檢：** `run` 啟動前會快速檢查 `config/config.toml` 可解析性與已安裝組件的必填設定完整性，嚴格性預設遵循 `ErisPulse.framework.strict_mode`（非 0 時檢查失敗即退出，0 時僅警告繼續）。設定檔遺失視為正常首次啟動，僅提示不判失敗。`--strict` 臨時開啟：預檢失敗即退出，同時框架嚴格級別本次提升為至少 1（跳過不合規組件，經 `ERISPULSE_FRAMEWORK_STRICT_MODE` 環境變數傳導到運行進程，不寫入設定檔）；`--no-strict` 反之臨時壓到寬鬆。自檢自身異常時自動跳過，不含網路探測，不會阻塞啟動。

### stop

停止正在運行的 ErisPulse 實例（由 `epsdk run` 啟動、並在同一項目目錄下執行）。  
`run` 啟動時會把監督進程 PID、當前框架子進程 PID 與原始啟動命令寫入  
`.erispulse/runtime.json`，`stop` 據此定位實例。

**停止順序：** POSIX 下先向監督進程發 SIGINT（與 Ctrl+C 同款優雅收尾路徑——  
finally 鏈自動終止框架子進程），超時逐級升級 SIGTERM / SIGKILL；Windows 無  
進程訊號語義，先終止框架子進程再終止監督進程（避免監督者把強殺誤判為崩潰  
重新拉起）。

**參數：**

| 參數 | 說明 |
|------|------|
| `--force` | 跳過優雅停止，直接強制終止 |
| `--pid PID` | 直接指定目標進程 PID（覆蓋運行狀態檔案，用於非標準啟動方式） |

**範例：**

```bash
# 停止當前項目的運行實例
epsdk stop

# 強制終止
epsdk stop --force
```

### restart

重新啟動正在運行的 ErisPulse 實例：按 `stop` 的語義停止後，以狀態檔案中記錄的  
**原始啟動命令**重新啟動（前檯接管當前終端，新實例會寫入新的運行狀態檔案）。

**參數：** 同 `stop`（`--force` / `--pid PID`）。

**範例：**

```bash
# 優雅重新啟動（pip 升級適配器/模組後讓程式碼生效；運行中模組也可用  
# sdk.reload_module / sdk.adapter.reload 程式級熱重載，無需重新啟動）
epsdk restart
```

> [!NOTE]  
> `python main.py` 等繞過 `epsdk run` 的啟動方式不會寫運行狀態檔案——此類  
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
> 本命令需要 ErisPulse **2.7.0+**。

診斷目前 CLI 運行環境，輸出健康報告。用於排查"為什麼裝不上 / 連不上"類問題。

| 參數 | 說明 |
|------|------|
| `--verbose` | 顯示詳細診斷資訊 |
| `--fix` | 診斷後嘗試自動修復可修復的問題 |

**檢查項**：
- **Python**：解釋器版本與路徑
- **安裝後端**：使用 `uv` 還是 `pip`
- **目標解釋器**：套件實際安裝到的目標 Python 環境
- **配置檔案**：`config/config.toml` 是否存在
- **組件配置**：已安裝組件的宣告式配置完整性（"裝好了跑不起來"多因必填項缺失）
- **PyPI 連通性**：能否存取 PyPI（並顯示發現的組件數）
- **系統代理**：是否檢測到代理

**自動修復（`--fix`）**：
- `config.toml` 缺失 → 按目前語言生成初始配置檔案（與 `init` 建項同源）
- 組件配置"待完善" → 逐個拉起互動式配置向導補全必填項（非互動環境提示改用 `epsdk config <名稱>`）
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

## 下一步

- **元件裝好了要填配置**：用 `epsdk config` 互動式精靈，或看 [配置檔說明](configuration.md) 手動編輯
- **程式碼寫完想要 IDE 補全**：跑 `epsdk types`，詳見 [型別存根生成](../getting-started/ide-completion.md)
- **機器人跑不起來**：先 `epsdk doctor` 診斷環境（見[環境診斷](#環境診斷)），要長期部署再看 [部署指南](deployment.md)