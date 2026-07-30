# 為 ErisPulse 貢獻

> **寫給第一次貢獻的你**
> 開源項目從來不是靠一兩個核心開發者的「大動作」撐起來的，更多時候，是無數個細微的變動在累積——一個錯別字、一句翻譯、一個小 Bug 的修復，都在讓 ErisPulse 往前走一點。所以不必去衡量自己的貢獻「夠不夠分量」，只要你願意提交 PR，就已經是這件事的一部分。

## 你可以參與的方式

貢獻不只是寫核心程式碼。下面這些事，都在讓 ErisPulse 變得更好：

- **完善文件** —— 修正錯別字、理順拗口的描述、補充自己踩過的坑。門檻最低，隨時可以開始。
- **補充翻譯** —— 框架支援 5 種語言（zh-CN / en / zh-TW / ja / ru），翻譯遺漏或不準確的地方，都歡迎來補。
- **修復 Bug** —— 在 [Issues](https://github.com/ErisPulse/ErisPulse/issues) 裡挑一個你熟悉的問題，重現並修掉它。
- **編寫範例** —— 把你的使用經驗整理成範例程式碼，留給後來的人參考。
- **開發模組 / 適配器** —— 為框架接入新的平台或能力。難度高一些，但也更有成就感。

> 如果不確定從哪開始，可以在 [Discussions](https://github.com/ErisPulse/ErisPulse/discussions) 裡說一聲，維護者會幫你找到合適的方向。

## 第一次提交 PR

如果你還沒有提交過 PR，建議先閱讀 [首次貢獻實戰](first-contribution.md)。其中涵蓋了從 fork 倉庫到合併 PR 的完整流程，遇到問題可在 Issue 或 Discussions 中提出。

## 開發環境

完整的開發規範見根目錄 [CONTRIBUTING.md](../../../CONTRIBUTING.md)。快速上手：

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
uv sync                       # 同步開發環境
uv run pytest -m unit         # 運行單元測試
uv run ruff check .           # 程式碼檢查
```

## 提交流程

簡單來說就是：fork 倉庫 → 基於 `Develop/v2` 建分支 → 改完跑通測試 → 提 PR 到 `Develop/v2`。

幾個要注意的點：

- PR 提到 **`Develop/v2`** 分支，別直接動 `main` 或 `Pre-Release/v2`
- 提交前確認 `pytest` / `ruff` / `basedpyright` 都過得去（類型檢查裡那些 `reportAny` / `Unknown*` 警告屬於「類型還在逐步完善」，不會卡合併）
- 改了功能就在 `CHANGELOG.md` 裡留筆
- 給公共 API 加了方法，記得補文件註解（[規範在這裡](../styleguide/docstring.md)）

## 貢獻模組或適配器

如果你打算做新的模組或適配器，建議先在 [Issues](https://github.com/ErisPulse/ErisPulse/issues) 裡用「新適配器或模組」模板簡單說一句你的想法。不用寫得很完整，說明意圖就行——維護者會幫你理清思路、對接好開發標準，讓後面順一些。

使用腳手架工具可以快速起步：

```bash
epsdk create    # 選擇 module 或 adapter，產生完整專案結構
```

隨後參考 [模組開發入門](../developer-guide/modules/getting-started.md) 或 [適配器開發入門](../developer-guide/adapters/getting-started.md)，完成後還可[發布到 PyPI 與模組商店](../developer-guide/publishing.md)。

> 模組和適配器通常是獨立倉庫，不必並入主倉庫。`examples/` 下的範例專案可供參考。

## 獲取幫助

- [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) —— 報告問題、提出需求
- [GitHub Discussions](https://github.com/ErisPulse/ErisPulse/discussions) —— 討論思路、提出疑問
- 郵件：`erisdev@88.com`