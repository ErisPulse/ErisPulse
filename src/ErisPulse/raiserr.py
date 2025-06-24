"""
# 错误管理系统

提供错误类型注册、抛出和管理功能，集成全局异常处理。支持自定义错误类型、错误链追踪和全局异常捕获。

## 核心功能
1. 错误类型注册和管理
2. 动态错误抛出
3. 全局异常处理
4. 错误信息追踪
5. 异步错误处理

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

### 全局异常处理
#### global_exception_handler(exc_type: type, exc_value: Exception, exc_traceback: traceback)
全局同步异常处理器。
- 参数:
  - exc_type: 异常类型
  - exc_value: 异常值
  - exc_traceback: 异常追踪信息
- 示例:
```python
# 系统会自动捕获未处理的异常
def risky_operation():
    raise Exception("未处理的异常")
    
# 异常会被global_exception_handler捕获并处理
risky_operation()
```

#### async_exception_handler(loop: asyncio.AbstractEventLoop, context: dict)
全局异步异常处理器。
- 参数:
  - loop: 事件循环实例
  - context: 异常上下文信息
- 示例:
```python
async def async_operation():
    raise Exception("异步操作错误")
    
# 异常会被async_exception_handler捕获并处理
asyncio.create_task(async_operation())
```

## 最佳实践
1. 错误类型注册
```python
# 为特定功能模块注册错误类型
sdk.raiserr.register("DatabaseError", "数据库操作错误")
sdk.raiserr.register("NetworkError", "网络连接错误")
sdk.raiserr.register("ValidationError", "数据验证错误")

# 使用继承关系组织错误类型
class ModuleError(Exception):
    pass
sdk.raiserr.register("ConfigError", "配置错误", ModuleError)
sdk.raiserr.register("PluginError", "插件错误", ModuleError)
```

2. 错误处理流程
```python
def process_data(data):
    try:
        if not data:
            sdk.raiserr.ValidationError("数据不能为空")
        if not isinstance(data, dict):
            sdk.raiserr.ValidationError("数据必须是字典类型")
            
        # 处理数据...
        
    except Exception as e:
        # 错误会被自动记录并处理
        sdk.raiserr.ProcessingError(f"数据处理失败: {str(e)}")
```

3. 异步环境使用
```python
async def async_task():
    try:
        result = await some_async_operation()
        if not result.success:
            sdk.raiserr.AsyncOperationError("异步操作失败")
    except Exception as e:
        # 异步错误会被async_exception_handler捕获
        raise
```

## 注意事项
1. 错误类型命名应具有描述性，便于理解错误来源
2. 错误消息应包含足够的上下文信息，便于调试
3. 适当使用exit参数，只在致命错误时设置为True
4. 避免在全局异常处理器中执行耗时操作
5. 确保异步代码中的错误能够被正确捕获和处理

"""

import sys
import traceback
import asyncio

class Error:
    def __init__(self):
        self._types = {}

    def register(self, name, doc="", base=Exception):
        if name not in self._types:
            err_cls = type(name, (base,), {"__doc__": doc})
            self._types[name] = err_cls
        return self._types[name]

    def __getattr__(self, name):
        def raiser(msg, exit=False):
            from .logger import logger
            err_cls = self._types.get(name) or self.register(name)
            exc = err_cls(msg)

            red = '\033[91m'
            reset = '\033[0m'

            logger.error(f"{red}{name}: {msg} | {err_cls.__doc__}{reset}")
            logger.error(f"{red}{ ''.join(traceback.format_stack()) }{reset}")

            if exit:
                raise exc
        return raiser

    def info(self, name: str = None):
        result = {}
        for err_name, err_cls in self._types.items():
            result[err_name] = {
                "type": err_name,
                "doc": getattr(err_cls, "__doc__", ""),
                "class": err_cls,
            }
        if name is None:
            return result
        err_cls = self._types.get(name)
        if not err_cls:
            return None
        return {
            "type": name,
            "doc": getattr(err_cls, "__doc__", ""),
            "class": err_cls,
        }

raiserr = Error()

# 全局异常处理器
def global_exception_handler(exc_type, exc_value, exc_traceback):
    from .logger import logger
    error_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.error(f"未处理的异常被捕获:\n{error_message}")
    raiserr.CaughtExternalError(
        f"检测到外部异常，请优先使用 sdk.raiserr 抛出错误。\n原始异常: {exc_type.__name__}: {exc_value}\nTraceback:\n{error_message}"
    )
sys.excepthook = global_exception_handler

def async_exception_handler(loop, context):
    from .logger import logger
    exception = context.get('exception')
    message = context.get('message', 'Async error')
    if exception:
        tb = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        logger.error(f"异步任务异常: {message}\n{tb}")
        raiserr.CaughtExternalError(
            f"检测到异步任务异常，请优先使用 sdk.raiserr 抛出错误。\n原始异常: {type(exception).__name__}: {exception}\nTraceback:\n{tb}"
        )
    else:
        logger.warning(f"异步任务警告: {message}")
asyncio.get_event_loop().set_exception_handler(async_exception_handler)