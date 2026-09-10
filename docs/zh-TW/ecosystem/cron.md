# ErisPulse-Cron

[ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) 是 ErisPulse 生態的**定時任務調度模組**，為其他模組提供統一的定時任務 API：支援一次性定時、間隔循環、Cron 表達式三種任務類型，回呼傳參，SQLite 持久化（重啟不丟任務）。

> [!IMPORTANT]
> Cron **不是** ErisPulse 框架的內建功能，需要單獨安裝：
>
> ```bash
> epsdk install Cron
> ```

安裝後透過 `sdk.Cron` 訪問全部接口。

## 功能速覽

- **三種定時類型**：一次性（`once`）、間隔循環（`interval`）、Cron 表達式（`cron`）
- **回調傳參**：建立時傳入 `callback_data`，觸發時原樣返回，方便識別任務來源
- **持久化**：任務儲存在 SQLite（經 `sdk.storage`），框架重啟後自動恢復
- **錯過策略**：立即觸發 / 跳過 / 重新排程，可按任務選擇
- **任務管理**：暫停、恢復、取消、手動觸發、清理過期任務
- **Dashboard 集成**：已安裝 [ErisPulse-Dashboard](dashboard.md) 時自動註冊管理視窗

## 快速開始

```python
from ErisPulse import sdk

# 1. 註冊回調處理器
@sdk.Cron.on_trigger
async def handle_trigger(info):
    data = info["callback_data"]
    print(f"任務觸發: {info['task_id']}, 數據: {data}")

# 2. 創建定時任務
task_id = sdk.Cron.once(
    delay=60,
    callback_data={"type": "reminder", "msg": "該喝水了"},
)
```

---

## API 概覽

### 創建任務

```python
# 一次性：延遲 600 秒觸發
sdk.Cron.once(delay=600, callback_data={"order_id": "123"}, label="訂單超時提醒")

# 間隔循環：每 300 秒觸發，最多 100 次
sdk.Cron.interval(interval_seconds=300, callback_data={"monitor": "server-1"}, max_runs=100)

# Cron 表達式：工作日每天 9:30
sdk.Cron.cron(expression="30 9 * * 1-5", callback_data={"type": "daily_report"})

# 通用可選參數：trigger_at（絕對時間戳）、delay（首次延遲）、timezone、
# max_runs（0=無限）、label、source（創建者模組名）、missed_policy（錯過策略）
```

常用 Cron 表達式：`*/5 * * * *`（每 5 分鐘）、`0 8 * * *`（每天早 8 點）、`30 9 * * 1-5`（工作日 9:30）、`0 0 1 * *`（每月 1 號）。

### 回調

```python
@sdk.Cron.on_trigger
async def my_handler(info):
    # info 含 task_id / task_type / callback_data / label / source /
    # run_count / max_runs / created_at / last_run / trigger_time
    ...
```

支援註冊多個 handler，全部依次調用，單個 handler 異常不會影響其他 handler。

### 管理任務

```python
sdk.Cron.cancel(task_id)                  # 取消
sdk.Cron.pause(task_id)                   # 暫停
sdk.Cron.resume(task_id)                  # 恢復（reschedule=True 重新計算下次觸發）
await sdk.Cron.trigger_now(task_id)       # 手動立即觸發（不影響原計劃）
sdk.Cron.get_task(task_id)                # 查看單個任務
sdk.Cron.list_tasks(source="MyModule")    # 列出任務（支援 source/status/task_type 過濾）
sdk.Cron.delete_task(task_id)             # 刪除任務記錄
sdk.Cron.cleanup()                        # 清理 7 天前的已完成/已取消任務
```

### 錯過策略（missed_policy）

框架重啟後，對於錯過觸發時間的任務：

| 策略 | 行為 |
|------|------|
| `fire_immediately` | 立即觸發（預設） |
| `skip` | 跳過本次，等下次 |
| `reschedule` | 從當前時間重新計算下次觸發 |

## 模組卸載時的行為

Cron 的任務資料是**持久化資產**：任務創建方模組被卸載或停用不會刪除已建立的任務。但該模組註冊的回呼句柄會被清除——基於歸屬權系統的[外部清理鉤子](../advanced/ownership.md#工具模組指南托管其它模組的句柄)，Cron 在替其他模組托管回呼時會自動記名，當對方模組被卸載/停用時會自動拋棄其回呼句柄，確保對方模組實例可以被正常回收。

- 任務創建方**重新載入**後重新 `on_trigger` 即恢復接收觸發
- 不再需要的任務可用 `sdk.Cron.cancel(task_id)` / `delete_task(task_id)` 清理

## 相關連結

- [GitHub 倉庫](https://github.com/wsu2059q/ErisPulse-Cron)
- [PyPI 頁面](https://pypi.org/project/ErisPulse-Cron/)
- [歸屬權（owner）系統](../advanced/ownership.md)