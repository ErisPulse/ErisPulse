"""
CLI 模块

ErisPulse 命令行接口

{!--< internal-use >!--}
CLI 拥有独立的国际化模块 (CLI.i18n)，与 Core.i18n 完全解耦。
此模块仅供内部使用，外部模块不应直接依赖 CLI.i18n。
{!--< /internal-use >!--}
"""

from .cli import CLI
from .i18n import i18n as _cli_i18n

__all__ = [
    "CLI",
]
