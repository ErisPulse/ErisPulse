# ErisPulse 开发指南

ErisPulse 是基于 [RyhBotPythonSDK V2](https://github.com/runoneall/RyhBotPythonSDK2) 和 [SDKFrame](https://github.com/runoneall/sdkFrame) 构建的异步 SDK 项目，最低支持 **Python 3.7**，推荐使用 **Python 3.9 或更高版本**。

---

## 快速开始

### 项目结构

```
ErisPulse/
├── __init__.py        # 项目初始化
├── __main__.py        # CLI 接口
├── envManager.py      # 环境配置管理
├── errors.py          # 自定义异常
├── logger.py          # 日志记录
├── origin.py          # 模块源管理
├── sdk.py             # SDK 核心
├── util.py            # 工具函数
└── modules/           # 功能模块目录
    └── ...
```

### 主要模块说明

- **envManager**: 负责管理环境配置和模块信息，使用 SQLite 数据库存储配置
- **logger**: 提供日志功能，支持不同日志级别
- **origin**: 管理模块源，添加、删除、更新模块源等方法在此处
- **util**: 提供工具函数，拓扑排序、异步执行
- **modules**: 功能模块目录

本项目采用模块化设计，开发者可以通过实现符合规范的模块快速扩展功能。以下是开发的核心步骤：

1.  **模块开发基础**：了解模块目录结构和开发建议。
2.  **模块接口规范**：实现 `moduleInfo` 字典和 `Main` 类。
3.  **核心特性**：掌握异步调用、日志记录和模块入口方法。
4.  **最佳实践**：遵循异步编程和日志记录的最佳实践。

详细内容请参考以下章节。

---

### 1. 模块开发基础

#### 1.1 建议

-   **日志记录**：使用 `logger` 记录关键操作，日志级别包括 `DEBUG < INFO < WARNING < ERROR < CRITICAL`。
-   **减少第三方依赖**：优先使用 Python 原生库实现功能，避免引入不必要的第三方库。
-   **性能优化**：
    -   使用异步编程模型。
    -   避免阻塞操作。
    -   引入缓存机制以提升性能。

#### 1.2 目录结构

模块目录应遵循以下结构：

```plaintext
模块名/
├── __init__.py        # 模块入口文件
└── Core.py            # 核心逻辑实现
```

-   `__init__.py` 必须包含 `moduleInfo` 字典，并导入 `Main` 类。
-   `Core.py` 必须实现 `Main` 类（`Core.py` 的命名不是必须的）。

---

### 2. 模块接口规范

#### 2.1 moduleInfo 字典

`moduleInfo` 是模块的元信息，定义如下：

```python
moduleInfo = {
    "meta": {
        "name": "logger",  # 模块名称（必填）
        "author": "ErisPulse",  # 开发者姓名（选填）
        "description": "Test Logger Module",  # 模块功能描述（选填）
        "version": "1.0.0",  # 版本号（选填）
        "license": "MIT",  # 许可证（选填）
        "homepage": "",  # 项目主页（选填）
    },
    "dependencies": {
        "requires": [],  # 必需依赖模块列表
        "optional": [["mod1", "mod2"], ["mod3"], "mod4"],  # 可选依赖模块列表（至少拥有其中一个依赖便可）
        "pip": [],  # 第三方 pip 依赖列表
    },
}
```

#### 2.2 Main 类

`Main` 类是模块的核心实现，其构造函数必须接受 `sdk` 参数：

```python
class Main:
    def __init__(self, sdk):
        self.sdk = sdk  # SDK 实例，提供核心功能
        self.logger = sdk.logger  # 日志记录器实例
```

-   `sdk` 实例：
    -   提供访问其他模块、注册事件处理器、管理配置等核心功能。
    -   可以通过 `sdk.模块名` 访问其他模块的实例。
-   `sdk.logger` ：
    -   用于记录模块运行时的各种信息，方便调试和监控。
    -   支持 `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` 等日志级别。

---

### 3. 核心特性

#### 3.1 内置 Logger 模块

使用 `sdk.logger` 开发者可以直接使用并记录日志到控制台：

```python
class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger

        # 记录不同级别的日志
        self.logger.info("这是一条信息日志")
        self.logger.debug("这是一条调试日志")
        self.logger.warning("这是一条警告日志")
        self.logger.error("这是一条错误日志")
        self.logger.critical("这是一条严重错误日志")
```

#### 3.2 动态服务加载与运行

```python
import asyncio
from sdk import sdk

# 初始化 SDK
sdk.init()

async def run_servers():
    tasks = []

    # 加载并运行 AsyncServer
    if hasattr(sdk, "AsyncServer"):
        tasks.append(sdk.AsyncServer.Run())
        sdk.AsyncServer.AddTrigger(sdk.NormalHandler)
        sdk.AsyncServer.AddTrigger(sdk.CommandHandler)

    # 加载并运行 OneBotAdapter
    if hasattr(sdk, "OneBotAdapter"):
        tasks.append(sdk.OneBotAdapter.Run())
        sdk.OneBotAdapter.AddTrigger(sdk.OneBotMessageHandler)

    # 并行运行所有服务
    await asyncio.gather(*tasks)

# 启动服务
await run_servers()
```

#### 3.3 灵活的配置初始化

支持两种方式初始化配置数据：

1.  **通过 `env.py` 文件直接定义变量**：

    ```python
    # env.py
    YUNHU_TOKEN = "114514"
    LOG_LEVEL = "DEBUG"
    SERVER = {"host": "0.0.0.0", "port": 11451, "path": "/114514"}
    ```

2.  **通过代码动态设置**：

    ```python
    # env.py
    from sdk import env

    env.set("YUNHU_TOKEN", "114514")
    env.set("LOG_LEVEL", "DEBUG")
    env.set("SERVER", {"host": "0.0.0.0", "port": 11451, "path": "/114514"})
    ```

#### 3.4 模块状态管理

可以使用 `envManager` 动态启用或禁用模块。

```python
from ErisPulse import env

# 禁用模块
env.set_module_status("模块名称", False)

# 启用模块
env.set_module_status("模块名称", True)
```

被禁用的模块不会被加载和运行。

---

### 4. 开发最佳实践

#### 4.1 异步编程注意事项

-   **避免阻塞操作**：尽量使用异步库替代阻塞式库（如 `aiohttp` 替代 `requests`）。
-   **任务管理**：使用 `asyncio.create_task` 创建后台任务，并确保任务异常被捕获。

#### 4.2 日志记录的最佳实践

-   **分级记录**：根据问题严重性选择合适的日志级别。
-   **上下文信息**：在日志中添加上下文信息（如用户 ID、请求 ID），便于排查问题。

#### 4.3 异常处理

-   **务必在入口方法中使用 `try...except` 捕获异常**，避免线程意外退出。

    ```python
    from ErisPulse import sdk

    class Main:
        def __init__(self, sdk, logger):
            self.sdk = sdk
            self.logger = logger

        def start_service(self):
            try:
                # ...服务逻辑...
            except Exception as e:
                self.logger.error("服务启动失败")
    ```

---
    
### 5. 示例项目

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
        if self.env.get("田所浩二", False) or self.env.get("目力先辈恶臭", False):
            self.logger.info("""
                该模块需要以下env配置才能运行，请检测是否配置正确
                \n田所浩二: 用来判断你是不是()
                \n目力先辈恶臭: ？
                """
            )

        # 初始化标志变量
        self.handlers_registered = False

        # 注册 NormalHandler
        if hasattr(sdk, "NormalHandler"):
            sdk.NormalHandler.AddHandle(self.handle_normal_message) #注册处理器
            self.logger.info("成功注册NormalHandler消息处理")
            self.handlers_registered = True

        # 注册 OneBotMessageHandler
        if hasattr(sdk, "OneBotMessageHandler"):
            sdk.OneBotMessageHandler.AddHandle(self.handle_onebot_message)#注册处理器
            self.logger.info("成功注册OneBotMessageHandler消息处理")
            self.handlers_registered = True

        # 检查 m_ServNormal 是否存在
        if hasattr(sdk, "m_ServNormal"):
            self.logger.info("此模块仅支持异步消息处理器，请使用其它模块代替")

        # 如果没有任何处理器被注册，记录警告日志
        if not self.handlers_registered:
            self.logger.warning("未找到任何可用的消息处理器")
    
    def Run(self):  # Run只是示例的启动方法，留给用户直接启动某些主任务模块，而不是sdk直接启动
        self.logger.info("示例模块已启动")

    # 消息处理器
    async def handle_normal_message(self, data):
        pass
    async def handle_onebot_message(self, data):
        pass
```

---

### 6. 贡献模块流程

1. Fork [模块仓库](https://github.com/ErisPulse/ErisPulse-ModuleRepo) 并新建分支。
2. 按照[模块开发基础](#1-模块开发基础)规范实现模块。
3. 提交 Pull Request，并在 PR 描述中说明模块功能与依赖。
4. 通过代码审核后合并。

---

### 7. 常见开发问题与排查

- **模块未被加载？**
  - 检查 `moduleInfo` 是否完整，`meta.name` 是否唯一。
  - 检查依赖模块是否已安装并启用。
  - 查看日志输出，定位加载失败原因。

- **依赖冲突或循环依赖？**
  - 检查 `requires` 和 `optional` 配置，避免循环引用。
  - 使用 CLI 的 `list` 命令查看依赖关系。

- **pip 依赖未自动安装？**
  - 确认 `pip` 字段已正确填写。
  - 检查网络环境，或手动执行 `pip install`。

---

### 8. FAQ

**Q: 如何在模块中访问其他模块？**  
A: 通过 `self.sdk.模块名` 访问已加载的模块实例。

**Q: 如何自定义日志格式？**  
A: 可使用 `self.sdk.env.set("LOG_LEVEL", 日志等级)` 修改中的日志格式化器。

**Q: 如何贡献文档？**  
A: 直接编辑 `docs/` 目录下的 Markdown 文件并提交 PR。
