"""
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
    error_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    raiserr.ExternalError(
        f"{exc_type.__name__}: {exc_value}\nTraceback:\n{error_message}"
    )
def async_exception_handler(loop, context):
    exception = context.get('exception')
    tb = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    raiserr.ExternalError(
        f"{type(exception).__name__}: {exception}\nTraceback:\n{tb}"
    )

sys.excepthook = global_exception_handler
asyncio.get_event_loop().set_exception_handler(async_exception_handler)