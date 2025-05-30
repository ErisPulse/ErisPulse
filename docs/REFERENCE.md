# ErisPulse 方法与接口文档

本文件详细说明 ErisPulse 框架的主要方法、API 入口、模块接口规范及常用调用方式。

## 1. SDK 入口对象

ErisPulse 通过 `sdk` 对象暴露核心能力：
- sdk实例有伪指针的特性,第三方模块可以通过重定义`sdk.<Name>`的方式重写底层模块。

```python
from ErisPulse import sdk

sdk.env         # 环境与配置管理
sdk.util        # 工具
sdk.logger      # 日志记录器
sdk.raiserr     # 内置的错误管理器
```

---

## 2. 主要方法说明

### 2.1 初始化方法

```python
sdk.init()
```
- **说明**：初始化并加载所有模块,所有模块会被加载到`sdk`实例中。
- **用法**：
    ```python
    from ErisPulse import sdk
    sdk.init()
    sdk.<ModuleName>.<ModuleFunc>
    ```

---

### 2.2 日志方法

通过 `sdk.logger` 记录日志：

```python
sdk.logger.debug(Msg)
sdk.logger.info(Msg)
sdk.logger.warning(Msg)
sdk.logger.error(Msg)
sdk.logger.critical(Msg)
```
- **说明**：`logger`模块提供了基本而健全的log系统,但显然它不是那么美观,你可以通过`安装`/`自主重写`logger模块来实现美观的log系统

---

### 2.3 环境与配置管理

```python
sdk.env.get(Key, [DefValue])
sdk.env.set(Key, Value)
sdk.env.delete(Key)
sdk.env.clear()
sdk.env.load_env_file()
```
- **说明**：用于读取、写入和管理全局配置。

---

### 2.4 模块状态管理

```python
sdk.env.set_module_status(ModuleName, True/False)
sdk.env.get_module_status(ModuleName)
```
- **说明**：启用/禁用模块，查询模块状态。

---

### 2.5 使用内置错误管理

通过 `sdk.raiserr` 注册或抛出错误
```pyhton
sdk.raiserr.register(ErrTypeName, [Doc], [BaseErrType])
sdk.raiserr.<ErrTypeName>(Msg, [isExit])

```

## 3. 模块接口规范

每个模块需实现如下接口：

```python
# __init__.py
moduleInfo = {
    "meta": {...},
    "dependencies": {...}
}
from .Core import Main

# Core.py
class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
```
- **详细规范**见 [开发指南](DEVELOPMENT.md#2-模块接口规范)。

---

> **更多详细开发接口与模块规范请参考 [开发指南](DEVELOPMENT.md)。**