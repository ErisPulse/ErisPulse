"""
主 CLI 类

ErisPulse 命令行接口主入口
"""

import sys
import importlib.metadata
import asyncio
import traceback
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from rich.panel import Panel

from ..console import console
from .registry import CommandRegistry
from .commands import (
    InstallCommand,
    UninstallCommand,
    ListCommand,
    ListRemoteCommand,
    UpgradeCommand,
    SelfUpdateCommand,
    RunCommand,
    InitCommand,
)


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
            description="ErisPulse SDK 命令行工具\n\n一个功能强大的模块化系统管理工具，用于管理ErisPulse生态系统中的模块、适配器和扩展。",
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
    
    def _register_builtin_commands(self):
        """注册所有内置命令"""
        self.registry.register(InstallCommand())
        self.registry.register(UninstallCommand())
        self.registry.register(ListCommand())
        self.registry.register(ListRemoteCommand())
        self.registry.register(UpgradeCommand())
        self.registry.register(SelfUpdateCommand())
        self.registry.register(RunCommand())
        self.registry.register(InitCommand())
        
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
