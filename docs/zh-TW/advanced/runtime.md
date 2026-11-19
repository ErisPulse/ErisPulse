# runtime 工具帶

> [!TIP]
> **何時需要閱讀本文**：想一站式了解 `ErisPulse.runtime` 包提供了哪些
> 可直接 import 的運行時工具時。各能力的詳細用法在對應主題文件，本頁是
> 速查索引 + 少量無主題歸屬能力的用法說明。

`ErisPulse.runtime` 是框架的聚合導出層：把散落在各模組的運行時工具收進
單一入口，腳本、模組、適配器代碼統一 `from ErisPulse.runtime import X`
取用，不必記深層路徑。

## 能力速查表

| 類別 | 名稱 | 用途 | 詳見 |
|------|------|------|------|
| 歸屬權 | `bind_owner` | 將 owner 上下文綫程入口 | [歸屬權系統](ownership.md) |
| 歸屬權 | `owner_scope` / `get_current_owner` | 代碼塊級歸屬上下文 | [歸屬權系統](ownership.md) |
| 歸屬權 | `get_owner_tasks` / `cancel_owner_tasks` | 查詢 / 取消某 owner 的後台任務 | [歸屬權系統](ownership.md) |
| 後台任務 | `spawn_background` / `spawn_later` / `spawn_thread` | 後台協程 / 延遲任務 / 線程任務 | [生命週期管理](lifecycle.md) |
| 後台任務 | `cancel_all_background_tasks` / `run_main_loop` | 後台任務收口與主迴圈註冊 | [生命週期管理](lifecycle.md) |
| 事件上下文 | `get_current_trace_id` | 讀取當前鏈路追蹤 ID | [鏈路追蹤](interaction.md#鏈路追蹤trace-id) |
| 事件上下文 | `get_send_receipts` | 讀取消息事務的發送回執帳本 | [消息事務](interaction.md#消息事務message_tx) |
| 事件上下文 | `get_current_event_account` / `get_current_caller` / `get_handler_waits` | 事件帳戶 / 調用方 / 等待表讀取 | [互動會話系統](interaction.md) |
| 內存 | `snapshot` / `log_snapshot` | 帶 label 的 RSS + tracemalloc 快照（自動計算增量） | [內存診斷](performance.md#內存診斷) |
| 內存 | `get_rss_mb` / `get_traced_mb` | 當前進程內存讀數 | [內存診斷](performance.md#內存診斷) |
| 配置解析 | `dict_to_dataclass` | dict → 類型安全 dataclass 實例 | 請見下節 |
| 配置解析 | `dataclass_to_defaults_dict` / `dataclass_to_toml_with_comments` | dataclass → 預設值 dict / 帶 TOML 序列化 | [宣告式配置](../developer-guide/configuration.md) |
| 排障 | `explain_module` / `explain_event` / `explain_trace` | 模組 / 事件 / 消息鏈路診斷 | [啟動排查](startup.md) 與 [事件處理](../getting-started/event-handling.md) |
| 排障 | `format_diagnostic_block` / `log_diagnostic` / `extract_user_frame` | 異常診斷塊渲染與使用者幀提取 | [啟動流程](startup.md) |
| 異常兜底 | `setup_exception_handling` / `global_exception_handler` | 全域異常處理器掛載 | [啟動流程](startup.md) |
| 安全 | `redact_secret` | 日誌 / 報告中的敏感值脫敏 | [啟動流程](startup.md) |
| 指標 | `metrics` / `MetricsRegistry` | 運行指標註冊表（`/metrics` 端點資料源） | [部署指南](../user-guide/deployment.md) |

## dict_to_dataclass：dict → 類型安全物件

宣告式 dataclass 配置的「反方向」——將任意 dict（API 回應、webhook payload、使用者輸入）依照宣告解析成類型安全的實例，取代手寫 `data.get("x", default)` 鏈：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime import dict_to_dataclass

@dataclass
class WebhookPayload:
    order_id: str
    amount: float = 0.0
    tags: list = field(default_factory=list)
    remark: str = ""

payload = dict_to_dataclass(WebhookPayload, {
    "order_id": "A-1024",
    "amount": "99.5",          # str → float 自動轉換
    "unknown_key": "忽略",      # 未宣告欄位自動忽略
})
payload.amount                   # 99.5（float）
```

- 類型轉換（str → int/float 等）、預設值填充、巢狀 dataclass 的遞迴填充
- 環境變數覆蓋：欄位 `metadata={"env": "NAME"}` 時，優先順序為 環境變數 > 數據 > 預設值
- 宣告式配置類（`ConfigClass` / `BaseConfig`）的熱更新回調內部即由它完成 dict → 配置物件的轉換

## 相關文件

- [宣告式設定](../developer-guide/configuration.md) - ConfigClass / BaseConfig 宣告式設定
- [歸屬權（owner）系統](ownership.md) - 資源歸屬與自動回收
- [生命週期管理](lifecycle.md) - 後台任務與主迴圈