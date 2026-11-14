# 迁移指南：从 AstrBot 到 ErisPulse

> [!TIP]
> **什么时候需要读这篇**：当你已有一个 AstrBot 机器人，想把它迁到 ErisPulse 时读这篇。全新搭建请直接看[快速开始](../quick-start.md)。

先说结论：**平台接入、模型、人格、知识库都能搬；AstrBot 插件不能搬**——两边插件 API 完全不同，插件需要按 ErisPulse 模块规范重写。数据不自动迁移。

## 概念对照

| AstrBot 里的 | ErisPulse 里的 | 说明 |
|---|---|---|
| 平台适配器（QQ/微信/Telegram…） | [平台适配器](../platform-guide/README.md) | 概念一致，装 ErisPulse 对应适配器即可 |
| LLM Provider（API Key、模型） | [QvQChat](../ecosystem/qvqchat.md) 模型池 | 都是 OpenAI 兼容接入；QvQChat 支持模型池自愈与难度路由 |
| 人格 Persona | QvQChat 人格系统 | 系统提示词 + 开场白 + 工具白名单，手工搬运 |
| 知识库 | QvQChat 知识库 | 世界书式关键词触发 + 向量检索，需重新导入 |
| WebUI | [Dashboard](../ecosystem/dashboard.md) | 模块启停、配置、日志、事件监控；QvQChat 另有独立控制台 |
| 插件 | 模块 | API 不同，需重写（见下） |
| 管理员/白名单 | 三维[作用域](../advanced/scope.md) + 模块自身权限（如 QvQChat `admins`） | 权限模型更细，逐模块配置 |

## 迁移步骤

1. **搭框架**：按[快速开始](../quick-start.md)初始化项目（Docker 或 pip 均可），装上 Dashboard
2. **接平台**：`epsdk install` 你原来用的平台适配器（QQ 生态装 OneBot 适配器，Telegram 装 Telegram 适配器……），登录方式与协议实现的选择和 AstrBot 时期相同
3. **装智能体**：`epsdk install ErisPulse-QvQChat`，在模型池里填入原来的 Base URL / API Key / 模型名
4. **搬人格与知识库**：人格到 QvQChat 人格页逐条新建；知识库文档重新导入
5. **重写插件**：按下节对照，把原插件的"命令 → 处理逻辑"翻译成 ErisPulse 模块

## 插件重写对照

同一个"收到 `/ping` 回 pong"的插件，两边的写法：

**AstrBot 插件**（示意，以 AstrBot 文档为准）：

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("ping")
async def ping(self, event: AstrMessageEvent):
    yield event.plain_result("pong")
```

**ErisPulse 模块**（完整可运行，见[模块开发入门](../developer-guide/modules/getting-started.md)）：

```python
from ErisPulse.Core.Event import command

@command("ping", help="测试机器人是否在线")
async def ping_handler(event):
    await event.reply("pong")
```

差异要点：

- **事件模型**：AstrBot 每个平台各自的事件对象；ErisPulse 是 OneBot12 统一事件，`event.reply` / SendDSL 在所有平台行为一致
- **包结构**：ErisPulse 模块是标准 Python 包，用 `epsdk create module` 脚手架生成，发布到 PyPI + 模块市场
- **定时任务 / 存储**：装 [Cron](../ecosystem/cron.md) 模块或直接用框架内置存储 API，不引第三方依赖

## 建议的迁移策略

**并行双跑**：ErisPulse 机器人先接一个测试群跑通全部功能，确认无缺失后再切主群。两边平台账号体系独立（各自的协议实现/Token），互不干扰，回退成本低。

> [!NOTE]
> AstrBot 的插件 API 与功能清单持续演进，本页对照以通用概念为主；具体某个插件能否找到 ErisPulse 等价物，先到[模块市场](https://www.erisdev.com/#market)搜一下，没有就照上节重写——多数业务插件在 ErisPulse 里的实现反而更短。

---

## 下一步

- **系统学习模块开发**：[模块开发入门](../developer-guide/modules/getting-started.md) → [核心概念](../developer-guide/modules/core-concepts.md)
- **AI 部分想配置得更细**：[QvQChat 通用智能体](../ecosystem/qvqchat.md)
- **还在犹豫要不要迁**：[对比：AstrBot 与 LangBot](comparison-agent-platforms.md)
