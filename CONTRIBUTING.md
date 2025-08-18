# 项目贡献指南

## 分支管理规范

### 分支结构
- **main**: 主分支，存放稳定可发布的代码
- **Develop/v2**: 开发主分支，所有功能分支最终合并至此
- **Pre-Release/v2**: 预发布分支，用于版本发布前的测试
- **feature/***: 功能开发分支，按功能命名
- **Archive/v1**: 归档分支，存放旧版本代码

## 代码注释规范

### 模块级文档注释
```python
"""
[模块名称]
[模块功能描述]

{!--< tips >!--}
重要使用说明或注意事项
{!--< /tips >!--}
"""
```

### 方法注释
#### 基本格式
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

#### 完整格式（适用于复杂方法）
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

### 特殊标签
| 标签格式 | 作用 | 示例 |
|---------|------|------|
| `{!--< internal-use >!--}` | 标记为内部使用 | `{!--< internal-use >!--}` |
| `{!--< ignore >!--}` | 忽略此方法 | `{!--< ignore >!--}` |
| `{!--< deprecated >!--}` | 标记为过时方法 | `{!--< deprecated >!--} 请使用new_func()代替` |
| `{!--< experimental >!--}` | 标记为实验性功能 | `{!--< experimental >!--} 可能不稳定` |
| `{!--< tips >!--}...{!--< /tips >!--}` | 多行提示内容 | `{!--< tips >!--}\n重要提示内容\n{!--< /tips >!--}` |

## 贡献流程

1. **Fork仓库**
   - 首先fork主仓库到您的个人账户

2. **创建个人分支**
   - 从`Develop/v2`创建功能分支，命名规范：
     - `feature/描述性名称` (如`feature/wsu2059q`)

3. **开发工作**
   - 在功能分支上进行开发
   - 保持提交信息清晰明确
   - 按照注释规范添加文档注释
   - 提交前确保已经在ChangeLog中添加描述
   - 定期从`Develop/v2`拉取更新

4. **提交Pull Request**
   - 开发完成后，向`Develop/v2`提交PR
   - 在PR模板中勾选对应选项或添加详情信息

5. **代码审查**
   - 确保代码符合注释规范
   - 检查特殊标签使用是否正确

6. **合并到Develop/v2**
   - 审查通过后，代码将被合并

7. **发布流程**
   - `Develop/v2` → `Pre-Release/v2` 进行测试
   - 测试通过后发布到`main`分支

## 注意事项

- 请勿直接向`main`或`Pre-Release/v2`分支提交代码
- 所有公开API方法必须包含完整注释
- 内部方法应添加`{!--< internal-use >!--}`标签
- 过时方法需标记并提供替代方案
- 如有疑问，请联系 `support@erisdev.com` 或 云湖群ID 635409929

感谢您的贡献！