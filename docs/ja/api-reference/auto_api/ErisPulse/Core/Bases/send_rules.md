# `ErisPulse.Core.Bases.send_rules` 模块

---

## 模块概述


SendDSL 发送规则系统

为 SendDSL 提供统一的发送规则装饰器（超时/重试/回调/延迟/优先级/进度上下文）。

规则通过链式方法附加到 SendDSL 实例（存储于 ``_rules`` 字典），
最终在发送方法返回 Task 时，由 :func:`apply_send_rules` 统一应用。

设计目标：
1. 对现有适配器零侵入 —— 适配器只需返回 ``asyncio.Task``，规则由框架统一处理
2. 无规则时完全保持原有行为（向后兼容）
3. 规则可叠加、可乱序、可跨 To/Using/Account 传播

> **提示**
> 1. 规则方法（Hook/Retry/Timeout 等）返回 self，必须在发送方法（Text/Image 等）之前调用
> 2. 规则随 To/Using/Account 创建的新实例传播，避免链式调用中规则丢失
> 3. SendContext 在规则执行过程中实时更新，供 OnProgress/OnError 回调读取

---

## 函数列表


### `_is_success(result: Any)`

判断发送结果是否为成功

约定：标准响应 dict 中 ``status == "ok"`` 视为成功；
非 dict 结果（无法判断）默认视为成功，避免误触发重试。

- **result** (`发送方法的返回值`): **返回值**: 是否成功

---


### `async _invoke_callback(callback: Any, ctx: Any)`

安全调用用户回调（兼容同步/异步），异常被吞掉不影响主流程

- **callback** (`用户回调（同步函数或协程函数）`): - **ctx**: 上下文对象（SendContext 或 BatchContext）

---


### `apply_send_rules(base_task_factory: Any)`

根据 ``_rules`` 包装一次发送，返回统一处理后的 Task

该函数：
1. 构建 SendContext
2. 处理延迟（Defer）
3. 处理优先级丢弃（Priority）
4. 在重试循环中执行 ``base_task_factory``（每次重试重新调用工厂获取新 Task）
5. 应用超时（Timeout）
6. 触发 OnProgress / OnError / Hook 回调

- **base_task_factory** (`无参可调用对象，每次调用返回一个新的`): ``asyncio.Task``
    （重试时需要重新发起，因此用工厂而非固定 Task）
- **rules** (`SendDSL`): 的 ``_rules`` 字典
- **send_ctx** (`基础发送上下文（platform/method/target_type/target_id/bot_id）`): **返回值** (`统一包装后的`): ``asyncio.Task``

---


## 类列表


### `class SendContext`

发送任务的实时执行上下文

在发送过程中持续更新，并传递给 OnProgress / OnError 回调，
便于业务层监控发送阶段、重试次数、耗时及介入决策。

:ivar task_id: 任务唯一标识（自动生成的短 ID）
:ivar platform: 平台标识
:ivar method: 发送方法名（如 ``Text``、``Raw_ob12``）
:ivar target_type: 目标类型（如 ``user``、``group``）
:ivar target_id: 目标 ID
:ivar bot_id: 发送账号 ID
:ivar stage: 当前阶段：
    ``"pending"``（排队中）、``"sending"``（发送中）、
    ``"retrying"``（重试中）、``"success"``（成功）、
    ``"failed"``（失败）、``"timeout"``（超时）、
    ``"cancelled"``（取消）、``"dropped"``（被优先级丢弃）
:ivar attempt: 当前尝试次数（0 表示首次，N 表示第 N+1 次重试）
:ivar max_attempts: 最大尝试次数（含首次）
:ivar started_at: 任务开始时间戳（``time.monotonic()``）
:ivar finished_at: 任务结束时间戳（``time.monotonic()``），未结束时为 None
:ivar error: 失败/超时/取消时的异常对象，成功时为 None
:ivar result: 成功时的发送结果
:ivar extra: 预留扩展字段


#### 方法列表


##### `elapsed()`

已耗时（秒）

**返回值** (`从`): started_at 到当前时间（若已结束则为 finished_at）的秒数

---


##### `to_dict()`

转为可序列化字典（用于日志/上报）

**返回值** (`包含上下文字段的字典，error`): 字段被转为字符串

---


### `class _PriorityQueue`

优先级丢弃的轻量级并发跟踪器（进程内、非持久化）

通过统计当前在途发送任务数量判断是否"积压"。
当 ``drop_if_busy`` 启用且在途任务超过阈值时，新消息直接放弃。

阈值可通过 ``rules["priority_threshold"]`` 配置（默认 64）。


#### 方法列表


##### `is_busy()`

判断当前是否处于积压状态

---


##### `enter(task_id: str)`

登记一个在途发送任务

---


##### `leave(task_id: str)`

注销一个在途发送任务

---


##### `set_threshold(threshold: int)`

设置积压阈值

---


##### `reset()`

重置状态（主要用于测试）

---

