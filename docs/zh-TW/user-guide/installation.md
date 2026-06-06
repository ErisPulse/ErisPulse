# 安裝與設定

本指南將介紹如何安裝 ErisPulse 並設定你的專案。

## 系統需求

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
# 建立專案目錄 && cd my_bot
mkdir my_bot && cd my_bot

# 安裝 Python 3.12
uv python install 3.12

# 建立虛擬環境
uv venv
```

#### 啟用虛擬環境

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

## 專案初始化

### 互動式初始化

```bash
epsdk init
```

按照提示完成：
1. 輸入專案名稱
2. 選擇日誌級別
3. 設定伺服器參數
4. 選擇適配器
5. 設定適配器參數

### 快速初始化

```bash
# 快速模式，跳過互動式設定
epsdk init -q -n my_bot
```

### 設定說明

初始化後會生成 `config/config.toml` 檔案：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[ErisPulse.framework]
enable_lazy_loading = true

```

## 模組安裝

### 從遠端倉庫安裝

```bash
# 安裝指定模組
epsdk install Yunhu

# 安裝多個模組
epsdk install Yunhu Weather
```

### 從本機安裝

```bash
# 安裝本機模組
epsdk install ./my-module
```

### 互動式安裝

```bash
# 不指定套件名進入互動式安裝
epsdk install
```

## 驗證安裝

### 檢查安裝

```bash
# 檢查 ErisPulse 版本
epsdk --version
```

### 運行測試

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
2. 尝试使用 `uv pip install ErisPulse` 替代 `pip install`
3. 如果提示权限错误，尝试 `pip install --user ErisPulse` 或使用虚拟环境
4. 如果在企业代理环境下遇到 SSL 证书错误，尝试 `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. 确保网络连接正常，pip 源可访问

### 配置错误

1. 检查 `config.toml` 语法是否正确（TOML 格式对缩进和引号敏感）
2. 确认所有必需的配置项都已填写
3. 查看终端日志获取详细错误信息
4. 使用 `epsdk init` 重新生成配置文件

### 模块安装失败

1. 确认模块名称拼写正确（大小写敏感）
2. 检查网络连接
3. 使用 `epsdk list-remote` 查看可用模块列表
4. 确认模块与你当前 SDK 版本兼容

### Windows PowerShell 执行策略

如果 PowerShell 提示"无法加载文件...因为在此系统上禁止运行脚本"：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 下一個步驟

- [CLI 命令參考](cli-reference.md) - 了解所有命令行命令
- [設定檔說明](configuration.md) - 詳細了解設定選項