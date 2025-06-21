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

提供平台适配器基类、消息发送DSL和适配器管理功能。

## 主要功能
- BaseAdapter: 适配器基类
- SendDSL: 链式消息发送接口
- AdapterManager: 适配器管理
- 适配器注册和生命周期管理

## API 文档
### 适配器基类 (BaseAdapter):
    - call_api(): 必须实现的API调用方法
    - start(): 启动适配器
    - shutdown(): 关闭适配器
    - on(): 事件监听装饰器
    - emit(): 触发事件

### 消息发送DSL (SendDSL):
    - To(): 设置消息目标
    - Text(): 发送文本消息
    - 可扩展其他消息类型

### 适配器管理 (AdapterManager):
    - register(): 注册适配器
    - startup(): 启动适配器
    - shutdown(): 关闭所有适配器
    - get(): 获取适配器实例

### 示例用法：

```
from ErisPulse import sdk

# 注册适配器
sdk.adapter.register("MyPlatform", MyAdapter)

# 发送消息
sdk.adapter.MyPlatform.Send.To("user", "123").Text("Hello")

# 启动适配器
await sdk.adapter.startup()
```

## db (source: [ErisPulse/db.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/db.py))

# 环境配置

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。

## API 文档
### 基本操作：
    - get(key, default=None) -> any: 获取配置项
    - set(key, value) -> bool: 设置配置项
    - delete(key) -> bool: 删除配置项
    - get_all_keys() -> list[str]: 获取所有键名

### 批量操作：
    - get_multi(keys) -> dict: 批量获取键值
    - set_multi(items) -> bool: 批量设置键值
    - delete_multi(keys) -> bool: 批量删除键值

### 事务管理：
    - transaction() -> contextmanager: 创建事务上下文

### 快照管理：
    - snapshot(name=None) -> str: 创建数据库快照
    - restore(snapshot_name) -> bool: 从快照恢复
    - list_snapshots() -> list: 列出所有快照
    - delete_snapshot(name) -> bool: 删除指定快照
    - set_snapshot_interval(seconds): 设置自动快照间隔

### 其他功能：
    - clear(): 清空所有配置
    - load_env_file(): 从env.py加载配置(SDK自动)

### 示例用法：

```
from ErisPulse import sdk

env = sdk.env

# 基本操作
env.set('config_key', 'value')
value = env.get('config_key')
value_another = env.config_key  # 通过属性访问
env.config_key = 'value'        # 通过属性赋值

# 事务使用
with env.transaction():
    env.set('key1', 'value1')
    env.set('key2', 'value2')
    
# 快照管理
snapshot_path = env.snapshot()
env.restore('snapshot_name')
```

## logger (source: [ErisPulse/logger.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/logger.py))

# 日志系统

提供模块化、多级别的日志记录功能，支持内存存储和文件输出。

## API 文档
### 基本操作：
    - debug(msg, *args, **kwargs):      调试信息
    - info(msg, *args, **kwargs):       运行信息  
    - warning(msg, *args, **kwargs):    警告信息
    - error(msg, *args, **kwargs):      错误信息
    - critical(msg, *args, **kwargs):   致命错误并终止程序

### 日志控制：
    - set_level(level):                     设置全局日志级别
    - set_module_level(module_name, level): 设置模块日志级别

### 日志存储：
    - save_logs(path):          保存内存中的日志到文件
    - set_output_file(path):    设置日志输出文件

### 示例用法：

```
from ErisPulse import sdk

# 基本日志记录
sdk.logger.debug("调试信息")
sdk.logger.info("运行状态")

# 模块级日志控制
sdk.logger.set_module_level("MyModule", "DEBUG")

# 异常捕获
@sdk.logger.catch
def risky_function():
    raise Exception("出错了")
```

## 准备弃用

catch(func_or_level=None, level="error"): 异常捕获装饰器
- 原因: 异常捕获功能已集成到 raiserr 模块中，建议使用 raiserr 进行异常处理。

## mods (source: [ErisPulse/mods.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/mods.py))

# 模块管理系统

提供模块的注册、状态管理和依赖解析功能。

## API 文档
### 模块状态：
    - set_module_status(module_name, status):   设置模块启用状态
    - get_module_status(module_name):           获取模块状态

### 模块信息：
    - set_module(module_name, module_info): 设置模块信息
    - get_module(module_name):              获取模块信息
    - get_all_modules():                    获取所有模块信息
    - remove_module(module_name):           删除模块

### 前缀管理：
    - update_prefixes(module_prefix, status_prefix): 更新存储前缀
    - module_prefix: 模块存储前缀属性
    - status_prefix: 状态存储前缀属性

### 示例用法：

```
from ErisPulse import sdk

# 设置模块状态
sdk.mods.set_module_status("MyModule", True)

# 获取模块信息
module_info = sdk.mods.get_module("MyModule")

# 批量操作
sdk.mods.set_all_modules({"Module1": {...}, "Module2": {...}})
```

## raiserr (source: [ErisPulse/raiserr.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/raiserr.py))

# 错误管理系统

提供错误类型注册、抛出和管理功能，集成全局异常处理。

## API 文档
### 错误注册：
    - register(name, doc="", base=Exception): 注册新的错误类型
    - info(name: str = None): 获取错误类型信息

### 错误抛出：
    - __getattr__(name): 动态获取错误抛出函数
    - ErrorType(msg, exit=False): 抛出注册的错误类型

### 全局处理：
    - global_exception_handler: 全局同步异常处理器
    - async_exception_handler: 全局异步异常处理器

### 示例用法：

```
from ErisPulse import sdk

# 注册自定义错误
sdk.raiserr.register("MyError", doc="自定义错误描述")

# 抛出错误
sdk.raiserr.MyError("发生了错误", exit=False)

# 获取错误信息
error_info = sdk.raiserr.info("MyError")
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

