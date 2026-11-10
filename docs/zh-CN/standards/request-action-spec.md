# ErisPulse 请求操作规范

> [!TIP]
> **什么时候需要读这篇**：当你的适配器需要处理好友请求/群邀请（转换请求事件、实现 `accept`/`reject`，含异构端点的请求类型上下文留存），或模块中要用 `event.approve()` / `event.reject()` 审批请求时对照本文。不需要则跳过。

本文档定义了 ErisPulse 适配器中请求事件操作的标准化规范，包括请求事件的字段要求、Request DSL 的使用方式和适配器实现要求。

## 1. 概述

请求事件（`type: "request"`）是 OneBot12 标准中定义的特殊事件类型，代表需要 Bot 做出决策的请求（如好友请求、群邀请等）。

与消息事件不同，请求事件需要**双向交互**：
1. **接收**：适配器将平台原生请求转换为标准请求事件
2. **响应**：模块通过 `Request` DSL 或 `Event.approve()`/`Event.reject()` 执行操作

```
平台原生请求事件
    │
    ▼
Converter.convert()        ← 适配器实现（正向转换）
    │
    ▼
标准请求事件 (含 request_id)
    │
    ├─→ 模块处理器 @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← 同意请求
    │       └─→ event.reject()      ← 拒绝请求
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← 适配器重写
    │               │
    │               ▼
    │       平台 API 调用
    │
    └─→ 或直接通过适配器操作
            await adapter.Request("req_id").accept()
```

## 2. 请求事件字段要求

### 2.1 标准字段

请求事件除必须包含 OneBot12 标准字段外，还需包含以下字段：

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `request_id` | string | **强烈推荐** | 请求标识符，用于同意/拒绝操作 |
| `user_id` | string | 是 | 请求发起者ID |
| `user_nickname` | string | 否 | 请求发起者昵称 |
| `comment` | string | 否 | 请求附言 |

### 2.2 `request_id` 字段

`request_id` 是请求操作的核心标识符：

- **用途**：标识一个可操作的请求，供 `Request` DSL 使用
- **生成规则**：
  - 优先使用平台原生的请求标识（如 OneBot11 的 `flag` 字段、Telegram 的 `chat_invite_link` 等）
  - 如果平台没有原生请求ID，适配器应生成一个唯一标识（建议格式：`{platform}_{timestamp}_{user_id}`）
- **唯一性**：在同一平台范围内应保持唯一
- **缺失行为**：当 `request_id` 缺失时，`event.approve()` / `event.reject()` 将抛出 `ValueError`

### 2.3 请求事件示例

```json
{
  "id": "evt_123456",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "请加好友",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 链式调用

`Request` 提供与 `Send` 风格一致的链式调用接口：

```python
# 基本用法
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# 指定 Bot 账号
await adapter.Request("req_id").Using("bot1").accept()

# 附带备注（通过 kwargs）
await adapter.Request("req_id").accept(comment="欢迎")
await adapter.Request("req_id").reject(comment="暂不添加")

# 组合使用
await adapter.Request("req_id").Using("bot1").accept(comment="欢迎")
```

### 3.2 方法列表

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `Using(account_id)` | 指定执行操作的 Bot 账号 | `RequestDSL`（支持链式调用） |
| `accept(**kwargs)` | 同意请求 | `asyncio.Task`（await 后返回标准响应） |
| `reject(**kwargs)` | 拒绝请求 | `asyncio.Task`（await 后返回标准响应） |

### 3.3 返回值格式

操作返回标准 API 响应格式：

**成功**：
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**失败**：
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "请求已过期或不存在"
}
```

**未实现**（适配器未重写 `_do_accept`/`_do_reject`）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "平台 MyAdapter 未实现请求操作 (accept)"
}
```

## 4. Event 便捷方法

`Event` 包装类提供了便捷方法，适合在请求事件处理器中使用：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # 检查请求ID
    request_id = event.get_request_id()
    if not request_id:
        print("警告：请求事件缺少 request_id")
        return
    
    # 同意请求
    result = await event.approve()
    
    # 或拒绝请求
    # result = await event.reject(comment="暂不添加好友")
    
    # 检查结果
    if result.get("status") == "ok":
        print("操作成功")
    else:
        print(f"操作失败: {result.get('message')}")
```

### 4.1 Event 方法列表

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `get_request_id()` | 获取请求ID | `str` |
| `approve(comment=None)` | 同意当前请求事件 | 标准响应格式 |
| `reject(comment=None)` | 拒绝当前请求事件 | 标准响应格式 |

## 5. 适配器实现要求

### 5.1 转换器要求

适配器的转换器在转换请求事件时，**必须**正确设置 `request_id` 字段：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """转换平台原生请求事件"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" 或 "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← 关键字段
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    从平台原生事件提取请求ID
    
    优先使用平台原生的请求标识，若无则生成唯一ID
    """
    # 优先使用平台原生ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # 兜底：生成唯一ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 内部类实现

基类的 `accept()` / `reject()` 是公开入口：内置 scope 授权闸口（`scope.actions.<owner>.request`，禁用时直接返回 34601 拒绝响应）与任务包装，**适配器不要重写公开入口**——重写会绕过授权闸口。适配器重写 `_do_accept` / `_do_reject`（异步方法，直接返回标准响应 dict）。

> **多账户提醒**：`_do_accept` / `_do_reject` 内是适配器自己调 `call_api`，账户不会自动注入——账户经 `self.request_context.get("account_id")` 获取（`Using()` 显式指定 > 事件链自动绑定，与 Send 的 `send_context` 同口径），并作为 `account_id` 参数传给 `call_api`，否则多账户部署下会落到默认账户。

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform 请求操作实现"""
        
        async def _do_accept(self, **kwargs) -> dict:
            """
            同意请求
            
            :param kwargs: 扩展参数，如 comment="备注"
            :return: 标准响应格式 dict
            """
            try:
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    account_id=self.request_context.get("account_id"),
                    approve=True,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "retcode": 34001,
                    "data": None,
                    "message_id": "",
                    "message": f"请求操作失败: {e}",
                }
        
        async def _do_reject(self, **kwargs) -> dict:
            """拒绝请求（与 _do_accept 同构：approve=False）"""
```

### 5.3 请求类型上下文留存（异构端点适配器必须）

#### 5.3.1 契约缺口

`Request` DSL 是无状态句柄：调用方只持 `request_id`（[§3](#3-request-dsl)），请求类型不在调用参数里。而不少平台的同意/拒绝端点是**异构**的——以 OneBot11 系为例：

| 请求类型 | 端点 |
|---|---|
| 好友添加 | `set_friend_add_request(flag, approve)` |
| 群申请 / 群邀请 | `set_group_add_request(flag, sub_type, approve)`，`sub_type ∈ {"add", "invite"}` |

调用方只知道 `request_id`，端点选择却需要类型。这段上下文只可能由适配器补齐：请求事件本就是适配器接收并转换的（类型信息在转换时就在手上），且一个 `request_id` 对应的请求类型不会变。适配器若不自行留存，只能猜测端点或依赖调用方传非标准参数——典型故障形态是**群邀请被送进好友端点**，flag 被协议端按 user_id 解析而报错。

#### 5.3.2 规范要求

平台端点异构（同意/拒绝需要按请求类型路由）的适配器，`accept` / `reject` 实现必须满足：

1. **事件侧留存**：适配器收到请求事件的入口处，把 `request_id → {请求类型, sub_type, group_id, 账户}` 写入实例内缓存（统一字段见 §5.3.3），并顺手清理过期条目
2. **操作侧路由**：`_do_accept` / `_do_reject` 内的端点选择顺序为 **kwargs 显式传参 > 缓存 > 回退默认端点并记 WARNING**——类型未知必须打日志（可观测），不得静默选端点
3. **kwargs 保留名**：显式覆盖参数统一命名 `request_type` / `sub_type` / `group_id`（无下划线前缀、跨适配器同名同义）；不使用 `_request_type` 一类私有约定名（标准调用方不会传）
4. **账户读取与归属校验**：操作账户统一经基类属性 `self.request_context.get("account_id")` 获取（`Using()` 显式指定 > 事件链自动绑定，与 Send 的 `send_context` 同口径）；留存条目的事件到达账户作为事件链缺失时的兜底（如轮询合成事件、跨重启重建）。**账户无法解析到具体账户实例时必须快速失败**（返回 34005），不得静默回退默认账户——回退会把操作打到错误连接（flag 在默认账户会话不存在，平台报 invalid，多账户下表现为「只有第一个账户能操作」）
5. **默认持久化**：留存介质默认为框架统一存储（`self.sdk.storage`）**单键整快照**——请求为低频批复类事件，事件到达时即写透（库内足迹恒为 1 个键）；启动时一次加载回内存，运行时读路径零开销；存储不可用时降级仅内存（WARNING），不阻断事件流
6. **处理后清理**：操作提交成功后删除该 `request_id` 条目并同步写透快照

单一请求端点的平台（如统一 `/set_request`）无需留存，透传即可。本节是适配器实现口径，`Request` DSL 契约不受影响。

#### 5.3.3 统一条目字段（介质无关）

上下文条目按以下统一字段形状留存。**字段形状是互操作契约**：内存 dict、KV value、ORM 行均按同一形状落存，后续跨适配器聚合或迁移时形状一致；存储介质自选，不因介质改变字段语义。

| 字段 | 类型 | 必含 | 语义与来源 |
|---|---|---|---|
| `request_type` | `str` | 是 | 请求类型，取自事件 `detail_type`（`"friend"` / `"group"`） |
| `sub_type` | `str \| None` | 群请求必含 | 群请求子类型 `"add"` / `"invite"`，取自平台原生事件（OB11 系 `sub_type`） |
| `group_id` | `str \| None` | 群请求必含 | 目标群 ID，取自平台原生事件 |
| `account` | `str \| None` | 多账户必含 | 事件到达账户，取自事件 `self.user_id` |
| `ts` | `float` | 是 | 事件到达 Unix 时间戳（秒），TTL 判定基准 |

条目一致性规则：

- **一一对应**：一个 `request_id` 至多对应一个条目；同 `request_id` 的重复事件覆盖写入（幂等）
- **处理后删除**：操作提交成功即删除条目
- **TTL**：以 `ts` 为基准，建议 1 小时级（覆盖平台侧请求有效期）；过期视同未留存，走回退默认端点 + WARNING
- **键名（KV 持久化时）**：`{适配器配置键}:request_ctx:{request_id}`，避免跨适配器冲突

#### 5.3.4 参考实现（统一存储单键快照，默认）

留存介质**默认为框架统一存储**（`self.sdk.storage`）：请求事件是批复类低频事件（好友/群请求，非消息流），**事件到达时即写透**不会造成写入压力。存储形式为**单键整快照**——整个上下文字典作为一个键一次写入（库内足迹恒为 1 个键，随处理自动收敛），不做逐 flag 分键。重启后启动时一次加载回内存，运行时读路径零开销。

```python
import time

from ErisPulse.Core import BaseAdapter, RequestDSL


class MyAdapter(BaseAdapter):
    """请求端点异构平台（好友与群请求分端点）"""

    _REQ_CTX_TTL = 86400   # 留存秒数（覆盖平台侧 flag 有效期，重启不丢）
    _REQ_CTX_MAX = 512     # 条目容量上限

    def __init__(self, sdk=None):
        super().__init__(sdk)
        self._request_ctx: dict[str, dict] = {}   # request_id → 请求上下文（内存态）
        self._ctx_key = f"{self._get_config_key()}:request_ctx"   # 单键整快照

    async def start(self):
        # 启动加载（重启后仍可审批）；存储不可用按冷启动处理
        try:
            loaded = self.sdk.storage.get(self._ctx_key, {}) or {}
            now = time.time()
            self._request_ctx = {k: v for k, v in loaded.items()
                                 if now - v.get("ts", 0) <= self._REQ_CTX_TTL}
        except Exception as e:
            self.logger.warning(f"请求上下文加载失败（按冷启动处理）: {e}")
            self._request_ctx = {}

    def _persist_ctx(self) -> None:
        """单键整快照写透（存储不可用时降级仅内存，不阻断事件流）"""
        try:
            self.sdk.storage.set(self._ctx_key, self._request_ctx)
        except Exception as e:
            self.logger.warning(f"请求上下文写透失败（降级仅内存）: {e}")

    def remember_request(self, request_id: str, *, request_type: str,
                         sub_type: str | None = None, group_id: str | None = None,
                         account: str | None = None) -> None:
        """事件侧留存请求上下文（适配器收到请求事件的入口处调用）"""
        now = time.time()
        expired = [k for k, c in self._request_ctx.items() if now - c["ts"] > self._REQ_CTX_TTL]
        for k in expired:
            self._request_ctx.pop(k)
        while len(self._request_ctx) >= self._REQ_CTX_MAX:
            self._request_ctx.pop(min(self._request_ctx, key=lambda k: self._request_ctx[k]["ts"]))
        self._request_ctx[request_id] = {
            "request_type": request_type,   # "friend" / "group"
            "sub_type": sub_type,           # 群请求子类型："add" / "invite"
            "group_id": group_id,
            "account": account,             # 事件到达账户（事件的 self.user_id / 代位账户名）
            "ts": now,
        }
        self._persist_ctx()

    class Request(RequestDSL):
        """端点路由：kwargs 显式传参 > 缓存 > 回退默认端点 + WARNING"""

        def _route(self, **kwargs) -> dict:
            ctx = {k: kwargs[k] for k in ("request_type", "sub_type", "group_id") if kwargs.get(k)}
            cached = self._adapter._request_ctx.get(self._request_id, {})
            if not ctx.get("request_type"):
                ctx.update({k: v for k, v in cached.items()
                            if k in ("request_type", "sub_type", "group_id") and v})
                ctx.setdefault("account", cached.get("account"))
            if not ctx.get("request_type"):
                self._adapter.logger.warning(f"请求 {self._request_id} 类型未知，按好友端点回退")
                ctx["request_type"] = "friend"
            return ctx

        def _resolve_or_fail(self, account):
            """
            审批账户归属校验：解析失败快速失败（34005），不回退默认账户。

            回退默认账户会把操作打到错误连接上（flag 在该账户会话不存在，
            平台报 invalid，表现为「只有第一个账户能操作」的玄学故障）。
            """
            if not account:
                return None, None            # 无任何账户信息时维持默认账户语义
            name, inst = self._adapter._resolve_account(account)
            hit = str(account) == str(name) or str(account) == str(getattr(inst, "bot_id", "") or "")
            if not hit:
                self._adapter.logger.warning(
                    f"请求 {self._request_id} 的账户 {account} 无法解析，拒绝回退默认账户")
                return None, "34005"
            return (name, inst), None

        async def _do_accept(self, **kwargs) -> dict:
            """同意请求；kwargs 类型路由可用 request_type / sub_type / group_id 显式覆盖"""
            return await self._do_action(approve=True, **kwargs)

        async def _do_reject(self, **kwargs) -> dict:
            """拒绝请求（与 _do_accept 同构：approve=False）"""
            return await self._do_action(approve=False, **kwargs)

        async def _do_action(self, approve: bool, **kwargs) -> dict:
            ctx = self._route(**kwargs)
            account = self.request_context.get("account_id") or ctx.get("account")
            resolved, fail = self._resolve_or_fail(account)
            if fail:
                return {
                    "status": "failed", "retcode": 34005, "data": None,
                    "message_id": "", "message": f"请求账户 {account} 无法解析到账户实例",
                }
            try:
                if ctx["request_type"] == "group":
                    result = await self._adapter.call_api(
                        endpoint="/set_group_add_request",
                        flag=self._request_id,
                        sub_type=ctx.get("sub_type") or "add",
                        approve=approve,
                        account_id=account,
                    )
                else:
                    result = await self._adapter.call_api(
                        endpoint="/set_friend_add_request",
                        flag=self._request_id,
                        approve=approve,
                        account_id=account,
                    )
                response = {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            except Exception as e:
                response = {
                    "status": "failed", "retcode": 34001, "data": None,
                    "message_id": "", "message": f"请求操作失败: {e}",
                }
            if response["status"] == "ok":
                self._adapter._request_ctx.pop(self._request_id, None)   # 处理后清理
                self._adapter._persist_ctx()
            return response
```

#### 5.3.5 边界与降级

**降级语义**：统一存储不可用（连接失败冷却期 fast-fail）时写透降级为仅内存（WARNING 可观测），事件照常分发；重启后条目丢失走「类型未知回退 + WARNING」路径。

**等价介质**：内置 ORM（`request_id` 主键建表，见 [数据模型层](../developer-guide/orm.md)）语义等价，适配器可按需选用；不引入额外文件或新依赖。

**多实例边界**：本规范不覆盖多进程实例协同——ErisPulse 为单进程多 bot 模型（多账户同进程，请求与其所属账户天然同侧），统一存储即满足重启语义；跨实例共享（多进程分摊账户）需要时再行立项。

### 5.4 平台不支持请求操作

如果平台本身不支持好友请求/群邀请操作（如某些平台自动处理请求），适配器可以：

1. **不重写 `Request` 内部类**：使用基类默认实现，调用 `accept()`/`reject()` 时返回 `retcode=10002`
2. **在转换时跳过 `request_id`**：不生成 `request_id`，让 `event.approve()` 抛出 `ValueError`
3. **记录日志**：在 `_do_accept` / `_do_reject` 中记录警告并返回适当错误码

### 5.5 总结：Send 与 Request 并行

适配器有两个并行的 DSL 内部类，各司其职：

```
BaseAdapter
├── Send(SendDSL)     ← 消息发送
│   ├── Raw_ob12()    ← 必须实现
│   ├── Text()        ← 推荐实现
│   └── Image()       ← 按需实现
│
└── Request(RequestDSL) ← 请求操作
    ├── accept()        ← 公开入口（scope 闸口 + 任务包装，勿重写）
    ├── reject()        ← 公开入口（同上）
    ├── _do_accept()    ← 按需重写
    └── _do_reject()    ← 按需重写
```

### 5.6 适配器 `__init__` 注意事项

重写 `Request` 内部类的 `__init__` 时，必须透传参数并调用 `super().__init__()`，详见 [适配器开发入门 - `__init__` 注意事项](../developer-guide/adapters/getting-started.md#init-注意事项)（`Request` 同理，参数为 `adapter, request_id, account_id`）。

## 6. 适配器实现检查清单

### 基础要求
- [ ] 若重写了 `__init__`，已调用 `super().__init__()`（确保 Send / Request 工厂初始化）

### 请求事件转换
- [ ] 请求事件包含 `request_id` 字段（强烈推荐）
- [ ] `detail_type` 正确映射为 `"friend"` 或 `"group"`
- [ ] 保留平台原始数据在 `{platform}_raw` 字段中
- [ ] `request_id` 生成规则有文档说明

### 请求操作
- [ ] `Request` 内部类已实现（如平台支持请求操作）
- [ ] `_do_accept()` / `_do_reject()` 已重写（公开入口 `accept()` / `reject()` 勿重写——绕过 scope 授权闸口）
- [ ] 操作返回标准 API 响应格式
- [ ] 不支持的操作返回 `retcode=10002`
- [ ] 网络错误返回 `retcode=33xxx`（遵循 API 响应标准）

### 请求类型上下文留存（异构端点平台，见 §5.3）
- [ ] 请求事件入口已留存 `request_id → {请求类型, sub_type, group_id, 账户}` 上下文
- [ ] 条目字段与 §5.3.3 统一字段表一致（含 `ts` 时间戳；`request_id` 一一对应、处理后删除）
- [ ] `accept` / `reject` 端点路由顺序为 kwargs 显式传参 > 缓存 > 回退默认端点 + WARNING
- [ ] 类型覆盖参数使用保留名 `request_type` / `sub_type` / `group_id`（无 `_request_type` 一类私有约定名）
- [ ] 缓存有 TTL 与容量上限，操作提交成功后清理对应条目
- [ ] 多账户：操作账户经 `self.request_context.get("account_id")` 读取（`Using()` > 事件链兜底），留存账户作事件链缺失时兜底
- [ ] 审批账户解析失败快速失败（34005），不回退默认账户
- [ ] 默认统一存储单键快照：启动加载、事件到达/处理后写透、存储不可用降级仅内存

## 7. 错误码扩展

请求操作相关的**适配器实现层**推荐错误码（遵循 [API 响应标准](api-response.md) §3.2，
落在 `34xxx` 平台错误段的低三位自定义）：

| 错误码 | 错误名 | 说明 |
|-------|-------|------|
| 34001 | Request Not Found | 请求不存在或已过期 |
| 34002 | Request Already Handled | 请求已被处理 |
| 34003 | Request Not Supported | 平台不支持该类型的请求操作 |
| 34004 | Permission Denied | Bot 无权处理此请求（平台返回） |
| 34005 | Request Account Unresolved | 请求所属账户无法解析到账户实例（快速失败，不回退默认账户） |

> **与框架码的边界**：以上 `340xx` 是**平台/适配器**返回的请求处理失败；
> ErisPulse 框架在 `scope.actions` 禁用某模块的 request 动作时，**在调用适配器之前**
> 直接返回 `34601`（Action Denied，见 [API 响应标准 §5.3](api-response.md#53-框架扩展返回码34xxx-平台错误段的低三位自定义)），
> 两者互不替代：先过 `34601` 框架闸口，再落到平台层 `340xx` 错误。

## 8. 相关文档

**实现请求操作时配套对照**：
- [事件转换标准](event-conversion.md) - 完整的事件转换规范（含 `request_id` 字段要求）
- [API 响应标准](api-response.md) - 适配器 API 响应格式标准（操作返回值与错误码）
- [存储后端](../advanced/storage-backends.md) - 需要跨重启留存请求上下文时的统一 KV 存储

**同一适配器的其它 DSL**：
- [发送方法规范](send-method-spec.md) - Send 类的方法命名和参数规范
- [会话类型标准](session-types.md) - 会话类型定义和映射关系
