# 企业微信（WeCom）平台特性文档

WeComAdapter 是基于企业微信自建应用 API 构建的适配器，通过回调接收消息、应用消息接口主动发送，并提供通讯录与消息卡片能力。

---

## 文档信息

- 对应模块版本: 0.1.2
- 维护者: ErisPulse
- 最后更新: 2026-11-10

## 基本信息

- 平台简介：企业微信自建应用机器人，适用于企业内部通知、智能问答、办公自动化等场景
- 适配器名称：WeComAdapter
- 平台注册名：`wecom`（别名 `wxwork`）
- 多账户支持：支持同时配置多个企业（每个账户对应一个 corpid + 应用）
- 连接方式：HTTP 回调接收（企业微信后台配置接收消息 URL）+ 主动 API 发送
- 认证方式：corpid + secret 换取 access_token（自动刷新）
- 回调加解密：Token + EncodingAESKey（企业微信官方加解密协议）
- 会话类型映射：应用消息 → `private`（成员私信），应用群聊 → `group`
- 链式修饰支持：支持 `.Reply()` 等链式修饰方法
- OneBot12 兼容：发送支持 OneBot12 标准消息段

## 标准化对齐（0.1.2）

本版本完成适配器标准化对齐，响应结构与错误码遵循 [API 响应规范](../../standards/api-response.md)。

### 账户与多账户

- `call_api` 支持双兼容账户字段：`account_id`（标准名）/ `_account_id`（旧名），框架 ApiDSL（`Api.Using(...)`）自动适配
- **`get_user_info` 等 6 个通讯录 Api 方法（`get_user_info` / `get_department_list` / `get_department_users` / `get_user_by_mobile` / `userid_to_openid` / `openid_to_userid`）已修复 `Using()` 兜底**：账户缺省时回落到 `Api.Using(...)` 指定的账户，不再被忽略
- `Send` 读取 `send_context`（事件账户兜底）：从事件上下文调用 `Send` 时默认回落到来源账户

### 标准字段

- **消息事件补齐顶层 `message_id`**（取企业微信 MsgId，缺失时以 uuid 兜底）
- **`get_user_info` 等查询返回标准化字段**：`user_id` / `user_name` / `user_displayname`，原始数据保留在 `wecom_raw`
- **`get_self_info` 补齐 `user_displayname`**（`user_id` 为 corpid，`user_name` / `user_displayname` 为 `wecom:{账户名}`）
- Converter 复用框架 `BaseConverter`（公共字段 id/time/platform/self/wecom_raw 由 `build_base_event` 统一构建）

### 错误码规范

| retcode | 含义 | 说明 |
|---------|------|------|
| 0 | 成功 | — |
| 34100 | 平台失败 | 企业微信返回失败（errcode != 0）；原始响应保留在 `wecom_raw` |
| 10003 | 参数错误 | 缺少或无效参数 |

## 配置说明

```toml
# config.toml
[WeComAdapter.accounts.default]
corpid = "YOUR_CORP_ID"        # 企业 ID（必填，企业微信后台-我的企业）
secret = "YOUR_APP_SECRET"     # 应用 Secret（必填，自建应用详情页）
agentid = 1000002              # 应用 AgentId（必填，自建应用详情页）
callback_enabled = true        # 启用回调接收（默认 true；关闭后仅能主动发送）
token = "YOUR_CALLBACK_TOKEN"  # 回调验证 Token（企业微信后台接收消息配置）
encoding_aes_key = "YOUR_AES_KEY_43CHARS"  # 回调加解密密钥（43 位）
callback_path = "/wecom/{account}"         # 回调路径，支持 {account} 占位符
enabled = true
```

**配置项说明（每个账户）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `corpid` | string | 是 | 企业 ID |
| `secret` | string | 是 | 应用 Secret |
| `agentid` | int | 建议 | 应用 AgentID |
| `callback_enabled` | bool | 否 | 回调接收开关（默认开启） |
| `token` | string | 否 | 回调验证 Token |
| `encoding_aes_key` | string | 否 | 回调加解密密钥（43 位） |
| `callback_path` | string | 否 | 回调路径，支持 `{account}` 占位符 |
| `enabled` | bool | 否 | 是否启用（默认 true） |

- `corpid` / `secret` / `agentid`：从[企业微信管理后台](https://work.weixin.qq.com)的自建应用页获取（前两项必填）
- `callback_enabled`：回调接收开关（默认开启）。**关闭后适配器跳过回调路由注册，仅保留主动发送能力**；面板中回调相关字段随之隐藏
- `token` / `encoding_aes_key`：回调消息验证与加解密，与企业微信后台「接收消息」配置一致
- `callback_path`：回调接收路径（默认 `/wecom/{账户名}`），企业微信后台需配置完整 URL：`http(s)://你的地址:端口/wecom/<账户名>`

**接收消息前置条件**：企业微信后台 → 自建应用 → 「接收消息」设置 API 接收，URL 填上述完整回调地址，Token 与 EncodingAESKey 与配置一致。**注意**：企业微信要求回调 URL 可公网访问（建议搭配反向代理）。

**API 环境**：
- API 基础地址：`https://qyapi.weixin.qq.com/cgi-bin`
- access_token 自动获取与缓存刷新，无需手动管理

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：

```python
from ErisPulse import sdk
wecom = sdk.adapter.get("wecom")

# 基础消息（target_type: "user"=成员 "group"=应用群聊）
await wecom.Send.To("user", "zhangsan").Text("你好")
await wecom.Send.To("group", "group_chat_id").Markdown("**加粗**通知")

# 媒体（本地路径 / bytes / URL；自动上传临时素材后发送）
await wecom.Send.To("user", "zhangsan").Image("banner.png")
await wecom.Send.To("user", "zhangsan").Voice("voice.amr")
await wecom.Send.To("user", "zhangsan").Video("demo.mp4")
await wecom.Send.To("user", "zhangsan").File("report.pdf")

# 图文与卡片
await wecom.Send.To("user", "zhangsan").News([
    {"title": "标题", "description": "摘要", "url": "https://...", "picurl": "https://.../img.png"},
])  # 最多 8 条

await wecom.Send.To("user", "zhangsan").TextCard(
    title="审批提醒",
    description="您有一条待审批单据",
    url="https://oa.example.com/approval/1",
    btntxt="去处理",
)

await wecom.Send.To("user", "zhangsan").TemplateCard(
    card_type="text_notice",  # 企业微信卡片类型，其余参数按官方卡片 JSON 透传
    source={"icon_url": "...", "desc": "OA"},
    main_title={"title": "会议提醒"},
)

# 被动回复：收到消息的 event.reply() 直接回复来源用户

# 多账户指定账户发送
await wecom.Send.To("user", "UserID", account_id="app2").Text("通过 app2 发送")
```

### 基本发送方法

| 方法 | 说明 | 参数 |
|------|------|------|
| `.Text(text)` | 发送纯文本消息 | `text: str` |
| `.Markdown(content)` | 发送 Markdown 消息（应用消息支持） | `content: str` |

### 媒体发送方法

媒体方法支持 `bytes`（自动上传获取 media_id）和 `str`（已上传的 media_id 或路径/URL）两种输入：

| 方法 | 说明 |
|------|------|
| `.Image(file, filename)` | 发送图片 |
| `.Voice(file, filename)` | 发送语音（需 AMR 格式，企业微信限制） |
| `.Audio(file, filename)` | Voice 的别名 |
| `.Video(file, filename)` | 发送视频 |
| `.File(file, filename)` | 发送文件 |

### 富文本卡片方法

| 方法 | 说明 |
|------|------|
| `.News(articles)` | 发送图文消息（最多 8 条） |
| `.TextCard(title, description, url, btntxt)` | 发送文本卡片 |
| `.TextCardMiniProgram(**kwargs)` | 发送小程序通知卡片 |
| `.TemplateCard(card_type, **kwargs)` | 发送模板卡片 |

### 原始消息发送

- `.Raw_ob12(message: List[Dict])`：发送 OneBot12 标准格式消息

### 链式修饰方法

| 方法 | 说明 |
|------|------|
| `.At(user_id)` | @指定用户（由框架 SendDSL 基类实现） |
| `.AtAll()` | @全体成员（由框架 SendDSL 基类实现） |
| `.Reply(message_id)` | 回复指定消息（由框架 SendDSL 基类实现） |

### 发送目标映射

| OB12 target_type | 企业微信目标字段 | API 接口 |
|---|---|---|
| `user` / `private` | `touser` | `message/send` |
| `group` | `chatid` | `appchat/send` |

## 标准 API 动作

```python
info = await wecom.Api.get_self_info()          # 应用信息（corpid/agentid）
status = await wecom.Api.get_status()           # 运行状态
ver = await wecom.Api.get_version()             # 适配器版本

# 通讯录（自动注入 access_token；0.1.2 起 Using() 兜底生效）
user = await wecom.Api.get_user_info("zhangsan")            # 成员详情（姓名/部门/职务/头像）
depts = await wecom.Api.get_department_list(0)              # 部门列表（0=根部门）
members = await wecom.Api.get_department_users(2)           # 部门成员列表
uid = await wecom.Api.get_user_by_mobile("13800000000")     # 手机号查 userid
openid = await wecom.Api.userid_to_openid("zhangsan")       # userid → openid（红包/对外支付）
userid = await wecom.Api.openid_to_userid("oXXXX")          # openid → userid

# 多账户：指定企业账户
result = await wecom.Api.Using("corp2").get_user_info("lisi")

# 任意企业微信 API 直调（endpoint 相对 cgi-bin，自动带 access_token）
result = await wecom.Api.call("message/send", touser="zhangsan", msgtype="text", agentid=1000002, text={"content": "hi"})
```

## 特有事件类型

需要 `platform == "wecom"` 检测再使用本平台特性。企业微信事件转换遵循 OneBot12 标准，同时通过 `wecom_` 前缀提供平台扩展。

### 消息事件 detail_type 映射

企业微信应用接收的消息统一映射为 `private`（私信）：

| 企业微信消息 | OneBot12 type / detail_type |
|---|---|
| `text` | `message` / `private` |
| `image` | `message` / `private` |
| `voice` | `message` / `private` |
| `video` / `shortvideo` | `message` / `private` |
| `location` | `message` / `private` |
| `link` | `message` / `private` |

### 特有事件类型（notice）

| detail_type | 说明 |
|---|---|
| `wecom_subscribe` | 用户关注 / 进入应用（subscribe / enter_agent） |
| `wecom_unsubscribe` | 用户取消关注 |
| `wecom_location_report` | 上报地理位置 |
| `wecom_menu_click` | 点击菜单跳转事件（click） |
| `wecom_menu_view` | 点击菜单链接跳转（view） |
| `wecom_scancode` | 扫码推事件 |
| `wecom_menu_photo` | 拍照/相册事件 |

> 上报事件（订阅/菜单点击等）转换为 `request` / `notice` 类事件。

### 标准消息段类型

转换后的消息段使用 OneBot12 标准格式：

| 消息段类型 | 说明 | data 字段 |
|---|---|---|
| `text` | 纯文本 | `text` |
| `image` | 图片 | `file`（PicUrl 或 MediaId），`url` |
| `audio` | 语音 | `file`（MediaId） |
| `video` | 视频 | `file`（MediaId），`thumbnail` |
| `location` | 位置 | `latitude`, `longitude`, `title` |
| `file` | 文件/链接 | `file`, `filename`, `url` |

### 平台扩展消息段

以 `wecom_` 前缀标识的扩展消息段（发送方向）：

| 消息段类型 | 说明 | data 字段 |
|---|---|---|
| `wecom_markdown` | Markdown 消息 | `content` |
| `wecom_news` | 图文消息 | `articles`（list） |
| `wecom_textcard` | 文本卡片 | `title`, `description`, `url`, `btntxt` |
| `wecom_miniprogram_notice` | 小程序通知 | 原生字段透传 |
| `wecom_template_card` | 模板卡片 | `card_type` + 原生字段 |

### 事件示例

#### 文本消息

```python
{
  "id": "1234567890123456",
  "time": 1348831860,
  "type": "message",
  "detail_type": "private",
  "platform": "wecom",
  "self": {"platform": "wecom", "user_id": "Corpid"},
  "message_id": "1234567890123456",
  "user_id": "UserID",
  "user_nickname": "UserID",
  "message": [{"type": "text", "data": {"text": "消息内容"}}],
  "alt_message": "消息内容",
  "wecom_raw": {"MsgType": "text", "Content": "消息内容", "...": "..."},
  "wecom_raw_type": "text",
  "wecom_agentid": "1000002",
  "wecom_corpid": "Corpid",
  "wecom_msg_id": "1234567890123456"
}
```

> **0.1.2 变化**：消息事件补齐顶层 `message_id`（取企业微信 MsgId，缺失时 uuid 兜底）。

#### 菜单点击事件

```python
{
  "type": "notice",
  "detail_type": "wecom_menu_click",
  "platform": "wecom",
  "user_id": "UserID",
  "wecom_event_key": "menu_key_1",
  "wecom_raw_type": "event"
}
```

## Event Mixin 扩展方法

适配器注册了以下平台专有方法，仅在 `platform == "wecom"` 时可用：

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_user_id()` | `str` | 获取发送者 UserID |
| `get_msg_type()` | `str` | 获取企业微信消息类型（text/image/...） |
| `get_content()` | `str` | 获取消息纯文本内容 |
| `get_agentid()` | `str` | 获取应用 AgentID |
| `get_corpid()` | `str` | 获取企业 Corpid |
| `get_msg_id()` | `str` | 获取消息 MsgId |
| `get_raw_xml()` | `str` | 获取解密后的原始 XML |
| `get_raw()` | `dict` | 获取解析后的原始数据字典 |
| `get_event_key()` | `str` | 获取菜单事件的 EventKey |
| `get_media_id()` | `str` | 获取媒体消息的 MediaId |

### 使用示例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "wecom":
        return

    msg_type = event.get_msg_type()
    user_id = event.get_user_id()
    content = event.get_content()

    if msg_type == "text":
        await event.reply(f"收到: {content}")

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "wecom":
        return

    if event.get("detail_type") == "wecom_menu_click":
        key = event.get_event_key()
        await event.reply(f"你点击了菜单: {key}")
```

## 扩展字段说明

- 所有特有字段均以 `wecom_` 前缀标识
- 保留原始数据在 `wecom_raw` 字段（解析后的字典）
- 保留解密后原始 XML 在 `wecom_raw_xml` 字段
- 保留原始事件类型在 `wecom_raw_type` 字段
- `wecom_corpid`：企业ID
- `wecom_agentid`：应用 AgentID
- `wecom_msg_id`：企业微信消息 ID

## 认证与加解密

### access_token 管理

- 每个账户独立缓存 access_token
- 有效期 7200 秒，提前 5 分钟自动刷新
- token 失效（errcode 40014/42001）时自动清除缓存并重试

### 消息加解密

- 算法：AES-256-CBC（PKCS7 填充）
- 密钥：`base64decode(EncodingAESKey + "=")`（32字节）
- IV：密钥前 16 字节
- 签名：`sha1("".join(sorted([token, timestamp, nonce, encrypt])))`
- 依赖库：`cryptography`

## 注意事项

1. **回调 URL 必须公网可达**：本地开发可用内网穿透；生产建议 Nginx 反代到 ErisPulse router 端口
2. **主动发送频率**：受企业微信应用消息接口限制（每应用每日量与企业规模相关），群发场景请用 `TaskCard`/`TemplateCard` 结合标签
3. **access_token 有效性**：适配器自动刷新；多实例部署同一 corpid+secret 时注意官方 token 互踢限制（建议由一个实例收发为宜）
4. **媒体文件**：Voice 需 AMR 格式（企业微信限制）；大文件走临时素材接口（适配器自动处理）
