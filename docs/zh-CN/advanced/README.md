# 高级主题

本目录收录 ErisPulse 框架的进阶专题——权限管控、灰度发布、多轮交互、存储后端等
深度能力，每篇解决一类具体问题。

> [!NOTE]
> 本目录全部为**按需查阅**的专题文档——请先读完首页的 L1 核心五篇，
> 遇到对应需求再来翻。每篇开头标有"什么时候需要读这篇"。

## L2 必读四篇

写生产级模块绕不开的四篇，建议在做复杂模块前通读（口径与文档首页一致）：

- [作用域（scope）](scope.md) - 三维作用域控制：模块可用性 / 事件准入 / 出站动作限制（含方法级细粒度规则与绑定继承 merge）
- [归属权（owner）系统](ownership.md) - 资源归属与自动回收：owner 上下文机制、归属资源全景、卸载清理序列与设计边界
- [生命周期管理](lifecycle.md) - 生命周期事件系统：模块 / 适配器加载、卸载、重载、禁用时各自该做什么
- [交互会话系统](interaction.md) - wait_reply / 会话定时器 / 多路等待 / 会话互斥租约 / 收件箱 / 消息事务 / 链路追踪

## 按场景分组

与文档首页「深入理解原理」的分组口径一致，每组首篇标注"不懂会踩什么坑"。

**运行启动** —— 不懂启动链路（Finder / Loader / Manager / Router），模块加载失败时只能对着日志干瞪眼

- [启动流程与手动控制](startup.md) - 启动链路拆解（Finder/Loader/Manager/Router）与手动完整启动
- [懒加载系统](lazy-loading.md) - 懒加载模块系统的工作原理、配置与事件驱动懒激活（activate_on）

**通信连接** —— 不懂服务契约（`meta.services`）白名单，跨模块 `module.call` 会被 `ServiceNotProvidedError` 拒绝且不知原因

- [模块间通信](module-communication.md) - RPC 协议化（module.call）、服务契约与目录、定向事件、冷启动回放、事件幂等去重
- [连接池与广播](connections.md) - 连接注册表：广播、分组订阅、跨模块传递与复用、连接池查看
- [路由管理器](router.md) - HTTP 和 WebSocket 路由管理（含单参注册、元组响应约定）

**数据存储** —— 不懂连接失败冷却期语义，数据库抖动时会误判"框架挂了"（实际是快速失败、冷却后自动重连）

- [存储后端](storage-backends.md) - sqlite / mysql / postgres 异步原生存储后端的选择、配置与切换
- [SQL 查询构建器](sql-builder.md) - 通用 SQL 链式查询构建器及存储后端抽象
- [HTTP 客户端](http-client.md) - 统一 HTTP 请求客户端

**消息对话** —— 不懂会话互斥租约，两个模块同时等同一用户的回复会互相踢掉

- [Conversation 多轮对话](conversation.md) - 多轮对话上下文的交互方法
- [会话收件箱](transcript.md) - 消息自动记录：保留策略旋钮、运行时覆盖 API 与风险/审计
- [MessageBuilder 详解](message-builder.md) - OneBot12 消息段构建器的双模式用法
- [国际化 (i18n)](i18n.md) - 多语言支持、翻译注册与语言检测

**灰度影子** —— 不懂五道隔离闸就提前转正，影子的出站消息会外溢到真实用户

- [影子模块与灰度转正](shadow.md) - 模块新版本独立 owner 并行试运行：出站拦截记账、行为 diff 对比、promote 转正与失败回滚

**异常与规范参考**

- [异常体系与捕获指南](errors.md) - 框架全部异常类型、发生位置与捕获建议
- [会话类型系统](../standards/session-types.md) - 会话类型定义、映射与自定义类型注册

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