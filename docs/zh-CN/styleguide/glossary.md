# 术语表（唯一真相源）

> [!TIP]
> **什么时候需要读这篇**：写文档 / 改文档时拿不准一个概念该叫什么，或发现两篇文档对同一概念说法不一致时。不需要则跳过。

本表收敛 ErisPulse 文档中曾经多处不一致的核心概念。每个术语只给一个**正式名**、一组**中英对照**与一段**历史别名说明**；正文与其它文档冲突时，以本表为准，并请顺手修正冲突文档。

收录原则：

- 只收"历史上叫法漂移过、或中英混用易歧义"的概念；纯代码标识符（如 `BaseModule`）不加收录
- 每条定义均先在 `docs/zh-CN` 全库与源码中 grep 验证过实际用法，定义与主流用法一致
- 文档内首次出现时给全称（中文 + 括注英文），后续用简称

---

## 1. Client 与 HttpClient

| 项 | 内容 |
|------|------|
| 正式名 | `Client`（基类 `BaseClient`） |
| 中英对照 | Client（统一 HTTP/WS 客户端） |
| 历史别名 | `HttpClient`（2.8.0 前类名，保留兼容别名）；`BaseHttpClient`（2.8.0 前基类名，保留兼容别名） |

**唯一定义**：统一 HTTP/WS 客户端，通过抽象层封装底层请求库（当前为 aiohttp），提供请求统计、重试、日志、WebSocket 客户端与 ErisPulse 异常体系。2.8.0 起类名由 `HttpClient` 更名为 `Client`，**`sdk.client` 属性名不变**。

**文档写法**：一律写 `Client`；仅在"旧代码迁移 / 兼容"语境提及 `HttpClient`，并括注"兼容别名"。定义出处见 [http-client](../advanced/http-client.md) 与 [架构总览](../architecture.md)。

## 2. storage、env 与 StorageManager

| 项 | 内容 |
|------|------|
| 正式名 | 实例：`storage`（类型 `BaseStorage`）；基类：`BaseStorage` |
| 中英对照 | storage（存储）；StorageManager（存储管理器，旧类名） |
| 历史别名 | `env`（v1 遗留别名，= 同一实例）；`StorageManager`（多后端重构前 SQLite 实现的原类名，现为 `SQLiteStorage` 的兼容别名） |

**唯一定义**：运行时存储通过实例 `storage` 访问（`sdk.storage` 或 `from ErisPulse import storage`），具体后端由 `ErisPulse.storage.backend` 配置调度（默认 sqlite，可切 mysql / postgres），三后端 API 一致。

**文档写法**：描述"存储系统 / 存储能力"用「存储（storage）」；指类型写 `BaseStorage`；指具体后端写 `SQLiteStorage` / `MySQLStorage` / `PostgresStorage`。`StorageManager` **只是 SQLite 实现类的兼容旧名**，不代表存储系统整体，新文档不使用；`env` 是 v1 遗留别名（同一实例），仅存量旧代码兼容，文档与示例一律用 `sdk.storage`。定义出处见 [存储后端](../advanced/storage-backends.md) 与 [SQL 构建器](../advanced/sql-builder.md)。

## 3. BaseConfig 与 AdapterConfig（含 ui / webui 元数据键）

| 项 | 内容 |
|------|------|
| 正式名 | 配置基类：`BaseConfig`；字段控件配置键：`"ui"` |
| 中英对照 | BaseConfig（声明式配置基类）；AdapterConfig（旧名，兼容别名） |
| 历史别名 | `AdapterConfig`（= `BaseConfig` 的向后兼容别名）；`"webui"` 字段元数据键（旧名，仍兼容） |

**唯一定义**：`BaseConfig` 是通用声明式配置基类，适用于适配器、模块、外部项目等任何场景（配置类以嵌套类 `ConfigClass` 声明挂到模块 / 适配器上）。字段 `metadata` 中 WebUI 控件配置键的正式名是 `"ui"`；读取优先级 `"ui"` > `"webui"`，`"webui"` 仅旧代码兼容。

**文档写法**：一律写 `BaseConfig` 与 `"ui"`。注意区分：示例代码里 `MyAdapterConfig` 这类名字是**开发者自己配置子类的命名习惯**，与 `AdapterConfig` 别名无关。定义出处见 [适配器基础概念](../developer-guide/adapters/core-concepts.md) 与 [模块基础概念](../developer-guide/modules/core-concepts.md)。

## 4. 作用域（scope）三维

| 项 | 内容 |
|------|------|
| 正式名 | 整体：作用域（scope）；三维：**模块维度 / 身份维度 / 出站维度** |
| 中英对照 | module dimension（模块维度）、identity dimension（身份维度）、outbound dimension（出站维度） |
| 历史别名 | 无旧名，但历史上出现过"权限系统 / 黑白名单系统"等不准确的泛称 |

**唯一定义**（对应源码 `Core/scope.py` 的三个判定入口）：

- **模块维度**：某个上下文里哪些模块可用——`scope.is_allowed`，绑定三级：平台 / Bot / 会话（优先级 会话 > Bot > 平台）
- **身份维度**：谁的事件收不收（事件准入）——`scope.is_identity_allowed`，策略四级：用户 / 会话 / Bot / 适配器（取最具体者）
- **出站维度**：模块能向外做什么（出站动作限制）——`scope.is_action_allowed`，默认全允许、显式收紧才禁，支持方法级细粒度

**文档写法**：三个维度名固定用"模块维度 / 身份维度 / 出站维度"，不用"模块过滤 / 身份校验 / 动作限制"等变体作正式名；文档中的 ①②③ 编号只是行文标记，不属于名称。黑白名单仅是模块维度配置的一种形态，不用它指称整个作用域系统。定义出处见 [作用域（scope）](../advanced/scope.md)。

## 5. owner / 归属权 / owner 上下文

| 项 | 内容 |
|------|------|
| 正式名 | 系统名：**归属权（owner）系统**；机制名：**owner 上下文** |
| 中英对照 | ownership（归属权）、owner context（owner 上下文）、`current_owner`（当前归属者） |
| 历史别名 | 中英混用：文档中"归属权""owner"曾交替指同一系统 |

**唯一定义**：归属权是模块"即插即用"的基石——模块在 owner 上下文中注册的一切框架资源（任务、连接、定时器、翻译域等）自动记名，模块卸载时统一回收。**owner 上下文**指模块代码执行期间由框架记录的当前归属者（`current_owner` 上下文变量），资源在该上下文内创建即归属当前模块；上下文不可用时（如工具线程回调）应显式传 `owner` 参数。统一回收门面为 `ErisPulse.Core.ownership`。

**文档写法**：中文行文用「归属权」，系统名首次出现写全「归属权（owner）系统」；代码标识与上下文机制名保留英文（owner 上下文、`current_owner`、`owner_scope`）。不用"所有权""属主"等译法。定义出处见 [归属权（owner）系统](../advanced/ownership.md)。

## 6. module.call 三词边界：服务契约 / 服务目录 / 服务白名单

| 项 | 内容 |
|------|------|
| 机制名 | **服务契约**（`meta.services` 声明端） |
| 接口名 | **服务目录**（`sdk.module.services()` 查询端） |
| 描述性词 | **服务白名单**（仅描述声明后的收紧语义，不作机制标题） |

**唯一定义**：

- **服务契约（meta.services）**：模块作者在 `get_meta()` 的 `services` 字段声明对外可调方法——契约的**声明端**。未声明时任意公开方法可调（向后兼容），声明后调用面收紧、越界抛 `ServiceNotProvidedError`
- **服务目录（services()）**：`sdk.module.services()` 运行时查询接口，列出已显式声明契约的模块及其方法签名与介绍——契约的**消费端**视图，为 MCP 化（调用点暴露给 AI）提供数据基础
- **服务白名单**：只用来**描述**"声明后仅白名单内方法可调"这一语义的行文词汇，不作为机制或接口的名称出现在标题中

一句话边界：**作者声明叫契约，运行时查询叫目录，"白名单"只描述收紧语义**。定义出处见 [模块间通信](../advanced/module-communication.md) 与 [核心模块 API](../api-reference/core-modules.md)。

---

## 相关页面

- [注释风格规范](docstring.md) - docstring 内特殊标签的写法与解析契约
- [文档与对外写作规则](docs-writing.md) - 术语之外的行文与结构规范
