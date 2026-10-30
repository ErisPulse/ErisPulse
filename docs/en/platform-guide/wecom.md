# WeCom Platform Features Documentation

WeComAdapter is an adapter built based on the Enterprise WeChat self-built application API, which receives messages through callbacks, actively sends messages via the application message interface, and provides contact list and message card capabilities.

---

## Documentation Information

- Corresponding Module Version: 0.1.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: WeCom self-built application bot, suitable for internal enterprise notifications, intelligent Q&A, office automation, and other scenarios.
- Adapter Name: WeComAdapter
- Multi-account Support: Supports configuring multiple enterprises simultaneously (each account corresponds to a corpid + application).
- Connection Method: HTTP callback reception (configure the message receiving URL in the WeCom backend) + active API sending.
- Authentication Method: Exchange corpid + secret for access_token (automatically refreshed).
- Callback Encryption/Decryption: Token + EncodingAESKey (WeCom official encryption/decryption protocol).
- Chained Modifier Support: Supports chained modifier methods such as `.Reply()`.
- OneBot12 Compatibility: Supports sending OneBot12 standard message segments.

## Configuration

```toml
# config.toml
[WeComAdapter.accounts.default]
corpid = "YOUR_CORP_ID"        # Enterprise ID (required, found in Enterprise WeChat backend - My Enterprise)
secret = "YOUR_APP_SECRET"     # Application Secret (required, found in self-built application details page)
agentid = 1000002              # Application AgentId (required, found in self-built application details page)
callback_enabled = true        # Enable callback reception (default true; if disabled, only active sending is possible)
token = "YOUR_CALLBACK_TOKEN"  # Callback verification Token (configured in Enterprise WeChat backend for receiving messages)
encoding_aes_key = "YOUR_AES_KEY_43CHARS"  # Callback encryption/decryption key (43 characters)
callback_path = "/wecom/{account}"         # Callback path, supports {account} placeholder
enabled = true
```

**Configuration Item Descriptions (per account):**

- `corpid` / `secret` / `agentid`: Obtain from the self-built application page in [Enterprise WeChat Management Backend](https://work.weixin.qq.com) (first two are required)
- `callback_enabled`: Callback reception switch (default enabled). **If disabled, the adapter skips callback route registration, retaining only active sending capability**; related callback fields in the panel are hidden accordingly
- `token` / `encoding_aes_key`: Used for callback message verification and encryption/decryption, must match the configuration in Enterprise WeChat backend under "Receive Messages"
- `callback_path`: Callback reception path (default `/wecom/{account name}`); Enterprise WeChat backend must configure the full URL: `http(s)://your address:port/wecom/<account name>`

**Prerequisites for Receiving Messages**: In the Enterprise WeChat backend → Self-built application → "Receive Messages" settings, enable API message reception, fill in the above complete callback URL, and ensure Token and EncodingAESKey match the configuration. **Note**: Enterprise WeChat requires the callback URL to be publicly accessible (recommended to use reverse proxy).

**API Environment**:
- API base URL: `https://qyapi.weixin.qq.com/cgi-bin`
- `access_token` is automatically obtained and cached with refresh, no manual management required

## Message Sending

```python
from ErisPulse import sdk
wecom = sdk.adapter.get("wecom")

# Basic message (target_type: "user"=user "group"=application group chat)
await wecom.Send.To("user", "zhangsan").Text("Hello")
await wecom.Send.To("group", "group_chat_id").Markdown("**Bold** notification")

# Media (local path / bytes / URL; automatically uploads temporary material before sending)
await wecom.Send.To("user", "zhangsan").Image("banner.png")
await wecom.Send.To("user", "zhangsan").Voice("voice.amr")
await wecom.Send.To("user", "zhangsan").Video("demo.mp4")
await wecom.Send.To("user", "zhangsan").File("report.pdf")

# News and cards
await wecom.Send.To("user", "zhangsan").News([
    {"title": "Title", "description": "Summary", "url": "https://...", "picurl": "https://.../img.png"},
])  # Maximum of 8 items

await wecom.Send.To("user", "zhangsan").TextCard(
    title="Approval Reminder",
    description="You have a pending approval document",
    url="https://oa.example.com/approval/1",
    btntxt="Go Process",
)

await wecom.Send.To("user", "zhangsan").TemplateCard(
    card_type="text_notice",  # WeCom card type; other parameters are passed through as per official card JSON
    source={"icon_url": "...", "desc": "OA"},
    main_title={"title": "Meeting Reminder"},
)

# Passive reply: reply directly to the source user using event.reply() after receiving a message
```

## Standard API Actions

```python
info = await wecom.Api.get_self_info()          # Application information (corpid/agentid)
status = await wecom.Api.get_status()           # Running status
ver = await wecom.Api.get_version()             # Adapter version

# Address Book (Added in 2.1.0, access_token injected automatically)
user = await wecom.Api.get_user_info("zhangsan")            # Member details (name/department/position/avatar)
depts = await wecom.Api.get_department_list(0)              # Department list (0=root department)
members = await wecom.Api.get_department_users(2)           # Department member list
uid = await wecom.Api.get_user_by_mobile("13800000000")     # Lookup userid by mobile phone number
openid = await wecom.Api.userid_to_openid("zhangsan")       # userid → openid (red packet/external payment)
userid = await wecom.Api.openid_to_userid("oXXXX")          # openid → userid

# Multi-account
result = await wecom.Api.Using("corp2").get_user_info("lisi")

# Direct call to any Enterprise WeChat API (endpoint relative to cgi-bin, access_token automatically included)
result = await wecom.Api.call("message/send", touser="zhangsan", msgtype="text", agentid=1000002, text={"content": "hi"})
```

## Event Description

- Message Event: `detail_type` is `private` (member sends message) / `group` (application group chat message); `user_id` is the member's userid
- The event object provides extended reading methods such as `get_raw_xml()` (original callback XML)
- Reported events (subscription/menu click, etc.) are converted into `request` / `notice` type events

## Notes

1. **Callback URL must be publicly accessible**: Use an internal network penetration tool for local development; for production, it is recommended to use Nginx reverse proxy to the ErisPulse router port.
2. **Outbound message frequency**: Limited by the enterprise WeChat application message interface (daily quota per application is related to the size of the enterprise). For mass messaging scenarios, use `TaskCard`/`TemplateCard` combined with tags.
3. **access_token validity**: The adapter automatically refreshes the token; when deploying multiple instances with the same corpid+secret, be aware of the official token mutual kick-off restriction (it is advisable to centrally manage sending and receiving via a single instance).
4. **Media files**: Voice files must be in AMR format (enterprise WeChat restriction); for large files, use the temporary material interface (handled automatically by the adapter).