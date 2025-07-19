"""
ErisPulse CLI模块示例 - 灵活版本

演示如何创建第三方CLI模块扩展主CLI功能
"""

import argparse
from typing import Any
from rich.panel import Panel

def example_cli_register(subparsers: Any, console: Any) -> None:
    """
    示例CLI注册函数
    
    :param subparsers: argparse的子命令解析器
    :param console: 主CLI提供的控制台输出实例
    """
    # 创建示例命令解析器
    example_parser = subparsers.add_parser(
        'example',
        help='示例命令演示第三方CLI功能'
    )
    example_parser.add_argument(
        '--name',
        type=str,
        default='World',
        help='指定问候的名称 (默认: World)'
    )
    example_parser.add_argument(
        '--repeat',
        type=int,
        default=1,
        help='重复次数 (默认: 1)'
    )
    
    def handle_example(args: argparse.Namespace):
        """实际处理函数"""
        try:
            console.print(Panel(
                f"来自第三方CLI模块的问候!",
                title="示例命令",
                style="info"
            ))
            
            for i in range(args.repeat):
                console.print(f"Hello {args.name}! ({i+1}/{args.repeat})")
                
            console.print(Panel(
                "命令执行完成",
                style="success"
            ))
        except Exception as e:
            console.print(Panel(
                f"命令执行失败: {e}",
                title="错误",
                style="error"
            ))
            raise
    
    # 设置处理函数
    example_parser.set_defaults(func=handle_example)
