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

### 步驟 4: 提交