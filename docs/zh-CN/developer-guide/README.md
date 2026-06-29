# 开发者指南

本指南帮助你开发自定义模块和适配器，扩展 ErisPulse 的功能。

## 内容列表

### 模块开发

1. [模块开发入门](modules/getting-started.md) - 创建第一个模块
2. [模块核心概念](modules/core-concepts.md) - 模块的核心概念和架构
3. [Event 包装类详解](modules/event-wrapper.md) - Event 对象的完整说明
4. [模块最佳实践](modules/best-practices.md) - 开发高质量模块的建议

### 适配器开发

1. [适配器开发入门](adapters/getting-started.md) - 创建第一个适配器
2. [适配器核心概念](adapters/core-concepts.md) - 适配器的核心概念
3. [SendDSL 详解](adapters/send-dsl.md) - Send 消息发送 DSL 的完整说明
4. [事件转换器](adapters/converter.md) - 实现事件转换器
5. [适配器最佳实践](adapters/best-practices.md) - 开发高质量适配器的建议

### 发布指南

- [发布与模块商店指南](publishing.md) - 将你的作品发布到 PyPI 和 ErisPulse 模块商店

## 开发准备

在开始开发之前，请确保你：

1. 阅读了[基础概念](../getting-started/basic-concepts.md)
2. 熟悉了[事件处理](../getting-started/event-handling.md)
3. 安装了开发环境（Python >= 3.10）
4. 安装了 ErisPulse SDK

## 开发类型选择

根据你的需求选择合适的开发类型：

| 开发类型 | 适用场景 | 入门指南 |
|---------|---------|---------|
| **模块开发** | 扩展机器人功能、实现业务逻辑、提供命令和消息处理 | [模块开发入门](modules/getting-started.md) |
| **适配器开发** | 连接新的消息平台、实现跨平台通信、提供平台特定功能 | [适配器开发入门](adapters/getting-started.md) |

> 如果你想扩展机器人的功能（如添加命令、处理消息），选择**模块开发**。如果你需要让机器人连接到一个新的平台，选择**适配器开发**。

## 开发工具

### 项目模板

ErisPulse 提供了示例项目作为参考：

- [模块示例](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module) - 模块的完整项目结构
- [适配器示例](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter) - 适配器的完整项目结构

### 开发模式

使用热重载模式进行开发，代码修改后自动重载：

```bash
epsdk run main.py --reload
```

### 调试技巧

在 `config/config.toml` 中启用 DEBUG 或 TRACE 级别日志：

```toml
[ErisPulse.logger]
# DEBUG: 输出模块加载、路由注册等开发调试信息
# TRACE: 最低级别，输出事件分发、存储写入、懒加载等框架内部详细流程
level = "DEBUG"
```

## 发布你的模块

完整的发布流程请参考 [发布与模块商店指南](publishing.md)，包括 PyPI 发布步骤、ErisPulse 模块商店提交流程等。

## 相关文档

- [标准规范](../standards/) - 确保兼容性的技术标准
- [平台特性指南](../platform-guide/) - 了解各平台适配器的特性
