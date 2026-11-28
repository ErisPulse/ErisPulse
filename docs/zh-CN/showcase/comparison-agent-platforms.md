# 对比：ErisPulse 与 AstrBot / LangBot

> [!TIP]
> **什么时候需要读这篇**：当你想要的是"群里的 AI 助手"，正在 AstrBot / LangBot 这类一体化平台和 ErisPulse 之间选型时读这篇。要写非 AI 业务代码则看 [对比：NoneBot2](comparison-nonebot.md)。

一句话定位差异：

- **AstrBot / LangBot**：一体化 AI 聊天机器人平台——安装、配 Key、开聊，LLM 对话是产品中心
- **ErisPulse**：机器人框架/SDK——AI 是其中一个可装卸的模块（[QvQChat](../ecosystem/qvqchat.md)），框架本身还要承载非 AI 的业务逻辑

三者最终都能得到"群里有个会干活的 AI"，路径和天花板不同。

## 对照

| 维度 | ErisPulse + QvQChat | AstrBot / LangBot |
|---|---|---|
| 起步体验 | 初始化项目 + 装适配器 + 装 QvQChat + 配模型池，约10分钟 | 安装 + 配 Key 即用，更快 |
| 平台覆盖 | 16 个平台适配器（含云湖、邮件、终端、Webhook 桥） | 主流 IM 平台 |
| LLM 支持 | OpenAI 兼容模型池（自愈、故障转移、难度路由）、MCP 客户端 | 多家 Provider 内置接入 |
| AI 深度 | 工具循环 + 子智能体 + 长期记忆/用户画像 + 知识库 + 电脑操作沙箱 + 定时"计划-执行-审查" | 对话、人格、知识库、插件工具 |
| 生态联动 | 任意 ErisPulse 模块声明服务即自动成为 AI 工具，装卸模块即增减 AI 能力 | 安装对应插件扩展 AI 能力 |
| 反向开放 | [ApiMCP](../ecosystem/apimcp.md) 把机器人暴露为 MCP 工具，Claude 等 AI 客户端可直接操控 | — |
| 热重载 | 模块/适配器级，保存即生效 | 插件更新通常需重启 |
| 非 AI 业务 | 框架原生：命令系统、多轮对话、ORM、定时任务、消息统计等模块各自独立 | 平台以 AI 对话为中心，非 AI 能力依赖插件 |
| 管理面板 | Dashboard（模块/配置/日志/事件 + 第三方视窗注册）、手机 App、AI Builder | WebUI 内置 |
| 社区规模 | 较年轻，生态成长中 | 用户基数更大、第三方插件更多 |

## 什么时候选谁

**选 AstrBot / LangBot**：你要的就是快速用上 AI 聊天，不打算写业务代码，也不需要小众平台（如云湖）接入。它们是成熟的一体化方案。

**选 ErisPulse**：机器人除了 AI 还要干别的（定时推送、群管理、消息统计、桥接……），希望 AI 只是其中一个可拆的模块；或者你在意热重载的开发节奏、模块市场的分发方式、以及"装一个模块 AI 就多一项能力"的生态联动；或者你需要 ApiMCP 这种让外部 AI 操控机器人的反向通道。

> [!NOTE]
> 对照基于双方公开文档整理；AstrBot / LangBot 的用户基数与插件数量更大是客观事实，涉及决策请以[对方官方文档](https://astrbot.app/) / ([LangBot](https://docs.langbot.app/))为准。

---

## 下一步

- **从 AstrBot 过来**：[迁移指南：从 AstrBot 到 ErisPulse](migrate-from-astrbot.md)
- **想直接看 ErisPulse 上的 AI 长什么样**：[QvQChat 通用智能体](../ecosystem/qvqchat.md)
- **想先跑起来再说**：[5 分钟快速开始](../quick-start.md)
