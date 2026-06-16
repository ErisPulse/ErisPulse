# 平台特性说明 — Webhook 通用桥接适配器

本文档详细说明 Webhook 适配器的双向桥接协议、字段映射与实现特性。

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
| `user_id` | `user_id` | 透传 |
| `user_nickname` | `user_nickname` | 透传（可选） |
| `group_id` | `group_id` | 透传（可选） |
| `message` | `message` | 透传 |
| 完整 body | `webhook_raw` | 原始请求 |
| 账户名 | `webhook_account` | 产生事件的账户名 |
| `type` 或 `message` | `webhook_raw_type` | 原始事件类型 |

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
| `Json(data)` | 原始 JSON 透传，封装为 `[{"type":"json","data":{"raw":data}}]` |

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

1. **单向出站**：若 `outgoing_url` 留空，该账户仅作入站接收，发送操作会返回错误
2. **密钥安全**：`secret` 在配置中以密文存储（metadata secret），传输建议使用 HTTPS
3. **路径唯一**：多个账户的 `callback_path` 必须互不相同，避免路由冲突
4. **幂等性**：适配器不保证入站事件去重，外部系统应自行处理重试
5. **超时**：出站请求使用 ErisPulse 内置 `client`，继承全局超时配置
