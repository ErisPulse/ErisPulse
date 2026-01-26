"""
命令模块

导出所有可用的 CLI 命令
"""

from .install import InstallCommand
from .uninstall import UninstallCommand
from .list import ListCommand
from .list_remote import ListRemoteCommand
from .upgrade import UpgradeCommand
from .self_update import SelfUpdateCommand
from .run import RunCommand
from .init import InitCommand

__all__ = [
    "InstallCommand",
    "UninstallCommand",
    "ListCommand",
    "ListRemoteCommand",
    "UpgradeCommand",
    "SelfUpdateCommand",
    "RunCommand",
    "InitCommand",
]
