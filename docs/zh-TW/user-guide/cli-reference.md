# CLI 命令參考

ErisPulse 命令行工具（`epsdk`）提供專案管理和套件管理功能。

> **提示**：所有命令均可透過 `epsdk <命令> --help` 查看詳細的參數說明。

---

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 套件管理命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `install` | `i`, `add` | `[套件]... [--upgrade/-U] [--pre] [-e 路徑] [--user] [--no-deps] [-t 目錄] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r 檔案] [-c 檔案] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix 目錄] [--src 目錄] [--config-settings 設定] [--no-binary 格式] [--only-binary 格式] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | 安裝模組/適配器 |
| `uninstall` | `rm`, `remove` | `<套件>... [--no-uv]` | 卸載模組/適配器 |
| `upgrade` | `up` | `[套件]... [--force/-f] [--pre] [--no-uv]` | 升級指定套件或全部 |
| `self-update` | `su`, `update` | `[版本] [--pre] [--force/-f] [--no-uv]` | 更新 SDK 本身 |

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 臨床診斷命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose]` | 臨床診斷環境並輸出健康報告 |

### install

安裝 ErisPulse 模組或適配器套件。若不指定套件名稱則進入互動式安裝介面。

**別名：** `i`, `add`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[package]...` | | 要安裝的套件名稱，可指定多個 |
| `--upgrade` | `-U` | 安裝時升級到最新版本 |
| `--pre` | | 允許安裝預發行版本 |
| `--editable` | `-e` | 以可編輯模式安裝（需指定路徑） |
| `--user` | | 安裝到使用者 site-packages 目錄 |
| `--no-deps` | | 不安裝相依性 |
| `--target` | `-t` | 安裝到指定目錄 |
| `--index-url` | | 指定 PyPI 鏡像來源地址 |
| `--extra-index-url` | | 額外 PyPI 鏡像來源地址（可多次指定） |
| `--no-cache-dir` | | 禁用快取 |
| `--requirement` | `-r` | 從 requirements 檔案安裝 |
| `--constraint` | `-c` | 從約束檔案安裝 |
| `--force-reinstall` | | 強制重新安裝 |
| `--ignore-installed` | | 忽略已安裝的套件 |
| `--compile` | | 安裝後編譯 .pyc 檔案 |
| `--no-compile` | | 安裝後不編譯 .pyc 檔案 |
| `--prefix` | | 安裝到指定前綴目錄 |
| `--src` | | 可編輯安裝時使用的原始碼目錄 |
| `--config-settings` | | 傳遞給建置後端的設定（可多次指定） |
| `--no-binary` | | 限制不使用二進位套件（格式如 `:all:`） |
| `--only-binary` | | 限制僅使用二進位套件（格式如 `:all:`） |
| `--prefer-binary` | | 优先選擇二進位套件 |
| `--build-isolation` | | 啟用建置隔離 |
| `--no-build-isolation` | | 禁用建置隔離 |
| `--upgrade-strategy` | | 升級策略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | 允許修改系統套件管理器管理的 Python 套件 |
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

卸載已安裝的 ErisPulse 模組或適配器套件。若不指定套件名稱則進入互動式卸載介面。

**別名：** `rm`, `remove`

**參數：**

| 參數 | 說明 |
|------|------|
| `<package>...` | 要卸載的套件名稱，可指定多個 |
| `--no-uv` | 使用 pip 代替 uv |

**示例：**

```bash
# 卸載單個模組
epsdk uninstall Weather

# 卸載多個模組
epsdk uninstall Yunhu Weather
```

### upgrade

升級已安裝的 ErisPulse 組件。不指定套件名稱則互動式升級全部。

**別名：** `up`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[package]...` | | 要升級的套件名稱，可指定多個 |
| `--force` | `-f` | 強制升級，跳過確認 |
| `--pre` | | 允許升級到預發行版本 |
| `--no-uv` | | 使用 pip 代替 uv |

**示例：**

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
| `--pre` | | 允許更新到預發行版本 |
| `--force` | `-f` | 強制更新，跳過確認 |
| `--no-uv` | | 使用 pip 代替 uv |

**示例：**

```bash
# 更新到最新穩定版
epsdk self-update

# 更新到指定版本
epsdk self-update 1.2.3

# 允許預發行版本
epsdk self-update --pre

# 強制更新
epsdk self-update -f

## 信息查詢命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | 列出已安裝的組件 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | 列出遠端可用的組件 |

### list

列出已安裝的 ErisPulse 模組和適配器。

**別名：** `l`, `ls`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--type` | `-t` | 指定類型：`modules`、`adapters`、`all`（預設） |
| `--outdated` | `-o` | 僅顯示可升級的套件 |

**示例：**

```bash
# 列出所有已安裝的組件
epsdk list

# 只列出模組
epsdk list -t modules

# 只列出適配器
epsdk list -t adapters

# 僅顯示可升級的套件
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

**示例：**

```bash
# 列出所有遠端可用組件
epsdk list-remote

# 只列出遠端模組
epsdk list-remote -t modules

# 強制刷新快取後列出
epsdk list-remote -r

## 運行控制命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | 執行指定腳本或 SDK |

### run

執行 ErisPulse 項目腳本或直接啟動 SDK。支援熱重載模式。

**別名：** `r`

**參數：**

| 參數 | 說明 |
|------|------|
| `[script]` | 要執行的腳本檔案，不指定則執行 SDK |
| `--reload` | 啟用熱重載模式，監控檔案變更自動重啟 |

**範例：**

```bash
# 直接執行 SDK
epsdk run

# 執行指定腳本檔案
epsdk run main.py

# 熱重載模式執行（檔案變更自動重啟）
epsdk run main.py --reload

# SDK 熱重載模式
epsdk run --reload

## 項目管理命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `init` | — | `[--project-name/-n <name>] [--quick/-q] [--force/-f] [--here] [--no-uv]` | 初始化 ErisPulse 項目 |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | 創建模組/適配器腳手架 |

### init

初始化一個新的 ErisPulse 項目。支援互動式與快速模式。

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--project-name` | `-n` | 項目名稱 |
| `--quick` | `-q` | 快速模式，跳過互動式嚮導 |
| `--force` | `-f` | 強制覆蓋現有配置檔案 |
| `--here` | | 在當前目錄初始化，不建立子目錄 |
| `--no-uv` | | 使用 pip 代替 uv |

**範例：**

```bash
# 互動式初始化
epsdk init

# 快速初始化
epsdk init -q -n my_bot

# 強制覆蓋已有配置
epsdk init -f

# 在當前目錄初始化
epsdk init --here -n my_bot
```

### create

創建 ErisPulse 模組或適配器的腳手架項目。

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `{module,adapter}` | | 要創建的類型：`module` 或 `adapter` |
| `--name` | `-n` | 項目名稱（PascalCase） |
| `--description` | `-d` | 項目描述 |
| `--author` | `-a` | 作者名稱 |
| `--email` | `-e` | 作者郵箱 |
| `--homepage` | | 項目主頁 URL |
| `--output` | `-o` | 輸出目錄（預設當前目錄） |
| `--force` | `-f` | 強制覆蓋已存在的目錄 |
| `--local` | | 創建本地插件（僅 `module` 可用）：生成 `plugins/<name>/` 包結構，免打包安裝 |

**範例：**

```bash
# 互動式創建（引導選擇類型和填寫資訊）
epsdk create

# 直接創建 Module 項目
epsdk create module -n MyModule

# 創建本地插件（放入項目 plugins/ 目錄，啟動時自動發現，支援熱重載）
epsdk create module -n MyModule --local

# 直接創建 Adapter 項目
epsdk create adapter -n MyAdapter

# 完整參數
epsdk create module -n MyModule -d "模組描述" -a "作者" -e "mail@example.com"

# 指定輸出目錄
epsdk create module -n MyModule -o ./projects

# 強制覆蓋已有目錄
epsdk create module -n MyModule -f

## 語言命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | 查看或切換 CLI 顯示語言 |

### i18n

查看當前 CLI 語言、列出支援的語言、切換顯示語言。若不指定參數則進入互動式選擇介面。

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

## 類型存根命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | 產生類型存根檔案以啟用 IDE 自動完成 |

### types

掃描已安裝的 ErisPulse 模組和適配器，為它們產生 `.pyi` 類型存根檔案，進而在 IDE 中獲得準確的程式碼自動完成與類型檢查支援。

**別名：** `t`, `stub`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--output` | `-o` | 輸出路徑（預設為當前目錄下的 `ep-stubs/`） |
| `--force` | | 強制覆蓋已存在的存根檔案 |
| `--adapters-only` | | 僅產生適配器的類型存根 |
| `--modules-only` | | 僅產生模組的類型存根 |

> **注意：** `--adapters-only` 與 `--modules-only` 相互排斥，同時指定時後者生效。

**範例：**

```bash
# 為所有已安裝的模組和適配器產生類型存根
epsdk types

# 僅產生適配器存根
epsdk types --adapters-only

# 輸出到指定目錄
epsdk types -o ./typings

# 強制覆蓋已有檔案
epsdk types --force
```

---

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 全局參數

以下參數適用於所有命令：

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--help` | `-h` | 顯示幫助資訊 |
| `--version` | `-V` | 顯示版本資訊 |
| `--verbose` | `-v` | 顯示詳細輸出（可疊加 `-vv`/`-vvv`） |
| `--no-color` | | 禁用彩色輸出（適合 CI / 日誌收集） |
| `--yes` | `-y` | 自動確認所有互動提示（非互動式運行） |

---

docs/zh-TW/quick-start.md

## 環境診斷

### doctor

> [!NOTE]
> 此命令需要 ErisPulse **2.7.0+**。

診斷目前 CLI 運行環境，並輸出健康報告。用於排查「為什麼無法安裝 / 連不上」之類的問題。

| 參數 | 說明 |
|------|------|
| `--verbose` | 顯示詳細診斷資訊 |

**檢查項目**：
- **Python**：解釋器版本與路徑
- **安裝後端**：使用 `uv` 還是 `pip`
- **目標解釋器**：套件實際安裝到的目標 Python 環境
- **設定檔**：`config/config.toml` 是否存在
- **PyPI 連通性**：能否存取 PyPI（並顯示發現的元件數）
- **系統代理**：是否偵測到代理

```bash
# 運行環境診斷
epsdk doctor

# 使用別名
epsdk diag
```

---

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 傳統中文

執行 `epsdk install` 時若未指定套件名稱，將進入互動式安裝：

```bash
epsdk install
```

互動介面提供：
1. 驅動程式選擇
2. 模組選擇
3. 自訂安裝

[**English**](docs/zh-TW/quick-start.md) | [**简体中文**](docs/zh-TW/quick-start.md)

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

### 產生類型存根

```bash
# 產生所有類型存根
epsdk types

# 僅產生模組類型存根
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