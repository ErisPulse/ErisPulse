# 配置文件说明
> 这个文档会介绍框架的配置文件，如果有第三方模块需要配置，请参考模块的文档。

ErisPulse 使用 TOML 格式的配置文件 `config/config.toml` 来管理项目配置。

## 配置文件位置

配置文件位于项目根目录的 `config/` 文件夹中：

```
project/
├── config/
│   └── config.toml
├── main.py
```

## 配置加载错误处理

框架在加载 `config.toml` 时会区分三种错误状态，并给出**可操作的诊断信息**，而不是静默回退到默认配置：

| 错误状态 | 触发条件 | 框架行为 |
|---------|---------|---------|
| 文件缺失 | `config.toml` 不存在 | 正常首次启动，静默使用空配置（不报警告） |
| TOML 语法错误 | 文件存在但格式非法（如少了引号、括号未闭合） | 输出**出错行号/列号与原因**，并提示已回退默认配置 |
| 权限/其他错误 | 无读权限、IO 错误等 | 输出**明确原因**，并提示已回退默认配置 |

例如，当你不慎把配置写成了 `port = 8000`（少了引号的字符串）时，日志会输出类似：

```
[ERROR] [Config] 配置文件 config/config.toml 语法错误（第 3 行 第 1 列）: ...
[WARNING] [Config] 已回退到默认配置，您的自定义设置未生效——请修复后重启
```

这样你可以在**默认 INFO 级别**下立刻定位问题，而不会困惑"为什么我改的配置没生效"。

> **运行中改坏配置文件？** 如果你在机器人运行期间手动编辑 `config.toml` 引入了语法错误，框架在下次写入（合并配置）时会输出「配置文件已损坏（语法错误，第 X 行），无法合并写入——请先修复配置文件后重启」，而不是令人困惑的「写入失败」。待写入的配置项会被保留，不会丢失。

## 完整配置示例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
memory_limit = 1000

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true

[ErisPulse.i18n]
language = "auto"
```

## 服务器配置

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 监听地址，0.0.0.0 表示所有接口 |
| port | integer | 8000 | 监听端口号 |
| ssl_certfile | string | 空 | SSL 证书文件路径 |
| ssl_keyfile | string | 空 | SSL 私钥文件路径 |

## 日志配置

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| level | string | INFO | 日志级别：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE 为最低级别，输出框架内部详细调试信息） |
| format | string | rich | 日志输出格式，默认使用 rich 彩色输出 |
| log_files | array | 空 | 日志输出文件列表 |
| memory_limit | integer | 1000 | 内存中保存的日志条数 |

## 框架配置

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | 是否启用模块懒加载 |
| uninit_timeout | integer | 30 | 优雅关闭的总超时时间（秒），超过后强制终止。0 表示不设超时 |
| strict_mode | integer | 0 | 严格模式级别，见下方「严格模式」说明 |

### 严格模式

严格模式控制模块/适配器在加载阶段不合规或失败时的处理策略。现代模块/适配器都应继承对应的基类（`BaseModule`/`BaseAdapter`），未继承基类的组件会影响框架的上下文系统与兜底清理，可能导致资源泄露。

> **2.5.2 变更**：默认级别从 `1`（跳过）调整为 `0`（宽松），以减少新用户初次使用时遇到的加载问题。未继承基类的组件将以 WARNING 提示并尝试加载，而非直接拒绝。如需恢复旧行为，请显式设置 `strict_mode = 1`。

| 级别 | 名称 | 行为 |
|------|------|------|
| 0 | 宽松（默认） | 违规仅警告，未继承基类的组件仍会尝试加载（兼容旧组件） |
| 1 | 严格-跳过 | 拒绝未继承基类的组件并跳过，其余正常启动 |
| 2 | 严格-致命 | 收集所有违规后统一报告并中止整个启动 |

各级别下，「加载/注册/初始化阶段报错」这类组件自身崩溃始终会被跳过；区别在于：

- **0 → 1**：唯一行为变化是「未继承基类」从「仍加载」变为「跳过」。
- **1 → 2**：所有违规（未继承基类、加载失败、注册失败、初始化失败等）升级为致命，会在启动检查点收集后一次性输出违规清单并中止。

#### 豁免清单

如果某些组件确实暂时无法迁移（例如依赖的旧模块），可以将其加入豁免清单，被列名的组件即使不合规也会按宽松模式对待，继续加载：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> 当某个组件被严格模式拒绝时，日志会明确提示如何恢复加载（加入豁免清单或调低级别）。

## 存储配置

```toml
[ErisPulse.storage]
use_global_db = false
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| use_global_db | boolean | false | 是否使用全局数据库（包内）而非项目数据库。`true` 时所有项目共享 ErisPulse 包内的 SQLite 数据库；`false`（默认）时每个项目使用 `config/` 目录下独立的数据库 |

## 事件配置

### 命令配置

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| prefix | string | / | 命令前缀 |
| case_sensitive | boolean | true | 是否区分大小写（`/Help` 与 `/help` 是否为不同命令） |
| allow_space_prefix | boolean | false | 是否允许空格作为前缀 |
| must_at_bot | boolean | false | 是否必须@机器人才能触发命令（私聊不受限制） |

### 消息配置

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 是否忽略机器人自己的消息 |

## 国际化配置

```toml
[ErisPulse.i18n]
language = "auto"
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| language | string | auto | 框架内置文本的显示语言。设为 `auto` 自动检测系统语言，也可设为具体代码：`zh-CN`、`zh-TW`、`en`、`ja`、`ru` |

## 模块配置

每个模块可以在配置文件中定义自己的配置：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

在模块中读取和写入配置：

```python
from ErisPulse import sdk

# 读取配置
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 运行时写入配置（延迟保存）
sdk.config.setConfig("MyModule.timeout", 60)

# 立即保存到文件
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` 默认采用延迟写入（约每 5 秒批量保存到文件），设置 `immediate=True` 可立即持久化。配置变更会触发 `config.set` 生命周期事件。

## 下一步

- [CLI 命令参考](cli-reference.md) - 了解所有命令行命令
- [开发者指南](../developer-guide/) - 学习开发自定义模块