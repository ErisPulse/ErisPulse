# Webhook 通用桥接适配器平台特性文档

WebhookAdapter 是一个协议级双向桥接适配器，不绑定任何特定平台：入站将外部系统 POST 的 JSON 转为 OneBot12 事件，出站将模块 Send 转为 POST 到外部系统。

---

## 文档信息

- 对应模块版本: 4.3.2
- 维护者: ErisPulse
- 最后更新: 2026-11-10

## 基本信息

- 平台简介：任意能发起 HTTP 请求的系统均可通过本适配器接入 ErisPulse
- 适配器名称：WebhookAdapter
- 平台标识：`webhook`
- 多账户支持：每个账户是独立的桥接配置（bot_id / callback_path / outgoing_url / secret）
- 框架要求：软依赖 `ErisPulse>=2.7.1`（运行时检测提示，不强制）

## 已对接平台能力

- **入站**：外部系统 POST 到 callback_path → 转为 OneBot12 事件（json/text 段透传）
- **出站**：模块 Send → POST 到 outgoing_url（双桥接）
- **API**：桥接身份信息与运行状态（最小集）

## v5 范式更新（4.2.0）

- **Api DSL 最小集**：get_self_info/get_status/get_version/get_supported_actions
- **框架软依赖**：运行时检测 ErisPulse>=2.7.1 并提示；启动输出版本日志
- 导入路径更新至 Core.Bases

## 标准化对齐（4.3.2）

响应结构与错误码遵循 [API 响应规范](../../standards/api-response.md)。

### 事件字段

- **消息事件补齐顶层 `message_id`**：优先透传入站 body 的 `message_id`，缺失时以 uuid 兜底（避免下游按 message_id 去重/回复时拿到空值）
- **事件注入 `self.account_id`**（账户名）：多账户场景下 `event.reply()` 自动路由到受理该事件的账户
- **`alt_message` 空串兜底**：入站未提供时补空串，保证标准字段完整
- **JSON 段名改为 `webhook_json`**：未加平台前缀的裸 `json` 段统一归一为 `webhook_json`（遵循平台扩展段命名规则）
- Converter 复用框架 `BaseConverter`（公共字段由 `build_base_event` 统一构建）
- `get_self_info` 补齐标准字段：`user_id`（账户 bot_id）/ `user_name` / `user_displayname`（`webhook:{账户名}`）

### 错误码规范

| retcode | 含义 | 说明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | 网络错误 | 出站 POST 目标失败（连接/超时等） |
| 10003 | 参数错误 | 出站 URL 未配置、参数缺失等 |

### 账户与多账户

- `call_api` 支持双兼容账户字段：`account_id`（标准名）/ `_account_id`（旧名），框架 ApiDSL（`Api.Using(...)`）自动适配
- `Send` 读取 `send_context`（事件账户兜底）：从事件上下文调用 `Send` 时默认回落到来源账户

## 总览

Webhook 适配器是一个**协议级桥接器**，不绑定任何特定平台。它通过 HTTP 收发消息，使任何能发起 HTTP 请求的系统都能接入 ErisPulse。

```
入站方向                                出站方向
────────                                ────────
外部系统                                ErisPulse 模块
   │                                       │
   │ POST JSON                             │ Send.Text(...)
   ▼                                       ▼
┌──────────────────────────────────────────────────┐
│              WebhookAdapter                       │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ 入站路由          │   │ 出站转发          │    │
│  │ GET  (健康检查)   │   │ client.post()    │    │
│  │ POST (接收事件)   │   │ → outgoing_url   │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
│           │                      │               │
│           ▼                      │               │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ WebhookConverter │   │ Send 类          │    │
│  │ JSON → OneBot12  │   │ 消息段 → JSON    │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
└───────────┼──────────────────────┼───────────────┘
            ▼                      │
     adapter.emit(event)    call_api("send_message")
            │                      │
            ▼                      │
       ErisPulse 事件系统 ◄────────┘
```

## 多账户模型

每个账户是一个独立的桥接配置，互不干扰：

| 账户 | bot_id | callback_path | outgoing_url | secret |
|------|--------|---------------|--------------|--------|
| `default` | `webhook_bot` | `/webhook/default` | `https://a.com/recv` | `key1` |
| `discord` | `discord_bot` | `/webhook/discord` | `https://b.com/send` | `key2` |

每个账户启动时独立注册路由、独立 emit connect。

### 账户配置字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `bot_id` | 否 | Bot 身份 ID（由此桥接表示） |
| `callback_path` | 否 | 入站回调路径（支持 `{account}` 占位符） |
| `outgoing_url` | 否 | 出站目标 URL（模块发送消息时 POST 到此地址） |
| `secret` | 否 | 鉴权密钥（留空则禁用验证；配置面板中以密文存储） |

## 入站协议

### 1. 健康检查（GET）

- **路径**：`{callback_path}`
- **方法**：`GET`
- **鉴权**：无
- **响应**：

```json
{"status": "ok", "account": "default"}
```

### 2. 接收事件（POST）

- **路径**：`{callback_path}`
- **方法**：`POST`
- **Content-Type**：`application/json`
- **鉴权**（配置 secret 时）：Header `X-Webhook-Secret` 或 Query `?secret=`

#### 请求 Body

```json
{
  "user_id": "u123",
  "user_nickname": "用户名",
  "group_id": "群组ID（仅群组会话）",
  "detail_type": "private",
  "message_id": "可选，透传为事件 message_id（缺失时自动生成 uuid）",
  "alt_message": "可选，纯文本备援",
  "message": [
    {"type": "text", "data": {"text": "消息内容"}}
  ],
  "raw": {}
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `user_id` | 是 | 发送者 ID |
| `user_nickname` | 否 | 发送者昵称 |
| `group_id` | 否 | 群组/频道 ID（群组会话时提供） |
| `detail_type` | 否 | 会话类型（`private`/`group`），缺省用账户默认 |
| `message_id` | 否 | 消息 ID，透传为事件顶层 `message_id`（缺失时 uuid 兜底） |
| `alt_message` | 否 | 纯文本备援，缺失时空串兜底 |
| `message` | 是 | OneBot12 消息段数组 |
| `raw` | 否 | 原始数据，原样存入 `webhook_raw` |

#### 响应

```json
{"status": "ok"}
```

错误响应带 HTTP 状态码：

| 状态码 | 含义 |
|--------|------|
| 400 | 无效 JSON / body 非对象 |
| 401 | 鉴权失败 |
| 404 | 未知账户 |
| 500 | 事件分发失败 |

### 3. 字段映射（入站 JSON → OneBot12 事件）

| 入站 JSON | OneBot12 事件字段 | 说明 |
|-----------|-------------------|------|
| — | `id` | 自动生成 |
| — | `time` | 当前 Unix 时间戳（秒） |
| — | `type` | 固定 `message` |
| `detail_type` | `detail_type` | 缺省用账户默认值 |
| — | `platform` | 固定 `webhook` |
| — | `self.platform` | 固定 `webhook` |
| — | `self.user_id` | 账户 `bot_id` |
| — | `self.account_id` | 账户名（4.3.2 注入，多账户路由） |
| `user_id` | `user_id` | 透传 |
| `user_nickname` | `user_nickname` | 透传（可选） |
| `group_id` | `group_id` | 透传（可选） |
| `message_id` | `message_id` | 透传，缺失时 uuid 兜底（4.3.2） |
| `alt_message` | `alt_message` | 透传，缺失时空串兜底（4.3.2） |
| `message` | `message` | 透传 |
| 完整 body | `webhook_raw` | 原始请求 |
| 账户名 | `webhook_account` | 产生事件的账户名 |
| `type` 或 `message` | `webhook_raw_type` | 原始事件类型 |

> 裸 `json` 段（`{"type": "json", ...}`）在入站/出站两侧均归一为 `webhook_json` 段。

## 出站协议

### 1. 发送消息

当模块调用 `Send.To(...).Text(...)` 等方法时，适配器向 `outgoing_url` 发起 POST：

- **方法**：`POST`
- **Content-Type**：`application/json`
- **鉴权 Header**（配置 secret 时）：`X-Webhook-Secret: {secret}`

#### 请求 Body

```json
{
  "target_type": "private",
  "target_id": "target_user_id",
  "account": "default",
  "message": [
    {"type": "text", "data": {"text": "消息内容"}}
  ],
  "timestamp": 1700000000
}
```

| 字段 | 说明 |
|------|------|
| `target_type` | 目标类型（来自 `Send.To(type, id)`），缺省用账户默认 |
| `target_id` | 目标 ID（来自 `Send.To`） |
| `account` | 发送账户名 |
| `message` | OneBot12 消息段数组 |
| `timestamp` | 发送时间戳（秒） |

### 2. 响应标准化

适配器把出站目标返回的响应标准化为 ErisPulse 标准响应格式：

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "...", ...},
  "message_id": "...",
  "message": "",
  "webhook_raw": {}
}
```

从目标响应 JSON 的 `message_id` 字段提取消息 ID。若目标未返回 `message_id`，则为空字符串。

请求失败时返回错误响应（`status: "failed"`, `retcode: 33001`）。

## Send 方法

| 方法 | 说明 |
|------|------|
| `Text(text)` | 发送文本，封装为 `[{"type":"text","data":{"text":text}}]` |
| `Image(file)` | 发送图片，封装为 `[{"type":"image","data":{"file":file}}]` |
| `Raw_ob12(message)` | 发送 OneBot12 原始消息段 |
| `Json(data)` | 原始 JSON 透传，封装为 `[{"type":"webhook_json","data":{"raw":data}}]` |

`At` / `AtAll` / `Reply` 修饰器由框架基类提供，通过 `_apply_modifiers` 合并到消息段。

## 事件扩展方法（WebhookEventMixin）

| 方法 | 说明 |
|------|------|
| `get_raw_data()` | 获取原始请求 body（`webhook_raw`） |
| `get_detail_type()` | 获取会话类型 |
| `get_webhook_account()` | 获取产生该事件的账户名 |

## 特性矩阵

| 特性 | 支持情况 |
|------|----------|
| 多账户 | ✅ 每个账户独立桥接 |
| 入站鉴权 | ✅ Header / Query 双模式 |
| 健康检查 | ✅ GET 返回状态 |
| 出站鉴权 | ✅ Header 携带 secret |
| OneBot12 标准事件 | ✅ 完整标准字段 |
| Meta 事件 | ✅ connect / disconnect |
| 路由发现 | ✅ 注册到 `webhook` 命名空间 |
| WebSocket | ❌ 仅 HTTP |
| 媒体上传 | ❌ 通过 URL 透传，不代传二进制 |

## 注意事项

1. **单向出站**：若 `outgoing_url` 留空，该账户仅作入站接收，发送操作会返回错误（`retcode: 10003`）
2. **密钥安全**：`secret` 在配置中以密文存储（metadata secret），传输建议使用 HTTPS
3. **路径唯一**：多个账户的 `callback_path` 必须互不相同，避免路由冲突
4. **幂等性**：适配器不保证入站事件去重，外部系统应自行处理重试
5. **超时**：出站请求使用 ErisPulse 内置 `client`，继承全局超时配置
