# 对比：ErisPulse 与 NoneBot2

> [!TIP]
> **什么时候需要读这篇**：当你会在 Python 机器人框架里写代码，正在 NoneBot2 和 ErisPulse 之间选型时读这篇。不写代码则跳过。

一句话定位差异：

- **NoneBot2**：插件生态最深厚的异步机器人框架，事件处理模型成熟，社区积累十余年
- **ErisPulse**：以 OneBot12 统一事件模型为核心的机器人 SDK，一份 handler 天然跨平台，模块级热重载与生态服务契约是原生设计

两者都是"开发者写代码"的框架，不是装好即用的产品。

## 设计差异对照

| 维度 | ErisPulse | NoneBot2 |
|---|---|---|
| 跨平台方式 | OneBot12 统一事件模型内建于核心，handler 无需感知平台差异 | 各适配器各有事件模型，跨平台依赖统一消息抽象插件（如 alconna） |
| 插件体系 | 模块 = PyPI 包 + `epsdk` CLI 安装 + [模块市场](https://www.erisdev.com/#market)索引 | 插件 = PyPI 包（`nonebot-plugin-*`），商店网站检索，pip 安装 |
| 发送 API | SendDSL 链式发送：@、回复、重试、超时、批量一行完成 | Matcher 侧 `send` / 各适配器 API，统一消息抽象由插件提供 |
| 热重载 | 模块/适配器级热重载，保存即生效，进程不重启 | dev 模式整进程 reload（文件变更重启进程） |
| AI 集成 | 框架零 AI 依赖；模块声明服务契约即自动成为 [QvQChat](../ecosystem/qvqchat.md) 智能体的工具；[ApiMCP](../ecosystem/apimcp.md) 可把机器人反向开放给 Claude 等 MCP 客户端 | 由社区插件按需组合 |
| 管理工具 | 官方 [Dashboard](../ecosystem/dashboard.md) Web 面板、`epsdk` CLI、ErisPulse-App 手机客户端 | 社区 WebUI 插件、nb-cli |
| 生产特性 | 三维作用域、归属权自动回收、影子模块灰度、模块间 RPC 服务契约 | 依赖注入、钩子系统、社区方案 |
| 存储 | 统一 KV + SQL API（sqlite/mysql/postgres 配置切换） | 各插件自选方案 |

## 什么时候选谁

**选 NoneBot2**：你需要它生态里已经存在的某个具体插件；或团队已深度熟悉其事件模型。插件存量是硬优势，别的差异都可以被代码弥补，生态不能。

**选 ErisPulse**：跨平台一致性是你的核心诉求（统一事件模型 + 16 个平台适配器）；你想要"改代码不重启"的开发节奏；你想让模块能力直接进入 AI 工具箱而不是单独接一遍 LLM。

> [!NOTE]
> 对照基于双方公开文档整理，NoneBot2 的插件生态与社区规模显著更大是客观事实；涉及决策请以[对方官方文档](https://nonebot.dev/)为准。

---

## 下一步

- **想看 ErisPulse 写起来什么样**：[5 分钟快速开始](../quick-start.md)
- **想了解统一事件模型的细节**：[基础概念](../getting-started/basic-concepts.md)
- **在对比"群里 AI 助手"类一体化平台**：[对比：AstrBot 与 LangBot](comparison-agent-platforms.md)
