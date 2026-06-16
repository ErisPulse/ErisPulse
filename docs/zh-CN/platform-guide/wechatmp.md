# 微信公众号（WechatMp）适配器 - 平台特性文档

## 基本信息
- 模块名称: `ErisPulse-WechatMpAdapter`
- 平台标识: `mp`（别名: `wechat_mp`）
- 模块版本: 4.0.0
- 维护者: ErisPulse
- 依赖: `cryptography`

## 支持的消息发送类型

| 方法 | 说明 | 微信 API |
|------|------|---------|
| `Text(text)` | 发送文本 | 客服消息 `message/custom/send` |
| `Image(file)` | 发送图片（自动上传获取 media_id） | 客服消息 + `media/upload` |
| `Voice(file)` | 发送语音（自动上传获取 media_id） | 客服消息 + `media/upload` |
| `Video(file, title, description)` | 发送视频（自动上传获取 media_id） | 客服消息 + `media/upload` |
| `Music(url, title, description, ...)` | 发送音乐 | 客服消息 |
| `News(articles)` | 发送图文消息 | 客服消息 |
| `Template(template_id, data, url)` | 发送模板消息 | `message/template/send` |
| `Menu(head_content, list, tail_content)` | 发送菜单消息 | 客服消息 `msgmenu` |
| `Raw_ob12(message)` | 发送 OneBot12 标准消息段 | - |

### 媒体文件说明
- 支持三种参数类型：
  - `str` URL（`http://` / `https://` 开头）：自动下载后上传
  - `str` 本地文件路径：自动读取后上传
  - `bytes` 二进制数据：直接上传
  - `str` media_id：以 `media:` 前缀可直接复用已上传的 media_id
- 上传后获得临时素材 `media_id`，有效期 3 天

### 重要限制
- 客服消息只能在用户与公众号交互后 **48 小时内** 主动发送
- 超过 48 小时需使用模板消息（需用户授权场景）

## 事件类型

### 消息事件 (message)
所有用户消息均为 `detail_type: private`（公众号 1v1 场景）。

| 微信 MsgType | 消息段类型 | 说明 |
|-------------|-----------|------|
| `text` | `text` | 文本消息 |
| `image` | `image` | 图片消息 |
| `voice` | `voice` | 语音消息（含语音识别结果） |
| `video` | `video` | 视频消息 |
| `shortvideo` | `video` | 小视频（标记 `mp_shortvideo`） |
| `location` | `location` | 地理位置消息 |
| `link` | `text` | 链接消息（转为文本） |

### 通知事件 (notice)
事件通过 `mp_event` 字段区分具体类型。

| 微信 Event | `mp_event` | 说明 |
|-----------|-----------|------|
| `subscribe` | `subscribe` | 关注公众号 |
| `unsubscribe` | `unsubscribe` | 取消关注 |
| `SCAN` | `scan` | 扫描带参数二维码 |
| `LOCATION` | `location_report` | 上报地理位置 |
| `CLICK` | `menu_click` | 自定义菜单点击 |
| `VIEW` | `menu_view` | 菜单跳转链接 |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | 模板消息发送结果 |
| `MASSSENDJOBFINISH` | `mass_send_finish` | 群发消息发送结果 |

## 平台扩展字段

事件对象中的微信特有字段（`mp_` 前缀）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `mp_raw` | str | 原始 XML 数据 |
| `mp_raw_type` | str | 原始消息/事件类型 |
| `mp_msg_id` | str | 微信消息 ID |
| `mp_event` | str | 事件类型（仅事件通知） |
| `mp_event_key` | str | 事件 Key（菜单点击/扫码等） |
| `mp_to_user` | str | 接收方微信号（公众号原始ID） |
| `mp_from_user` | str | 发送方 OpenID |
| `mp_data` | dict | 解析后的 XML 字典数据 |

## 事件扩展方法

通过 `register_event_mixin("mp", ...)` 注册，在事件对象上可直接调用：

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `get_openid()` | str | 发送者 OpenID |
| `get_msg_type()` | str | 微信原始消息类型 |
| `get_event()` | str | 事件类型（仅事件通知） |
| `get_content()` | str | 消息纯文本内容 |
| `get_raw_xml()` | str | 原始 XML 数据 |

## 配置选项

### 多账户配置

每个账户对应一个公众号：

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # 安全模式/兼容模式才需要（43位）
callback_path = "/mp/main"               # 回调路径
enable = true

[WechatMpAdapter.accounts.secondary]
appid = "wx0987654321fedcba"
appsecret = "another_app_secret"
token = "another_callback_token"
callback_path = "/mp/secondary"
enable = true
```

### 配置字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `appid` | 是 | 公众号 AppID |
| `appsecret` | 是 | 公众号 AppSecret（secret） |
| `token` | 否 | 回调验证 Token（建议填写以启用签名验证） |
| `encoding_aes_key` | 否 | 消息加解密密钥（43位，安全模式必需） |
| `callback_path` | 否 | 回调路径模板，默认 `/mp/{account}`，`{account}` 会被账户名替换 |
| `enable` | 否 | 是否启用，默认 true |

## 加密模式说明

微信公众号提供三种消息加解密模式：

| 模式 | 说明 | encoding_aes_key | 验证字段 |
|------|------|-----------------|---------|
| 明文模式 | XML 明文传输 | 不需要 | `signature` |
| 兼容模式 | 明文+密文同时存在 | 可选 | `signature` / `msg_signature` |
| 安全模式 | 全部加密 | 必需 | `msg_signature` |

本适配器自动处理：
- 明文模式：验证 `signature`，直接解析 XML
- 安全/兼容模式：检测 `Encrypt` 字段，验证 `msg_signature`，使用 AES-256-CBC 解密
- 解密依赖 `cryptography` 库（已声明在 dependencies 中）

## 回调路由

适配器为每个已启用账户注册两个路由（GET + POST）：

- **GET**：微信服务器接入验证，验证签名后返回 `echostr`
- **POST**：接收用户消息和事件，验证签名→解密（如需）→转换→emit

实际访问路径会自动添加模块前缀，例如注册路径 `/mp/main`，
实际访问路径为 `/mp_{account}_verify/mp/main` 和 `/mp_{account}_message/mp/main`。

## API 响应

所有 `call_api` 调用返回标准化响应：

- 成功：`status: "ok"`, `retcode: 0`
- 失败：`status: "failed"`, `retcode: 34000+errcode`
- 始终包含 `mp_raw`（原始响应）、`message_id`
