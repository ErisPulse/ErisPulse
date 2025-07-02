# ErisPulse 开发文档合集

本文件由多个开发文档合并而成，用于辅助 AI 理解 ErisPulse 的模块开发规范与 SDK 使用方式。

## 各文件对应内容说明

| 文件名 | 作用 |
|--------|------|
| README.md | 项目概览、安装说明和快速入门指南 |
| DEVELOPMENT.md | 模块结构定义、入口文件格式、Main 类规范 |
| ADAPTERS.md | 平台适配器说明，包括事件监听和消息发送方式 |
| REFERENCE.md | SDK 接口调用方式（如 `sdk.env`, `sdk.logger`, `sdk.adapter` 等） |

## 合并内容开始

<!-- README.md -->

# ErisPulse - 异步机器人开发框架

![ErisPulse Logo](.github/assets/erispulse_logo.png)

[![FramerOrg](https://img.shields.io/badge/合作伙伴-FramerOrg-blue?style=flat-square)](https://github.com/FramerOrg)
[![License](https://img.shields.io/github/license/ErisPulse/ErisPulse?style=flat-square)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)

> 文档站: 
[![Docs-Main](https://img.shields.io/badge/docs-main_site-blue?style=flat-square)](https://www.erisdev.com/docs.html)
[![Docs-CF Pages](https://img.shields.io/badge/docs-cloudflare-blue?style=flat-square)](https://erispulse.pages.dev/docs.html)
[![Docs-GitHub](https://img.shields.io/badge/docs-github-blue?style=flat-square)](https://erispulse.github.io/docs.html)
[![Docs-Netlify](https://img.shields.io/badge/docs-netlify-blue?style=flat-square)](https://erispulse.netlify.app/docs.htm)


## 核心特性

| 特性 | 描述 |
|------|------|
| **异步架构** | 完全基于 async/await 的异步设计 |
| **模块化系统** | 灵活的插件和模块管理 |
| **热重载** | 开发时自动重载，无需重启 |
| **错误管理** | 统一的错误处理和报告系统 |
| **配置管理** | 灵活的配置存储和访问 |

---

## 快速开始

### 框架选型指南

| 需求 | 推荐框架 | 理由 |
|------|---------|------|
| 轻量化/底层模块化 | [Framer](https://github.com/FramerOrg/Framer) | 高度解耦的模块化设计 |
| 全功能机器人开发 | ErisPulse | 开箱即用的完整解决方案 |

---

## 安装指南

我们全面采用 [`uv`](https://github.com/astral-sh/uv) 作为 Python 工具链，提供更快速可靠的安装体验。

> ℹ️ **uv** 是由 Astral 开发的新一代 Python 包管理工具，比传统 pip 快 10-100 倍，并具有更好的依赖解析能力。

### 1. 安装 uv

#### 通用方法 (pip):
```bash
pip install uv
```

#### macOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

验证安装:
```bash
uv --version
```

### 2. 安装 ErisPulse

```bash
uv python install 3.12          # 安装 Python 3.12
uv venv                         # 创建虚拟环境
source .venv/bin/activate       # 激活环境 (Windows: .venv\Scripts\activate)
uv pip install ErisPulse --upgrade  # 安装框架
```

---

## 测试与开发

### 克隆项目并进入目录

```bash
git clone https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
```

### 使用 `uv` 同步项目环境

```bash
uv sync

# 启动虚拟环境
source .venv/bin/activate   
# Windows: .venv\Scripts\activate
```

> `ErisPulse` 目前正在使用 `python3.13` 进行开发(所以您同步环境时会自动安装 `3.13`)，但也可以使用其他版本(版本不应低于 `3.10`)。

### 安装依赖并开始

```bash
uv pip install -e .
```

这将以“开发模式”安装 SDK，所有本地修改都会立即生效。

### 验证安装

运行以下命令确认 SDK 正常加载：

```bash
python -c "from ErisPulse import sdk; sdk.init()"
```

### 运行测试

我们提供了一个交互式测试脚本，可以帮助您快速验证SDK功能：

```bash
uv run devs/test.py
```

测试功能包括:
- 日志系统测试
- 环境配置测试
- 错误管理测试
- 工具函数测试
- 适配器功能测试

### 开发模式 (热重载)
```bash
epsdk run your_script.py --reload
```

---

## 🤝 贡献指南

我们欢迎各种形式的贡献，包括但不限于:

1. **报告问题**  
   在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交bug报告

2. **功能请求**  
   通过 [社区讨论](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法

3. **代码贡献**  
   提交 Pull Request 前请阅读我们的 [开发指南](docs/DEVELOPMENT.md)

4. **文档改进**  
   帮助完善文档和示例代码

---

[加入社区讨论 →](https://github.com/ErisPulse/ErisPulse/discussions)

<!--- End of README.md -->

<!-- DEVELOPMENT.md -->

# ErisPulse 开发者指南

> 本指南从开发者角度出发，帮助你快速理解并接入 **ErisPulse** 框架，进行模块和适配器的开发。

---
## 一、使用 SDK 功能
### SDK 提供的核心对象

| 名称 | 用途 |
|------|------|
| `sdk.env` | 获取/设置全局配置 |
| `sdk.mods` | 管理模块 |
| `sdk.logger` | 日志记录器 |
| `sdk.raiserr` | 错误管理器 |
| `sdk.util` | 工具函数（缓存、重试等） |
| `sdk.adapter` | 获取其他适配器实例 |
| `sdk.BaseAdapter` | 适配器基类 |

#### 日志记录：

```python
#  设置单个模块日志级别
sdk.logger.set_module_level("MyModule", "DEBUG")

#  单次保持所有模块日志历史到文件
sdk.logger.save_logs("log.txt")

#  各等级日志
sdk.logger.debug("调试信息")
sdk.logger.info("运行状态")
sdk.logger.warning("警告信息")
sdk.logger.error("错误信息")
sdk.logger.critical("致命错误")    # 会触发程序崩溃
```

#### env配置模块：

```python
# 设置配置项
sdk.env.set("my_config_key", "new_value")

# 获取配置项
config_value = sdk.env.get("my_config_key", "default_value")

# 删除配置项
sdk.env.delete("my_config_key")

# 获取所有配置项(不建议，性能浪费)
all_config = sdk.env.get_all_keys()

# 批量操作
sdk.env.set_multi({
    'config1': 'value1',
    'config2': {'data': [1,2,3]},
    'config3': True
})

values = sdk.env.get_multi(['config1', 'config2'])
sdk.env.delete_multi(['old_key1', 'old_key2'])

# 事务使用
with sdk.env.transaction():
    sdk.env.set('important_key', 'value')
    sdk.env.delete('temp_key')
    # 如果出现异常会自动回滚

# 快照管理
# 创建重要操作前的快照
snapshot_path = sdk.env.snapshot('before_update')

# 恢复数据库状态
sdk.env.restore('before_update')

# 自动快照(默认每小时)
sdk.env.set_snapshot_interval(3600)  # 设置自动快照间隔(秒)

# 性能提示：
# - 批量操作比单次操作更高效
# - 事务可以保证多个操作的安全性
# - 快照适合在重大变更前创建
```

#### 注册自定义错误类型：

```python
#  注册一个自定义错误类型
sdk.raiserr.register("MyCustomError", doc="这是一个自定义错误")

#  获取错误信息
error_info = sdk.raiserr.info("MyCustomError")
if error_info:
    print(f"错误类型: {error_info['type']}")
    print(f"文档描述: {error_info['doc']}")
    print(f"错误类: {error_info['class']}")
else:
    print("未找到该错误类型")

#  抛出一个自定义错误
sdk.raiserr.MyCustomError("发生了一个错误")

```

#### 工具函数：

```python
# 工具函数装饰器：自动重试指定次数
@sdk.util.retry(max_attempts=3, delay=1)
async def my_retry_function():
    # 此函数会在异常时自动重试 3 次，每次间隔 1 秒
    ...

# 缓存装饰器：缓存函数调用结果（基于参数）
@sdk.util.cache
def get_expensive_result(param):
    # 第一次调用后，相同参数将直接返回缓存结果
    ...

# 异步执行装饰器：将同步函数放入线程池中异步执行
@sdk.util.run_in_executor
def sync_task():
    # 此函数将在独立线程中运行，避免阻塞事件循环
    ...

# 在同步函数中调用异步任务
sdk.util.ExecAsync(sync_task)

```

---

### 5. 模块间通信

通过 `sdk.<ModuleName>` 访问其他模块实例：

```python
other_module = sdk.OtherModule
result = other_module.some_method()
```

### 6. 适配器的方法调用
通过 `sdk.adapter.<AdapterName>` 访问适配器实例：
```python
adapter = sdk.adapter.AdapterName
result = adapter.some_method()
```

## 二、模块开发

### 1. 目录结构

一个标准模块应包含以下两个核心文件：

```
MyModule/
├── __init__.py    # 模块入口
└── Core.py        # 核心逻辑
```

### 2. `__init__.py` 文件

该文件必须定义 `moduleInfo` 字典，并导入 `Main` 类：

```python
moduleInfo = {
    "meta": {
        "name": "MyModule",
        "version": "1.0.0",
        "description": "我的功能模块",
        "author": "开发者",
        "license": "MIT"
    },
    "dependencies": {
        "requires": [],       # 必须依赖的其他模块
        "optional": [         # 可选依赖模块列表（满足其中一个即可）
            "可选模块",
            ["可选模块"],
            ["可选组依赖模块1", "可选组依赖模块2"]
        ],
        "pip": []             # 第三方 pip 包依赖
    }
}

from .Core import Main
```

其中, 可选依赖支持组依赖：
- 可选模块与组依赖模块（如 `["组依赖模块1", "组依赖模块2"]` 和 `["组依赖模块3", "组依赖模块4"]`）构成“或”关系，即满足其中一组即可。
- 组依赖模块以数组形式表示，视为一个整体（例如：`组依赖模块1 + 组依赖模块2` 和 `可选模块` 中任意一组存在即符合要求）。

> ⚠️ 注意：模块名必须唯一，避免与其他模块冲突。

---

### 3. `Core.py` 文件

实现模块主类 `Main`，构造函数必须接收 `sdk` 参数：

```python
class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
        self.env = sdk.env
        self.util = sdk.util
        self.raiserr = sdk.raiserr

        self.logger.info("模块已加载")

    def print_hello(self):
        self.logger.info("Hello World!")

```

- 所有 SDK 提供的功能都可通过 `sdk` 对象访问。
```python
# 这时候在其它地方可以访问到该模块
from ErisPulse import sdk
sdk.MyModule.print_hello()

# 运行模块主程序（推荐使用CLI命令）
# epsdk run main.py --reload
```
---

## 三、平台适配器开发（Adapter）

适配器用于对接不同平台的消息协议（如 Yunhu、OneBot 等），是框架与外部平台交互的核心组件。

### 1. 目录结构

```
MyAdapter/
├── __init__.py    # 模块入口
└── Core.py        # 适配器逻辑
```

### 2. `__init__.py` 文件

同样需定义 `moduleInfo` 并导入 `Main` 类：

```python
moduleInfo = {
    "meta": {
        "name": "MyAdapter",
        "version": "1.0.0",
        "description": "我的平台适配器",
        "author": "开发者",
        "license": "MIT"
    },
    "dependencies": {
        "requires": [],
        "optional": [],
        "pip": ["aiohttp"]
    }
}

from .Core import Main, MyPlatformAdapter

adapterInfo = {
    "myplatform": MyPlatformAdapter,
}
```

### 3. `Core.py`
实现适配器主类 `Main`，并提供适配器类继承 `sdk.BaseAdapter`：

```python
from ErisPulse import sdk

class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
        #   这里是模块的初始化类，当然你也可以在这里进行一些方法提供
        #   在这里的方法可以通过 sdk.<模块名>.<方法名> 访问
        #   如果该模块专精于Adapter，那么本类不建议提供方法
        #   在 MyPlatformAdapter 中的方法可以使用 sdk.adapter.<适配器注册名>.<方法名> 访问

class MyPlatformAdapter(sdk.BaseAdapter):
    class Send(sdk.BaseAdapter.Send):  # 继承BaseAdapter内置的Send类
        # 底层SendDSL中提供了To方法，用户调用的时候类会被定义 `self._target_type` 和 `self._target_id`/`self._target_to` 三个属性
        # 当你只需要一个接受的To时，例如 mail 的To只是一个邮箱，那么你可以使用 `self.To(email)`，这时只会有 `self._target_id`/`self._target_to` 两个属性被定义
        # 或者说你不需要用户的To，那么用户也可以直接使用 Send.Func(text) 的方式直接调用这里的方法
        
        # 可以重写Text方法提供平台特定实现
        def Text(self, text: str):
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
            
        # 添加新的消息类型
        def Image(self, file: bytes):
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_image",
                    file=file,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )

    #   这里的call_api方法需要被实现, 哪怕他是类似邮箱时一个轮询一个发送stmp无需请求api的实现
    #   因为这是必须继承的方法
    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError()

    #   启动方法，你需要在这里定义你的adapter启动时候的逻辑
    async def start(self):
        raise NotImplementedError()
    #   停止方法，你需要在这里进行必要的释放资源等逻辑
    async def shutdown(self):
        raise NotImplementedError()
    #  适配器设定了启动和停止的方法，用户可以直接通过 sdk.adapter.update() 来启动所有适配器，当然在底层捕捉到您adapter的错误时我们会尝试停止适配器再进行重启等操作
```
### 接口规范说明

#### 必须实现的方法

| 方法 | 描述 |
|------|------|
| `call_api(endpoint: str, **params)` | 调用平台 API |
| `start()` | 启动适配器 |
| `shutdown()` | 关闭适配器资源 |

#### 可选实现的方法

| 方法 | 描述 |
|------|------|
| `on(event_type: str)` | 注册事件处理器 |
| `add_handler(event_type: str, func: Callable)/add_handler(func: Callable)` | 添加事件处理器 |
| `middleware(func: Callable)` | 添加中间件处理传入数据 |
| `emit(event_type: str, data: Any)` | 自定义事件分发逻辑 |

- 在适配器中如果需要向底层提交事件，请使用 `emit()` 方法。
- 这时用户可以通过 `on([事件类型])` 修饰器 或者 `add_handler()` 获取到您提交到adapter的事件。

> ⚠️ 注意：
> - 适配器类必须继承 `sdk.BaseAdapter`；
> - 必须实现 `call_api`, `start`, `shutdown` 方法 和 `Send`类并继承自 `super().Send`；
> - 推荐实现 `.Text(...)` 方法作为基础消息发送接口。

### 4. DSL 风格消息接口（SendDSL）

每个适配器可定义一组链式调用风格的方法，例如：

```python
class Send(super().Send):
    def Text(self, text: str):
        return asyncio.create_task(
            self._adapter.call_api(...)
        )

    def Image(self, file: bytes):
        return asyncio.create_task(
            self._upload_file_and_call_api(...)
        )
```

调用方式如下：

```python
sdk.adapter.MyPlatform.Send.To("user", "U1001").Text("你好")
```

> 建议方法名首字母大写，保持命名统一。

---
### 四、最简 main.py 示例
```python
from ErisPulse import sdk

async def main():
    try:
        sdk.init()
        await sdk.adapter.startup()

    except Exception as e:
        sdk.logger.error(e)
    except KeyboardInterrupt:
        sdk.logger.info("正在停止程序")
    finally:
        await sdk.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### 四、开发建议

#### 1. 使用异步编程模型
- **优先使用异步库**：如 `aiohttp`、`asyncpg` 等，避免阻塞主线程。
- **合理使用事件循环**：确保异步函数正确地被 `await` 或调度为任务（`create_task`）。

#### 2. 异常处理与日志记录
- **统一异常处理机制**：结合 `sdk.raiserr` 注册自定义错误类型，提供清晰的错误信息。
- **详细的日志输出**：在关键路径上打印调试日志，便于问题排查。

#### 3. 模块化与解耦设计
- **职责单一原则**：每个模块/类只做一件事，降低耦合度。
- **依赖注入**：通过构造函数传递依赖对象（如 `sdk`），提高可测试性。

#### 4. 性能优化
- **缓存机制**：利用 `@sdk.util.cache` 缓存频繁调用的结果。
- **资源复用**：连接池、线程池等应尽量复用，避免重复创建销毁开销。

#### 5. 安全与隐私
- **敏感数据保护**：避免将密钥、密码等硬编码在代码中，使用环境变量或配置中心。
- **输入验证**：对所有用户输入进行校验，防止注入攻击等安全问题。

---

## 五、提交到官方源

如果你希望将你的模块或适配器加入 ErisPulse 官方模块仓库，请参考 [模块源贡献](https://github.com/ErisPulse/ErisPulse-ModuleRepo)。


<!--- End of DEVELOPMENT.md -->

<!-- REFERENCE.md -->

# API Reference Documentation

## __init__ (source: [ErisPulse/__init__.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/__init__.py))

# SDK 核心初始化

提供SDK全局对象构建和初始化功能。

## 主要功能
- 构建全局sdk对象
- 预注册核心错误类型
- 提供SDK初始化入口
- 集成各核心模块

## API 文档
### 核心对象：
    - sdk: 全局SDK命名空间对象
    - sdk.init(): SDK初始化入口函数

### 预注册错误类型：
    - CaughtExternalError: 外部捕获异常
    - InitError: 初始化错误
    - MissingDependencyError: 缺少依赖错误  
    - InvalidDependencyError: 无效依赖错误
    - CycleDependencyError: 循环依赖错误
    - ModuleLoadError: 模块加载错误

### 示例用法：

```
from ErisPulse import sdk

# 初始化SDK
sdk.init()

# 访问各模块功能
sdk.logger.info("SDK已初始化")
```

## __main__ (source: [ErisPulse/__main__.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/__main__.py))

# CLI 入口

提供命令行界面(CLI)用于模块管理、源管理和开发调试。

## 主要功能
- 模块管理: 安装/卸载/启用/禁用
- 源管理: 添加/删除/更新源
- 热重载: 开发时自动重启
- 彩色终端输出

## 主要命令
### 模块管理:
    init: 初始化SDK
    install: 安装模块
    uninstall: 卸载模块
    enable: 启用模块
    disable: 禁用模块
    list: 列出模块
    update: 更新模块列表
    upgrade: 升级模块

### 源管理:
    origin add: 添加源
    origin del: 删除源  
    origin list: 列出源

### 开发调试:
    run: 运行脚本
    --reload: 启用热重载

### 示例用法:

```
# 安装模块
epsdk install MyModule

# 启用热重载
epsdk run main.py --reload

# 管理源
epsdk origin add https://example.com/map.json
```

## adapter (source: [ErisPulse/adapter.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/adapter.py))

# 适配器系统

提供平台适配器基类、消息发送DSL和适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。

## API 文档

### 适配器基类 (BaseAdapter)
适配器基类提供了与外部平台交互的标准接口。

#### call_api(endpoint: str, **params) -> Any
调用平台API的抽象方法。
- 参数:
  - endpoint: API端点
  - **params: API参数
- 返回:
  - Any: API调用结果
- 说明:
  - 必须由子类实现
  - 处理与平台的实际通信
- 示例:
```python
class MyPlatformAdapter(BaseAdapter):
    async def call_api(self, endpoint: str, **params):
        if endpoint == "/send":
            return await self._send_message(params)
        elif endpoint == "/upload":
            return await self._upload_file(params)
        raise NotImplementedError(f"未实现的端点: {endpoint}")
```

#### start() -> None
启动适配器的抽象方法。
- 参数: 无
- 返回:
  - None
- 说明:
  - 必须由子类实现
  - 处理适配器的初始化和启动逻辑
- 示例:
```python
class MyPlatformAdapter(BaseAdapter):
    async def start(self):
        self.client = await self._create_client()
        self.ws = await self.client.create_websocket()
        self._start_heartbeat()
```

#### shutdown() -> None
关闭适配器的抽象方法。
- 参数: 无
- 返回:
  - None
- 说明:
  - 必须由子类实现
  - 处理资源清理和关闭逻辑
- 示例:
```python
class MyPlatformAdapter(BaseAdapter):
    async def shutdown(self):
        if self.ws:
            await self.ws.close()
        if self.client:
            await self.client.close()
```

#### on(event_type: str = "*") -> Callable
事件监听装饰器。
- 参数:
  - event_type: 事件类型，默认"*"表示所有事件
- 返回:
  - Callable: 装饰器函数
- 示例:
```python
adapter = MyPlatformAdapter()

@adapter.on("message")
async def handle_message(data):
    print(f"收到消息: {data}")

@adapter.on("error")
async def handle_error(error):
    print(f"发生错误: {error}")

# 处理所有事件
@adapter.on()
async def handle_all(event):
    print(f"事件: {event}")
```

#### emit(event_type: str, data: Any) -> None
触发事件。
- 参数:
  - event_type: 事件类型
  - data: 事件数据
- 返回:
  - None
- 示例:
```python
class MyPlatformAdapter(BaseAdapter):
    async def _handle_websocket_message(self, message):
        # 处理消息并触发相应事件
        if message.type == "chat":
            await self.emit("message", {
                "type": "chat",
                "content": message.content,
                "sender": message.sender
            })
```

#### middleware(func: Callable) -> Callable
添加中间件处理器。
- 参数:
  - func: 中间件函数
- 返回:
  - Callable: 中间件函数
- 示例:
```python
adapter = MyPlatformAdapter()

@adapter.middleware
async def log_middleware(data):
    print(f"处理数据: {data}")
    return data

@adapter.middleware
async def filter_middleware(data):
    if "spam" in data.get("content", ""):
        return None
    return data
```

### 消息发送DSL (SendDSL)
提供链式调用风格的消息发送接口。

#### To(target_type: str = None, target_id: str = None) -> 'SendDSL'
设置消息目标。
- 参数:
  - target_type: 目标类型（可选）
  - target_id: 目标ID
- 返回:
  - SendDSL: 发送器实例
- 示例:
```python
# 发送到用户
sdk.adapter.Platform.Send.To("user", "123").Text("Hello")

# 发送到群组
sdk.adapter.Platform.Send.To("group", "456").Text("Hello Group")

# 简化形式（只有ID）
sdk.adapter.Platform.Send.To("123").Text("Hello")
```

#### Text(text: str) -> Task
发送文本消息。
- 参数:
  - text: 文本内容
- 返回:
  - Task: 异步任务
- 示例:
```python
# 发送简单文本
await sdk.adapter.Platform.Send.To("user", "123").Text("Hello")

# 发送格式化文本
name = "Alice"
await sdk.adapter.Platform.Send.To("123").Text(f"Hello {name}")
```

### 适配器管理 (AdapterManager)
管理多个平台适配器的注册、启动和关闭。

#### register(platform: str, adapter_class: Type[BaseAdapter]) -> bool
注册新的适配器类。
- 参数:
  - platform: 平台名称
  - adapter_class: 适配器类
- 返回:
  - bool: 注册是否成功
- 示例:
```python
# 注册适配器
sdk.adapter.register("MyPlatform", MyPlatformAdapter)

# 注册多个适配器
adapters = {
    "Platform1": Platform1Adapter,
    "Platform2": Platform2Adapter
}
for name, adapter in adapters.items():
    sdk.adapter.register(name, adapter)
```

#### startup(platforms: List[str] = None) -> None
启动指定的适配器。
- 参数:
  - platforms: 要启动的平台列表，None表示所有平台
- 返回:
  - None
- 示例:
```python
# 启动所有适配器
await sdk.adapter.startup()

# 启动指定适配器
await sdk.adapter.startup(["Platform1", "Platform2"])
```

#### shutdown() -> None
关闭所有适配器。
- 参数: 无
- 返回:
  - None
- 示例:
```python
# 关闭所有适配器
await sdk.adapter.shutdown()

# 在程序退出时关闭
import atexit
atexit.register(lambda: asyncio.run(sdk.adapter.shutdown()))
```

## db (source: [ErisPulse/db.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/db.py))

# 环境配置

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

## API 文档

### 基本操作
#### get(key: str, default: Any = None) -> Any
获取配置项的值。
- 参数:
  - key: 配置项键名
  - default: 如果键不存在时返回的默认值
- 返回:
  - Any: 配置项的值，如果是JSON格式则自动解析为Python对象
- 示例:
```python
# 获取基本配置
timeout = sdk.env.get("network.timeout", 30)

# 获取结构化数据
user_settings = sdk.env.get("user.settings", {})
if "theme" in user_settings:
    apply_theme(user_settings["theme"])

# 条件获取
debug_mode = sdk.env.get("app.debug", False)
if debug_mode:
    enable_debug_features()
```

#### set(key: str, value: Any) -> bool
设置配置项的值。
- 参数:
  - key: 配置项键名
  - value: 配置项的值，复杂类型会自动序列化为JSON
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 设置基本配置
sdk.env.set("app.name", "MyApplication")

# 设置结构化数据
sdk.env.set("server.config", {
    "host": "localhost",
    "port": 8080,
    "workers": 4
})

# 更新现有配置
current_settings = sdk.env.get("user.settings", {})
current_settings["last_login"] = datetime.now().isoformat()
sdk.env.set("user.settings", current_settings)
```

#### delete(key: str) -> bool
删除配置项。
- 参数:
  - key: 要删除的配置项键名
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 删除临时配置
sdk.env.delete("temp.session")

# 条件删除
if not is_feature_enabled():
    sdk.env.delete("feature.config")

# 清理旧配置
for key in sdk.env.get_all_keys():
    if key.startswith("deprecated."):
        sdk.env.delete(key)
```

#### get_all_keys() -> list[str]
获取所有配置项的键名。
- 参数: 无
- 返回:
  - list[str]: 所有配置项的键名列表
- 示例:
```python
# 列出所有配置
all_keys = sdk.env.get_all_keys()
print(f"当前有 {len(all_keys)} 个配置项")

# 按前缀过滤
user_keys = [k for k in sdk.env.get_all_keys() if k.startswith("user.")]
print(f"用户相关配置: {user_keys}")

# 导出配置摘要
config_summary = {}
for key in sdk.env.get_all_keys():
    parts = key.split(".")
    if len(parts) > 1:
        category = parts[0]
        if category not in config_summary:
            config_summary[category] = 0
        config_summary[category] += 1
print("配置分类统计:", config_summary)
```

### 批量操作
#### get_multi(keys: list) -> dict
批量获取多个配置项的值。
- 参数:
  - keys: 要获取的配置项键名列表
- 返回:
  - dict: 键值对字典，只包含存在的键
- 示例:
```python
# 批量获取配置
settings = sdk.env.get_multi([
    "app.name", 
    "app.version", 
    "app.debug"
])
print(f"应用: {settings.get('app.name')} v{settings.get('app.version')}")

# 获取相关配置组
db_keys = ["database.host", "database.port", "database.user", "database.password"]
db_config = sdk.env.get_multi(db_keys)
connection = create_db_connection(**db_config)

# 配置存在性检查
required_keys = ["api.key", "api.endpoint", "api.version"]
config = sdk.env.get_multi(required_keys)
missing = [k for k in required_keys if k not in config]
if missing:
    raise ValueError(f"缺少必要配置: {missing}")
```

#### set_multi(items: dict) -> bool
批量设置多个配置项的值。
- 参数:
  - items: 要设置的键值对字典
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 批量设置基本配置
sdk.env.set_multi({
    "app.name": "MyApp",
    "app.version": "1.0.0",
    "app.debug": True
})

# 更新系统设置
sdk.env.set_multi({
    "system.max_connections": 100,
    "system.timeout": 30,
    "system.retry_count": 3
})

# 从外部配置导入
import json
with open("config.json", "r") as f:
    external_config = json.load(f)
    
# 转换为扁平结构
flat_config = {}
for section, values in external_config.items():
    for key, value in values.items():
        flat_config[f"{section}.{key}"] = value
        
sdk.env.set_multi(flat_config)
```

#### delete_multi(keys: list) -> bool
批量删除多个配置项。
- 参数:
  - keys: 要删除的配置项键名列表
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 批量删除临时配置
temp_keys = [k for k in sdk.env.get_all_keys() if k.startswith("temp.")]
sdk.env.delete_multi(temp_keys)

# 删除特定模块的所有配置
module_keys = [k for k in sdk.env.get_all_keys() if k.startswith("module_name.")]
sdk.env.delete_multi(module_keys)

# 清理测试数据
test_keys = ["test.user", "test.data", "test.results"]
sdk.env.delete_multi(test_keys)
```

### 事务管理
#### transaction() -> contextmanager
创建事务上下文，确保多个操作的原子性。
- 参数: 无
- 返回:
  - contextmanager: 事务上下文管理器
- 示例:
```python
# 基本事务
with sdk.env.transaction():
    sdk.env.set("user.id", user_id)
    sdk.env.set("user.name", user_name)
    sdk.env.set("user.email", user_email)

# 带有条件检查的事务
def update_user_safely(user_id, new_data):
    with sdk.env.transaction():
        current = sdk.env.get(f"user.{user_id}", None)
        if not current:
            return False
            
        for key, value in new_data.items():
            sdk.env.set(f"user.{user_id}.{key}", value)
        
        sdk.env.set(f"user.{user_id}.updated_at", time.time())
    return True

# 复杂业务逻辑事务
def transfer_credits(from_user, to_user, amount):
    with sdk.env.transaction():
        # 检查余额
        from_balance = sdk.env.get(f"user.{from_user}.credits", 0)
        if from_balance < amount:
            raise ValueError("余额不足")
            
        # 更新余额
        sdk.env.set(f"user.{from_user}.credits", from_balance - amount)
        
        to_balance = sdk.env.get(f"user.{to_user}.credits", 0)
        sdk.env.set(f"user.{to_user}.credits", to_balance + amount)
        
        # 记录交易
        transaction_id = str(uuid.uuid4())
        sdk.env.set(f"transaction.{transaction_id}", {
            "from": from_user,
            "to": to_user,
            "amount": amount,
            "timestamp": time.time()
        })
```

### 快照管理
#### snapshot(name: str = None) -> str
创建数据库快照。
- 参数:
  - name: 快照名称，默认使用当前时间戳
- 返回:
  - str: 快照文件路径
- 示例:
```python
# 创建命名快照
sdk.env.snapshot("before_migration")

# 创建定期备份
def create_daily_backup():
    date_str = datetime.now().strftime("%Y%m%d")
    return sdk.env.snapshot(f"daily_{date_str}")

# 在重要操作前创建快照
def safe_operation():
    snapshot_path = sdk.env.snapshot("pre_operation")
    try:
        perform_risky_operation()
    except Exception as e:
        sdk.logger.error(f"操作失败: {e}")
        sdk.env.restore(snapshot_path)
        return False
    return True
```

#### restore(snapshot_name: str) -> bool
从快照恢复数据库。
- 参数:
  - snapshot_name: 快照名称或路径
- 返回:
  - bool: 恢复是否成功
- 示例:
```python
# 恢复到指定快照
success = sdk.env.restore("before_migration")
if success:
    print("成功恢复到之前的状态")
else:
    print("恢复失败")

# 回滚到最近的每日备份
def rollback_to_last_daily():
    snapshots = sdk.env.list_snapshots()
    daily_snapshots = [s for s in snapshots if s[0].startswith("daily_")]
    if daily_snapshots:
        latest = daily_snapshots[0]  # 列表已按时间排序
        return sdk.env.restore(latest[0])
    return False

# 灾难恢复
def disaster_recovery():
    snapshots = sdk.env.list_snapshots()
    if not snapshots:
        print("没有可用的快照")
        return False
        
    print("可用快照:")
    for i, (name, date, size) in enumerate(snapshots):
        print(f"{i+1}. {name} - {date} ({size/1024:.1f} KB)")
        
    choice = input("选择要恢复的快照编号: ")
    try:
        index = int(choice) - 1
        if 0 <= index < len(snapshots):
            return sdk.env.restore(snapshots[index][0])
    except ValueError:
        pass
    return False
```

#### list_snapshots() -> list
列出所有可用的快照。
- 参数: 无
- 返回:
  - list: 快照信息列表，每项包含(名称, 创建时间, 大小)
- 示例:
```python
# 列出所有快照
snapshots = sdk.env.list_snapshots()
print(f"共有 {len(snapshots)} 个快照")

# 显示快照详情
for name, date, size in snapshots:
    print(f"名称: {name}")
    print(f"创建时间: {date}")
    print(f"大小: {size/1024:.2f} KB")
    print("-" * 30)

# 查找特定快照
def find_snapshot(prefix):
    snapshots = sdk.env.list_snapshots()
    return [s for s in snapshots if s[0].startswith(prefix)]
```

#### delete_snapshot(name: str) -> bool
删除指定的快照。
- 参数:
  - name: 要删除的快照名称
- 返回:
  - bool: 删除是否成功
- 示例:
```python
# 删除指定快照
sdk.env.delete_snapshot("old_backup")

# 清理过期快照
def cleanup_old_snapshots(days=30):
    snapshots = sdk.env.list_snapshots()
    cutoff = datetime.now() - timedelta(days=days)
    for name, date, _ in snapshots:
        if date < cutoff:
            sdk.env.delete_snapshot(name)
            print(f"已删除过期快照: {name}")

# 保留最新的N个快照
def retain_latest_snapshots(count=5):
    snapshots = sdk.env.list_snapshots()
    if len(snapshots) > count:
        for name, _, _ in snapshots[count:]:
            sdk.env.delete_snapshot(name)
```

## 最佳实践

1. 配置组织
```python
# 使用层次结构组织配置
sdk.env.set("app.server.host", "localhost")
sdk.env.set("app.server.port", 8080)
sdk.env.set("app.database.url", "postgresql://localhost/mydb")

# 使用命名空间避免冲突
sdk.env.set("module1.config.timeout", 30)
sdk.env.set("module2.config.timeout", 60)
```

2. 事务使用
```python
# 确保数据一致性
def update_configuration(config_data):
    with sdk.env.transaction():
        # 验证
        for key, value in config_data.items():
            if not validate_config(key, value):
                raise ValueError(f"无效的配置: {key}")
                
        # 更新
        for key, value in config_data.items():
            sdk.env.set(key, value)
            
        # 记录更新
        sdk.env.set("config.last_updated", time.time())
```

3. 快照管理
```python
# 定期创建快照
def schedule_backups():
    # 每日快照
    if not sdk.env.snapshot(f"daily_{datetime.now().strftime('%Y%m%d')}"):
        sdk.logger.error("每日快照创建失败")
        
    # 清理旧快照
    cleanup_old_snapshots(days=30)
    
# 自动备份重要操作
def safe_bulk_update(updates):
    snapshot_name = f"pre_update_{time.time()}"
    sdk.env.snapshot(snapshot_name)
    
    try:
        with sdk.env.transaction():
            for key, value in updates.items():
                sdk.env.set(key, value)
    except Exception as e:
        sdk.logger.error(f"批量更新失败: {e}")
        sdk.env.restore(snapshot_name)
        raise
```

## logger (source: [ErisPulse/logger.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/logger.py))

# 日志系统

提供模块化、多级别的日志记录功能，支持内存存储和文件输出。实现了模块级别的日志控制、彩色输出和灵活的存储选项。

## API 文档

### 基本日志操作

以debug为例：
> 此外，还有其他级别的日志记录函数，如info, warning, error, critical等，用法相同。

debug(msg: str, *args, **kwargs) -> None

记录调试级别的日志信息。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None
- 示例:

```python
sdk.logger.debug("这是一条日志")
```

### 日志级别控制
#### set_level(level: str) -> None
设置全局日志级别。
- 参数:
  - level: 日志级别，可选值为 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
- 返回:
  - None
- 示例:
```python
# 设置为调试级别
sdk.logger.set_level("DEBUG")

# 设置为生产环境级别
sdk.logger.set_level("INFO")

# 根据环境设置日志级别
if is_production():
    sdk.logger.set_level("WARNING")
else:
    sdk.logger.set_level("DEBUG")
```

#### set_module_level(module_name: str, level: str) -> bool
设置特定模块的日志级别。
- 参数:
  - module_name: 模块名称
  - level: 日志级别，可选值为 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
- 返回:
  - bool: 设置是否成功
- 示例:
```python
# 为特定模块设置详细日志
sdk.logger.set_module_level("NetworkModule", "DEBUG")

# 为敏感模块设置更高级别
sdk.logger.set_module_level("AuthModule", "WARNING")

# 根据配置设置模块日志级别
for module, level in config.get("logging", {}).items():
    success = sdk.logger.set_module_level(module, level)
    if not success:
        print(f"无法为模块 {module} 设置日志级别 {level}")
```

### 日志存储和输出
#### set_output_file(path: str | list) -> None
设置日志输出文件。
- 参数:
  - path: 日志文件路径，可以是单个字符串或路径列表
- 返回:
  - None
- 异常:
  - 如果无法设置日志文件，会抛出异常
- 示例:
```python
# 设置单个日志文件
sdk.logger.set_output_file("app.log")

# 设置多个日志文件
sdk.logger.set_output_file(["app.log", "debug.log"])

# 使用日期命名日志文件
from datetime import datetime
log_file = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
sdk.logger.set_output_file(log_file)
```

#### save_logs(path: str | list) -> None
保存内存中的日志到文件。
- 参数:
  - path: 保存路径，可以是单个字符串或路径列表
- 返回:
  - None
- 异常:
  - 如果无法保存日志，会抛出异常
- 示例:
```python
# 保存到单个文件
sdk.logger.save_logs("saved_logs.txt")

# 保存到多个文件
sdk.logger.save_logs(["main_log.txt", "backup_log.txt"])

# 在应用退出前保存日志
import atexit
atexit.register(lambda: sdk.logger.save_logs("final_logs.txt"))
```

## raiserr (source: [ErisPulse/raiserr.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/raiserr.py))

# 错误管理系统

提供错误类型注册、抛出和管理功能，集成全局异常处理。支持自定义错误类型、错误链追踪和全局异常捕获。

## API 文档

### 错误注册
#### register(name: str, doc: str = "", base: type = Exception) -> type
注册新的错误类型。
- 参数:
  - name: 错误类型名称
  - doc: 错误描述文档
  - base: 基础异常类，默认为Exception
- 返回:
  - type: 注册的错误类型类
- 示例:
```python
# 注册一个简单错误
sdk.raiserr.register("SimpleError", "简单的错误类型")

# 注册带有自定义基类的错误
class CustomBase(Exception):
    pass
sdk.raiserr.register("AdvancedError", "高级错误", CustomBase)
```

#### info(name: str = None) -> dict | None
获取错误类型信息。
- 参数:
  - name: 错误类型名称，如果为None则返回所有错误类型信息
- 返回:
  - dict: 包含错误类型信息的字典，包括类型名、文档和类引用
  - None: 如果指定的错误类型不存在
- 示例:
```python
# 获取特定错误信息
error_info = sdk.raiserr.info("SimpleError")
print(f"错误类型: {error_info['type']}")
print(f"错误描述: {error_info['doc']}")

# 获取所有注册的错误信息
all_errors = sdk.raiserr.info()
for name, info in all_errors.items():
    print(f"{name}: {info['doc']}")
```

### 错误抛出
#### ErrorType(msg: str, exit: bool = False)
动态生成的错误抛出函数。
- 参数:
  - msg: 错误消息
  - exit: 是否在抛出错误后退出程序
- 示例:
```python
# 抛出不退出的错误
sdk.raiserr.SimpleError("操作失败")

# 抛出导致程序退出的错误
sdk.raiserr.CriticalError("致命错误", exit=True)

# 带有异常捕获的使用方式
try:
    sdk.raiserr.ValidationError("数据验证失败")
except Exception as e:
    print(f"捕获到错误: {e}")
```

## util (source: [ErisPulse/util.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/util.py))

# 工具函数集合

提供各种实用工具函数和装饰器，简化开发流程。

## API 文档
### 拓扑排序：
    - topological_sort(elements, dependencies, error): 拓扑排序依赖关系
    - show_topology(): 可视化模块依赖关系

### 装饰器：
    - @cache: 缓存函数结果
    - @run_in_executor: 将同步函数转为异步
    - @retry(max_attempts=3, delay=1): 失败自动重试

### 异步执行：
    - ExecAsync(async_func, *args, **kwargs): 异步执行函数

### 示例用法：

```
from ErisPulse import sdk

# 拓扑排序
sorted_modules = sdk.util.topological_sort(modules, dependencies, error)

# 缓存装饰器
@sdk.util.cache
def expensive_operation(param):
    return heavy_computation(param)
    
# 异步执行
@sdk.util.run_in_executor
def sync_task():
    pass
    
# 重试机制
@sdk.util.retry(max_attempts=3, delay=1)
def unreliable_operation():
    pass
```



<!--- End of REFERENCE.md -->

<!-- ADAPTERS.md -->

# ErisPulse Adapter 文档

## 简介
ErisPulse 的 Adapter 系统旨在为不同的通信协议提供统一事件处理机制。目前支持的主要适配器包括：

- **TelegramAdapter**
- **OneBotAdapter**
- **YunhuAdapter**

每个适配器都实现了标准化的事件映射、消息发送方法和生命周期管理。以下将详细介绍现有适配器的功能、支持的方法以及推荐的开发实践。

---

## 适配器功能概述

### 1. YunhuAdapter
YunhuAdapter 是基于云湖协议构建的适配器，整合了所有云湖功能模块，提供统一的事件处理和消息操作接口。

#### 支持的事件类型

| 官方事件命名                  | 映射名称       | 说明                     |
|-------------------------------|----------------|--------------------------|
| `message.receive.normal`      | `message`      | 普通消息                 |
| `message.receive.instruction` | `command`      | 指令消息                 |
| `bot.followed`                | `follow`       | 用户关注机器人           |
| `bot.unfollowed`              | `unfollow`     | 用户取消关注机器人       |
| `group.join`                  | `group_join`   | 用户加入群组             |
| `group.leave`                 | `group_leave`  | 用户离开群组             |
| `button.report.inline`        | `button_click` | 按钮点击事件             |
| `bot.shortcut.menu`           | `shortcut_menu`| 快捷菜单触发事件         |

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
await yunhu.Send.To("user", user_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str, buttons: List = None)`：发送纯文本消息，可选添加按钮。
- `.Html(html: str, buttons: List = None)`：发送HTML格式消息。
- `.Markdown(markdown: str, buttons: List = None)`：发送Markdown格式消息。
- `.Image(file: bytes, buttons: List = None)`：发送图片消息。
- `.Video(file: bytes, buttons: List = None)`：发送视频消息。
- `.File(file: bytes, buttons: List = None)`：发送文件消息。
- `.Batch(target_ids: List[str], message: str)`：批量发送消息。
- `.Edit(msg_id: str, text: str)`：编辑已有消息。
- `.Recall(msg_id: str)`：撤回消息。
- `.Board(board_type: str, content: str, **kwargs)`：发布公告看板。
- `.Stream(content_type: str, generator: AsyncGenerator)`：发送流式消息。

#### 按钮参数说明
`buttons` 参数是一个嵌套列表，表示按钮的布局和功能。每个按钮对象包含以下字段：

| 字段         | 类型   | 是否必填 | 说明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | 按钮上的文字                                                         |
| `actionType` | int    | 是       | 动作类型：<br>`1`: 跳转 URL<br>`2`: 复制<br>`3`: 点击汇报            |
| `url`        | string | 否       | 当 `actionType=1` 时使用，表示跳转的目标 URL                         |
| `value`      | string | 否       | 当 `actionType=2` 时，该值会复制到剪贴板<br>当 `actionType=3` 时，该值会发送给订阅端 |

示例：
```python
buttons = [
    [
        {"text": "复制", "actionType": 2, "value": "xxxx"},
        {"text": "点击跳转", "actionType": 1, "url": "http://www.baidu.com"}
    ]
]
await yunhu.Send.To("user", user_id).Text("带按钮的消息", buttons=buttons)
```

#### env.py 配置示例
```python
sdk.env.set("YunhuAdapter", {
    "token": "",       # 机器人 Token
    "mode": "server",  # server / polling (polling使用社区脚本支持)
    "server": {
        "host": "0.0.0.0",
        "port": 25888,
        "path": "/yunhu/webhook"
    },
    "polling": {
        "url": "https://example.com/",
    }
})
```
> **注意：**
> - 云湖适配器使用 `server` 模式时，需要配置 `server` 字段；使用 `polling` 模式时，需要配置 `polling` 字段。
> - 云湖需要在控制台指向我们开启的 `server` 地址，否则无法正常接收消息。

#### 数据格式示例
云湖目前有9种事件会推送给机器人：

|事件字段名称|事件用途|
|:---:|:---:|
|message.receive.normal|普通消息|
|message.receive.instruction|指令消息|
|group.join|用户加群|
|group.leave|用户退群|
|bot.followed|机器人关注|
|bot.unfollowed|机器人取关|
|bot.shortcut.menu|快捷菜单|
|button.report.inline|按钮汇报|
|bot.setting|机器人设置|

每个事件的触发条件以及数据结构如下：

##### 普通消息事件
当用户向机器人或机器人所在的群聊发送消息，且没有选择指令时，将会触发该事件。
```json
{
  "version": "1.0",
  "header": 
    "eventId": "c192ccc83d5147f2859ca77bcfafc9f9",
    "eventType": "message.receive.normal",
    "eventTime": 1748613099002
  }
  "event": {
    "sender": 
      "senderId": "6300451",
      "senderType": "user",
      "senderUserLevel": "owner",
      "senderNickname": "ShanFish"
    },
    "chat": {
      "chatId": "49871624",
      "chatType": "bot"
    },
    "message": {
      "msgId": "5c887bc0a82244c7969c08000f5b3ae8",
      "parentId": "",
      "sendTime": 1748613098989,
      "chatId": "49871624",
      "chatType": "bot",
      "contentType": "text",
      "content": {
        "text": "你好"
      },
      "instructionId": 0,
      "instructionName": "",
      "commandId": 0,
      "comandName": ""
    }
  }
}
```
##### 指令消息事件
当用户点击聊天栏的"/"图标时，将列出该机器人/群聊可用的所有指令。用户发送带有指令的消息后，将会触发该事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "ee74aded326b4578959073fe88f0076a",
        "eventType": "message.receive.instruction",
        "eventTime": 1749442433069
    },
    "event": {
        "sender": {
            "senderId": "6300451",
            "senderType": "user",
            "senderUserLevel": "owner",
            "senderNickname": "ShanFish"
        },
        "chat": {
            "chatId": "49871624",
            "chatType": "bot"
        },
        "message": {
            "msgId": "1d879c6ec68c4c52b78f87d83084955e",
            "parentId": "",
            "sendTime": 1749442433057,
            "chatId": "49871624",
            "chatType": "bot",
            "contentType": "text",
            "content": {
                "text": "/抽奖信息",
                "menu": {}
            },
            "instructionId": 1505,
            "instructionName": "抽奖信息",
            "commandId": 1505,
            "commandName": "抽奖信息"
        }
    }
}
```
##### 用户加群事件
当用户加入机器人所在的群聊后，将会触发该事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "d5429cb5e4654fbcaeee9e4adb244741",
        "eventType": "group.join",
        "eventTime": 1749442891943
    },
    "event": {
        "time": 1749442891843,
        "chatId": "985140593",
        "chatType": "group",
        "userId": "3707697",
        "nickname": "ShanFishApp",
        "avatarUrl": "https://chat-storage1.jwznb.com/defalut-avatars/Ma%20Rainey.png?sign=b19c8978f4e0d9e43a8aec4f1e3c82ef&t=68466f5b"
    }
}
```
##### 用户退群事件
```json
{
    "version": "1.0",
    "header": {
        "eventId": "06959e95aaf547078367104ba754c554",
        "eventType": "group.leave",
        "eventTime": 1749442644367
    },
    "event": {
        "time": 1749442644343,
        "chatId": "985140593",
        "chatType": "group",
        "userId": "3707697",
        "nickname": "ShanFishApp",
        "avatarUrl": "https://chat-storage1.jwznb.com/defalut-avatars/Ma%20Rainey.png?sign=92fdef22a240a05de78b13afdab5ac51&t=68466e64"
    }
}
```
##### 用户关注机器人事件
当用户在机器人ID或机器人推荐处添加机器人后，将会触发该事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "3fe280a400f9460daa03a642d1fad39b",
        "eventType": "bot.followed",
        "eventTime": 1749443049592
    },
    "event": {
        "time": 1749443049580,
        "chatId": "49871624",
        "chatType": "bot",
        "userId": "3707697",
        "nickname": "ShanFishApp",
        "avatarUrl": "https://chat-storage1.jwznb.com/defalut-avatars/Ma%20Rainey.png?sign=33bb173f1b22ed0e44da048b175767c6&t=68466ff9"
    }
}
```
##### 用户取关机器人事件
当用户点击删除机器人按钮后，将会触发该事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "b4f51386d916464b99782052c030c5b7",
        "eventType": "bot.unfollowed",
        "eventTime": 1749443036382
    },
    "event": {
        "time": 1749443036373,
        "chatId": "49871624",
        "chatType": "bot",
        "userId": "3707697",
        "nickname": "ShanFishApp",
        "avatarUrl": "https://chat-storage1.jwznb.com/defalut-avatars/Ma%20Rainey.png?sign=07cf8e9d6ca0875835f9a4a6811b6b4c&t=68466fec"
    }
}
```
##### 按钮汇报事件
机器人可以发送带按钮的消息。当用户按下按钮actionType为3(汇报类按钮)的按钮时，将会触发该事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "0d6d269ff7f046828c8562f905f9ee08",
        "eventType": "button.report.inline",
        "eventTime": 1749446185273
    },
    "event": {
        "time": 1749446185268,
        "msgId": "1838c3dd84474e9e9e1e00ca64e72065",
        "recvId": "6300451",
        "recvType": "user",
        "userId": "6300451",
        "value": "xxxx"
    }
}
```

##### 快捷菜单事件
当用户点击了开发者自行配置的快捷菜单时，且该快捷菜单类型为普通菜单，将会触发本事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "93d0e36ce0334da58448409fd0527590",
        "eventType": "bot.shortcut.menu",
        "eventTime": 1749445822197
    },
    "event": {
        "botId": "49871624",
        "menuId": "HNH1LDHF",
        "menuType": 1,
        "menuAction": 1,
        "chatId": "985140593",
        "chatType": "group",
        "senderType": "user",
        "senderId": "6300451",
        "sendTime": 1749445822
    }
}

```
##### 机器人设置事件
当开发者配置了机器人设置项时，在机器人列表处将会出现"设置"按钮。用户设置完成后，将会触发本事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "5ad7e23399ef46a685cead1abe2efa19",
        "eventType": "bot.setting",
        "eventTime": 1749446299131
    },
    "event": {
        "time": 1749446299128,
        "chatId": "49871624",
        "chatType": "bot",
        "groupId": "985140593",
        "groupName": "云湖测试群",
        "avatarUrl": "https://chat-img.jwznb.com/77db590d9cee77de13e7c8cf0887b5ba.jpg",
        "settingJson": {
            "wezzrm": {
                "id": "wezzrm",
                "type": "switch",
                "label": "测试",
                "value": true
            }
        }
    }
}

```

#### 注意：`chat` 与 `sender` 的误区

##### 常见问题：

| 字段 | 含义 |
|------|------|
| `data.event.chatType` | 当前聊天类型（`user`/`bot` 或 `group`） |
| `data.event.sender.senderType` | 发送者类型（通常为 `user`） |
| `data.event.sender.senderId` | 发送者唯一 ID |

> **注意：**  
> - 使用 `chatType` 判断消息是私聊还是群聊  
> - 群聊使用 `chatId`，私聊使用 `senderId` 作为目标地址  
> - `senderType` 通常为 `"user"`，不能用于判断是否为群消息  

---

##### 示例代码：

```python
@sdk.adapter.Yunhu.on("message")
async def handle_message(data):
    if data.event.chatType == "group":
        targetId = data.event.chat.chatId
        targeType = "group"
    else:
        targetId = data.event.sender.senderId
        targeType = "user"

    await sdk.adapter.Yunhu.Send.To(targeType, targetId).Text("收到你的消息！")
```

---

### 2. TelegramAdapter
TelegramAdapter 是基于 Telegram Bot API 构建的适配器，支持多种消息类型和事件处理。

#### 支持的事件类型

| Telegram 原生事件       | 映射名称           | 说明                     |
|-------------------------|--------------------|--------------------------|
| `message`               | `message`          | 普通消息                 |
| `edited_message`        | `message_edit`     | 消息被编辑               |
| `channel_post`          | `channel_post`     | 频道发布消息             |
| `edited_channel_post`   | `channel_post_edit`| 频道消息被编辑           |
| `inline_query`          | `inline_query`     | 内联查询                 |
| `chosen_inline_result`  | `chosen_inline_result` | 内联结果被选择       |
| `callback_query`        | `callback_query`   | 回调查询（按钮点击）     |
| `shipping_query`        | `shipping_query`   | 配送信息查询             |
| `pre_checkout_query`    | `pre_checkout_query` | 支付预检查询           |
| `poll`                  | `poll`             | 投票创建                 |
| `poll_answer`           | `poll_answer`      | 投票响应                 |

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
await telegram.Send.To("user", user_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: bytes, caption: str = "")`：发送图片消息。
- `.Video(file: bytes, caption: str = "")`：发送视频消息。
- `.Audio(file: bytes, caption: str = "")`：发送音频消息。
- `.Document(file: bytes, caption: str = "")`：发送文件消息。
- `.EditMessageText(message_id: int, text: str)`：编辑已有消息。
- `.DeleteMessage(message_id: int)`：删除指定消息。
- `.GetChat()`：获取聊天信息。

#### env.py 配置示例
```python
sdk.env.set("TelegramAdapter", {
    # 必填：Telegram Bot Token
    "token": "YOUR_BOT_TOKEN",

    # Webhook 模式下的服务配置（如使用 webhook）
    "server": {
        "host": "127.0.0.1",            # 推荐监听本地，防止外网直连
        "port": 8443,                   # 监听端口
        "path": "/telegram/webhook"     # Webhook 路径
    },
    "webhook": {
        "host": "example.com",          # Telegram API 监听地址（外部地址）
        "port": 8443,                   # 监听端口
        "path": "/telegram/webhook"     # Webhook 路径
    }

    # 启动模式: webhook 或 polling
    "mode": "webhook",

    # 可选：代理配置（用于连接 Telegram API）
    "proxy": {
        "host": "127.0.0.1",
        "port": 1080,
        "type": "socks5"  # 支持 socks4 / socks5
    }
})
```

#### 数据格式示例
> 略: 使用你了解的 TG 事件数据格式即可,这里不进行演示

---

### 3. OneBotAdapter
OneBotAdapter 是基于 OneBot V11 协议构建的适配器，适用于与 go-cqhttp 等服务端交互。

#### 支持的事件类型

| OneBot 原生事件       | 映射名称           | 说明                     |
|-----------------------|--------------------|--------------------------|
| `message`             | `message`          | 消息事件                 |
| `notice`              | `notice`           | 通知类事件（如群成员变动）|
| `request`             | `request`          | 请求类事件（如加群请求） |
| `meta_event`          | `meta_event`       | 元事件（如心跳包）       |

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
await onebot.Send.To("group", group_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: str)`：发送图片消息（支持 URL 或 Base64）。
- `.Voice(file: str)`：发送语音消息。
- `.Video(file: str)`：发送视频消息。
- `.Raw(message_list: List[Dict])`：发送原生 OneBot 消息结构。
- `.Recall(message_id: int)`：撤回消息。
- `.Edit(message_id: int, new_text: str)`：编辑消息。
- `.Batch(target_ids: List[str], text: str)`：批量发送消息。

#### env.py 配置示例
```python
sdk.env.set("OneBotAdapter", {
    "mode": "client", # 或者 "server"
    "server": {
        "host": "127.0.0.1",
        "port": 8080,
        "path": "/",
        "token": ""
    },
    "client": {
        "url": "ws://127.0.0.1:3001",
        "token": ""
    }
})
```

#### 数据格式示例
> 略: 使用你了解的 OneBot v11 事件数据格式即可,这里不进行演示

---

## 生命周期管理

### 启动适配器
```python
await sdk.adapter.startup()
```
此方法会根据配置启动适配器，并初始化必要的连接。

### 关闭适配器
```python
await sdk.adapter.shutdown()
```
确保资源释放，关闭 WebSocket 连接或其他网络资源。

---

## 开发者指南

### 如何编写新的 Adapter
1. **继承 BaseAdapter**  
   所有适配器需继承 `sdk.BaseAdapter` 类，并实现以下方法：
   - `start()`：启动适配器。
   - `shutdown()`：关闭适配器。
   - `call_api(endpoint: str, **params)`：调用底层 API。

2. **定义 Send 方法**  
   使用链式语法实现消息发送逻辑，推荐参考现有适配器的实现。

3. **注册事件映射**  
   在 `_setup_event_mapping()` 方法中定义事件映射表。

4. **测试与调试**  
   编写单元测试验证适配器的功能完整性，并在不同环境下进行充分测试。

### 推荐的文档结构
新适配器的文档应包含以下内容：
- **简介**：适配器的功能和适用场景。
- **事件映射表**：列出支持的事件及其映射名称。
- **发送方法**：详细说明支持的消息类型和使用示例。
- **数据格式**：展示典型事件的 JSON 数据格式。
- **配置说明**：列出适配器所需的配置项及默认值。
- **注意事项**：列出开发和使用过程中需要注意的事项。

---

## 参考链接
ErisPulse 项目：
- [主库](https://github.com/ErisPulse/ErisPulse/)
- [ErisPulse Yunhu 适配器库](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [ErisPulse Telegram 适配器库](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [ErisPulse OneBot 适配器库](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

官方文档：
- [OneBot V11 协议文档](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 官方文档](https://core.telegram.org/bots/api)
- [云湖官方文档](https://www.yhchat.com/document/1-3)

---

## 参与贡献

我们欢迎更多开发者参与编写和维护适配器文档！请按照以下步骤提交贡献：
1. Fork [ErisPuls](https://github.com/ErisPulse/ErisPulse) 仓库。
2. 在 `docs/` 目录下找到 ADAPTER.md 适配器文档。
3. 提交 Pull Request，并附上详细的描述。

感谢您的支持！

<!--- End of ADAPTERS.md -->

<!-- CLI.md -->

# ErisPulse CLI 命令手册

## 模块管理
**说明**：
- `--init`参数：执行命令前先初始化模块状态
- 支持通配符批量启用/禁用/安装/卸载模块

| 命令       | 参数                      | 描述                                  | 示例                          |
|------------|---------------------------|---------------------------------------|-------------------------------|
| `enable`   | `<module> [--init]`       | 激活指定模块                          | `epsdk enable chatgpt --init`       |
| `disable`  | `<module> [--init]`       | 停用指定模块                          | `epsdk disable weather`             |
| `list`     | `[--module=<name>] [--init]` | 列出模块（可筛选）                   | `epsdk list --module=payment`       |
| `update`   | -                         | 更新模块索引                           | `epsdk update`                      |
| `upgrade`  | `[--force] [--init]`      | 升级模块（`--force` 强制覆盖）        | `epsdk upgrade --force --init`      |
| `install`  | `<module...> [--init]`    | 安装一个或多个模块（空格分隔），支持本地目录路径 | `epsdk install YunhuAdapter OpenAI`<br>`epsdk install .`<br>`epsdk install /path/to/module` |
| `uninstall`| `<module> [--init]`       | 移除指定模块                          | `epsdk uninstall old-module --init` |
| `init`    | -                         | 初始化sdk | `epsdk init`                        |
| `run` | `<script> [--reload]` | 运行指定脚本（支持热重载） | `epsdk run main.py --reload` |

## 源管理
| 命令 | 参数 | 描述 | 示例 |
|------|------|------|------|
| `origin add` | `<url>` | 添加源 | `epsdk origin add https://erisdev.com/map.json` |
| `origin list` | - | 源列表 | `epsdk origin list` |
| `origin del` | `<url>` | 删除源 | `epsdk origin del https://erisdev.com/map.json` |

---

## 反馈与支持
如遇到 CLI 使用问题，请在 GitHub Issues 提交反馈。

<!--- End of CLI.md -->

