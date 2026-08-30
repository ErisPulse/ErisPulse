# 生態模組

ErisPulse 框架本身僅提供核心能力（事件系統、模組系統、設定、路由、日誌等），**不內建** GUI、圖片渲染、視覺化等「重型」功能。這些能力由社群維護的 **第三方模組** 提供，按需安裝即可。

> [!IMPORTANT]
> 本目錄下的文件分為兩類，安裝方式不同：
>
> - **模組**（如 Dashboard / Takumi）使用 `epsdk install` 安裝：
>
>   ```bash
>   epsdk install <模組名>
>   ```
>
> - **獨立程式**（如 ErisPulse-App 用戶端）直接從對應 GitHub Releases 下載安裝，無需 `epsdk`。
>

---

## 推薦模組與官方用戶端

| 專案 | 類型 | 用途 | 文件 |
|------|------|------|------|
| [ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) | 官方用戶端 | 官方全平台用戶端（Android / Windows / Linux / macOS）：原生介面建立 / 執行 / 管理多個執行個體，內建模組商店與事件建構器；**手機直接執行**，桌面托盤常駐 | [ErisPulse-App 安裝與使用](docs/zh-TW/app.md) |
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | 模組 | Web 管理面板：模組啟停、設定編輯、日誌查看、事件監控；支援其他模組向側邊欄註冊自定義視窗 | [Dashboard 使用與視窗註冊](docs/zh-TW/dashboard.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)） | 模組 | 圖片渲染：HTML / 節點樹 / Jinja / SVG / 動畫，基於 [takumi-py](https://github.com/BalconyJH/takumi-py)；內建中英文字體，開箱即用 | [Takumi 圖片渲染](docs/zh-TW/takumi.md) |

---

## 我也想把自己的模块列在这里？

欢迎推荐优质的、可被广泛复用的 ErisPulse 生态模块。要求：

1. 已发布到 [PyPI](https://pypi.org/)，且包名以 `ErisPulse-` 开头
2. 提供基本的 README 与使用示例
3. 积极维护，对 Issue 有响应

满足以上条件的模块作者可以通过 PR 在本目录下新增 `<模块名>.md` 文档，并在本表的「推荐模块」中追加一行。

