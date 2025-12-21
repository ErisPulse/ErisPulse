# 懒加载模块系统

ErisPulse SDK 提供了一个强大的懒加载模块系统，允许模块在实际需要时才进行初始化，从而显著提升应用启动速度和内存效率。

## 概述

懒加载模块系统是 ErisPulse 的核心特性之一，它通过以下方式工作：

- **延迟初始化**：模块只有在第一次被访问时才会实际加载和初始化
- **透明使用**：对于开发者来说，懒加载模块与普通模块在使用上几乎没有区别
- **自动依赖管理**：模块依赖会在被使用时自动初始化
- **生命周期支持**：对于继承自 `BaseModule` 的模块，会自动调用生命周期方法

## 工作原理

### LazyModule 类

懒加载系统的核心是 `LazyModule` 类，它是一个包装器，在第一次访问时才实际初始化模块：

```python
class LazyModule:
    """
    懒加载模块包装器
    
    当模块第一次被访问时才进行实例化
    """
```

### 初始化过程

当模块首次被访问时，`LazyModule` 会执行以下操作：

1. 获取模块类的 `__init__` 参数信息
2. 根据参数决定是否传入 `sdk` 引用
3. 设置模块的 `moduleInfo` 属性
4. 对于继承自 `BaseModule` 的模块，调用 `on_load` 方法
5. 触发 `module.init` 生命周期事件

## 配置懒加载

### 全局配置

在配置文件中启用/禁用全局懒加载：

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true=启用懒加载(默认)，false=禁用懒加载
```

### 模块级别控制

模块可以通过实现 `should_eager_load()` 静态方法来控制是否使用懒加载：

```python
from ErisPulse.Core.Bases import BaseModule

class MyModule(BaseModule):
    @staticmethod
    def should_eager_load() -> bool:
        """
        模块是否应该在启动时加载
        默认为False(即懒加载)
        """
        return True  # 返回True表示禁用懒加载，在启动时立即加载
```

## 使用懒加载模块

### 基本使用

对于开发者来说，懒加载模块与普通模块在使用上几乎没有区别：

```python
# 通过SDK访问懒加载模块
from ErisPulse import sdk

# 以下访问会触发模块懒加载
result = await sdk.my_module.my_method()
```

### 异步初始化

对于需要异步初始化的模块，建议先显式加载：

```python
# 先显式加载模块
await sdk.load_module("my_module")

# 然后使用模块
result = await sdk.my_module.my_method()
```

### 同步初始化

对于不需要异步初始化的模块，可以直接访问：

```python
# 直接访问会自动同步初始化
result = sdk.my_module.some_sync_method()
```

## 高级特性

### 属性代理

`LazyModule` 透明地代理所有属性访问和方法调用：

```python
# 所有这些操作都会被透明地代理到实际模块实例
value = sdk.my_module.some_property
result = await sdk.my_module.some_method()
sdk.my_module.some_property = new_value
```

### 方法代理

模块的方法调用也会被代理：

```python
# 模块函数调用
result = sdk.my_module(arg1, arg2)
```

### 属性列表

可以使用 `dir()` 函数获取模块的属性列表：

```python
# 这会触发模块初始化并返回其属性列表
attributes = dir(sdk.my_module)
```

### 调试表示

模块提供了有意义的字符串表示：

```python
# 未初始化
print(sdk.my_module)  # 输出: <LazyModule my_module (not initialized)>

# 已初始化
await sdk.my_module.init()
print(sdk.my_module)  # 输出: <MyModule object at 0x...>
```

## 生命周期集成

懒加载模块系统与 ErisPulse 的生命周期系统完全集成：

### 自动事件触发

模块加载时会自动触发以下事件：

```python
# 模块初始化完成事件
await lifecycle.submit_event(
    "module.init",
    msg=f"模块 {module_name} 初始化完毕",
    data={
        "module_name": module_name,
        "success": True,
    }
)
```

### 模块生命周期方法

对于继承自 `BaseModule` 的模块：

```python
class MyModule(BaseModule):
    async def on_load(self, event: dict) -> bool:
        """模块加载时自动调用"""
        print(f"模块 {event['module_name']} 正在加载...")
        # 执行初始化逻辑
        return True
    
    async def on_unload(self, event: dict) -> bool:
        """模块卸载时自动调用"""
        print(f"模块 {event['module_name']} 正在卸载...")
        # 执行清理逻辑
        return True
```

## 最佳实践

### 1. 合理选择加载策略

- 使用懒加载作为默认策略，除非有特殊需求
- 对于提供基础服务的模块，考虑禁用懒加载（`should_eager_load=True`）

### 2. 处理异步初始化

对于需要异步初始化的模块：

```python
class AsyncInitModule(BaseModule):
    def __init__(self):
        self._db = None
        self._ready = False
    
    async def _init_async(self):
        """异步初始化逻辑"""
        self._db = await some_async_setup()
        self._ready = True
    
    async def ensure_ready(self):
        """确保模块已准备好"""
        if not self._ready:
            await self._init_async()
    
    async def do_something(self):
        await self.ensure_ready()
        return self._db.query(...)
```

### 3. 错误处理

懒加载模块会处理初始化错误并触发相应事件：

```python
try:
    result = await sdk.my_module.some_method()
except ImportError as e:
    logger.error(f"无法加载模块: {e}")
except Exception as e:
    logger.error(f"模块初始化失败: {e}")
```

### 4. 性能考虑

- 懒加载主要提升应用启动性能
- 对于大型应用，懒加载可以显著减少初始内存占用
- 但第一个访问操作会有轻微延迟

## 故障排除

### 常见问题

1. **模块需要异步初始化但在同步上下文中访问**
   ```
   RuntimeError: 模块 my_module 需要异步初始化，请使用 'await sdk.load_module("my_module")' 来初始化模块
   ```
   
   解决方案：先显式异步加载模块

2. **模块初始化失败**
   - 检查模块代码是否有错误
   - 确保所有依赖都已安装
   - 查看日志获取详细错误信息

3. **配置不生效**
   - 确保配置文件路径正确
   - 检查配置格式是否符合要求
   - 确认配置在应用启动前已加载

## 总结

懒加载模块系统是 ErisPulse 提供的一项强大功能，它能够在不改变开发者使用习惯的情况下，显著提升应用性能。通过合理的配置和使用，可以让应用启动更快，内存占用更低，同时保持代码的简洁和可维护性。

对于大多数模块，建议保持默认的懒加载行为，只有在模块确实需要在应用启动时就可用的情况下，才考虑禁用懒加载。