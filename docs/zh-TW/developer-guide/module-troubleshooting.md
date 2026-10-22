# 模組排查指南

> [!TIP]  
> **什麼時候需要閱讀本文**：當機器人「沒有反應」時——模組已安裝但未載入、發出指令卻無回應、事件處理器未執行、修改程式碼 reload 後仍維持舊行為、模組明明已啟用卻收不到事件——請根據症狀對應到相應的排查場景。若不需排查則可跳過，這不會影響其他功能的使用。

當模組「沒有反應」時，請根據症狀對應到相應的排查場景；前三類場景有框架內建的診斷工具可直接提供結論：

| 症狀 | 診斷工具 | 定位層面 |
|------|---------|---------|
| 模組未載入 | `ErisPulse.runtime.explain_module(name)` | 注冊與載入鏈 |
| 事件未響應 | `ErisPulse.runtime.explain_event(event)` | 分發入口檢查 |
| 命令未觸發 | 分發決策鏈（測試側 `DispatchTrace` / 框架內建 `trace`） | 命令判定鏈 |

上述兩個診斷函數均為**純讀取**操作，不會改變任何狀態，可在任何時刻調用；返回的 dict 為機器可讀取格式，搭配 `format_report()` 可渲染為人類可閱讀的文本。

## 場景一：模組未載入

```python
from ErisPulse.runtime import explain_module, format_report

report = explain_module("MyModule")
print(format_report(report))
```

`explain_module()` 會逐一檢查並提供結論，涵蓋以下原因：

| 檢查項目 | 說明 |
|-------|------|
| 未註冊 | 套件未安裝、entry-point 組名錯誤，或註冊名稱與查詢名稱不一致 |
| 慢載入未實例化 | **正常狀態而非故障**：慢載入模組首次被呼叫（`module.call` / 命令觸發等）時才實例化 |
| 配置已停用 | `ErisPulse.modules.status.<模組名> = false`（未配置即預設啟用） |
| 依賴未載入 | 模組宣告的 `depends` 列表中有模組未就緒 |
| SDK 版本不符 | 模組元數據宣告的 `min_sdk_version` 高於目前框架版本 |
| on_load 異常 | 登記正常但未載入且無上述原因——檢查啟動日誌中模組名對應的 ERROR 記錄 |

回傳 dict 的結構化欄位：`registered` / `loaded` / `lazy` / `enabled`（`None` 表示未配置即預設啟用）/ `missing_dependencies` / `sdk_version_ok` / `conclusion`（一句話結論）/ `reasons`（原因清單）。

## 場景二：事件沒響應

```python
from ErisPulse.runtime import explain_event, format_report

report = explain_event(event)   # 在處理器內拿到的 Event 或原始事件 dict
print(format_report(report))
```

`explain_event()` 按分發入口的實際檢查順序輸出結論：

1. **平台適配器未註冊**：`platform` 對應的適配器實例不存在——事件根本沒進入框架。
2. **身份維度被作用域拒絕**：用戶 / 會話 / Bot / 適配器被拉黑——事件在分發入口被完全丟棄。作用域配置見[模組配置](../user-guide/configuration.md)。
3. **模組被會話屏蔽**：區分當前會話 `available_modules`（可用）與 `blocked_modules`（被作用域屏蔽）。
4. **文本形如命令但未命中**：帶命令前綴但不是任何註冊命令——檢查前綴配置與命令名。

入口檢查全部通過仍無響應時，結論會指引繼續檢查兩處：

- **處理器過濾條件**：`detail_type` / `pattern=` / `regex=` 等條件不滿足；
- **中間件否決**：中間件顯式返回 `False` 會在事件層面丟棄，並觸發 `adapter.event.blocked` 生命週期鉤子（攜帶中間件名與完整事件）——可註冊該鉤子審計「是誰丟棄了事件」。

## 場景三：命令未觸發（分發決策鏈）

一條帶前綴的消息要真正執行命令，需依次通過：命令文本判定 → 命令命中（未命中附拼寫建議）→ 作用域 → 用戶 ACL → 主人檢查 → 權限函數 → 冷卻 / 限流 / 用量靜默丟棄 → 廢棄拒絕與提示 → 參數解析 → 執行。框架把每個判定点記錄為因果鏈，給出「為什麼沒觸發」的結論。

### 測試中：TestBot.dispatch 返回 DispatchTrace

推薦用測試復現問題後直接讀取因果鏈（工具用法見[模組測試](testing.md)）：

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict          # executed / rejected / dropped / failed / no_match / passed
print(trace.explain()) # 逐行因果說明（當前語言）
trace.assert_no_match()
```

### 框架內建 trace 模組

決策鏈由 `ErisPulse.Core.Event.trace` 提供，預設**零開銷**——未處於採集上下文時判定点直接跳過，生產路徑無感知：

```python
from ErisPulse.Core.Event import (
    start_dispatch_trace,
    format_dispatch_trace,
    final_verdict,
)

with start_dispatch_trace() as records:
    ...  # 采集上下文內發生的分發（含其派生的處理器任務）

print(format_dispatch_trace(records))   # 人類可讀因果鏈（當前語言）
print(final_verdict(records))           # 總結論
```

`final_verdict()` 的取值：

| 結論 | 含義 |
|------|------|
| `executed` | 命令已執行 |
| `rejected` | 被權限類判定拒絕（作用域 / ACL / 主人 / 權限函數） |
| `dropped` | 被靜默丟棄（冷卻 / 限流 / 用量 / 中間件否決） |
| `failed` | 執行出錯 |
| `no_match` | 帶前綴但未命中任何命令 |
| `passed` | 非命令文本，放行給訊息處理器 |

記錄為機器可讀 dict（`stage` / `verdict` / `message_key` / `params`），自定義展示時可按 `stage` 過濾（如只看 `cooldown`）。

### 治理類靜默命中的辨別

`cooldown=` / `rate_limit=` / `usage_limit=` 命中時**預設靜默丟棄**（命令仍被認領，不漏給低优先級處理器），容易誤判為「命令壞了」：現象是部分使用者可用、部分使用者無回應，且決策鏈中出現對應 `stage` 的 `dropped` 記錄。`deprecated=` 命令則表現為呼叫時自動回覆廢棄文案（`deprecated_reject=True` 時拒絕執行）。

## 場景四：改了程式碼 reload 後還是舊行為（2.11+）

請依序核對：

1. **看回傳值與失敗現場**：`reload` / `load` 回傳 `False` 時，直接呼叫
   `sdk.module.last_error("模組名")`——回傳例外與完整 traceback（含出錯行號），
   無需翻查日誌檔案；`module.get_info(名字)["last_error"]` 同源。
2. **語法錯誤不會卸載**：reload 在卸載前做語法預檢，失敗即拒絕（舊實例繼續提供服務），
   日誌會給出檔案 + 行號；修正語法後再 reload 即可。
3. **身份未變更警示**：日誌出現「重載後程式碼身份未變更」或事件 `identity_changed: false`
   時，表示進程內仍執行舊程式碼（常見於 C 擴展等無法清除的快取）——這類模組需要重啟框架。
4. **確認模組來源可重導入**：執行時註冊（`sdk.module.register()`）的模組，類定義在
   `__main__` / 入口腳本內時拒絕重導入（守衛警示）；請將類移入可導入的模組檔案。
5. **懶加載模組被強制激活**：重載會把原本懶加載的模組激活（明確日誌）；休眠
   （歸眠）中的模組保持休眠。

## 場景五：模組「明明啟用卻收不到事件」（懶加載休眠，2.11+）

宣告了 `dormant_after` 的懶加載模組在閒置超過閾值後會**自動歸眠**：運行時資源釋放、
事件處理器註銷，因此不再接收事件（`activate_on` 宣告的事件除外——事件先喚醒再轉發）。

- 確認是否歸眠：日誌中檢索「已歸眠」 / `module.sleep` 事件，或觀察
  `sdk.module.get_status_summary()` 中該模組不再是 `loaded`
- 立即喚醒：任意屬性存取（`sdk.模組名.任意屬性`）或 `await sdk.module.call(...)`
- 不希望自動歸眠：移除 `get_load_strategy()` 中的 `dormant_after` 宣告
- 狀態是否遺失：歸眠前會觸發 `on_before_unload(reason="dormant")`，若模組未實現
  該鈎子保存狀態，歸眠即遺失記憶體態（與卸載一致）——需要接續狀態請參考
  [懶加載休眠](../advanced/lazy-loading.md#懶加載休眠dormant_after)

## 通用建議

- 排查前先把日誌調到 `DEBUG` / `TRACE`（配置見[開發者指南](README.md#調試技巧)），可以看到模組載入、路由註冊、事件分發等框架內部流程；
- `explain_module` / `explain_event` 隨時可調、純讀無副作用，適合直接掛到運維命令或管理面板；
- "命令沒觸發"類問題優先寫一個 `DispatchTrace` 斷言測試復現——`assert_executed` / `assert_rejected` 等斷言失敗時會自動附上完整因果鏈。

## 問題仍未解決

- **先查已知問題**：對照 [Bug 追蹤](../bug-tracker.md)，確認是否為已記錄的問題及其避開方法；
- **提交回饋**：到 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 報告問題時，附上 `explain_module` / `explain_event` 的輸出、`DispatchTrace` 因果鏈與框架版本號，能大幅縮短定位時間；
- **討論與求助**：拿不定是不是 Bug 時，先在 [Discussions](https://github.com/ErisPulse/ErisPulse/discussions) 描述症狀與重現步驟。