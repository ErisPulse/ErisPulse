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
| `--reload` | 启用热重载模式，监控文件变化自动触发组件级代码热重载（联动热重载系统，无需整进程重启） |
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
- **PyPI 连通性**：能否访问 PyPI（并显示发现的组件数）
- **系统代理**：是否检测到代理

**自动修复（`--fix`）**：
- `config.toml` 缺失 → 按当前语言生成初始配置文件（与 `init` 建项同源）
- 组件配置"待完善" → 逐个拉起交互式配置向导补全必填项（非交互环境提示改用 `epsdk config <名称>`）
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

## 下一步

- **组件装好了要填配置**：用 `epsdk config` 交互式向导，或看 [配置文件说明](configuration.md) 手动编辑
- **代码写完想要 IDE 补全**：跑 `epsdk types`，详见 [类型存根生成](../getting-started/ide-completion.md)
- **机器人跑不起来**：先 `epsdk doctor` 诊断环境（见[环境诊断](#环境诊断)），要长期部署再看 [部署指南](deployment.md)
