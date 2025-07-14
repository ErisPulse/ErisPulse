# ErisPulse 模块迁移指南：从传统方式到PyPI包

## 概述

本文档指导你将现有的ErisPulse模块从传统的目录扫描方式迁移到PyPI包方式

## 迁移步骤

### 1. 创建包结构

将现有模块转换为标准Python包结构：

```
my_module/
├── pyproject.toml   # 包配置文件
├── my_module/
│   ├── __init__.py
│   └── Core.py   # 原Core.py内容
```

### 2. 配置包信息

在`pyproject.toml`中定义模块信息（请不要使用`setup.py`进行配置）：

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "My awesome module"
readme = "README.md"
requires-python = ">=3.8"
license = { file = "LICENSE" }
urls = { "https://github.com/your-username/your-module" }
authors = [
    { name = "Your Name", email = "your@email.com" }
]
dependencies = []

# 定义模块信息
[project.entry-points]
"erispulse.module"  = { "my_module" = "my_module.core:Main" }

[tool.erispulse.dependencies]
requires = ["OneBotAdapter"]     # 必须的erispulse包内依赖模块
optional = ["YunhuAdapter"]      # 可选的erispulse包内依赖模块
```

## 依赖配置处理的逻辑

1. **显式配置优先**：
   ```toml
   [tool.erispulse.dependencies]
   requires = ["OneBotAdapter"]  # 必须的依赖模块
   optional = ["YunhuAdapter"]   # 可选的依赖模块
   ```
   - 系统会构建完整的依赖图
   - 使用拓扑排序确定加载顺序

2. **自动推断模式**：
   - 分析PyPI包的`requires`元数据
   - 只识别 包含模块/适配器 信息的模块

### 3. 修改模块代码

移除`__init__.py`中的`moduleInfo`定义，只保留：

```python
from .Core import Main
```

### 4. 构建并发布包

```bash
# 安装构建工具
pip install build

# 构建包
python -m build

# 发布到PyPI
pip install twine
twine upload dist/*
```

## 验证迁移

1. 安装新包：
```bash
pip install erispulse-my-module
```

2. 检查模块加载：
```python
from ErisPulse import sdk
sdk.init()
print(hasattr(sdk, 'my_module'))  # 应该返回True
```

3. 查看日志确认：
```
[Init] 模块 my_module 已从包配置加载
```

## 注意事项
**适配器迁移**：
适配器迁移方式类似，使用`erispulse-adapter`作为entry-point组名, 但是有特殊要求：

强烈推荐创建一个事件解析模块，用于处理适配器事件(这是推荐做法, 虽然你也可以不做,但这会使得该适配器的模块适性变得很差)

```toml
[project.entry-points]
"erispulse.module" = { "MyAdapterEventTools" = "MyAdapter:MyAdapterEventParser"}
"erispulse.adapter" = { "MyAdapter" = "MyAdapter:MyPlatformAdapter" }
```

## FAQ

**Q: 迁移后模块还能放在modules目录下吗？**

A: 直到 `2.1.0` 之前都会保持维护，当前版本已弃用使用模块目录

**Q: 多个模块可以打包在一个包中吗？** 

A: 可以，但建议每个模块单独打包到一个包中
