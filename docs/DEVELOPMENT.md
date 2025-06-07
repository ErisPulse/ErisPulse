# ErisPulse 开发指南

ErisPulse（EP）是一个基于全异步架构和模块化设计的机器人开发框架。它通过内置的 sdk 对象将环境配置、日志、错误处理和工具函数封装起来，极大简化了模块开发和扩展。

## 快速开始

### 初始化 SDK

```python
from ErisPulse import sdk
sdk.init()
```

通过 sdk 对象，您可以访问以下核心功能：
- `sdk.env` - 环境配置管理
- `sdk.raiserr` - 内置错误管理器
- `sdk.logger` - 日志记录器
- `sdk.util` - 工具函数（如拓扑排序）

### 项目结构

```
ErisPulse/
├── __init__.py        # 项目初始化
├── __main__.py        # CLI 接口
├── db.py              # 环境配置管理
├── util.py            # 工具函数
├── logger.py          # 日志记录
├── adapter.py         # 平台适配器
├── raiserr.py         # 自定义异常
└── modules/           # 功能模块目录
    └── ...
```

### 主要模块说明

- **db**: 负责管理环境配置和模块信息，使用 SQLite 数据库存储配置
- **util**: 提供工具函数，包括拓扑排序和异步执行器
- **logger**: 提供日志功能，支持不同日志级别和日志输出控制
- **adapter**: 提供平台适配器基类及管理
- **raiserr**: 提供自定义错误管理，支持注册和抛出模块特定错误
- **modules/**: 存放所有功能模块

## 模块开发基础

### 目录结构

模块目录建议应遵循以下结构：

```
模块名/
├── __init__.py        # 模块入口文件
└── Core.py            # 核心逻辑实现
```
`Core.py` 不是必须的命名方式，基本上来说你可以是任何命名，只要在 `__init__.py` 中导入 `Main` 类即可。
- `__init__.py` 必须包含 `moduleInfo` 字典，并导入 `Main` 类
- `Core.py` 必须实现 `Main` 类

### 模块开发建议

- **异步支持**：优先使用异步编程模型（async/await）
- **性能优化**：避免阻塞操作，引入缓存机制以提升性能
- **减少第三方依赖**：优先使用 Python 原生库实现功能
- **日志记录**：使用 `logger` 记录关键操作，日志级别包括 `DEBUG < INFO < WARNING < ERROR < CRITICAL`

## 模块接口规范

### moduleInfo 字典

`moduleInfo` 是模块的元信息，定义如下：

```python
# __init__.py
moduleInfo = {
    "meta": {
        "name": "示例模块",              # 模块名称（必填）
        "version": "1.0.0",             # 版本号
        "description": "模块描述信息",   # 功能描述
        "author": "开发者",             # 模块作者
        "license": "MIT",               # 许可协议
        "homepage": ""                  # 项目主页（可选）
    },
    "dependencies": {
        "requires": [],  # 必需依赖模块列表
        "optional": [],  # 可选依赖模块列表（满足其中一项即可）
        "pip": []        # 第三方 pip 依赖包列表
    },
}
```

### Main 类

`Main` 类是模块的核心实现，其构造函数必须接受 `sdk` 参数：

```python
# Core.py
class Main:
    def __init__(self, sdk):
        self.sdk = sdk          # sdk 对象，包含 env、logger、raiserr、util
        self.logger = sdk.logger
        self.env = sdk.env
        self.raiserr = sdk.raiserr
        self.util = sdk.util
        self.adapter = sdk.adapter
        self.logger.info("模块已启动")

    def any_function(self):
        self.logger.info("模块中的 any_function 方法被调用")
```

这时用户即可使用 sdk.<ModuleName>.<ModuleFunc> 调用模块方法, 或者是您的自定义操作模块，如监听某个Adapter的事件，并执行相应的操作。

## 核心特性

### 异步编程支持

ErisPulse 完全基于异步架构，利用 asyncio 实现非阻塞操作。模块开发中应该使用 async/await 模式，确保高并发下的稳定运行。

### 模块间通信

通过 `sdk.模块名` 访问已加载的模块实例，实现模块间通信。

## 伪指针特性

ErisPulse 的 sdk 实例支持伪指针特性，第三方模块可以通过重写 `sdk.<Name>`（如 `sdk.logger`、`sdk.env` 等）来直接覆盖底层模块实现。例如：

```python
# 示例：重写日志模块
class CustomLogger:
    def info(self, msg):
        print(f"CustomLogger INFO: {msg}")
    def debug(self, msg):
        print(f"CustomLogger DEBUG: {msg}")
    def warning(self, msg):
        print(f"CustomLogger WARNING: {msg}")
    def error(self, msg):
        print(f"CustomLogger ERROR: {msg}")
    def critical(self, msg):
        print(f"CustomLogger CRITICAL: {msg}")

# 重定义 sdk.logger
sdk.logger = CustomLogger()
sdk.logger.info("通过自定义日志模块打印信息")
```

### 内置错误管理

通过 `sdk.raiserr` 统一注册和抛出模块错误。开发者可使用 `sdk.raiserr.register` 注册自定义错误类型，并使用相应属性触发错误。

```python
# 注册新的错误类型
sdk.raiserr.register("CustomError", doc="自定义错误描述")

# 抛出错误（默认仅记录日志，不中断程序）
sdk.raiserr.CustomError("发生了自定义错误", exit=False)
```

### 灵活的配置管理

利用 `sdk.env` 实现全局配置的动态读取与写入。

```python
# 获取配置项
value = sdk.env.get("配置项", "默认值")

# 设置配置项
sdk.env.set("配置项", "新值")
```

## 日志系统

### 日志等级

ErisPulse 使用标准日志等级：
- DEBUG - 调试信息，用于开发时的问题排查
- INFO - 重要操作记录，用于跟踪模块运行状态
- WARNING - 潜在问题警告，提示开发者注意
- ERROR - 错误发生，但不影响模块继续运行
- CRITICAL - 严重错误，可能导致模块停止

### 日志记录

使用 `sdk.logger` 开发者可以直接使用并记录日志到控制台：

```python
class Main:
    def __init__(self, sdk):
        self.logger = sdk.logger
        self.logger.info("这是一条信息日志")
        self.logger.debug("这是一条调试日志")
        self.logger.warning("这是一条警告日志")
        self.logger.error("这是一条错误日志")
        self.logger.critical("这是一条严重错误日志")
```

### 模块级日志控制

ErisPulse 支持为每个模块设置独立的日志等级：

```python
# 设置模块日志等级
sdk.logger.set_module_level("模块名", "DEBUG")

# 每个模块可以独立设置日志等级
sdk.logger.set_module_level("模块A", "INFO")
sdk.logger.set_module_level("模块B", "DEBUG")
```

### 日志输出和保存

支持将日志输出到多个文件，并可手动保存日志到指定位置：

```python
# 设置日志输出文件（支持多个文件）
sdk.logger.set_output_file(["日志1.log", "日志2.log"])

# 手动保存日志（支持多个文件）
sdk.logger.save_logs(["日志1.log", "日志2.log"])
```

## 模块系统

### 模块加载机制

模块加载时会检查以下内容：
1. 模块元信息是否完整
2. 必需依赖是否满足
3. 可选依赖是否可用

### 模块依赖管理

模块可以通过 `dependencies` 字段声明依赖：

```python
"dependencies": {
    "requires": ["依赖模块1", "依赖模块2"],  # 必需依赖
    "optional": [["可选依赖1", "可选依赖2"], ["可选依赖3"]],  # 可选依赖
    "pip": ["第三方依赖包1", "第三方依赖包2"]  # pip 依赖
}
```

### 模块初始化流程

模块初始化流程包括：
1. 检查模块元信息
2. 验证模块依赖
3. 进行拓扑排序
4. 初始化模块配置
5. 实例化模块

## SDK 核心功能

### 异步支持

ErisPulse 的所有核心功能都支持异步操作，开发者可以充分利用 async/await 模式进行开发。

### 模块间通信

通过 `self.sdk.模块名` 访问其他模块的实例，实现模块间通信。

### 环境配置管理

通过 `sdk.env` 实现全局配置的动态读取与写入。

### 错误处理

通过 `sdk.raiserr` 统一注册和抛出模块错误。

## 内置工具

工具模块提供了一系列实用函数和装饰器，用于简化开发过程并提高代码质量。

### 工具列表

*   **`ExecAsync(async_func, *args, **kwargs)`**: 在事件循环中异步执行一个异步函数。
*   **`@cache`**: 缓存函数结果的装饰器。
*   **`@run_in_executor`**: 将同步函数转换为异步函数，并在线程池中执行。
*   **`@retry(max_attempts=3, delay=1)`**: 自动重试可能会失败的函数。

### 示例

以下示例展示了如何在模块中使用工具模块中的函数和装饰器：

```python
import asyncio
from ErisPulse import sdk, util

class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger

    @util.run_in_executor
    def blocking_task(self, data):
        # 模拟一个耗时的同步任务
        import time
        time.sleep(2)
        return f"处理后的数据: {data}"

    @util.cache
    def cached_calculation(self, arg):
        # 模拟一个计算密集型任务
        self.logger.info(f"执行缓存计算，参数: {arg}")
        return arg * 2

    async def start(self):
        self.logger.info("模块启动")

        # 异步执行同步任务
        result = await self.blocking_task("一些数据")
        self.logger.info(f"异步任务结果: {result}")

        # 使用缓存
        result1 = self.cached_calculation(5)
        self.logger.info(f"第一次缓存结果: {result1}")
        result2 = self.cached_calculation(5)  # 从缓存中获取
        self.logger.info(f"第二次缓存结果: {result2}")

        # 使用重试装饰器
        try:
            await self.unreliable_operation()
        except Exception as e:
            self.logger.error(f"重试操作失败: {e}")

    @util.retry(max_attempts=3, delay=1)
    async def unreliable_operation(self):
        # 模拟一个可能失败的异步操作
        import random
        if random.random() < 0.5:
            raise Exception("操作失败")
        self.logger.info("操作成功")
```

在这个示例中，我们展示了如何使用 `@run_in_executor` 异步执行同步任务，使用 `@cache` 缓存计算结果，以及使用 `@retry` 自动重试可能失败的操作。

## 开发最佳实践

### 异步编程注意事项

- **避免阻塞操作**：尽量使用异步库替代阻塞式库（如 `aiohttp` 替代 `requests`）
- **任务管理**：使用 `asyncio.create_task` 创建后台任务，并确保任务异常被捕获
- **资源管理**：使用 `async with` 语句管理异步资源

### 日志记录的最佳实践

- **分级记录**：根据问题严重性选择合适的日志级别
- **上下文信息**：在日志中添加上下文信息（如用户 ID、请求 ID）
- **模块区分**：通过模块名区分日志来源

### 异常处理

- **务必捕获异常**：在模块入口方法中使用 `try...except` 捕获异常
- **自定义错误**：为模块定义专门的错误类型
- **合理使用 exit 参数**：决定错误是否中断程序

### 配置管理

- **统一配置访问**：所有配置通过 `sdk.env` 访问
- **动态配置更新**：支持运行时动态更新配置
- **配置持久化**：配置更改会持久化存储

## 示例项目

以下是一个完整的示例模块，展示如何实现一个简单的异步模块：

```python
# __init__.py
from .Core import Main

moduleInfo = {
    "meta": {
        "name": "示例模块",
        "version": "1.0.0",
        "description": "这是一个示例模块",
        "author": "开发者",
        "license": "MIT",
        "homepage": "",
    },
    "dependencies": {
        "requires": [],
        "optional": [],
        "pip": [],
    },
}
```

```python
# Core.py
class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
        self.env = sdk.env
        self.raiserr = sdk.raiserr
        self.adapter = sdk.adapter

    # 消息处理器
    self.adapter.Yunhu.on("message")
    async def handle_normal_message(self, data):
        pass

    self.adapter.QQ.on("message")
    async def handle_onebot_message(self, data):
        pass
```

## 贡献模块流程

1. Fork [模块仓库](https://github.com/ErisPulse/ErisPulse-ModuleRepo) 并新建分支
2. 按照[模块开发基础](#1-模块开发基础)规范实现模块
3. 提交 Pull Request，并在 PR 描述中说明模块功能与依赖
4. 通过代码审核后合并

## 常见开发问题与排查

### 模块未被加载

- 检查 `moduleInfo` 是否完整，`meta.name` 是否唯一
- 检查依赖模块是否已安装并启用
- 查看日志输出，定位加载失败原因

### pip 依赖未自动安装

- 确认 `pip` 字段已正确填写
- 检查网络环境

### 模块状态管理

- 通过 `env.set_module_status("模块名称", True)` 启用模块
- 通过 `env.set_module_status("模块名称", False)` 禁用模块
- 被禁用的模块不会被加载和运行

## FAQ

### 如何在模块中访问其他模块？

通过 `self.sdk.模块名` 访问已加载的模块实例。

### 如何贡献文档？

直接编辑 `docs/` 目录下的 Markdown 文件并提交 PR。

### 如何查看模块的运行时配置？

通过 `sdk.env.get("KEY")` 获取配置，通过 `sdk.env.set("KEY", "VALUE")` 设置配置。
