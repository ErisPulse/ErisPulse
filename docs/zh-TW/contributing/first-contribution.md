# 首次貢獻實戰

> 第一次提交 PR 難免會有些不確定，這很正常。這篇教程把整個過程拆成了幾個小步驟，跟著走就行。中間遇到任何問題都可以在 Issue 或 Discussions 裡問——沒有人會因為你的問題「太基礎」而說什麼，大家更在意的是你在往前走。

本文用「補一個 i18n 翻譯鍵」當例子，因為它修改最小、最容易跑通。不過同樣的流程，對其他類型的貢獻也適用。

## 準備工作

開始前，你需要準備：

- 一個 GitHub 帳戶
- 本地安裝好 [uv](https://docs.astral.sh/uv/)（ErisPulse 的套件管理器）
- Python 3.10+

## 1. Fork 並克隆倉庫

前往 [ErisPulse 倉庫](https://github.com/ErisPulse/ErisPulse)，點擊右上角的 **Fork** 將其複製到你的帳戶，然後克隆到本地（將「你的使用者名稱」替換為實際名稱）：

```bash
git clone -b Develop/v2 https://github.com/你的使用者名稱/ErisPulse.git
cd ErisPulse
```

添加上游地址，便於日後同步主倉庫的更新：

```bash
git remote add upstream https://github.com/ErisPulse/ErisPulse.git
```

## 2. 安裝開發環境

```bash
uv sync                       # 安裝依賴並建立 .venv
```

驗證環境是否正常：

```bash
uv run pytest -m unit -q      # 測試應全部通過
```

## 3. 建立功能分支

請始終從 `Develop/v2` 分支切出：

```bash
git checkout Develop/v2
git pull upstream Develop/v2   # 先同步最新程式碼
git checkout -b docs/add-hello-translation
```

分支名稱隨意，只要能看得出來你要做什麼即可。

## 4. 進行修改

以補充一個翻譯鍵為例，假設要新增一句 `mymodule.hello`。

規則只有一條：**新增翻譯鍵，5 種語言（zh-CN / en / zh-TW / ja / ru）要一起補**，不然其他語言的使用者會看到缺失。

打開 `src/ErisPulse/Core/i18n/locales/` 下的 5 個文件，分別添加一行：

```python
# zh_cn.py
"mymodule.hello": "你好",
# en.py
"mymodule.hello": "Hello",
# zh_tw.py
"mymodule.hello": "你好",
# ja.py
"mymodule.hello": "こんにちは",
# ru.py
"mymodule.hello": "Привет",
```

> 若這次變動涉及新的公共方法，記得為它補上文件註釋，詳見[文件註釋規範](../styleguide/docstring.md)。

## 5. 本地驗證

```bash
uv run ruff check .            # 代碼風格檢查
uv run basedpyright src/ErisPulse   # 類型檢查（修改了原始碼才需要） - 你可能會遇到幾百個 warning（不用在意忽略就可以...嘻..嘻嘻）
uv run pytest -m unit -q       # 執行測試
```

只要這三條都通過即可。類型檢查中那些 `reportAny` / `Unknown*` 警告屬於「類型系統仍在逐步完善中」，不會阻礙合併。

> 如果修改了核心模組（Bases / runtime / config / loaders），建議順手補上對應的測試用例，方便後續維護。

## 6. 更新 CHANGELOG

開啟 `CHANGELOG.md`，找到最上方仍在開發的版本，在適當的分類下新增一筆記錄：

```markdown
### 優化

- `Core/i18n/locales` 补充 `mymodule.hello` 翻譯鍵（zh-CN / en / zh-TW / ja / ru）
```

## 7. 提交並推送

```bash
git add .
git commit -m "i18n: add mymodule.hello translation"
git push origin docs/add-hello-translation
```

## 8. 提交 Pull Request

推送之後，GitHub 會提示 **Compare & pull request**，點進去：

1. 確認目標分支是 **`Develop/v2`**（別選成 `main`）
2. 勾選變更類型，簡單寫寫你改了什麼
3. 提交，等維護者審查

審查提出意見很正常，不代表你做得不好——按建議改完再 push 一次就行。通過之後，你的變更就正式進 `Develop/v2`，下個版本就能用上。

## 貢獻模組或適配器

模組和適配器是具有完整結構的小型套件，使用腳手架工具起步最為方便：

```bash
epsdk create    # 選擇 module 或 adapter
```

生成完之後，照著這些文件往下做即可：

- [模組開發入門](../developer-guide/modules/getting-started.md)
- [適配器開發入門](../developer-guide/adapters/getting-started.md)
- [發布到 PyPI 與模組商店](../developer-guide/publishing.md)

> 建議開發前先在 [Issues](https://github.com/ErisPulse/ErisPulse/issues) 裡用「新適配器或模組」模板說明你的計畫，維護者能協助你對接標準、避開一些常見的坑。

模組和適配器通常是獨立倉庫，不必塞進主倉庫。`examples/example-module/` 和 `examples/example-adapter/` 是給你參考的範例。

## 可能會遇到的問題

**PR 提了多久會有人看？**  
一般幾天內。維護者會留下 review 意見，你按需調整後再 push 一次就好。

**程式碼檢查報錯了？**  
先試 `uv run ruff check . --fix`，能自動修掉一大半。

**跟主倉庫衝突了？**  
`git pull upstream Develop/v2`，解決衝突再 push。

**能直接提到 `main` 嗎？**  
不行，所有更改都走 `Develop/v2`，再由維護者統一發布到 `main`。