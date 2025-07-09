# ErisPulse 注释风格规范

在创建EP核心方法时必须添加方法注释，注释格式如下：

## 模块级文档注释

每个模块文件开头应包含模块文档：
```python
"""
[模块名称]
[模块功能描述]

{!--< tips >!--}
重要使用说明或注意事项
{!--< /tips >!--}
"""
```

## 方法注释

### 基本格式
```python
def func(param1: type1, param2: type2) -> return_type:
    """
    [功能描述]
    
    :param param1: [类型1] [参数描述1]
    :param param2: [类型2] [参数描述2]
    :return: [返回类型] [返回描述]
    """
    pass
```

### 完整格式（适用于复杂方法）
```python
def complex_func(param1: type1, param2: type2 = None) -> Tuple[type1, type2]:
    """
    [功能详细描述]
    [可包含多行描述]
    
    :param param1: [类型1] [参数描述1]
    :param param2: [类型2] [可选参数描述2] (默认: None)
    
    :return: 
        type1: [返回参数1描述]
        type2: [返回参数2描述]
    
    :raises ErrorType: [错误描述]
    """
    pass
```

## 特殊标签（用于API文档生成）

当方法注释包含以下内容时，将在API文档构建时产生对应效果：

| 标签格式 | 作用 | 示例 |
|---------|------|------|
| `{!--< internal-use >!--}` | 标记为内部使用，不生成文档 | `{!--< internal-use >!--}` |
| `{!--< ignore >!--}` | 忽略此方法，不生成文档 | `{!--< ignore >!--}` |
| `{!--< deprecated >!--}` | 标记为过时方法 | `{!--< deprecated >!--} 请使用new_func()代替` |
| `{!--< experimental >!--}` | 标记为实验性功能 | `{!--< experimental >!--} 可能不稳定` |
| `{!--< tips >!--}...{!--< /tips >!--}` | 多行提示内容 | `{!--< tips >!--}\n重要提示内容\n{!--< /tips >!--}` |
| `{!--< tips >!--}` | 单行提示内容 | `{!--< tips >!--} 注意: 此方法需要先初始化` |

## 最佳建议

1. **类型标注**：使用Python类型标注语法
   ```python
   def func(param: int) -> str:
   ```

2. **参数说明**：对可选参数注明默认值
   ```python
   :param timeout: [int] 超时时间(秒) (默认: 30)
   ```

3. **返回值**：多返回值使用`Tuple`或明确说明
   ```python
   :return: 
       str: 状态信息
       int: 状态码
   ```

4. **异常说明**：使用`:raises`标注可能抛出的异常
   ```python
   :raises ValueError: 当参数无效时抛出
   ```

5. **内部方法**：非公开API应添加`{!--< internal-use >!--}`标签

6. **过时方法**：标记过时方法并提供替代方案
   ```python
   {!--< deprecated >!--} 请使用new_method()代替 | 2025-07-09
   ```