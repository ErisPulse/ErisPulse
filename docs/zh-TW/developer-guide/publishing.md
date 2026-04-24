# 發布與模組商店指南

將你開發的模組或適配器發布到 ErisPulse 模組商店，讓其他用戶可以方便地發現和安裝。

## 模組商店概述

ErisPulse 模組商店是一個集中式的模組註冊表，用戶可以透過 CLI 工具瀏覽、搜尋和安裝社群貢獻的模組、適配器。

### 瀏覽與發現

```bash
# 列出遠端可用的所有套件
epsdk list-remote

# 只查看模組
epsdk list-remote -t modules

# 只查看適配器
epsdk list-remote -t adapters

# 強制刷新遠端套件列表
epsdk list-remote -r
```

你也可以訪問 [ErisPulse 官網](https://www.erisdev.com/#market) 在線瀏覽模組商店。

### 支援的提交類型

| 類型 | 說明 | Entry-point 組 |
|------|------|----------------|
| 模組 (Module) | 擴展機器人功能、實現業務邏輯 | `erispulse.module` |
| 適配器 (Adapter) | 連接新的訊息平台 | `erispulse.adapter` |

## 發布流程

整個發布流程分為四個步驟：準備專案 → 發布到 PyPI → 提交到模組商店 → 審核上線。

### 步驟 1: 準備專案

確保你的專案包含以下檔案：

```
MyModule/
├── pyproject.toml      # 專案配置（必須）
├── README.md           # 專案說明（必須）
├── LICENSE             # 開源許可證（推薦）
└── MyModule/
    ├── __init__.py     # 套件入口
    └── ...
```

### 步驟 2: 配置 pyproject.toml

根據你要發布的類型，正確配置 `entry-points`：

#### 模組

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "模組功能描述"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### 適配器

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "適配器功能描述"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **注意**：套件名稱建議以 `ErisPulse-` 開頭，便於用戶識別。Entry-point 的鍵名（如 `"MyModule"`）將作為模組在 SDK 中的存取名稱。

### 步驟 3: 發布到 PyPI

```bash
# 安裝建構工具
pip install build twine

# 建構分發套件
python -m build

# 發布到 PyPI
python -m twine upload dist/*
```

發布成功後，確認你的套件可以透過 `pip install` 安裝：

```bash
pip install ErisPulse-MyModule
```

### 步驟 4: 提交到 ErisPulse 模組商店

在確認套件已發布到 PyPI 後，前往 [ErisPulse-ModuleRepo](https://github.com/ErisPulse/ErisPulse-ModuleRepo/issues/new?template=module_submission.md) 提交申請。

填寫以下資訊：

#### 提交類型

選擇你要提交的類型：
- 模組 (Module)
- 適配器 (Adapter)

#### 基本資訊

| 欄位 | 說明 | 範例 |
|------|------|------|
| **名稱** | 模組/適配器名稱 | Weather |
| **描述** | 簡短功能描述 | 天氣查詢模組，支援全球城市 |
| **作者** | 你的名字或 GitHub 用戶名 | MyName |
| **倉庫地址** | 程式碼倉庫 URL | https://github.com/MyName/MyModule |

#### 技術資訊

| 欄位 | 說明 |
|------|------|
| **最低 SDK 版本要求** | 如 `>=2.0.0`（如適用） |
| **依賴項** | 除 ErisPulse 外的額外依賴（如適用） |

#### 標籤

用逗號分隔，幫助用戶搜尋發現你的模組。例如：`天氣, 查詢, 工具`

#### 檢查清單

提交前請確認：
- 程式碼遵循 ErisPulse 開發規範
- 包含適當的文件（README.md）
- 包含測試用例（如適用）
- 已在 PyPI 發布

### 步驟 5: 審核與上線

提交後，維護者會審核你的申請。審核要點：

1. 套件可以在 PyPI 上正常安裝
2. Entry-point 配置正確，能被 SDK 正確發現
3. 功能與描述一致
4. 不存在安全問題或惡意程式碼
5. 不與已有模組嚴重衝突

審核通過後，你的模組會自動出現在模組商店中。

## 更新已發布模組

當你更新模組版本時：

1. 更新 `pyproject.toml` 中的 `version`
2. 重新建構並上傳到 PyPI：
   ```bash
   python -m build
   python -m twine upload dist/*
   ```
3. 模組商店會自動同步 PyPI 上的最新版本資訊

用戶可以透過以下命令升級：

```bash
epsdk upgrade MyModule
```

## 開發模式測試

在正式發布前，你可以使用可編輯模式在本地測試：

```bash
# 以可編輯模式安裝
epsdk install -e /path/to/MyModule

# 或使用 pip
pip install -e /path/to/MyModule
```

## 常見問題

### Q: 套件名稱必須以 `ErisPulse-` 開頭�？

不強制，但強烈推薦。這有助於用戶在 PyPI 上識別 ErisPulse 生態的套件。

### Q: 一個套件可以註冊多個模組嗎？

可以。在 `entry-points` 中配置多個鍵值對即可：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Q: 如何指定最低 SDK 版本要求？

在 `pyproject.toml` 的 `dependencies` 中設定：

```toml
dependencies = [
    "ErisPulse>=2.0.0",
]
```

模組商店會檢查版本相容性，防止用戶安裝不相容的模組。

### Q: 審核需要多長時間？

通常在 1-3 個工作日內完成。你可以在 Issue 中查看審核進度。