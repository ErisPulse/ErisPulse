# 用戶使用指南

本指南將協助您安裝、配置和管理 ErisPulse 專案。

## 內容列表

1. [安裝和配置](installation.md) - 安裝 ErisPulse 並配置專案
2. [CLI 命令參考](cli-reference.md) - 命令列工具的完整使用說明
3. [配置檔案說明](configuration.md) - 配置檔案的詳細說明

## 快速參考

### 常用命令

| 命令 | 說明 | 示例 |
|-------|------|------|
| `epsdk init` | 初始化專案 | `epsdk init -q -n my_bot` |
| `epsdk install` | 安裝模組/適配器 | `epsdk install Yunhu` |
| `epsdk run` | 執行專案 | `epsdk run main.py --reload` |
| `epsdk list` | 列出已安裝的模組 | `epsdk list -t modules` |
| `epsdk upgrade` | 升級模組 | `epsdk upgrade Yunhu` |

### 常見配置位置

| 配置項 | 說明 |
|--------|------|
| `[ErisPulse.server]` | 伺服器配置（主機、埠口） |
| `[ErisPulse.logger]` | 日誌配置（等級、輸出檔案） |
| `[ErisPulse.framework]` | 框架配置（懶加載） |
| `[ErisPulse.event.command]` | 命令事件配置（前綴） |
| `[適配器名]` | 各適配器的特定配置 |

### 專案目錄結構

```
project/
├── config/
│   └── config.toml          # 專案配置檔案
├── main.py                  # 專案進入點檔案
└── requirements.txt          # 依賴列表
```

## 開發模式

### 熱重載模式

開發時請使用熱重載模式，修改程式碼後會自動重載：

```bash
epsdk run main.py --reload
```

### 一般執行模式

生產環境中使用一般執行模式：

```bash
epsdk run main.py
```

## 常見任務

### 安裝新模組

```bash
# 從遠端倉庫安裝
epsdk install Yunhu Weather

# 從本地目錄安裝
epsdk install ./my-module

# 互動式安裝
epsdk install
```

### 查看可用模組

```bash
# 列出所有模組
epsdk list

# 只列出適配器
epsdk list -t adapters

# 只列出模組
epsdk list -t modules

# 列出遠端可用模組
epsdk list-remote
```

### 升級模組

```bash
# 升級指定模組
epsdk upgrade Yunhu

# 升級所有模組
epsdk upgrade
```

### 解除安裝模組

```bash
# 解除安裝指定模組
epsdk uninstall Yunhu

# 解除安裝多個模組
epsdk uninstall Yunhu Weather
```

## 相關文件

- [快速開始](../quick-start.md) - 快速入門指南
- [新手入門](../getting-started/) - 入門教學
- [開發者指南](../developer-guide/) - 開發自定義模組和適配器
- [API 參考](../api-reference/) - API 文件