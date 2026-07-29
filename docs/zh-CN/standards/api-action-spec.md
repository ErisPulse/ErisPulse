# ErisPulse API 动作标准

本文档定义 ErisPulse 适配器中 **OneBot12 标准 API 动作**的统一接口规范，使模块开发者可以面向标准接口编程，由适配器负责映射到平台原生 API。

## 1. 设计背景

在 ErisPulse 中，消息段（消息收发）和事件格式已经完全遵循 OneBot12 标准，但 **API 动作调用**（如获取用户信息、获取群列表、撤回消息等）此前未统一——模块开发者必须为每个平台写不同的 `call_api` 调用。

`ApiDSL` 通过提供强类型的标准动作方法，解决这一问题：

```
模块代码（跨平台统一）             适配器实现（平台特定）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  适配器 call_api / 覆盖
adapter.Api.get_group_list()      →  适配器 call_api / 覆盖
adapter.Api.delete_message("id")  →  适配器 call_api / 覆盖
```

## 2. 三层 DSL 并行结构

ErisPulse 适配器有三个并行的 DSL 内部类，各司其职：

```
BaseAdapter
├── Send(SendDSL)       ← 消息发送（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← 请求操作（accept/reject）
└── Api(ApiDSL)          ← 标准 API 动作（信息查询/群管理/消息管理/文件操作）★
```

| DSL | 职责 | 方法风格 | 返回值 |
|-----|------|---------|--------|
| `Send` | 发送消息 | 链式 + `asyncio.Task` | 标准响应 |
| `Request` | 处理请求事件 | `asyncio.Task` | 标准响应 |
| `Api` | 查询/管理操作 | `async` 方法 | 标准响应 |

## 3. 标准动作列表

### 3.1 用户相关

| 方法 | OB12 动作 | 参数 | data 返回 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | 无 | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | 无 | `list[get_user_info 响应]` |

### 3.2 群组相关

| 方法 | OB12 动作 | 参数 | data 返回 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | 无 | `list[get_group_info 响应]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info 响应]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | 无 |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | 无 |

### 3.3 消息管理

| 方法 | OB12 动作 | 参数 | 说明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | 撤回/删除消息 |

> **发送消息**（`send_message`）由 `SendDSL` 的 `Raw_ob12` 处理，不在 `ApiDSL` 中重复。

### 3.4 文件操作

| 方法 | OB12 动作 | 参数 | data 返回 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` 的 `type` 参数：
- `"url"`：通过 URL 上传（需提供 `url`）
- `"path"`：通过本地路径上传（需提供 `path`）
- `"data"`：通过二进制数据上传（需提供 `data`）

### 3.5 通用扩展动作

| 方法 | 说明 |
|------|------|
| `call(action, **params)` | 平台扩展动作的逃生舱，遵循 OB12 扩展命名规则 `{prefix}.{action}` |

## 4. 使用方式

### 4.1 基本调用

```python
from ErisPulse import adapter

# 获取用户信息（跨平台统一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"用户名: {user_name}")

# 获取群列表
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# 撤回消息
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 指定 Bot 账号（多账户模式）

```python
# 使用指定 Bot 账号执行操作
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 平台扩展动作

```python
# 调用平台特有的扩展动作（建议使用 {prefix}.{action} 命名）
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 在事件处理器中使用

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # 获取发送者详细信息
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"你好，{user_name}！")
```

## 5. 适配器实现

### 5.1 默认行为（零配置）

`ApiDSL` 的默认实现将标准动作名作为 `endpoint` 直接传递给 `adapter.call_api()`：

```python
# ApiDSL 默认实现等价于：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**适用场景**：适配器后端本身就是 OneBot12 实现（如 NapCat、Lagrange 等），`call_api` 天然支持标准动作名。

### 5.2 覆盖标准方法（映射到平台原生 API）

适配器可覆盖单个标准方法，将其映射到平台原生 API：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 标准 API 动作实现"""

        async def get_user_info(self, user_id: str) -> dict:
            # 映射到平台原生 API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34001, message="用户不存在")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 未支持的动作

适配器未覆盖的标准方法走默认实现（委托给 `call_api`）。如果 `call_api` 也不支持该动作，应返回标准错误响应：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"不支持的动作: {endpoint}")
    # ... 平台 API 调用
```

模块开发者可通过返回值的 `retcode` 判断是否支持：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("该平台不支持获取好友列表")
```

## 6. 响应格式

所有 `ApiDSL` 方法返回标准 API 响应格式（详见 [API 响应标准](api-response.md)）：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **注意**：信息查询类动作的 `message_id` 为空字符串（仅消息发送类动作才有 `message_id`）。

## 7. 与 SendDSL / RequestDSL 的关系

| 场景 | 使用 DSL | 示例 |
|------|---------|------|
| 发送消息 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| 同意/拒绝请求 | `Request` | `adapter.Request("req_id").accept()` |
| 获取用户/群信息 | `Api` | `adapter.Api.get_user_info("123")` |
| 撤回消息 | `Api` | `adapter.Api.delete_message("msg_id")` |
| 退出群 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. 适配器实现检查清单

### 标准动作
- [ ] `call_api` 能处理标准动作名（或覆盖对应 `ApiDSL` 方法）
- [ ] 不支持的动作返回 `retcode=10002`
- [ ] 返回值遵循标准 API 响应格式
- [ ] `data` 字段包含 OB12 标准定义的字段

### 扩展动作
- [ ] 平台扩展动作使用 `{prefix}.{action}` 命名
- [ ] 扩展动作的参数和响应仍遵循 OB12 动作请求/响应结构

## 9. 相关文档

- [API 响应标准](api-response.md) - 适配器 API 响应格式标准
- [发送方法规范](send-method-spec.md) - Send 类的方法命名和参数规范
- [请求操作规范](request-action-spec.md) - Request DSL 的使用方式
- [事件转换标准](event-conversion.md) - 事件格式和消息段标准
