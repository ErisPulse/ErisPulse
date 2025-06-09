# ErisPulse 开发者指南

> 本指南从开发者角度出发，帮助你快速理解并接入 **ErisPulse** 框架，进行模块和适配器的开发。

---

## 一、模块开发

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
        "optional": [],       # 可选依赖模块列表（满足其中一个即可）
        "pip": []             # 第三方 pip 包依赖
    }
}

from .Core import Main
```

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
```

- 所有 SDK 提供的功能都可通过 `sdk` 对象访问。
- 不需要注册适配器。

---

### 4. 使用 SDK 功能

#### 日志记录：

```python
self.logger.debug("调试信息")
self.logger.info("运行状态")
self.logger.warning("警告信息")
self.logger.error("错误信息")
```

#### 获取配置项：

```python
config_value = self.env.get("my_config_key", "default_value")
```

#### 设置配置项：

```python
self.env.set("my_config_key", "new_value")
```

#### 注册自定义错误类型：

```python
self.raiserr.register("MyCustomError", doc="这是一个自定义错误")

self.raiserr.MyCustomError("发生了一个错误")
```

#### 工具函数：

```python
@self.util.retry(max_attempts=3, delay=1)
async def my_retry_function():
    ...
```

---

### 5. 模块间通信

通过 `sdk.<ModuleName>` 访问其他模块实例：

```python
other_module = self.sdk.OtherModule
result = other_module.some_method()
```

---

## 二、平台适配器开发（Adapter）

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

from .Core import Main
```

### 3. `Core.py`
实现适配器主类 `Main`，并提供适配器类继承 `sdk.BaseAdapter`：

```python
from ErisPulse import sdk

class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger

    def register_adapters(self):
        return {
            "myplatform": MyPlatformAdapter
        }

class MyPlatformAdapter(sdk.BaseAdapter):
    class Send(sdk.SendDSL):
        def Text(self, text: str):
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )

    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError()

    async def start(self):
        raise NotImplementedError()

    async def shutdown(self):
        raise NotImplementedError()
```

> ⚠️ 注意：
> - 适配器类必须继承 `sdk.BaseAdapter`；
> - 必须实现 `call_api`, `start`, `shutdown` 方法；
> - 推荐实现 `.Text(...)` 方法作为基础消息发送接口。

---

### 4. DSL 风格消息接口（SendDSL）

每个适配器可定义一组链式调用风格的方法，例如：

```python
class Send(sdk.SendDSL):
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

### 5. BaseAdapter 接口规范

适配器必须继承 `BaseAdapter` 并实现以下方法：

| 方法 | 描述 |
|------|------|
| `call_api(endpoint: str, **params)` | 调用平台 API |
| `start()` | 启动适配器 |
| `shutdown()` | 关闭适配器资源 |

可选实现：

| 方法 | 描述 |
|------|------|
| `on(event_type: str)` | 注册事件处理器 |
| `middleware(func: Callable)` | 添加中间件处理传入数据 |
| `emit(event_type: str, data: Any)` | 自定义事件分发逻辑 |

---

## 三、模块元信息（moduleInfo）说明

所有模块都必须提供 `moduleInfo` 字典，其结构如下：

```python
moduleInfo = {
    "meta": {
        "name": "模块名称",         # 唯一标识符
        "version": "版本号",         # 版本信息
        "description": "模块描述",   # 功能简介
        "author": "作者",            # 开发者或团队
        "license": "许可协议",       # 如 MIT
        "homepage": "项目主页"       # 可选
    },
    "dependencies": {
        "requires": ["模块A", "模块B"],     # 必须依赖的模块
        "optional": [["模块C", "模块D"]],   # 至少满足其中一项
        "pip": ["requests", "some-library"]  # pip 安装依赖
    }
}
```

---

## 四、SDK 提供的核心对象

| 名称 | 用途 |
|------|------|
| `sdk.env` | 获取/设置全局配置 |
| `sdk.mods` | 管理模块 |
| `sdk.logger` | 日志记录器 |
| `sdk.raiserr` | 错误管理器 |
| `sdk.util` | 工具函数（缓存、重试等） |
| `sdk.adapter` | 获取其他适配器实例 |
| `sdk.BaseAdapter` | 适配器基类 |
| `sdk.SendDSL` | 消息发送接口模板 |

---

## 五、开发建议

- 所有消息方法推荐使用首字母大写（如 `Text`, `Image`）；
- 所有 `.Send.*()` 方法应返回 `asyncio.Task`，以便异步调用；
- 在 `call_api` 中做好异常捕获与日志记录；
- 若涉及上传操作，封装为 `_upload_file_and_call_api` 更好；
- 避免同步阻塞操作，优先使用异步库（如 `aiohttp`）；

---

## 六、示例代码

### 示例：最小化模块

```python
# Core.py
class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
        self.logger.info("Hello from MyModule")
```

### 示例：最小化适配器

```python
# Core.py
from ErisPulse import sdk

class Main:
    def __init__(self, sdk):
        self.sdk = sdk

    def register_adapters(self):
        return {
            "myplatform": MyAdapter
        }

class MyAdapter(sdk.BaseAdapter):
    class Send(sdk.SendDSL):
        def Text(self, text: str):
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )

    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError("请实现具体的 API 调用逻辑")

    async def start(self):
        self.logger.info("适配器启动")

    async def shutdown(self):
        self.logger.info("适配器关闭")
```

---

## 七、提交到官方源

如果你希望将你的模块或适配器加入 ErisPulse 官方模块仓库，请参考 [模块源贡献](https://github.com/ErisPulse/ErisPulse-ModuleRepo)。

---

> ⚠️ 本文档仅关注开发实践，完整的 API 文档请参考[ErisPulse 方法与接口文档](docs/REFERENCE.md)