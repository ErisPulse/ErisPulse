"""
Version 命令实现

显示 ErisPulse SDK 与运行时版本信息
"""

import platform
import sys

from rich.panel import Panel

from ..base import Command
from ..console import console
from ..i18n import i18n


class VersionCommand(Command):
    """
    version 命令

    显示 ErisPulse SDK 与 Python 运行时版本信息（与 ``epsdk -V`` 等效）
    """

    name = "version"
    description = i18n.t("cli.version.description")
    aliases = ["ver"]

    def add_arguments(self, parser):
        """version 命令无额外参数"""

    def execute(self, args):
        """
        输出版本信息面板

        :param args: 解析后的参数对象
        """
        from ErisPulse import __version__

        console.print(
            Panel(
                f"[title]{i18n.t('cli.run.version_text', version=__version__)}[/]",
                subtitle=f"Python {platform.python_version()} ({sys.executable})",
                style="title",
            )
        )


__all__ = ["VersionCommand"]
