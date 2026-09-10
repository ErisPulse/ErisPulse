# ErisPulse-Cron

[ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) 是 ErisPulse 生态的**定时任务调度模块**，为其他模块提供统一的定时任务 API：支持一次性定时、间隔循环、Cron 表达式三种任务类型，回调传参，SQLite 持久化（重启不丢任务）。

> [!IMPORTANT]
> Cron **不是** ErisPulse 框架的内置功能，需要单独安装：
>
> ```bash
> epsdk install Cron
> ```

安装后通过 `sdk.Cron` 访问全部接口。

---

## 功能速览

- **三种定时类型**：一次性（`once`）、间隔循环（`interval`）、Cron 表达式（`cron`）
- **回调传参**：创建时传入 `callback_data`，触发时原样返回，方便识别任务来源
- **持久化**：任务存储在 SQLite（经 `sdk.storage`），框架重启后自动恢复
- **错过策略**：立即触发 / 跳过 / 重新调度，可按任务选择
- **任务管理**：暂停、恢复、取消、手动触发、清理过期任务
- **Dashboard 集成**：已安装 [ErisPulse-Dashboard](dashboard.md) 时自动注册管理视窗

---

## 快速开始

```python
from ErisPulse import sdk

# 1. 注册回调处理器
@sdk.Cron.on_trigger
async def handle_trigger(info):
    data = info["callback_data"]
    print(f"任务触发: {info['task_id']}, 数据: {data}")

# 2. 创建定时任务
task_id = sdk.Cron.once(
    delay=60,
    callback_data={"type": "reminder", "msg": "该喝水了"},
)
```

---

## API 概览

### 创建任务

```python
# 一次性：延迟 600 秒触发
sdk.Cron.once(delay=600, callback_data={"order_id": "123"}, label="订单超时提醒")

# 间隔循环：每 300 秒触发，最多 100 次
sdk.Cron.interval(interval_seconds=300, callback_data={"monitor": "server-1"}, max_runs=100)

# Cron 表达式：工作日每天 9:30
sdk.Cron.cron(expression="30 9 * * 1-5", callback_data={"type": "daily_report"})

# 通用可选参数：trigger_at（绝对时间戳）、delay（首次延迟）、timezone、
# max_runs（0=无限）、label、source（创建者模块名）、missed_policy（错过策略）
```

常用 Cron 表达式：`*/5 * * * *`（每 5 分钟）、`0 8 * * *`（每天早 8 点）、`30 9 * * 1-5`（工作日 9:30）、`0 0 1 * *`（每月 1 号）。

### 回调

```python
@sdk.Cron.on_trigger
async def my_handler(info):
    # info 含 task_id / task_type / callback_data / label / source /
    # run_count / max_runs / created_at / last_run / trigger_time
    ...
```

支持注册多个 handler，全部依次调用，单个 handler 异常不影响其他 handler。

### 管理任务

```python
sdk.Cron.cancel(task_id)                  # 取消
sdk.Cron.pause(task_id)                   # 暂停
sdk.Cron.resume(task_id)                  # 恢复（reschedule=True 重新计算下次触发）
await sdk.Cron.trigger_now(task_id)       # 手动立即触发（不影响原计划）
sdk.Cron.get_task(task_id)                # 查看单个任务
sdk.Cron.list_tasks(source="MyModule")    # 列出任务（支持 source/status/task_type 过滤）
sdk.Cron.delete_task(task_id)             # 删除任务记录
sdk.Cron.cleanup()                        # 清理 7 天前的已完成/已取消任务
```

### 错过策略（missed_policy）

框架重启后，对于错过触发时间的任务：

| 策略 | 行为 |
|------|------|
| `fire_immediately` | 立即触发（默认） |
| `skip` | 跳过本次，等下次 |
| `reschedule` | 从当前时间重新计算下次触发 |

---

## 模块卸载时的行为

Cron 的任务数据是**持久化资产**：任务创建方模块被卸载或禁用不会删除已创建的任务。但该模块注册的回调句柄会被清理——基于归属权系统的[外部清理钩子](../advanced/ownership.md#工具模块指南托管其它模块的句柄)，Cron 在替其他模块托管回调时会自动记名，对方模块被卸载/禁用时自动抛弃其回调句柄，保证对方模块实例可以被正常回收。

- 任务创建方**重载**后重新 `on_trigger` 即恢复接收触发
- 不再需要的任务可用 `sdk.Cron.cancel(task_id)` / `delete_task(task_id)` 清理

---

## 相关链接

- [GitHub 仓库](https://github.com/wsu2059q/ErisPulse-Cron)
- [PyPI 页面](https://pypi.org/project/ErisPulse-Cron/)
- [归属权（owner）系统](../advanced/ownership.md)
