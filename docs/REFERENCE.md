# ErisPulse 方法与接口文档

本文件详细说明 ErisPulse 框架的主要方法、API 入口、模块接口规范及常用调用方式。

---

## 目录

- [ErisPulse 方法与接口文档](#erispulse-方法与接口文档)
  - [目录](#目录)
  - [1. SDK 入口对象](#1-sdk-入口对象)
  - [2. 初始化方法 `sdk.init()`](#2-初始化方法-sdkinit)
  - [3. 日志记录器 (Logger)](#3-日志记录器-logger)
    - [模块级日志控制](#模块级日志控制)
    - [输出与保存日志](#输出与保存日志)
  - [4. 环境配置管理 (Env)](#4-环境配置管理-env)
  - [5. 错误处理 (Raiserr)](#5-错误处理-raiserr)
  - [6. 工具函数 (Util)](#6-工具函数-util)
    - [示例：](#示例)
  - [7. 模块系统 (Mods)](#7-模块系统-mods)
    - [获取模块信息：](#获取模块信息)
  - [8. 适配器系统 (Adapter)](#8-适配器系统-adapter)
    - [BaseAdapter 接口规范](#baseadapter-接口规范)
      - [必须实现的方法：](#必须实现的方法)
      - [可选重写的方法：](#可选重写的方法)
  - [9. DSL 风格消息发送接口（SendDSL）](#9-dsl-风格消息发送接口senddsl)
    - [定义消息类型](#定义消息类型)
    - [必须实现的方法：Text(...)](#必须实现的方法text)
    - [可选推荐方法](#可选推荐方法)
    - [内部工作原理简析](#内部工作原理简析)
    - [自定义扩展示例：Card(...) 消息](#自定义扩展示例card-消息)
    - [开发者建议](#开发者建议)
  - [10. 模块开发基础](#10-模块开发基础)
    - [目录结构](#目录结构)
    - [moduleInfo 字典](#moduleinfo-字典)
    - [Main 类](#main-类)
  - [11. 模块间通信](#11-模块间通信)
  - [12. 伪指针特性](#12-伪指针特性)

---

## 1. SDK 入口对象

通过 sdk 对象访问核心功能：

```python
from ErisPulse import sdk

sdk.env         # 环境配置管理
sdk.mods        # 模块管理器
sdk.util        # 工具函数和装饰器
sdk.logger      # 日志记录器
sdk.raiserr     # 内置错误管理器
sdk.adapter     # 平台适配器注册中心
sdk.BaseAdapter # 适配器基类
sdk.SendDSL     # DSL 发送消息接口
```

> 所有模块都可通过 `sdk.<ModuleName>.<Method>` 的方式调用。

---

## 2. 初始化方法 `sdk.init()`

在启动项目前，需调用 `sdk.init()` 来加载所有模块：

```python
from ErisPulse import sdk
sdk.init()
```

此方法会自动完成以下操作：
- 加载 `env.py` 中的配置；
- 注册模块；
- 解析依赖；
- 注册适配器（若有）；
- 实例化模块。

---

## 3. 日志记录器 (Logger)

通过 `sdk.logger` 提供日志功能，支持多种日志级别：

```python
sdk.logger.debug(Msg)       # 调试信息
sdk.logger.info(Msg)        # 运行状态
sdk.logger.warning(Msg)     # 警告信息
sdk.logger.error(Msg)       # 错误信息
sdk.logger.critical(Msg)    # 致命错误
```

### 模块级日志控制

可为每个模块设置独立日志等级：

```python
sdk.logger.set_module_level("模块名", "DEBUG")
```

### 输出与保存日志

支持输出到文件和手动保存日志：

```python
sdk.logger.set_output_file(["日志1.log", "日志2.log"])  # 设置输出路径
sdk.logger.save_logs(["日志1.log", "日志2.log"])        # 保存当前日志
```

---

## 4. 环境配置管理 (Env)

通过 `sdk.env` 实现全局配置的动态读写：

```python
sdk.env.get(Key, [DefValue])     # 获取配置项
sdk.env.set(Key, Value)          # 设置配置项
sdk.env.delete(Key)              # 删除配置项
sdk.env.clear()                  # 清空配置
sdk.env.load_env_file()          # 从 env.py 加载配置
```

---

## 5. 错误处理 (Raiserr)

通过 `sdk.raiserr` 统一注册和抛出模块错误：

```python
sdk.raiserr.register("CustomError", doc="自定义错误描述")  # 注册错误类型
sdk.raiserr.CustomError("发生了自定义错误", exit=False)      # 抛出错误
```

- `exit=True` 表示抛出异常并中断程序。
- `exit=False` 仅记录日志，不中断程序。

---

## 6. 工具函数 (Util)

提供常用工具函数和装饰器：

- `ExecAsync(async_func, *args, **kwargs)`：异步执行函数
- `@cache`：缓存函数结果
- `@run_in_executor`：将同步函数包装为异步
- `@retry(max_attempts=3, delay=1)`：失败重试机制

### 示例：

```python
import asyncio
from ErisPulse import util

@util.retry(max_attempts=3, delay=1)
async def unreliable_operation():
    raise Exception("模拟失败")

try:
    await unreliable_operation()
except:
    print("操作失败")
```

---

## 7. 模块系统 (Mods)

模块管理系统负责模块的加载、卸载、依赖解析等。

### 获取模块信息：

```python
sdk.mods.get_module("模块名")               # 获取模块元信息
sdk.mods.get_all_modules()                 # 获取所有模块
sdk.mods.set_module_status("模块名", True)  # 启用/禁用模块
```

---

## 8. 适配器系统 (Adapter)

适配器用于对接不同平台的消息协议（如 Yunhu、OneBot）。适配器必须继承 `BaseAdapter` 并实现其接口。

### BaseAdapter 接口规范

```python
class MyAdapter(sdk.BaseAdapter):
    class Send(sdk.SendDSL):
        def Text(self, text: str): ...
        def Image(self, file: bytes): ...

    async def call_api(self, endpoint: str, **params): ...
    async def start(self): ...
    async def shutdown(self): ...
    async def emit(self, event_type: str, data: Any): ...
```

#### 必须实现的方法：

- `call_api(endpoint: str, **params)`：调用平台 API
- `start()`：启动适配器
- `shutdown()`：关闭适配器
- `emit(event_type: str, data: Any)`：事件分发逻辑

#### 可选重写的方法：

- `on(event_type: str)`：注册事件处理器(装饰器)
- `add_handler(event_type: str, handler: Callable)/remove_handler(handler: Callable)`: 添加事件处理器
- `middleware(func: Callable)`：添加中间件

---

## 9. DSL 风格消息发送接口（SendDSL）

DSL 风格的消息发送接口是 ErisPulse 的核心设计之一，它不仅提升了代码可读性，还简化了多平台适配器的开发流程。

### 定义消息类型

每个平台适配器需继承 `sdk.SendDSL` 并在其内部定义所需的消息方法：

```python
class YunhuAdapter(sdk.BaseAdapter):
    class Send(sdk.SendDSL):
        def Text(self, text: str, buttons: List = None, parent_id: str = ""):
            return asyncio.create_task(
                self._adapter.call_api(...)
            )

        def Image(self, file: bytes):
            return asyncio.create_task(
                self._upload_file_and_call_api(...)
            )
```

> **提示**：
> - 所有方法必须使用 `self._adapter.call_api(...)` 或封装后的 API 调用函数。
> - 推荐方法名首字母大写（如 `Text`, `Image`），以便统一风格。
> - 参数命名清晰且符合平台 API 规范（例如 `recvId`, `recvType`）。

---

### 必须实现的方法：Text(...)

- **`Text(...)`**：文本消息是基础功能，任何适配器都应实现此方法。
  ```python
  def Text(self, text: str, buttons: List = None, parent_id: str = "")
  ```

---

### 可选推荐方法

| 方法 | 描述 |
|------|------|
| `.Text(text: str)` | 发送纯文本消息（必须） |
| `.Image(file: bytes)` | 发送图片文件 |
| `.Video(file: bytes)` | 发送视频文件 |
| `.File(file: bytes)` | 发送任意类型的文件 |
| `.Markdown(markdown: str)` | 发送 Markdown 格式内容 |
| `.Html(html: str)` | 发送 HTML 格式内容 |
| `.Batch(target_ids: List[str], message: Any)` | 批量发送消息 |
| `.Edit(msg_id: str, text: str)` | 编辑已发送的消息 |
| `.Recall(msg_id: str)` | 撤回消息 |

---

### 内部工作原理简析

当开发者调用如下语句时：

```python
sdk.adapter.Yunhu.Send.To("user", "U1001").Text("你好")
```

框架会执行以下流程：

1. 创建 `YunhuAdapter.Send` 实例；
2. 调用 `.To(...)` 设置目标用户/群组；
3. 调用 `.Text(...)` 构造请求参数；
4. 使用 `call_api(...)` 发送 HTTP 请求；
5. 返回异步任务对象（`asyncio.Task`）供外部 await。

> ⚠️ 注意：
> - 所有 `.Send.*()` 方法必须返回 `asyncio.Task` 类型，以支持异步链式调用。
> - 若需上传文件（如图片、视频），应通过 `_upload_file_and_call_api` 先上传再调用主接口。

---

### 自定义扩展示例：Card(...) 消息

假设你的平台支持富文本卡片格式，可以这样扩展：

```python
class YunhuAdapter(sdk.BaseAdapter):
    class Send(sdk.SendDSL):
        def Card(self, title: str, content: str, image_url: str = None):
            payload = {
                "title": title,
                "content": content
            }
            if image_url:
                payload["imageUrl"] = image_url

            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/bot/send",
                    recvId=self._target_id,
                    recvType=self._target_type,
                    contentType="card",
                    content=payload
                )
            )
```

调用方式：

```python
sdk.adapter.Yunhu.Send.To("group", "G1001").Card(
    title="通知",
    content="这是一条重要提醒",
    image_url="https://example.com/alert.png"
)
```

---

### 开发者建议

- **保持命名一致性**：方法名首字母大写，动词+名词结构（如 `Text`, `Image`, `EditMessage`）。
- **封装公共逻辑**：如上传文件、构建消息体等，避免重复代码。
- **异步优先**：确保所有操作都在异步环境中运行，提高并发能力。
- **异常处理**：在 call_api 中捕获并记录错误，提升健壮性。

---

## 10. 模块开发基础

### 目录结构

```bash
模块名/
├── __init__.py    # 模块入口
└── Core.py        # 核心逻辑
```

### moduleInfo 字典

`__init__.py` 中必须包含 `moduleInfo` 字典：

```python
moduleInfo = {
    "meta": {
        "name": "MyModule",
        "version": "1.0.0",
        "description": "模块描述",
        "author": "开发者",
        "license": "MIT"
    },
    "dependencies": {
        "requires": ["依赖模块1"],
        "optional": [["可选依赖1", "可选依赖2"]],
        "pip": ["第三方库"]
    }
}
```

### Main 类

`Core.py` 中实现 `Main` 类：

```python
class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
        self.env = sdk.env
        self.raiserr = sdk.raiserr
        self.adapter = sdk.adapter
        self.logger.info("模块已启动")
```

---

## 11. 模块间通信

通过 `sdk.<ModuleName>` 访问其他模块实例：

```python
class Main:
    def __init__(self, sdk):
        self.sdk = sdk

    def your_function(self, ...):
        other_module = self.sdk.OtherModule  # 访问其他模块
```

---

## 12. 伪指针特性

SDK 支持伪指针特性，允许覆盖底层模块实现：

```python
class CustomLogger:
    def info(self, msg): print(f"INFO: {msg}")

sdk.logger = CustomLogger()  # 替换日志模块
```


> 更多详细信息请阅读源码。
