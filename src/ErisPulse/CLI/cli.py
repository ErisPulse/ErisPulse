"""
主 CLI 类

ErisPulse 命令行接口主入口
"""

import sys
import importlib
import importlib.metadata
import asyncio
import traceback
import pkgutil
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from rich.panel import Panel

from .console import console
from .registry import CommandRegistry
from .base import Command


class CLI:
    """
    ErisPulse 命令行接口主类
    
    提供完整的命令行交互功能，支持动态加载第三方命令
    """
    
    def __init__(self):
        """初始化 CLI"""
        self.registry = CommandRegistry()
        self.parser = self._create_parser()
        self._register_builtin_commands()
        self._load_external_commands()
    
    def _create_parser(self) -> ArgumentParser:
        """
        创建命令行参数解析器
        
        :return: 配置好的 ArgumentParser 实例
        """
        parser = ArgumentParser(
            prog="epsdk",
            formatter_class=RawDescriptionHelpFormatter,
            description="ErisPulse SDK 命令行工具",
        )
        parser._positionals.title = "命令"
        parser._optionals.title = "选项"
        
        # 全局选项
        parser.add_argument(
            "--version", "-V",
            action="store_true",
            help="显示版本信息"
        )
        parser.add_argument(
            "--verbose", "-v",
            action="count",
            default=0,
            help="增加输出详细程度 (-v, -vv, -vvv)"
        )
        
        # 子命令
        subparsers = parser.add_subparsers(
            dest='command',
            metavar="<命令>",
            help="要执行的操作"
        )
        
        self.subparsers = subparsers
        return parser
    
    def _auto_discover_commands(self):
        """
        自动发现并注册 commands 目录中的所有命令
        
        动态扫描 commands 目录，查找所有继承自 Command 基类的命令类
        并自动注册到命令注册表中。
        """
        # 获取 commands 包的路径
        commands_package = 'ErisPulse.CLI.commands'
        
        try:
            # 遍历 commands 包中的所有模块
            for importer, module_name, ispkg in pkgutil.iter_modules(
                importlib.import_module(commands_package).__path__,
                prefix=f"{commands_package}."
            ):
                # 跳过 __init__ 和 __pycache__ 目录
                if module_name.endswith('.__init__') or '__pycache__' in module_name:
                    continue
                
                try:
                    # 动态导入模块
                    module = importlib.import_module(module_name)
                    
                    # 查找模块中所有继承自 Command 的类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        # 检查是否是 Command 的子类（排除 Command 基类本身）
                        if (isinstance(attr, type) and 
                            issubclass(attr, Command) and 
                            attr is not Command):
                            try:
                                # 实例化并注册命令
                                command_instance = attr()
                                self.registry.register(command_instance)
                            except Exception as e:
                                console.print(f"[warning]实例化命令 {attr_name} 失败: {e}[/]")
                                
                except Exception as e:
                    console.print(f"[warning]加载命令模块 {module_name} 失败: {e}[/]")
                    
        except ImportError as e:
            console.print(f"[warning]无法导入 commands 包: {e}[/]")
    
    def _register_builtin_commands(self):
        """注册所有内置命令（通过自动发现）"""
        self._auto_discover_commands()
        
        # 添加所有命令的参数
        for command in self.registry.get_all():
            parser = self.subparsers.add_parser(
                command.name,
                help=command.description
            )
            command.add_arguments(parser)
    
    def _load_external_commands(self):
        """
        加载第三方 CLI 命令
        """
        try:
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                cli_entries = entry_points.select(group='erispulse.cli')
            else:
                cli_entries = entry_points.get('erispulse.cli', [])
            
            for entry in cli_entries:
                try:
                    cli_func = entry.load()
                    if callable(cli_func):
                        # 传入 subparsers 和 console，保持兼容性
                        cli_func(self.subparsers, console)
                    else:
                        console.print(f"[warning]模块 {entry.name} 的入口点不是可调用对象[/]")
                except Exception as e:
                    console.print(f"[error]加载第三方命令 {entry.name} 失败: {e}[/]")
        except Exception as e:
            console.print(f"[warning]加载第三方CLI命令失败: {e}[/]")
    
    def _print_version(self):
        """打印版本信息"""
        from ErisPulse import __version__
        console.print(Panel(
            f"[title]ErisPulse SDK[/] 版本: [bold]{__version__}[/]",
            subtitle=f"Python {sys.version.split()[0]}",
            style="title"
        ))
    
    def run(self):
        """
        运行 CLI
        
        :raises KeyboardInterrupt: 用户中断时抛出
        :raises Exception: 命令执行失败时抛出
        """
        args = self.parser.parse_args()
        
        # 处理版本选项
        if args.version:
            self._print_version()
            return
        
        # 没有指定命令时显示帮助
        if not args.command:
            self.parser.print_help()
            return
        
        try:
            # 执行命令
            command = self.registry.get(args.command)
            if command:
                command.execute(args)
            else:
                # 第三方命令处理
                self._execute_external_command(args)
                
        except KeyboardInterrupt:
            console.print("\n[warning]操作被用户中断[/]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[error]执行命令时出错: {e}[/]")
            if args.verbose >= 1:
                console.print(traceback.format_exc())
            sys.exit(1)
    
    def _execute_external_command(self, args):
        """
        执行第三方命令
        
        :param args: 解析后的参数
        """
        try:
            # 第三方命令在注册时已经通过 set_defaults(func=handle_command) 设置了处理函数
            # 所以 args.func 就是处理函数
            if hasattr(args, 'func') and args.func:
                handler_func = args.func
                if asyncio.iscoroutinefunction(handler_func):
                    # 异步函数：使用 asyncio.run() 运行
                    asyncio.run(handler_func(args))
                else:
                    # 同步函数：直接调用
                    handler_func(args)
            else:
                console.print(f"[error]命令 {args.command} 没有处理函数[/]")
                sys.exit(1)
        except Exception as e:
            console.print(f"[error]执行第三方命令失败: {e}[/]")
            if args.verbose >= 1:
                console.print(traceback.format_exc())
            sys.exit(1)
