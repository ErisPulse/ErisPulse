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

### 常用指令

| 指令 | 說明 |
|------|------|
| `epsdk init` | 初始化專案（`-q` 快速模式，`-n` 指定名稱） |
| `epsdk install <套件名>` | 安裝模組/介面卡（無參數進入互動模式） |
| `epsdk run main.py` | 執行專案（`--reload` 熱重載模式） |
| `epsdk list` | 列出已安裝的模組/介面卡 |
| `epsdk upgrade <套件名>` | 升級模組/介面卡 |
| `epsdk doctor` | 診斷環境（Python/後端/設定/PyPI 連通性） |

> 完整的指令清單和參數說明請參考 [CLI 指令參考](cli-reference.md)。

### 常見設定位置

| 設定項 | 說明 | 詳見 |
|--------|------|------|
| `[ErisPulse.server]` | 伺服器設定（主機、連接埠） | [設定檔說明](configuration.md#伺服器設定) |
| `[ErisPulse.logger]` | 日誌設定（層級、輸出檔案） | [設定檔說明](configuration.md#日誌設定) |
| `[ErisPulse.framework]` | 框架設定（延遲載入） | [設定檔說明](configuration.md#框架設定) |
| `[ErisPulse.event.command]` | 指令事件設定（前綴） | [設定檔說明](configuration.md#事件設定) |
| `[介面卡名稱]` | 各介面卡的特定設定 | [平台特性指南](../platform-guide/) |

## 相關文件

- [快速開始](../quick-start.md) - 快速入門指南
- [新手入門](../getting-started/) - 入門教程
- [開發者指南](../developer-guide/) - 開發自定義模組和適配器
- [API 參考](../api-reference/) - API 文件

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第 8 條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。