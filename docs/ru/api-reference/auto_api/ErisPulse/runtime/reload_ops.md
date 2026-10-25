# `ErisPulse.runtime.reload_ops` 模块

---

## 模块概述


热重载操作协调器

reload / restart / 归眠（sleep）共享的全局互斥与 restart 风暴合并：

- **互斥**：单模块重载 / 全量重载 / 适配器重载 / 归眠全程持同一把锁。

  重载共享注册表快照单槽（``_last_module_objs``）、finder 缓存、
  ``sys.modules`` purge 与级联闭包，按模块名分锁无法保护这些共享资源；
  重载是运维触发型操作（保存文件 / 手动命令），串行化无性能代价，
  watcher 风暴下串行正是期望行为。
- **重入直通**：已持锁任务内再触发重载（如模块 ``on_unload`` 钩子内调用

  ``sdk.reload_module``）直接执行——调用方已在串行管线内，同任务内再入
  不会与其它重载并发。
- **restart 合并**：restart 进行中再收到 restart 请求时置 dirty 标记并

  立即返回（合并），持锁任务每轮结束后检查 dirty 并补跑一轮——保存
  风暴至多引起「一轮完整重载 + 一轮补跑」，绝不并发交叉。

---

## 函数列表


### `_current_task() -> 'asyncio.Task[Any] | None'`

**内部方法** 当前任务（无运行循环时为 None）

---


### `async run_reload_exclusive(fn: 'Callable[[], Awaitable[_T]]') -> _T`

在热重载全局互斥下执行 fn（重入直通）

所有重载入口（单模块 / 全量 / 适配器 / restart 内部管线）统一经本
函数进入：并发触发自动串行；已持锁任务内重入（如 ``on_unload``
钩子内再触发重载）直接执行避免自锁。

- **fn**: 待执行的无参协程工厂

**返回值** (`fn`): 的返回值

**示例**:

```python
await run_reload_exclusive(lambda: loader.reload_module("dice", m, s))
```

---


## 类列表


### `class ReloadOpsCoordinator`

**内部方法**
热重载操作的全局互斥锁与 restart 合并状态机

状态机:
```
IDLE ──restart()──► RUNNING ──完成──┬─ dirty=0 → 释放锁（IDLE）
             │restart()             └─ dirty=1 → 置0，补跑一轮（RUNNING）
             ▼
         dirty=True（记「已合并」日志）
```

``reload_module`` / ``reload_adapter`` / ``reload_all`` / ``sleep`` 不
参与 dirty 状态机——晚到的文件改动必须真正执行，不能靠「restart 已
覆盖」推断丢弃（改动可能发生在 restart 读取文件之后），它们只在锁上
排队等待。

**示例**:

```python
from ErisPulse.runtime.reload_ops import run_reload_exclusive
result = await run_reload_exclusive(lambda: loader.reload_module(...))
```


#### 方法列表


##### `is_reentrant() -> bool`

当前任务是否已持有热重载互斥锁（重入直通判定）

**返回值**: 是否重入

---


##### `is_locked() -> bool`

互斥锁是否被持有（任意任务）

**返回值**: 是否有热重载操作进行中

---


##### `mark_restart_pending() -> bool`

登记一次 restart 请求（restart() 入口调用）

**返回值**: True = 已有 restart 进行中，本次请求已合并为 dirty 补跑

    （调用方直接返回，无需自行调度）；False = 当前无 restart
    持锁（调用方需自行调度执行）

---


##### `begin_restart_section() -> None`

**内部方法**
标记当前持锁任务为 restart（进入补跑循环前调用）

---


##### `consume_restart_dirty() -> bool`

**内部方法**
消费 dirty 标记（restart 每轮结束时调用）

**返回值**: True = 期间有合并进来的 restart 请求，需补跑一轮

---


##### `async run_or_skip(fn: 'Callable[[], Awaitable[_T]]', *, timeout: float, skip_log_key: str, log_params: 'dict[str, Any] | None' = None) -> '_T | None'`

限时等待互斥锁后执行 fn；超时跳过（返回 None，调用方下轮再试）

重入（当前任务已持锁）时直接执行，不等待。

- **fn**: 待执行的无参协程工厂
- **timeout**: 等锁超时（秒）——只限锁等待，不限 fn 本身执行
- **skip_log_key**: 超时跳过的 debug 日志文案键
- **log_params**: 日志参数

**返回值** (`fn`): 的返回值；超时跳过时为 None

---

