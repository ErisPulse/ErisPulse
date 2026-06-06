# API 参考

本目录包含 ErisPulse 框架的 API 参考文档。

## 文档列表

| 文档 | 说明 |
|------|------|
| [核心模块 API](core-modules.md) | Storage、Config、Logger、Adapter、Module、Lifecycle、Router、HTTP Client 的 API 快速参考 |
| [事件系统 API](event-system.md) | Command、Message、Notice、Request、Meta 事件模块的 API 参考 |
| [适配器系统 API](adapter-system.md) | Adapter 管理器、SendDSL、中间件、Bot 状态管理的 API 参考 |
| [自动生成 API](auto_api/README.md) | 从源码 docstring 自动生成的完整 API 文档 |

> 手动编写的 API 文档侧重于用法示例和快速查阅；自动生成的 API 文档包含完整的类/方法签名，两者互补。

## 模块概览

### 核心模块

| 模块 | 访问路径 | 说明 |
|------|---------|------|
| `sdk.storage` | `sdk.storage` | 基于 SQLite 的键值存储 + SQL 链式查询 |
| `sdk.config` | `sdk.config` | TOML 格式的配置管理 |
| `sdk.logger` | `sdk.logger` | 模块化日志系统，支持子日志器 |
| `sdk.adapter` | `sdk.adapter` | 多平台适配器管理 |
| `sdk.module` | `sdk.module` | 模块注册、加载、卸载管理 |
| `sdk.lifecycle` | `sdk.lifecycle` | 生命周期事件管理 |
| `sdk.router` | `sdk.router` | HTTP/WebSocket 路由管理 |
| `sdk.client` | `sdk.client` | 统一 HTTP/WS 客户端 |

### 事件系统

| 模块 | 导入路径 | 说明 |
|------|---------|------|
| `command` | `ErisPulse.Core.Event.command` | 命令处理（前缀解析、别名） |
| `message` | `ErisPulse.Core.Event.message` | 消息事件（私聊、群聊、@消息） |
| `notice` | `ErisPulse.Core.Event.notice` | 通知事件（好友、群成员变化） |
| `request` | `ErisPulse.Core.Event.request` | 请求事件（好友请求、群邀请） |
| `meta` | `ErisPulse.Core.Event.meta` | 元事件（连接、断开、心跳） |

### 基类

| 基类 | 导入路径 | 说明 |
|------|---------|------|
| `BaseModule` | `ErisPulse.Core.Bases.module.BaseModule` | 模块基类（on_load/on_unload） |
| `BaseAdapter` | `ErisPulse.Core.Bases.adapter.BaseAdapter` | 适配器基类（start/shutdown/call_api） |

## 相关文档

- [核心概念](../getting-started/basic-concepts.md) - 理解框架核心概念
- [模块开发指南](../developer-guide/modules/) - 开发自定义模块
- [适配器开发指南](../developer-guide/adapters/) - 开发平台适配器
- [高级主题](../advanced/) - 路由、HTTP 客户端、SQL 构建器等深入文档
