# 使用者使用指南

本指南協助您安裝、設定和管理 ErisPulse 專案。

## 內容清單

| 文件 | 說明 |
|------|------|
| [安裝與設定](installation.md) | 系統需求、安裝方式（pip/uv/Docker）、驗證安裝 |
| [CLI 命令參考](cli-reference.md) | `epsdk` 命令列工具的完整使用說明 |
| [設定檔說明](configuration.md) | `config/config.toml` 各設定項目的詳細說明 |
| [部署指南](deployment.md) | Docker 部署、systemd 服務、SSL 設定 |

## 快速參考

### 常用命令

| 命令 | 說明 |
|------|------|
| `epsdk init` | 初始化專案（`-q` 快速模式，`-n` 指定名稱） |
| `epsdk install <套件名稱>` | 安裝模組/配接器（無參數則進入互動模式） |
| `epsdk run main.py` | 執行專案（`--reload` 熱重載模式） |
| `epsdk list` | 列出已安裝的模組/配接器 |
| `epsdk upgrade <套件名稱>` | 升級模組/配接器 |
| `epsdk doctor` | 診斷環境（Python/後端/設定/PyPI 連通性） |

> 完整的命令列表和參數說明請參考 [CLI 命令參考](cli-reference.md)。

### 常見設定位置

| 設定項 | 說明 | 詳見 |
|--------|------|------|
| `[ErisPulse.server]` | 伺服器設定（主機、連接埠） | [設定檔說明](configuration.md#伺服器設定) |
| `[ErisPulse.logger]` | 日誌設定（層級、輸出檔案） | [設定檔說明](configuration.md#日誌設定) |
| `[ErisPulse.framework]` | 框架設定（懶載入） | [設定檔說明](configuration.md#框架設定) |
| `[ErisPulse.event.command]` | 命令事件設定（前綴） | [設定檔說明](configuration.md#事件設定) |
| `[配接器名稱]` | 各配接器的特定設定 | [平台特性指南](../platform-guide/) |

## 相關文件

- [快速開始](../quick-start.md) - 快速入門指南
- [新手入門](../getting-started/) - 入門教學
- [開發者指南](../developer-guide/) - 開發自訂模組和配接器
- [API 參考](../api-reference/) - API 文件