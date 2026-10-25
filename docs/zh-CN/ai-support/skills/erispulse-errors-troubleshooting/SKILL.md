---
name: erispulse-errors-troubleshooting
description: "适用于：遇到异常/组件不工作时的诊断路径：异常总览、排障指南、bug 追踪。覆盖场景：ErisPulse 所有自定义异常都继承自 `ErisPulseError`，底层库异常（aiohttp、aiomysql 等）。本文档记录 ErisPulse SDK 的已知 Bug 及其修复情况，按修复版本时间顺序排列。"
---

# ErisPulse 异常体系与排障

本技能由 ErisPulse 文档自动构建（generate-skills.py）。
仓库：https://github.com/ErisPulse/ErisPulse
各节末尾标注了来源文档路径，需要最新内容请以仓库 docs/zh-CN/ 为准。

## 异常捕获总览

> 来源: `docs/zh-CN/advanced/errors.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/advanced/errors.md）

# 异常体系与捕获指南

> [!NOTE]
> **L1 核心必读**——首页"阅读路径"中的五篇核心文档之一，模块开发必备。


ErisPulse 所有自定义异常都继承自 `ErisPulseError`，底层库异常（aiohttp、aiomysql 等）
会在框架内部被捕获并转换为对应的 ErisPulse 异常——业务代码**无需依赖任何底层库异常类型**。

{!--< tips >!--}
1. 想宽泛兜底：捕获 `ErisPulseError`（所有框架异常的基类）
2. 想精确处理：按模块捕获（如 `ModuleCallTimeoutError`、`StorageUnreachableError`）
3. 存储操作默认不抛出：失败时记日志并返回 `False / None / default`；连接状态变化订阅 `storage.unreachable` / `storage.recovered` 事件
{!--< /tips >!--}

## 异常总览

```text
ErisPulseError                      # 所有框架异常的基类
├── ClientError                     # HTTP/WS 客户端请求异常基类（Core/client）
│   ├── ClientConnectionError       # 连接层错误：DNS 解析失败、连接被拒、网络不可达
│   ├── ClientTimeoutError          # 请求超时
│   └── HTTPStatusError             # HTTP 状态码错误（如 4xx/5xx 且 raise_for_status）
├── WebSocketError                  # WebSocket 异常基类（Core/client 的 WS 连接）
│   └── WebSocketDisconnect         # WebSocket 断开连接（服务端/客户端通用）
├── ConnectionRegistryError         # 连接注册表异常基类（Core/connections，2.10+）
│   ├── ConnectionNotFoundError     # 连接不存在/已断开注销（connections.get/close）
│   └── ConnectionPermissionError   # 非 owner 关闭他人连接（关闭权归创建者）
├── StorageError                    # 存储异常基类（Core/storage）
│   └── StorageUnreachableError     # 存储后端不可达（建池重试耗尽：数据库不可达/凭据错误）
├── InteractionError                # 交互会话异常基类（Core/Event/interaction）
│   ├── InteractionCancelled        # 挂起的等待/租约被取消（wait_reply 上层转为返回 None）
│   └── SessionOccupiedError        # 会话互斥租约被占用（hold() 获取失败）
├── ModuleError                     # 模块系统异常基类（Core/module）
│   └── ModuleCallError             # 模块间调用异常基类
│       ├── ModuleNotAvailableError # 目标模块未注册/未启用/初始化失败（含懒加载访问）
│       ├── ServiceNotProvidedError # 目标模块未声明该服务（meta.services 白名单外）
│       └── ModuleCallTimeoutError  # 被调方法执行超时（默认 30s）
├── ShadowError                     # 影子模块异常基类（Core/shadow）
│   ├── ShadowStateError            # 状态不满足：目标未加载/已有活跃影子/未绑定影子（start/dismiss）
│   ├── ShadowSourceError           # 影子源不可用：路径不存在/加载器缺失/装载失败（start）
│   └── ShadowPromoteError          # 转正失败：影子未注册/未加载/加载器无快照/重载失败（promote）
└── StrictModeError                 # 严格模式致命违规（中止启动流程，loaders/strict）
```

## 结构化属性

捕获异常后可读取结构化属性（无需解析消息文本）：

| 异常 | 属性 |
|------|------|
| `ClientError`（含子类） | `.url` 请求 URL、`.method` 请求方法、`.attempts` 已尝试次数（重试耗尽时） |
| `HTTPStatusError` | `.status` 状态码、`.message` 响应消息 |
| `WebSocketDisconnect` | `.code` 关闭码、`.reason` 关闭原因 |
| `ConnectionNotFoundError` | `.connection_id` 查找的连接 id |
| `ConnectionPermissionError` | `.connection_id` 目标连接 id、`.owner` 连接归属 owner |
| `StorageUnreachableError` | `.backend` 后端名（sqlite/mysql/postgres）、`.cooldown` 冷却秒数 |
| `ModuleCallError`（含子类） | `.module` 目标模块名、`.method` 目标方法名 |
| `ModuleCallTimeoutError` | 继承 `.module/.method`，另有 `.timeout` 超时时限（秒） |
| `InteractionCancelled` | `.reason` 取消原因、`.wait_key` 会话键 |
| `SessionOccupiedError` | `.wait_key` 会话键、`.owner` 占用者 |
| `StrictModeError` | `.violations` 违规记录列表 |

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await sdk.client.post(url, json=payload)
except ClientError as e:
    print(f"请求失败 {e.method} {e.url}，共尝试 {e.attempts} 次: {e}")
```

## 各异常说明与发生位置

### Client 系列 — `Core/client.py` / `Core/Bases/client.py`

`sdk.client` / HTTP 客户端与 WebSocket 客户端发起请求时抛出：

| 异常 | 发生位置 | 典型场景 |
|------|----------|----------|
| `ClientError` | 请求封装层 | 其它客户端错误（底层 aiohttp 异常已转换） |
| `ClientConnectionError` | 连接建立阶段 | 目标服务不可达、DNS 失败、连接被拒 |
| `ClientTimeoutError` | 请求执行阶段 | 超过请求超时时间 |
| `HTTPStatusError` | `raise_for_status()` | 响应状态码为 4xx/5xx |

```python
from ErisPulse.Core.Bases.errors import ClientTimeoutError

try:
    resp = await sdk.client.get("https://api.example.com", timeout=5)
except ClientTimeoutError:
    ...
```

### WebSocket 系列 — `Core/client.py`（`send` / `receive`）

| 异常 | 发生位置 | 典型场景 |
|------|----------|----------|
| `WebSocketError` | WS 收发方法 | 连接已关闭、收到意外消息类型、底层 WS 异常 |
| `WebSocketDisconnect` | WS 收发方法 | 对端正常断开连接（框架会自动重连） |

### 连接注册表系列 — `Core/connections.py`（2.10+）

| 异常 | 发生位置 | 典型场景 |
|------|----------|----------|
| `ConnectionNotFoundError` | `connections.get` / `assign` / `dismiss` / `close` | 连接 id 不存在或已断开注销 |
| `ConnectionPermissionError` | 非 owner 调用 `conn.close()` | 跨模块关闭他人连接（发送与分组不受限） |

### Storage 系列 — `Core/storage` / `Core/Bases/sql_base.py`

| 异常 | 发生位置 | 典型场景 |
|------|----------|----------|
| `StorageError` | 存储层 | 存储相关异常基类 |
| `StorageUnreachableError` | 建池阶段 | 数据库不可达 / 凭据错误 / 网络隔离，重试耗尽 |

> **存储操作的失败语义**：KV 与查询操作**默认不抛出**——失败时记录 ERROR 日志并
> 返回 `False` / `None` / `default`（避免连接问题阻塞框架运行）。因此业务代码通常
> **不会**捕获到 `StorageUnreachableError`（它主要供直接操作存储底层或自定义后端使用）。
> 运行时感知连接状态请订阅生命周期事件 `storage.unreachable` / `storage.recovered`
> （详见[生命周期事件](lifecycle.md#存储连接状态)）。

连接失败行为详见[存储后端 → 连接失败行为](storage-backends.md#连接失败行为)。

### Interaction — `Core/Event/interaction.py`

`wait_reply` / 会话租约 / 提醒定时器相关：

| 异常 | 发生位置 | 典型场景 |
|------|----------|----------|
| `InteractionError` | 交互会话层 | 交互会话异常基类 |
| `InteractionCancelled` | 挂起等待被取消时 | 设置到等待 future 上（等待方可捕获获取 `.reason`） |
| `SessionOccupiedError` | `hold()` 租约获取失败 | 会话已被其他 owner 占用（`.owner` 可查占用者） |

等待被取消（模块卸载 / 平台关闭 / 同会话新等待取代）时，`wait_reply` **返回 `None`**
而不抛出异常（`InteractionCancelled` 在内部被转换）；需要区分取消原因时才直接捕获它。

### Module 系列 — `Core/module.py`（`sdk.module.call`）

| 异常 | 发生位置 | 典型场景 |
|------|----------|----------|
| `ModuleError` | 模块系统 | 模块系统异常基类 |
| `ModuleCallError` | `module.call()` | 模块间调用异常基类 |
| `ModuleNotAvailableError` | `module.call()` / 懒加载属性访问 | 目标未注册 / 未启用 / 初始化失败 |
| `ServiceNotProvidedError` | `module.call()` | 目标 `meta.services` 白名单未声明该方法 |
| `ModuleCallTimeoutError` | `module.call()` | 被调协程超过超时时间（默认 30s） |

"目标模块不可用"在不同访问路径下的异常类型：

| 访问路径 | 异常 |
|----------|------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError`（类型化） |
| `sdk.module.X.attr`（懒加载属性访问，初始化失败后） | `ModuleNotAvailableError` |
| `sdk.module.X`（模块未启用时的属性访问） | `AttributeError`（Python 属性惯例，`hasattr` 依赖此语义） |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # 目标模块不存在 / 未启用
except ServiceNotProvidedError:
    ...  # 目标模块未提供该服务
```

### Shadow 系列 — `Core/shadow.py`（影子模块）

| 异常 | 发生位置 | 典型场景 |
|------|----------|----------|
| `ShadowError` | 影子模块机制 | 影子异常基类（统一捕获所有影子错误） |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | 目标未加载 / 已有活跃影子 / 未绑定影子 |
| `ShadowSourceError` | `shadow_start()` | 源路径不存在 / 插件加载器缺失 / 源无可加载类 / 装载失败 |
| `ShadowPromoteError` | `promote_shadow()` | 影子未注册 / 未加载 / 加载器不支持快照 / 转正重载失败 |

### 框架内部参数校验（ValueError）

存储查询构建器的参数校验（空列类型、`Insert` 非 dict、不安全列类型等）抛标准
`ValueError`——这类属于**开发期编码错误**，正常业务代码不应捕获，而应修正调用。

适配器标准动作失败**不抛异常**：返回带 `retcode` 的响应字典（协议语义，如
`retcode=10002` 表示动作未实现）——与 client 层"失败抛 `ClientError`"是两条并行
的错误通道，适配器开发时需同时处理。

## 捕获建议

```python
from ErisPulse.Core import ErisPulseError  # 基类已从 Core 聚合导出

try:
    ...
except ErisPulseError as e:
    ...  # 统一兜底：所有框架自定义异常
```

- 模块开发：按需精确捕获（上表），最外层可用 `ErisPulseError` 兜底
- 异常均已从 `ErisPulse.Core` 聚合导出（含 `SessionOccupiedError` / `InteractionCancelled` / `StrictModeError`），也可从 `ErisPulse.Core.Bases.errors` 导入
- 完整定义见 `src/ErisPulse/Core/Bases/errors.py`

## 关停噪音折叠

长期驻留进程在关停（或后台循环被取消）时，事件循环常会刷出一批无处置价值的
`Task was destroyed but it is pending!` 类解释器噪音。框架内置**同类噪音折叠**：
2 秒窗口内的同类消息降级为 TRACE 并合并计数，只输出一次，结尾带
「（另有 N 次同类消息被折叠）」后缀。这是刻意的降噪行为——看到折叠后缀不代表
框架吞掉了真实异常，业务异常（上表各类）照常完整输出。折叠仅针对解释器退出噪音，
业务异常不受影响。什么级别的异常值得留痕、什么可以降级/折叠，遵循
[工程健壮性规则 · 异常留痕分级](../styleguide/engineering.md#1-异常留痕分级)。

## 已知问题追踪

> 来源: `docs/zh-CN/bug-tracker.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/bug-tracker.md）

# Bug 追踪器

本文档记录 ErisPulse SDK 的已知 Bug 及其修复情况，按修复版本时间顺序排列。

> **写给读者**
> 没有任何软件天生完美，再细心的开发者也会留下小错误。本追踪收录的都是对运行有实际影响的问题——那些过于细微、连「轻微」等级都达不到的瑕疵并不会出现在这里。清单中「严重」项看起来不少，但公开记录这些 Bug 的初衷是让排查与回溯更顺畅，而非制造焦虑：能被看见、被记录、被修复的问题，本身就是项目不断变好的证明。看到这份清单不必紧张，它是一份排查工具，而不是恐惧的来源。

> **如何阅读 & 维护约定**
> - 每条 Bug 记录包含问题描述、根因分析、影响版本范围、修复方案等结构化字段，建议升级前先检索「影响版本」是否覆盖当前使用的版本。
> - 如需新增 Bug 条目，请在对应位置补充内容，遵循下文字段规范与严重性/类型分类。

---

## 字段说明

### 必填字段

| 字段 | 说明 |
|------|------|
| **问题** | Bug 的外在表现、用户可观察到的异常现象。尽量给出报错信息或典型场景 |
| **原因** | 根因分析，指向具体的代码缺陷（含「根因链路」图示用于复杂场景） |
| **影响版本** | 受影响的版本区间，格式 `引入版本 - 修复版本`（含两端 dev 版本） |
| **修复版本** | 修复该 Bug 的具体版本号 |
| **修复内容** | 修复方案的简要描述，含关键代码变更点 |
| **修复日期** | 对应修复版本的发布日期，采用 `YYYY/MM/DD` 格式 |
| **严重性** | 按下文「严重性分级」标注 |
| **类型** | 按下文「类型分类」标注，可组合（如 `适配器 / 路由`） |

### 可选字段

| 字段 | 说明 | 适用场景 |
|------|------|---------|
| **复现步骤** | 触发该 Bug 的最小可复现路径 | 复杂 Bug、偶发性 Bug 建议补充 |
| **关联** | 相关 Issue / PR / Commit 链接 | 有外部讨论记录时补充 |
| **回归测试** | 验证修复、防止再次回归的测试用例位置 | 已编写对应 pytest 用例时补充 |

---

## 严重性分级

| 标识 | 级别 | 判定标准 | 典型表现 |
|------|------|---------|---------|
| 🔴 | 严重 | 导致进程崩溃、数据丢失/损坏、核心功能完全不可用、安全漏洞 | OOM Kill、消息无法发送、模块无法加载、热重载失败 |
| 🟡 | 中等 | 功能异常但有规避路径、非核心功能失效、偶发问题 | 状态判断错误、重复触发、缓存过期、错误提示不准 |
| 🟢 | 轻微 | 不影响核心功能、仅代码质量或体验问题、潜在风险未爆发 | 弃用 API、死代码、缺失 warning 日志 |

---

## 类型分类

| 类型 | 覆盖范围 |
|------|---------|
| 配置系统 | `ConfigManager`、配置读写、配置 Schema、热更新 |
| 事件系统 | `Event` 模块（command/message/notice/request/meta）、事件分发、处理器注册 |
| 适配器 | `AdapterManager`、`BaseAdapter`、账户解析、Bot 状态、中间件 |
| 路由 | `RouterManager`、HTTP/WebSocket/SSE 路由、限流、CORS |
| 客户端 | `HttpClient`、`ClientWebSocket`、aiohttp 封装 |
| 存储 | `StorageManager`、SQLite、SQL 构建器、嵌套键 |
| 加载系统 | `Loader`、`LazyModule`、`ModuleInitializer`、严格模式、模块发现 |
| CLI | `epsdk` 命令、`init`/`run`/`install`、参数解析、信号处理 |
| 运行时 | `sdk.run`/`restart`/`uninit`、生命周期、信号、子进程 |

---

## 条目模板

新增 Bug 条目请遵循以下格式：

```markdown
### [BUG-XXX] 标题

**问题**: 问题描述（报错信息或典型现象）
**原因**: 根因分析
**影响版本**: 引入版本 - 修复版本
**修复版本**: x.x.x
**修复内容**: 修复方案
**修复日期**: YYYY/MM/DD

<!-- 可选字段 -->
**复现步骤**: （复杂 Bug 建议补充）
**关联**: （Issue/PR 链接）
**回归测试**: （验证用例路径）

**严重性**: 🔴 严重 | 🟡 中等 | 🟢 轻微
**类型**: 配置系统 / 事件系统 / 适配器 / 路由 / 客户端 / 存储 / 加载系统 / CLI / 运行时
```

---

## 统计概览

| 严重性 | 数量 |
|--------|------|
| 🔴 严重 | 16 |
| 🟡 中等 | 26 |
| 🟢 轻微 | 3 |
| **合计** | **45** |

| 类型 | 数量 |
|------|------|
| 事件系统 | 12 |
| 配置系统 | 12 |
| 适配器 | 7 |
| CLI | 3 |
| 存储 | 3 |
| 加载系统 | 4 |
| 路由 | 2 |
| 客户端 | 1 |
| 运行时 | 1 |

> 注：单条 Bug 可归属多个类型，上表按主类型统计。
> 注：BUG-028 / BUG-031 编号空缺（登记时废弃，为保持既有编号稳定不回收重排）。

---

## 已修复的 Bug

### [BUG-001] 事件处理器重复注册导致事件被多次处理

**问题**: 使用多个 `@message` / `@notice` 等装饰器注册处理器时，同一事件会被重复触发多次，导致命令被执行多遍、日志重复输出。

**原因**: `BaseEventHandler` 向适配器事件总线注册处理器时缺少去重逻辑，每个装饰器都会向总线挂载一次，事件分发时被多次调用。

**影响版本**: 2.2.0-dev.0 - 2.2.1-dev.0

**修复版本**: 2.2.1-dev.0

**修复内容**: 优化 `BaseEventHandler`，确保每个事件类型只向适配器注册一次处理器，避免重复触发。

**修复日期**: 2025/08/18

**严重性**: 🔴 严重

**类型**: 事件系统

---

### [BUG-002] Init 命令适配器配置路径类型错误

**问题**: 使用 `ep init` 命令进行交互式初始化时，选择配置适配器会出现类型错误：

```
交互式初始化失败: unsupported operand type(s) for /: 'str' and 'str'
```

**原因**: 2.3.7 版本调整配置文件路径时，方法参数类型不一致。`_configure_adapters_interactive_sync` 接收 `str` 类型参数，但内部使用 `Path` 的 `/` 操作符拼接路径。

**影响版本**: 2.3.7 - 2.3.9-dev.1

**修复版本**: 2.3.9-dev.1

**修复内容**: 将 `_configure_adapters_interactive_sync` 方法的参数类型从 `str` 改为 `Path`，调用时直接传递 `Path` 对象。

**修复日期**: 2026/03/23

**严重性**: 🟡 中等

**类型**: CLI

---

### [BUG-003] 重启后命令事件失效

**问题**: 调用 `sdk.restart()` 后，通过 `@command` 注册的命令无法被触发，表现为发送命令后机器人无响应。

**原因**: `adapter.shutdown()` 清空事件总线后，`BaseEventHandler` 的 `_linked_to_adapter_bus` 状态未重置为 `False`，导致 `_process_event` 方法认为已经挂载到适配器总线，跳过重新挂载操作。

**影响版本**: 2.2.x - 2.4.0-dev.2

**修复版本**: 2.4.0-dev.3

**修复内容**: 引入 `_linked_to_adapter_bus` 状态追踪，`_clear_handlers()` 断开总线连接后，下次 `register()` 自动重新挂载，适配 shutdown/restart 场景。

**修复日期**: 2026/04/09

**严重性**: 🔴 严重

**类型**: 事件系统

---

### [BUG-004] 生命周期事件处理器未清理

**问题**: `sdk.restart()` 后，旧的生命周期事件处理器仍然存在并重复触发，导致同一个事件被多次处理。

**原因**: `lifecycle._handlers` 字典在 `uninit()` 时从未被清理，restart 后旧处理器与新处理器同时存在。

**影响版本**: 2.3.0 - 2.4.0-dev.2

**修复版本**: 2.4.0-dev.3

**修复内容**: 在 `Uninitializer` 的清理流程末尾（所有事件提交之后），清空 `lifecycle._handlers`。

**修复日期**: 2026/04/09

**严重性**: 🟡 中等

**类型**: 运行时

---

### [BUG-005] Event.is_friend_add/is_friend_delete 的 detail_type 与 OB12 标准不一致

**问题**: `Event.is_friend_add()` 检查 `detail_type == "friend_add"`，`Event.is_friend_delete()` 检查 `detail_type == "friend_delete"`，但 OneBot12 标准定义的 `detail_type` 值为 `"friend_increase"` 和 `"friend_decrease"`。与 `notice.py` 中 `on_friend_add`/`on_friend_remove` 装饰器使用的值不一致，导致通过装饰器注册的处理器触发时，对应的 `is_friend_add()`/`is_friend_delete()` 判断方法返回 `False`。

**原因**: `wrapper.py` 中使用了非标准的命名，而 `notice.py` 使用了正确的 OB12 标准命名。

**影响版本**: 实装至今

**修复版本**: 2.4.2-dev.1

**修复内容**: 将 `is_friend_add()` 的匹配值从 `"friend_add"` 改为 `"friend_increase"`，`is_friend_delete()` 从 `"friend_delete"` 改为 `"friend_decrease"`。

**修复日期**: 2026/04/13

**严重性**: 🟡 中等

**类型**: 事件系统

---

### [BUG-006] adapter.clear() 未清理 _started_instances 导致重启后状态不正确

**问题**: `AdapterManager.clear()` 方法清除了 `_adapters`、`_adapter_info`、处理器和 `_bots`，但遗漏了 `_started_instances` 集合。如果适配器正在运行时调用 `clear()`，`_started_instances` 会保留悬空引用，导致重启后状态判断错误。

**原因**: 2.4.0-dev.1 引入 `_started_instances` 时未在 `clear()` 中同步清理。

**影响版本**: 2.4.0-dev.1 - 2.4.2-dev.0

**修复版本**: 2.4.2-dev.1

**修复内容**: 在 `clear()` 方法中添加 `self._started_instances.clear()`。

**修复日期**: 2026/04/13

**严重性**: 🟡 中等

**类型**: 适配器

---

### [BUG-007] command.wait_reply() 使用已弃用的 asyncio.get_event_loop()

**问题**: `CommandHandler.wait_reply()` 方法使用 `asyncio.get_event_loop()` 创建 future 和获取时间戳，该方法在 Python 3.10+ 中已弃用，在异步上下文中应使用 `asyncio.get_running_loop()`。与同文件中 `wrapper.py` 的 `wait_for()` 方法使用的 `get_running_loop()` 不一致。

**原因**: 开发时使用了旧版 API，后续新增的 `wait_for()` 使用了正确的 API 但未回溯修复旧代码。

**影响版本**: 2.3.0-dev.0

**修复版本**: 2.4.2-dev.1

**修复内容**: 将 `command.py` 中两处 `asyncio.get_event_loop()` 替换为 `asyncio.get_running_loop()`。

**修复日期**: 2026/04/13

**严重性**: 🟢 轻微

**类型**: 事件系统

---

### [BUG-008] Bot 离线事件在 shutdown 过程中被重复提交

**问题**: 调用 `adapter.shutdown()` 关闭所有适配器时，`_update_bot_status()` 会在关闭流程中反复提交 Bot 离线事件，导致同一批 Bot 被多次标记离线并触发多次 `adapter.bot.offline` 生命周期事件。

**原因**: 2.4.0-dev.1 引入的 Bot 状态追踪系统未在 `shutdown()` 期间设置"正在关闭"标志，`_update_bot_status()` 无法区分正常离线与关闭流程中的级联离线。

**影响版本**: 2.4.0-dev.1 - 2.4.2-dev.1

**修复版本**: 2.4.2-dev.1

**修复内容**: 在 `AdapterManager` 中新增 `_is_being_shutdown` 标志，`shutdown()` 开始时置为 True、结束时清除；`_update_bot_status()` 检查该标志后跳过关闭过程中的重复提交。

**修复日期**: 2026/04/21

**严重性**: 🟡 中等

**类型**: 适配器

---

### [BUG-009] LazyModule 同步访问 BaseModule 导致未初始化完成

**问题**: 用户在同步上下文中访问懒加载的 BaseModule 属性时，模块使用 `loop.create_task()` 异步初始化但不等待，导致属性访问时可能未初始化完成，引发竞态条件。

**原因**: `_ensure_initialized()` 对 BaseModule 使用 `loop.create_task(self._initialize())` 后立即返回，未确保初始化完成。

**影响版本**: 2.4.0-dev.0 - 2.4.2-dev.1

**修复版本**: 2.4.2-dev.2

**修复内容**: 在同步上下文中，BaseModule 的初始化改为使用 `asyncio.run(self._initialize())`，确保初始化完成后再返回。保持透明代理特性，用户无需感知同步/异步差异。

**修复日期**: 2026/04/21

**严重性**: 🟡 中等

**类型**: 加载系统

---

### [BUG-010] 配置系统多线程写入导致数据丢失

**问题**: 在多线程环境下，多个线程同时调用 `config.setConfig()` 时，`_flush_config()` 读取-修改-写入操作不是原子性的，可能导致部分写入丢失。

**原因**: `_flush_config()` 虽然使用了 `RLock`，但文件读取和写入之间没有文件锁保护，且 `_schedule_write` 的 Timer 可能被多次触发导致覆盖。

**影响版本**: 2.3.0 - 2.4.2-dev.1

**修复版本**: 2.4.2-dev.2

**修复内容**:
1. 添加文件锁机制（`_file_lock`）确保文件操作原子性
2. 使用临时文件写入后原子性重命名（`os.replace`/`os.rename`）
3. 改进 `_schedule_write` 的 Timer 取消和重新调度逻辑

**修复日期**: 2026/04/21

**严重性**: 🔴 严重

**类型**: 配置系统

---

### [BUG-011] Windows 下 CTRL+C 无法停止程序

**问题**: 在 Windows 上直接运行 `python main.py` 时，按下 CTRL+C 无法终止程序。程序正常启动并输出路由服务器信息后，CTRL+C 完全无响应，只能通过任务管理器强杀进程。而通过 `epsdk run` 启动时可以正常停止——但 `epsdk run` 是通过子进程模型运行的。

**原因**: Hypercorn ASGI 服务器的 `serve()` 函数内部通过 `signal.signal(SIGINT, handler)` 注册了自己的 SIGINT 处理器，覆盖了 Python 默认的 `KeyboardInterrupt` 处理机制。当通过 `asyncio.create_task()` 启动 Hypercorn 作为后台任务时，Hypercorn 的内部 shutdown 流程无法正常触发（因为它期望的是 `worker_serve` 模式），导致 CTRL+C 信号被 Hypercorn 吞掉但不会引发任何清理动作。

**影响版本**: 2.3.6 - 2.4.2

**修复版本**: 2.4.3-dev.0

**修复内容**:
1. 将 ASGI 服务器从 Hypercorn 切换为 Uvicorn（`pyproject.toml` 依赖变更）
2. 使用 `uvicorn.Server._serve()` 直接启动服务器，**绕过** `capture_signals()` 信号处理上下文管理器
3. 通过 `server.should_exit = True` 实现优雅停止，超时则取消后台任务
4. 同步移除子进程运行模型和 `runtime/cleanup.py` 清理模块（子进程清理机制不再需要）

**修复日期**: 2026/04/28

**严重性**: 🔴 严重

**类型**: CLI / 运行时

---

### [BUG-012] 热重启后已更新模块的 Python 代码未生效

**问题**: 执行 `sdk.restart()` 软重启后，已通过 `epsdk install` 升级的模块/适配器的新代码（如新增 API 路由）不生效，仍运行旧版本逻辑。必须完全重启进程才能加载最新代码。

**原因**: `_do_restart()` 在重新初始化时调用 `entry_point.load()`，但该函数从 `sys.modules` 返回了缓存的旧版本模块对象，而非从磁盘重新加载。

**影响版本**: 早期版本 - 2.4.3-dev.1

**修复版本**: 2.4.3-dev.1

**修复内容**: 在 `uninit()` 后、`init()` 前清理 `sys.modules` 中已加载模块/适配器包的缓存，使 `entry_point.load()` 从磁盘加载最新代码。新增 `_collect_top_level_modules()` 与 `_invalidate_module_cache()` 辅助方法，通过 `top_level.txt` 或 entry-point value 推导顶层模块名。

**修复日期**: 2026/05/03

**严重性**: 🔴 严重

**类型**: 加载系统 / 运行时

---

### [BUG-013] 模块加载策略排序逻辑错误

**问题**: `ModuleLoadStrategy` 提供了 `priority` 字段用于声明模块的初始化优先级，但加载策略的实现存在失误，导致模块未按预期的优先级顺序初始化，实际按 `entry_points()` 的默认顺序加载。当模块间存在加载依赖时，无法通过 `priority` 确保正确的初始化先后关系。

**原因**: 加载策略的实现中排序逻辑有误，`initialize_modules()` 未使用 `priority` 对模块列表进行排序。

**影响版本**: 2.3.4 - 2.4.5-dev.2

**修复版本**: 2.4.5-dev.3

**修复内容**: 在 `initialize_modules()` 遍历前，按 `priority` 降序排序模块列表。同 priority 的模块保持原有相对顺序（稳定排序）。

**修复日期**: 2026/05/15

**严重性**: 🟡 中等

**类型**: 加载系统

---

### [BUG-014] 适配器中间件返回 None 导致事件数据丢失

**问题**: `adapter.emit()` 在执行 OneBot12 中间件链时，如果某个中间件返回 `None`（例如忘记 `return data`），后续中间件和所有事件处理器收到的 `processed_data` 变为 `None`，导致事件处理完全失效。

**原因**: 中间件链的实现 `processed_data = await middleware(processed_data)` 未检查返回值是否为 `None`，直接覆盖了上一步的处理结果。

**影响版本**: unknown - 2.4.5-dev.3

**修复版本**: 2.4.5-dev.4

**修复内容**: 中间件返回 `None` 时忽略该返回值，保留原数据继续传递，并输出 warning 级别日志。

**修复日期**: 2026/05/15

**严重性**: 🔴 严重

**类型**: 适配器 / 事件系统

---

### [BUG-015] 配置文件路径依赖工作目录

**问题**: `ConfigManager` 的配置文件路径默认为相对路径 `"config/config.toml"`，在运行时依赖 `os.getcwd()` 解析。如果工作目录在运行期间发生变化（例如通过 `os.chdir()`），配置文件的读写操作会指向错误的位置，导致配置丢失或读取到旧数据。

**原因**: `__init__` 中直接存储相对路径，未在初始化时将其解析为绝对路径。

**影响版本**: 2.3.7 - 2.4.5-dev.3

**修复版本**: 2.4.5-dev.4

**修复内容**: 在 `ConfigManager.__init__()` 中，如果传入的路径为相对路径，自动通过 `os.path.abspath()` 解析为绝对路径。

**修复日期**: 2026/05/15

**严重性**: 🟡 中等

**类型**: 配置系统

---

### [BUG-016] BaseStorage 将存储值 None 与键不存在混淆

**问题**: `BaseStorage.get_multi()` / `__getattr__()` 无法区分"键不存在"与"键的值就是 `None`"两种情况，用户显式存入 `None` 后再读取时会被当作键不存在处理。

**原因**: 取值逻辑直接用 `value is None` 判断键是否存在，缺少独立的"缺失"标记。

**影响版本**: 早期版本 - 2.4.6-dev.6

**修复版本**: 2.4.6-dev.6

**修复内容**: 引入 `_SENTINEL` 哨兵值区分"键不存在"与"值为 None"，二者不再混淆。

**修复日期**: 2026/06/07

**严重性**: 🟡 中等

**类型**: 存储

---

### [BUG-017] WebSocket 路由 auto_accept 标志在服务重启后丢失

**问题**: 服务重启（如 `sdk.restart()`）后，所有 WebSocket 路由的 `auto_accept` 配置都变回 `False`，原本期望自动 accept 的连接变为挂起状态，客户端长时间收不到响应，表现为 WS 连接卡死。

**原因**: `_restore_routes_from_records()` 在从持久化记录恢复路由时把 `auto_accept` 硬编码为 `False`，未读取原始记录中的值；同时路由存储元组也从二元组扩展为三元组时未同步更新恢复逻辑。

**影响版本**: 2.3.8-dev.0 - 2.4.6-dev.6

**修复版本**: 2.4.6-dev.6

**修复内容**: 路由存储元组扩展为 `(handler, auth_handler, auto_accept)`，`_restore_routes_from_records()` 从记录读取真实 `auto_accept` 值而非硬编码 `False`。

**修复日期**: 2026/06/07

**严重性**: 🔴 严重

**类型**: 路由

---

### [BUG-018] HTTP/WS 客户端并发调用导致崩溃与连接泄漏

**问题**: `Core/client.py` 的 HTTP 与 WebSocket 客户端在并发场景下存在多个稳定性缺陷，会导致连接泄漏或进程崩溃：
- 多协程并发调用 `ClientWebSocket.receive()` 时 aiohttp 抛出 `Concurrent call to receive() is not allowed`
- `_get_http_session()` / `_get_ws_session()` 并发调用可能创建多个 session 且 `_drain_sessions()` 未关闭旧连接，造成连接泄漏
- `request()` 的异常捕获顺序错误：`except ClientConnectionError`（ErisPulse 异常）永不触发，aiohttp 的连接错误被通用 `except Exception` 接住，导致"连接重试 + session 重建"逻辑（死代码）从未执行
- `send_json()` 忽略 `mode="binary"` 参数；`_get_ws_session()` 未传入默认请求头

**原因**: 客户端初次实现（2.4.6-dev.5）缺少并发保护与异常分类，对 aiohttp 异常体系与 ErisPulse 自定义异常的继承关系处理不当。

**影响版本**: 2.4.6-dev.5 - 2.4.8

**修复版本**: 2.4.8

**修复内容**:
1. 新增 `_recv_lock` 序列化所有 `receive()` / `receive_text()` / `receive_bytes()` 调用
2. 新增 `_session_lock` 保护 session 创建；`_drain_sessions()` 改为异步方法并真正关闭旧 session
3. 重构 `request()` 异常捕获顺序：`asyncio.TimeoutError` → `aiohttp.ClientConnectionError`（触发 session 重建）→ `aiohttp.ClientError` → `ClientError`（透传）→ `Exception`
4. 修复 `send_json()` 的 mode 处理、`_get_ws_session()` 默认请求头透传、`close()` 的并发竞态、`HttpResponse.__aexit__` 重复 `release()`

**修复日期**: 2026/06/12

**严重性**: 🔴 严重

**类型**: 客户端

---

### [BUG-019] 适配器热重载时路由冲突导致重载失败

**问题**: 第三方模块（如 Dashboard）触发适配器热重载，或适配器启动失败重试时，因上次注册的旧路由（如 `onebot11_default`）未清理，抛出 `WebSocket路径 ... 已注册` 冲突，导致重载失败。需要完全重启进程才能恢复。

**原因**: `AdapterManager.shutdown()` 仅以 `unregister_all_by_namespace(platform)` 清理路由，但适配器（如 OneBot11）以 `onebot11_{account_name}` 为命名空间注册 WS 路由，颗粒度不匹配导致清理为空操作；启动失败重试路径也未清理上次残留路由。

**影响版本**: 早期版本 - 2.4.9

**修复版本**: 2.4.9

**修复内容**:
1. 路由注册时通过 `current_owner` ContextVar 自动追踪 `owner → namespace` 归属关系
2. 新增 `unregister_all_by_owner(owner)`，停止/重启时同时按 owner 清理，覆盖细颗粒度命名空间
3. 新增 `_stop_adapter(platform)` 原语（"停止即清理"），将停止适配器与回收其注册的资源绑定在一次调用里，`restart()` 和启动失败重试均经此入口
4. 新增框架级 `adapter.restart(platform)` API，第三方模块应调用此方法而非直接操作适配器实例

**修复日期**: 2026/06/12

**严重性**: 🔴 严重

**类型**: 适配器 / 路由

---

### [BUG-020] 子进程模式 `ep run <script>` 找不到脚本所在目录的子包

**问题**: 使用 `ep r .\main.py` 非热重载模式运行脚本时，如果脚本有相对导入（如 `from qg import ...`），会报 `No module named 'qg'` 错误。而 `--reload` 模式可以正常运行。

**原因**: 非热重载模式直接调用 `runpy.run_path()` 执行脚本，该函数不会自动将脚本所在目录加入 `sys.path`。而 `--reload` 模式通过 `subprocess.Popen` 子进程运行，子进程自动继承当前工作目录，`sys.path[0]` 即为脚本所在目录，所以能正常工作。

**影响版本**: 2.5.0 - 2.5.2-dev.0

**修复版本**: 2.5.2-dev.0

**修复内容**: 在 `runpy.run_path()` 调用前，手动将脚本所在目录插入 `sys.path[0]`。

**修复日期**: 2026/06/27

**严重性**: 🟡 中等

**类型**: CLI

---

### [BUG-021] SQL 查询构建器拒绝合法通配符和列表达式

**问题**: `SQLiteQueryBuilder` 的 `_build_select_sql()` 对所有 SELECT 列调用 `_validate_identifier()`，该函数使用严格的白名单正则 `^[a-zA-Z_][a-zA-Z0-9_]*$`，导致合法 SQL 语法被误判为不安全列名：

- `SELECT *` — `*` 是 SQL 标准通配符
- `SELECT COUNT(*)` — 聚合函数
- `SELECT users.name` — 限定列名
- `SELECT col AS alias` — 列别名

其中 `Select("*")` 被 Cron 等模块使用，导致模块 `on_load` 执行失败，模块无法加载。

**原因**: 2.4.6 版本增强了 SQL 注入防护，引入了 `_validate_identifier()` 白名单校验。该校验应用于所有列名，但未区分读取端（SELECT/ORDER BY）和写入端（INSERT/UPDATE）。SELECT 列允许复杂的 SQL 表达式，不应受简单标识符白名单限制。

**影响版本**: 2.4.6 - 2.5.2-dev.1

**修复版本**: 2.5.2-dev.2

**修复内容**: 将 SELECT/ORDER BY 的列校验从白名单模式改为黑名单模式：
1. 新增 `_validate_select_column()` 函数，仅拦截 SQL 注入危险字符（`;` `'` `"` `--` `/*` `*/` `\x00` 换行符）
2. 允许任意合法 SQL 列表达式（`*`、`table.*`、`table.column`、`COUNT(*)`、`col AS alias` 等）
3. INSERT/UPDATE 列名仍保持严格白名单校验（仅允许简单标识符）

**修复日期**: 2026/06/29

**严重性**: 🔴 严重

**类型**: 存储

---

### [BUG-022] _resolve_account() 账户解析回归（_accounts_data 未填充）

**问题**: 2.5.2 配置系统重构后，声明了 `AccountConfigClass` 的多账户适配器在调用 `wait_reply`、`reply` 等需要发送消息的方法时，报错 `ValueError("未声明 AccountConfigClass，无法解析账户")`。即使适配器正确配置了多账户信息，账户解析仍然失败。

**原因**: 2.5.2-dev.5 将 `_load_accounts()`（负责读取配置 + 校验 + 填充 `_accounts_data`）重构为 `_ensure_accounts_exist()`（仅生成配置模板），但 `_resolve_account()` 仍检查 `self._accounts_data is None`。由于 `_ensure_accounts_exist()` 不再填充 `_accounts_data`，该属性始终为 `None`，导致 `_resolve_account()` 提前返回 `(None, None)`，账户解析完全失效。

**根因链路**:
```
_load_accounts() 被删除
  → __init__ 不再填充 _accounts_data
    → _accounts_data 恒为 None
      → _resolve_account() 检查 _accounts_data is None → return (None, None)
        → 下游调用 _resolve_account 的地方（如 call_api）拿到 None
          → 触发报错
```

**影响版本**: 2.5.2-dev.5 - 2.5.2

**修复版本**: 2.5.3

**修复内容**: 在 `BaseAdapter.__init__` 中，`_ensure_accounts_exist()` 之后恢复 `_accounts_data` 的填充：
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # 恢复填充，数据源为实时读取的 accounts 属性
```
`_resolve_account()` 逻辑保持不变，完全向后兼容：
- 不声明 `AccountConfigClass` 的适配器：`_accounts_data` 保持 `None` → 返回 `(None, None)`
- 声明了 `AccountConfigClass` 的适配器：`_accounts_data` 被填充 → 正常解析
- 覆写 `_load_accounts` 或手动设置 `_accounts_data` 的适配器：在 `super().__init__()` 后覆盖，优先级最高

**修复日期**: 2026/07/07

**严重性**: 🔴 严重

**类型**: 适配器 / 配置系统

---

### [BUG-023] 修改账户配置后适配器缓存未刷新导致账户解析失败

**问题**: 用户通过 Dashboard 修改多账户适配器的账户配置（如填写 token）后，适配器仍使用旧缓存，调用发送消息相关方法时报 `未找到可用账户 (account_id=default)`。必须重启进程才能让新配置生效。

**原因**: `_accounts_data` 仅在 `BaseAdapter.__init__` 时从配置存储读取一次，之后不再刷新。`AdapterManager._run_adapter()` 与 `restart()` 在调用 `adapter.start()` 前未重新读取账户配置，导致缓存与实际配置脱节。

**影响版本**: 2.4.6 - 2.5.4

**修复版本**: 2.5.4

**修复内容**: 在 `AdapterManager._run_adapter()` 和 `restart()` 中，调用 `adapter.start()` 之前刷新 `adapter._accounts_data = adapter.accounts`，确保每次启动时使用最新配置。

**修复日期**: 2026/07/09

**严重性**: 🔴 严重

**类型**: 适配器 / 配置系统

---

### [BUG-024] storage.set() 写入大数字 ID 键时触发 OOM Kill

**问题**: 调用 `storage.set()` 写入包含大纯数字段（如 QQ 群号 `871684833`）的嵌套键路径时，进程被容器 OOM Kill（退出码 -9），服务直接崩溃无法恢复。

**原因**: `_set_nested_value` 的递归实现中，嵌套键路径里的纯数字段被 `isdigit()` 误判为列表索引，触发 `current.extend([None] * (index - len(current) + 1))`，试图分配数亿元素的列表，瞬间耗尽内存。

**根因链路**:
```
键路径包含纯数字段（如群号 871684833）
  → isdigit() 误判为数组索引
    → extend([None] * (871684833 - len(current) + 1))
      → 尝试分配数亿元素
        → 内存耗尽 → 容器 OOM Kill（退出码 -9）
```

**影响版本**: 2.5.1 - 2.5.5

**修复版本**: 2.5.5

**修复内容**:
1. 预创建中间层时始终使用字典，不再根据下一段是否为数字猜测容器类型
2. 设置最终值时，仅当容器本身已是列表且索引小于 `STORAGE_MAX_LIST_INDEX`（10000）时才按索引处理，超大索引安全跳过
3. 将递归实现改为迭代实现，消除原代码中潜在的无限递归风险
4. 新增 `STORAGE_MAX_LIST_INDEX` 常量到 `Core/constants.py`，集中管理索引安全上限

**修复日期**: 2026/07/10

**复现步骤**:
```python
# 写入包含大数字段（如 QQ 群号）的嵌套键路径即可触发
await sdk.storage.aset("groups.871684833.name", "某群")
# → 进程内存瞬间飙升，被 OOM Kill
```

**回归测试**: `tests/unit/test_unit_storage.py` 新增 4 个回归用例
- `test_nested_key_numeric_segment_as_dict_key` — 精确复现 OOM 场景
- `test_nested_key_numeric_segment_multiple` — 多个连续数字段均作为字典键
- `test_nested_key_existing_list_index_set_within_limit` — 已有列表合理索引写入
- `test_nested_key_list_index_safety_limit` — 超大索引安全限制验证

**严重性**: 🔴 严重

**类型**: 存储

---

### [BUG-025] on_config_update 回调未被核心路由

**问题**: `on_config_update(old, new)` 回调在基类（`BaseModule` / `BaseAdapter`）中已定义，但框架核心未将其与配置变更事件关联。实际表现：通过配置管理面板改配置时可以触发，而手动编辑 `config.toml` 或代码调用 `setConfig()` 时不会触发 `on_config_update`。

**原因**: `ConfigManager` 在配置变更时会发射 `config.set` / `config.updated` 生命周期事件，但缺少将这些事件转发到各组件 `on_config_update` 方法的订阅逻辑。

**根因链路**:
```
核心未订阅 config.set / config.updated
  → 配置变更事件无转发
    → on_config_update 未被调用
      → 手动编辑文件 / 代码 setConfig 不触发热更新回调
```

**影响版本**: 全版本

**修复版本**: 2.6.2

**修复内容**: `ModuleManager` / `AdapterManager` 注册 `config.set`（覆盖代码 `setConfig()` 路径）与 `config.updated`（覆盖手动编辑文件路径）事件订阅，按配置键前缀匹配后调用对应组件的 `on_config_update`，传入类型安全的配置对象。同时修复 `_flush_config()` 写入文件后未同步 `_config_mtime` 的问题，避免框架自身写入被文件监听任务误判为外部修改而重复触发 `config.updated`。

**兼容性说明**: 配置热更新现由框架核心统一维护。此前由配置管理面板代为触发的逻辑已移除，升级框架后需同步升级配置管理面板，否则会出现重复触发（核心 + 面板各调一次）。`on_config_update` 方法签名与语义保持不变，子类无需修改。

**修复日期**: 2026/07/23

**严重性**: 🟡 中等

**类型**: 配置系统

---

### [BUG-026] notice/request 事件 reply 目标推断错误

**问题**: 在群通知事件（如成员加群 `group_member_increase`）中调用 `event.reply()`，消息被发送到触发事件的用户私聊，而非事件所在的群。好友通知事件同理，回复目标可能错乱。

**原因**: `infer_receive_type()` 将事件的 `detail_type` 直接当作会话类型返回。对于 message 事件这是正确的（`detail_type` 值 `private`/`group` 即会话类型），但 notice/request 事件的 `detail_type` 是语义子类型（如 `group_member_increase`、`friend_increase`），不是会话类型。后续的 `convert_to_send_type()` 和 `get_id_field()` 在映射表中找不到该值，回退到默认的 `"user"` / `"user_id"`，导致回复目标错乱。

**根因链路**:
```
notice 事件 detail_type="group_member_increase"
  → infer_receive_type() 直接返回 "group_member_increase"
    → convert_to_send_type("group_member_increase") 不在映射表 → 回退 "user"
    → get_id_field("group_member_increase") 不在映射表 → 回退 "user_id"
      → target_id = event["user_id"]  ← 新成员私聊（而非群）
```

**影响版本**: 全版本

**修复版本**: 2.7.0-dev.3

**修复内容**: `infer_receive_type()` 增加判断——`detail_type` 只有在是已知会话类型（标准类型或自定义类型）时才直接返回；否则根据 ID 字段（`group_id` / `channel_id` / `user_id` 等）推断正确的会话类型。

**回归测试**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference`（10 用例）

**修复日期**: 2026/07/29

**严重性**: 🟢 轻微

**类型**: 事件系统

---

### [BUG-027] 路由限流清理任务使用固定窗口导致长窗口限流规则失效

**问题**: 将路由限流配置为长窗口规则（如 `100/hour`、`{"requests": 100, "window": 3600}`）时，限流形同虚设——实际表现近似 `100/minute`（每小时可放过至约 6000 次请求），完全无法起到预期的小时级防护作用。

**原因**: `_apply_rate_limit` 解析得到每路由的实际 `window`（最高 3600 秒），per-request 检查也确实使用该窗口；但后台清理任务 `_cleanup_expired_rate_limits` 却用固定常量 `DEFAULT_RATE_LIMIT_WINDOW_SECS`（60 秒）作为**所有**路由的统一清理阈值。于是 `100/hour` 路由中早于 60 秒的时间戳被清理任务提前清除，小时窗口内永远累积不到接近 100 条记录，限流被严重削弱。

**根因链路**:
```
_apply_rate_limit 解析 window=3600（100/hour）
  → per-request 检查按 3600s 保留时间戳（正确）
  → 但 _cleanup_expired_rate_limits 用固定 max_window=60s 清理
    → 60s 前的时间戳被全部清除
      → 小时窗口永远只余最近 1 分钟的记录
        → 100/hour 实际退化为 ~100/minute（放宽约 60 倍）
```

**影响版本**: 2.6.0-dev.0 - 2.7.0-dev.4

**修复版本**: 2.7.0-dev.5

**修复内容**: 新增 `_rate_limit_windows: dict[str, int]` 按 store key 记录每路由实际窗口；`_apply_rate_limit` 首次创建条目时写入窗口；`_cleanup_expired_rate_limits` 改为按各 key 自身窗口清理（缺失时回退默认值）；清理删除条目与 `stop()` 时同步维护两个字典。

**修复日期**: 2026/07/31

**回归测试**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**严重性**: 🔴 严重

**类型**: 路由

---

### [BUG-029] 配置监听任务广播半成品 TOML 并静默吞掉异常

**问题**: 用户手动编辑 `config.toml` 保存到一半（产生瞬时的语法错误）时，配置监听后台线程会检测到 mtime 变化、重载配置，但加载失败后仍以空配置 `{}` 发射 `config.updated` 事件，导致适配器/模块的 `on_config_update` 收到空配置、误以为所有配置项被清空而回退默认值。此外监听循环用 `except Exception: pass` 静默吞掉所有异常，watcher 故障无从排查。

**原因**: 两个缺陷叠加：
1. `_load_config` 在 TOML 语法错误/权限错误时把 `self._cache` 擦写为 `{}`，但后台监听线程 `_watch_loop` 与缓存超时路径 `_check_cache_validity` 都在调用 `_load_config()` 后**无条件**执行 `_emit_config_updated()`，把"加载失败产生的空缓存"当作真实变更广播。
2. `_watch_loop` 的 `except Exception: pass` 不记录任何日志。

**根因链路**:
```
用户保存到一半 → TOML 语法错误
  → _load_config() 擦写 _cache = {}
    → _watch_loop 无条件 _emit_config_updated(new_config={})
      → 适配器/模块 on_config_update 收到空配置
        → 误判配置被清空，回退默认值
```

**影响版本**: 2.6.2-dev.1 - 2.7.0-dev.4

**修复版本**: 2.7.0-dev.5

**修复内容**:
1. `_load_config` 改为返回 `bool`；TOML 语法错误/权限/其他错误时**保留上次有效缓存**（不再擦写为 `{}`），仅记录诊断日志并返回 `False`
2. `_watch_loop` 与 `_check_cache_validity` 仅在 `_load_config()` 返回 `True` 时才发射 `config.updated`
3. `_watch_loop` 的 `except Exception` 改为以 warning 级别记录（新增 i18n 键 `core.config.watcher_error`，五语言同步）

**修复日期**: 2026/07/31

**回归测试**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`、`test_permission_denied_logs_clear_message`（更新为验证保留缓存 + 返回 False）

**严重性**: 🟡 中等

**类型**: 配置系统

---

### [BUG-030] 配置 watcher 竞态导致 setConfig 延迟写入静默丢数据

**问题**: 多个用户报告使用 `config.setConfig(key, value)`（默认 `immediate=False`）后，自己的模块配置未写入 `config.toml`，而其它模块的配置正常。设置 `immediate=True`（强制刷盘）可规避。表现为：运行期写入的配置在下次重启后丢失，启动期模板生成的配置保留。

**原因**: 两个叠加缺陷：
1. **逻辑缺陷**：`_watch_loop` 在 `_check_file_change()` 返回 `True` 时无条件 `_dirty_keys.clear()` 丢弃所有待写键。但 `_check_file_change()` 仅用 `!=` 对比 mtime，框架自身的 `_flush_config` 写盘也会改变 mtime——虽然 `_flush_config` 在写盘后更新 `_config_mtime`，但 watcher 线程在文件写入与 mtime 赋值之间（以及粗粒度文件系统上）仍可能观测到 mtime 差值，误判为"外部修改"并清空全部待写键。
2. **线程缺陷**：`_watch_loop` 操作 `_write_timer`/`_dirty_keys` 时未持有 `_lock`，与 `setConfig`（持锁写 `_dirty_keys`）、`_schedule_write`（持锁写 `_write_timer`）存在数据竞争。

**根因链路**:
```
模块A setConfig(immediate=True) → flush 写盘，mtime 变化
  → 用户模块 setConfig(immediate=False) → 进入 _dirty_keys，5s 后刷盘
    → watcher 轮询，_check_file_change 观测到先前自身写入的 mtime 差值
      → _dirty_keys.clear() → 用户模块的待写键被静默丢弃
        → 重启后配置缺失
```

**影响版本**: 2.6.0 - 2.7.0

**修复版本**: 2.7.1

**修复内容**:
1. 新增 `_last_self_write_mtime` 字段，`_flush_config` 写盘后同步记录；`_check_file_change` 在 mtime 变化时先对比该值，匹配则判定为自身写入返回 `False`
2. `_watch_loop` 整段持 `_lock`；真正外部修改时保留 `_dirty_keys`（merge 语义），下次 flush 与外部内容合并（脏键优先），不再 `clear()`
3. `getConfig`/`_check_cache_validity` 路径不受影响（其 reload 本就不清脏键）

**修复日期**: 2026/08/06

**回归测试**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`、`test_external_change_preserves_dirty_keys`、`test_flush_merges_dirty_with_external`

**严重性**: 🔴 严重

**类型**: 配置系统

---

### [BUG-032] 配置延迟刷盘期间「写后立读」读到旧值

**问题**: `config.setConfig()`（默认 `immediate=False` 延迟约 5 秒刷盘）写入点分键后，立即读取其**父级/祖先节点**（如 `set_erispulse_section("scope.actions.MyModule", {...})` 后调用 `get_erispulse_config()`）返回的是旧值，写入的子键"消失"，直到刷盘后才可见。作用域配置热更新等"写-读-写"场景受影响（2.8.0 测试插件 `/t_section` 用例暴露）。

**原因**: `setConfig` 将点分键以**扁平形式**存入待写队列 `_dirty_keys`，仅 `getConfig` 的**精确键查询**命中待写队列；树形路径查询（`getConfig("ErisPulse.scope")`）只走缓存树，不叠加待写值——延迟刷盘（`_flush_config` 才将脏键合并进缓存并清队列）期间形成读-你-写断层。

**影响版本**: 2.6.0 - 2.8.0-dev.1

**修复版本**: 2.8.0-dev.1

**修复内容**: `getConfig` 引入待写叠加语义——① 精确命中待写键直接返回（原有行为不变）；② 待写键是查询键的祖先 → 取最长待写祖先，在其值子树内解析剩余路径；③ 待写键是查询键的后代 → 构建叠加子树（`_dirty_overlay`）与缓存子树深合并（`_deep_merge`，override 优先，不修改原缓存对象）。无待写键时走原快路径，零额外开销。

**修复日期**: 2026/09/04

**回归测试**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`、`test_get_config_overlay_merges_with_cache_siblings`、`test_get_config_overlay_new_branch`、`test_get_config_dirty_ancestor_query`、`test_get_config_dirty_exact_key_still_wins`

**严重性**: 🟡 中等

**类型**: 配置系统

---

### [BUG-033] wait_reply 挂起的回复被高优先级处理器饿死

**问题**: 模块调用 `wait_reply()` 等待用户回复期间，若该回复消息被更高优先级的事件处理器认领（`mark_processed()`），命令分发器在入口看到 `_processed` 标记后直接返回，排在分发器末尾的回复匹配逻辑永远执行不到——等待方收不到回复，只能干等到超时返回 `None`。典型触发场景：使用了高优先级消息处理器（记录/审计/拦截类）的机器人，所有对话式交互随机性失效。

**原因**: 回复匹配 `_check_pending_reply` 挂在 `_handle_message` 末尾（命令未匹配时才执行），而 `_processed` 检查在其之前——认领检查与回复命中判定的顺序颠倒。交互等待是框架级的会话延续机制而非竞争处理器，不应受其他处理器的认领影响。

**影响版本**: 2.2.0-dev.0 - 2.8.0-dev.1

**修复版本**: 2.8.0-dev.2

**修复内容**: 回复命中判定提前至 `_handle_message` 入口（`_processed` 检查之前、仅 message 事件）：先尝试完成挂起的对话，命中后事件被标记已处理、下方检查自然短路；未命中则继续原有命令匹配流程。同时判定链委托新的交互会话管理器（`Core/Event/interaction.py`），顺带获得按归属取消与权限复查能力。

**修复日期**: 2026/09/08

**回归测试**: `tests/unit/test_unit_interaction.py`（`TestRegisterResolve` 命中/未命中/认领标记）、`tests/unit/test_unit_event.py`（wait_reply 全链路）

**严重性**: 🟡 中等

**类型**: 事件系统 / 命令系统


---

### [BUG-034] 作用域 persist=False 运行时绑定被任意后续配置写入静默冲掉

**问题**: `scope.set_module(..., persist=False)` 等运行时写入仅修改内存 `self._data`；但 scope 订阅了 `config.set` / `config.updated` 事件，任意一处代码写配置（如某模块加载时写自己的默认配置）都会触发 scope 从配置文件整体重建配置树，此前所有运行时绑定静默丢失（判定回退为默认放行），且无任何日志提示。依赖运行时绑定的场景（Dashboard"仅运行时"开关、模块运行期动态禁用）在无关模块写配置后行为回退。

**原因**: 根因链路：`scope.set/delete(persist=False)` 仅写内存（`Core/scope.py`）→ 任意 `setConfig` 触发 `config.set` 事件 → `_on_config_updated` 无条件 `_load_config()` → `_apply_tree()` 以 `self._data = {...}` 整体替换 → 不在配置文件中的运行时绑定被丢弃。

**影响版本**: 2.8.0-dev.1 - 2.8.0-dev.2
**修复版本**: 2.8.0-dev.2
**修复内容**: 引入运行时覆盖层 `_runtime_overrides`（含删除哨兵）：`persist=False` 写/删记录进覆盖层，`_apply_tree()` 重建持久层后按写入顺序重放，运行时规则在任意配置写入后保持有效；`persist=True` 写/删清除对应覆盖记录（用户持久化语义优先）；`config.set` 按事件 key 精确过滤、`config.updated` 对比新旧 scope 节，仅 scope 实际变化时才重建（附带避免无关写入冲刷判定 LRU 缓存）；新增 `unregister_by_owner()` 供模块卸载时随调用方兜底清理。`Core.Event.overrides` 的 persist=False 运行时覆写存在同类问题，同步以覆盖层架构修复。
**修复日期**: 2026/09/09

**复现步骤**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` → 判定 False；② 任意模块执行 `config.setConfig("HelpModule", {...})` → 触发 scope 重建；③ `scope.is_allowed("testplat", None, "TestB")` 返回 True（预期仍为 False）。
**关联**: Issue #432
**回归测试**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival`（无关写入存活/树重建重放/删除哨兵/持久化清除/精确失效/owner 清理）

**严重性**: 🟡 中等
**类型**: 配置系统 / 运行时

---

### [BUG-035] 配置面板 select 选项与字典字段渲染为 [object Object]

**问题**: WebUI 配置面板中，select 字段的选项下拉显示 `[object Object]`（如动态生成的配色风格选项）；未声明控件类型的 dict 字段（如 `stalker_mode`、`knowledge_base` 等嵌套配置段）在文本框中显示 `[object Object]`，无法正常查看与编辑。

**原因**: 两处独立缺陷：① 框架 i18n 解析器 `_resolve_i18n_text` 仅还原带 `i18n` 键的字典，选项标签为仅含 `default` 的字典（无 i18n 键的动态文本）时原样透传，前端 `esc(label)` 字符串强转得到 `[object Object]`；② Dashboard 渲染分支只对 array 类型做 JSON textarea，dict 值落入纯文本输入分支被 `String()` 强转。此外模块若将 `_schema_meta` 误声明为普通 dataclass 字段（缺 `ClassVar` 注解），会作为配置字段进入 schema 加剧混乱。

**影响版本**: 2.7.0 - 2.8.0-dev.2
**修复版本**: 2.8.0-dev.2
**修复内容**: ① `_resolve_i18n_text` 支持仅含 `default` 的字典还原为文本；② 框架 schema/模板/默认值/填充/校验五处一律排除下划线前缀字段（误声明无害化）；③ Dashboard select 选项 label 对象兜底解析（`default` 优先）、dict/table 字段渲染为 JSON textarea（保存路径按 `tp=object` JSON.parse 回写，完整往返）。
**修复日期**: 2026/09/09

**回归测试**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`、`TestSchemaUnderscoreFieldExclusion`

**严重性**: 🟡 中等
**类型**: 配置系统

---

### [BUG-036] 多实例共享配置目录时配置写入偶发失败（ENOENT）

**问题**: Docker 部署场景下（多容器挂载同一宿主机配置目录），日志偶发连续两条 `Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'`。该次配置写入被丢弃（旧配置完整保留，未观察到配置丢失），功能不受影响，但告警反复出现干扰排查，且待写入的配置项需等待下次写入才能落盘。

**原因**: 根因链路：`_flush_config` / `setConfigTemplate` 使用**固定名**临时文件 `config.toml.tmp` 承载新内容，`write()` 后不 `fsync` 直接 `rename()`。两个 ErisPulse 实例共享同一配置目录时，B 实例 `open("w")` 可能 **truncate** A 实例正在写的临时文件 → A rename 时目标已被 B 取走或内容被截断，报 ENOENT（即用户日志中的连续两条错误）。已报告案例中仅表现为写入失败告警（旧配置保留）；若交错时序更极端，rename 可能输出空/半截的 `config.toml`（属潜在风险，尚未在真实环境爆发）。单实例场景下 ext4 延迟分配同样存在「rename 元数据先于数据块落盘」的崩溃窗口（SIGKILL / 断电）。`_file_lock` 为进程内 `threading.RLock`，对跨进程/跨容器写入无约束。

**影响版本**: 2.2.0-dev.0 - 2.8.0

**修复版本**: 2.8.1

**修复内容**: 配置写入统一收敛到 `_atomic_write_text()`：同目录 `mkstemp` 生成进程唯一临时文件（消除固定名争抢，多实例下退化为 last-writer-wins，不再 ENOENT）→ 写毕 `flush + fsync` 强制数据落盘（消除「rename 已生效、数据未落盘」窗口）→ `os.replace` 原子替换目标（POSIX/Windows 均原子，任一时刻磁盘上要么完整旧内容、要么完整新内容）；POSIX 下额外 fsync 配置目录。`_flush_config`、`setConfigTemplate`、根目录配置迁移三处写入点全部切换；异常路径清理逻辑随唯一临时文件名重构。新增**多实例检测**：启动时 advisory lock（POSIX `flock` / Windows `msvcrt.locking`）独占持有配置目录锁文件 `.erispulse_config.lock`，被占用即输出 i18n 告警（不阻塞启动），锁由 OS 在进程退出时自动释放、无幽灵锁。

**修复日期**: 2026/09/13

**复现步骤**: ① 两个容器挂载同一宿主机 `config/` 目录并同时运行 ErisPulse；② 任一实例触发配置写入（如模块注册默认配置）；③ 观察日志出现 ENOENT 写失败告警，本次写入被丢弃（旧配置保留）。

**关联**: 用户报告（1Panel 容器 ×2）

**回归测试**: `tests/unit/test_unit_config_atomic_write.py`（内容完整写入/无临时文件残留/写失败保原文件/双实例并发写入文件始终合法/锁文件创建/多实例告警/迁移原子写入）

**严重性**: 🟢 轻微

**类型**: 配置系统

---

### [BUG-037] 空格子命令名注册后永远无法被触发

**问题**: 以空格分隔的多 token 命令名注册子命令（如 `@command("admin add")`）后，命令可正常注册并出现在帮助列表中，但用户发送 `/admin add` 时机器人永远无响应——输入被父 token 命令匹配为 `admin` + 参数 `["add"]`；若父 token 也未注册则完全无响应。仅当使用点分命名（`admin.reload`，整体为单 token）时可规避。

**原因**: 根因链路：`CommandHandler.__call__` 将任意命令名（含空格形式）原样存入平铺的 `self.commands` 字典 → 分发阶段 `_try_execute_command` 仅取消息首 token 匹配（`cmd_name = parts[0]`）→ 多 token 命令名作为字典键永远查不到。注册与匹配两阶段对命令名的空间假设不一致，且无任何注册期告警（静默失效）。

**影响版本**: 引入命令系统起 - 2.8.0

**修复版本**: 2.8.1

**修复内容**: 匹配层改为**最长前缀匹配**：从最长候选（`" ".join(parts[:n])`，n 上限为已注册命令名/别名的最大 token 数缓存 `_max_name_tokens`）逐级降级尝试，命中即以剩余 token 为参数执行，下游作用域/ACL/覆写/master/权限链对命令全名自然生效。配套语义：父子并存时未注册的子命令输入回落父命令（历史行为不变）；子命令未声明 `permission` 时沿父链继承最近声明权限的祖先命令（保护父命令即保护其下全部子命令）；仅注册单 token 命令时首轮即命中，分发开销与原先一致。`unregister` / `unregister_by_owner` / 全量清理同步维护 token 数缓存。

**修复日期**: 2026/09/13

**复现步骤**: ① 模块内 `@command("admin add")` 注册；② 发送 `/admin add x`；③ 修复前无响应（或被同时注册的 `/admin` 以参数形式接住），修复后 `admin add` 触发且 `get_command_args()` 为 `["x"]`。

**回归测试**: `tests/unit/test_unit_command_subcommand.py`（最长前缀匹配/仅子命令触发/三级嵌套/大小写敏感两模式/单与多 token 别名/事件载荷全名/生命周期钩子全名/权限继承六例/ACL glob 全名/master/注销回落与缓存重算）

**严重性**: 🟡 中等

**类型**: 事件系统

---

### [BUG-038] persist=False 运行时绑定被持久化写入顺带落盘，模块卸载后从磁盘"复活"

**问题**: 以 `scope.set(path, value, persist=False)` 写入的运行时绑定（文档承诺不落盘、进程重启即失效、模块卸载时清理）会随任意一次无关的 `persist=True` 写入（默认值，如模块 `set_module` / WebUI 保存配置）被差量写入用户 `config.toml`；此后即使模块卸载注销了运行时绑定，下次配置重载时该绑定仍从磁盘"复活"继续生效、进程重启后依然存在——与"运行时绑定不落盘"的语义契约相反，且极难排查。

**原因**: 根因链路：`ScopeManager.set()` 先把值写入内存配置树 `_data`（运行时绑定同样直接写入 `_data`）→ 持久化分支对**整棵 `_data`** 做深拷贝快照提交给 `update_erispulse_config` 差量落盘 → 快照中混入了 `persist=False` 绑定的值。`delete(persist=True)` 同源：把 `_data` 的活引用（`parent` 节点）交给延迟写脏队列，延迟刷盘期间对该节点下兄弟键的运行时修改会被一并落盘，且活引用在脏队列滞留期间存在跨写污染窗口。

**影响版本**: 2.8.0-dev.2 - 2.9.0-dev.0

**修复版本**: 2.9.0-dev.2

**修复内容**: 引入持久化基线 `_persisted_tree`（配置树重建时以磁盘加载、校验后的树刷新）作为磁盘真相镜像：`set(persist=True)` 只在基线上应用本次变更后提交差量，运行时绑定永不进入持久化内容；"写后立读"改用内存最终态快照直接恢复，不再经 `_apply_tree` 重建以免污染基线。`delete(persist=True)` 同口径：在基线上应用删除并把基线子树的深拷贝交给持久化层；`set_action` 整体替换语义先按同口径删除再写入，旧规则键不残留在持久化内容中。

**修复日期**: 2026/09/27

**复现步骤**: ① 模块内执行 `scope.set("bots.p.debug_mode", {"blocked": ["X"]}, persist=False)`；② 触发任意持久化写入（如另一模块调用 `set_module`）；③ 打开 `config/config.toml`，可见 `debug_mode` 已被写入（修复前）；④ 卸载该模块（运行时绑定被注销）后触发配置重载，`scope.get("bots.p.debug_mode")` 仍返回绑定值。

**回归测试**: `tests/unit/test_unit_scope.py::TestPersistBaseline`（运行时绑定不随无关持久化写入落盘 / 卸载注销后配置重载不复活 / delete 提交基线子树不带运行时兄弟键 / set_action 替换不留残留键 / cache_size 配置生效）

**严重性**: 🔴 严重

**类型**: 配置系统

---

### [BUG-039] 整节写与点分写并存时读写不一致（点分覆写丢失）

**问题**: 延迟刷盘窗口内，同节并存整节写（`setConfig("Mod", {...})`，如 `BaseModule.cfg` 写回）与点分写（`setConfig("Mod.key", v)`，如配置热更 / 测试工具覆写）时有两个变体：变体 A（读路径）——`getConfig("Mod")` 整节读取返回旧整节待写快照，看不到更晚的点分覆写（点分读取路径正常）；变体 B（写路径，更重）——点分写在前、整节写在后（测试工具注入覆写 → 模块 `self.cfg = ...` 写回的常见时序）时，flush 按插入序应用脏键，整节写整体替换该节，**点分覆写在磁盘上永久丢失**。生产环境"配置热更 + 模块运行时写回"组合即可触发，与测试环境无关（ErisPulse-DailyCard 测试反馈暴露）。

**原因**: `getConfig` 第①段（精确命中 `_dirty_keys`）提前 `return self._dirty_keys[key]`，完全绕过第④段 `_dirty_overlay` 后代叠加；`_flush_config` 按 `_dirty_keys` 插入序应用脏键，整节写恰好排在点分写之后时点分值被整体替换。另：第①段返回脏队列**原对象引用**，调用方原地修改返回 dict 会直接改动待落盘状态。

**影响版本**: 2.6.0 - 2.9.0-dev.2

**修复版本**: 2.9.0-dev.2

**修复内容**: 脏窗口内统一为**特异性优先**语义——点分（更具体）待写值优先于整节（较宽）待写值，读路径与落盘路径同口径：① `getConfig` 精确命中待写键后仍叠加 `_dirty_overlay` 后代待写值（非 dict 值返回叠加子树，与③+④标量边角同口径）；② `_flush_config` 脏键按路径深度排序应用（整节/祖先先、点分/后代后，稳定排序保持同深度写入时序）。代价：同一脏窗口内（约 5 秒）整节写回无法覆盖仍挂起的点分写——读路径修复后读-改-写自然携带点分值，实际影响面极小。③ 涉及待写值的 `getConfig` 返回（精确命中 / 祖先子树 / 叠加合并）改为 `copy.deepcopy` 隔离拷贝，不再泄漏脏队列内部引用；无脏键快路径与纯缓存读行为不变。

**修复日期**: 2026/09/28

**复现步骤**: ① `setConfig("FB.y", 1)`；② `setConfig("FB", {"z": 2})`；③ `force_save()`——修复前磁盘只剩 `[FB] z = 2`（y 丢失），修复后 `{"y": 1, "z": 2}`；变体 A：步骤①②后不落盘直接 `getConfig("FB")`——修复前不含 `y`，修复后可见。

**回归测试**: `tests/unit/test_unit_config.py::TestSectionAndDottedDirtyConsistency`（变体 A 两种插入序 / 变体 B 落盘与顺序无关 / 三层混合存活 / 隔离拷贝 / 祖先子树隔离）

**严重性**: 🟡 中等

**类型**: 配置系统


### [BUG-040] 平台切段消息的命令尾部参数静默丢失

**问题**: 平台把一条消息切成多个 text 段（如 `/kick` 与参数之间夹着 mention 段、或输入法分段）时，命令分发只取第一个 text 段做匹配——`/艾特 @xxx 123` 解析为无参数的 `艾特`，声明了 `args=` 的命令直接报"参数缺失"，且无任何留痕。
**原因**: `command.py` 的文本提取循环取到首个 `type=="text"` 段后 `break`，其余段（含全部非文本段）被丢弃。
**影响版本**: 2.6.0（命令分发引入）- 2.10.0
**修复版本**: 2.10.1-dev.0
**修复内容**: 命令文本改为按段顺序收集全部 text 段空格拼接；mention/图片夹层不再导致命令整体无法解析；同步补齐畸形段容错（`message` 为 None/字符串/非 dict 段不再击穿分发器）。
**回归测试**: tests/unit/test_unit_command_multiseg.py

**严重性**: 🟡 中等
**类型**: 事件系统

### [BUG-041] 被拒绝命令经 alt_message 整链重跑：重复回复与权限函数副作用双触发

**问题**: 适配器的 `alt_message` 与消息段文本不一致时（如 alt 含 @文本前缀），命中命令被 scope/ACL/master/permission 拒绝后，分发器用 alt_message 把整条链重跑一遍——用户收到两条"权限不足"回复，自定义权限函数（常带查库/计数副作用）被调用两次。
**原因**: 拒绝路径 `return False` 与"未命中命令"共用同一返回值，分发器据此认为可尝试 alt 兜底；而事件在拒绝前已被认领，重跑仅多执行了回复与权限判定。
**影响版本**: 2.9.0（治理/权限链成形）- 2.10.0
**修复版本**: 2.10.1-dev.0
**修复内容**: 文本处理改三态契约（unmatched/consumed/rejected）——命中注册命令后（无论拒绝与否）不再 alt 回退；仅未命中任何命令时保持 alt 兜底。
**回归测试**: tests/unit/test_unit_command_multiseg.py::test_denied_command_not_rerun_via_alt

**严重性**: 🟡 中等
**类型**: 事件系统

### [BUG-042] 命令处理器内注册的 wait_reply 被同一条触发消息立即消费

**问题**: 命令执行体内调用 `wait_reply` / 注册交互等待时，等待被同一条命令消息立即命中——交互流首问被跳过，"用户回复"实为命令文本本身（答非所问/数据污染）。
**原因**: `_handle_message` 在方法开头与结尾各调用一次 `interaction.resolve`，命令执行后结尾的二次 resolve 会命中执行期间新注册的等待；cmdpass 关闭时 alt 缺失场景判定为空串直接放行，加重了该问题。
**影响版本**: 2.8.0（交互会话系统引入）- 2.10.0
**修复版本**: 2.10.1-dev.0
**修复内容**: 分发链收敛为单次 `interaction.resolve`（方法开头处），删除结尾二次调用；等待统一由下一条消息消费。
**回归测试**: tests/unit/test_unit_command_multiseg.py::test_wait_reply_not_consumed_by_command_trigger

**严重性**: 🟡 中等
**类型**: 事件系统

### [BUG-043] select() 同键多路等待后者静默取消前者

**问题**: `event.select()` 的多条期望推导出同一会话键（同 user 不同 pattern、多条 session 期望等）时，后注册路把先注册路以"冲突"取消，select 直接抛 `InteractionCancelled` 而非文档承诺的超时返回 `(None, None)`。
**原因**: 每路独立调用 `interaction.register`，其互斥语义对同键旧等待发 `REASON_CONFLICT` 取消；注释声称"同 user 多路因事件副本独立互不冲突"不成立——副本只改 user_id，同 user 多路的键完全相同。
**影响版本**: 2.9.0（select 引入）- 2.10.0
**修复版本**: 2.10.1-dev.0
**修复内容**: select 改为聚合等待——全部期望合并为自定义 matcher 的单条目（按键集合登记、共享同一 future），任一路命中即返回对应下标；同键多路天然共存。
**回归测试**: tests/unit/test_unit_command_multiseg.py::test_select_same_user_multi_branch

**严重性**: 🟡 中等
**类型**: 事件系统

### [BUG-044] BaseConverter.at() 产出 OB11 遗留 "at" 段，全框架 mention 判定不识别

**问题**: 适配器用 `BaseConverter.at()` 组装入站事件时，`must_at_bot` / `has_mention()` / `on_at_message` 全部失明——@机器人命令在群里静默失效。
**原因**: `at()` 产出 `{"type": "at"}`（OB11 形态），而框架全部 mention 判定与构建侧（MessageBuilder/发送修饰器）均为 OB12 的 `"mention"`，双轨并存且无任何告警。
**影响版本**: 引入版本不早于 2.5.0 - 2.10.0
**修复版本**: 2.10.1-dev.0
**修复内容**: `at()` 改产 `{"type": "mention", "data": {"user_id": ...}}`（方法名保留别名，新增 `mention` 别名）。
**回归测试**: tests/unit/test_unit_command_multiseg.py::test_converter_at_produces_mention

**严重性**: 🟡 中等
**类型**: 适配器

### [BUG-045] 无 alt_message 的适配器上交互原语永久超时、命令穿透失效

**问题**: 适配器只填 message 段不填 `alt_message` 时：`confirm` / `choose` / `collect` 对用户明文回复（如"是"）永久等待；等待期间的已注册命令永远无法穿透执行；`Event.get_text()` 返回空串导致脚手架示例静默失效。
**原因**: 上述路径全部直取 `alt_message` 字符串、无消息段回退——框架"alt_message 为适配器可选字段"的契约下，仅段填充是合法形态。
**影响版本**: 各交互原语引入版本 - 2.10.0
**修复版本**: 2.10.1-dev.0
**修复内容**: 统一走 `alt_message` 优先 + text 段回退的 `extract_text` 口径（交互原语五处取值/校验点、cmdpass 判定、`Event.get_text()/get_message_text()`）。
**回归测试**: tests/unit/test_unit_command_multiseg.py

**严重性**: 🟡 中等
**类型**: 事件系统

### [BUG-046] 声明式配置模板的嵌套子表头漂移为顶层表

**问题**: 嵌套 dataclass 声明的配置（ConfigClass 内嵌 dataclass 字段）首次生成配置模板时，子表头 `[Nested]` 落在文件顶层而非组件节内——适配器读 `cfg.嵌套字段` 拿不到值；`config.full.example` 中同样错位。
**原因**: 模板生成器对嵌套 dataclass 渲染相对表头（`[Nested]`），而 TOML 表头语义是从根算起的绝对路径；`setConfigTemplate` 旧实现把解析后的表对象搬进组件节、`full.example` 直接文本拼装，两条路径都未把相对表头重锚到组件路径下。
**影响版本**: 2.10.0 - 2.10.1（嵌套 dataclass 模板渲染随该版本引入）
**修复版本**: 2.10.2
**修复内容**: `setConfigTemplate` 按模板解析出的子表路径集合精确重锚表头（`[Nested]` → `[组件名.Nested]`）；`config.full.example` 生成侧改传 `_prefix` 直接产出绝对表头。
**回归测试**: tests/unit/test_unit_config.py::TestTomlclassEngineMigration::test_template_write_idempotent_and_nested_anchored

**严重性**: 🟡 中等
**类型**: 配置系统 / 适配器

---

### [BUG-047] 服务目录全量枚举漏掉懒加载模块

**问题**: `sdk.module.services()` 全量目录对未实例化（懒加载）模块一律跳过——模块声明了 `meta.services` 也不出现在目录中，以目录为发现入口的消费方（AI 智能体、help 模块等）无法发现其服务；单模块精确查询 `services("Name")` 与拓扑 `get_topology()` 不受影响。
**原因**: `ModuleManager.services()` 全量枚举分支对无契约缓存（未加载）的模块在**现场解析契约之后**仍无条件 `continue`——本意是跳过"未声明服务的模块"，实际把未加载模块整体跳过了；已加载模块因加载时写入契约缓存不受影响。
**影响版本**: 2.9.0 - 2.10.1（模块 RPC 与服务目录随 2.9.0 引入）
**修复版本**: 2.10.2
**修复内容**: 删除无条件跳过，统一由"解析结果为空才跳过"裁决；未加载模块现场解析 `get_meta().services`（与 `module.call()` 白名单同口径），声明了服务的照常进入目录。
**回归测试**: tests/unit/test_unit_module_rpc.py::TestServicesDirectory::test_lazy_declared_module_in_full_directory

**严重性**: 🟡 中等
**类型**: 加载系统

### [BUG-048] 会话收件箱查询 API 丢失消息归因（sender 与事件元数据）

**问题**: 收件箱所有查询接口（`get()` / `get_by_trace()` / `event.history()`）返回的记录只有 `role/text/ts/event_id`——存储层已存在的 `sender` 列被查询层丢弃，群聊回放时不同成员的消息在 API 层不可区分（AI 把成员 B 误认为上一轮对话者 A）；入站记录同时不归档事件时刻的昵称等元数据，事后反查拿到的是"现在的昵称"而非"当时的昵称"。
**原因**: 2.8.0 加 `sender` 列时的注释即写明用于"回放时还原消息来源"，但 Select 与返回构造均未携带（实现疏漏）；元数据归档则从未设计——`append()` 无 meta 通道，表结构无对应列。
**影响版本**: 2.8.0 - 2.11.0（sender 列随 2.8.0 引入）
**修复版本**: 2.11.1-dev.0
**修复内容**: 新增 `meta` 列（白名单契约：入站 nickname/self_id/sub_type/message_id，出站发送上下文与 module；旧表自动迁移，后端不支持 ALTER 时静默回退 `{}`）；`append()` 增加 `meta` 参数贯穿内存缓冲与批量落盘；`get` / `recent` / `get_by_trace` / `event.history` 统一返回 `sender` + `meta`（JSON 损坏回退 `{}`）。
**关联**: #467（同批 #468 / #469 / #470）
**回归测试**: tests/unit/test_unit_transcript_attribution.py::TestSenderMetaReadback / TestMetaMigration

**严重性**: 🟡 中等
**类型**: 会话收件箱 / 存储系统

### [BUG-049] 入站 bot 自发消息回声被记为 user，污染收件箱归因

**问题**: 开启消息回显的平台/协议端（OneBot v11 `report-self-message`、Telegram outgoing 等）把 bot 自己发的消息以 message 事件上报时，收件箱一律记 `role="user"`——机器人自发言与真实用户输入不可区分，下游模块把 bot 自发言当成用户输入处理（AI 据此回应"用户"说过的话），role 统计失真。
**原因**: 入站自动记录点（`Core/adapter.py`）对所有 `event_type == "message"` 无条件记 `role="user"`，未消费 `self` 字段做 bot 回声判定——而紧随其后的 bot 自动发现逻辑已在消费同一字段（记录时刻可用，记录逻辑漏用）。
**影响版本**: 2.8.0 - 2.11.0（收件箱自动记录随 2.8.0 引入）
**修复版本**: 2.11.1-dev.0
**修复内容**: 记录前按 `self.user_id == user_id` 识别回声，按新配置 `ErisPulse.transcript.self_echo` 三模式处理：`"bot"`（默认）记 `role="bot"` + `sender=self_id` + `meta.self_echo=true`；`"skip"` 不记录；`"user"` 保持旧行为。非回显平台（self 缺失或不相等）逐字段回归不变。
**关联**: #470（依赖 #467 的 meta 列承载 self_echo 标记）
**回归测试**: tests/unit/test_unit_transcript_attribution.py::TestSelfEcho

**严重性**: 🟡 中等
**类型**: 适配器 / 会话收件箱
