# 高级主题

本目录包含 ErisPulse 框架的高级特性和深入主题。

## 文档列表

- [启动流程与手动控制](startup.md) - 启动链路拆解（Finder/Loader/Manager/Router）与手动完整启动
- [懒加载系统](lazy-loading.md) - 懒加载模块系统的工作原理、配置与事件驱动懒激活（activate_on）
- [作用域（scope）](scope.md) - 三维作用域控制：模块可用性 / 事件准入 / 出站动作限制（含方法级细粒度规则与绑定继承 merge）
- [归属权（owner）系统](ownership.md) - 资源归属与自动回收：owner 上下文机制、归属资源全景、卸载清理序列与设计边界
- [交互会话系统](interaction.md) - wait_reply / 会话定时器 / 多路等待 / 会话互斥租约 / 收件箱 / 消息事务 / 链路追踪
- [模块间通信](module-communication.md) - RPC 协议化（module.call）、服务契约与目录、定向事件、冷启动回放、事件幂等去重
- [国际化 (i18n)](i18n.md) - 多语言支持、翻译注册与语言检测
- [生命周期管理](lifecycle.md) - 生命周期事件系统的使用方法
- [路由管理器](router.md) - HTTP 和 WebSocket 路由管理
- [HTTP 客户端](http-client.md) - 统一 HTTP 请求客户端
- [MessageBuilder 详解](message-builder.md) - OneBot12 消息段构建器的双模式用法
- [SQL 查询构建器](sql-builder.md) - 通用 SQL 链式查询构建器及存储后端抽象
- [存储后端](storage-backends.md) - sqlite / mysql / postgres 异步原生存储后端的选择、配置与切换
- [异常体系与捕获指南](errors.md) - 框架全部异常类型、发生位置与捕获建议
- [会话类型系统](../standards/session-types.md) - 会话类型定义、映射与自定义类型注册
- [Conversation 多轮对话](conversation.md) - 多轮对话上下文的交互方法

> [!NOTE]
> Dashboard 视窗注册、Takumi 图片渲染等 **第三方生态模块** 的文档已迁移至 [生态模块](../ecosystem/README.md) 目录。

## 适用对象

这些文档适合以下开发者：

- 已经熟悉 ErisPulse 基础功能的开发者
- 需要深入理解框架内部机制的开发者
- 需要优化性能或实现复杂功能的开发者

## 前置知识

阅读本目录文档前，建议先了解：

- [基础概念](../getting-started/basic-concepts.md)
- [事件处理入门](../getting-started/event-handling.md)
- [模块开发指南](../developer-guide/modules/)