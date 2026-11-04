# 企业微信（WeCom）平台特性文档

WeComAdapter 是基于企业微信自建应用 API 构建的适配器，通过回调接收消息、应用消息接口主动发送，并提供通讯录与消息卡片能力。

---

## 文档信息

- 对应模块版本: 0.1.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：企业微信自建应用机器人，适用于企业内部通知、智能问答、办公自动化等场景
- 适配器名称：WeComAdapter
- 多账户支持：支持同时配置多个企业（每个账户对应一个 corpid + 应用）
- 连接方式：HTTP 回调接收（企业微信后台配置接收消息 URL）+ 主动 API 发送
- 认证方式：corpid + secret 换取 access_token（自动刷新）
- 回调加解密：Token + EncodingAESKey（企业微信官方加解密协议）
- 链式修饰支持：支持 `.Reply()` 等链式修饰方法
- OneBot12 兼容：发送支持 OneBot12 标准消息段

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

- `corpid` / `secret` / `agentid`：从[企业微信管理后台](https://work.weixin.qq.com)的自建应用页获取（前两项必填）
- `callback_enabled`：回调接收开关（默认开启）。**关闭后适配器跳过回调路由注册，仅保留主动发送能力**；面板中回调相关字段随之隐藏
- `token` / `encoding_aes_key`：回调消息验证与加解密，与企业微信后台「接收消息」配置一致
- `callback_path`：回调接收路径（默认 `/wecom/{账户名}`），企业微信后台需配置完整 URL：`http(s)://你的地址:端口/wecom/<账户名>`

**接收消息前置条件**：企业微信后台 → 自建应用 → 「接收消息」设置 API 接收，URL 填上述完整回调地址，Token 与 EncodingAESKey 与配置一致。**注意**：企业微信要求回调 URL 可公网访问（建议搭配反向代理）。

**API 环境**：
- API 基础地址：`https://qyapi.weixin.qq.com/cgi-bin`
- access_token 自动获取与缓存刷新，无需手动管理

## 消息发送

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
```

## 标准 API 动作

```python
info = await wecom.Api.get_self_info()          # 应用信息（corpid/agentid）
status = await wecom.Api.get_status()           # 运行状态
ver = await wecom.Api.get_version()             # 适配器版本

# 通讯录（2.1.0 新增，自动注入 access_token）
user = await wecom.Api.get_user_info("zhangsan")            # 成员详情（姓名/部门/职务/头像）
depts = await wecom.Api.get_department_list(0)              # 部门列表（0=根部门）
members = await wecom.Api.get_department_users(2)           # 部门成员列表
uid = await wecom.Api.get_user_by_mobile("13800000000")     # 手机号查 userid
openid = await wecom.Api.userid_to_openid("zhangsan")       # userid → openid（红包/对外支付）
userid = await wecom.Api.openid_to_userid("oXXXX")          # openid → userid

# 多账户
result = await wecom.Api.Using("corp2").get_user_info("lisi")

# 任意企业微信 API 直调（endpoint 相对 cgi-bin，自动带 access_token）
result = await wecom.Api.call("message/send", touser="zhangsan", msgtype="text", agentid=1000002, text={"content": "hi"})
```

## 事件说明

- 消息事件：`detail_type` 为 `private`（成员发消息）/ `group`（应用群聊消息）；`user_id` 为成员 userid
- 事件对象提供 `get_raw_xml()`（原始回调 XML）等扩展读取方法
- 上报事件（订阅/菜单点击等）转换为 `request` / `notice` 类事件

## 注意事项

1. **回调 URL 必须公网可达**：本地开发可用内网穿透；生产建议 Nginx 反代到 ErisPulse router 端口
2. **主动发送频率**：受企业微信应用消息接口限制（每应用每日量与企业规模相关），群发场景请用 `TaskCard`/`TemplateCard` 结合标签
3. **access_token 有效性**：适配器自动刷新；多实例部署同一 corpid+secret 时注意官方 token 互踢限制（ centrally 由一个实例收发为宜）
4. **媒体文件**：Voice 需 AMR 格式（企业微信限制）；大文件走临时素材接口（适配器自动处理）
