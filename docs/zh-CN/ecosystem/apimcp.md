# ErisPulse-ApiMCP 用 AI 客户端操控机器人

> [!TIP]
> **什么时候需要读这篇**：当你想让 Claude Desktop 等支持 MCP 的 AI 客户端直接操控你的机器人——发消息、看消息、调模块、管适配器、观测事件流——时读这篇。不需要则跳过。

[ErisPulse-ApiMCP](https://github.com/wsu2059q/ErisPulse-ApiMCP) 把机器人运行时能力经 **MCP（Model Context Protocol）** 开放给 AI 客户端：装上之后，Claude Desktop 里就多出 14 个工具，AI 可以替你收发消息、排查模块问题、订阅群聊事件——机器人从"你管理的程序"变成"AI 的手和眼"。

> [!IMPORTANT]
> ApiMCP 需要单独安装，且**必须显式配置 token** 后桥才启用：
>
> ```bash
> epsdk install ErisPulse-ApiMCP
> ```
>
> 在 `config.toml` 的 `[ApiMCP]` 节设置 `token = "长随机串"`（或环境变量 `ERISPULSE_APIMCP_TOKEN`）。未配置时除探活外所有端点返回 503，避免令牌静默泄漏。

## 工作原理

两层结构，机器人本体不引入任何 AI 依赖：

- **机器人进程内**：ApiMCP 模块在框架内置 HTTP server 上挂一个 REST 桥（`/apimcp/*`，token 鉴权，默认限流 30 请求/分钟）
- **独立进程**：`erispulse-apimcp` 命令用官方 `mcp` SDK 起 stdio server，把 MCP 工具调用转发到机器人 HTTP 桥

```
Claude Desktop ──MCP(stdio)──► erispulse-apimcp ──HTTP──► 机器人进程 REST 桥 ──► sdk.*
```

机器人不在线或桥未配置时，工具返回可读错误与排查指引，不抛栈。

## Claude Desktop 接入

编辑 `claude_desktop_config.json`（Windows: `%APPDATA%\Claude\`；macOS: `~/Library/Application Support/Claude/`）：

```json
{
  "mcpServers": {
    "erispulse": {
      "command": "erispulse-apimcp",
      "env": {
        "ERISPULSE_APIMCP_URL": "http://127.0.0.1:8000",
        "ERISPULSE_APIMCP_TOKEN": "你的token"
      }
    }
  }
}
```

保存后完全重启 Claude Desktop，工具列表出现 `erispulse` 服务器即接入成功。任何支持 MCP stdio server 的客户端（Claude Code、Cursor 等）都能用同样方式接入。

## 14 个工具一览

| 类别 | 工具 | 说明 |
|---|---|---|
| 模块 | `list_modules` / `get_module_info` / `call_module` / `reload_module` | 查看与调用已装模块的公开服务，触发热重载 |
| 适配器 | `list_adapters` / `get_adapter_status` / `reload_adapter` | 平台在线状态；适配器重载默认禁用 |
| 消息 | `send_message` / `recent_messages` | 向任意平台发文本/图/音/视/文件；经 [transcript](../advanced/transcript.md) 回看最近消息 |
| 事件 | `subscribe_events` / `unsubscribe` / `poll_events` | 订阅消息/通知等事件，环形缓冲（默认 1000 条），增量轮询 |
| 运行时 | `get_topology` / `sdk_health` | 运行时拓扑（已脱敏）与健康摘要 |

一个典型用法：AI 先 `subscribe_events(["message"])`，然后周期性 `poll_events` 观察群里在聊什么，决定要不要 `send_message` 插话或 `call_module` 触发某个模块的能力。

## 安全要点

- **token 即完全控制权**：能读消息、发消息、调白名单内模块方法。切勿提交仓库或贴到公开频道；多租户场景请拆多个机器人实例
- **最小授权**：`module_call_whitelist` 收窄可调用模块（支持 `模块.方法` 精确放行），`send_target_whitelist` 收窄发送目标（如只允许发某个群），`allow_adapter_reload` 保持默认关闭
- **只监听本机**：仅本机使用时把框架 HTTP server 设为 `server.host = "127.0.0.1"`；跨机器必须内网 + 反向代理加 TLS
- 输出经过键名级净化（密钥/路径类键整键丢弃）；深度净化是模块自身责任，敏感会话勿开放订阅

完整配置项（缓冲容量、回溯窗口、事件类型白名单等）与 REST 端点明细见[项目 README](https://github.com/wsu2059q/ErisPulse-ApiMCP)。

---

## 下一步

- **想让 AI 在群里"活"起来而不只是被操控**：QvQChat 是正向方向——智能体主动聊天干活，见 [QvQChat 通用智能体](qvqchat.md)；ApiMCP 是反向方向——外部 AI 操控机器人，两者可同装
- **想看最近消息的数据从哪来**：[会话收件箱 transcript](../advanced/transcript.md)
- **想了解机器人 HTTP server**：[路由系统](../advanced/router.md)
