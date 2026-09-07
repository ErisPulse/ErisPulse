# 生態模組

ErisPulse 框架本身只提供核心能力（事件系統、模組系統、配置、路由、日誌等），**不內建** GUI、圖片渲染、可視化等「重型」功能。這些能力由社群維護的 **第三方模組** 提供，按需安裝即可。

> [!IMPORTANT]
> 本目錄下的文件分為兩類，安裝方式不同：
>
> - **模組**（如 Dashboard / Takumi）使用 `epsdk install` 安裝：
>
>   ```bash
>   epsdk install <模組名>
>   ```
>
> - **獨立程式**（如 ErisPulse-App 客戶端）直接從對應的 GitHub Releases 下載安裝，無需 `epsdk`。
>

---

## 推薦模組與官方客戶端

| 項目 | 類型 | 用途 | 文件 |
|------|------|------|------|
| [ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) | 官方客戶端 | 官方全平台客戶端（Android / Windows / Linux / macOS）：原生介面建立 / 運行 / 管理多個實例，內建模組商店與事件建構器；**手機直接運行**，桌面托盤常駐 | [ErisPulse-App 安裝與使用](app.md) |
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | 模組 | Web 管理面板：模組啟停、設定編輯、日誌查看、事件監控；支援其他模組向側邊欄註冊自訂視窗 | [Dashboard 使用與視窗註冊](dashboard.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)） | 模組 | 圖片渲染：HTML / 節點樹 / Jinja / SVG / 動畫，基於 [takumi-py](https://github.com/BalconyJH/takumi-py)；內建中英文字型，開箱即用 | [Takumi 圖片渲染](takumi.md) |

---

## 我也想把自己的模組列在這裡？

歡迎推薦優質的、可廣泛複用的 ErisPulse 生態模組。要求如下：

1. 已發布到 [PyPI](https://pypi.org/)，且套件名稱以 `ErisPulse-` 開頭
2. 提供基本的 README 與使用範例
3. 积极維護，對 Issue 有回應

符合以上條件的模組作者可以透過 PR 在本目錄下新增 `<模組名>.md` 文件，並在本表的「推薦模組」中新增一行。