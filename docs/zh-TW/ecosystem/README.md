# 生態模組

ErisPulse 框架本身僅提供核心能力（事件系統、模組系統、配置、路由、日誌等），**不內建** GUI、圖片渲染、視覺化等「重型」功能。這些能力由社群維護的 **第三方模組** 提供，按需安裝即可。

> [!IMPORTANT]
> 本目錄下所有文件描述的模組 **都需要單獨安裝**，不是 ErisPulse 框架自帶的：
>
> ```bash
> epsdk install <模組名>
> ```

---

## 推薦模組

| 模組 | 用途 | 文件 |
|------|------|------|
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | Web 管理面板：模組啟停、配置編輯、日誌查看、事件監控；支援其他模組向側邊欄註冊自定義視窗 | [Dashboard 使用與視窗註冊](dashboard.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)） | 圖片渲染：HTML / 節點樹 / Jinja / SVG / 動畫，基於 [takumi-py](https://github.com/BalconyJH/takumi-py)；內建中英文字體，開箱即用 | [Takumi 圖片渲染](takumi.md) |

---

## 我也想把自己的模組列在這裡？

歡迎推薦優質的、可被廣泛複用的 ErisPulse 生態模組。要求：

1. 已發布到 [PyPI](https://pypi.org/)，且包名以 `ErisPulse-` 開頭
2. 提供基本的 README 與使用範例
3. 積極維護，對 Issue 有回應

滿足以上條件的模組作者可以通過 PR 在本目錄下新增 `<模組名>.md` 文件，並在本表的「推薦模組」中追加一行。