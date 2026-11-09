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

**未实现**（适配器未重写 `accept`/`reject`）：
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

适配器在 `Request` 内部类中重写 `accept` 和 `reject` 即可：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform 请求操作实现"""
        
        def accept(self, **kwargs):
            """
            同意请求
            
            :param kwargs: 扩展参数，如 comment="备注"
            :return: asyncio.Task
            """
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
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
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """拒绝请求"""
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=False,
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
            
            return self._create_task(_do())
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
2. **操作侧路由**：端点选择顺序为 **kwargs 显式传参 > 缓存 > 回退默认端点并记 WARNING**——类型未知必须打日志（可观测），不得静默选端点
3. **kwargs 保留名**：显式覆盖参数统一命名 `request_type` / `sub_type` / `group_id`（无下划线前缀、跨适配器同名同义）；不使用 `_request_type` 一类私有约定名（标准调用方不会传）
4. **账户一并留存**：缓存保存事件到达时的账户（事件的 `self.user_id`）；调用方未显式 `Using()` 时按该账户受理
5. **处理后清理**：操作提交成功后从缓存删除该 `request_id`

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

#### 5.3.4 参考实现（内存缓存）

```python
import time

from ErisPulse.Core import BaseAdapter, RequestDSL


class MyAdapter(BaseAdapter):
    """请求端点异构平台（好友与群请求分端点）"""

    _REQ_CTX_TTL = 3600    # 上下文留存秒数，覆盖平台侧请求有效期即可
    _REQ_CTX_MAX = 512     # 缓存容量上限

    def __init__(self, sdk=None):
        super().__init__(sdk)
        self._request_ctx: dict[str, dict] = {}   # request_id → 请求上下文

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
            "account": account,             # 事件到达账户（事件的 self.user_id）
            "ts": now,
        }

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

        def accept(self, **kwargs):
            """
            同意请求

            :param kwargs: 扩展参数；类型路由可用 request_type / sub_type / group_id 显式覆盖
            :return: asyncio.Task
            """
            async def _do():
                ctx = self._route(**kwargs)
                account = self._account_id or ctx.get("account")
                try:
                    if ctx["request_type"] == "group":
                        result = await self._adapter.call_api(
                            endpoint="/set_group_add_request",
                            flag=self._request_id,
                            sub_type=ctx.get("sub_type") or "add",
                            approve=True,
                            account=account,
                        )
                    else:
                        result = await self._adapter.call_api(
                            endpoint="/set_friend_add_request",
                            flag=self._request_id,
                            approve=True,
                            account=account,
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
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"请求操作失败: {e}",
                    }
                if response["status"] == "ok":
                    self._adapter._request_ctx.pop(self._request_id, None)   # 处理后清理
                return response

            return self._create_task(_do())
```

`reject` 与 `accept` 同构：调用链与路由逻辑相同，`approve=False`，清理条件同样为 `status == "ok"`。

#### 5.3.5 跨重启持久化（可选）

进程内存 + TTL 已覆盖绝大多数场景：请求从到达到被处理通常几秒～几分钟，平台侧本有过期时间，重启丢缓存的窗口极小（回退端点 + WARNING 已保证可观测）。仅当适配器在意「处理瞬间恰好重启」时，才把上下文落到持久化介质，介质自选其一，均按 §5.3.3 统一字段形状落存：

- **KV 存储**：`self.storage`（框架统一 KV 存储，即 `self.sdk.storage`，后端切换见 [存储后端](../advanced/storage-backends.md)）：

  ```python
  # 事件入口：写入（key 见 §5.3.3 键名规则）
  key = f"{self._get_config_key()}:request_ctx:{request_id}"
  self.storage.set(key, {"request_type": "group", "sub_type": "invite",
                         "group_id": group_id, "account": self_id, "ts": time.time()})

  # 操作侧：读取 + 清理
  ctx = self.storage.get(key)
  self.storage.delete(key)
  ```

  存储层不做条目过期：条目自带 `ts`，读取方判断过期即视为未留存（走回退 + WARNING）；处理后必须 `delete`。

- **内置 ORM**：`Model` / `Field` 声明式模型（2.9+ 内置，见 [数据模型层](../developer-guide/orm.md)）可作为等价介质，表按统一字段表建列（`request_id` 主键）。注意两点：`create_table` 为 `IF NOT EXISTS` 幂等，后续字段演进由适配器自行迁移存量表；表属于适配器自有数据，非跨适配器共享表。

无论选择哪种介质：**持久化写入失败不得阻断事件流**——存储后端不可用（冷却期 fast-fail）时降级为仅内存留存，事件照常分发；两种持久化介质均为可选，默认内存即可，不新增任何外部依赖。

### 5.4 平台不支持请求操作

如果平台本身不支持好友请求/群邀请操作（如某些平台自动处理请求），适配器可以：

1. **不重写 `Request` 内部类**：使用基类默认实现，调用 `accept()`/`reject()` 时返回 `retcode=10002`
2. **在转换时跳过 `request_id`**：不生成 `request_id`，让 `event.approve()` 抛出 `ValueError`
3. **记录日志**：在 `accept`/`reject` 中记录警告并返回适当错误码

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
    ├── accept()        ← 按需实现
    └── reject()        ← 按需实现
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
- [ ] `accept()` 方法已实现
- [ ] `reject()` 方法已实现
- [ ] 操作返回标准 API 响应格式
- [ ] 不支持的操作返回 `retcode=10002`
- [ ] 网络错误返回 `retcode=33xxx`（遵循 API 响应标准）

### 请求类型上下文留存（异构端点平台，见 §5.3）
- [ ] 请求事件入口已留存 `request_id → {请求类型, sub_type, group_id, 账户}` 上下文
- [ ] 条目字段与 §5.3.3 统一字段表一致（含 `ts` 时间戳；`request_id` 一一对应、处理后删除）
- [ ] `accept` / `reject` 端点路由顺序为 kwargs 显式传参 > 缓存 > 回退默认端点 + WARNING
- [ ] 类型覆盖参数使用保留名 `request_type` / `sub_type` / `group_id`（无 `_request_type` 一类私有约定名）
- [ ] 缓存有 TTL 与容量上限，操作提交成功后清理对应条目
- [ ] 多账户：缓存含事件到达账户，调用方未显式 `Using()` 时按该账户受理
- [ ] 若用持久化介质：写入失败降级为仅内存留存，不阻断事件流

## 7. 错误码扩展

请求操作相关的**适配器实现层**推荐错误码（遵循 [API 响应标准](api-response.md) §3.2，
落在 `34xxx` 平台错误段的低三位自定义）：

| 错误码 | 错误名 | 说明 |
|-------|-------|------|
| 34001 | Request Not Found | 请求不存在或已过期 |
| 34002 | Request Already Handled | 请求已被处理 |
| 34003 | Request Not Supported | 平台不支持该类型的请求操作 |
| 34004 | Permission Denied | Bot 无权处理此请求（平台返回） |

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
