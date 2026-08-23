# 模块开发入门

本指南带你从零开始创建一个 ErisPulse 模块。

## 项目结构

一个标准的模块结构：

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py
```

## pyproject.toml 配置

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "模块功能描述"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = []

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

## __init__.py

```python
from .Core import Main
```

## Core.py - 基础模块

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command

class Main(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
    
    @staticmethod
    def get_load_strategy():
        """返回模块加载策略"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[],  # 可选：依赖的其他模块列表
            # 可选：事件驱动懒激活——声明触发器，首个匹配事件/命令到达时自动加载
            # activate_on=[{"command": {"name": "hello", "help": "发送问候"}}],
        )
    
    async def on_load(self, event):
        """模块加载时调用"""
        @command("hello", help="发送问候")
        async def hello_command(event):
            name = event.get_user_nickname() or "朋友"
            await event.reply(f"你好，{name}！")
        
        self.logger.info("模块已加载")
    
    async def on_unload(self, event):
        """模块卸载时调用"""
        self.logger.info("模块已卸载")
```

> **配置读取**：上面的基础示例未使用配置。需要读取配置时，推荐声明嵌套的 `ConfigClass` 并通过 `self.cfg` 实时读取（见 [模块核心概念](core-concepts.md#声明式配置推荐)）。手动调用 `_load_config()` 的旧写法已废弃。

## 测试模块

### 本地测试

```bash
# 在项目目录安装模块
epsdk install ./MyModule

# 运行项目
epsdk run main.py --reload
```

### 测试命令

发送命令测试：

```
/hello
```

## 核心概念

### BaseModule 基类

所有模块必须继承 `BaseModule`，提供以下方法：

| 方法 | 说明 | 必须 |
|------|------|------|
| `__init__(self, sdk)` | 构造函数（框架传入 `sdk` 实例） | 否 |
| `get_load_strategy()` | 返回加载策略 | 否 |
| `get_meta()` | 返回模块介绍元信息（可选） | 否 |
| `on_load(self, event)` | 模块加载时调用 | 是 |
| `on_unload(self, event)` | 模块卸载时调用 | 是 |

### 模块介绍 meta

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

通过 `get_meta()` 声明模块的介绍元信息（这个模块是干什么的、属于哪一类等）。
元信息是模块的**通用介绍数据**，供 help 模块、Dashboard 模块列表、模块商店等各类界面/生态模块消费。

与 `get_load_strategy()` 返回 `ModuleLoadStrategy` 一致，**推荐返回 `ModuleMeta` 配置类实例**（属性键入、IDE 补全），也兼容直接返回 dict：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天气",               # 显示名（默认注册名）
            description="查询城市天气",  # 模块简介
            version="1.0.0",
            author="ErisDev",
            group="工具",               # 功能分组
            tags=["天气", "查询"],
        )
```

兼容写法（dict）：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "天气",
            "description": "查询城市天气",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "工具",
            "tags": ["天气", "查询"],
        }
```

- `module.get_meta("MyModule")` 读取已解析的元信息（类声明 > 注册 info，自动补全该模块的命令名）。
- `module.get_commands_overview()` 聚合「模块 meta + 其注册的命令（别名/分组/帮助）」，按模块组织的命令总览。
- 命令归属模块通过 `cmd_info["owner"]` 获取（注册时由上下文系统自动注入）。

#### meta 字段的 i18n 支持

元信息字段值可用纯字符串，或 i18n 字典 `{"i18n": "key.path", "default": "兜底文本"}`（与配置 `description` 约定一致）。
翻译键通过 `I18nClass` 声明注册，`module.get_meta()` 读取时自动解析为当前语言文本：

```python
class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        meta_description: I18nKey = I18nKey(
            default="Weather lookup",
            zh_CN="查询城市天气",
            en="Weather lookup",
        )

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天气",
            description={"i18n": "MyModule.meta_description", "default": "Weather lookup"},
        )
```

### SDK 对象

通过 `sdk` 对象访问核心功能：

```python
from ErisPulse import sdk

sdk.storage    # 存储系统
sdk.config     # 配置系统
sdk.logger     # 日志系统
sdk.adapter    # 适配器系统
sdk.router     # 路由系统
sdk.lifecycle  # 生命周期系统
```

## 下一步

- [模块核心概念](core-concepts.md) - 深入了解模块架构
- [Event 包装类详解](event-wrapper.md) - 学习 Event 对象
- [模块最佳实践](best-practices.md) - 开发高质量模块