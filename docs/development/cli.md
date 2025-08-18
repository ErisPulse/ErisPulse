# ErisPulse CLI 模块开发指南
> 从 2.1.6 版本开始，ErisPulse支持第三方CLI模块，允许用户通过`epsdk`命令调用自定义的命令。

## 创建第三方CLI模块

### 1. 项目结构
创建一个标准的Python包，建议结构如下：
```
my_cli_module/
├── my_cli_module/
│   ├── __init__.py   # 建议这里import你的命令注册函数
│   └── cli.py        # CLI命令实现
├── pyproject.toml    # 项目配置
├── README.md         # 项目说明
└── LICENSE           # 项目许可证
```

### 2. 实现CLI命令

在`cli.py`中实现命令注册函数：

```python
import argparse
from typing import Any
from rich.panel import Panel

def my_command_register(subparsers: Any, console: Any) -> None:
    """
    注册自定义CLI命令
    
    参数:
        subparsers: argparse的子命令解析器
        console: 主CLI提供的控制台输出实例
    """
    # 创建命令解析器
    parser = subparsers.add_parser(
        'yourcommand',  # 命令名称
        help='你的命令描述'
    )
    
    # 添加参数
    parser.add_argument(
        '--option',
        type=str,
        default='default',
        help='选项描述'
    )
    
    # 命令处理函数
    def handle_command(args: argparse.Namespace):
        try:
            console.print(Panel("命令开始执行", style="info"))
            
            # 你的命令逻辑
            console.print(f"执行操作，选项值: {args.option}")
            
            console.print(Panel("命令执行完成", style="success"))
        except Exception as e:
            console.print(Panel(f"错误: {e}", style="error"))
            raise
    
    # 设置处理函数
    parser.set_defaults(func=handle_command)
```

### 3. 配置项目

在`pyproject.toml`中声明入口点：

```toml
[project]
name = "your-module-name"
version = "1.0.0"
dependencies = ["ErisPulse>=2.1.6"]

[project.entry-points."erispulse.cli"]
"yourcommand" = "my_cli_module:your_command_register"
```

### 4. 安装测试

```bash
# 开发模式安装
pip install -e .

# 测试命令
epsdk yourcommand --option value
```
