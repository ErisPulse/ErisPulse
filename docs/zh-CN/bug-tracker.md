# Bug 追踪器

本文档记录 ErisPulse SDK 的已知 Bug 和修复情况。

---

## 已修复的 Bug

### [BUG-001] Init 命令适配器配置路径类型错误

**问题**: 使用 `ep init` 命令进行交互式初始化时，选择配置适配器会出现类型错误：

```
交互式初始化失败: unsupported operand type(s) for /: 'str' and 'str'
```

**原因**: 2.3.7 版本调整配置文件路径时，方法参数类型不一致。`_configure_adapters_interactive_sync` 接收 `str` 类型参数，但内部使用 `Path` 的 `/` 操作符拼接路径。

**影响版本**: 2.3.7 - 2.3.9-dev.1

**修复版本**: 2.3.9-dev.1

**修复内容**: 将 `_configure_adapters_interactive_sync` 方法的参数类型从 `str` 改为 `Path`，调用时直接传递 `Path` 对象。

**修复日期**: 2026/03/23

---

### [BUG-002] 重启后命令事件失效

**问题**: 调用 `sdk.restart()` 后，通过 `@command` 注册的命令无法被触发，表现为发送命令后机器人无响应。

**原因**: `adapter.shutdown()` 清空事件总线后，`BaseEventHandler` 的 `_linked_to_adapter_bus` 状态未重置为 `False`，导致 `_process_event` 方法认为已经挂载到适配器总线，跳过重新挂载操作。

**影响版本**: 2.2.x - 2.4.0-dev.2

**修复版本**: 2.4.0-dev.3

**修复内容**: 引入 `_linked_to_adapter_bus` 状态追踪，`_clear_handlers()` 断开总线连接后，下次 `register()` 自动重新挂载，适配 shutdown/restart 场景。

**修复日期**: 2026/04/09

---

### [BUG-003] 生命周期事件处理器未清理

**问题**: `sdk.restart()` 后，旧的生命周期事件处理器仍然存在并重复触发，导致同一个事件被多次处理。

**原因**: `lifecycle._handlers` 字典在 `uninit()` 时从未被清理，restart 后旧处理器与新处理器同时存在。

**影响版本**: 2.3.0 - 2.4.0-dev.2

**修复版本**: 2.4.0-dev.3

**修复内容**: 在 `Uninitializer` 的清理流程末尾（所有事件提交之后），清空 `lifecycle._handlers`。

**修复日期**: 2026/04/09

---

### [BUG-004] Event.confirm() 确认词集合赋值重复

**问题**: `Event.confirm()` 方法中，`_yes`、`_no`、`_all` 三个变量的赋值代码被完全重复了两次（共6行），导致无意义的重复计算。

**原因**: 代码复制粘贴错误。

**影响版本**: 2.4.0-dev.4

**修复版本**: 2.4.2-dev.1

**修复内容**: 删除 `wrapper.py` 中 739-741 行的重复赋值代码。

**修复日期**: 2026/04/13

---

### [BUG-005] MessageBuilder.at 方法定义被覆盖（死代码）

**问题**: `MessageBuilder` 类中 `at` 方法被定义了三次：一个实例方法、一个静态方法、最后被 `_DualMethod` 赋值覆盖。前两个定义是永远不会被执行的死代码。

**原因**: 重构为 `_DualMethod` 双模式描述符时，忘记删除旧的手动定义。

**影响版本**: 2.4.0-dev.0

**修复版本**: 2.4.2-dev.1

**修复内容**: 删除 `message_builder.py` 中 159-181 行的两个死 `at` 方法定义，只保留 `_DualMethod` 赋值。

**修复日期**: 2026/04/13

---

### [BUG-006] Event.is_friend_add/is_friend_delete 的 detail_type 与 OB12 标准不一致

**问题**: `Event.is_friend_add()` 检查 `detail_type == "friend_add"`，`Event.is_friend_delete()` 检查 `detail_type == "friend_delete"`，但 OneBot12 标准定义的 `detail_type` 值为 `"friend_increase"` 和 `"friend_decrease"`。与 `notice.py` 中 `on_friend_add`/`on_friend_remove` 装饰器使用的值不一致，导致通过装饰器注册的处理器触发时，对应的 `is_friend_add()`/`is_friend_delete()` 判断方法返回 `False`。

**原因**: `wrapper.py` 中使用了非标准的命名，而 `notice.py` 使用了正确的 OB12 标准命名。

**影响版本**: rq实装至今

**修复版本**: 2.4.2-dev.1

**修复内容**: 将 `is_friend_add()` 的匹配值从 `"friend_add"` 改为 `"friend_increase"`，`is_friend_delete()` 从 `"friend_delete"` 改为 `"friend_decrease"`。

**修复日期**: 2026/04/13

---

### [BUG-007] adapter.clear() 未清理 _started_instances 导致重启后状态不正确

**问题**: `AdapterManager.clear()` 方法清除了 `_adapters`、`_adapter_info`、处理器和 `_bots`，但遗漏了 `_started_instances` 集合。如果适配器正在运行时调用 `clear()`，`_started_instances` 会保留悬空引用，导致重启后状态判断错误。

**原因**: 2.4.0-dev.1 引入 `_started_instances` 时未在 `clear()` 中同步清理。

**影响版本**: 2.4.0-dev.1 - 2.4.2-dev.0

**修复版本**: 2.4.2-dev.1

**修复内容**: 在 `clear()` 方法中添加 `self._started_instances.clear()`。

**修复日期**: 2026/04/13

---

### [BUG-008] command.wait_reply() 使用已弃用的 asyncio.get_event_loop()

**问题**: `CommandHandler.wait_reply()` 方法使用 `asyncio.get_event_loop()` 创建 future 和获取时间戳，该方法在 Python 3.10+ 中已弃用，在异步上下文中应使用 `asyncio.get_running_loop()`。与同文件中 `wrapper.py` 的 `wait_for()` 方法使用的 `get_running_loop()` 不一致。

**原因**: 开发时使用了旧版 API，后续新增的 `wait_for()` 使用了正确的 API 但未回溯修复旧代码。

**影响版本**: 2.3.0-dev.0

**修复版本**: 2.4.2-dev.1

**修复内容**: 将 `command.py` 中两处 `asyncio.get_event_loop()` 替换为 `asyncio.get_running_loop()`。

**修复日期**: 2026/04/13

---

### [BUG-009] Event.collect() 字段缺少 key 时静默跳过

**问题**: `Event.collect()` 方法在遍历字段列表时，如果某个字段字典缺少 `key`，会静默跳过该字段，不输出任何日志或警告。开发者如果拼写错误（如 `"Key"` 而非 `"key"`），整个字段会被悄悄忽略，导致下游行为难以排查。

**原因**: 缺少输入验证和错误反馈。

**影响版本**: 2.4.0-dev.4

**修复版本**: 2.4.2-dev.1

**修复内容**: 在跳过前添加 `logger.warning()` 记录缺少 `key` 的字段信息。

**修复日期**: 2026/04/13

---

### [BUG-010] LazyModule 同步访问 BaseModule 导致未初始化完成

**问题**: 用户在同步上下文中访问懒加载的 BaseModule 属性时，模块使用 `loop.create_task()` 异步初始化但不等待，导致属性访问时可能未初始化完成，引发竞态条件。

**原因**: `_ensure_initialized()` 对 BaseModule 使用 `loop.create_task(self._initialize())` 后立即返回，未确保初始化完成。

**影响版本**: 2.4.0-dev.0 - 2.4.2-dev.1

**修复版本**: 2.4.2-dev.2

**修复内容**: 在同步上下文中，BaseModule 的初始化改为使用 `asyncio.run(self._initialize())`，确保初始化完成后再返回。保持透明代理特性，用户无需感知同步/异步差异。

**修复日期**: 2026/04/21

---

### [BUG-011] 配置系统多线程写入导致数据丢失

**问题**: 在多线程环境下，多个线程同时调用 `config.setConfig()` 时，`_flush_config()` 读取-修改-写入操作不是原子性的，可能导致部分写入丢失。

**原因**: `_flush_config()` 虽然使用了 `RLock`，但文件读取和写入之间没有文件锁保护，且 `_schedule_write` 的 Timer 可能被多次触发导致覆盖。

**影响版本**: 2.3.0 - 2.4.2-dev.1

**修复版本**: 2.4.2-dev.2

**修复内容**:
1. 添加文件锁机制（`_file_lock`）确保文件操作原子性
2. 使用临时文件写入后原子性重命名（`os.replace`/`os.rename`）
3. 改进 `_schedule_write` 的 Timer 取消和重新调度逻辑

**修复日期**: 2026/04/21

---

### [BUG-012] SDK 属性访问错误信息不准确

**问题**: 访问不存在的属性时，错误提示"您可能使用了错误的SDK注册对象"，可能误导用户，实际可能是模块未启用或名称拼写错误。

**原因**: `__getattribute__` 的错误信息没有区分不同场景，统一给出模糊的提示。

**影响版本**: 2.0.0 - 2.4.2-dev.1

**修复版本**: 2.4.2-dev.2

**修复内容**: 根据属性名称区分不同场景：
1. 已注册但未启用：提示模块/适配器未启用
2. 完全不存在：提示检查名称拼写
同时将原始 AttributeError 重新抛出，便于上层捕获。

**修复日期**: 2026/04/21

---

### [BUG-013] Uninitializer 对未初始化 LazyModule 的清理逻辑过于复杂

**问题**: `Uninitializer` 为从未被访问过的 LazyModule 创建临时实例来调用 `on_unload`，代码复杂且容易出错。

**原因**: 试图为所有 LazyModule 调用生命周期方法，但未初始化的模块不需要也不应该被初始化。

**影响版本**: 2.4.0-dev.0 - 2.4.2-dev.1

**修复版本**: 2.4.2-dev.2

**修复内容**: 简化清理逻辑，只处理已初始化的 LazyModule：
1. 跳过未初始化的 LazyModule，不创建临时实例
2. 只为已初始化的模块调用 `on_unload`
3. 删除复杂的临时实例创建逻辑

**修复日期**: 2026/04/21
