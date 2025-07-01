"""
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

"""

import logging
import inspect
import datetime

class Logger:
    def __init__(self):
        self._logs = {}
        self._module_levels = {}
        self._logger = logging.getLogger("ErisPulse")
        self._logger.setLevel(logging.DEBUG)
        self._file_handler = None
        if not self._logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(console_handler)

    def set_level(self, level: str):
        level = level.upper()
        if hasattr(logging, level):
            self._logger.setLevel(getattr(logging, level))

    def set_module_level(self, module_name: str, level: str) -> bool:
        from .db import env
        if not env.get_module_status(module_name):
            self._logger.warning(f"模块 {module_name} 未启用，无法设置日志等级。")
            return False
        level = level.upper()
        if hasattr(logging, level):
            self._module_levels[module_name] = getattr(logging, level)
            self._logger.info(f"模块 {module_name} 日志等级已设置为 {level}")
            return True
        else:
            self._logger.error(f"无效的日志等级: {level}")
            return False

    def set_output_file(self, path: str | list):
        if self._file_handler:
            self._logger.removeHandler(self._file_handler)
            self._file_handler.close()

        if isinstance(path, str):
            path = [path]

        for p in path:
            try:
                file_handler = logging.FileHandler(p, encoding='utf-8')
                file_handler.setFormatter(logging.Formatter("%(message)s"))
                self._logger.addHandler(file_handler)
                self._logger.info(f"日志输出已设置到文件: {p}")
            except Exception as e:
                self._logger.error(f"无法设置日志文件 {p}: {e}")
                raise e

    def save_logs(self, path: str | list):
        if self._logs == None:
            self._logger.warning("没有log记录可供保存。")
            return
        if isinstance(path, str):
            path = [path]

        for p in path:
            try:
                with open(p, "w", encoding="utf-8") as file:
                    for module, logs in self._logs.items():
                        file.write(f"Module: {module}\n")
                        for log in logs:
                            file.write(f"  {log}\n")
                    self._logger.info(f"日志已被保存到：{p}。")
            except Exception as e:
                self._logger.error(f"无法保存日志到 {p}: {e}。")
                raise e

    def _save_in_memory(self, ModuleName, msg):
        if ModuleName not in self._logs:
            self._logs[ModuleName] = []
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"{timestamp} - {msg}"
        self._logs[ModuleName].append(msg)

    def _get_effective_level(self, module_name):
        return self._module_levels.get(module_name, self._logger.level)

    def _get_caller(self):
        frame = inspect.currentframe().f_back.f_back
        module = inspect.getmodule(frame)
        module_name = module.__name__
        if module_name == "__main__":
            module_name = "Main"
        if module_name.endswith(".Core"):
            module_name = module_name[:-5]
        if module_name.startswith("ErisPulse"):
            module_name = "ErisPulse"
        return module_name

    def debug(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= logging.DEBUG:
            self._save_in_memory(caller_module, msg)
            self._logger.debug(f"[{caller_module}] {msg}", *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= logging.INFO:
            self._save_in_memory(caller_module, msg)
            self._logger.info(f"[{caller_module}] {msg}", *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= logging.WARNING:
            self._save_in_memory(caller_module, msg)
            self._logger.warning(f"[{caller_module}] {msg}", *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= logging.ERROR:
            self._save_in_memory(caller_module, msg)
            self._logger.error(f"[{caller_module}] {msg}", *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= logging.CRITICAL:
            self._save_in_memory(caller_module, msg)
            self._logger.critical(f"[{caller_module}] {msg}", *args, **kwargs)
            from .raiserr import raiserr
            raiserr.register("CriticalError", doc="发生致命错误")
            raiserr.CriticalError(f"程序发生致命错误：{msg}", exit=True)

logger = Logger()