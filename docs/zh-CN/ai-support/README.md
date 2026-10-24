# AI 辅助开发

ErisPulse 提供两种互补的 AI 辅助开发方式，让 AI 能基于最新框架规范生成代码：

- **物料文档**：一份大 Markdown，一次性灌入上下文，适合整项目开发
- **MCP 服务器**：让 AI 按需检索官方文档，适合日常代码补全和查 API

| | 物料文档 | MCP 服务器 |
|---|---|---|
| 形式 | 一份大 Markdown，**一次性灌入** | AI **按需检索** |
| 上下文成本 | 高（占 token） | 低（只取相关片段） |
| 时效性 | 随版本发布更新 | 实时（GitHub 拉取 + 缓存） |
| 适合 | 上下文窗口大、做整项目开发 | 日常代码补全、查 API |
| 客户端 | 任何 AI 工具 | 仅支持 MCP 的客户端 |

两者并不冲突：开发大型项目时可以同时用——物料文档打底，MCP 兜底查漏。

## 物料文档

物料文档位于 `prompts/` 目录下，按开发场景分为三种：

| 文档 | 场景 | 说明 |
|------|------|------|
| **ErisPulse-ModuleDev.md** | 模块开发 | 覆盖模块开发全流程（事件处理、路由、生命周期等） |
| **ErisPulse-AdapterDev.md** | 适配器开发 | 在模块开发基础上，外加适配器核心概念、SendDSL、平台适配指南 |
| **ErisPulse-Full.md** | 全栈参考 | 上述全部内容 + 完整用户指南与 API 参考合集 |

获取方式：从 `prompts/` 目录直接获取（与文档同步更新），或从 [GitHub Releases](https://github.com/ErisPulse/ErisPulse/releases) 下载对应版本。

### 使用方式

1. 根据目标选择文档（模块 → `ModuleDev`，适配器 → `AdapterDev`，复杂需求 → `Full`）
2. 将文档内容作为上下文提供给 AI：IDE 内放入工作区，对话类直接粘贴，API 调用作为 system message 注入
3. 用下方模板描述需求，越具体生成质量越高

### 需求描述模板

**模块：**

```
请基于 ErisPulse 模块开发规范，生成一个 [模块名称] 模块的完整代码。

功能描述：[核心功能]
需要监听的事件：[消息 / 命令 / 通知 / 请求]，处理逻辑：[操作]
需要的配置项：[键名]：[用途]（[必填/可选]，默认值：[值]）
其他要求：[额外约束]
```

**适配器：**

```
请基于 ErisPulse 适配器开发规范，生成一个 [适配器名称] 适配器的完整代码。

平台信息：[名称]，通信协议：[WebSocket / WebHook / HTTP 轮询]，API 文档：[地址]
事件转换：平台事件 [类型] → OneBot12 映射 [关系]
需要实现的发送方法：[Text / Image / Voice ...]
配置项：[键名]：[用途]（[必填/可选]）
```

## MCP 服务器

ErisPulse 提供一个文档检索 MCP Server，让 AI 编码助手（支持 MCP 的均可）在你写代码时直接检索、查阅 ErisPulse 官方文档。

接入方式有两种：**本地进程（推荐）**或**官方在线端点**。工具集一致：

| 工具 | 参数 | 说明 |
|------|------|------|
| **`search_docs`** | `query` (必填), `top_k?=5`, `lang?=zh-CN` | BM25 关键词检索，可一次传多个关键词 |
| **`read_document`** | `doc_path` (必填), `lang?=zh-CN` | 读取单篇文档完整 Markdown |
| **`list_documents`** | `lang?=zh-CN` | 列出当前语言下所有文档标题、路径、分类 |
| **`list_languages`** | — | 列出文档支持的所有语言及文档数量 |

支持语言：`zh-CN` / `en` / `zh-TW` / `ja` / `ru`。检索技巧：用**多个关键词**而不是整句，例如 `命令注册 事件监听` 比 `怎么注册一个命令` 更好。

### 方式一：本地进程（推荐）

安装后直接本地启动：

```bash
npm i -g @erisdev/mcp-server   # 全局安装 → 出现 epsdk-mcp 命令
epsdk-mcp --server               # 启动 MCP 服务；首次运行自动拉取文档到 ~/.cache/erispulse-mcp/docs
```

不全局安装也可通过 `npx` 直跑（免装）：

```bash
npx @erisdev/mcp-server --server
```

有本地文档目录时指定它（不联网）：

```bash
ERISPULSE_DOCS_DIR=/path/to/erispulse/docs epsdk-mcp --server
```

在 MCP 客户端中按 **stdio 传输**配置，标准键值（`command` + `args` 指向上面的启动方式；具体配置位置与格式见各客户端自己的 MCP 接入文档）：

```json
{
  "command": "epsdk-mcp",
  "args": ["--server"]
}
```

或

```json
{
  "command": "npx",
  "args": ["@erisdev/mcp-server", "--server"]
}
```

### 方式二：官方在线端点

不想本地起进程时，连官方托管的 [`mcp.erisdev.com`](https://mcp.erisdev.com/)。MCP 客户端按 **HTTP 传输**配置：

```json
{
  "url": "https://mcp.erisdev.com/"
}
```

服务默认公开、无需 Token，有 IP 限流（每 IP 每分钟 60 次）。官方端点可随时停用，**生产工作流建议用方式一（本地进程）或自托管**。

## 常见问题

**生成的代码不符合预期？**
检查是否提供了完整文档；在需求中补充更多细节（输入输出示例、边界条件）；让 AI 分步生成（先骨架再补功能）；参考 [examples/](../../examples/) 目录示例作为补充上下文。

**MCP 接入后 AI 没调用 `search_docs`？**
确认客户端加载了该 server（**重启客户端后可看到工具已生效**）；部分客户端需要在 prompt 里显式提示「使用 ErisPulse 文档工具查证 API」。

## 下一步

- [模块开发入门](../developer-guide/modules/getting-started.md) -- 手动开发模块的完整教程
- [适配器开发入门](../developer-guide/adapters/getting-started.md) -- 手动开发适配器的完整教程
- [示例代码](../../examples/) -- 参考已有的模块和适配器实现
- [模块构建器](https://www.erisdev.com/builder.html) -- 浏览器内的可视化 AI 模块生成器
