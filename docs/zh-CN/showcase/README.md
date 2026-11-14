# 选型指南

> [!TIP]
> **什么时候需要读这篇**：当你在几个机器人框架 / AI 机器人平台之间做选择，想知道 ErisPulse 适合谁、不适合谁时读这篇。已经在用 ErisPulse 则跳过。

我们不认为存在"最好的框架"，只存在"匹配场景的框架"。这个目录用对照表说清 ErisPulse 与常见选项的设计差异，帮你做决定——包括什么时候应该**不选**我们。

| 你在对比什么 | 读这篇 | 面向 |
|---|---|---|
| ErisPulse vs NoneBot2 | [对比：NoneBot2](comparison-nonebot.md) | 开发者 |
| ErisPulse（+QvQChat）vs AstrBot / LangBot | [对比：AstrBot 与 LangBot](comparison-agent-platforms.md) | 想要"群里 AI 助手"的用户 |
| 从 AstrBot 迁移到 ErisPulse | [迁移指南：从 AstrBot 到 ErisPulse](migrate-from-astrbot.md) | AstrBot 现有用户 |

## 场景速查

- **想要装好即用的 AI 聊天机器人，不写代码**：AstrBot / LangBot 的起步体验更快；若你看重热重载、模块市场与 16 平台覆盖，用 ErisPulse + [QvQChat](../ecosystem/qvqchat.md) + [Dashboard](../ecosystem/dashboard.md) 也能到同一终点，多花约半小时初始化
- **要写业务代码、跨平台复用**：ErisPulse 的 OneBot12 统一事件模型让一份 handler 天然跨平台，无需为平台差异写适配分支
- **要给自己的模块/AI 做生态**：ErisPulse 模块声明服务即成为 AI 工具（[QvQChat](../ecosystem/qvqchat.md) 自动发现），生态与智能体原生联动
- **已有大量 NoneBot 插件依赖**：NoneBot2 十余年插件生态是客观优势，迁移成本需自行权衡

## 阅读纪律

对照内容基于各方公开文档整理，随版本演进可能过时——**涉及决策前请以对方官方文档为准**。发现失实或过时的描述，欢迎提 Issue 或 PR 修订，我们不删合理的批评。
