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