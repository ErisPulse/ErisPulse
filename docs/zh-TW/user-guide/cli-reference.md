# CLI 命令參考

ErisPulse 命令列工具 (`epsdk`) 提供專案管理和套件管理功能。

> **提示**：所有命令均可透過 `epsdk <命令> --help` 查看詳細的參數說明。

---

## 套件管理命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | 安裝模組/配接器 |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | 解除安裝模組/配接器 |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 升級指定模組或全部 |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | 更新 SDK 本身 |

## 診斷命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose]` | 診斷環境並輸出健康報告 |

### install

安裝 ErisPulse 模組或配接器套件。若不指定套件名稱則進入互動式安裝介面。

**別名：** `i`, `add`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[package]...` | | 要安裝的套件名稱，可指定多個 |
| `--upgrade` | `-U` | 安裝時升級到最新版本 |
| `--pre` | | 允許安裝預發布版本 |
| `--editable` | `-e` | 以可編輯模式安裝（需指定路徑） |
| `--user` | | 安裝到使用者 site-packages 目錄 |
| `--no-deps` | | 不安裝依賴 |
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
| `--config-settings` | | 傳遞給建置後端的設定（可多次指定） |
| `--no-binary` | | 限制不使用二進位套件（格式如 `:all:`） |
| `--only-binary` | | 限制僅使用二進位套件（格式如 `:all:`） |
| `--prefer-binary` | | 優先選擇二進位套件 |
| `--build-isolation` | | 啟用建置隔離 |
| `--no-build-isolation` | | 禁用建置隔離 |
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

解除安裝已安裝的 ErisPulse 模組或配接器套件。若不指定套件名稱則進入互動式解除安裝介面。

**別名：** `rm`, `remove`

**參數：**

| 參數 | 說明 |
|------|------|
| `<package>...` | 要解除安裝的套件名稱，可指定多個 |
| `--no-uv` | 使用 pip 代替 uv |

**範例：**

```bash
# 解除安裝單個模組
epsdk uninstall Weather

# 解除安裝多個模組
epsdk uninstall Yunhu Weather
```

### upgrade

升級已安裝的 ErisPulse 元件。不指定套件名稱則互動式升級全部。

**別名：** `up`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[package]...` | | 要升級的套件名稱，可指定多個 |
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

---

## 資訊查詢命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | 列出已安裝的元件 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | 列出遠端可用的元件 |

### list

列出已安裝的 ErisPulse 模組和配接器。

**別名：** `l`, `ls`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--type` | `-t` | 指定類型：`modules`、`adapters`、`all`（預設） |
| `--outdated` | `-o` | 僅顯示可升級的套件 |

**範例：**

```bash
# 列出所有已安裝的元件
epsdk list

# 只列出模組
epsdk list -t modules

# 只列出配接器
epsdk list -t adapters

# 只顯示可升級的套件
epsdk list -o
```

### list-remote

列出遠端倉庫中可用的 ErisPulse 模組和配接器。

**別名：** `lsr`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--type` | `-t` | 指定類型：`modules`、`adapters`、`all`（預設） |
| `--refresh` | `-r` | 強制重新整理遠端套件列表快取 |

**範例：**

```bash
# 列出所有遠端可用元件
epsdk list-remote

# 只列出遠端模組
epsdk list-remote -t modules

# 強制重新整理快取後列出
epsdk list-remote -r
```

---

## 執行控制命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | 執行指定腳本或 SDK |

### run

執行 ErisPulse 專案腳本或直接啟動 SDK。支援熱重載模式。

**別名：** `r`

**參數：**

| 參數 | 說明 |
|------|------|
| `[script]` | 要執行的腳本檔案，不指定則執行 SDK |
| `--reload` | 啟用熱重載模式，監控檔案變化自動重啟 |

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
```

---

## 專案管理命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `init` | — | `[--project-name/-n <name>] [--quick/-q] [--force/-f] [--here] [--no-uv]` | 初始化 ErisPulse 專案 |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | 建立模組/配接器腳手架 |

### init

初始化一個新的 ErisPulse 專案。支援互動式與快速模式。

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--project-name` | `-n` | 專案名稱 |
| `--quick` | `-q` | 快速模式，跳過互動式嚮導 |
| `--force` | `-f` | 強制覆蓋現有設定檔 |
| `--here` | | 在當前目錄初始化，不建立子目錄 |
| `--no-uv` | | 使用 pip 代替 uv |

**範例：**

```bash
# 互動式初始化
epsdk init

# 快速初始化
epsdk init -q -n my_bot

# 強制覆蓋已有設定
epsdk init -f

# 在當前目錄初始化
epsdk init --here -n my_bot
```

### create

建立 ErisPulse 模組或配接器的腳手架專案。

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `{module,adapter}` | | 要建立的類型：`module` 或 `adapter` |
| `--name` | `-n` | 專案名稱（PascalCase） |
| `--description` | `-d` | 專案描述 |
| `--author` | `-a` | 作者名稱 |
| `--email` | `-e` | 作者電子郵件 |
| `--homepage` | | 專案首頁 URL |
| `--output` | `-o` | 輸出目錄（預設當前目錄） |
| `--force` | `-f` | 強制覆蓋已存在的目錄 |

**範例：**

```bash
# 互動式建立（引導選擇類型和填寫資訊）
epsdk create

# 直接建立 Module 專案
epsdk create module -n MyModule

# 直接建立 Adapter 專案
epsdk create adapter -n MyAdapter

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
```

---

## 類型存根命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | 產生類型存根檔案以啟用 IDE 自動補全 |

### types

掃描已安裝的 ErisPulse 模組和配接器，為它們產生 `.pyi` 類型存根檔案，從而在 IDE 中獲得準確的程式碼自動補全與類型檢查支援。

**別名：** `t`, `stub`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--output` | `-o` | 輸出路徑（預設當前目錄下的 `ep-stubs/`） |
| `--force` | | 強制覆蓋已存在的存根檔案 |
| `--adapters-only` | | 僅產生配接器的類型存根 |
| `--modules-only` | | 僅產生模組的類型存根 |

> **注意：** `--adapters-only` 與 `--modules-only` 互斥，同時指定時後者生效。

**範例：**

```bash
# 為所有已安裝的模組和配接器產生類型存根
epsdk types

# 僅產生配接器存根
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
| `--help` | `-h` | 顯示說明資訊 |
| `--version` | `-V` | 顯示版本資訊 |
| `--verbose` | `-v` | 顯示詳細輸出（可疊加 `-vv`/`-vvv`） |
| `--no-color` | | 禁用彩色輸出（適合 CI / 日誌採集） |
| `--yes` | `-y` | 自動確認所有互動提示（非互動式執行） |

---

## 環境診斷

### doctor

診斷當前 CLI 執行環境，輸出健康報告。用於排查"為什麼裝不上 / 連不上"類問題。

| 參數 | 說明 |
|------|------|
| `--verbose` | 顯示詳細診斷資訊 |

**檢查項**：
- **Python**：直譯器版本與路徑
- **安裝後端**：使用 `uv` 還是 `pip`
- **目標直譯器**：套件實際安裝到的目標 Python 環境
- **設定檔**：`config/config.toml` 是否存在
- **PyPI 連通性**：能否存取 PyPI（並顯示發現的元件數）
- **系統代理**：是否偵測到代理

```bash
# 執行環境診斷
epsdk doctor

# 使用別名
epsdk diag
```

---

## 互動式安裝

執行 `epsdk install` 不指定套件名稱時進入互動式安裝：

```bash
epsdk install
```

互動介面提供：
1. 配接器選擇
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

### 列出元件

```bash
# 列出所有元件
epsdk list

# 只列出配接器
epsdk list -t adapters

# 只列出可升級的元件
epsdk list -o

# 查看遠端可用元件
epsdk list-remote
```

### 解除安裝元件

```bash
# 解除安裝單個元件
epsdk uninstall Weather

# 解除安裝多個元件
epsdk uninstall Yunhu Weather
```

### 升級元件

```bash
# 升級所有元件
epsdk upgrade

# 升級指定元件
epsdk upgrade Weather

# 強制升級
epsdk upgrade -f
```

### 執行專案

```bash
# 普通執行
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