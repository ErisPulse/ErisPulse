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
