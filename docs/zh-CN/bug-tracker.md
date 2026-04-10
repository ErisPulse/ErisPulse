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
