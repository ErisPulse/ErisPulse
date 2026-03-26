# CLI 擴充開發指南

本指南協助您開發 ErisPulse CLI 的擴充指令。

## CLI 擴充簡介

### 什麼是 CLI 擴充

CLI 擴充功能允許您為 `epsdk` 指令新增自訂指令，擴充架構的命令列功能。

### 使用情境

- 自訂專案產生器
- 第三方工具整合
- 自動化腳本
- 部署和發佈工具

## 專案結構

標準的 CLI 擴充套件結構：

```
my-cli-module/
├── pyproject.toml
├── README.md
├── LICENSE
└── my_cli_module/
    ├── __init__.py
    └── cli.py
```

## 快速開始

### 1. 建立專案

```bash
mkdir my-cli-module && cd my-cli-module
```

### 2. 建立 pyproject.toml

```toml
[project]
name = "my-cli-module"
version = "1.0.0"
description = "我的 CLI 擴充模組"
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

### 3. 實作指令註冊函式

```python
# my_cli_module/cli.py
import argparse
from typing import Any

def my_command_register(subparsers: Any, console: Any) -> None:
    """
    註冊自訂 CLI 指令
    
    :param subparsers: argparse 的子指令解析器
    :param console: 主 CLI 提供的主控台輸出實例
    """
    # 建立指令解析器
    parser = subparsers.add_parser(
        'mycommand',           # 指令名稱
        help='這是一個自訂指令'    # 指令說明
    )
    
    # 新增參數
    parser.add_argument(
        '--option',
        type=str,
        default='default',
        help='指令選項'
    )
    
    # 設定處理函式
    parser.set_defaults(func=handle_command)

def handle_command(args: argparse.Namespace):
    """指令處理函式"""
    console.print("執行自訂指令...")
    
    # 處理邏輯
    if args.option:
        console.print(f"選項值: {args.option}")
    
    # 使用 rich 輸出
    from rich.panel import Panel
    console.print(Panel("指令執行完成", style="success"))
```

### 4. 建立套件入口

```python
# my_cli_module/__init__.py
from .cli import my_command_register
```

## Rich Console 使用
> ErisPulse 使用 [Rich](https://github.com/willmcgugan/rich) 函式庫提供美觀的終端機輸出。
> 您可以不新增相依性來直接匯入 `rich` 函式庫來使用。
CLI 使用 Rich 函式庫提供美觀的終端機輸出：

### 基本輸出

```python
from rich.console import Console
from rich.panel import Panel

console = Console()

# 簡單輸出
console.print("Hello World!")

# 帶樣式的輸出
console.print("成功！", style="green")
console.print("警告！", style="yellow")
console.print("錯誤！", style="red")

# 帶面板的輸出
console.print(Panel("這是面板內容", style="info"))
```

### 表格輸出

```python
from rich.table import Table

table = Table(title="模組列表")

table.add_column("名稱", justify="left")
table.add_column("版本", justify="center")
table.add_column("狀態", justify="center")

table.add_row("Module1", "1.0.0", "[green]啟用")
table.add_row("Module2", "2.0.0", "[red]停用")

console.print(table)
```

### 進度條

```python
from rich.progress import Progress

with Progress() as progress:
    task1 = progress.add_task("下載...", total=100)
    task2 = progress.add_task("安裝...", total=100)
    
    for i in range(100):
        progress.update(task1, advance=1)
        progress.update(task2, advance=1)
```

## 參數處理

### 必要參數

```python
parser.add_argument(
    'input_file',           # 參數名稱
    type=argparse.FileType('r'),  # 參數類型
    help='輸入檔案路徑'
)
```

### 選用參數

```python
parser.add_argument(
    '--output',            # 長參數名稱
    '-o',                # 短參數名稱
    type=str,
    default='output.txt',   # 預設值
    help='輸出檔案路徑'
)
```

### 布林參數

```python
parser.add_argument(
    '--verbose',
    action='store_true',   # store_true 表示布林開關
    help='詳細輸出'
)
```

### 互斥參數

```python
group = parser.add_mutually_exclusive_group()

group.add_argument('--mode1', action='store_true', help='模式 1')
group.add_argument('--mode2', action='store_true', help='模式 2')
```

## 指令組織

### 子指令

```python
# 建立子指令
subparsers = parser.add_subparsers(dest='command', help='子指令')

# 新增子指令
parser_list = subparsers.add_parser('list', help='列表操作')
parser_list.add_argument('--type', help='列表類型')

parser_install = subparsers.add_parser('install', help='安裝操作')
parser_install.add_argument('package', help='套件名稱')

# 在處理函式中判斷子指令
def handle_command(args):
    if args.command == 'list':
        handle_list(args)
    elif args.command == 'install':
        handle_install(args)
```

## 錯誤處理

### 異常捕獲

```python
def handle_command(args: argparse.Namespace):
    try:
        # 業務邏輯
        result = do_something(args.option)
        console.print(Panel(f"結果: {result}", style="success"))
    except ValueError as e:
        # 業務錯誤
        console.print(Panel(f"參數錯誤: {e}", style="warning"))
    except FileNotFoundError as e:
        # 檔案不存在
        console.print(Panel(f"檔案不存在: {e}", style="error"))
    except Exception as e:
        # 未知錯誤
        console.print(Panel(f"發生錯誤: {e}", style="error"))
        raise
```

### 輸入驗證

```python
def handle_command(args: argparse.Namespace):
    # 驗證參數
    if not args.input_file:
        console.print(Panel("必須指定輸入檔案", style="error"))
        return
    
    # 驗證檔案存在
    if not os.path.exists(args.input_file):
        console.print(Panel(f"檔案不存在: {args.input_file}", style="error"))
        return
```

## 整合 ErisPulse API

### 存取 SDK

某些情況下，CLI 擴充可能需要存取 ErisPulse SDK：

```python
from ErisPulse import sdk

def my_command_register(subparsers, console):
    def handle_command(args):
        # 初始化 SDK
        import asyncio
        asyncio.run(sdk.init())
        
        # 使用 SDK 功能
        modules = sdk.module.list_loaded()
        console.print(f"已載入的模組: {modules}")
```

### 操作設定

```python
from ErisPulse.Core import config

def handle_command(args):
    # 取得設定
    config_manager = config.ConfigManager("config.toml")
    my_config = config_manager.getConfig("MyCLI")
    
    console.print(f"設定: {my_config}")
```

## 最佳實務

### 1. 清晰的說明資訊

```python
parser.add_argument(
    '--format',
    choices=['json', 'yaml', 'toml'],
    default='json',
    help='輸出格式'
)
```

### 2. 友善的錯誤提示

```python
from rich.text import Text

def handle_error(error):
    console.print(
        Text(f"錯誤: {error}", style="red bold")
    )
```

### 3. 進度回饋

```python
with Progress() as progress:
    task = progress.add_task("處理中...", total=total)
    
    for item in items:
        # 處理每個項目
        process_item(item)
        progress.update(task, advance=1)
```

### 4. 指令別名

```python
# 可以在主 CLI 中為指令新增別名
# 參考 ErisPulse CLI 的指令註冊機制
```

## 相關文件

- [命令列工具](../../user-guide/cli-reference.md) - 檢視 CLI 指令
- [風格指南](../../styleguide/) - 保持程式碼風格一致