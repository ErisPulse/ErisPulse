# 技能清单

本目录由 CI 从文档自动构建，每个技能覆盖一个主题，按需安装即可。

| 技能 | 主题 | 适用场景 | 文档数 |
|---|---|---|---|
| `erispulse-getting-started` | 快速上手与核心概念 | 第一次接触 ErisPulse，想从零跑起一个机器人并理解核心概念 | 7 |
| `erispulse-module-dev` | 模块开发 | 要开发 ErisPulse 模块（业务逻辑载体）：命令、事件、多轮对话、ORM | 7 |
| `erispulse-adapter-dev` | 适配器开发 | 要把一个聊天平台接入 ErisPulse：协议转换、发送规范、发布流程 | 7 |
| `erispulse-adapter-standards` | 适配器技术标准 | 实现/评审适配器时需要对照的硬性技术规范 | 7 |
| `erispulse-config-cli` | 配置系统与 CLI 工具链 | 配置声明式 schema、排查配置问题、使用 epsdk 命令行与部署 | 4 |
| `erispulse-hot-reload` | 热重载与懒加载休眠 | 改代码不重启（热重载）、闲置自动归眠（dormant_after）、运行时注册模块 | 3 |
| `erispulse-scope-ownership` | 权限作用域与归属权 | 写生产级模块绕不开的两套机制：谁能收到什么（scope）、资源归谁怎么回收（ownership） | 3 |
| `erispulse-communication` | 通信与连接 | 模块间通信（RPC/定向/广播）、HTTP/WS 客户端、连接管理 | 4 |
| `erispulse-shadow-transcript` | 影子灰度与消息追踪 | 新旧版本灰度对照（shadow）、消息收件箱与行为追踪（transcript） | 2 |
| `erispulse-errors-troubleshooting` | 异常体系与排障 | 遇到异常/组件不工作时的诊断路径：异常总览、排障指南、bug 追踪 | 2 |
| `erispulse-ecosystem` | 生态与多平台 | 了解生态组件（Dashboard/Cron/AI 模块等）与各平台适配器的接入差异 | 6 |

## 安装

1. 下载同目录下的 `skills-<语言>.zip`（或直接拷贝本目录）
2. 解压后把技能目录拷入智能体的技能目录（如 `.zcode/skills/`、`.claude/skills/`）
3. 智能体按各技能 `description` 自动触发，无需手动引用

> 由 `python -m scripts.tools gen skills` 生成，请勿手改。
