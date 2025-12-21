# 懒加载配置说明

ErisPulse 框架支持模块的懒加载机制，即模块在第一次被访问时才进行初始化。然而，某些用户的模块可能不适应这种懒加载机制，因此框架提供了全局开关来控制是否使用懒加载。

## 配置方式

在项目的配置文件中，可以通过 `framework.enable_lazy_loading` 选项来控制全局的懒加载行为：

```toml
[ErisPulse.framework]
enable_lazy_loading = false  # 禁用懒加载，所有模块立即加载
```

或者

```toml
[ErisPulse.framework]
enable_lazy_loading = true   # 启用懒加载（默认值）
```

## 工作机制

1. **全局配置优先**：框架首先会检查全局的 `enable_lazy_loading` 配置
   - 如果设置为 `false`，则所有模块都会立即加载，无论模块自身的设置如何
   - 如果设置为 `true` 或未配置，则继续使用模块级的懒加载控制

2. **模块级控制**：即使全局启用了懒加载，模块仍可以通过实现 `should_eager_load()` 方法来控制自身的加载行为

## 示例

### 禁用全局懒加载

```toml
# config.toml
[ErisPulse.framework]
enable_lazy_loading = false
```

这将使所有模块在框架初始化时立即加载，而不是在第一次访问时加载。

### 模块级控制

即使全局启用了懒加载，模块仍可以控制自身的加载行为：

```python
class MyModule(BaseModule):
    @staticmethod
    def should_eager_load() -> bool:
        """
        返回 True 表示该模块应该立即加载，而不是懒加载
        """
        return True
```

## 注意事项

1. 禁用懒加载可能会增加框架初始化时间，但可以减少模块首次访问时的延迟
2. 如果模块之间存在复杂的依赖关系，建议使用立即加载以确保所有依赖都正确初始化
3. 全局配置的优先级高于模块级配置，当全局禁用懒加载时，所有模块都会立即加载