"""
# 日志系统

提供模块化、多级别的日志记录功能，支持内存存储和文件输出。实现了模块级别的日志控制、彩色输出和灵活的存储选项。

## 核心功能
1. 多级别日志记录
2. 模块级别日志控制
3. 内存日志存储
4. 文件输出支持
5. 自动调用者识别
6. 异常捕获装饰器

## API 文档

### 基本日志操作
#### debug(msg: str, *args, **kwargs) -> None
记录调试级别的日志信息。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None
- 示例:
```python
# 基本调试信息
sdk.logger.debug("初始化配置")

# 带有变量的调试信息
config_value = get_config("timeout")
sdk.logger.debug(f"读取配置: timeout = {config_value}")

# 在条件下记录调试信息
if is_development_mode():
    sdk.logger.debug("开发模式下的详细信息: %s", detailed_info)
```

#### info(msg: str, *args, **kwargs) -> None
记录信息级别的日志信息。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None
- 示例:
```python
# 基本信息记录
sdk.logger.info("应用已启动")

# 带有上下文的信息
user_count = get_active_users()
sdk.logger.info(f"当前活跃用户: {user_count}")

# 记录操作结果
sdk.logger.info("数据导入完成，共处理 %d 条记录", record_count)
```

#### warning(msg: str, *args, **kwargs) -> None
记录警告级别的日志信息。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None
- 示例:
```python
# 基本警告信息
sdk.logger.warning("配置文件未找到，使用默认配置")

# 性能警告
if response_time > threshold:
    sdk.logger.warning(f"响应时间过长: {response_time}ms > {threshold}ms")

# 资源使用警告
memory_usage = get_memory_usage()
if memory_usage > 80:
    sdk.logger.warning("内存使用率高: %d%%", memory_usage)
```

#### error(msg: str, *args, **kwargs) -> None
记录错误级别的日志信息。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None
- 示例:
```python
# 基本错误信息
sdk.logger.error("数据库连接失败")

# 带有异常信息的错误
try:
    process_data()
except Exception as e:
    sdk.logger.error(f"数据处理错误: {str(e)}")

# 带有错误代码的错误
sdk.logger.error("API请求失败，状态码: %d, 错误: %s", status_code, error_message)
```

#### critical(msg: str, *args, **kwargs) -> None
记录致命错误级别的日志信息，并终止程序。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None (程序会终止)
- 示例:
```python
# 致命错误记录
if not database_connection:
    sdk.logger.critical("无法连接到主数据库，应用无法继续运行")

# 安全相关的致命错误
if security_breach_detected():
    sdk.logger.critical("检测到安全漏洞，强制关闭系统")

# 资源耗尽的致命错误
if disk_space < min_required:
    sdk.logger.critical("磁盘空间不足 (%dMB)，无法继续运行", disk_space)
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

### 异常捕获 (准备弃用)
#### catch(func_or_level=None, level="error")
异常捕获装饰器。
- 参数:
  - func_or_level: 要装饰的函数或日志级别
  - level: 捕获异常时使用的日志级别
- 返回:
  - function: 装饰后的函数
- 注意:
  - 此功能已集成到 raiserr 模块中，建议使用 raiserr 进行异常处理
- 示例:
```python
# 基本用法 (不推荐，请使用raiserr)
@sdk.logger.catch
def risky_function():
    # 可能抛出异常的代码
    process_data()

# 指定日志级别 (不推荐，请使用raiserr)
@sdk.logger.catch(level="critical")
def very_important_function():
    # 关键操作
    update_database()
```

## 最佳实践
1. 日志级别使用
```python
# 开发环境使用详细日志
if is_development():
    sdk.logger.set_level("DEBUG")
    sdk.logger.debug("详细的调试信息")
else:
    sdk.logger.set_level("INFO")
    
# 性能敏感模块使用更高级别
sdk.logger.set_module_level("PerformanceModule", "WARNING")
```

2. 结构化日志信息
```python
# 使用一致的格式
def log_api_request(endpoint, method, status, duration):
    sdk.logger.info(
        f"API请求: {method} {endpoint} - 状态: {status}, 耗时: {duration}ms"
    )

# 包含关键上下文
def log_user_action(user_id, action, result):
    sdk.logger.info(
        f"用户操作: [用户:{user_id}] {action} - 结果: {result}"
    )
```

3. 日志文件管理
```python
# 按日期分割日志文件
from datetime import datetime
import os

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"app_{today}.log")
    
    sdk.logger.set_output_file(log_file)
    sdk.logger.info(f"日志文件已设置: {log_file}")
```

4. 异常处理与日志
```python
# 推荐方式：使用raiserr结合logger
def process_with_logging():
    try:
        result = perform_operation()
        sdk.logger.info(f"操作成功: {result}")
        return result
    except Exception as e:
        sdk.logger.error(f"操作失败: {str(e)}")
        sdk.raiserr.OperationError(f"处理失败: {str(e)}")
```

## 注意事项
1. 日志级别选择
   - DEBUG: 详细的调试信息，仅在开发环境使用
   - INFO: 常规操作信息，适用于生产环境
   - WARNING: 潜在问题或异常情况
   - ERROR: 错误但不影响整体功能
   - CRITICAL: 致命错误，导致程序终止

2. 性能考虑
   - 避免在高频循环中记录过多日志
   - 使用适当的日志级别减少不必要的输出
   - 考虑日志文件大小和轮转策略

3. 敏感信息保护
   - 不要记录密码、令牌等敏感信息
   - 在记录用户数据前进行脱敏处理
   - 遵循数据保护法规要求

4. 迁移建议
   - 从catch装饰器迁移到raiserr模块
   - 使用结构化的错误处理方式
   - 结合日志和错误管理实现完整的异常处理流程
"""

import logging
import inspect
import datetime
import functools

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

    def catch(self, func_or_level=None, level="error"):
        if isinstance(func_or_level, str):
            return lambda func: self.catch(func, level=func_or_level)
        if func_or_level is None:
            return lambda func: self.catch(func, level=level)
        func = func_or_level

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                import traceback
                error_info = traceback.format_exc()

                module_name = func.__module__
                if module_name == "__main__":
                    module_name = "Main"
                func_name = func.__name__

                error_msg = f"Exception in {func_name}: {str(e)}\n{error_info}"

                log_method = getattr(self, level, self.error)
                log_method(error_msg)

                return None
        return wrapper

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