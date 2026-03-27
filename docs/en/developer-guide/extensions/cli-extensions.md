# CLI Extension Development Guide

This guide helps you develop extension commands for the ErisPulse CLI.

## Introduction to CLI Extensions

### What is a CLI Extension

CLI extensions allow you to add custom commands to the `epsdk` command, extending the command-line capabilities of the framework.

### Use Cases

- Custom project generators
- Third-party tool integration
- Automation scripts
- Deployment and release tools

## Project Structure

Standard CLI extension package structure:

```
my-cli-module/
├── pyproject.toml
├── README.md
├── LICENSE
└── my_cli_module/
    ├── __init__.py
    └── cli.py
```

## Quick Start

### 1. Create Project

```bash
mkdir my-cli-module && cd my-cli-module
```

### 2. Create pyproject.toml

```toml
[project]
name = "my-cli-module"
version = "1.0.0"
description = "My CLI extension module"
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

### 3. Implement Command Registration Function

```python
# my_cli_module/cli.py
import argparse
from typing import Any

def my_command_register(subparsers: Any, console: Any) -> None:
    """
    Register custom CLI command
    
    :param subparsers: Sub-command parser from argparse
    :param console: Console output instance provided by the main CLI (rich Console)
    """
    # Create command parser
    parser = subparsers.add_parser(
        'mycommand',           # Command name
        help='This is a custom command'    # Command help
    )
    
    # Add arguments
    parser.add_argument(
        '--option',
        type=str,
        default='default',
        help='Command option'
    )
    
    # Set handler function
    parser.set_defaults(func=handle_command)

def handle_command(args: argparse.Namespace):
    """Command handler function"""
    console.print("Executing custom command...")
    
    # Processing logic
    if args.option:
        console.print(f"Option value: {args.option}")
    
    # Use rich for output
    from rich.panel import Panel
    console.print(Panel("Command execution completed", style="success"))
```

### 4. Create Package Entry

```python
# my_cli_module/__init__.py
from .cli import my_command_register
```

## Using Rich Console
> ErisPulse uses the [Rich](https://github.com/willmcgugan/rich) library to provide beautiful terminal output.
> You can import the `rich` library directly without adding dependencies to use it.
The CLI uses the Rich library to provide beautiful terminal output:

### Basic Output

```python
from rich.console import Console
from rich.panel import Panel

console = Console()

# Simple output
console.print("Hello World!")

# Styled output
console.print("Success!", style="green")
console.print("Warning!", style="yellow")
console.print("Error!", style="red")

# Output with panel
console.print(Panel("This is panel content", style="info"))
```

### Table Output

```python
from rich.table import Table

table = Table(title="Module List")

table.add_column("Name", justify="left")
table.add_column("Version", justify="center")
table.add_column("Status", justify="center")

table.add_row("Module1", "1.0.0", "[green]Enabled")
table.add_row("Module2", "2.0.0", "[red]Disabled")

console.print(table)
```

### Progress Bar

```python
from rich.progress import Progress

with Progress() as progress:
    task1 = progress.add_task("Downloading...", total=100)
    task2 = progress.add_task("Installing...", total=100)
    
    for i in range(100):
        progress.update(task1, advance=1)
        progress.update(task2, advance=1)
```

## Argument Handling

### Required Arguments

```python
parser.add_argument(
    'input_file',           # Argument name
    type=argparse.FileType('r'),  # Argument type
    help='Input file path'
)
```

### Optional Arguments

```python
parser.add_argument(
    '--output',            # Long option name
    '-o',                # Short option name
    type=str,
    default='output.txt',   # Default value
    help='Output file path'
)
```

### Boolean Arguments

```python
parser.add_argument(
    '--verbose',
    action='store_true',   # store_true indicates boolean switch
    help='Verbose output'
)
```

### Mutually Exclusive Arguments

```python
group = parser.add_mutually_exclusive_group()

group.add_argument('--mode1', action='store_true', help='Mode 1')
group.add_argument('--mode2', action='store_true', help='Mode 2')
```

## Command Organization

### Subcommands

```python
# Create subcommand
subparsers = parser.add_subparsers(dest='command', help='Subcommands')

# Add subcommands
parser_list = subparsers.add_parser('list', help='List operation')
parser_list.add_argument('--type', help='List type')

parser_install = subparsers.add_parser('install', help='Install operation')
parser_install.add_argument('package', help='Package name')

# Check subcommand in handler function
def handle_command(args):
    if args.command == 'list':
        handle_list(args)
    elif args.command == 'install':
        handle_install(args)
```

## Error Handling

### Exception Handling

```python
def handle_command(args: argparse.Namespace):
    try:
        # Business logic
        result = do_something(args.option)
        console.print(Panel(f"Result: {result}", style="success"))
    except ValueError as e:
        # Business error
        console.print(Panel(f"Argument error: {e}", style="warning"))
    except FileNotFoundError as e:
        # File not found
        console.print(Panel(f"File not found: {e}", style="error"))
    except Exception as e:
        # Unknown error
        console.print(Panel(f"An error occurred: {e}", style="error"))
        raise
```

### Input Validation

```python
def handle_command(args: argparse.Namespace):
    # Validate arguments
    if not args.input_file:
        console.print(Panel("Must specify input file", style="error"))
        return
    
    # Verify file exists
    if not os.path.exists(args.input_file):
        console.print(Panel(f"File not found: {args.input_file}", style="error"))
        return
```

## Integrating ErisPulse API

### Accessing SDK

In some cases, CLI extensions may need to access the ErisPulse SDK:

```python
from ErisPulse import sdk

def my_command_register(subparsers, console):
    def handle_command(args):
        # Initialize SDK
        import asyncio
        asyncio.run(sdk.init())
        
        # Use SDK features
        modules = sdk.module.list_loaded()
        console.print(f"Loaded modules: {modules}")
```

### Managing Configuration

```python
from ErisPulse.Core import config

def handle_command(args):
    # Get configuration
    config_manager = config.ConfigManager("config.toml")
    my_config = config_manager.getConfig("MyCLI")
    
    console.print(f"Configuration: {my_config}")
```

## Best Practices

### 1. Clear Help Information

```python
parser.add_argument(
    '--format',
    choices=['json', 'yaml', 'toml'],
    default='json',
    help='Output format (json/yaml/toml)'
)
```

### 2. Friendly Error Messages

```python
from rich.text import Text

def handle_error(error):
    console.print(
        Text(f"Error: {error}", style="red bold")
    )
```

### 3. Progress Feedback

```python
with Progress() as progress:
    task = progress.add_task("Processing...", total=total)
    
    for item in items:
        # Process each item
        process_item(item)
        progress.update(task, advance=1)
```

### 4. Command Aliases

```python
# You can add aliases for commands in the main CLI
# Refer to the ErisPulse CLI command registration mechanism
```

## Related Documentation

- [Command Line Tools](../../user-guide/cli-reference.md) - View CLI commands
- [Style Guide](../../styleguide/) - Maintain consistent code style