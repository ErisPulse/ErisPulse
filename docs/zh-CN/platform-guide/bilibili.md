# Bilibili 平台特性文档

BilibiliAdapter 是基于 bilibili-api-python 的 B 站私信适配器，支持 Cookie / 扫码双登录与事件驱动的私信收发。

---

## 文档信息

- 对应模块版本: 0.1.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：B 站私信机器人（无官方个人 Bot API，通过模拟登录使用 Web 私信接口）
- 适配器名称：BilibiliAdapter
- 多账户支持：支持（每账户一个 B 站账号，独立会话监听）
- 连接方式：事件驱动会话监听（bilibili-api `Session`）
- 认证方式：Cookie（SESSDATA / bili_jct / buvid3 / dedeuserid）或面板扫码登录
- 链式修饰支持：支持 `.Reply()` 等链式修饰方法
- OneBot12 兼容：支持标准消息段（text / image）

## 配置说明

```toml
[BilibiliAdapter.accounts.default]
login_mode = "cookie"          # cookie=手填凭据 / qrcode=面板扫码（推荐）
sessdata = "YOUR_SESSDATA"     # cookie 模式必填
bili_jct = "YOUR_BILI_JCT"     # cookie 模式必填
buvid3 = "YOUR_BUVID3"         # 可选，降低风控概率
dedeuserid = "YOUR_UID"        # 可选，即账号 UID
bot_id = ""                    # 留空登录后自动获取
enabled = true
```

**配置项说明（每个账户）：**

- `login_mode`：登录方式。`cookie` 手填凭据；`qrcode` 面板扫码（推荐）。两种模式的凭据最终都落在 sessdata/bili_jct 等字段
- `sessdata` / `bili_jct`：登录态 Cookie（cookie 模式必填；面板中密码形态显示）
- `buvid3`：设备指纹 Cookie（可选），携带后可显著降低风控概率
- `dedeuserid`：账号 UID（可选），同时作为 `bot_id` 的默认来源
- `bot_id`：账号 UID，留空则在登录后通过 `get_self_info` 自动获取

**扫码登录流程**：`login_mode = "qrcode"` 保存后，在 Dashboard → 组件配置 → 添加账户向导中选择「扫码登录 B 站」→ B 站 APP 扫码 → 手机确认 → 适配器轮询登录状态（scan → confirm → done），凭据自动写入该账户配置并生效。

> 适配器同时注册 `POST /bilibili/qr/start`（获取二维码，返回图片 URL + 会话令牌）与 `POST /bilibili/qr/poll`（轮询登录状态）端点，第三方前端也可直接对接。轮询请求需携带 start 返回的 `poll_token`，防止未授权轮询。

## 消息发送

所有发送方法返回 Task，await 后得到标准响应（见「返回值格式」）。

### 基础发送

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# 文本私信（target 为对方 UID）
await bili.Send.To("user", "123456789").Text("Hello Bilibili!")

# 图片私信（URL 或本地路径，转 B 站私信图片）
await bili.Send.To("user", "123456789").Image("https://example.com/pic.jpg")
await bili.Send.To("user", "123456789").Image("./local.png")
```

### 链式修饰方法

```python
# 回复指定消息（msg_key 来自收到消息的 message_id）
await bili.Send.To("user", "123456789").Reply("msg_key").Text("收到！")
```

### OneBot12 标准段发送

```python
message = [
    {"type": "text", "data": {"text": "第一行"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}},
]
await bili.Send.To("user", "123456789").Raw_ob12(message)
```

### 多账户发送

```python
await bili.Send.Using("account2").To("user", "123456789").Text("来自第二个账号")
```

### 支持与不支持的消息段

| 段 | 支持 | 说明 |
|----|------|------|
| `text` | 支持 | 拼接后通过 `send_msg`（TEXT）发送 |
| `image` | 支持 | `file` 为 URL / 本地路径，通过 `send_msg`（PICTURE）发送 |
| `reply` | 部分支持 | 修饰器接受，B 站私信无引用展示，仅作发送上下文 |
| `mention` / `face` / `voice` / `video` / `file` 等 | 不支持 | 返回 `retcode=10002` 并列出收到的段类型 |

## 标准 API 动作（Api）

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# 自身信息（昵称/头像/UID）
result = await bili.Api.get_self_info()

# 用户公开信息（任意用户，昵称/头像）
result = await bili.Api.get_user_info("123456789")

# 拉取指定会话的历史消息（begin_seqno 用于翻页）
result = await bili.Api.get_session_msgs("123456789", begin_seqno=0)

# 状态与版本
result = await bili.Api.get_status()
result = await bili.Api.get_version()

# 多账户
result = await bili.Api.Using("account2").get_self_info()
```

### 支持的标准动作

| 方法 | 说明 | 数据来源 |
|------|------|---------|
| `get_self_info()` | 自身信息（mid/name/face） | Web API（空间信息） |
| `get_user_info(user_id)` | 用户公开信息（昵称/头像） | Web API（用户信息卡） |
| `get_session_msgs(talker_id, begin_seqno)` | 会话历史消息 | Web 私信接口（session_msgs） |
| `get_status()` | 适配器运行状态 | 本地 |
| `get_version()` | 适配器版本 | 本地 |

### 不支持的标准动作

以下标准动作 B 站私信无对应能力，调用返回 `retcode=10002`：

- `get_friend_list` / `get_group_list` / `get_group_member_info`
- `delete_message`（B 站私信仅对方可撤回自己的消息）
- `set_group_name` / `leave_group` 等群管理类

### 通用动作入口

```python
# send_message：文本与图片段组合发送（等价于 Send 链）
result = await bili.call_api(
    "send_message",
    _account_id="default",
    target_id="123456789",
    message=[{"type": "text", "data": {"text": "hi"}}],
)
```

## 返回值格式

所有发送与 API 方法遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",              # ok / failed
    "retcode": 0,                # 0 成功；10002 不支持；10003 参数/目标错误；33100 B 站接口错误
    "data": {...},               # 响应数据（send_msg 原始返回）
    "self": {"platform": "bilibili", "user_id": "..."},
    "message_id": "123456",      # B 站 msg_key
    "message": "",               # 错误信息
    "bilibili_raw": {...}        # 原始响应
}
```

## 事件类型

需要 `platform == "bilibili"` 检测再使用本平台特性。

### 事件映射

| B 站私信事件 | Adapter 事件 | 说明 |
|--------------|--------------|------|
| TEXT（文本消息） | message（text 段） | 常规私聊文本 |
| PICTURE（图片消息） | message（image 段） | content.pictures → image 段（URL） |
| WITHDRAW（撤回） | 仅记录日志 | 对方撤回消息 |

### 事件字段示例

```python
{
  "id": "uuid",
  "time": 1793277000,
  "type": "message",
  "detail_type": "private",
  "platform": "bilibili",
  "self": {"platform": "bilibili", "user_id": "10000", "user_name": "Bot昵称", "account_id": "default"},
  "user_id": "123456789",                  # 对方 UID（sender_uid）
  "user_nickname": "小王",                  # content.sender_name（可能缺失）
  "message": [{"type": "text", "data": {"text": "你好"}}],
  "alt_message": "你好",
  "bilibili_raw": {...},                   # B 站原始私信数据
  "bilibili_raw_type": "text"              # text / picture
}
```

### 扩展字段说明

- 所有特有字段均以 `bilibili_` 前缀标识（`bilibili_raw` / `bilibili_raw_type`）
- 接收图片为 image 段，`data.file` 是 B 站图床 URL
- `user_nickname` 来自消息 content 的 `sender_name`，部分消息类型可能缺失

## 注意事项

1. **B 站无官方个人 Bot API**：本适配器通过模拟登录使用 Web 私信接口，属非官方用法，接口可能随 B 站更新变动
2. **风控**：高频/批量私信极易触发风控（账号私信功能被临时禁言）。请务必在模块侧做节流；`buvid3` 携带后可降低概率
3. **登录态失效**：Cookie 过期后适配器会记录错误日志，请重新扫码或更新 Cookie；凭据面板中密码形态显示
4. 单聊限制：仅支持一对一私信；粉丝群聊暂不支持
5. 合规：请勿用于骚扰、营销群发等违规用途，遵守 B 站社区规则
