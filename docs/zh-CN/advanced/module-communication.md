# 模块间通信

> [!NOTE]
> 本章内容需要 ErisPulse **2.8.0+**。

ErisPulse 的模块之间有**三层通信模型**，按"点对点 → 定向 → 广播"排列：

| 层 | API | 语义 | 典型场景 |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | 点对点请求-响应，带契约 / 审计 / 超时 | 调用另一模块的能力（查历史、翻译、退款） |
| **定向事件** | `await sdk.module.emit_to("Chat", "message_received", {...})` | 投递给指定模块的通知 | 上游状态变化通知下游（"收到新消息了"） |
| **广播** | `await lifecycle.emit("config.updated", {...})` | 全框架可见的生命周期事件 | 配置热更新、模块上下线 |

{!--< tips >!--}
选型口诀：**要返回值用 `call`，只通知一个模块用 `emit_to`，通知所有人用 `lifecycle`**。
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

需要精细控制（覆盖 docstring / 多语言）时用 dict 形态声明 description（支持 i18n 字典）：

```python
services=[
    {"name": "translate", "description": "把文本翻译成指定语言"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "摘要对话"}},
]
```

## 服务目录：services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': '把文本翻译成指定语言'}]}

sdk.module.services("Chat")   # 仅查询指定模块
```

- 只列出**显式声明** `meta.services` 的模块（未声明模块不出现在目录中）
- 每个服务带方法签名字符串（`inspect.signature` 提取）与介绍文本
- 同时进入拓扑：`sdk.module.get_topology()` 的各模块条目带 `services` 字段

{!--< tips >!--}
**MCP 化路线**：服务目录（名称 + 签名 + 描述）即 MCP tool 的形状——
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

## 定向事件：emit_to

```python
# 投递方：校验目标启用后，事件进入 module.<名称>.<事件> 命名空间
await sdk.module.emit_to("Chat", "message_received", {"text": "hi", "from": "u1"})

# 订阅方（Chat 模块内）：按命名空间注册钩子
from ErisPulse.Core.lifecycle import lifecycle

@lifecycle.on("module.Chat.message_received")
async def on_message_received(data): ...

@lifecycle.on("module.Chat")          # 或接收该模块的全部定向事件
async def on_any(data): ...
```

语义细节：

- 目标未注册 / 未启用 → `ModuleNotAvailableError`（**不发往不存在的地方**）
- 目标是懒加载模块 → **先唤醒再投递**（定向事件即激活源，与 `activate_on` 语义对齐）
- `data` 为 dict 时自动携带 `_trace_id`（不覆盖已有值），与全链路追踪打通

## 懒加载与调用

`module.call()` 与 `emit_to()` 对懒加载模块都是**透明唤醒**：

- 事件驱动懒模块（`activate_on` 声明）→ 走激活锁 `_activate()`，激活后触发器 stub 自动注销
- 普通懒模块 → 同步初始化或常规加载路径（幂等）
- 唤醒失败 → `ModuleNotAvailableError`（`call`）/ 激活失败（`emit_to`）

即：**调用方不需要关心目标模块是否已加载**，也无需为唤醒它而等待某条事件。

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

## 相关文档

- [交互会话系统](interaction.md) - wait_reply / 定时器 / 多路等待 / 会话互斥
- [作用域（scope）](scope.md) - 出站维度审计的完整配置
- [归属权（owner）系统](ownership.md) - owner 上下文如何贯穿跨模块调用
- [懒加载系统](lazy-loading.md) - 懒加载与事件驱动懒激活（activate_on）
- [生命周期管理](lifecycle.md) - 广播层事件总线的机制
