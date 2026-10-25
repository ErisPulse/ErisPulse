---
name: erispulse-communication
description: "适用于：模块间通信（RPC/定向/广播）、HTTP/WS 客户端、连接管理。覆盖场景：需要跨模块调用（RPC）、服务契约、定向事件或冷启动回放时。需要 WebSocket/SSE 连接池、广播分组、跨模块推送或查看连接时。需要出站 HTTP / WebSocket 请求时。需要 HTTP / WebSocket / SSE 路由（含连接池广播）时。"
---

# ErisPulse 通信与连接

本技能由 ErisPulse 文档自动构建（generate-skills.py）。
仓库：https://github.com/ErisPulse/ErisPulse
各节末尾标注了来源文档路径，需要最新内容请以仓库 docs/zh-CN/ 为准。

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 模块间通信: 68-97 行
- RPC：module.call: 99-126 行
- 服务契约：meta.services: 128-196 行
- 服务目录：services(): 198-220 行
- 出站审计：谁能调用谁: 222-236 行
- 定向事件：lifecycle.emit 的 to 参数: 238-269 行
- 懒加载与调用: 271-282 行
- 冷启动回放: 284-315 行
- 事件幂等去重: 317-327 行
- 连接管理: 329-350 行
- 概述: 352-378 行
- 查看连接池: 380-404 行
- 广播与订阅: 406-469 行
- 跨模块传递 / 复用: 471-496 行
- 出站连接（Client 侧）: 498-512 行
- 跨线程投递: 514-529 行
- 卸载与清理语义: 531-539 行
- API 一览: 541-555 行
- HTTP 客户端: 557-567 行
- 概述: 569-580 行
- 快速开始: 582-629 行
- HttpResponse: 631-652 行
- 请求方法: 654-737 行
- 参数说明: 739-760 行
- 超时与重试: 762-780 行
- 自定义默认头: 782-792 行
- 请求统计: 794-805 行
- 生命周期事件: 807-831 行
- 上下文管理: 833-840 行
- WebSocket 客户端: 842-949 行
- 异常体系: 951-1027 行
- 适配器中使用: 1029-1052 行
- 最佳实践: 1054-1062 行
- 路由: 1064-1074 行
- 概述: 1076-1091 行
- 抽象类型: 1093-1105 行
- 装饰器路由（推荐）: 1107-1226 行
- 传统注册方式: 1228-1293 行
- WebSocket 生命周期钩子: 1295-1317 行
- 路由分组: 1319-1334 行
- 路由中间件: 1336-1351 行
- 请求关联 ID（X-Request-ID）: 1353-1376 行
- 速率限制: 1378-1392 行
- CORS 配置: 1394-1411 行
- 安全头: 1413-1426 行
- 自动文档: 1428-1442 行
- 路径处理: 1444-1455 行
- 系统路由: 1457-1476 行
- 主页入口: 1478-1515 行
- 生命周期集成: 1517-1529 行
- 最佳实践: 1531-1540 行

## 模块间通信

> 来源: `docs/zh-CN/advanced/module-communication.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/advanced/module-communication.md）

# 模块间通信

> [!TIP]
> **什么时候需要读这篇**：需要跨模块调用（RPC）、服务契约、定向事件或冷启动回放时。不需要则跳过，不影响其它功能的使用。

> **读完你会知道**：三层通信模型（RPC / 定向事件 / 广播）的选型口诀、
> `meta.services` 服务契约与服务目录、出站审计的配置方式、懒唤醒与冷启动回放。
>
> **本篇不涉及**：生命周期事件系统本身的注册 / 触发 / 优先级机制
> （见[生命周期管理](lifecycle.md)）；懒加载的配置与 activate_on 声明
> （见[懒加载系统](lazy-loading.md)）。

> [!NOTE]
> 本章内容需要 ErisPulse **2.8.0+**。

ErisPulse 的模块之间有**三层通信模型**，按"点对点 → 定向 → 广播"排列：

| 层 | API | 语义 | 典型场景 |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | 点对点请求-响应，带契约 / 审计 / 超时 | 调用另一模块的能力（查历史、翻译、退款） |
| **定向事件** | `await lifecycle.emit("message_received", {...}, to="Chat")` | 仅分发给指定模块注册的生命周期钩子 | 上游状态变化通知下游（"收到新消息了"） |
| **广播** | `await lifecycle.emit("config.updated", {...})` | 全框架可见的生命周期事件 | 配置热更新、模块上下线 |

{!--< tips >!--}
选型口诀：**要返回值用 `call`，只通知一个模块的钩子用 `emit(..., to=...)`，通知所有人用 `emit(...)`**。
{!--< /tips >!--}

## RPC：module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

与裸属性访问 `sdk.module.Chat.get_history(...)`（保留不变）的差异：

| | `module.call()` | 裸属性访问 |
|---|---|---|
| 目标未注册 / 未启用 | 抛 `ModuleNotAvailableError` | 抛 `AttributeError` |
| 懒加载模块 | **自动唤醒**（事件驱动模块走激活锁） | 异步初始化模块抛 RuntimeError |
| `current_owner` | 归因到**目标模块**（其内部 wait_reply / 发送 / 日志正确归属） | 保持调用方 |
| 超时 | 默认 30 秒（`timeout=` 覆盖，None 不限时） | 无 |
| scope 审计 | 调用方过出站闸口 `actions.<调用方>.call` | 无 |
| 契约校验 | `meta.services` 白名单 | 无 |

### 异常体系

```
ModuleError                      # 模块系统异常基类
└── ModuleCallError              # 跨模块调用基类（含 module / method 属性）
    ├── ModuleNotAvailableError  # 目标未注册 / 未启用 / 唤醒失败
    ├── ServiceNotProvidedError  # 方法不在 services 白名单 / 私有方法 / 不存在
    └── ModuleCallTimeoutError   # 协程方法超时
```

均挂在 `ErisPulseError` 体系下，可 `from ErisPulse.Core import ModuleCallError` 捕获。

## 服务契约：meta.services

服务方在 `get_meta()` 声明对外提供的白名单（与 `commands` 字段对称）：

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="聊天",
            services=[
                "get_history",                                       # 简单形态
                {"name": "translate", "description": "把文本翻译成指定语言"},  # 带介绍
            ],
        )

    async def get_history(self, session_id, n=20): ...
    async def translate(self, text, target_lang): ...
    def _internal_helper(self): ...   # 下划线方法始终禁止被外部调用
```

**开发者无感是默认**：

- 未声明 `services` → 所有**公开**方法天然可被 `module.call()` 调用（与裸属性访问一致），
  无需任何声明
- 声明后 → 收紧为白名单，越界调用抛 `ServiceNotProvidedError`——用于标记
  "这些方法才是对外承诺"
- 限制的**主控制权在用户侧**：`scope.actions` 配置决定"谁能调用谁"（见下文审计），
  模块作者的 `services` 只是服务面声明，两层互不替代

**服务介绍**：给每个服务配上人类 / AI 可读的描述——不需要就什么都不写，
介绍自动取**方法 docstring 首行**（框架本就要求 docstring 风格）：

```python
async def translate(self, text, target_lang):
    """把文本翻译成指定语言"""    # ← 这一行自动成为服务介绍
    ...
```

**参数提示**：调用方（尤其是 AI 智能体）需要知道每个参数的含义。不需要就什么都不写，
提示自动取方法 docstring 的 **`:param:` 行**：

```python
async def render_card(self, html, width=800, height=0):
    """渲染 HTML 为图片文件

    :param html: 要渲染的 HTML 文本          ← 自动成为参数提示
    :param width: 画布宽度像素，0 为按内容自适应
    :param height: 画布高度像素，0 为按内容自适应
    """
```

需要精细控制（覆盖 docstring / 多语言）时用 dict 形态声明 description 与 parameters
（均支持 i18n 字典；`parameters` 按**参数**与 docstring 合并，单参数内显式声明优先，
声明了签名中不存在的参数会被过滤）：

```python
services=[
    {"name": "translate", "description": "把文本翻译成指定语言"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "摘要对话"}},
    {
        "name": "render_card",
        "description": "渲染 HTML 为图片文件",
        "parameters": {"html": "HTML 文本", "width": "宽度像素，0 为自适应"},
    },
]
```

## 服务目录：services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': '把文本翻译成指定语言',
#            'parameters': {'session_id': '会话 ID', 'n': '返回条数'}}]}

sdk.module.services("Chat")   # 仅查询指定模块
```

- 只列出**显式声明** `meta.services` 的模块（未声明模块不出现在目录中）
- 每个服务带方法签名字符串（`inspect.signature` 提取）、介绍文本与参数提示
- **懒加载模块同样进入目录**（服务发现先于加载发生）——调用方可据此决定是否
  `call()` 唤醒目标模块
- 同时进入拓扑：`sdk.module.get_topology()` 的各模块条目带 `services` 字段

{!--< tips >!--}
**MCP 化路线**：服务目录（名称 + 签名 + 描述 + 参数提示）即 MCP tool 的形状——
每个服务天然长成 ``{"name", "description", "parameters"}``。
未来框架可把 ``services()`` 直接暴露为 MCP server 端点，让 AI 发现并调用模块能力；
``scope.actions.call`` 审计天然成为 AI 调用的安全闸口。
{!--< /tips >!--}

## 出站审计：谁能调用谁

每次 `module.call()` 都以**调用方模块**的身份过 scope 出站闸口：

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # 禁止 CallerModule 调 Chat 的 get_history
# allow = ["Chat.get_*"]           # 或白名单：只允许调 Chat 的 get 开头服务
```

- `name` 格式为 `<目标模块>.<方法名>`，支持精确 / glob / `re:` 正则
- 框架层调用（无 owner 上下文，如启动脚本）不受审计约束
- 被拒调用抛 `ModuleCallError`（TRACE 日志 `core.module.call_denied`）

配置方式详见 [作用域（scope）](scope.md)的出站维度。

## 定向事件：lifecycle.emit 的 to 参数

生命周期事件支持定向传播：`to` 指定目标拥有者（owner）后，事件只分发给以该
owner 身份注册的钩子（模块在 `on_load` 内注册的钩子自动归属本模块），
其它模块与通配符 `*` 处理器不感知。

```python
from ErisPulse.Core.lifecycle import lifecycle

# 投递方：事件只投给 Chat 模块注册的钩子
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# 订阅方（Chat 模块内）：注册同名钩子，owner 在注册时自动记录
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # 点式父级前缀同样生效（按 owner 过滤）
async def on_any(data): ...
```

语义细节：

- 目标 owner 无已注册钩子 → 事件**静默丢弃**（**不发往不存在的地方**），
  可用 `lifecycle.has_handlers("message_received")` 提前探测
- `data` 为 dict 时自动携带 `_trace_id`（不覆盖已有值），与全链路追踪打通
- 广播与定向共用一套钩子注册：`emit(...)` 不带 `to` 即全框架广播，
  带 `to` 则同一事件只对目标模块可见
- `emit_sync` / `submit_event`（兼容 API）同样支持 `to=` 参数

> [!NOTE]
> 定向事件是轻量通知，**不做目标校验与懒唤醒**；需要目标存在性校验、
> 契约审计或返回值时，改用 [RPC：module.call](#rpcmodulecall)。

## 懒加载与调用

`module.call()` 对懒加载模块是**透明唤醒**：

- 事件驱动懒模块（`activate_on` 声明）→ 走激活锁 `_activate()`，激活后触发器 stub 自动注销
- 普通懒模块 → 同步初始化或常规加载路径（幂等）
- 唤醒失败 → `ModuleNotAvailableError`

即：**调用方不需要关心目标模块是否已加载**，也无需为唤醒它而等待某条事件。

定向事件（`lifecycle.emit(..., to=...)`）不做懒唤醒——目标未加载即无钩子，
事件静默丢弃；需要确保送达时改用 `module.call()`。

## 冷启动回放

新装 / 重启的模块错过了一段聊天——`get_load_strategy(replay=...)` 让框架在模块
就绪后，把会话收件箱里最近的消息**回放给该模块自己**：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # 回放最近 5 分钟（"1h" / "300" 秒写法均可）
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # 合成事件：仅补上下文，不要触发发送等副作用
                ...
```

语义细节：

- 数据源是[会话收件箱](interaction.md#会话收件箱eventhistory)（`sdk.transcript.recent()`），
  模块加载完成后后台执行，不阻塞启动
- 合成事件带 `replayed: True` 标志、完整 `platform / detail_type / user_id / alt_message`，
  **只分发给本模块的处理器**——其他模块不受回放影响
- 收件箱未启用 / 无记录 / 时长声明非法（`replay_invalid` 告警）时静默跳过

## 事件幂等去重

平台 websocket 重连后经常重推同一事件（相同 `event["id"]`）——分发入口按 id 做
LRU 去重（容量 4096），同 id 事件只分发一次。

```toml
[ErisPulse.framework]
event_dedupe = true   # 默认开启；测试环境固定 id 合成事件可关闭
```

适配器**注册**（新连接生命周期起点）时自动重置去重缓存。

## 连接管理

> 来源: `docs/zh-CN/advanced/connections.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/advanced/connections.md）

# 连接池与广播

> [!TIP]
> **什么时候需要读这篇**：需要 WebSocket/SSE 连接池、广播分组、跨模块推送或查看连接时。不需要则跳过，不影响其它功能的使用。

> **读完你会知道**：三种连接如何自动登记进注册表、分组订阅与广播 API、
> 跨模块复用与关闭权归属，以及模块卸载时连接的清理语义。
>
> **本篇不涉及**：WebSocket / SSE 路由的注册写法与连接生命周期钩子
> （见[路由管理器](router.md)）；客户端 HTTP 请求（见[网络客户端](http-client.md)）。


连接（服务端 WebSocket / SSE / 客户端出站 WebSocket）在 ErisPulse 中是**框架级一等资源**：
随连接建立自动登记进统一注册表，支持广播、业务分组订阅与跨模块传递/复用，
模块卸载时由框架自动关闭回收——业务不再自建 `_ws_clients` 集合，也不会因忘记清理而泄漏。

> 本文档示例均为**根导入**写法（2.10+ 推荐）：
> `from ErisPulse import connections, router, client, WebSocketConnection`

## 概述

```python
from ErisPulse import connections, router, WebSocketConnection

# 服务端：连接自动登记，handler 内加入业务分组
@router.ws("MyModule", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")            # 分组命名完全由业务约定
    async for msg in ws.iter_text():
        ...                             # 断开时框架自动注销、清理分组

# 任意位置：向分组广播（返回成败明细）
result = await connections.broadcast({"type": "notify"}, group="room:1")
if not result.ok:
    ...                                 # result.failed: {连接id: 异常}
```

三种连接统一进入注册表：

| kind | 来源 | 归属 owner | 说明 |
|------|------|-----------|------|
| `server` | `@router.ws(...)` / `register_websocket(...)` | 注册路由的模块名 | 断开自动注销 |
| `sse` | `@router.sse(...)` / `register_sse(...)` | 注册路由的模块名 | 广播走 `sse.send()` |
| `client` | `await client.ws_connect(url)` | 当前模块（或显式 `owner=`） | 关闭/远端断开自动注销；适配器停止时框架统一关闭 |

不想要自动登记时：路由传 `track=False`，出站连接传 `track=False`，老代码行为完全不变。

## 查看连接池

```python
from ErisPulse import connections

# 查看某模块的连接池（"某模块现在有几条活连接"）
conns = connections.list(namespace="Dashboard")
for conn in conns:
    print(conn.id, conn.kind, conn.groups, conn.meta)

# 按其它维度过滤（各条件 AND）
connections.list(owner="MyAdapter", kind="client")
connections.list(group="tenant:acme")

# 全局统计（各维度计数）
stats = connections.stats()
# {'total': 5, 'by_kind': {...}, 'by_namespace': {...}, 'by_owner': {...}, 'groups': {...}}

# 归属权审计计数（ownership 门面同样可见）
from ErisPulse import ownership
ownership.counts("Dashboard")   # {'connections': 3, ...}
```

每条连接可读的身份信息：`conn.id`（形如 `Dashboard:1a2b3c4d`）、`conn.namespace`、
`conn.owner`、`conn.kind`、`conn.groups`、`conn.meta`（业务自由字典）。

## 广播与订阅

### 分组（订阅模型）

分组是**扁平字符串**，命名完全由业务约定（房间 / 租户 / 主题……），
嵌套层级用命名约定表达（如 `tenant:acme/room:1`），框架不约束格式。

两个方向都可以操作：

```python
# 方向一：连接侧主动加入/退出（handler 内）
@router.ws("Chat", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")        # 等价 connections.assign(ws.id, "room:1")
    ws.leave_group("room:1")

# 方向二：管理侧被动分配（路由侧 / 其它模块）
connections.assign(conn_id, "tenant:acme")
connections.dismiss(conn_id, "tenant:acme")   # 不传分组名 = 退出全部分组
```

连接断开时自动退出全部分组，无需业务清理。

### 广播

```python
result = await connections.broadcast(
    data,                       # WS 走 send_json；SSE 走 send（自动 JSON 序列化）
    namespace="Dashboard",      # 按命名空间过滤
    group="room:1",             # 按分组过滤
    kind="sse",                 # 按连接种类过滤
    owner="MyAdapter",          # 按归属过滤
    ids={conn_id, ...},         # 显式指定候选集（过滤条件仍生效）
    exclude={conn_id},          # 排除某些连接
    timeout=10.0,               # 单条连接发送超时（非总时长）
    concurrency=64,             # 并发发送上限
    raise_on_error=False,       # True 时有失败项则抛出首个异常
)
result.total      # 目标连接总数（排除前）
result.sent       # 成功的连接 id 列表
result.failed     # {连接 id: 异常对象}（超时/已断开/发送失败）
result.excluded   # 被排除的连接 id
result.ok         # 是否全部送达
```

过滤条件之间是 **AND**；单条失败不影响其它连接；`ids` 中已不存在的连接会计入
`failed`（让业务知道全貌）。

### 生命周期事件

连接登记/注销/分组变化会发射标准生命周期事件，Dashboard 等可订阅做实时呈现：

```python
from ErisPulse import lifecycle

@lifecycle.on("connection.registered")
async def on_registered(data): ...
@lifecycle.on("connection.unregistered")
async def on_unregistered(data): ...
@lifecycle.on("connection.group.joined")
async def on_joined(data): ...
@lifecycle.on("connection.group.left")
async def on_left(data): ...
```

## 跨模块传递 / 复用

连接是框架登记的资源，任何模块都可以通过连接 id 拿到它并**复用**——
不需要自己再建一条，也不需要知道连接是谁建的：

```python
from ErisPulse import connections

conn = connections.get("Dashboard:1a2b3c4d")   # 不存在/已断开抛 ConnectionNotFoundError
await conn.send_json({"ping": 1})              # 任何模块都可发送
conn.join_group("someone-elses-room")          # 也可参与分组
```

**归属与关闭权**：

- 连接的 `owner`（创建它的模块）独占关闭权。非 owner 调用 `close()` 抛
  `ConnectionPermissionError`（`from ErisPulse import ConnectionPermissionError`）；
- 发送与分组操作对所有模块开放，不需要授权；
- owner 模块卸载 / 适配器停止时，框架**统一关闭并注销**其名下全部连接
  （服务端 + 出站），已拿到的引用再发送会得到失败结果，监听
  `connection.unregistered` 事件可感知；
- 框架内部回收路径用 `close(force=True)` 绕过校验。

> 归因说明：关闭权校验依赖运行时 owner 上下文（`owner_scope` / 事件分发 /
> `spawn_background` 等自动携带）。上下文不可归因的调用（未归因的老代码）会放行，
> 保证 0 破坏；新代码在 owner 上下文中调用即受保护。

## 出站连接（Client 侧）

```python
from ErisPulse import client

ws = await client.ws_connect("wss://example.com/ws")
ws.id          # 已登记，可被 connections 查询/广播
ws.owner       # 当前模块（owner 上下文不可用时建议显式传）

# owner 上下文不可用（如工具线程回调）时显式指定，卸载才能自动回收：
ws = await client.ws_connect("wss://example.com/ws", owner="MyAdapter")
```

远端主动断开、本地 `close()` 都会自动注销登记；模块卸载时框架关闭其名下
全部出站连接。等旧代码裸建连接各自管理、忘记清理导致泄漏的日子到此为止。

## 跨线程投递

从子线程触达连接（广播 / 推送 / 关闭）时，用框架标准工具投递回主循环，
**不要手写 `run_coroutine_threadsafe`**：

```python
from ErisPulse import run_main_loop, spawn_later, spawn_thread

# 子线程阻塞取结果：
run_main_loop(connections.broadcast({"tick": 1}, group="room:1"), timeout=5)

# 后台线程 + 延迟任务（owner 归属，卸载自动取消）：
def push_tick():
    return connections.broadcast({"tick": 1}, group="room:1")
spawn_later(30, push_tick, owner="MyModule")
```

## 卸载与清理语义

模块卸载 / 适配器停止的归属权回收链会依次：取消归属后台任务与定时器 →
**关闭并注销归属连接** → 触发 on_cleanup 钩子 → 注销路由/处理器等注册类资源。
详见 [归属权（owner）系统](ownership.md)。

> [!WARNING]
> 2.10 起，模块卸载会关闭其名下登记的 WS/SSE/出站连接。依赖"卸载后连接仍存活"的
> 下游组件（如旧版 Dashboard 推送）需知悉——这是杜绝连接泄漏的预期行为。

## API 一览

| API | 说明 |
|-----|------|
| `connections.get(id)` | 取连接（跨模块入口），不存在抛 `ConnectionNotFoundError` |
| `connections.list(namespace=, owner=, group=, kind=)` | 过滤查询连接列表 |
| `connections.stats(namespace=, owner=)` | 各维度计数统计 |
| `connections.assign(id, *groups)` / `dismiss(id, *groups)` | 管理侧加入/移出分组 |
| `await connections.broadcast(data, ...)` | 广播，返回 `BroadcastResult` |
| `await connections.close(id, force=False)` | 关闭并注销（权限校验） |
| `await connections.close_owner(owner)` | 关闭注销某 owner 名下全部连接（框架卸载链调用） |
| `conn.join_group(*groups)` / `conn.leave_group(*groups)` | 连接侧分组 |
| `conn.send_json / send_text / iter_text / ...` | 收发（服务端/客户端接口一致） |
| `conn.meta` | 业务元数据字典 |
| `conn.close(force=False)` | 关闭（非 owner 抛 `ConnectionPermissionError`） |

## HTTP 客户端

> 来源: `docs/zh-CN/advanced/http-client.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/advanced/http-client.md）

# 网络客户端

> [!TIP]
> **什么时候需要读这篇**：需要出站 HTTP / WebSocket 请求时。不需要则跳过，不影响其它功能的使用。


ErisPulse 提供了统一的网络客户端，聚合了 HTTP 请求、WebSocket 连接和连接池管理。模块和适配器**必须优先使用**此客户端，而非自行导入 `aiohttp` / `httpx` / `requests` 等第三方库。

## 概述

网络客户端的主要功能：

- **统一接口**：提供 `get` / `post` / `put` / `delete` / `patch` / `request` 方法
- **WebSocket 客户端**：通过 `ws_connect` 建立客户端 WebSocket 连接
- **自动日志**：所有请求自动记录日志和统计信息
- **生命周期集成**：每次请求触发 `client.request` 生命周期事件，WS 连接触发 `client.ws.connect` 事件
- **重试支持**：可配置自动重试次数和间隔
- **超时控制**：独立的连接超时和请求超时
- **连接池复用**：基于 aiohttp.ClientSession 的连接池管理
- **异常体系**：aiohttp 异常自动转换为 ErisPulse 异常 (ClientError 体系)

## 快速开始

### HTTP 请求

```python
from ErisPulse.Core import client

# GET 请求
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST 请求
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket 连接

```python
from ErisPulse import client   # 2.10+ 根导入（ErisPulse.Core.client 深路径仍兼容）

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

#### 出站连接自动入池（2.10+）

`ws_connect` 建立的连接**默认自动登记**进框架连接池（`track=False` 可关闭）：
可被 `connections.list(owner=...)` 查看、向其广播；连接关闭 / 远端断开自动注销；
**模块卸载 / 适配器停止时框架统一关闭**其名下全部出站连接，杜绝泄漏。

```python
from ErisPulse import client, connections

ws = await client.ws_connect("wss://example.com/ws")
print(ws.id, ws.owner)   # 已登记：连接 id 与归属

# owner 上下文不可用（如工具线程回调）时显式指定归属，卸载才能自动回收：
ws2 = await client.ws_connect("wss://example.com/ws2", owner="MyAdapter")
```

详见[连接池与广播](connections.md)。

## HttpResponse

所有请求方法返回 `HttpResponse` 对象：

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP 状态码 (如 200, 404)
resp.reason       # str | None - 状态描述 (如 "OK")
resp.headers      # 响应头 (大小写不敏感)
resp.content_type # str | None - Content-Type
resp.url          # 最终 URL (可能因重定向变化)
resp.raw          # 底层原生响应对象 (当前为 aiohttp.ClientResponse)

# 读取响应体
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # 解析 JSON
text = await resp.text("gbk")  # 指定编码
```

## 请求方法

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# JSON 请求体
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# 表单请求体
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# 原始数据
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# 文件上传 (使用 files 参数, 无需导入 aiohttp)
# 格式: {字段名: 文件对象/bytes/(filename, file)/(filename, file, content_type)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "头像"},            # 可选: 同时携带普通表单字段
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# 简化写法: 直接传文件对象
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# 内存数据直接上传 (无需落盘)
import io

resp = await client.post(
    "https://api.example.com/upload",
    files={"file": ("data.txt", io.BytesIO(b"file content"), "text/plain")},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### 通用 request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## 参数说明

### HTTP 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `url` | `str` | 请求 URL |
| `params` | `dict[str, str]` | 查询参数 (可选) |
| `headers` | `dict[str, str]` | 额外请求头 (可选) |
| `data` | `Any` | 请求体 (表单或原始数据) (可选) |
| `json` | `Any` | JSON 请求体 (可选) |
| `files` | `dict[str, Any]` | 文件上传字段 (可选, 自动构建 multipart/form-data) |
| `timeout` | `float` | 本次请求超时 (秒) (可选, 覆盖默认值) |
| `max_retries` | `int` | 本次最大重试次数 (可选, 覆盖默认值) |

### ws_connect 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `url` | `str` | WebSocket 服务器 URL |
| `headers` | `dict[str, str]` | 额外请求头 (可选) |
| `heartbeat` | `float` | 心跳间隔秒数 (可选) |

## 超时与重试

```python
from ErisPulse.Core import Client

# 创建带自定义超时的客户端
client = Client(
    timeout=60,           # 请求总超时 60s
    connect_timeout=5,    # 连接超时 5s
    max_retries=3,        # 失败自动重试 3 次
    retry_delay=2,        # 重试间隔 2s
)

# 单次请求覆盖超时
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> 客户端类从 2.8.0 起更名为 `Client`（`sdk.client` 属性名不变）；旧名 `HttpClient` 保留为兼容别名，老代码无需修改。

## 自定义默认头

```python
client = Client(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## 请求统计

```python
from ErisPulse.Core import client

# 查看统计
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# 重置统计
client.reset_stats()
```

## 生命周期事件

### HTTP 请求事件

每次请求完成后触发 `client.request` 事件，可用于监控：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### WebSocket 连接事件

每次 WebSocket 连接建立后触发 `client.ws.connect` 事件：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS 连接: {event_data['url']}")
```

## 上下文管理

```python
# 作为上下文管理器，自动关闭会话
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket 客户端

通过 `client.ws_connect()` 建立 WebSocket 客户端连接，返回 `ClientWebSocket` 对象。客户端和服务端 WebSocket 共享相同的 `WebSocketConnectionBase` 基类，send/receive/iter 接口完全一致。

### 基本用法

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### 接收消息

#### 高级方法 (推荐)

自动过滤消息类型，断开时抛出 `WebSocketDisconnect`：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# 单条接收
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# 迭代接收 (自动在断开时停止)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### 低级方法

使用 `receive()` 和 `iter_messages()` 处理原始消息类型，可区分 TEXT / BINARY / CLOSE / ERROR：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# 单条接收原始消息
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# 迭代原始消息 (CLOSE/ERROR 时自动停止)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"文本: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"二进制: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` 是统一的 WebSocket 消息类型，不依赖底层库：

| 属性 | 类型 | 说明 |
|------|------|------|
| `type` | `str` | 消息类型: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | 消息数据 |

### ClientWebSocket 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `url` | `URL` | 连接 URL |
| `headers` | `Headers` | 响应头 |
| `closed` | `bool` | 连接是否已关闭 |
| `raw` | `object` | 底层原生对象 (aiohttp.ClientWebSocketResponse) |

### 生命周期钩子

与 `服务端 WebSocketConnection` 一致，支持 `on_disconnect` 和 `on_error` 回调：

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"连接断开: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"连接错误: {error}")
```

### 关闭连接

```python
await ws.close(code=1000, reason="Normal closure")
```

## 异常体系

ErisPulse 定义了统一的异常层级，通过 `sdk.client` 发起的请求会自动将底层 aiohttp 异常转换为 ErisPulse 异常。

> **向后兼容**：直接使用 `aiohttp.ClientSession` 的旧模块/适配器完全不受影响。异常转换仅在通过 `sdk.client` 发起请求时生效，直接使用 aiohttp 的代码仍然捕获 `aiohttp.ClientError` 等原生异常。两种方式可以共存。

### 异常层级

```
ErisPulseError
├── ClientError                  # 所有 HTTP/WS 客户端请求异常的基类
│   ├── ClientConnectionError    # 连接失败 (DNS 解析失败、连接被拒绝、网络不可达)
│   ├── ClientTimeoutError       # 连接超时或请求超时
│   └── HTTPStatusError          # HTTP 4xx/5xx 状态码错误
└── WebSocketError               # WebSocket 异常基类
    └── WebSocketDisconnect      # WebSocket 连接断开 (客户端和服务端通用)
```

### 异常捕获

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import (
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)

# HTTP 请求异常处理
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("无法连接到服务器")
except ClientTimeoutError:
    print("请求超时")
except ClientError as e:
    print(f"请求失败: {e}")

# WebSocket 异常处理
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"连接断开: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocket 错误: {e}")
```

### 统一捕获

使用 `ClientError` 统一捕获所有 HTTP/WS 客户端请求异常：

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"客户端错误: {e}")
```

### HTTPStatusError

当需要在请求后检查状态码并抛出异常时，可手动使用：

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## 适配器中使用

适配器可使用全局客户端或自行创建客户端实例发送平台 API 请求：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.errors import ClientError

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        try:
            resp = await client.post(
                f"https://api.platform.com/{endpoint}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return await resp.json()
        except ClientError as e:
            self.logger.error(f"API 调用失败: {e}")
            raise
```

> 也可通过 `from ErisPulse import sdk` 使用 `sdk.client`，效果相同。

## 最佳实践

1. **优先使用全局客户端**：使用 `from ErisPulse.Core import client` 获取全局单例，便于框架统一管理和监控
2. **避免直接导入 aiohttp**：使用 `client` 替代 `aiohttp.ClientSession`，未来更换底层实现无需修改代码。旧代码直接使用 aiohttp 仍可正常工作，两种方式可以共存
3. **使用 ErisPulse 异常体系**：通过 `sdk.client` 请求时捕获 `ClientError` 而非 `aiohttp.ClientError`，确保代码不依赖特定 HTTP 库。直接使用 aiohttp 的旧代码不受影响
4. **合理设置超时**：根据 API 响应速度设置合理的超时时间，避免长时间阻塞
5. **使用重试机制**：对不稳定的 API 启用重试，提高可靠性
6. **监控请求统计**：通过 `sdk.client.stats` 或 `client.request` 生命周期事件监控请求情况
7. **WebSocket 使用高级方法**：优先使用 `iter_text` / `iter_json` 等高级方法，仅在需要区分消息类型时使用 `iter_messages`

## 路由

> 来源: `docs/zh-CN/advanced/router.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/advanced/router.md）

# 路由管理器

> [!TIP]
> **什么时候需要读这篇**：需要 HTTP / WebSocket / SSE 路由（含连接池广播）时。不需要则跳过，不影响其它功能的使用。


ErisPulse 路由管理器提供统一的 HTTP 和 WebSocket 路由管理，支持多适配器路由注册和生命周期管理。底层通过抽象层封装（当前为 FastAPI + Uvicorn）

## 概述

路由管理器的主要功能：

- **装饰器路由**：支持 `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` 装饰器快捷注册
- **自动注入**：路由处理器无需导入 FastAPI 类型，框架自动注入抽象对象
- **路由分组**：支持带前缀和版本号的 `RouteGroup`
- **路由中间件**：支持 glob 模式匹配的请求拦截
- **速率限制**：内置滑动窗口限流
- **CORS 支持**：一键开启跨域资源共享
- **安全头**：自动添加安全响应头
- **自动文档**：基于 OpenAPI 的交互式文档
- **WebSocket 支持**：完整的 WebSocket 连接管理、自定义认证和生命周期钩子
- **生命周期集成**：与 ErisPulse 生命周期系统深度集成
- **SSL/TLS 支持**：支持 HTTPS 和 WSS 安全连接
- **主页入口**：支持模块在根路由 `/` 注册快捷入口按钮，支持国际化

## 抽象类型

ErisPulse 提供了服务端抽象类型，使模块无需直接依赖 FastAPI：

| 抽象类型 | FastAPI 对应 | 说明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP 请求封装，接口完全兼容 |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket 连接封装，额外提供生命周期钩子 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket 断开异常 |

> `WebSocketConnection` 继承自 `WebSocketConnectionBase`，与客户端 WebSocket (`ClientWebSocket`) 共享相同的 send/receive/iter/close 接口。客户端和服务端 WebSocket 可以使用相同的业务逻辑代码。
>
> 通过 `.raw` 属性可访问底层 FastAPI 原生对象。直接使用 FastAPI 类型的代码也完全兼容。

## 装饰器路由（推荐）

### 注册形态：单参（推荐）与双参

装饰器路由支持两种形态，**推荐单参**——与命令 / 事件触发器一致，命名空间自动归属当前模块：

```python
from ErisPulse import router

# 单参（推荐）：自动归属 模块名/hello → 实际路径 /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# 单参 WebSocket：@ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# 双参：显式指定模块名（规则不变，跨模块/工具代码注册时使用）
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> 单参形态要求在模块/适配器**加载上下文**中注册（加载期框架已注入归属）；
> 在无归属上下文处调用会抛 `ValueError` 并提示显式传入模块名。

### HTTP 装饰器

```python
from ErisPulse import router, HttpRequest

# 也可显式标注抽象类型
@router.post("/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **自动注入规则**：当处理器第一个参数名为 `request` 或 `req` 且无 FastAPI 类型注解时，框架自动注入 `HttpRequest`。无参数或非请求参数名的处理器不受影响。

#### 响应返回约定（2.10+）

处理器返回值支持**元组约定**（推荐写法，明确控制状态码），dict/str/Response 照旧：

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "token 无效"}, 401
    # (body, status_code, headers) 还可带响应头
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# 或使用 respond() 帮助函数（message 自动合并进响应体）
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

路径 / 查询参数直接用 FastAPI 原生注解即可（`item_id: int`、`page: int = 1`），
中间件见[路由中间件](#路由中间件)一节。

### WebSocket 装饰器

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# 基本 WebSocket（单参形态）
@router.ws("ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 带生命周期钩子的 WebSocket
@router.ws("/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"用户断开: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"连接错误: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 带认证的 WebSocket
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocket 处理器和认证处理器也支持自动注入。无需参数注解即可获得 `WebSocketConnection`。标注 `fastapi.WebSocket` 也可传入原生对象，但推荐使用抽象类型。

### 连接自动登记（连接池，2.10+）

`@ws` / `@sse` 建立的连接**默认自动登记**进框架连接池（`track=False` 可关闭）：
handler 内 `ws.id` / `ws.join_group(...)` 可用，任意模块可
`connections.list(namespace=...)` 查看本模块连接、向分组广播。
详见[连接池与广播](connections.md)。

## 传统注册方式

```python
async def hello_handler(request):
    return {"message": "Hello World"}

# 基本注册
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# 带限流和文档信息
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="数据接口",
    tags=["API"],
)
```

### WebSocket 注册

```python
from ErisPulse.Core import WebSocketConnection

async def websocket_handler(ws: WebSocketConnection):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 基本注册
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# 带认证的注册（推荐）
async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `module_name` | 模块名称（必须） | - |
| `path` | WebSocket 路径 | - |
| `handler` | 处理函数 | - |
| `auth_handler` | 认证函数，返回 `False` 会自动关闭连接 | `None` |
| `auto_accept` | 是否自动 `accept()` | `True` |

> **推荐**：使用 `auth_handler` 进行连接确认，而非关闭 `auto_accept`。仅在你需要完全控制连接流程时才设置 `auto_accept=False`。

## WebSocket 生命周期钩子

`WebSocketConnection` 提供了断开连接和错误的回调注册，无需手动 try/catch：

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # 装饰器方式注册
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"断开原因: {reason}")

    # 也可直接调用
    async def on_err(ws, error=""):
        print(f"错误: {error}")
    ws.on_error(on_err)

    # 正常业务逻辑
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## 路由分组

```python
# 创建带前缀的路由组
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# 实际路径: /my_module/v1/users
```

## 路由中间件

中间件支持 glob 模式匹配路径：

```python
@router.middleware("/my_module/*")
async def auth_middleware(request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    return await call_next(request)

@router.middleware("/my_module/admin/*")
async def admin_middleware(request, call_next):
    return await call_next(request)
```

## 请求关联 ID（X-Request-ID）

从 2.7.0 起，每个 HTTP 请求都会携带一个 `X-Request-ID` 关联 ID，用于日志 / 链路追踪串联：

- **生成规则**：优先沿用客户端传入的 `X-Request-ID` 请求头（分布式追踪场景）；否则自动生成 UUID
- **响应头**：响应会回写 `X-Request-ID`，方便客户端把请求与日志对应
- **生命周期事件**：`server.request` 与 `server.response` 事件数据中新增 `request_id` 字段

```python
# 在模块中监听请求事件，按 request_id 串联请求-响应
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

客户端可自定义 ID 以便跨服务追踪：

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## 速率限制

使用滑动窗口算法对路由进行限流：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

速率限制格式：`{次数}/{时间窗口}`，如 `10/minute`、`100/hour`。

## CORS 配置

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

也可通过 `config.toml` 配置：

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## 安全头

```python
router.setup_security_headers()
```

自动添加 `X-Content-Type-Options`、`X-Frame-Options`、`X-XSS-Protection` 等安全头。

也可通过 `config.toml` 配置：

```toml
[router.security]
enabled = true
```

## 自动文档

Router 默认启用 OpenAPI 交互式文档：

```python
# 禁用文档
router.disable_docs()

# 自定义文档信息
router.set_docs_info(
    title="My API",
    description="API 文档",
    version="1.0.0"
)
```

## 路径处理

路由路径会自动添加模块名称作为前缀，避免冲突：

```python
# 注册路径 "/api" 到模块 "my_module"
# 实际访问路径为 "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> 路由路径（含模块名前缀）**大小写敏感**。注册时的模块名是什么大小写，实际路径就是什么大小写：模块名为 `Test` 时注册 `/api` 的实际路径是 `/Test/api`，访问 `/test/api` 将返回 404。

## 系统路由

路由管理器自动提供以下系统路由：

### 健康检查

```
GET /health
# 返回:
{"status": "ok", "service": "ErisPulse Router"}
```

### 根页面

```
GET /
# 返回 ErisPulse 品牌页
```

根路由 `/` 显示 ErisPulse 品牌页面，自动检测 Dashboard 可用性并添加入口按钮。

## 主页入口

路由管理器允许外部模块在根路由 `/` 上注册快捷入口按钮，方便用户快速访问各模块的管理页面。

### 注册入口

```python
# 简单注册
router.register_home_entry(
    name="我的面板",
    url="/mymodule/admin",
)

# 带图标的注册（SVG）
router.register_home_entry(
    name="控制台",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# 支持国际化的注册（项目 i18n 字典格式）
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "我的面板"},
    url="/mymodule/admin",
)
```

**参数说明：**

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `name` | `str` / `dict` | 按钮显示文本；传入 `{"i18n": "key", "default": "文本"}` 字典时使用国际化 | 是 |
| `url` | `str` | 按钮链接地址 | 是 |
| `icon_svg` | `str` | 可选 SVG 图标标记 | 否 |

### Dashboard 自动注册

当检测到 `sdk.Dashboard` 可用时，路由管理器自动在入口列表首位添加 Dashboard 按钮，无需手动注册。

## 生命周期集成

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"服务器已启动: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("服务器正在停止...")
```

## 最佳实践

1. **优先使用抽象类型**：使用 `HttpRequest` / `WebSocketConnection` 替代 `fastapi.Request` / `fastapi.WebSocket`，避免硬依赖
2. **利用自动注入**：处理器第一个参数命名为 `request` 或 `req`，无需任何类型注解即可获得 `HttpRequest`
3. **单参形态优先**：模块加载上下文中优先单参形态（自动归属命名空间）；跨模块/工具代码注册时显式传模块名
4. **使用路由分组**：对同一模块的多个路由使用 `group()` 组织
5. **安全性考虑**：为敏感操作实现认证机制和安全头
6. **合理限流**：对高频接口设置速率限制
7. **使用生命周期钩子**：通过 `@ws.on_disconnect` / `@ws.on_error` 处理 WebSocket 异常，避免手动 try/catch
