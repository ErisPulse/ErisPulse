# ErisPulse 核心模块工作原理
本文档将介绍如何使用 ErisPulse 的核心模块以及如何使用它们

## 一、了解工作原理

### 核心对象

你可以通过 `from ErisPulse.Core import env, mods, logger, raiserr, util, adapter, BaseAdapter, EventDataBase` 直接获取核心模块对象

当然, 为了保持兼容性，你也可以通过 `sdk` 获取 SDK 对象，并使用 `sdk.<核心模块名>` 访问核心模块对象, 乃至使用三方模块重写SDK功能!

| 名称 | 用途 |
|------|------|
| `sdk` | SDK对象 |
| `env`/`sdk.env` | 获取/设置全局配置 |
| `mods`/`sdk.mods` | 模块管理器 |
| `logger`/`sdk.logger` | 日志记录器 |
| `raiserr`/`sdk.raiserr` | 错误管理器 |
| `util`/`sdk.util` | 工具函数（缓存、重试等） |
| `adapter`/`sdk.adapter` | 获取其他适配器实例 |
| `BaseAdapter`/`sdk.BaseAdapter` | 适配器基类 |
| `EventDataBase`/`sdk.EventDataBase` | 事件数据处理基类 |

### 模块调用

ErisPulse 框架提供了一个 `sdk` 对象, 所有模块都会被注册在 `sdk` 对象中

例如一个模块的结构是:
```python
# from ErisPulse import sdk
# from ErisPulse.Core import logger 

class MyModule:
    def __init__(self, sdk):    # 注: 这里也可以不传入 sdk 参数 | 你可以直接 from ErisPulse import sdk 来获得sdk对象
        self.sdk = sdk
        self.logger = sdk.logger

    def hello(self):
        self.logger.info("hello world")
        return "hello world"
```

这时候你可以在 `main.py` 中这样调用:
```python
from ErisPulse import sdk

sdk.init()

sdk.MyModule.hello()
```
这样就可以调用到模块中的方法了, 当然任何地方都可以调用模块中的方法, 只要它被加载到了 `sdk` 对象中

通过 `sdk.<ModuleName>` 访问其他模块实例：
```python
other_module = sdk.OtherModule
result = other_module.some_method()
```

---

适配器的使用: 
```python
from ErisPulse import sdk

async def main():
    sdk.init()

    await sdk.adapter.startup("MyAdapter")  # 这里不指定适配器名称的话, 会自动选择启动所有被注册到 `adapter`/`sdk.adapter` 中的适配器

    MyAdapter = sdk.adapter.get("MyAdapter")

    @MyAdapter.on("message")
    async def on_message(data):
        sdk.MyAdapterEvent(data)
        sender_type = sdk.MyAdapterEvent.sender_type()
        sender_id = sdk.MyAdapterEvent.sender_id()

    type, id = "Guild", "1234567890"
    await MyAdapter.Send.To(type, id).Text("Hello World!")  # 这里使用了DSL风格的调用, 在以后的章节中会详细介绍
```

通过 `sdk.adapter.<AdapterName>` 访问适配器实例：
```python
adapter = sdk.adapter.AdapterName
result = adapter.some_method()
```

## 二、核心对象功能示例

### 日志记录：

```python
from ErisPulse.Core import logger

#  设置单个模块日志级别
logger.set_module_level("MyModule", "DEBUG")

#  单次保持所有模块日志历史到文件
logger.save_logs("log.txt")

#  各等级日志
logger.debug("调试信息")
logger.info("运行状态")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("致命错误")    # 会触发程序崩溃
```

### env配置模块：

```python
from ErisPulse.Core import env

# 设置配置项
env.set("my_config_key", "new_value")

# 获取配置项
config_value = env.get("my_config_key", "default_value")

# 删除配置项
env.delete("my_config_key")

# 事务使用
with env.transaction():
    env.set('important_key', 'value')
    env.delete('temp_key')
    # 如果出现异常会自动回滚

# 获取模块配置
# 如果模块未注册，则返回None | 不支持设置默认值
env.getConfig("MyModule")
env.setConfig("MyModule", "MyConfig")
# 这里的建议使用是，先获取 "MyModule" 模块的配置项，如果为空，则设置 "MyModule" 模块的配置项为 默认需要生成的默认配置（被生成到用户的项目下的config.toml）

# 标准的示例:
def _getConfig():
    config = env.getConfig("MyModule")
    if config is None:
        defaultConfig = {
            "MyKey": "MyValue"
        }
        env.setConfig("MyModule", defaultConfig)
        return defaultConfig
    return config

# 其它深入操作请阅读API文档
```

### 注册自定义错误类型：

```python
from ErisPulse.Core import raiserr

#  注册一个自定义错误类型
raiserr.register("MyCustomError", doc="这是一个自定义错误")

#  获取错误信息
error_info = raiserr.info("MyCustomError")
if error_info:
    print(f"错误类型: {error_info['type']}")
    print(f"文档描述: {error_info['doc']}")
    print(f"错误类: {error_info['class']}")
else:
    print("未找到该错误类型")

#  抛出一个自定义错误
raiserr.MyCustomError("发生了一个错误")

```

### 工具函数：

```python
from ErisPulse import util

# 工具函数装饰器：自动重试指定次数
@util.retry(max_attempts=3, delay=1)
async def my_retry_function():
    # 此函数会在异常时自动重试 3 次，每次间隔 1 秒
    ...

# 缓存装饰器：缓存函数调用结果（基于参数）
@util.cache
def get_expensive_result(param):
    # 第一次调用后，相同参数将直接返回缓存结果
    ...

# 异步执行装饰器：将同步函数放入线程池中异步执行
@util.run_in_executor
def sync_task():
    # 此函数将在独立线程中运行，避免阻塞事件循环
    ...

# 在同步函数中调用异步任务
util.ExecAsync(sync_task)

```

## 监听适配器事件以及使用适配器

你可以使用以下代码监听被转换为OneBot12的事件
（你可以参考 Adapter.md 文档获取更多信息）
```python
from ErisPulse import sdk
from ErisPulse.Core import adapter

@adapter.on("message")
async def on_message(data):
    # 处理消息, 几乎所有适配器都实现了 Text 发送方法，所有这里示例发送获取到的文本消息
    
    # 获取哪个平台
    platform = data.get("platform")
    detail_type = data.get("detail_type", "private")
    datail_id = data.get("user_id") if detail_type == "private" else data.get("group_id")

    echo_text = data.get("alt_message")

    # 获取适配器, 并且调用对应的发送方法
    if hasattr(adapter, platform):
        await getattr(adapter, platform).To("user" if detail_type == "private" else "group", datail_id).Text(echo_text)

```

> 更多使用请查看 [docs/api/](docs/api/) 目录