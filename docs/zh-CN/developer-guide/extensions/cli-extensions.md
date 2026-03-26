# CLI 扩展开发指南

本指南帮助你开发 ErisPulse CLI 的扩展命令。

## CLI 扩展简介

### 什么是 CLI 扩展

CLI 扩展允许你为 `epsdk` 命令添加自定义命令，扩展框架的命令行功能。

### 使用场景

- 自定义项目生成器
- 第三方工具集成
- 自动化脚本
- 部署和发布工具

## 项目结构

标准的 CLI 扩展包结构：

```
my-cli-module/
├── pyproject.toml
├── README.md
├── LICENSE
└── my_cli_module/
    ├── __init__.py
    └── cli.py
```

## 快速开始

### 1. 创建项目

```bash
mkdir my-cli-module && cd my-cli-module
```

### 2. 创建 pyproject.toml

```toml
[project]
name = "my-cli-module"
version = "1.0.0"
description = "我的 CLI 扩展模块"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = [
    "ErisPulse>=2.1.6"
]

[project.urls]
"homepage" = "https://github.com/yourname/my-cli-module"

[project.entry-points."erispulse.cli"]
"mycommand" = "my_cli_module:my_command_register"
```

### 3. 实现命令注册函数

```python
# my_cli_module/cli.py
import argparse
from typing import Any

def my_command_register(subparsers: Any, console: Any) -> None:
    """
    注册自定义 CLI 命令
    
    :param subparsers: argparse 的子命令解析器
    :param console: 主 CLI 提供的控制台输出实例（rich Console）
    """
    # 创建命令解析器
    parser = subparsers.add_parser(
        'mycommand',           # 命令名称
        help='这是一个自定义命令'    # 命令帮助
    )
    
    # 添加参数
    parser.add_argument(
        '--option',
        type=str,
        default='default',
        help='命令选项'
    )
    
    # 设置处理函数
    parser.set_defaults(func=handle_command)

def handle_command(args: argparse.Namespace):
    """命令处理函数"""
    console.print("执行自定义命令...")
    
    # 处理逻辑
    if args.option:
        console.print(f"选项值: {args.option}")
    
    # 使用 rich 输出
    from rich.panel import Panel
    console.print(Panel("命令执行完成", style="success"))
```

### 4. 创建包入口

```python
# my_cli_module/__init__.py
from .cli import my_command_register
```

## Rich Console 使用
> ErisPulse 使用 [Rich](https://github.com/willmcgugan/rich) 库提供美观的终端输出。
> 你可以不添加依赖来直接导入 `rich` 库来使用。
CLI 使用 Rich 库提供美观的终端输出：

### 基本输出

```python
from rich.console import Console
from rich.panel import Panel

console = Console()

# 简单输出
console.print("Hello World!")

# 带样式的输出
console.print("成功！", style="green")
console.print("警告！", style="yellow")
console.print("错误！", style="red")

# 带面板的输出
console.print(Panel("这是面板内容", style="info"))
```

### 表格输出

```python
from rich.table import Table

table = Table(title="模块列表")

table.add_column("名称", justify="left")
table.add_column("版本", justify="center")
table.add_column("状态", justify="center")

table.add_row("Module1", "1.0.0", "[green]启用")
table.add_row("Module2", "2.0.0", "[red]禁用")

console.print(table)
```

### 进度条

```python
from rich.progress import Progress

with Progress() as progress:
    task1 = progress.add_task("下载...", total=100)
    task2 = progress.add_task("安装...", total=100)
    
    for i in range(100):
        progress.update(task1, advance=1)
        progress.update(task2, advance=1)
```

## 参数处理

### 必需参数

```python
parser.add_argument(
    'input_file',           # 参数名
    type=argparse.FileType('r'),  # 参数类型
    help='输入文件路径'
)
```

### 可选参数

```python
parser.add_argument(
    '--output',            # 长参数名
    '-o',                # 短参数名
    type=str,
    default='output.txt',   # 默认值
    help='输出文件路径'
)
```

### 布尔参数

```python
parser.add_argument(
    '--verbose',
    action='store_true',   # store_true 表示布尔开关
    help='详细输出'
)
```

### 互斥参数

```python
group = parser.add_mutually_exclusive_group()

group.add_argument('--mode1', action='store_true', help='模式1')
group.add_argument('--mode2', action='store_true', help='模式2')
```

## 命令组织

### 子命令

```python
# 创建子命令
subparsers = parser.add_subparsers(dest='command', help='子命令')

# 添加子命令
parser_list = subparsers.add_parser('list', help='列表操作')
parser_list.add_argument('--type', help='列表类型')

parser_install = subparsers.add_parser('install', help='安装操作')
parser_install.add_argument('package', help='包名')

# 在处理函数中判断子命令
def handle_command(args):
    if args.command == 'list':
        handle_list(args)
    elif args.command == 'install':
        handle_install(args)
```

## 错误处理

### 异常捕获

```python
def handle_command(args: argparse.Namespace):
    try:
        # 业务逻辑
        result = do_something(args.option)
        console.print(Panel(f"结果: {result}", style="success"))
    except ValueError as e:
        # 业务错误
        console.print(Panel(f"参数错误: {e}", style="warning"))
    except FileNotFoundError as e:
        # 文件不存在
        console.print(Panel(f"文件不存在: {e}", style="error"))
    except Exception as e:
        # 未知错误
        console.print(Panel(f"发生错误: {e}", style="error"))
        raise
```

### 输入验证

```python
def handle_command(args: argparse.Namespace):
    # 验证参数
    if not args.input_file:
        console.print(Panel("必须指定输入文件", style="error"))
        return
    
    # 验证文件存在
    if not os.path.exists(args.input_file):
        console.print(Panel(f"文件不存在: {args.input_file}", style="error"))
        return
```

## 集成 ErisPulse API

### 访问 SDK

某些情况下，CLI 扩展可能需要访问 ErisPulse SDK：

```python
from ErisPulse import sdk

def my_command_register(subparsers, console):
    def handle_command(args):
        # 初始化 SDK
        import asyncio
        asyncio.run(sdk.init())
        
        # 使用 SDK 功能
        modules = sdk.module.list_loaded()
        console.print(f"已加载的模块: {modules}")
```

### 操作配置

```python
from ErisPulse.Core import config

def handle_command(args):
    # 获取配置
    config_manager = config.ConfigManager("config.toml")
    my_config = config_manager.getConfig("MyCLI")
    
    console.print(f"配置: {my_config}")
```

## 最佳实践

### 1. 清晰的帮助信息

```python
parser.add_argument(
    '--format',
    choices=['json', 'yaml', 'toml'],
    default='json',
    help='输出格式（json/yaml/toml）'
)
```

### 2. 友好的错误提示

```python
from rich.text import Text

def handle_error(error):
    console.print(
        Text(f"错误: {error}", style="red bold")
    )
```

### 3. 进度反馈

```python
with Progress() as progress:
    task = progress.add_task("处理中...", total=total)
    
    for item in items:
        # 处理每个项目
        process_item(item)
        progress.update(task, advance=1)
```

### 4. 命令别名

```python
# 可以在主 CLI 中为命令添加别名
# 参考 ErisPulse CLI 的命令注册机制
```

## 相关文档

- [命令行工具](../../user-guide/cli-reference.md) - 查看 CLI 命令
- [风格指南](../../styleguide/) - 保持代码风格一致