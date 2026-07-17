# CLI 命令参考

ErisPulse 命令行工具（`epsdk`）提供项目管理和包管理功能。

> **提示**：所有命令均可通过 `epsdk <命令> --help` 查看详细的参数说明。

---

## 包管理命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | 安装模块/适配器 |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | 卸载模块/适配器 |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 升级指定模块或全部 |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | 更新 SDK 本身 |

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

---

## 信息查询命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | 列出已安装的组件 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | 列出远程可用的组件 |

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

## 运行控制命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | 运行指定脚本或 SDK |

### run

运行 ErisPulse 项目脚本或直接启动 SDK。支持热重载模式。

**别名：** `r`

**参数：**

| 参数 | 说明 |
|------|------|
| `[script]` | 要运行的脚本文件，不指定则运行 SDK |
| `--reload` | 启用热重载模式，监控文件变化自动重启 |

**示例：**

```bash
# 直接运行 SDK
epsdk run

# 运行指定脚本文件
epsdk run main.py

# 热重载模式运行（文件变更自动重启）
epsdk run main.py --reload

# SDK 热重载模式
epsdk run --reload
```

---

## 项目管理命令

| 命令 | 别名 | 参数 | 说明 |
|------|------|------|------|
| `init` | — | `[--project-name/-n <name>] [--quick/-q] [--force/-f] [--here] [--no-uv]` | 初始化 ErisPulse 项目 |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | 创建模块/适配器脚手架 |

### init

初始化一个新的 ErisPulse 项目。支持交互式与快速模式。

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `--project-name` | `-n` | 项目名称 |
| `--quick` | `-q` | 快速模式，跳过交互式向导 |
| `--force` | `-f` | 强制覆盖现有配置文件 |
| `--here` | | 在当前目录初始化，不创建子目录 |
| `--no-uv` | | 使用 pip 代替 uv |

**示例：**

```bash
# 交互式初始化
epsdk init

# 快速初始化
epsdk init -q -n my_bot

# 强制覆盖已有配置
epsdk init -f

# 在当前目录初始化
epsdk init --here -n my_bot
```

### create

创建 ErisPulse 模块或适配器的脚手架项目。

**参数：**

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `{module,adapter}` | | 要创建的类型：`module` 或 `adapter` |
| `--name` | `-n` | 项目名称（PascalCase） |
| `--description` | `-d` | 项目描述 |
| `--author` | `-a` | 作者名称 |
| `--email` | `-e` | 作者邮箱 |
| `--homepage` | | 项目主页 URL |
| `--output` | `-o` | 输出目录（默认当前目录） |
| `--force` | `-f` | 强制覆盖已存在的目录 |

**示例：**

```bash
# 交互式创建（引导选择类型和填写信息）
epsdk create

# 直接创建 Module 项目
epsdk create module -n MyModule

# 直接创建 Adapter 项目
epsdk create adapter -n MyAdapter

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
| `--verbose` | `-v` | 显示详细输出 |

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
