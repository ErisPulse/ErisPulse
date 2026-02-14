# ErisPulse 文档

ErisPulse 是一个可扩展的多平台消息处理框架，支持通过适配器与不同平台进行交互，提供灵活的模块系统用于功能扩展。

## 文档导航

### 快速开始

- [快速开始指南](quick-start.md) - 安装和运行 ErisPulse 的入门指南

### 新手入门

如果你是第一次使用 ErisPulse，建议按以下顺序阅读：

1. [入门指南总览](getting-started/README.md)
2. [创建第一个机器人](getting-started/first-bot.md)
3. [基础概念](getting-started/basic-concepts.md)
4. [事件处理入门](getting-started/event-handling.md)
5. [常见任务示例](getting-started/common-tasks.md)

### 用户使用指南

- [安装和配置](user-guide/installation.md)
- [CLI 命令参考](user-guide/cli-reference.md)
- [配置文件说明](user-guide/configuration.md)

### 开发者指南

#### 模块开发

- [模块开发入门](developer-guide/modules/getting-started.md)
- [模块核心概念](developer-guide/modules/core-concepts.md)
- [Event 包装类详解](developer-guide/modules/event-wrapper.md)
- [模块开发最佳实践](developer-guide/modules/best-practices.md)

#### 适配器开发

- [适配器开发入门](developer-guide/adapters/getting-started.md)
- [适配器核心概念](developer-guide/adapters/core-concepts.md)
- [SendDSL 详解](developer-guide/adapters/send-dsl.md)
- [适配器开发最佳实践](developer-guide/adapters/best-practices.md)

#### 扩展开发

- [CLI 扩展开发](developer-guide/extensions/cli-extensions.md)

### 平台特性指南

- [平台特性说明](platform-guide/README.md)
- [云湖平台特性](platform-guide/yunhu.md)
- [Telegram 平台特性](platform-guide/telegram.md)
- [OneBot11 平台特性](platform-guide/onebot11.md)
- [OneBot12 平台特性](platform-guide/onebot12.md)
- [邮件平台特性](platform-guide/email.md)

### API 参考

- [核心模块 API](api-reference/core-modules.md)
- [事件系统 API](api-reference/event-system.md)
- [适配器系统 API](api-reference/adapter-system.md)

### 技术标准

- [事件转换标准](standards/event-conversion.md)
- [API 响应标准](standards/api-response.md)
- [命名规范](standards/naming-conventions.md)

### 高级主题

- [懒加载系统](advanced/lazy-loading.md)
- [生命周期管理](advanced/lifecycle.md)
- [路由系统](advanced/router.md)

### AI 辅助开发

- [AI 辅助开发](ai-support/README.md)

### 风格指南

- [文档风格指南](styleguide/docstring.md)

## 开发方式

ErisPulse 支持两种开发方式：

### 1. 模块开发（推荐）

创建独立的模块包，通过包管理器安装使用。这种方式便于分发和管理，适合公开发布的功能。

### 2. 嵌入式开发

直接在项目中嵌入 ErisPulse 代码，无需创建独立模块。这种方式适合快速原型开发或项目内部专用功能。

示例：

```python
# 直接嵌入使用
from ErisPulse import sdk
from ErisPulse.Core.Event import command

# 注册命令处理器
@command("hello")
async def hello_handler(event):
    await event.reply("你好！")

# 初始化 SDK
await sdk.init()
```

## 获取帮助

- GitHub 仓库：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 问题反馈：提交 Issue
- 技术讨论：查看 Discussions

## 相关链接

- [OneBot12 标准](https://12.onebot.dev/)
- [云湖官方文档](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)