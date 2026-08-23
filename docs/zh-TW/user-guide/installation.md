# 安裝參考

> 本文是安裝方式的**完整參考**（pip / uv / Docker / 故障排查）。
> 如果你只想快速跑起來，[5 分鐘快速開始](../quick-start.md) 已經覆蓋了最簡流程。

## 系統要求

- Python 3.10 或更高版本
- pip 或 uv（推薦）
- 足夠的磁碟空間（至少 100MB）

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
# 建立專案目錄
mkdir my_bot && cd my_bot

# 安裝 Python 3.12
uv python install 3.12

# 建立虛擬環境
uv venv
```

#### 啟動虛擬環境

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

## 專案初始化與模組安裝

安裝完成後，專案初始化、模組安裝、執行的完整流程請見 [5 分鐘快速開始](../zh-TW/quick-start.md)。

### 方式三：使用 ErisPulse-App 用戶端（免終端）

不想安裝 Python 環境？[ErisPulse-App](../zh-TW/ecosystem/app.md) 是官方全平台用戶端
（Android / Windows / Linux / macOS），**手機直接執行**，桌面版支援最小化到
系統圖示後台常駐；內建 Python 執行環境與 ErisPulse SDK，無需終端機與手動設定：

- 從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 按平台選擇下載
  （Android `online`/`offline` APK、Windows `setup.exe`/`zip`、Linux `tar.gz`、macOS `zip`）
- 在 App 內建立並啟動執行個體，透過原生介面管理適配器與模組、瀏覽模組商店

> 完整說明請見 [ErisPulse-App 安裝與使用](../zh-TW/ecosystem/app.md)。

## 驗證安裝

### 檢查安裝

```bash
# 檢查 ErisPulse 版本
epsdk --version
```

### 執行測試

```bash
# 執行專案
epsdk run main.py
```

如果看到類似的輸出說明安裝成功：

```
[INFO] 正在初始化 ErisPulse...
[INFO] 介面卡已載入: Yunhu
[INFO] 模組已載入: MyModule
[INFO] ErisPulse 初始化完成

## 常見問題

### 安裝失敗

1. 檢查 Python 版本是否 >= 3.10（推薦 3.10 - 3.13）
2. 嘗試使用 `uv pip install ErisPulse` 替代 `pip install`
3. 如果提示權限錯誤，嘗試 `pip install --user ErisPulse` 或使用虛擬環境
4. 如果在企業代理環境下遇到 SSL 憑證錯誤，嘗試 `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. 確保網路連線正常，pip 源可存取

### 配置錯誤

1. 檢查 `config.toml` 語法是否正確（TOML 格式對縮排和引號敏感）
2. 確認所有必要的配置項都已填寫
3. 查看終端日誌取得詳細錯誤資訊
4. 使用 `epsdk init` 重新生成配置檔案

### 模組安裝失敗

1. 確認模組名稱拼寫正確（區分大小寫）
2. 檢查網路連線
3. 使用 `epsdk list-remote` 查看可用模組清單
4. 確認模組與您當前 SDK 版本相容

### Windows PowerShell 執行策略

如果 PowerShell 提示「無法載入檔案...因為在此系統上禁止執行腳本」：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 下一步

- [CLI 命令參考](cli-reference.md) - 了解所有命令行命令
- [設定檔說明](configuration.md) - 詳細了解設定選項