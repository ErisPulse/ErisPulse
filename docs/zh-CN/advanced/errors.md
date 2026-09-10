# 异常体系与捕获指南

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
└── StrictModeError                 # 严格模式致命违规（中止启动流程，loaders/strict）
```

## 结构化属性

捕获异常后可读取结构化属性（无需解析消息文本）：

| 异常 | 属性 |
|------|------|
| `ClientError`（含子类） | `.url` 请求 URL、`.method` 请求方法、`.attempts` 已尝试次数（重试耗尽时） |
| `HTTPStatusError` | `.status` 状态码、`.message` 响应消息 |
| `WebSocketDisconnect` | `.code` 关闭码、`.reason` 关闭原因 |
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
