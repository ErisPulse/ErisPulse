# 安裝參考

> 本文是安裝方式的**完整參考**（pip / uv / Docker / 故障排除）。
> 如果你只想快速跑起來，[5 分鐘快速開始](../quick-start.md) 已經涵蓋了最簡流程。

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
# 建立專案資料夾
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

## 項目初始化與模組安裝

安裝完成後，項目初始化、模組安裝、執行的完整流程見 [5 分鐘快速開始](../quick-start.md)。

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
[INFO] 适配器已加载: Yunhu
[INFO] 模块已加载: MyModule
[INFO] ErisPulse 初始化完成
```

## 常見問題

### 安裝失敗

1. 檢查 Python 版本是否 >= 3.10（推薦 3.10 - 3.13）
2. 嘗試使用 `uv pip install ErisPulse` 替代 `pip install`
3. 如果提示權限錯誤，嘗試 `pip install --user ErisPulse` 或使用虛擬環境
4. 如果在企業代理環境下遇到 SSL 證書錯誤，嘗試 `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. 確保網路連線正常，pip 源可訪問

### 配置錯誤

1. 檢查 `config.toml` 語法是否正確（TOML 格式對縮進和引號敏感）
2. 確認所有必需的配置項都已填寫
3. 查看終端日誌獲取詳細錯誤資訊
4. 使用 `epsdk init` 重新生成配置檔案

### 模組安裝失敗

1. 確認模組名稱拼寫正確（大小寫敏感）
2. 檢查網路連線
3. 使用 `epsdk list-remote` 查看可用模組列表
4. 確認模組與你目前 SDK 版本相容

### Windows PowerShell 執行策略

如果 PowerShell 提示「無法加載檔案...因為在此系統上禁止運行腳本」：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 下一步

- [CLI 命令參考](cli-reference.md) - 了解所有命令列命令
- [配置檔案說明](configuration.md) - 详细了解配置選項