# 开发者指南

本指南帮助你开发自定义模块和适配器，扩展 ErisPulse 的功能。

## 内容列表

### 模块开发

1. [模块开发入门](modules/getting-started.md) - 创建第一个模块
2. [模块核心概念](modules/core-concepts.md) - 模块的核心概念和架构
3. [Event 包装类详解](modules/event-wrapper.md) - Event 对象的完整说明
4. [模块最佳实践](modules/best-practices.md) - 开发高质量模块的建议

### 适配器开发

1. [适配器开发入门](adapters/getting-started.md) - 创建第一个适配器
2. [适配器核心概念](adapters/core-concepts.md) - 适配器的核心概念
3. [SendDSL 详解](adapters/send-dsl.md) - Send 消息发送 DSL 的完整说明
4. [事件转换器](adapters/converter.md) - 实现事件转换器
5. [适配器最佳实践](adapters/best-practices.md) - 开发高质量适配器的建议

### 扩展开发

1. [CLI 扩展开发](extensions/cli-extensions.md) - 开发自定义 CLI 命令

## 开发准备

在开始开发之前，请确保你：

1. 阅读了[基础概念](../getting-started/basic-concepts.md)
2. 熟悉了[事件处理](../getting-started/event-handling.md)
3. 安装了开发环境（Python >= 3.10）
4. 安装了 ErisPulse SDK

## 开发类型选择

根据你的需求选择合适的开发类型：

### 模块开发

**适用场景：**
- 扩展机器人功能
- 实现特定业务逻辑
- 提供命令和消息处理

**示例：**
- 天气查询机器人
- 音乐播放器
- 数据收集工具

**入门指南：** [模块开发入门](modules/getting-started.md)

### 适配器开发

**适用场景：**
- 连接新的消息平台
- 实现跨平台通信
- 提供平台特定功能

**示例：**
- Discord 适配器
- Slack 适配器
- 自定义平台适配器

**入门指南：** [适配器开发入门](adapters/getting-started.md)

### CLI 扩展开发

**适用场景：**
- 扩展命令行工具
- 提供自定义管理命令
- 自动化部署流程

**示例：**
- 部署脚本
- 数据迁移工具
- 配置管理工具

**入门指南：** [CLI 扩展开发](extensions/cli-extensions.md)

## 开发工具

### 项目模板

ErisPulse 提供了示例项目作为参考：

- `examples/example-module/` - 模块示例
- `examples/example-adapter/` - 适配器示例
- `examples/example-cli-module/` - CLI 扩展示例

### 开发模式

使用热重载模式进行开发：

```bash
epsdk run main.py --reload
```

### 调试技巧

启用 DEBUG 级别日志：

```toml
[ErisPulse.logger]
level = "DEBUG"
```

使用模块自己的日志记录器：

```python
from ErisPulse import sdk

logger = sdk.logger.get_child("MyModule")
logger.debug("调试信息")
```

## 发布你的模块

### 打包

确保项目包含以下文件：

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py
```

### pyproject.toml 配置

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "模块功能描述"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

### 发布到 PyPI

```bash
# 构建分发包
python -m build

# 发布到 PyPI
python -m twine upload dist/*
```

## 相关文档

- [标准规范](../standards/) - 确保兼容性的技术标准
- [平台特性指南](../platform-guide/) - 了解各平台适配器的特性
