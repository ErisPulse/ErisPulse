# OneBot12平台特性文档

OneBot12Adapter 是基于 OneBot V12 协议构建的适配器，作为 ErisPulse 框架的基线协议适配器。

---

## 文档信息

- 对应模块版本: 4.6.2
- 维护者: ErisPulse
- 协议版本: OneBot V12
- 最后更新: 2026-11-10

## 基本信息

- 平台简介：OneBot V12 是一个通用的聊天机器人应用接口标准，是ErisPulse框架的基线协议
- 适配器名称：OneBot12Adapter
- 支持的协议/API版本：OneBot V12
- 多账户支持：完全多账户架构，支持同时配置和运行多个OneBot12账户

## v5 范式更新（4.3.0）

本适配器已完成 v5 范式对齐（增量升级，API 兼容）：

- **BaseConverter 继承**：转换器公共字段（id/time/platform/self/raw）由框架 build_base_event 构建，按 OB11 字段名（echo/time/self_id）覆盖
- **spawn_background 任务归属**：Client 模式连接任务改用 Runtime.spawn_background（owner 归属，shutdown 自动回收）
- **框架软依赖**：安装适配器不再声明 ErisPulse 硬依赖，避免 pip 解析时调整框架版本；运行时检测 ErisPulse>=2.7.1 并在版本过低时打日志提示
- **启动版本日志**：初始化时输出 OneBot12Adapter vX.Y.Z 已加载

已有能力（4.2.0 起支持）：多账户、Api DSL 标准动作映射（get_self_info→get_login_info 等）、Request DSL（好友/群请求审批：event.approve() / event.reject()）、EventMixin、i18n。

## 标准化对齐

本节说明适配器与 ErisPulse 标准化规范对齐的行为。规范详情参见 SDK 文档《请求操作规范》（`docs/zh-CN/standards/request-action-spec.md`）与《API 响应规范》（`docs/zh-CN/standards/api-response.md`）。

### 请求事件与 Request DSL

- **request_id 保障**：请求事件透传时保障顶层 `request_id` 字段（优先原生 `request_id`，OB11 风格实现回退映射 `flag` 字段；两者皆无时不合成），供 Request DSL 使用
- **缺省账户回退**：`Request` DSL（基于 `handle_quick_request` 动作）未显式 `Using()` 指定账户时，回退使用请求事件的来源账户（`request_context`），确保事件链内 `event.approve()`/`event.reject()` 正确路由

### call_api 错误处理

- 账户未连接或连接已关闭时，`call_api` 不再抛出 `ConnectionError`，而是返回标准失败响应（`status="failed"`、`retcode=33001`）
- API 调用超时同样返回标准失败响应（`retcode=33001`）

### 账户字段双兼容与 send_context

- `call_api` 同时接受标准字段 `account_id` 与旧字段名 `_account_id`（标准名优先）；框架 ApiDSL 自动适配，模块代码推荐使用 `account_id`
- `Send`/`Recall`/`Edit`/`Batch` 全方法读取 `send_context`：事件链内自动使用当前事件来源账户，显式 `Using()` 指定的账户优先

### 事件字段注入

- 所有事件注入 `self.account_id`（来源账户名），多账户模式下事件可正确回路由到来源账户
- 所有事件必含 `onebot12_raw_type` 字段（原始事件类型，符合事件转换规范）
- 表情包/贴纸消息段名为 `onebot12_sticker`（`.Sticker()` 方法内部发送该段）

### 错误码规范

| retcode | 含义 | 触发场景 |
|---------|------|----------|
| 0 | 成功 | 动作执行成功 |
| 33001 | 网络错误 | 账户未连接、连接已关闭、API 调用超时 |
| 10002 | 不支持的动作 | 后端不支持的动作请求 |
| 10003 | 参数错误 | 缺少必要参数 |

> 后端返回的原始响应数据保留在 `onebot12_raw` 字段。

---
## 标准Api动作（Api DSL）

OneBot12 后端原生支持所有 OB12 标准动作名，Api DSL 默认直接委托 call_api 透传（无需映射）：

```python
from ErisPulse import sdk
ob12 = sdk.adapter.get("onebot12")

result = await ob12.Api.get_self_info()
result = await ob12.Api.get_friend_list()
await ob12.Api.delete_message(message_id="MSG_ID")

# 指定账户（多账户）
result = await ob12.Api.Using("main").get_self_info()

# 平台扩展动作
result = await ob12.Api.call("extend_action", param=1)
```

> 支持的动作以后端实现为准（NapCat/Lagrange/LLOneBot 等）；不支持的动作由后端返回错误并透传。

---

## 请求操作（Request DSL）

基于 OneBot12 标准的 handle_quick_request 动作，处理好友请求与加群邀请的同意/拒绝：

### Event 便捷方法

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    if event.get("platform") != "onebot12":
        return
    comment = event.get("comment", "")
    if comment == "passphrase":
        await event.approve()      # 同意
    else:
        await event.reject()       # 拒绝
```

### 手动调用 Request DSL

```python
await ob12.Request("request_flag").accept()
await ob12.Request("request_flag").reject()
await ob12.Request("request_flag").Using("main").accept()
```

---
## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# 使用默认账户发送
await onebot12.Send.To("group", group_id).Text("Hello World!")

# 指定特定账户发送
await onebot12.Send.To("group", group_id).Account("main").Text("来自主账户的消息")
```

### 大小写不敏感调用

所有发送方法和链式修饰方法均支持大小写不敏感调用，适配器会自动映射到正确的标准方法名：

```python
# 以下所有调用方式等价
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# 链式修饰方法同样支持
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### 不支持的方法调用

当调用不存在的方法时，适配器会返回友好的文本提示，而不是抛出异常：

```python
# 调用不支持的方法
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# 返回的结果是发送的文本消息
# 消息内容: [不支持的发送类型] 方法名: UnsupportedMethod, 参数: [args[0]: 'test']
```

### 基础消息类型

- `.Text(text: str)`：发送纯文本消息
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：发送图片消息（支持URL、Base64或bytes）
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`：发送音频消息
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")`：发送语音消息（Audio的别名，兼容OneBot11）
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：发送视频消息

### 链式修饰方法（返回self支持链式调用）

- `.At(user_id: Union[str, int])`：@用户（可多次调用）
- `.AtAll()`：@全体成员
- `.Reply(message_id: Union[str, int])`：回复消息

### 原始消息发送

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)`：发送OneBot12原始格式消息（符合命名规范）

### 其他消息类型

- `.Sticker(file_id: str)`：发送表情包/贴纸（`onebot12_sticker` 消息段）
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`：发送位置

### 管理功能

- `.Recall(message_id: Union[str, int])`：撤回消息
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`：编辑消息
- `.Raw(message_segments: List[Dict])`：发送原生OneBot12消息段
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`：批量发送消息

## OneBot12标准事件

OneBot12适配器完全遵循OneBot12标准，事件格式无需转换，直接提交到框架。

### 新增特性：原始事件类型字段

符合 `standards/event-conversion.md` 规范，所有事件都会保留原始事件类型字段 `onebot12_raw_type`：

```python
{
    "id": "event-id",
    "type": "message",              # 事件类型
    "onebot12_raw_type": "message", # 原始事件类型（与type相同）
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}
```

### 消息事件 (Message Events)

```python
# 私聊消息
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}

# 群聊消息
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "group_id": "group-id",
    "message": [{"type": "text", "data": {"text": "Hello group"}}],
    "alt_message": "Hello group",
    "time": 1234567890
}
```

### 通知事件 (Notice Events)

```python
# 群成员增加
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_increase",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "approve",
    "time": 1234567890
}

# 群成员减少
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_decrease",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "leave",
    "time": 1234567890
}
```

### 请求事件 (Request Events)

```python
# 好友请求
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "申请消息",
    "request_id": "request-flag",
    "flag": "request-flag",
    "time": 1234567890
}

# 群邀请请求
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "申请消息",
    "request_id": "request-flag",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### 元事件 (Meta Events)

```python
# 生命周期事件
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# 心跳事件
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "heartbeat",
    "self": {"user_id": "bot-id"},
    "interval": 5000,
    "status": {"online": true},
    "time": 1234567890
}
```

## 配置选项

### 账户配置

每个账户独立配置以下选项：

- `mode`: 该账户的运行模式 ("server" 或 "client")
- `server_path`: Server模式下的WebSocket路径
- `server_token`: Server模式下的认证Token（可选）
- `client_url`: Client模式下要连接的WebSocket地址
- `client_token`: Client模式下的认证Token（可选）
- `enabled`: 是否启用该账户
- `platform`: 平台标识，默认为 "onebot12"
- `implementation`: 实现标识，如 "go-cqhttp"（可选）

### 配置示例

```toml
[OneBotv12_Adapter.accounts.main]
mode = "server"
server_path = "/onebot12-main"
server_token = "main_token"
enabled = true
platform = "onebot12"
implementation = "go-cqhttp"

[OneBotv12_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true
platform = "onebot12"
implementation = "shinonome"

[OneBotv12_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### 默认配置

如果未配置任何账户，适配器会自动创建：

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## 发送方法返回值

### 消息发送方法
所有消息发送方法（如 `.Text()`, `.Image()`, `.Raw_ob12()` 等）均返回一个 `asyncio.Task` 对象，可以直接 await 获取发送结果：

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### 链式修饰方法
所有链式修饰方法（如 `.At()`, `.AtAll()`, `.Reply()`）均返回 `self`，支持链式调用：

```python
# 组合使用多个修饰方法
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("文本")
```

## API响应标准

适配器遵循 ErisPulse 标准化返回规范（`standards/api-response.md`）：

```python
# 成功响应
{
    "status": "ok",              // 必须：执行状态
    "retcode": 0,                // 必须：返回码（0表示成功）
    "data": {                     // 必须：响应数据
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       // 必须：消息ID（无则为空字符串）
    "message": "",                // 必须：错误信息（成功时为空）
    "echo": "1234",               // 可选：原样返回请求中的echo
    "onebot12_raw": {...}        // 可选：原始响应数据
}

# 失败响应
{
    "status": "failed",           // 必须：执行状态
    "retcode": 10003,            // 必须：返回码（非0表示失败）
    "data": None,                // 必须：失败时为null
    "message_id": "",            // 必须：失败时为空字符串
    "message": "缺少必要参数",    // 必须：错误描述
    "echo": "1234",              // 可选：原样返回请求中的echo
    "onebot12_raw": {...}        // 可选：原始响应数据
}
```

### 错误码规范

遵循 OneBot12 标准错误码：

- **0**: 成功
- **1xxxx**: 动作请求错误
- **2xxxx**: 动作处理器错误
- **3xxxx**: 动作执行错误（33001为网络超时）

### 多账户发送语法

```python
# 账户选择方法
await onebot12.Send.Using("main").To("group", 123456).Text("主账户消息")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API调用方式
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## 异步处理机制

OneBot12适配器采用异步非阻塞设计：

1. 消息发送不会阻塞事件处理循环
2. 多个并发发送操作可以同时进行
3. API响应能够及时处理
4. WebSocket连接保持活跃状态
5. 多账户并发处理，每个账户独立运行

## 错误处理

适配器提供完善的错误处理机制：

1. 网络连接异常自动重连（支持每个账户独立重连，间隔30秒）
2. API调用超时处理（固定30秒超时，超时返回 `retcode=33001` 标准失败响应）
3. 账户未连接/连接已关闭时 `call_api` 返回 `retcode=33001` 标准失败响应，不再抛出 `ConnectionError`
4. 不支持的方法调用会返回友好的文本提示

## 事件处理增强

多账户模式下，所有事件都会自动添加账户信息：

```python
{
    "type": "message",
    "onebot12_raw_type": "message",  // 原始事件类型
    "detail_type": "private",
    "self": {"user_id": "123456"},  // 发送事件的账户ID（标准字段）
    "platform": "onebot12",
    // ... 其他事件字段
}
```

## 管理接口

```python
# 获取所有账户信息
accounts = onebot12.accounts

# 检查账户连接状态
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# 动态启用/禁用账户（需要重启适配器）
onebot12.accounts["test"].enabled = False
```

## OneBot12标准特性

### 消息段标准

OneBot12使用标准化的消息段格式：

```python
# 文本消息段
{"type": "text", "data": {"text": "Hello"}}

# 图片消息段
{"type": "image", "data": {"file_id": "image-id"}}

# 提及消息段
{"type": "mention", "data": {"user_id": "user-id", "user_name": "Username"}}

# 回复消息段
{"type": "reply", "data": {"message_id": "msg-id"}}
```

### API标准

遵循OneBot12标准API规范：

- `send_message`: 发送消息
- `delete_message`: 撤回消息
- `edit_message`: 编辑消息
- `get_message`: 获取消息
- `get_self_info`: 获取自身信息
- `get_user_info`: 获取用户信息
- `get_group_info`: 获取群组信息

## 最佳实践

1. **配置管理**: 建议使用多账户配置，将不同用途的机器人分开管理
2. **错误处理**: 始终检查API调用的返回状态
3. **消息发送**: 使用合适的消息类型，避免发送不支持的消息
4. **连接监控**: 定期检查连接状态，确保服务可用性
5. **性能优化**: 批量发送时使用Batch方法，减少网络开销
6. **方法调用**: 推荐使用标准的大驼峰命名（如 `.Text()`），但也支持小写形式以兼容不同编程风格(这种方式可能会不兼容旧版本)
