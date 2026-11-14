# Sandbox 平台特性文档

SandboxAdapter 是 ErisPulse 内置的沙盒适配器，用于本地开发与模块调试——无需真实平台即可模拟消息收发。

---

## 文档信息

- 对应模块版本: 4.2.3
- 维护者: ErisPulse
- 最后更新: 2026-11-10

## 基本信息

- 平台简介：本地沙盒环境，提供虚拟用户/群组、Web 调试面板与消息持久化
- 适配器名称：SandboxAdapter
- 平台标识：`sandbox`
- 单账户设计（本地调试场景）
- 框架要求：软依赖 `ErisPulse>=2.7.1`（运行时检测提示，不强制）

## v5 范式更新（4.1.0）

- **Api DSL 最小集**：`get_self_info` / `get_status` / `get_version` / `get_supported_actions`
- **spawn_background 任务归属**：心跳任务改用 `runtime.spawn_background`
- **框架软依赖**：运行时检测 `ErisPulse>=2.7.1` 并提示
- 导入路径更新至 `Core.Bases`（BaseConfig）

## 标准化对齐（4.2.3）

响应结构与错误码遵循 [API 响应规范](../standards/api-response.md)。

### HTML 发送方法

- `.Html(html: str)`：发送 HTML 消息（经 html 通道渲染到 Web 面板）
- `.HTML(html: str)`：`.Html()` 的别名（与标准 Send 方法命名保持一致）

### 元动作（已标准）

标准元动作返回标准响应：

| 动作 | data 内容 |
|------|----------|
| `get_self_info` | `user_id`（配置的 `self_id`）/ `user_name`（`sandbox`） |
| `get_status` | `good`（运行状态）/ `bots`（账户列表） |
| `get_version` | `impl`（ErisPulse-SandboxAdapter）/ `version` / `onebot_version` |
| `get_supported_actions` | 支持的动作名列表 |

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

result = await sandbox.Api.get_self_info()   # 沙盒机器人身份
result = await sandbox.Api.get_status()
result = await sandbox.Api.get_version()
result = await sandbox.Api.get_supported_actions()
```

### 请求事件处理（Request stub）

沙盒会合成 `type="request"` 事件（好友/群申请，`request_id` 透传自模拟事件），模块可用标准方式审批（完整规范见 [请求操作规范](../standards/request-action-spec.md)）：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    await event.approve()   # 或 event.reject()
```

适配器侧 Request DSL 为**模拟桩**：`accept()` / `reject()` 校验 `request_id`（缺失时返回标准错误 `retcode=34001`，属于请求操作族错误码），校验通过后模拟审批成功返回标准成功响应，便于下游联调 `approve()` / `reject()` 流程。

### 错误码规范

| retcode | 含义 | 说明 |
|---------|------|------|
| 0 | 成功 | — |
| 10002 | 不支持 | 平台无对应能力 |
| 10003 | 参数错误 | 缺少或无效参数 |
| 10006 | 无效消息段数据 | `MergeForward` 节点无有效文本内容 |
| 34001 | 请求不存在 | `Request.accept()/reject()` 缺少 `request_id`（请求操作族） |

## 配置说明

```toml
[Sandbox]
self_id = "sandbox_bot"  # 沙盒机器人ID
enable = true            # 是否启用
```

## 使用说明

- 沙盒提供虚拟用户与群组，模块可像真实平台一样收发消息
- Web 调试面板可手动发送消息触发模块处理逻辑
- 消息数据持久化存储（`sdk.storage`），重启后可恢复

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

await sandbox.Send.To("private", "user1").Text("Hello")
await sandbox.Send.To("group", "group1").Markdown("**加粗**")
```

支持的发送类型包括：

| 方法 | 说明 |
|------|------|
| `.Text(text)` | 发送文本消息 |
| `.Image(file, summary=None)` | 发送图片 |
| `.Face(face_id)` | 发送表情 |
| `.Record(file, magic=False)` | 发送语音 |
| `.Voice(file)` | 发送语音（audio 通道） |
| `.Video(file)` | 发送视频 |
| `.File(file, filename=None)` | 发送文件 |
| `.Html(html)` / `.HTML(html)` | 发送 HTML 消息（后者为别名） |
| `.Markdown(markdown)` | 发送 Markdown 消息 |
| `.Json(json_data)` | 发送 JSON 卡片消息 |
| `.Xml(xml_data)` | 发送 XML 卡片消息 |
| `.Music(platform, id, title=None)` | 发送音乐消息 |
| `.Share(url, title, content=None, image=None)` | 发送链接分享 |
| `.Location(lat, lon, title=None, content=None)` | 发送位置消息 |
| `.Dice()` | 发送骰子 |
| `.Rps()` | 发送猜拳 |
| `.Poke(user_id, type="poke")` | 戳一戳 |
| `.Recall(message_id)` | 模拟撤回消息 |
| `.MergeForward(nodes, title="合并聊天记录")` | 发送合并转发消息（渲染为 `<details>` 折叠 HTML 卡片，html 通道发出），用于验证模块的合并转发逻辑 |
| `.Raw_ob12(message)` | 发送 OneBot12 原始消息段（纯 node 列表自动路由合并转发，混合列表 node 段降级为纯文本） |

`At` / `AtAll` / `Reply` 修饰器由框架 SendDSL 基类提供。
