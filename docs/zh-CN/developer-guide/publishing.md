# 发布与模块商店指南

将你开发的模块或适配器发布到 ErisPulse 模块商店，让其他用户可以方便地发现和安装。

## 模块商店概述

ErisPulse 模块商店是一个集中式的模块注册表，用户可以通过 CLI 工具浏览、搜索和安装社区贡献的模块、适配器。

### 浏览与发现

```bash
# 列出远程可用的所有包
epsdk list-remote

# 只查看模块
epsdk list-remote -t modules

# 只查看适配器
epsdk list-remote -t adapters

# 强制刷新远程包列表
epsdk list-remote -r
```

你也可以访问 [ErisPulse 官网](https://www.erisdev.com/#market) 在线浏览模块商店。

### 支持的提交类型

| 类型 | 说明 | Entry-point 组 |
|------|------|----------------|
| 模块 (Module) | 扩展机器人功能、实现业务逻辑 | `erispulse.module` |
| 适配器 (Adapter) | 连接新的消息平台 | `erispulse.adapter` |

## 发布流程

整个发布流程分为四个步骤：准备项目 → 发布到 PyPI → 提交到模块商店 → 审核上线。

### Step 1: 准备项目

确保你的项目包含以下文件：

```
MyModule/
├── pyproject.toml      # 项目配置（必须）
├── README.md           # 项目说明（必须）
├── LICENSE             # 开源许可证（推荐）
└── MyModule/
    ├── __init__.py     # 包入口
    └── ...
```

### Step 2: 配置 pyproject.toml

根据你要发布的类型，正确配置 `entry-points`：

#### 模块

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "模块功能描述"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### 适配器

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "适配器功能描述"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **注意**：包名建议以 `ErisPulse-` 开头，便于用户识别。Entry-point 的键名（如 `"MyModule"`）将作为模块在 SDK 中的访问名称。

### Step 3: 发布到 PyPI

```bash
# 安装构建工具
pip install build twine

# 构建分发包
python -m build

# 发布到 PyPI
python -m twine upload dist/*
```

发布成功后，确认你的包可以通过 `pip install` 安装：

```bash
pip install ErisPulse-MyModule
```

### Step 4: 提交到 ErisPulse 模块商店

在确认包已发布到 PyPI 后，前往 [ErisPulse-ModuleRepo](https://github.com/ErisPulse/ErisPulse-ModuleRepo/issues/new?template=module_submission.md) 提交申请。

填写以下信息：

#### 提交类型

选择你要提交的类型：
- 模块 (Module)
- 适配器 (Adapter)

#### 基本信息

| 字段 | 说明 | 示例 |
|------|------|------|
| **名称** | 模块/适配器名称 | Weather |
| **描述** | 简短功能描述 | 天气查询模块，支持全球城市 |
| **作者** | 你的名字或 GitHub 用户名 | MyName |
| **仓库地址** | 代码仓库 URL | https://github.com/MyName/MyModule |

#### 技术信息

| 字段 | 说明 |
|------|------|
| **最低 SDK 版本要求** | 如 `>=2.0.0`（如适用） |
| **依赖项** | 除 ErisPulse 外的额外依赖（如适用） |

#### 标签

用逗号分隔，帮助用户搜索发现你的模块。例如：`天气, 查询, 工具`

#### 检查清单

提交前请确认：
- 代码遵循 ErisPulse 开发规范
- 包含适当的文档（README.md）
- 包含测试用例（如适用）
- 已在 PyPI 发布

### Step 5: 审核与上线

提交后，维护者会审核你的申请。审核要点：

1. 包可以在 PyPI 上正常安装
2. Entry-point 配置正确，能被 SDK 正确发现
3. 功能与描述一致
4. 不存在安全问题或恶意代码
5. 不与已有模块严重冲突

审核通过后，你的模块会自动出现在模块商店中。

## 更新已发布模块

当你更新模块版本时：

1. 更新 `pyproject.toml` 中的 `version`
2. 重新构建并上传到 PyPI：
   ```bash
   python -m build
   python -m twine upload dist/*
   ```
3. 模块商店会自动同步 PyPI 上的最新版本信息

用户可以通过以下命令升级：

```bash
epsdk upgrade MyModule
```

## 开发模式测试

在正式发布前，你可以使用可编辑模式在本地测试：

```bash
# 以可编辑模式安装
epsdk install -e /path/to/MyModule

# 或使用 pip
pip install -e /path/to/MyModule
```

## 常见问题

### Q: 包名必须以 `ErisPulse-` 开头吗？

不强制，但强烈推荐。这有助于用户在 PyPI 上识别 ErisPulse 生态的包。

### Q: 一个包可以注册多个模块吗？

可以。在 `entry-points` 中配置多个键值对即可：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Q: 如何指定最低 SDK 版本要求？

在 `pyproject.toml` 的 `dependencies` 中设置：

```toml
dependencies = [
    "ErisPulse>=2.0.0",
]
```

模块商店会检查版本兼容性，防止用户安装不兼容的模块。

### Q: 审核需要多长时间？

通常在 1-3 个工作日内完成。你可以在 Issue 中查看审核进度。
