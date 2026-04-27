# 云湖用户平台特性文档

YunhuUserAdapter 是基于云湖用户账户协议构建的适配器，通过用户邮箱账户登录，使用 WebSocket 接收事件，提供统一的事件处理和消息操作接口。

---

## 文档信息

- 对应模块版本: 1.4.0
- 维护者: wsu2059

## 基本信息

- 平台简介：云湖（Yunhu）是一个企业级即时通讯平台，本适配器通过**用户账户**（而非机器人账户）与之交互
- 适配器名称：YunhuUserAdapter
- 多账户支持：支持通过账户名识别并配置多个用户账户
- 链式修饰支持：支持 `.Reply()` 等链式修饰方法
- OneBot12兼容：支持发送 OneBot12 格式消息
- 通信方式：通过邮箱登录获取 token，使用 WebSocket 接收事件，HTTP + Protobuf 协议发送消息
- 会话类型：支持私聊（user）、群聊（group）、机器人会话（bot）

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str, buttons: Optional[List] = None)`：发送纯文本消息。
- `.Html(html: str, buttons: Optional[List] = None)`：发送HTML格式消息。
- `.Markdown(markdown: str, buttons: Optional[List] = None)`：发送Markdown格式消息。
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`：发送图片消息，支持URL、本地路径或二进制数据。
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`：发送视频消息，支持URL、本地路径或二进制数据。
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`：发送语音消息，支持URL、本地路径或二进制数据，自动检测音频时长。
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`：`.Audio()` 的别名。
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`：发送文件消息，支持URL、本地路径或二进制数据。
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`：发送表情/贴纸消息，支持贴纸ID、贴纸URL或二进制图片数据。
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`：发送A2UI消息（消息类型14），A2UI JSON 数据会填入 text 字段发送。
- `.Edit(msg_id: str, text: str, content_type: str = "text")`：编辑已有消息。
- `.Recall(msg_id: str)`：撤回消息。
- `.Raw_ob12(message: Union[List, Dict])`：发送 OneBot12 格式消息。

### 媒体文件处理

所有媒体类型（图片、视频、音频、文件）支持以下输入方式：
- **URL**：`"https://example.com/image.jpg"` — 自动下载后上传
- **本地路径**：`"/path/to/file.jpg"` — 自动读取后上传
- **二进制数据**：`open("file.jpg", "rb").read()` — 直接上传

媒体文件会自动上传到七牛云存储，支持以下特性：
- 自动通过 `filetype` 库检测文件类型和 MIME
- 自动计算文件大小
- 音频文件自动检测时长（支持 MP3、MP4/M4A 格式）

### 按钮参数说明

`buttons` 参数是一个嵌套列表，表示按钮的布局和功能。每个按钮对象包含以下字段：

| 字段         | 类型   | 是否必填 | 说明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | 按钮上的文字                                                         |
| `actionType` | int    | 是       | 动作类型：<br>`1`: 跳转 URL<br>`2`: 复制<br>`3`: 点击汇报            |
| `url`        | string | 否       | 当 `actionType=1` 时使用，表示跳转的目标 URL                         |
| `value`      | string | 否       | 当 `actionType=2` 时，该值会复制到剪贴板<br>当 `actionType=3` 时，该值会发送给订阅端 |

示例：
```python
buttons = [
    [
        {"text": "复制", "actionType": 2, "value": "xxxx"},
        {"text": "点击跳转", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "汇报事件", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("带按钮的消息")
```

### 链式修饰方法（可组合使用）

链式修饰方法返回 `self`，支持链式调用，必须在最终发送方法前调用：

- `.Reply(message_id: str)`：回复指定消息。
- `.At(user_id: str)`：@指定用户（文本形式 @user_id）。
- `.AtAll()`：@所有人（伪@全体，发送 @all 文本）。
- `.Buttons(buttons: List)`：添加按钮。

> **注意：** 因为用户账户较为特殊，即便不是管理员也可以 @全体，但这里的 `AtAll()` 只会发送一个艾特全体的文本，是一个伪@全体。

### 链式调用示例

```python
# 基础发送
await yunhu_user.Send.To("user", user_id).Text("Hello")

# 回复消息
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("回复消息")

# 回复 + 按钮
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("带回复和按钮的消息")

# 指定账户 + 回复 + 按钮
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("完整链式调用")
```

### OneBot12消息支持

适配器支持发送 OneBot12 格式的消息，便于跨平台消息兼容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：发送 OneBot12 格式消息。

```python
# 发送 OneBot12 格式消息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合链式修饰
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 支持自动将混合消息段分组处理：
- `text`、`mention` 类型可合并为一组发送
- `image`、`video`、`audio`、`file`、`face`、`markdown`、`html`、`a2ui` 等类型各自独立成组
- `reply` 类型可附加到任何组

## 发送方法返回值

所有发送方法均返回一个 Task 对象，可以直接 await 获取发送结果。返回结果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 执行状态
    "retcode": 0,             // 返回码
    "data": {...},            // 响应数据
    "message_id": "123456",   // 消息ID
    "message": "",            // 错误信息
    "yunhu_user_raw": {...}   // 原始响应数据
}
```

## 特有事件类型

需要 `platform == "yunhu_user"` 检测再使用本平台特性

### 核心差异点

1. 特有事件类型：
    - 超级文件分享：`yunhu_user_file_send`
    - 机器人公告看板：`yunhu_user_bot_board`
    - 消息编辑通知：`message_edit`
    - 消息删除通知：`message_delete`（撤回）
2. 特有消息段类型：
    - 表单消息段：`yunhu_user_form`
    - 文章消息段：`yunhu_user_post`
    - 贴纸消息段：`yunhu_user_sticker`
    - 按钮消息段：`yunhu_user_button`
    - A2UI 消息段：`a2ui`
3. 扩展字段：
    - 所有特有字段均以 `yunhu_user_` 前缀标识
    - 保留原始数据在 `yunhu_user_raw` 字段
    - 原始事件类型记录在 `yunhu_user_raw_type` 字段
    - 私聊中 `self.user_id` 表示当前登录用户ID

### 支持的原始事件类型

| 原始事件类型 | OneBot12 类型 | 说明 |
|-------------|--------------|------|
| `push_message` | `message` | 推送消息（私聊、群聊、Bot 会话） |
| `edit_message` | `notice` (`message_edit`) | 消息编辑事件 |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | 超级文件分享事件 |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | 机器人公告看板事件 |

> 其他事件类型（如 `heartbeat_ack`、`draft_input`、`stream_message` 等）会被忽略。

### OneBot12 支持的 detail_type

| OneBot12 detail_type | 云湖 chat_type | 说明 |
|---------------------|---------------|------|
| `private` | 1 | 私聊消息 |
| `group` | 2 | 群聊消息 |
| `bot` | 3 | 机器人会话 |

### 消息事件示例

```python
{
    "id": "event_id",
    "time": 1234567890,
    "type": "message",
    "detail_type": "group",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message": [
        {"type": "text", "data": {"text": "消息内容"}}
    ],
    "alt_message": "消息内容",
    "user_id": "sender_user_id",
    "user_nickname": "发送者昵称",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### 消息编辑通知示例

```python
{
    "type": "notice",
    "detail_type": "message_edit",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message_id": "msg_id",
    "user_id": "sender_user_id",
    "user_nickname": "发送者昵称",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### 超级文件分享事件示例

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_file_send",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "user_id": "send_user_id",
    "user_nickname": "",
    "yunhu_user_file_send": {
        "send_user_id": "发送者ID",
        "user_id": "接收用户ID",
        "send_type": "发送类型",
        "data": "文件数据"
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "file_send_message"
}
```

### 机器人公告看板事件示例

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_bot_board",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "bot_id": "bot_id",
    "bot_name": "机器人名称",
    "yunhu_user_bot_board": {
        "bot_id": "bot_id",
        "chat_id": "chat_id",
        "chat_type": 1,
        "content": "公告内容",
        "content_type": 1,
        "last_update_time": 1234567890
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "bot_board_message"
}
```

### 事件处理示例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_yunhu_user_message(event):
    """处理云湖用户消息"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"用户 {user_nickname}({user_id}): {alt_message}")
    
    # 检查消息段中的特有类型
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"收到表单消息: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"收到文章消息: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"收到贴纸消息: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"消息包含按钮: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"收到A2UI消息: {a2ui_data}")
    
    # 使用 event.reply() 自动回复
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """处理云湖用户通知事件"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"用户 {user_nickname} 编辑了消息 {message_id}")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"收到超级文件分享: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"机器人 {bot_name} 发布了公告: {board_data.get('content', '')}")
```

## 扩展字段说明

- 所有特有字段均以 `yunhu_user_` 前缀标识，避免与标准字段冲突
- 保留原始数据在 `yunhu_user_raw` 字段，便于访问云湖平台的完整原始数据
- 原始事件类型记录在 `yunhu_user_raw_type` 字段（如 `push_message`、`edit_message` 等）
- `self.user_id` 表示当前登录用户ID（从登录响应中获取）
- 超级文件分享通过 `yunhu_user_file_send` 字段提供文件分享数据
- 机器人公告看板通过 `yunhu_user_bot_board` 字段提供公告数据

### 特有消息段类型

#### 表单消息段 (yunhu_user_form)

当 content_type 为 5 时，消息段类型为 `yunhu_user_form`：

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "表单数据"
    }
}
```

#### 文章消息段 (yunhu_user_post)

当 content_type 为 6 时，消息段类型为 `yunhu_user_post`：

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "文章ID",
        "post_title": "文章标题",
        "post_content": "文章内容"
    }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `post_id` | string | 文章唯一标识 |
| `post_title` | string | 文章标题 |
| `post_content` | string | 文章内容 |

#### 贴纸消息段 (yunhu_user_sticker)

当 content_type 为 7 时，消息段类型为 `yunhu_user_sticker`：

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "贴纸图片URL"
    }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_id` | string | 贴纸图片URL |

#### 按钮消息段 (yunhu_user_button)

消息中包含按钮时，会附加 `yunhu_user_button` 消息段：

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "按钮文字", "actionType": 3, "value": "值"}]]
    }
}
```

#### A2UI 消息段 (a2ui)

当 content_type 为 14 时，消息段类型为 `a2ui`：

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSON数据"
    }
}
```

---

## 多账户配置

### 配置说明

YunhuUserAdapter 支持同时配置和运行多个用户账户。

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket重连间隔（秒）
ws_timeout = 70             # WebSocket超时时间（秒）

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # 用户邮箱（必填）
password = "password1"       # 用户密码（必填）
platform = "windows"         # 登录平台（可选，默认windows）
device_id = ""               # 设备ID（可选，不填自动生成）
enabled = true               # 是否启用（可选，默认为true）

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**配置项说明：**
- `email`：用户邮箱（必填），用于登录云湖平台
- `password`：用户密码（必填）
- `platform`：登录平台标识（可选，默认为 `windows`），可选值：`windows`、`macos`、`linux`、`ios`、`android`
- `device_id`：设备ID（可选，不填自动生成），建议填写固定值以保持会话一致性
- `enabled`：是否启用该账户（可选，默认为 `true`）

**适配器级别配置：**
- `ws_reconnect_interval`：WebSocket 重连间隔（秒，默认 30）
- `ws_timeout`：WebSocket 超时时间（秒，默认 70）

**重要提示：**
1. 适配器使用邮箱登录方式获取 token，登录后通过 WebSocket 接收事件
2. WebSocket 连接断开后会自动重连，最多重试 3 次
3. 建议为每个账户设置固定的 `device_id`，以保持会话一致性
4. 未修改的模板账户（默认邮箱和密码）会被自动跳过

### 使用Send DSL指定账户

可以通过 `Using()` 方法指定使用哪个账户发送消息。该方法支持两种参数：
- **账户名**：配置中的账户名称（如 `default`、`account2`）
- **user_id**：登录后获取的用户 ID

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# 使用账户名发送消息
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# 使用 user_id 发送消息（自动匹配对应账户）
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# 不指定时使用第一个启用的账户
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **提示：** 使用 `user_id` 时，系统会自动查找配置中匹配的账户。这在处理事件回复时特别有用，可以直接使用 `event["self"]["user_id"]` 来回复同一账户。

### 事件中的账户标识

接收到的事件会自动包含对应的用户ID信息：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # 获取当前登录用户ID
        my_user_id = event["self"]["user_id"]
        print(f"消息来自账户: {my_user_id}")
        
        # 使用相同账户回复消息
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("回复消息")
```

### 日志信息

适配器会在日志中自动包含账户信息，便于调试和追踪：

```
[INFO] 账户 default (user1@example.com) 登录成功，用户ID: 12345678
[INFO] 账户 default WebSocket 监听任务已启动
[INFO] 账户 account2 (user2@example.com) 登录成功，用户ID: 87654321
```

### 管理接口

```python
# 获取所有账户信息
accounts = yunhu_user.accounts
# 返回格式: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# 检查账户是否启用
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# 通过账户名获取 HTTP 客户端
http_client = yunhu_user._get_http_client("default")

# 通过 user_id 查找账户
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API 调用

适配器提供 `call_api` 方法，支持直接调用平台 API：

```python
# 发送消息
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# 编辑消息
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="新内容",
    content_type="text"
)

# 撤回消息
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# 批量撤回消息
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# 获取消息列表
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# 获取消息编辑记录
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# 按钮事件报告
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**支持的 API 端点：**

| 端点 | 说明 |
|------|------|
| `/send` | 发送消息 |
| `/edit` | 编辑消息 |
| `/recall` | 撤回消息 |
| `/recall_batch` | 批量撤回消息 |
| `/list` | 获取消息列表 |
| `/list_by_seq` | 通过序列获取消息 |
| `/list_by_mid_seq` | 通过消息ID和序列获取消息 |
| `/list_edit_record` | 获取消息编辑记录 |
| `/button_report` | 按钮事件报告 |
