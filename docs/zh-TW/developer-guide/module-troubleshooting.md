# 模組排查指南

當模組「沒有反應」時，可依症狀分為三類問題，每類皆有對應的框架診斷工具（RFC EPRFC-2026-001 方向五）：

| 症狀 | 診斷工具 | 定位層面 |
|------|---------|---------|
| 模組未載入 | `ErisPulse.runtime.explain_module(name)` | 注冊與載入鏈 |
| 事件未響應 | `ErisPulse.runtime.explain_event(event)` | 分發入口檢查 |
| 命令未觸發 | 分發決策鏈（測試端 `DispatchTrace` / 框架內建 `trace`） | 命令判定鏈 |

這兩個診斷函數皆為**純讀取**操作，不會改變任何狀態，可在任意時刻調用；返回機器可讀的 dict，搭配 `format_report()` 可渲染為人類可讀的文本。

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

## 通用建議

- 排查前先把日誌調到 `DEBUG` / `TRACE`（配置見[開發者指南](README.md#調試技巧)），可以看到模組載入、路由註冊、事件分發等框架內部流程；
- `explain_module` / `explain_event` 隨時可調、純讀無副作用，適合直接掛到運維命令或管理面板；
- "命令沒觸發"類問題優先寫一個 `DispatchTrace` 斷言測試復現——`assert_executed` / `assert_rejected` 等斷言失敗時會自動附上完整因果鏈。