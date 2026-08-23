# ErisPulse-App

[ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) 是由 ErisDev 直接維護的 **官方多端用戶端**（Android / Windows / Linux / macOS 均已發布），
提供完全原生的圖形化管理介面：在手機或電腦上建立、執行、管理多個機器人實例，
無需終端機，也無需單獨安裝 Python 環境。

> [!IMPORTANT]
> ErisPulse-App 是**獨立安裝的用戶端程式**，不是 `epsdk install` 安裝的模組。
> 它內建了 Python 執行時環境與 ErisPulse SDK，安裝即用——**手機上也能直接執行**。

请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。

再次提醒：如果文档包含语言切换行（各语言名称用 `` | `` 分隔的行），务必严格遵守上方第8条的格式要求，不要写出 ``[**Label**](file)`` 这类错误格式。

## 功能速覽

- **多實例管理**：建立 / 啟動 / 停止 / 刪除多個實例，連接埠與存取權杖自動分配，支援全新環境或克隆既有環境
- **概覽儀表板**：適配器 / 模組 / 在線機器人 / 事件總數統計，CPU / 記憶體佔用告警變色
- **模組商店**：搜尋與標籤篩選、一鍵安裝 / 升級 / 解除安裝、指定版本安裝、pip 映像源與 Git 套件支援
- **事件流 + 事件構建器**：即時事件查看，視覺化建構測試事件並提交至適配器
- **監控**：日誌 / 生命週期 / 審計三合一檢視
- **指令管理**：前置字串與別名等全域設定、啟停與平台黑白名單
- **機器人總覽 / 設定 / 檔案管理**：原生介面直接操作實例
- **背景常駐**：Android 前台服務保活；Windows 最小化至系統匣，關閉視窗不中斷實例
- **模組動態視窗**：模組註冊的頁面自動出現在側邊導覽（與 Dashboard 同分組），點擊直接導向

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 支援平台

所有平台的安裝程式均可從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下載，按需選擇即可：

| 平台 | 安裝程式 | 說明 |
|------|--------|------|
| Android | `online-*.apk` / `offline-*.apk` | **手機直接執行**，無需電腦 |
| Windows | `windows-x64-setup.exe` / `windows-x64.zip` | 安裝版 / 免安裝版 |
| Linux | `linux-x64.tar.gz` | 解壓即用 |
| macOS | `macos-arm64.zip` | Apple Silicon（arm64） |

一個 Flutter 程式庫涵蓋所有平台。

## 安裝方式（Android / 手機直接執行）

從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下載 APK 安裝即可，有兩種建構：

| 建構 | 執行時映像 | 適用場景 |
|------|-----------|---------|
| `erispulse-app-online-*.apk` | 首次啟動時下載 | 安裝檔更小，適合網路良好 |
| `erispulse-app-offline-*.apk` | 已打包進 APK | 離線自包含，安裝後無需上網 |

兩種建構安裝步驟相同：

1. 下載並安裝 APK，啟動時允許通知權限（用於保持後台服務存活）
2. 首頁出現初始化橫幅後點擊執行首次初始化（含進度與日誌檢視）
3. 建立一個實例並啟動
4. 在 App 內建的管理介面設定配接器與模型 API Key

> 離線包自包含——安裝後無需網路。如果首次啟動下載慢或不穩定，
> 可在設定頁將下載來源切換為映像（ghfast / gh-proxy）。

### 安裝方式（桌面端：Windows / Linux / macOS）

1. 從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下載對應平台安裝包
   （Windows `setup.exe` 或免安裝 `zip`、Linux `tar.gz`、macOS `zip`）
2. 安裝並啟動
3. 在歡迎頁選擇要安裝的 ErisPulse SDK 版本（預設最新）並安裝
4. 建立實例並啟動

---

## 運作原理

```
┌────────────────────────────────────────────────────┐
│  ErisPulse-App (Flutter)                            │
│                                                    │
│  原生 UI ── Dashboard REST / WS API                │
│       │                                            │
│       ├── Android：前台服務 + proot + Ubuntu rootfs│
│       │        + Python + ErisPulse 實例           │
│       └── 桌面端：內建 Python + 直接進程管理         │
└────────────────────────────────────────────────────┘
```

- **Android**：實例運行在前台服務（background isolate）托管的 proot（使用者態 chroot）內，UI 關閉後機器人仍持續運行，崩潰自動重啟
- **桌面端**：實例作為 App 的直接子進程運行；Windows 支援最小化到系統匣背景常駐（關閉視窗不中斷實例），App 重啟後自動恢復對仍在運行實例的管理，退出時統一停止全部實例
- 所有平台的原生 UI 都透過 `127.0.0.1:<port>/Dashboard/*` 的 REST / WebSocket API 與實例通訊，與 [ErisPulse-Dashboard](dashboard.md) 共用同一套 API

---

## 與 SDK 的關係

- App 內建 ErisPulse SDK：Android 端打包在 Ubuntu 映像中，桌面端從 PyPI 安裝
  （歡迎頁可選版本，預設最新）
- App 中的執行個體與命令列 `epsdk` 建立的執行個體等價，可使用相同的模組 / 適配器
- 模組開發者可透過 [儀表板視窗註冊 API](docs/zh-TW/dashboard.md) 註冊自訂頁面：
  視窗會自動出現在 App 側邊導航（分組與儀表板一致），點擊跳轉對應頁面渲染

---

請直接傳回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 相關連結

- GitHub 儲存庫：[https://github.com/ErisPulse/ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App)
- 下載：[GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases)
- 討論：[Discussions](https://github.com/ErisPulse/ErisPulse-App/discussions)