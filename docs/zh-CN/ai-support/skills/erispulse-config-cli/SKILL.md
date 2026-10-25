---
name: erispulse-config-cli
description: "适用于：配置声明式 schema、排查配置问题、使用 epsdk 命令行与部署。覆盖场景：- 连接参数变更后需重启框架生效；连接池创建瞬时失败会自动指数退避重试。忘记某个 `epsdk` 命令的参数、想把组件管理写进脚本，或要控制 run / stop / restart 行为时查阅。日常只用 `init` / `install` / `run` 的话，记住一条就够：`epsdk <命令> --help` 随时可查参数说明，不需要通读本文。需要挑一种安装方式（pip / uv / Docker / ErisPulse-App 客户端），或安装失败要排查时读。只想最快跑起来，[5 分钟快速开始](../quick-start.md) 已覆盖最简流程，。机器人要长期挂着跑时——Docker 部署、systemd / Supervisor 进程守护、反向代理与 SSL、备份与升级都在这里。本地开发调试阶段。"
---

# ErisPulse 配置系统与 CLI 工具链

本技能由 ErisPulse 文档自动构建（generate-skills.py）。
仓库：https://github.com/ErisPulse/ErisPulse
各节末尾标注了来源文档路径，需要最新内容请以仓库 docs/zh-CN/ 为准。

## 配置系统

> 来源: `docs/zh-CN/user-guide/configuration.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/user-guide/configuration.md）

# 配置文件说明

> [!NOTE]
> **L1 核心必读**——首页"阅读路径"中的五篇核心文档之一，模块开发必备。

> 这篇讲框架自身的配置文件 `config/config.toml`：每个配置节管什么、哪些支持热更新、如何用环境变量覆盖。第三方模块的配置项请参考模块自己的文档。

ErisPulse 使用 TOML 格式的配置文件 `config/config.toml` 来管理项目配置。

## 配置文件位置

配置文件位于项目根目录的 `config/` 文件夹中：

```
project/
├── config/
│   └── config.toml
├── main.py
```

### 多实例提示与锁文件

框架启动时会在项目根的运行状态目录 **`.erispulse/`** 下创建 `config.lock` 锁文件并持有到进程退出（用于检测多实例共享配置目录；2.10 及以前位于 `config/` 目录的 `.erispulse_config.lock` 会在升级后首次启动时自动清除）。如果日志出现「检测到配置文件可能正被另一个 ErisPulse 实例同时使用」的告警，说明有**两个以上的 ErisPulse 进程在写同一份配置**（典型场景：多个容器挂载了同一个宿主机 `config/` 目录）——并发写入会互相覆盖，请为每个实例使用独立的配置目录。

### 敏感配置不入库

配置文件含令牌（token / API key）等敏感信息：框架初始化与 `epsdk init` 会自动在 `config/` 目录生成 `.gitignore`（内容仅一行 `*`——**目录内全部文件不入版本库，忽略文件自身也在排除范围内**）；已存在的 `.gitignore` 不会被覆盖。`.erispulse/` 运行状态目录（实例锁、CLI 运行状态文件）同属机器本地状态，项目模板的 `.gitignore` 已默认忽略。

## 配置加载错误处理

框架在加载 `config.toml` 时会区分三种错误状态，并给出**可操作的诊断信息**，而不是静默回退到默认配置：

| 错误状态 | 触发条件 | 框架行为 |
|---------|---------|---------|
| 文件缺失 | `config.toml` 不存在 | 正常首次启动，静默使用空配置（不报警告） |
| TOML 语法错误 | 文件存在但格式非法（如少了引号、括号未闭合） | 输出**出错行号/列号与原因**，并**保留上次有效配置继续运行**（本次文件修改不生效） |
| 权限/其他错误 | 无读权限、IO 错误等 | 输出**明确原因**，并**保留上次有效配置继续运行** |

> **注意"上次有效配置"≠ 默认配置**：文件损坏时框架沿用**本次启动前最后一份解析成功的配置**（运行中热更新改坏文件则沿用旧值），而不是把所有配置项重置为出厂默认。故障处置时不要假设"配置已被重置"。

例如，当你不慎把配置写成了 `port = 8000`（少了引号的字符串）时，日志会输出类似：

```
[ERROR] [Config] 配置文件 config/config.toml 语法错误（第 3 行 第 1 列）: ...
[WARNING] [Config] 配置文件读取失败。继续使用上次有效配置运行，本次文件修改未生效——请修复后重新加载或重启
```

这样你可以在**默认 INFO 级别**下立刻定位问题，而不会困惑"为什么我改的配置没生效"。

> **运行中改坏配置文件？** 如果你在机器人运行期间手动编辑 `config.toml` 引入了语法错误，框架在下次写入（合并配置）时会输出「配置文件已损坏（语法错误，第 X 行），无法合并写入——请先修复配置文件后重启」，而不是令人困惑的「写入失败」。待写入的配置项会被保留，不会丢失。

## 注释保留与最小化落盘

config.toml 中的**注释与键顺序在框架写入后完整保留**：无论是代码 `setConfig()`、
CLI 配置向导保存还是适配器/模块首次生成配置模板，框架都只改动涉及的键，
你写的注释、整理的顺序不会被抹掉或重排（基于 tomlclass 无损 TOML 引擎，
未触碰的内容逐字节保真，文件原有的 CRLF/LF 行尾风格也不会被改变）。

框架对落盘内容保持克制：

- **框架默认配置不自动落盘**：`gc`、`scope`、`transcript` 等内置默认值仅驻内存，
  config.toml 只包含你显式设置的键，保持最小化。完整可配置项参考项目内的
  `config/config.full.example`，按需复制到 config.toml 修改即可（未配置项一律走内置默认值，行为不变）
- **`config.full.example` 自动维护**：无论是否执行过 `epsdk init`，只要启动框架
  （`epsdk run` / `main.py`），都会在 `config/config.full.example` 缺失时自动生成
  完整配置参考；文件首行为框架自维护标记，生成器内容更新（如新增配置项、新装
  组件）时启动会刷新一次，删除/改动首行即转为手动接管、框架不再覆盖
- **适配器/模块配置模板**：首次初始化时以带注释的模板落盘（字段描述即注释）；
  声明为 `example` 标志的字段不落盘，仅记录在 config.full.example 供参考
- **声明式注释回读**：配置文件里的注释本身就是文档——`ep doctor` 与配置校验
  失败提示会引用该字段在文件中的注释原文（即使你手动改过注释，提示跟随文件
  现状），报错时无需再翻文档查找字段含义

## 环境变量覆盖

框架支持用环境变量**覆盖** `ErisPulse.*` 配置项（适合 Docker / 容器化 / CI 部署，无需修改 `config.toml`）。

命名规则：把点分路径 `ErisPulse.<section>.<key>` 改为全大写、`.` 替换为 `_`，并加上 `ERISPULSE_` 前缀：

| 配置项 | 环境变量 | 示例值 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

行为说明：
- **优先级最高**：环境变量覆盖「配置文件」与「默认值」，按原值类型自动转换（`bool` / `int` / `float` / 逗号分隔的 `list` / 字符串）
- **不持久化**：覆盖只在运行期生效，不会写回 `config.toml`
- **支持热更新**：运行中修改环境变量后，配合配置监听的重载即可生效

```bash
# Docker 部署示例：不修改 config.toml，直接覆盖端口
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` 这类框架配置走 `get_server_config()` 等 API 读取，均受环境变量覆盖影响。

### 模块配置的环境变量绑定（2.9.0+）

模块自己的声明式配置（`ConfigClass`）支持字段级环境变量绑定——在 `field(metadata=...)` 中声明 `env`：

```python
@dataclass
class MyConfig(BaseConfig):
    api_key: str = field(default="", metadata={
        "description": "API 密钥",
        "env": "MYMODULE_API_KEY",   # 环境变量绑定
    })
    retries: int = field(default=3, metadata={"env": "MYMODULE_RETRIES"})
```

行为说明：

- **优先级**：环境变量 > `config.toml` > 声明默认值（配置文件热更新后同样保持此优先级）
- **类型转换**：环境变量值按字段注解自动转换——`str` 原样、`int` / `float` / `bool`（`true` / `1` / `yes` / `on`）自动转换、`list` / `dict` 走 JSON 解析；转换失败时忽略该覆盖（回退配置文件 / 默认值）并输出告警
- **声明一处、处处生效**：配置读取、热更新、校验使用同一管道；配置面板 Schema 会标注 `env` 名，`config.toml` 模板注释也会提示可用的环境变量（模板不写入环境变量的实际值，避免泄露）
- **完全兼容**：未声明 `env` 的字段行为不变；直接实例化 ConfigClass（不经框架配置管道）不受环境变量影响

```bash
# Docker 部署示例：不修改 config.toml，直接注入模块密钥
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **配置类 vs 模型字段怎么选？** 配置类管"模块怎么运转"（行为参数、热更新），
> ORM 的 `Field()` 管"用户产生了什么数据"（数据库表、查询）。两者共享同一套
> 约束词表与校验器引擎；对照表见
> [数据模型层 · 两种声明何时用哪个](../developer-guide/orm.md#两种声明何时用哪个)。

## 配置热更新

从 2.7.0 起，框架对配置热更新做了**系统化支持**。外部修改 `config.toml` 后（后台 watcher 每 5 秒检测一次），或代码调用 `setConfig()` 后，各组件自动响应：

| 组件 | 支持热更新的配置 | 行为 |
|------|----------------|------|
| **日志 Logger** | `logger.level` / `log_files` / `log_dir`（含分段参数）/ `memory_limit` / `format` / `exclude_levels` | 自动重新应用（带变更检测） |
| **命令系统 CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 下一条消息即生效 |
| **适配器并发** | `framework.handler_max_concurrency` | 失效缓存信号量，按新值重建 |
| **主动 GC** | `framework.proactive_gc_*` | 配置变更即时重启 GC 任务，支持运行时调整/禁用/重新启用 |
| **主人系统 Master** | `master.users` | 每次 `is_master()` 检查实时读取，无需重启 |
| **模块/适配器配置** | 各自的配置项 | 触发 `on_config_update(old, new)` 回调 |

**需重启的配置**（无法安全热切换，变更时会输出告警"需重启进程后生效"）：

| 配置 | 原因 |
|------|------|
| `router.cors.*` / `router.security.*` | 中间件在服务启动时写入 FastAPI，运行时无法安全热切换 |
| `storage.use_global_db` | SQLite 文件句柄已在运行时打开，切换路径不安全 |

> **中途编辑保存出错？** 若编辑 `config.toml` 时出现瞬时语法错误，框架会**保留上次有效配置**并输出诊断日志，不会把空配置广播给各组件（避免 `on_config_update` 收到空值误回退默认）。

### 热更新链路内部拆解

「改了配置，各组件怎么知道的？」——背后是一条检测 → 重载 → 广播的链路：

```mermaid
flowchart TD
    A["外部编辑 config.toml"] --> B{"谁先发现？"}
    B -->|"后台 watcher 线程<br/>每 5 秒轮询 mtime"| C["_check_file_change 判定变更"]
    B -->|"代码读取配置时<br/>缓存超 60 秒"| C
    C --> D["_load_config 重新解析 TOML"]
    D --> E{"解析成功？"}
    E -->|"否（语法错误）"| F["保留上次有效配置<br/>不广播，打诊断日志"]
    E -->|"是"| G["lifecycle.emit config.updated<br/>携带 old_config / new_config"]
    G --> H["各组件监听者响应<br/>（logger / scope / 命令 / GC ...）"]
```

**两条检测路径**（取其一即可，均能兜底）：

| 路径 | 机制 | 触发时机 |
|------|------|---------|
| 后台 watcher | daemon 线程 `config-watcher` 每 **5 秒** `wait` 轮询文件 `mtime` | 外部改文件后最多 5 秒内 |
| 惰性检测 | 任何 `getConfig()` 读取时，若缓存超过 **60 秒**则先查文件 | 下次读配置时 |

> **框架不会误伤自己**：`setConfig()` 写盘时会记录「自身写入的 mtime」，watcher 对比时把它排除，只把**外部编辑**视为变更。

**两类配置变更事件：**

| 事件 | 触发者 | 数据 | 典型场景 |
|------|--------|------|---------|
| `config.set` | 代码 / Dashboard 调 `setConfig()` | `{key, old_value, new_value}` | 单键写入（模板生成、状态记录、运行时改配置） |
| `config.updated` | 外部编辑后 watcher/惰性检测捕获 | `{old_config, new_config, config_file}` | 手改 `config.toml` |

> `setConfig()` 默认**延迟 5 秒落盘**（合并多次写入），`immediate=True` 立即写。watcher 检测到外部修改后只更新内存缓存，**不会**把外部改动回写文件。

**自动响应方清单**（两类事件通常会都订阅，响应内容一致）：

| 组件 | 监听 | 响应 |
|------|------|------|
| Logger | `config.set` + `config.updated` | 级别/文件/目录分段/内存上限/格式/屏蔽等级重新应用（带变更检测，无变化不动） |
| Scope | `config.updated` | 作用域绑定缓存重建 |
| 命令系统 | `config.updated` | 前缀/大小写/空格前缀/must_at_bot 解析参数刷新，下一条消息生效 |
| 适配器并发 | `config.set` + `config.updated` | `handler_max_concurrency` 失效重建信号量 |
| 主动 GC | `config.set` + `config.updated` | `proactive_gc_*` 即时重启 GC 后台任务 |
| 适配器 | 路由到 `on_config_update` | 各适配器 `on_config_update(old, new)` 回调 |
| 模块 | 路由到 `on_config_update` | 各模块 `on_config_update(old, new)` 回调 |
| 存储 | `config.updated` | `use_global_db` 变更**仅告警**（需重启） |
| 路由 | `config.updated` | `cors.*` / `security.*` 变更**仅告警**（需重启） |


## 配置读取与删除 API

### getAllConfig：全量配置快照

替代直接读取私有 `_cache`（外部读私有属性不受版本兼容保护）：

```python
config = sdk.config.getAllConfig()     # 深拷贝快照，原地修改不影响框架状态
config["ErisPulse"]["server"]["port"]
```

视图口径与 `getConfig` 一致：未落盘的 `setConfig` / `delete` 均已反映，
与延迟刷盘后的文件内容严格一致。

### delConfig：删除配置键

`setConfig(key, None)` 只是置空、键仍保留在文件中；`delConfig` 会把键从文件中**移除**：

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # 延迟写入
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # 立即落盘
```

- 支持点分路径；键不存在时返回 `False`
- 落盘走注释保留路径，文件其余内容与顺序不受影响
- 复用 `config.set` 事件广播（`new_value=None`）：适配器 / 模块的
  `on_config_update` 等现有监听方零改动即可感知删除

## 完整配置示例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users 支持两种写法（二选一）：
#   全局主人（所有平台生效）：users = ["123456", "789012"]
#   按平台指定主人：users = { yunhu = ["123456"], telegram = ["789012"] }
users = {}

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
log_dir = ""
log_rotation = "size"
log_max_size_mb = 10
log_backup_count = 5
log_rotation_when = "midnight"
memory_limit = 1000
exclude_levels = []

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
backend = "sqlite"
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
auto_start = true
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
# 容器 / 无文件挂载场景可内联 PEM 内容（优先级高于 certfile/keyfile 路径）
# ssl_cert = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
# ssl_key = """-----BEGIN PRIVATE KEY-----
# ...
# -----END PRIVATE KEY-----"""
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 监听地址，0.0.0.0 表示所有接口 |
| port | integer | 8000 | 监听端口号 |
| auto_start | boolean | true | 是否在 `sdk.init()` 时自动启动路由服务器。设为 `false` 可跳过路由服务器启动（纯事件/无 WebUI 场景） |
| ssl_certfile | string | 空 | SSL 证书文件路径 |
| ssl_keyfile | string | 空 | SSL 私钥文件路径 |
| ssl_cert | string | 空 | **内联 PEM 证书内容**（非路径）。与 `ssl_key` 成对使用时优先于 `ssl_certfile`/`ssl_keyfile`；框架临时落盘构建 SSL 上下文后立即删除临时文件 |
| ssl_key | string | 空 | **内联 PEM 私钥内容**（非路径），语义同上 |

> **端口占用不是致命错误**：启动时若检测到 `port` 已被占用，框架会跳过路由服务器启动并告警，**适配器与模块照常运行**（仅 HTTP/WS/SSE 路由与 WebUI 不可用）。排查"机器人能跑但 WebUI 打不开"时先确认端口。

## 主人系统配置

主人系统用于识别「框架主人」账号（如 Bot 管理员）。`master.users` 支持两种写法：

```toml
[ErisPulse.master]
# 写法一：全局主人（所有平台生效）
users = ["123456", "789012"]

# 写法二：按平台指定主人（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| users | array / object | 空 | 主人账号列表。`list` 形式为全局主人（所有平台生效）；`dict` 形式按平台指定（键为平台名，值为该平台的主人账号列表） |

代码中通过 `master.is_master(event)` 或 `master.is_master(platform, user_id)` 检查，每次调用实时读取配置（支持热更新，无需重启）：

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("主人你好")
```

### 判定链与运行时增删

主人判定链为 **配置主人 → 运行时记录 → provider 链**：

```python
from ErisPulse.Core import master

master.is_master(event)                      # 从事件判定
master.is_master("yunhu", "123")             # 显式判定
master.add("yunhu", "123")                   # 运行时添加（默认持久化；persist=False 仅内存）
master.remove("yunhu", "123")                # 移除（默认持久化）
master.list()                                # 汇总：{"global": [...], "<platform>": [...]}
```

### 自定义身份源（provider）

除配置外，还可注册自定义身份源：`fn(platform, user_id) -> bool`，
内置身份源（配置 + 运行时记录）未命中时依次尝试，任一 provider 放行即认定为主人。
适合对接适配器管理员接口、数据库角色等外部身份体系。

注册入口 `master.provider` 支持装饰器 / 函数式两种写法，
注销统一走被注册函数上的 `fn.unregister()`：

```python
from ErisPulse.Core import master

# 写法一：装饰器（常驻身份源，推荐）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自定义判定逻辑

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 不再需要时注销

# 写法二：函数式（模块加载期注册 / 卸载期注销）
fn = master.provider(admin_provider)
fn.unregister()
```

> provider 异常会被捕获并跳过，不阻断身份判定链。
> 绑定实例方法无法挂载 `unregister`，需要注册/注销配对的场景请用**模块级函数**。

### 用户优先：主人生效范围由用户最终决定

命令的 `master=True` 只是**开发者默认**：用户可在
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false`
覆写收紧或放开（见[统一事件覆写配置](#统一事件覆写配置eventoverrides)，用户显式配置即生效）。

## 日志配置

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # 显式日志文件列表（与 log_dir 互斥，优先级更高）
log_dir = ""                  # 日志目录（设置后自动分段轮转）
log_rotation = "size"         # 分段方式: "size" / "date" / "none"
log_max_size_mb = 10          # size 模式单文件上限（MB）
log_backup_count = 5          # 保留的历史日志文件数
log_rotation_when = "midnight"  # date 模式轮转周期: S/M/H/D/midnight
memory_limit = 1000             # 单模块内存日志条数上限（0 = 关闭内存日志副本）
total_memory_limit = 5000       # 全部模块内存日志总条数上限（0 = 不限）
exclude_levels = ["EVENT"]
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| level | string | INFO | 日志级别：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE 为最低级别，输出框架内部详细调试信息） |
| format | string | rich | 日志输出格式：`rich`（彩色，默认）、`plain`（纯文本无颜色，适合日志采集/管道重定向）、`json`（JSON 结构化，适合 ELK 等） |
| log_files | array | 空 | 日志输出文件列表（显式路径，不分段） |
| log_dir | string | 空 | 日志输出目录（自动创建）。设置后写入目录内 `erispulse.log` 并按 `log_rotation` 自动分段；与 `log_files` 互斥，`log_files` 优先 |
| log_rotation | string | size | 分段方式：`size`（按大小）/ `date`（按时间）/ `none`（不分段） |
| log_max_size_mb | float | 10 | size 模式单文件大小上限（MB），超过后轮转为 `.1`/`.2` 备份 |
| log_backup_count | integer | 5 | 保留的历史日志文件数，超出的最旧备份自动删除 |
| log_rotation_when | string | midnight | date 模式轮转周期：`S`/`M`/`H`/`D`/`midnight`（默认每天零点） |
| memory_limit | integer | 1000 | 单模块内存中保存的日志条数；`0` 表示关闭内存日志副本（不再写入内存，已有记录保留） |
| total_memory_limit | integer | 5000 | 全部模块内存日志总条数上限；`0` 表示不限。超限时按轮转策略淘汰最旧记录（优先削减条数最多的模块队列），与单模块 `memory_limit` 独立生效 |
| exclude_levels | array | 空 | 屏蔽指定日志等级。被屏蔽等级的日志**完全丢弃**（不写内存、不推送给 Dashboard 等订阅器、不打印、不写文件）。支持热更新 |

也可在代码中动态切换：

```python
from ErisPulse.Core import logger

# 按大小分段：单文件 10MB，保留 5 份
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 按时间分段：每天零点轮转，保留 7 份
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` 及分段相关配置需要 ErisPulse **2.8.0+**。

> **隐私保护**：消息收发内容以 **EVENT 等级**（数值 21）记录。设置 `exclude_levels = ["EVENT"]` 即可让后台（如 Dashboard 日志面板）无法看到各群/私聊的消息内容，同时不影响其它等级日志。

> [!NOTE]
> `exclude_levels` 本特性需要 ErisPulse **2.8.0+**。

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
| handler_max_concurrency | integer | 64 | 事件处理器最大并发 Task 数，设大提高吞吐但增加内存占用 |
| handler_queue_max_pending | integer | 4096 | 事件洪峰入队背压：单平台待处理 handler Task 数上限，超限时新事件的处理器 Task 直接丢弃并记 WARNING（丢弃计数可在 troubleshoot 排查中查看）；`0` 表示不限 |
| offline_bot_expiry | integer | 3600 | 离线 Bot 记录自动过期时间（秒），0 表示不过期 |
| plugins_dir | string / list | "plugins" | 本地插件文件夹（相对项目根目录）；新增/删除/修改插件文件会被热重载 watcher 自动发现 |
| watch_ignore_dirs | list | 内置清单 | 热重载文件监控忽略的目录名（`.venv`/`.git`/`__pycache__` 等）；非空列表**整体替换**内置清单，`[]` 表示不忽略任何目录 |
| watch_include_plugin_dirs | boolean | true | `epsdk run --reload` 是否把插件目录交给插件热重载 watcher 精确处理（单模块重载），并从全量监控中排除 |

### 主动 GC 配置

SDK 初始化完成后启动主动 GC 后台任务，周期性执行 Python GC 与内部资源回收（离线 Bot 清理等）。全部参数均支持热更新，变更时即时重启任务。

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回收间隔（秒），支持小数。0 表示禁用主动 GC |
| proactive_gc_generation | integer | 0 | 常规轮次回收分代（0/1/2，钳制到 0..2）。注意 `gc.collect(2)` 等价于全量回收，默认 0 保持轻量；深度回收由 `proactive_gc_full_every` 周期性触发 |
| proactive_gc_full_every | integer | 20 | 每 N 轮做一次全量回收，0 表示禁用周期性全量。全量回收受 `proactive_gc_memory_growth_mb` 门限约束 |
| proactive_gc_memory_growth_mb | integer | 32 | 全量回收的内存增长门限（MB）：对比上次全量后的内存基线（优先 tracemalloc，其次 RSS），仅当增长达到此值才执行全量回收。0 表示不设门限 |
| proactive_gc_idle_only | boolean | false | 开启后，事件洪峰（存在未完成的 pending handler）时本轮跳过 Python GC，避免停顿与消息处理竞争；内部资源回收不受影响 |
| proactive_gc_gen0_min | integer | 500 | 常规轮次触发回收的 gen0 垃圾量下限：`gc.get_count()[0]` 低于此值直接跳过（空转轮次近乎零开销）。0 表示始终回收 |

> **2.7.1 变更**：默认 `proactive_gc_generation` 由 `2` 调整为 `0`，默认 `proactive_gc_full_every` 由 `0` 调整为 `20`。此前 `generation=2` 意味着每轮都做最重的全量回收；新默认在保持回收覆盖的同时显著降低空转开销。显式配置的旧值仍按字面语义生效。

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

#### 与 CLI 的联动

`epsdk run` 的启动前自检（配置文件可解析性、组件必填配置完整性）默认跟随本配置：非 0 时检查失败即拒绝启动，0 时仅警告继续。也可以不改配置临时切换：`epsdk run --strict` 本次将自检与严格级别同时开启（级别只升不降，经 `ERISPULSE_FRAMEWORK_STRICT_MODE` 环境变量传导到运行进程），`--no-strict` 本次临时压到宽松并仅警告。

## 存储配置

2.8.0 起存储引擎支持三种异步后端，**API 完全一致、配置一键切换**：

| 后端 | 驱动 | 安装 | 特点 |
|------|------|------|------|
| SQLite（默认） | aiosqlite | 开箱即用 | 零配置、单文件、WAL 并发 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 已有 MySQL 基础设施、多实例共享 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | 事务能力强、高并发 |

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite"（默认）/ "mysql" / "postgres"
use_global_db = false     # 仅 SQLite：使用包内全局数据库 data/config.db

[ErisPulse.storage.mysql]      # backend = "mysql" 时生效
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
# charset = "utf8mb4"
# pool_min = 1
# pool_max = 10

[ErisPulse.storage.postgres]   # backend = "postgres" 时生效
host = "127.0.0.1"
port = 5432
user = "erispulse"
password = ""
database = "erispulse"
# pool_min = 1
# pool_max = 10
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| backend | string | sqlite | 存储后端：`sqlite` / `mysql` / `postgres`，切换零代码改动 |
| use_global_db | boolean | false | 仅 SQLite：是否使用包内全局数据库而非项目独立数据库 |
| storage.mysql.* | table | 见上 | MySQL 连接参数（host / port / user / password / database / charset / pool） |
| storage.postgres.* | table | 见上 | PostgreSQL 连接参数（host / port / user / password / database / pool） |

也支持环境变量覆盖（Docker / 12-factor）：`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`。

> [!TIP]
> - 连接参数变更后需重启框架生效；连接池创建瞬时失败会自动指数退避重试
> - 切换后端前可用验证脚本自检：`python tests/devs/test_storage_backend_verify.py --backend mysql`
> - 事务 / 方言差异 / 自定义后端等完整说明见[存储后端](../advanced/storage-backends.md)

## 事件配置

### 命令配置

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
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

## 会话收件箱配置（transcript）

```toml
[ErisPulse.transcript]
enabled = true
max_per_session = 50
ttl_hours = 168.0
self_echo = "bot"
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| enabled | boolean | true | 是否自动记录入站/出站消息（关闭后停止写入，历史仍可查询） |
| max_per_session | int | 50 | 单会话保留条数（0 = 关闭该会话裁剪） |
| ttl_hours | float | 168.0 | 全局保留时长（小时，0 = 永不清理） |
| self_echo | string | bot | 入站 bot 回声（`self.user_id == user_id`，如 OneBot `report-self-message`）处理：`bot` = 记为 bot 并标记 `meta.self_echo`；`skip` = 不记录；`user` = 记为 user（旧行为） |

> 保留策略的风险与审计见 [会话收件箱](../advanced/transcript.md)；归因字段（`sender` / `meta`）与出站归属（`meta.module`）同见该文档。

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

## 作用域配置（scope）

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

作用域声明"**什么范围内生效**"——某平台 / Bot / 会话里哪些模块可用（① 模块维度）、
某用户 / 群 / Bot / 适配器的事件收不收（② 身份维度）、
模块能发起哪些出站调用（③ 出站维度）：

```toml
[ErisPulse.scope]
default_allow = true        # 全局兜底（false = 隐式拒绝严格模式；不影响出站维度）
cache_size = 1024           # LRU 缓存大小

# ① 模块维度（优先级：会话 > Bot > 平台；条目支持精确 / glob / re: 正则）
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# 子级绑定写 merge = true 时与低优先级逐条目并集（默认整体覆盖）
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② 身份维度（优先级：用户 > 会话 > Bot > 适配器；每级只写 allow 或 deny 之一）
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # 该平台所有事件在入口丢弃
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # 用户键支持 glob / re: 正则
deny = ["u_bad", "spam_*"]

# ③ 出站维度（默认全允许；规则为内联表，条目支持精确 / glob / re: 正则）
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # 全禁发送
api = { allow = ["get_*"] }               # 仅允许查询类标准 API
request = { deny = true }                 # 禁止处理请求
```

| 配置项 | 类型 | 说明 |
|---------|------|------|
| `scope.default_allow` | boolean | 全局兜底：模块/身份未命中规则的放行/拒绝（`true`） |
| `scope.cache_size` | integer | LRU 缓存大小（默认 1024） |
| `scope.platforms / bots / sessions` | table | ① 模块三级绑定：`{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② 身份四级绑定：`{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<动作>` | table | ③ 出站规则：`{allow=[...], deny=true|[...]}`（动作取 send / api / request） |

> 详解与运行时 API（维度化 `sdk.scope.set_module()` / `set_identity()` /
> `set_action()`，判定 `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`，
> 以及字典式兜底 `get()` / `set()` / `delete()`）详见[作用域（scope）](../advanced/scope.md)。

## 统一事件覆写配置（event.overrides）

统一覆写系统：按**事件类型**覆写任意模块处理器的行为，不改模块代码。
OneBot12 标准类型（meta / message / notice / request）与扩展类型（command）
各自拥有专属的可覆写参数：

```toml
[ErisPulse.event.overrides]

# message：文本触发条件（与代码内条件 AND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta：detail_type 白名单（条目支持精确 / glob / re: 正则）
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command（扩展类型）：实现参数覆写（用户优先；禁用统一走 acl deny）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # 覆写为仅框架主人（false 则放开开发者的主人限制）
hidden = true               # 帮助列表中隐藏
aliases = ["rs"]            # 生效别名

# acl（command 专属）：命令用户黑白名单（命令名支持 glob / re: 正则，精确键优先）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # 用户标识 "platform:user_id"
deny = ["onebot11:u_bad"]

# ACL 兜底：未配置 ACL 的命令放行（true）/ 严格拒绝（false）
acl_default_allow = true
```

| 配置项 | 类型 | 说明 |
|---------|------|------|
| `event.overrides.message.<module>` | table | 文本条件：`{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | 模块级参数覆写（`hidden = true` 等标量） |
| `event.overrides.command.<module>.<command>` | table | 命令级覆写（命令级优先） |
| `event.overrides.acl.<命令名>` | table | 用户黑白名单：`{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACL 兜底：未配置 ACL 的命令放行（`true`）/ 严格拒绝（`false`） |

> 运行时 API（`from ErisPulse.Core.Event import overrides` 后按类型子命名空间调用
> `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` 等，
> 或经 `sdk.Event.overrides` 访问）
> 见 [事件处理入门 · 事件覆写](../getting-started/event-handling.md#事件覆写不改模块代码覆写任意事件类型的行为)。

## CLI 参考

> 来源: `docs/zh-CN/user-guide/cli-reference.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/user-guide/cli-reference.md）

# CLI 命令参考

> [!TIP]
> **什么时候需要读这篇**：忘记某个 `epsdk` 命令的参数、想把组件管理写进脚本，或要控制 run / stop / restart 行为时查阅。日常只用 `init` / `install` / `run` 的话，记住一条就够：`epsdk <命令> --help` 随时可查参数说明，不需要通读本文。

`epsdk` 是 ErisPulse 的命令行工具：初始化项目、安装 / 升级模块与适配器、交互式配置组件、运行与停止机器人、诊断环境，都在这一条命令下。

> **提示**：`epsdk`（不带命令）的主帮助按类别分组展示：**项目**（init / create / run）、**组件管理**（install / uninstall / upgrade / list / list-remote / types）、**配置与诊断**（config / doctor / i18n）、**其他**（self-update / version）。

---

## 包管理命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | 安装模块/适配器 |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | 卸载模块/适配器 |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 升级指定模块或全部 |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | 更新 SDK 本身 |

## 诊断命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose] [--fix]` | 诊断环境并输出健康报告；`--fix` 尝试自动修复 |

### install

安装 ErisPulse 模块或适配器包。若不指定包名则进入交互式安装界面。

**别名：** `i`, `add`

> **uv 项目联动**（2.11.1+）：在 uv 管理的项目内（存在 `uv.lock` 或 `[tool.uv]`），
> `install` / `upgrade` / `uninstall` 自动改走 `uv add` / `uv remove`——依赖同步写入
> `pyproject.toml` 与 `uv.lock`，`uv sync` 不再清掉 epsdk 装的组件；失败自动回退
> uv pip / pip 通道。`--user` 等 uv 不支持的参数直接走 pip。目标环境解析顺序：
> `ERISPULSE_PYTHON` → `UV_PROJECT_ENVIRONMENT` → 项目 `.venv` → `UV_PYTHON` →
> `VIRTUAL_ENV` → 当前解释器（`epsdk doctor` 可查看完整决策链）。

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `[package]...` | | 要安装的包名称，可指定多个 |
| `--upgrade` | `-U` | 安装时升级到最新版本 |
| `--pre` | | 允许安装预发布版本 |
| `--editable` | `-e` | 以可编辑模式安装（需指定路径） |
| `--user` | | 安装到用户 site-packages 目录 |
| `--no-deps` | | 不安装依赖 |
| `--target` | `-t` | 安装到指定目录 |
| `--index-url` | | 指定 PyPI 镜像源地址 |
| `--extra-index-url` | | 额外 PyPI 镜像源地址（可多次指定） |
| `--no-cache-dir` | | 禁用缓存 |
| `--requirement` | `-r` | 从 requirements 文件安装 |
| `--constraint` | `-c` | 从约束文件安装 |
| `--force-reinstall` | | 强制重新安装 |
| `--ignore-installed` | | 忽略已安装的包 |
| `--compile` | | 安装后编译 .pyc 文件 |
| `--no-compile` | | 安装后不编译 .pyc 文件 |
| `--prefix` | | 安装到指定前缀目录 |
| `--src` | | 可编辑安装时使用的源码目录 |
| `--config-settings` | | 传递给构建后端的配置（可多次指定） |
| `--no-binary` | | 限制不使用二进制包（格式如 `:all:`） |
| `--only-binary` | | 限制仅使用二进制包（格式如 `:all:`） |
| `--prefer-binary` | | 优先选择二进制包 |
| `--build-isolation` | | 启用构建隔离 |
| `--no-build-isolation` | | 禁用构建隔离 |
| `--upgrade-strategy` | | 升级策略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | 允许修改系统包管理器管理的 Python 包 |
| `--no-uv` | | 使用 pip 代替 uv |

**示例：**

```bash
# 安装单个模块
epsdk install Weather

# 安装多个模块
epsdk install Yunhu Weather

# 从镜像源安装并升级
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 可编辑模式安装（开发模式）
epsdk install -e ./my-adapter
```

### uninstall

卸载已安装的 ErisPulse 模块或适配器包。若不指定包名则进入交互式卸载界面。

**别名：** `rm`, `remove`

**参数：**

| 参数 | 说明 |
|------|------|
| `<package>...` | 要卸载的包名称，可指定多个 |
| `--no-uv` | 使用 pip 代替 uv |

**示例：**

```bash
# 卸载单个模块
epsdk uninstall Weather

# 卸载多个模块
epsdk uninstall Yunhu Weather
```

### upgrade

升级已安装的 ErisPulse 组件。不指定包名则交互式升级全部。

**别名：** `up`

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `[package]...` | | 要升级的包名称，可指定多个 |
| `--force` | `-f` | 强制升级，跳过确认 |
| `--pre` | | 允许升级到预发布版本 |
| `--no-uv` | | 使用 pip 代替 uv |

**示例：**

```bash
# 升级所有包
epsdk upgrade

# 升级指定包
epsdk upgrade Weather

# 强制升级（跳过确认）
epsdk upgrade -f
```

### self-update

更新 ErisPulse SDK 本身到最新版本。

**别名：** `su`, `update`

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `[version]` | | 指定要更新的目标版本号 |
| `--pre` | | 允许更新到预发布版本 |
| `--force` | `-f` | 强制更新，跳过确认 |
| `--no-uv` | | 使用 pip 代替 uv |

**示例：**

```bash
# 更新到最新稳定版
epsdk self-update

# 更新到指定版本
epsdk self-update 1.2.3

# 允许预发布版本
epsdk self-update --pre

# 强制更新
epsdk self-update -f
```

> [!NOTE]
> 通过 `uv tool install ErisPulse` 安装时，本命令自动改走 `uv tool upgrade ErisPulse`（指定版本时为 `uv tool install ErisPulse==<版本> --force`），直接 pip 升级工具环境会被 uv 的清单还原抹掉。
> Windows 下更新在新控制台窗口中进行：当前 CLI 需先退出以解除工具环境文件占用，窗口提示完成后重新打开终端即可。

---

## 信息查询命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | 列出已安装的组件 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | 列出远程可用的组件 |
| `version` | `ver` | | 显示 SDK 与 Python 版本信息（与 `-V` 等效） |

### list

列出已安装的 ErisPulse 模块和适配器。

**别名：** `l`, `ls`

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `--type` | `-t` | 指定类型：`modules`、`adapters`、`all`（默认） |
| `--outdated` | `-o` | 仅显示可升级的包 |

**示例：**

```bash
# 列出所有已安装的组件
epsdk list

# 只列出模块
epsdk list -t modules

# 只列出适配器
epsdk list -t adapters

# 只显示可升级的包
epsdk list -o
```

### list-remote

列出远程仓库中可用的 ErisPulse 模块和适配器。

**别名：** `lsr`

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `--type` | `-t` | 指定类型：`modules`、`adapters`、`all`（默认） |
| `--refresh` | `-r` | 强制刷新远端包列表缓存 |

**示例：**

```bash
# 列出所有远程可用组件
epsdk list-remote

# 只列出远程模块
epsdk list-remote -t modules

# 强制刷新缓存后列出
epsdk list-remote -r
```

---

## 配置命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l] [--json]` | 交互式配置适配器/模块的声明式配置项 |

### config

交互式填写适配器/模块的声明式配置项。向导由适配器/模块声明的配置类（`ConfigClass` / `AccountConfigClass`）驱动，自动生成表单并校验，无需手写 config.toml。

适配器额外支持多账户（bot 账户）管理：添加/编辑/删除账户，以及启用/禁用开关。

**别名：** `cfg`, `conf`

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `[name]` | | 目标名称（适配器平台名或模块名），留空进入交互选择 |
| `--list` | `-l` | 仅列出所有目标的配置状态，不进入向导 |
| `--json` | | 以 JSON 输出全部目标及其配置状态（供 CI / 脚本消费），不进入向导 |

**示例：**

```bash
# 查看所有适配器/模块的配置状态
epsdk config --list

# 以 JSON 输出配置状态（CI / 脚本消费）
epsdk config --json

# 交互选择目标进行配置
epsdk config

# 直接配置指定适配器
epsdk config yunhu

# 直接配置指定模块
epsdk config MyModule
```

**说明：**

- 配置状态分为四档：`已就绪`（校验通过）、`待完善`（必填项缺失或校验失败）、`未配置`（从未生成）、`无配置`（目标未声明配置类）
- 字段值带来源标注：已有配置显示 `（当前:值）`，未配置时显示 schema 默认值 `（默认:值）`；直接回车即保留该值
- 密钥类字段（声明 `secret`）输入时不回显，回车保留已设置的值
- 交互选择模式下，单个向导结束后会回到选择菜单（状态已刷新），可连续配置多个目标，留空退出
- 全局表单校验失败且放弃重新填写时，本次向导中止且不写入任何配置（避免产生"已启用但配置不完整"的半成品状态）
- 保存后立即写入 `config/config.toml`，Dashboard 与运行中的 SDK 均可见；运行中的适配器如需应用新账户配置，重启进程即可
- `epsdk install`（交互式安装）与 `epsdk init` 安装适配器成功后，若检测到配置声明会自动引导进入本向导；命令行直接指定包名安装时仅打印配置提示

---

## 运行控制命令

> [!TIP]
> `epsdk run` 会自动检测并使用项目目录下的 `.venv` 虚拟环境运行机器人
> （也可通过 `ERISPULSE_PYTHON` 环境变量显式指定解释器）。`epsdk install` /
> `uninstall` / `upgrade` / `list` 同样作用于项目虚拟环境。

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload] [--strict/--no-strict]` | 运行指定脚本或 SDK |
| `stop` | — | `[--force] [--pid PID]` | 停止正在运行的实例（由 `epsdk run` 启动） |
| `restart` | — | `[--force] [--pid PID]` | 重启正在运行的实例（停止后按原参数重新启动） |

### run

运行 ErisPulse 项目脚本或直接启动 SDK。支持热重载模式。

**别名：** `r`

**参数：**

| 参数 | 说明 |
|------|------|
| `[script]` | 要运行的脚本文件，不指定则运行 SDK |
| `--reload` | 启用热重载模式：监控文件变化自动触发组件级代码热重载（无需整进程重启）；默认忽略 `.venv`/`.git` 等目录（可经 `ErisPulse.framework.watch_ignore_dirs` 配置），插件目录交给插件热重载 watcher 精确处理 |
| `--strict` / `--no-strict` | 临时开启 / 关闭严格模式（仅本次生效，不写入配置）；缺省跟随 `ErisPulse.framework.strict_mode` |

**示例：**

```bash
# 直接运行 SDK
epsdk run

# 运行指定脚本文件
epsdk run main.py

# 热重载模式运行（文件变更自动触发代码级热重载）
epsdk run main.py --reload

# SDK 热重载模式
epsdk run --reload

# 临时严格模式：启动前自检失败即退出，框架严格级别本次提升为至少 1
epsdk run main.py --strict

# 临时宽松模式（配置里开了 strict_mode 但本次想先跑起来）
epsdk run main.py --no-strict
```

**启动前自检：** `run` 启动前会快速检查 `config/config.toml` 可解析性与已安装组件的必填配置完整性，严格性默认跟随 `ErisPulse.framework.strict_mode`（非 0 时检查失败即退出，0 时仅警告继续）。配置文件缺失视为正常首次启动，仅提示不判失败。`--strict` 临时开启：预检失败即退出，同时框架严格级别本次提升为至少 1（跳过不合规组件，经 `ERISPULSE_FRAMEWORK_STRICT_MODE` 环境变量传导到运行进程，不写入配置文件）；`--no-strict` 反之临时压到宽松。自检自身异常时自动跳过，不含网络探测，不会阻塞启动。

> **`--reload` 的监督结构**（2.11.1 起）：`epsdk run --reload` 以「监督进程 + 重载 worker 子进程」运行。保存 `.py` 文件触发的热重载全部在 worker 内完成（互斥串行、风暴合并）；模块侧语法错误会被整体预检拒绝，旧实例继续服务。`sdk.hard_restart()` 时 worker 以退出码 42 退出，监督进程展示原因后自动重拉全新 worker——升级框架本体后新代码即刻生效。

### stop

停止正在运行的 ErisPulse 实例（由 `epsdk run` 启动、并在同一项目目录下执行）。
`run` 启动时会把监督进程 PID、当前框架子进程 PID 与原始启动命令写入
`.erispulse/runtime.json`，`stop` 据此定位实例。

**停止顺序：** POSIX 下先向监督进程发 SIGINT（与 Ctrl+C 同款优雅收尾路径——
finally 链自动终止框架子进程），超时逐级升级 SIGTERM / SIGKILL；Windows 无
进程信号语义，先终止框架子进程再终止监督进程（避免监督者把强杀误判为崩溃
重新拉起）。

**参数：**

| 参数 | 说明 |
|------|------|
| `--force` | 跳过优雅停止，直接强制终止 |
| `--pid PID` | 直接指定目标进程 PID（覆盖运行状态文件，用于非标启动方式） |

**示例：**

```bash
# 停止当前项目的运行实例
epsdk stop

# 强制终止
epsdk stop --force
```

### restart

重启正在运行的 ErisPulse 实例：按 `stop` 的语义停止后，以状态文件中记录的
**原始启动命令**重新启动（前台接管当前终端，新实例会写入新的运行状态文件）。

**参数：** 同 `stop`（`--force` / `--pid PID`）。

**示例：**

```bash
# 优雅重启（pip 升级适配器/模块后让代码生效；运行中模块也可用
# sdk.reload_module / sdk.adapter.reload 代码级热重载，无需重启）
epsdk restart
```

> [!NOTE]
> `python main.py` 等绕过 `epsdk run` 的启动方式不会写运行状态文件——此类
> 进程请用系统工具管理，或用 `epsdk stop --pid <PID>` 指定 PID。

---

## 项目管理命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--adapter/-a <name>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | 初始化 ErisPulse 项目 |
| `create` | — | `{module,adapter,pack} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f] [--local]` | 创建模块/适配器脚手架；`pack` 将本地插件转换为可发布项目 |

### init

初始化一个新的 ErisPulse 项目。支持交互式与快速模式，2.8.4 起生成 `pyproject.toml`（依赖清单）、可选创建项目 `.venv` 虚拟环境并安装框架与适配器，并支持**指定任意目录**。

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `[path]` | | 目标路径（可包含父目录，如 `../apps/mybot`；纯名称等价 `--project-name`） |
| `--project-name` | `-n` | 项目名称 |
| `--path` | | 项目父目录（与 `-n` 组合指定创建位置） |
| `--adapter` | `-a` | 预选要安装的适配器（可重复传参或逗号分隔），传入时跳过适配器问询与选择 |
| `--quick` | `-q` | 快速模式，跳过交互式向导（默认创建 `.venv` 并安装依赖） |
| `--force` | `-f` | 强制覆盖现有配置文件 |
| `--here` | | 在当前目录初始化，不创建子目录 |
| `--no-uv` | | 使用 pip 代替 uv |
| `--no-venv` | | 跳过虚拟环境创建与依赖安装 |

**示例：**

```bash
# 交互式初始化
epsdk init

# 快速初始化（当前目录下创建 my_bot/，含 pyproject.toml + .venv）
epsdk init -q -n my_bot

# 快速初始化并预装适配器（免交互，脚本 / CI 场景）
epsdk init -q -n my_bot --adapter yunhu,telegram

# 指定任意目录初始化（../apps/mybot）
epsdk init ../apps/mybot

# 组合父目录与项目名
epsdk init -n my_bot --path ../apps

# 强制覆盖已有配置
epsdk init -f

# 在当前目录初始化
epsdk init --here -n my_bot

# 只生成项目结构，不创建虚拟环境
epsdk init --no-venv -n my_bot
```

init 产物：`main.py`、`pyproject.toml`（依赖清单）、`config/config.toml` + `config.full.example`、`config/ssl/`、`logs/`、`.gitignore`、`README.md`；选择创建虚拟环境时额外生成 `.venv` 并将 `erispulse` 与所选适配器安装其中。

> [!NOTE]
> `.gitignore` 为分组式模板：Python 字节码与构建产物、虚拟环境与 `.env`、工具缓存、编辑器与系统文件，并**整体排除 `config/` 与 `logs/` 运行时目录**——`config.toml` 含适配器令牌等敏感信息，不建议入库；共享配置骨架请使用 `config.full.example`。

> [!WARNING]
> **不要使用 `uv run epsdk run` 运行机器人**。`uv run` 在无 `pyproject.toml` 的目录执行时创建**一次性隔离环境**——在其中通过 `epsdk install` 安装的适配器不会持久化。请在项目目录内使用 `epsdk run`（自动使用项目 `.venv`），或先激活虚拟环境再运行。

### create

创建 ErisPulse 模块或适配器的脚手架项目；`pack` 子命令将本地插件（`plugins/` 目录）转换为可发布的标准项目。

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `{module,adapter,pack}` | | 要创建的类型：`module` / `adapter` / `pack`（插件转项目）|
| `--name` | `-n` | 项目名称（PascalCase） |
| `--description` | `-d` | 项目描述 |
| `--author` | `-a` | 作者名称 |
| `--email` | `-e` | 作者邮箱 |
| `--homepage` | | 项目主页 URL |
| `--output` | `-o` | 输出目录（默认当前目录） |
| `--force` | `-f` | 强制覆盖已存在的目录 |
| `--local` | | 创建本地插件（`module` / `adapter` 可用）：生成 `plugins/<name>/` 包结构，免打包安装 |

**示例：**

```bash
# 交互式创建（引导选择类型和填写信息）
epsdk create

# 直接创建 Module 项目
epsdk create module -n MyModule

# 创建本地插件（放入项目 plugins/ 目录，启动时自动发现）
epsdk create module -n MyModule --local

# 创建本地适配器插件（同上，免打包开发）
epsdk create adapter -n MyAdapter --local

# 直接创建 Adapter 项目
epsdk create adapter -n MyAdapter

# 将本地插件转换为可发布项目（交互选择插件 → 补全元信息 → 生成标准项目）
epsdk create pack

# 完整参数
epsdk create module -n MyModule -d "模块描述" -a "作者" -e "mail@example.com"

# 指定输出目录
epsdk create module -n MyModule -o ./projects

# 强制覆盖已有目录
epsdk create module -n MyModule -f
```

---

## 语言命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | 查看或切换 CLI 显示语言 |

### i18n

查看当前 CLI 语言、列出支持的语言、切换显示语言。若不指定参数则进入交互式选择界面。

**别名：** `language`, `lang`

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `[lang]` | | 要切换的语言代码（如 `zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | 列出所有支持的语言 |

**示例：**

```bash
# 交互式选择语言
epsdk i18n

# 切换到英文
epsdk i18n en

# 切换到日文
epsdk i18n ja

# 列出所有支持的语言
epsdk i18n --list
```

---

## 类型存根命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | 生成类型存根文件以启用 IDE 补全 |

### types

扫描已安装的 ErisPulse 模块和适配器，为它们生成 `.pyi` 类型存根文件，从而在 IDE 中获得准确的代码补全与类型检查支持。

**别名：** `t`, `stub`

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `--output` | `-o` | 输出路径（默认当前目录下的 `ep-stubs/`） |
| `--force` | | 强制覆盖已存在的存根文件 |
| `--adapters-only` | | 仅生成适配器的类型存根 |
| `--modules-only` | | 仅生成模块的类型存根 |

> **注意：** `--adapters-only` 与 `--modules-only` 互斥，同时指定时后者生效。

**示例：**

```bash
# 为所有已安装的模块和适配器生成类型存根
epsdk types

# 仅生成适配器存根
epsdk types --adapters-only

# 输出到指定目录
epsdk types -o ./typings

# 强制覆盖已有文件
epsdk types --force
```

---

## 全局参数

以下参数适用于所有命令：

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `--help` | `-h` | 显示帮助信息 |
| `--version` | `-V` | 显示版本信息 |
| `--verbose` | `-v` | 显示详细输出（可叠加 `-vv`/`-vvv`） |
| `--no-color` | | 禁用彩色输出（适合 CI / 日志采集） |
| `--no-banner` | | 跳过启动 Banner（脚本化调用 / CI 场景；非交互终端与 `ERISPULSE_NO_BANNER=1` 下自动静默） |
| `--yes` | `-y` | 自动确认所有交互提示（非交互式运行） |

---

## 环境诊断

### doctor

> [!NOTE]
> 本命令需要 ErisPulse **2.7.0+**。

诊断当前 CLI 运行环境，输出健康报告。用于排查"为什么装不上 / 连不上"类问题。

| 参数 | 说明 |
|------|------|
| `--verbose` | 显示详细诊断信息 |
| `--fix` | 诊断后尝试自动修复可修复的问题 |

**检查项**：
- **Python**：解释器版本与路径
- **安装后端**：使用 `uv` 还是 `pip`
- **目标解释器**：包实际安装到的目标 Python 环境
- **配置文件**：`config/config.toml` 是否存在
- **组件配置**：已安装组件的声明式配置完整性（"装好了跑不起来"多因必填项缺失）
- **配置污染**（2.11.1+）：扫描历史升级遗留的残留键（旧版运行时绑定的影子状态键、游离配置节），检出即提示
- **PyPI 连通性**：能否访问 PyPI（并显示发现的组件数）
- **系统代理**：是否检测到代理

**自动修复（`--fix`）**：
- `config.toml` 缺失 → 按当前语言生成初始配置文件（与 `init` 建项同源）
- 组件配置"待完善" → 逐个拉起交互式配置向导补全必填项（非交互环境提示改用 `epsdk config <名称>`）
- 配置污染残留键 → 列明来源并经确认后删除（tomlclass 无损路径，注释与顺序保真）
- Python 版本过低、PyPI 无法访问等需人工介入的问题 → 仅输出行动建议

```bash
# 运行环境诊断
epsdk doctor

# 使用别名
epsdk diag

# 诊断并尝试自动修复
epsdk doctor --fix
```

---

## 交互式安装

运行 `epsdk install` 不指定包名时进入交互式安装：

```bash
epsdk install
```

交互界面提供：
1. 适配器选择
2. 模块选择
3. 自定义安装

## 常见用法

### 安装模块

```bash
# 安装单个模块
epsdk install Weather

# 安装多个模块
epsdk install Yunhu Weather

# 升级模块
epsdk install Weather -U
```

### 列出组件

```bash
# 列出所有组件
epsdk list

# 只列出适配器
epsdk list -t adapters

# 只列出可升级的组件
epsdk list -o

# 查看远程可用组件
epsdk list-remote
```

### 卸载组件

```bash
# 卸载单个组件
epsdk uninstall Weather

# 卸载多个组件
epsdk uninstall Yunhu Weather
```

### 配置组件

```bash
# 查看配置状态
epsdk config --list

# 交互选择目标配置
epsdk config

# 配置指定适配器
epsdk config yunhu
```

### 升级组件

```bash
# 升级所有组件
epsdk upgrade

# 升级指定组件
epsdk upgrade Weather

# 强制升级
epsdk upgrade -f
```

### 运行项目

```bash
# 普通运行
epsdk run main.py

# 热重载模式
epsdk run main.py --reload
```

### 切换语言

```bash
# 交互式选择语言
epsdk i18n

# 直接切换到英文
epsdk i18n en

# 列出支持的语言
epsdk i18n --list
```

### 生成类型存根

```bash
# 生成所有类型存根
epsdk types

# 仅生成模块类型存根
epsdk types --modules-only
```

### 初始化项目

```bash
# 交互式初始化
epsdk init

# 快速初始化
epsdk init -q -n my_bot
```

### 创建脚手架

```bash
# 交互式创建（引导选择类型和填写信息）
epsdk create

# 直接创建 Module 项目
epsdk create module -n MyModule

# 直接创建 Adapter 项目
epsdk create adapter -n MyAdapter

# 完整参数
epsdk create module -n MyModule -d "模块描述" -a "作者" -e "mail@example.com"

# 强制覆盖已有目录
epsdk create module -n MyModule -f
```

## 安装

> 来源: `docs/zh-CN/user-guide/installation.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/user-guide/installation.md）

# 安装参考

> [!TIP]
> **什么时候需要读这篇**：需要挑一种安装方式（pip / uv / Docker / ErisPulse-App 客户端），或安装失败要排查时读。只想最快跑起来，[5 分钟快速开始](../quick-start.md) 已覆盖最简流程，不需要则跳过。

## 系统要求

- Python 3.10 – 3.14（3.14t 自由线程 / 无 GIL 构建为实验性支持，框架以实验性 CI 冒烟持续监测，不作正式承诺）
- pip 或 uv（推荐）
- 足够的磁盘空间（至少 100MB）

## 安装方式

### 方式一：使用 pip 安装

```bash
# 安装 ErisPulse
pip install ErisPulse

# 升级到最新版本
pip install ErisPulse --upgrade
```

### 方式二：使用 uv 安装（推荐）

uv 是一个更快的 Python 工具链，推荐用于开发环境。

#### 安装 uv

```bash
# 使用 pip 安装 uv
pip install uv

# 验证安装
uv --version
```

#### 创建虚拟环境

```bash
# 创建项目目录
mkdir my_bot && cd my_bot

# 安装 Python 3.12
uv python install 3.12

# 创建虚拟环境
uv venv
```

#### 激活虚拟环境

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 安装 ErisPulse

```bash
# 安装 ErisPulse
uv pip install ErisPulse --upgrade
```

### 方式三：使用 uv tool 安装（全局 CLI，推荐）

只想把 `epsdk` 当全局命令行工具使用时，`uv tool install` 是最干净的方式——
epsdk 运行在独立的工具环境中，不污染任何项目环境：

```bash
# 安装（epsdk 立即可用，无需激活任何虚拟环境）
uv tool install ErisPulse

# 升级（或直接使用 epsdk self-update，会自动走此通道）
uv tool upgrade ErisPulse
```

> [!NOTE]
> 工具环境里的 epsdk 在项目目录内运行时会自动感知项目 `.venv`：
> `epsdk install` 将组件安装进项目环境、`epsdk run` 使用项目环境运行机器人，
> 框架本体仍由工具环境提供，两边互不干扰。
>
> 一键安装脚本（`get.erisdev.com/install.sh` / `install.ps1`）的菜单中
> 同样提供「全局 CLI 安装（uv tool）」方式，会自动安装 uv 并引导完成。

## 项目初始化与模块安装

安装完成后，项目初始化、模块安装、运行的完整流程见 [5 分钟快速开始](../quick-start.md)。

### 方式四：使用 ErisPulse-App 客户端（免终端）

不想装 Python 环境？[ErisPulse-App](../ecosystem/app.md) 是官方全平台客户端
（Android / Windows / Linux / macOS），**手机直接运行**，桌面版支持最小化到
系统托盘后台常驻；内置 Python 运行时与 ErisPulse SDK，无需终端与手动配置：

- 从 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 按平台选择下载
  （Android `online`/`offline` APK、Windows `setup.exe`/`zip`、Linux `tar.gz`、macOS `zip`）
- 在 App 内创建并启动实例，通过原生界面管理适配器与模块、浏览模块商店

> 完整说明见 [ErisPulse-App 安装与使用](../ecosystem/app.md)。

## 验证安装

### 检查安装

```bash
# 检查 ErisPulse 版本
epsdk --version
```

### 运行测试

```bash
# 运行项目
epsdk run main.py
```

如果看到类似的输出说明安装成功：

```
[INFO] 正在初始化 ErisPulse...
[INFO] 适配器已加载: Yunhu
[INFO] 模块已加载: MyModule
[INFO] ErisPulse 初始化完成
```

## 常见问题

### 安装失败

1. 检查 Python 版本是否在支持范围内（支持 3.10 – 3.14；3.14t 自由线程 / 无 GIL 构建为实验性支持，不作正式承诺）
2. 尝试使用 `uv pip install ErisPulse` 替代 `pip install`
3. 如果提示权限错误，尝试 `pip install --user ErisPulse` 或使用虚拟环境
4. 如果在企业代理环境下遇到 SSL 证书错误，尝试 `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. 确保网络连接正常，pip 源可访问

### 配置错误

1. 检查 `config.toml` 语法是否正确（TOML 格式对缩进和引号敏感）
2. 确认所有必需的配置项都已填写
3. 查看终端日志获取详细错误信息
4. 使用 `epsdk init` 重新生成配置文件

### 模块安装失败

1. 确认模块名称拼写正确（大小写敏感）
2. 检查网络连接
3. 使用 `epsdk list-remote` 查看可用模块列表
4. 确认模块与你当前 SDK 版本兼容

### Windows PowerShell 执行策略

如果 PowerShell 提示"无法加载文件...因为在此系统上禁止运行脚本"：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debian/Ubuntu 虚拟环境创建失败

如果安装脚本提示「虚拟环境创建失败」，且错误信息包含 `ensurepip is not available`，是因为 Debian/Ubuntu 默认未安装 `python3-venv`（系统 Python 的 `ensurepip` 被禁用）：

```bash
sudo apt install python3.13-venv   # 按实际 Python 版本安装对应包
# 或安装通用元包：
sudo apt install python3-venv
```

安装后重新运行安装脚本即可。新版安装脚本在检测到该问题时会主动询问并尝试自动安装对应系统包；也可以改用 uv（`uv venv` 不依赖 `ensurepip`）。

## 部署

> 来源: `docs/zh-CN/user-guide/deployment.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/user-guide/deployment.md）

# 部署指南

> [!TIP]
> **什么时候需要读这篇**：机器人要长期挂着跑时——Docker 部署、systemd / Supervisor 进程守护、反向代理与 SSL、备份与升级都在这里。本地开发调试阶段不需要则跳过。

机器人开发完只是开始。这篇覆盖把它稳定挂在服务器上所需的三种部署方式（Docker / systemd / Supervisor），以及反向代理、安全加固与备份。

## Docker 部署（推荐）

ErisPulse 提供官方 Docker 镜像，内置 ErisPulse 框架和 Dashboard 管理面板，支持 `linux/amd64` 和 `linux/arm64` 架构。

### 快速启动

```bash
# 拉取镜像
docker pull erispulse/erispulse:latest

# 下载 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 设置 Dashboard 登录令牌并启动
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

启动后访问 `http://localhost:8000/Dashboard`，使用设置的令牌作为密码登录。

### 国内镜像加速

如果 Docker Hub 无法访问，可以使用 GitHub Container Registry 拉取镜像：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

使用 ghcr.io 镜像时，需要修改 `docker-compose.yml` 中的 image：

```yaml
services:
  erispulse:
    image: ghcr.io/erispulse/erispulse:latest
```

### docker-compose.yml

```yaml
services:
  erispulse:
    image: erispulse/erispulse:${ERISPULSE_TAG:-latest}
    container_name: ${CONTAINER_NAME:-erispulse}
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
      # 持久化 Python 包目录
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - LANG=${LANG:-en_US.UTF-8}
      - ERISPULSE_LANG=${ERISPULSE_LANG:-}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    # 优雅停机由框架内信号处理完成（SIGTERM），此处仅控制宽限时长
    stop_grace_period: 30s
    restart: on-failure:5
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

> 以上与仓库根 [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) 保持一致（仓库版本头部另有镜像加速与环境变量说明注释），推荐直接下载使用。

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard 端口映射 |
| `ERISPULSE_TAG` | `latest` | 镜像 tag（如需锁定版本可设为具体版本号） |
| `CONTAINER_NAME` | `erispulse` | 容器名（多实例部署时区分实例） |
| `ERISPULSE_DASHBOARD_TOKEN` | 自动生成 | Dashboard 登录令牌（强烈建议设置） |
| `TZ` | `Asia/Shanghai` | 时区 |
| `LANG` | `en_US.UTF-8` | 系统语言，自动检测启动界面语言 |
| `ERISPULSE_LANG` | 空 | 强制启动界面语言：`zh` / `zh_TW` / `en` / `ja` / `ru`（覆盖 `LANG`） |

### 数据持久化

`./config` 目录挂载了配置文件和数据库，包含：

- `config/config.toml` — 配置文件
- `config/config.db` — SQLite 存储数据库
- `config/.packages` — Python site-packages 持久化卷，保存框架、适配器和已安装模块（首次启动时由入口点从镜像内置备份自动初始化，之后的模块安装与框架热更新均写入此目录）

> **框架升级（含 pre/rc）与镜像自愈**：入口点会在每次容器启动时做核心包完整性自检，
> 损坏时按"用户已安装版本优先"原则修复——持久卷内显式安装/升级的版本
> （如 Dashboard 安装的 pre 版本）会从 PyPI **重装同版本**，绝不静默回退到
> 镜像内置版本。因此 Dashboard 升级框架后，任意次容器重启都应保持目标版本。

## Dashboard 管理面板

ErisPulse Docker 镜像内置 Dashboard 模块，提供 Web 可视化管理界面。

### 功能概览

| 功能 | 说明 |
|------|------|
| 仪表盘 | 系统概览、CPU/内存监控、运行时长、事件统计 |
| 机器人管理 | 查看各平台机器人在线状态和信息 |
| 事件查看 | 实时事件流，支持按类型和平台过滤 |
| 日志查看 | 按模块和级别过滤的日志查看器 |
| 模块管理 | 查看、加载、卸载已安装的模块和适配器 |
| 模块商店 | 浏览远程可用包并一键安装 |
| 配置编辑 | 在线编辑 `config.toml` |
| 存储管理 | 浏览和编辑 Key-Value 存储数据 |
| 备份 | 导出/导入配置和存储数据 |
| 审计日志 | 记录所有管理操作 |

### 通过 Dashboard 安装模块

Dashboard 集成了模块商店功能，你可以：

1. **从商店安装**：浏览远程模块列表，选择需要的模块一键安装
2. **上传本地包**：直接上传 `.whl` 或 `.zip` 文件进行安装，方便测试个人开发的模块

> **模块开发者的快速测试流程**：使用 Docker 部署后，在 Dashboard 中通过「上传本地包」功能直接上传你构建的 `.whl` 文件进行测试，无需手动操作容器。

## 进程监督与硬重启

ErisPulse 的硬重启（`sdk.hard_restart()`）依赖**外部监督者**在进程退出码为 42 时重新拉起进程——SDK 自己不拉起新进程。生产环境务必配置监督者，否则硬重启后进程不会自动恢复：

- Docker：官方 compose 使用 `restart: on-failure:5`——非零退出码即重启（覆盖硬重启的退出码 42），连续 5 次上限防死循环；需要不限次数可自行改为 `unless-stopped`
- systemd：`Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord：将 42 加入可重启退出码
- 纯 Python 自定义监督者：循环 `Popen` + 检测 `returncode == 42`

各监督者的完整配置示例与退出码 42 契约说明见 [启动流程 → 监督者指南](../advanced/startup.md#监督者指南)。

## 健康检查

SDK 内置健康检查端点：

```bash
# 健康检查
curl http://localhost:8000/health
```

官方 docker-compose.yml 已内置以下健康检查；自写 compose 文件时可参考：

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

## 反向代理

如果需要通过 Nginx 等反向代理暴露 Dashboard：

```nginx
server {
    listen 80;
    server_name bot.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket 支持（Dashboard 实时事件流需要）
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL 可使用 Let's Encrypt：

```bash
sudo certbot --nginx -d bot.example.com
```

## 手动部署（pip）

如果不使用 Docker，也可以手动部署。

### 生产环境配置

```toml
# config/config.toml

[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"
log_files = ["app.log"]
memory_limit = 5000

[ErisPulse.framework]
enable_lazy_loading = true
```

### systemd (Linux)

创建 `/etc/systemd/system/erispulse-bot.service`：

```ini
[Unit]
Description=ErisPulse Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/erispulse-bot
ExecStart=/opt/erispulse-bot/venv/bin/epsdk run main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

管理：

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

创建 `/etc/supervisor/conf.d/erispulse-bot.conf`：

```ini
[program:erispulse-bot]
command=/opt/erispulse-bot/venv/bin/python -m ErisPulse run main.py
directory=/opt/erispulse-bot
user=bot
autostart=true
autorestart=true
stderr_logfile=/var/log/erispulse-bot/err.log
stdout_logfile=/var/log/erispulse-bot/out.log
```

### uv tool 分离部署（CLI 与项目环境隔离）

`uv tool install` 将 `epsdk` 安装为**独立的工具环境**，CLI 自身与项目依赖彻底隔离：升级 CLI 不会触碰项目 `.venv`，项目依赖变动也不会影响 CLI。

```bash
# 1. 全局安装 CLI（自动暴露 epsdk / ep 命令）
uv tool install ErisPulse

# 2. 项目内只放机器人依赖（.venv 由 uv 管理）
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # 按需追加适配器

# 3. 用 CLI 运行（自动探测并使用项目 .venv 中的解释器）
epsdk run main.py
```

行为要点：

- `epsdk run` 的目标解释器解析顺序：`ERISPULSE_PYTHON` 环境变量 → 项目 `.venv` → 当前解释器；工具环境本身只承载 CLI，组件（适配器/模块）应装进项目 `.venv`
- `epsdk install` / `uninstall` / `upgrade` / `list` 同样作用于项目 `.venv`，不会污染工具环境
- 升级 CLI：`uv tool upgrade ErisPulse`（或直接 `epsdk self-update`，uv tool 环境下自动改走 `uv tool upgrade`）；升级项目依赖：在项目目录执行 `uv sync` / `uv add`，两者互不影响
- 服务器场景下工具环境由 uv 统一管理（`uv tool list` 查看、`uv tool upgrade --all` 批量升级），无需手工维护全局 pip 包
- 若在无项目的目录用 `uv run epsdk ...` 执行，会落入**一次性隔离环境**（安装的组件不持久化）；服务器上请始终用 `epsdk` 直接调用，或先 `cd` 进项目目录

## 安全建议

1. **设置 Dashboard 令牌**：使用强随机令牌，不要使用默认值
2. **不要暴露端口到公网**：除非使用反向代理 + SSL，否则将 Dashboard 端口限制在内网
3. **保护数据目录**：`config/` 目录包含配置和数据库，设置适当的文件权限
4. **定期更新**：使用 `epsdk self-update` 或拉取最新 Docker 镜像
5. **不要以 root 运行**：手动部署时创建专用用户
6. **使用 Docker 重启策略**：官方 compose 的 `restart: on-failure:5` 已确保异常退出（含硬重启退出码 42）后自动重启

## 多实例部署

运行多个机器人实例时：

1. 每个实例使用独立的项目目录和 `docker-compose.yml`
2. 使用不同的端口号：`ERISPULSE_PORT=8001`
3. 使用不同的容器名：`container_name: erispulse-bot2`

## 更新与维护

### Docker 方式

```bash
# 拉取最新镜像
docker compose pull

# 重启使用新镜像
docker compose up -d
```

### pip 方式

```bash
epsdk self-update
epsdk upgrade
```

### uv tool 方式

```bash
# 升级 CLI 工具环境
uv tool upgrade ErisPulse

# 升级项目依赖（项目目录内执行）
uv sync
```

### 运行时热重载服务器配置

修改监听地址 / 端口 / SSL 证书后无需重启进程，在任意协程中调用 `router.reload()`：

```python
await sdk.router.reload(port=9000)                                # 换端口
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # 热更换证书（证书续期场景）
await sdk.router.reload(host="0.0.0.0", port=9000)                # 缺省参数沿用当前配置
```

- 复用同一 FastAPI 应用，模块注册的 HTTP / WebSocket / SSE 路由全部保留
- 先验证新配置（证书可构建、端口可用）再切换；失败时以旧配置恢复服务并返回 `False`，
  保证返回 `False` = 旧服务保持可用
- 服务器未运行时返回 `False`（首次启动请使用 `sdk.router.start()`）

### 备份

定期备份 `config/` 目录：

```bash
# Docker 部署
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# 或在 Dashboard 中使用「备份」功能导出
```
