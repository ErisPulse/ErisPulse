# ErisPulse 文档

ErisPulse 是一个可扩展的多平台消息处理框架，支持通过适配器与不同平台交互，提供灵活的模块系统用于功能扩展。

> **第一次使用?** 直接看 [5 分钟快速开始](quick-start.md) —— 从安装到运行第一个机器人，一条龙走完。
>
> 遇到不理解的术语?查看 [术语表](terminology.md)。

---

## 选择你的路径

根据你的目标，选择对应的学习路径。每条路径内部按由浅入深排列。

### 一、我要使用机器人

让机器人跑起来、装模块、做配置。

| 进度 | 文档 | 说明 |
|------|------|------|
| **① 上手** | [5 分钟快速开始](quick-start.md) | 安装、初始化、运行 —— 唯一的起步入口 |
| ② 深入 | [创建第一个机器人](getting-started/first-bot.md) | 编写第一个命令处理器 |
| ③ 概念 | [基础概念](getting-started/basic-concepts.md) | 理解适配器/模块/事件的设计 |
| ④ 实战 | [常见任务示例](getting-started/common-tasks.md) | 存储、定时任务、权限控制 |
| 参考 | [配置文件说明](user-guide/configuration.md) · [CLI 命令](user-guide/cli-reference.md) · [部署指南](user-guide/deployment.md) | 按需查阅 |
| 参考 | [平台特性指南](platform-guide/README.md) | 各平台（云湖/QQ/Telegram…）的差异 |

### 二、我要开发模块 / 适配器

为 ErisPulse 编写可分发的扩展。

| 类型 | 入门 | 进阶 |
|------|------|------|
| **模块开发**（推荐） | [模块开发入门](developer-guide/modules/getting-started.md) | [核心概念](developer-guide/modules/core-concepts.md) · [Event 包装类](developer-guide/modules/event-wrapper.md) · [最佳实践](developer-guide/modules/best-practices.md) |
| **适配器开发** | [适配器开发入门](developer-guide/adapters/getting-started.md) | [核心概念](developer-guide/adapters/core-concepts.md) · [SendDSL 详解](developer-guide/adapters/send-dsl.md) · [事件转换器](developer-guide/adapters/converter.md) · [最佳实践](developer-guide/adapters/best-practices.md) |
| **技术标准** | [标准规范总览](standards/README.md) | 适配器开发必须遵循的 [会话类型](standards/session-types.md) · [事件转换](standards/event-conversion.md) · [发送方法](standards/send-method-spec.md) · [API 响应](standards/api-response.md) · [请求操作](standards/request-action-spec.md) 规范 |
| **发布** | [发布与模块商店](developer-guide/publishing.md) | 将作品发布到 PyPI 和模块商店 |

### 三、我要深入理解原理

了解框架内部如何运作。

| 文档 | 说明 |
|------|------|
| [架构概览](architecture.md) | 可视化图表：核心架构、初始化流程、事件处理、生命周期 |
| [启动流程与手动控制](advanced/startup.md) | 启动链路拆解、手动驱动各环节、加载失败诊断 |
| [事件系统](api-reference/event-system.md) | 五大类事件的完整 API |
| [适配器系统](api-reference/adapter-system.md) | 适配器注册、启停、API 调用 |
| [核心模块](api-reference/core-modules.md) | Storage / Config / Logger / Router 等基础能力 |
| [生命周期管理](advanced/lifecycle.md) · [懶加载](advanced/lazy-loading.md) · [路由系统](advanced/router.md) | 内部子系统 |
| [Conversation 多轮对话](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL 构建](advanced/sql-builder.md) · [HTTP 客户端](advanced/http-client.md) · [国际化](advanced/i18n.md) | 进阶工具 |

### 四、推荐生态模块

按需安装、即装即用的 **第三方社区模块**（不是框架内置功能）。

| 文档 | 说明 |
|------|------|
| [生态模块总览](ecosystem/README.md) | 了解如何安装生态模块、为什么这些不是内置功能 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理面板 + 视窗注册 API（模块可向侧边栏注册自定义页面） |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 图片渲染（HTML / 节点树 / SVG / 动画，内置中英文字体） |

### 五、我要为 ErisPulse 贡献

让框架更好

| 文档 | 说明 |
|------|------|
| [为 ErisPulse 贡献](contributing/README.md) | 贡献方式总览：文档 / i18n / Bug / 模块 / 适配器 |
| [首次贡献](contributing/first-contribution.md) | 从 fork 到提交 PR |

---

## 开发方式

ErisPulse 支持两种开发方式：

- **模块开发（推荐）**：创建独立的模块包，通过包管理器安装，便于分发和管理。
- **嵌入式开发**：直接在项目中编写处理器，适合快速原型。详见 [快速开始](quick-start.md)。

## 其他

- [文档风格指南](styleguide/docstring.md) — 贡献文档时的写作规范
- [为 ErisPulse 贡献](contributing/README.md) — 参与项目共建的入口
- [AI 辅助开发](ai-support/README.md) — 获取供 AI 编程助手使用的项目提示词

## 获取帮助

- GitHub 仓库：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 问题反馈：提交 Issue
- 技术讨论：查看 Discussions

## 相关链接

- [OneBot12 标准](https://12.onebot.dev/)
- [云湖官方文档](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
