# `ErisPulse.runtime.proactive_gc` 模块

---

## 模块概述


ErisPulse 主动 GC 周期任务

SDK 主动垃圾回收后台任务的实现：周期性 Python GC 与内部资源回收（离线 Bot 清理）、
框架配置读取与钳制、配置热更新即时重启联动、事件洪峰门控。
由 ``ErisPulse.SDK`` 的同名私有方法薄委托调用；SDK 上保留方法形态，
以便测试与子类按 ``patch.object(SDK, "_start_proactive_gc")`` 方式补丁。

---

## 函数列表


### `start_proactive_gc(sdk: SDK)`

> **内部方法**
启动主动 GC 后台任务

定期执行 Python GC 和内部资源回收（离线 Bot 清理等），
防止长期运行时的内存增长。

GC 行为由多项框架配置控制（均支持热更新，变更时即时重启任务）：

- ``proactive_gc_interval``: 回收间隔秒数（0 禁用）
- ``proactive_gc_generation``: 常规轮次回收分代（0/1/2，钳制到 0..2）
- ``proactive_gc_full_every``: 每 N 轮做一次全量回收（0 禁用）
- ``proactive_gc_memory_growth_mb``: 全量回收的内存增长门限（0 不设限）
- ``proactive_gc_idle_only``: 事件洪峰时跳过 Python GC（避免停顿竞争）
- ``proactive_gc_gen0_min``: gen0 垃圾量下限，低于则跳过回收（空转轮次零开销）

初始化阶段已调用 ``gc.freeze()`` 将框架对象移入永久代，
此处 ``gc.collect()`` 仅扫描运行期新建对象。

---


### `stop_proactive_gc(sdk: SDK)`

> **内部方法**
停止主动 GC 后台任务，并反注册配置变更钩子

---


### `read_gc_config()`

> **内部方法**
读取并钳制主动 GC 相关框架配置

**返回值** (```(interval,`): generation, full_every, growth_mb, idle_only, gen0_min)``
         元组，值均已钳制到合法范围；``interval`` 为秒（支持小数）

---


### `on_gc_config_event(sdk: SDK, _data: dict)`

> **内部方法**
``config.set`` / ``config.updated`` 回调：proactive_gc_* 配置变化时重启 GC 任务

相比旧实现"每轮重读"，此钩子使配置变更（含 0→N 重新启用）即时生效。
从后台线程（如 config watcher）触发时，调度回主事件循环再重启。

---


### `has_handler_backlog()`

> **内部方法**
事件处理器洪峰检测

**返回值** (`存在未完成的`): pending handler task 时返回 True

---


### `run_full_gc_collection(gc_module: Any, baseline: float | None, growth_mb: int)`

> **内部方法**
执行一次全量回收（受内存增长门限约束）

优先使用 tracemalloc 追踪值，不可用则回退 RSS。当 ``growth_mb > 0``
且距上次全量回收基线增长不足时跳过回收，避免内存稳定时空转。

- **gc_module** (```gc```): 模块（便于测试注入）
- **baseline** (`上次全量回收后的内存基线（MB），None`): 表示首次
- **growth_mb** (`内存增长门限（MB），0`): 表示不设门限
**返回值** (```(collected,`): 新基线)``

---

