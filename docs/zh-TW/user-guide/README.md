# 使用者指南

本指南將協助您安裝、設定及管理 ErisPulse 專案。

## 內容列表

| 文件 | 說明 |
|------|------|
| [安裝和設定](installation.md) | 系統需求、安裝方式 (pip/uv/Docker)、驗證安裝 |
| [ErisPulse-App 手機/桌面客戶端](../ecosystem/app.md) | 官方用戶端：手機 / 桌面直接執行、原生介面管理 ErisPulse 實例 |
| [CLI 指令參考](cli-reference.md) | `epsdk` 命令列工具的完整使用說明 |
| [設定檔說明](configuration.md) | `config/config.toml` 各配置項的詳細說明 |
| [部署指南](deployment.md) | Docker 部署、systemd 服務、SSL 設定 |

## 快速參考

### 常用命令

| 命令 | 說明 |
|------|------|
| `epsdk init` | 初始化項目（`-q` 快速模式，`-n` 指定名稱） |
| `epsdk install <包名>` | 安裝模組/適配器（不帶參數進入互動模式） |
| `epsdk config <名稱>` | 互動式配置適配器/模組的宣告式配置項 |
| `epsdk run main.py` | 運行項目（`--reload` 熱重載模式） |
| `epsdk list` | 列出已安裝的模組/適配器 |
| `epsdk upgrade <包名>` | 升級模組/適配器 |
| `epsdk doctor` | 臨床診斷環境（Python/後端/配置/PyPI 連通性） |

> 完整的命令列表和參數說明請參考 [CLI 命令參考](cli-reference.md)。

### 常見配置位置

| 配置項 | 說明 | 详见 |
|--------|------|------|
| `[ErisPulse.server]` | 伺服器配置（主機、端口） | [配置文件說明](configuration.md#伺服器配置) |
| `[ErisPulse.logger]` | 日誌配置（等級、輸出檔案） | [配置文件說明](configuration.md#日誌配置) |
| `[ErisPulse.framework]` | 框架配置（懶加載） | [配置文件說明](configuration.md#框架配置) |
| `[ErisPulse.event.command]` | 命令事件配置（前綴） | [配置文件說明](configuration.md#事件配置) |
| `[適配器名]` | 各適配器的特定配置 | [平台特性指南](../platform-guide/) |

## 相關文件

- [快速開始](../quick-start.md) - 快速入門指南
- [新手入門](../getting-started/) - 入門教程
- [開發者指南](../developer-guide/) - 開發自定義模組和適配器
- [API 參考](../api-reference/) - API 文件

