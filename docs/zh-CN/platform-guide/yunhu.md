# 云湖平台特性文档

YunhuAdapter 是基于云湖协议构建的适配器，整合了所有云湖功能模块，提供统一的事件处理和消息操作接口。

---

## 文档信息

- 对应模块版本: 4.3.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：云湖（Yunhu）是一个企业级即时通讯平台
- 适配器名称：YunhuAdapter
- 多账户支持：支持通过 bot_id 识别并配置多个云湖机器人账户
- 链式修饰支持：支持 `.Reply()` 等链式修饰方法
- OneBot12兼容：支持发送 OneBot12 格式消息

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Html(html: str)`：发送HTML格式消息。
- `.Markdown(markdown: str)`：发送Markdown格式消息。
- `.A2UI(text: str)`：发送A2UI格式消息。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`：发送图片消息，支持流式上传和自定义文件名。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`：发送视频消息，支持流式上传和自定义文件名。
- `.File(file: bytes, stream: bool = False, filename: str = None)`：发送文件消息，支持流式上传和自定义文件名。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：批量发送消息。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：编辑已有消息。
- `.Recall(msg_id: str)`：撤回消息。
- `.Board(content: str, content_type: str = "text")`：发布公告看板。作用域由 `To()` 推断（指定目标=本地看板，未指定=全局看板）。链式修饰：`.Expire(duration)` 相对过期（秒）、`.ExpireAt(timestamp)` 绝对过期（秒级时间戳）、`.ForMember(member_id)` 群成员看板；**内容为空时自动转为撤销看板**。仍兼容旧式 `Board("local", "公告")` 显式 scope 写法。
- `.DismissBoard()`：撤销公告看板。作用域同样由 `To()` 推断，支持 `.ForMember(member_id)`；仍兼容旧式 `DismissBoard("local")` 写法。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：发送流式消息。

### 群组管理方法

所有群组管理方法需要通过链式语法指定群组，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`：移除群成员。机器人需要`允许移除群成员`权限。
- `.Ban(user_id: str, duration: int = 600)`：用户禁言。`duration`为禁言时长（秒），0为解禁，-1为永久禁言。机器人需要`允许禁言用户`权限。
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`：创建群标签。`color`格式为#RRGGBB，`sort`越小越靠前。机器人需要`允许控制标签组`权限。
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`：修改群标签。各参数可选，不传则不修改。机器人需要`允许控制标签组`权限。
- `.DeleteTag(tag: str)`：删除群标签。机器人需要`允许控制标签组`权限。
- `.GetTagList()`：获取群标签列表。返回包含`list`数组的响应数据。
- `.AddUserTag(user_id: str, tag: str)`：给用户添加标签。机器人需要`允许控制标签组`权限。
- `.RemoveUserTag(user_id: str, tag: str)`：给用户移除标签。机器人需要`允许控制标签组`权限。
- `.SetMsgTypeLimit(types: str)`：控制群内消息类型。`types`为消息类型名称，多个用逗号分隔（如`"text,image,video"`），空字符串表示不限制。机器人需要`允许修改群信息`权限。

### 消息查询方法

获取指定会话（用户/群）的历史消息列表，需要通过链式语法指定目标，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`：获取会话历史消息。返回包含`list`数组和`total`总数的响应数据。
  - `message_id`：消息ID（可选）。不填时配合`before`返回最近的N条消息。
  - `before`：返回指定消息ID前N条。
  - `after`：返回指定消息ID后N条。
  - > **注意：** `before` 和 `after` 至少需指定一个且大于0，否则服务器不会返回任何消息。

Board 作用域由 `To()` 自动推断：
- 指定 `To(target_type, target_id)` → 本地看板（指定用户/群组）
- 未指定 `To()` → 全局看板

```python
# 本地看板（60 秒后相对过期）
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# 群成员看板（仅指定成员可见）
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("仅你可见")

# 绝对时间戳过期
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("指定时间过期")

# 全局看板
await yunhu.Send.Board("全局公告")

# 清空本地看板（内容为空 → 自动撤销）
await yunhu.Send.To("group", group_id).Board("")
```

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
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("带按钮的消息")
```
> **注意：**
> - 只有用户点击了**按钮汇报事件**的按钮才会收到推送，**复制**和**跳转URL**均无法收到推送。

### 链式修饰方法（可组合使用）

链式修饰方法返回 `self`，支持链式调用，必须在最终发送方法前调用：

- `.Reply(message_id: str)`：回复指定消息。
- `.At(user_id: str)`：@指定用户。
- `.AtAll()`：@所有人。
- `.Buttons(buttons: List)`：添加按钮。

### 链式调用示例

```python
# 基础发送
await yunhu.Send.To("user", user_id).Text("Hello")

# 回复消息
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("回复消息")

# 回复 + 按钮
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("带回复和按钮的消息")
```

### 群组管理示例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 移除群成员
await yunhu.Send.To("group", group_id).Kick(user_id)

# 用户禁言（10分钟）
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# 解除禁言
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# 永久禁言
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# 创建群标签
await yunhu.Send.To("group", group_id).CreateTag("VIP用户", color="#FF5733", desc="VIP会员")

# 修改群标签
await yunhu.Send.To("group", group_id).EditTag("VIP用户", new_tag="SVIP用户", color="#33C4FF")

# 删除群标签
await yunhu.Send.To("group", group_id).DeleteTag("VIP用户")

# 获取群标签列表
result = await yunhu.Send.To("group", group_id).GetTagList()

# 给用户添加标签
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP用户")

# 移除用户标签
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP用户")

# 设置消息类型限制
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# 取消消息类型限制
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### 消息查询示例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 获取群最近10条消息（共返回10条）
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# 获取群中指定消息ID前10条（共返回11条）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# 获取群中指定消息ID前后各10条（共返回21条）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# 获取用户会话历史消息
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12消息支持

适配器支持发送 OneBot12 格式的消息，便于跨平台消息兼容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：发送 OneBot12 格式消息。

```python
# 发送 OneBot12 格式消息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合链式修饰
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 标准 API 动作（ApiDSL）

> [!NOTE]
> 本特性需要 ErisPulse **2.7.0+** 且 YunhuAdapter **4.3.0+**。

除了 `Send` 链式发送，适配器还提供 `Api` 内部类，暴露 OneBot12 标准 API 动作与云湖平台扩展动作。所有方法返回标准响应格式。

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 信息查询（通过公开 Web API，无需鉴权）
result = await yunhu.Api.get_self_info()              # 机器人自身信息
result = await yunhu.Api.get_user_info("7058262")     # 任意用户信息
result = await yunhu.Api.get_group_info("635409929")  # 群信息

# 文件操作
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# 撤回消息（需额外提供 chat_id + chat_type）
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# 多账户：指定 Bot 账号
info = await yunhu.Api.Using("bot1").get_self_info()
```

### 支持的标准动作

| 方法 | 说明 | 数据来源 |
|------|------|---------|
| `get_self_info()` | 机器人自身信息 | 公开 Web API（bot-info） |
| `get_user_info(user_id)` | 用户信息（任意用户可查） | 公开 Web API（user/homepage） |
| `get_group_info(group_id)` | 群信息 | 公开 Web API（group-info） |
| `upload_file(*, type, name, ...)` | 上传文件（自动判定 image/video/file） | Bot 开放 API |
| `get_file(file_id)` | 获取文件（file_id 即 URL） | — |
| `delete_message(message_id, *, chat_id, chat_type)` | 撤回消息 | Bot 开放 API（/bot/recall） |

> **注意**：`get_self_info` / `get_user_info` / `get_group_info` 通过**非官方公开 Web API**（chat-web-go.jwzhd.com）实现，这些接口无需鉴权但非官方文档、可能随平台更新变动；失败时返回标准错误响应。

### 不支持的标准动作

以下标准动作云湖无对应 API，调用时返回 `retcode=10002`（不支持的操作）：
- `get_friend_list`（Bot 开放 API 的"机器人用户列表"尚在待上线状态）
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### 平台扩展动作

通过 `Api.call("yunhu.xxx", **params)` 调用云湖特有动作（参数采用 OB12 风格命名，适配器自动翻译为云湖字段）：

| 扩展动作 | 说明 | 等价 Send 方法 |
|---------|------|---------------|
| `yunhu.recall` | 撤回消息（msg_id, chat_id, chat_type） | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | 移除群成员（group_id, user_id） | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | 禁言（group_id, user_id, duration） | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | 解除禁言（group_id, user_id） | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | 群标签 CRUD（group_id, ...） | `Send.To("group", g).CreateTag(...)` 等 |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | 给用户添加/移除标签 | `Send.To("group", g).AddUserTag(...)` 等 |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **成员头衔语义别名**（标签≈头衔，内部映射到 tag.relate） | — |
| `yunhu.msg_type_limit` | 群消息类型限制（group_id, type） | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | 获取历史消息（chat_id, chat_type, message_id?, before?, after?） | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | 公开 bot-info 查询（bot_id） | — |
| `yunhu.user_homepage` | 公开用户主页查询（user_id） | — |

```python
# 平台扩展示例
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **标签与头衔**：云湖的"标签"语义等同 OneBot12 群成员 `title`。`yunhu.set_member_title` 是 `yunhu.tag.relate` 的原生语义别名，二者内部映射到同一端点。群消息事件中发送者角色由 `senderUserLevel` 映射到标准 `role` 字段（owner/admin/member）。

## 发送方法返回值

所有发送方法均返回一个 Task 对象，可以直接 await 获取发送结果。返回结果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 执行状态
    "retcode": 0,             // 返回码
    "data": {...},            // 响应数据
    "self": {...},            // 自身信息（包含 bot_id）
    "message_id": "123456",   // 消息ID
    "message": "",            // 错误信息
    "yunhu_raw": {...}        // 原始响应数据
}
```

## 特有事件类型

需要 platform=="yunhu" 检测再使用本平台特性

### 核心差异点

1. 特有事件类型：
    - 表单（如表单指令）：yunhu_form
    - 表情包/贴纸消息段：yunhu_expression
    - 按钮点击：yunhu_button_click
    - A2UI按钮点击：yunhu_a2ui_button
    - 机器人设置：yunhu_bot_setting
    - 快捷菜单：yunhu_shortcut_menu
2. 标准字段扩展（4.3.0+）：
    - 消息事件新增标准 `role` 字段（由云湖 `senderUserLevel` 映射为 `owner`/`admin`/`member`）
    - 新增 `user_avatar` 字段（发送者头像 URL）
3. 扩展字段：
    - 所有特有字段均以yunhu_前缀标识
    - 保留原始数据在yunhu_raw字段
    - 私聊中self.user_id表示机器人ID

### 特殊字段示例

```python
# 表单命令
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "表单指令名",
    "id": "指令ID",
    "form": {
      "字段ID1": {
        "id": "字段ID1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "字段标签",
        "value": "字段值"
      }
    }
  }
}

# 按钮事件
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "点击按钮的用户ID",
  "user_nickname": "用户昵称",
  "message_id": "消息ID",
  "yunhu_button": {
    "id": "按钮ID（可能为空）",
    "value": "按钮值"
  }
}

# A2UI按钮事件
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "操作用户ID",
  "user_nickname": "用户昵称",
  "message_id": "消息ID",
  "yunhu_a2ui": {
    "recv_id": "接收者ID",
    "recv_type": "接收者类型",
    "action_name": "操作名称",
    "source_component_id": "来源组件ID",
    "form_context": {},
    "interaction_json": "交互数据JSON字符串"
  }
}

### 按钮点击事件处理示例

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """处理云湖通知事件

    使用通用的 on_notice() 装饰器来处理所有通知事件，
    然后通过 detail_type 区分不同类型的通知
    event.reply() 会自动通过云湖平台回复
    """
    # 检查是否是按钮点击事件
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"用户 {user_nickname}({user_id}) 点击了按钮: {button_value}")

        # 使用 event.reply() 自动回复（会根据平台自动选择正确的发送方式）
        if button_value == "confirm":
            await event.reply("你点击了确认按钮！")
        elif button_value == "cancel":
            await event.reply("操作已取消")
        else:
            await event.reply(f"收到你的选择: {button_value}")

    # 处理快捷菜单事件
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"触发了快捷菜单: {menu_id}")

    # 处理机器人设置变更
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"设置已更新: {settings}")

    # 处理A2UI按钮事件
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI操作: {action_name}, 表单数据: {form_context}")
```

### 使用链式调用发送带按钮消息

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "确认", "actionType": 3, "value": "confirm"},
        {"text": "取消", "actionType": 3, "value": "cancel"},
        {"text": "查看详情", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# 发送带按钮的消息到群组
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("请确认以下操作")

# 发送带按钮的消息到用户私聊
await yunhu.Send.To("user", "789").Buttons(buttons).Text("请选择你的偏好设置")
```

### 发送A2UI消息

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# 发送A2UI消息
await yunhu.Send.To("user", user_id).A2UI("A2UI交互卡片内容")
```

# 机器人设置
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "群组ID（可能为空）",
  "user_nickname": "用户昵称",
  "yunhu_setting": {
    "设置项ID": {
      "id": "设置项ID",
      "type": "input/radio/checkbox/select/switch",
      "value": "设置值"
    }
  }
}

# 快捷菜单
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "触发菜单的用户ID",
  "user_nickname": "用户昵称",
  "group_id": "群组ID（如果是群聊）",
  "yunhu_menu": {
    "id": "菜单ID",
    "type": "菜单类型(整数)",
    "action": "菜单动作(整数)"
  }
}
```

## Event Mixin 扩展方法

适配器注册了以下平台专有方法，仅在 `platform == "yunhu"` 时可用：

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 获取云湖原始事件数据（`yunhu_raw`） |
| `get_sender_level()` | `str` | 发送者云湖原生级别（owner/administrator/member/unknown） |
| `get_sender_role()` | `str` | 发送者 OneBot12 标准 role（owner/admin/member） |
| `get_sender_title()` | `str` | 发送者头衔（标准 `title` 字段访问器，预留） |
| `get_sender_avatar()` | `str` | 发送者头像 URL |
| `get_command()` | `dict` | 指令数据（仅指令消息事件，`yunhu_command`） |
| `get_button_value()` | `str` | 按钮点击事件的 value（`yunhu_button.value`） |
| `get_a2ui_action()` | `str` | A2UI 按钮事件的 actionName |
| `get_a2ui_form_context()` | `dict` | A2UI 按钮事件的表单上下文 |
| `get_menu_id()` | `str` | 快捷菜单事件 ID（`yunhu_menu.id`） |
| `get_setting()` | `dict` | 机器人设置事件的设置数据（`yunhu_setting`） |
| `is_command_message()` | `bool` | 是否为指令消息 |
| `is_button_click()` | `bool` | 是否为按钮点击事件 |
| `is_a2ui_button()` | `bool` | 是否为 A2UI 按钮事件 |

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    if event.get("platform") != "yunhu":
        return

    if event.is_button_click():
        value = event.get_button_value()
        await event.reply(f"你点击了按钮: {value}")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()
```

## 扩展字段说明

- 所有特有字段均以 `yunhu_` 前缀标识，避免与标准字段冲突
- 保留原始数据在 `yunhu_raw` 字段，便于访问云湖平台的完整原始数据
- `self.user_id` 表示机器人ID（从配置中的bot_id获取）
- 表单指令通过 `yunhu_command` 字段提供结构化数据
- 按钮点击事件通过 `yunhu_button` 字段提供按钮相关信息
- A2UI按钮事件通过 `yunhu_a2ui` 字段提供A2UI交互相关信息
- 机器人设置变更通过 `yunhu_setting` 字段提供设置项数据
- 快捷菜单操作通过 `yunhu_menu` 字段提供菜单相关信息
- 表情包/贴纸消息通过 `yunhu_expression` 消息段提供贴纸数据（sticker_id、贴纸包ID、图片尺寸等）

### 表情包/贴纸消息段 (yunhu_expression)

当用户发送表情包或贴纸时，消息段类型为 `yunhu_expression`：

```json
{
  "type": "yunhu_expression",
  "data": {
    "sticker_id": "35154",
    "sticker_pack_id": "1670",
    "expression_id": "0",
    "image_name": "sticker/fabb9077f2ba302402ea871cab3686ad7a3fc52c.gif",
    "width": 500,
    "height": 500
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `sticker_id` | string | 贴纸唯一标识 |
| `sticker_pack_id` | string | 贴纸包ID |
| `expression_id` | string | 表情ID |
| `image_name` | string | 表情图片文件路径 |
| `width` | int | 图片宽度（可选） |
| `height` | int | 图片高度（可选） |

使用示例：
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"收到表情包: sticker_id={data['sticker_id']}, 包ID={data['sticker_pack_id']}")
```

---

## 多Bot配置

### 配置说明

云湖适配器支持同时配置和运行多个云湖机器人账户。

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # 机器人token（必填）
mode = "ws"  # 接收模式（可选，默认为"ws"，可选值："ws"、"webhook"）
webhook_path = "/webhook/bot1"  # Webhook路径（可选，默认为"/webhook"）
enabled = true  # 是否启用（可选，默认为true）

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # 第二个机器人的token
webhook_path = "/webhook/bot2"  # 独立的webhook路径
enabled = true
```

**配置项说明：**
- `token`：云湖平台提供的API token（必填）
- `mode`：接收模式（可选，默认为 `"ws"`，可选值 `"ws"`、`"webhook"`）
- `webhook_path`：接收云湖事件的HTTP路径（可选，默认为"/webhook"，仅 webhook 模式使用）
- `enabled`：是否启用该账户（可选，默认为true）

**重要提示：**
1. 云湖平台的机器人ID在**运行时自动检测**，无需在配置中指定
2. webhook 模式下每个bot都应该有独立的`webhook_path`，以便接收各自的webhook事件
3. 在云湖平台配置webhook时，请为每个bot配置对应的URL，例如：
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### 使用Send DSL指定Bot

可以通过`Using()`方法指定使用哪个bot发送消息。该方法支持两种参数：
- **账户名**：配置中的 bot 名称（如 `bot1`, `bot2`）
- **bot_id**：配置中的 `bot_id` 值

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 使用账户名发送消息
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# 使用 bot_id 发送消息（自动匹配对应账户）
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# 不指定时使用第一个启用的bot
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **提示：** 使用 `bot_id` 时，系统会自动查找配置中匹配的账户。这在处理事件回复时特别有用，可以直接使用 `event["self"]["user_id"]` 来回复同一账户。

### 事件中的Bot标识

接收到的事件会自动包含对应的`bot_id`信息：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # 获取触发事件的机器人ID
        bot_id = event["self"]["user_id"]
        print(f"消息来自Bot: {bot_id}")
        
        # 使用相同bot回复消息
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("回复消息")
```

### 日志信息

适配器会在日志中自动包含 `bot_id` 信息，便于调试和追踪：

```
[INFO] [yunhu] [bot:30535459] 收到来自用户 user123 的私聊消息
[INFO] [yunhu] [bot:12345678] 消息发送成功，message_id: abc123
```

### 管理接口

```python
# 获取所有账户信息
bots = yunhu.bots

# 检查账户是否启用
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# 动态启用/禁用账户（需要重启适配器）
yunhu.bots["bot1"].enabled = False
```

### 旧配置兼容

旧版 `[Yunhu_Adapter.bots.*]` 配置（含 `bot_id` 字段）会自动迁移到 `accounts` 格式（`bot_id` 已改为运行时自动检测，配置中的值会被忽略）；建议尽快迁移到新格式。