# 微信 ClawBot（WechatClaw）适配器 - 平台特性文档

## 基本信息
- 模块名称: `ErisPulse-WechatClaw`
- 平台标识: `wechatclaw`
- 模块版本: 0.1.0
- 维护者: wsu2059q
- 最后更新: 2026-11-17
- 依赖: `qrcode`、`pycryptodome`

## 平台定位

基于**腾讯官方 iLink Bot API**（微信 ClawBot 机器人通道）的微信个人号接入适配器：扫码绑定、令牌自动写回、长轮询接收。官方合规渠道，非逆向协议；能力范围以微信官方开放为准。

## 接入与绑定

- `token` 配置留空时，适配器启动即打印登录二维码（终端 ASCII 图案 + 链接兜底），手机微信扫码确认后完成绑定
- **Dashboard 面板扫码**（推荐）：适配器向「添加账户向导」注册「扫码登录微信」扩展区，面板内直接扫码绑定（对齐 bilibili 适配器的面板扫码约定）
- 绑定成功后 `token` / `bot_user_id` / `base_url` 经框架无损 TOML 引擎自动写回 `config.toml`（保留用户注释），重启免重扫
- 令牌失效（长轮询返回 401/403）时日志明示"清空 token 重新扫码"

### 扫码登录端点（第三方前端可对接）

适配器随启动注册 `POST /wechatclaw/qr/start` 与 `POST /wechatclaw/qr/poll`：

- `qr/start`：获取二维码，返回 `{success, task_id, poll_token, qr_img}`（`qr_img` 为 SVG data URI）
- `qr/poll`：请求携带 `task_id` + `poll_token`（防未授权轮询，缺失返回 403），返回 `{success, status}`，status ∈ `pending` / `scan` / `done` / `timeout`
- `done` 时凭据已自动写入配置，响应附带 `account`

## 标准化对齐

事件与响应遵循 [事件转换标准](../standards/event-conversion.md) 与 [API 响应规范](../standards/api-response.md)。

- 消息事件顶层携带标准 `message_id`（取官方 message_id，缺失回退 client_id/seq）
- 事件 `id` 带账户维度（`{bot_id}:{message_id}`），幂等去重与跨账户隔离由框架处理
- 发送返回标准响应：`status` / `retcode` / `data` / `message_id` / `message` + 顶层 `wechatclaw_raw`

### 消息事件

- 事件类型：`message` / `private`（官方通道为个人号私信，无群聊能力）
- 入站消息段：`text`、`image`、`voice`、`file`、`video`
- 媒体段不落地文件：携带 `wechatclaw_cdn`（CDN 描述 + 密钥），经 `call_api("download_media")` 按需下载解密

### 上下文令牌与回复

协议要求回复携带 `context_token`（随收到的消息下发）。适配器按用户缓存最近上下文：

- 事件链内回复（`event.reply()` / `Send.To("user", ...)`）自动携带该用户上下文
- **主动私信**受协议限制：无会话上下文的用户可能被平台拒绝（响应 errcode 反馈）

## 支持的消息发送类型

| 方法 | 说明 | 官方 API |
|------|------|---------|
| `Text(text)` | 发送文本（Markdown 自动降级纯文本） | `sendmessage` |
| `Image(file)` | 发送图片（URL/路径/base64:///bytes，自动加密上传） | `getuploadurl` + CDN |
| `Video(file)` | 发送视频 | 同上 |
| `File(file)` | 发送文件 | 同上 |
| `Voice(file)` | 发送语音（仅 SILK 编码；其余音频按文件消息降级） | 同上 |
| `Reply(message_id)` | 引用回复（引用目标为该会话最近一条收到的消息） | `sendmessage` + ref_msg |

> `mention` / `at` 段在个人号私信无语义，发送时静默忽略。

## 扩展 API（call_api）

| 端点 | 参数 | 说明 |
|------|------|------|
| `download_media` | `media`（入站媒体段的 `wechatclaw_cdn`） | 下载解密并落盘，`data.path` 返回本地路径 |
| `send_typing` | `user_id`，可选 `status`（1=输入中 2=取消） | "正在输入"状态（需有效会话上下文） |

## 平台限制

- 仅私信（官方通道不开放群聊）
- 部分视频消息可能缺少解密密钥（官方通道已知问题），此类媒体无法下载
- 语音要求 SILK 编码（encode_type=6，24kHz）

## 配置参考

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `token` | "" | 留空即扫码登录，绑定后自动写回 |
| `bot_user_id` | "" | 官方账号 ID，绑定后自动写回 |
| `base_url` | 官方默认 | API 基址，绑定后可能自动更新 |
| `login_timeout` | 300 | 扫码等待时长（秒） |
| `poll_interval` | 1.0 | 长轮询批次间隔（秒，服务端单次挂起约 35 秒） |
