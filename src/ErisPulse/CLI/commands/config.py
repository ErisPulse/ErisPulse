"""
Config 命令实现

交互式配置适配器/模块（schema 驱动向导，含适配器多账户管理）
"""

from argparse import ArgumentParser

from rich.box import SIMPLE
from rich.prompt import Prompt
from rich.table import Table

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils import config_wizard
from ..utils.config_wizard import (
    STATUS_INCOMPLETE,
    STATUS_NONE,
    STATUS_OK,
    STATUS_UNCONFIGURED,
)
from ..utils.display import section_header


class ConfigCommand(Command):
    """
    config 命令

    交互式配置适配器/模块；适配器支持多账户（bot 账户）管理
    """

    name = "config"
    description = i18n.t("cli.config.description")
    aliases = ["cfg", "conf"]

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "name",
            nargs="?",
            help=i18n.t("cli.config.name_help"),
        )
        parser.add_argument(
            "--list",
            "-l",
            action="store_true",
            help=i18n.t("cli.config.list_help"),
        )

    def execute(self, args):
        from ErisPulse import config

        targets = config_wizard.load_config_targets()
        if not targets:
            console.print(f"[dim]  {i18n.t('cli.config.no_targets')}[/]")
            console.print(f"[dim]  {i18n.t('cli.config.install_hint')}[/]")
            return

        if args.name:
            self._run_named(targets, args.name, config)
            return

        self._print_status_table(targets, config)

        if args.list:
            return

        if not config_wizard.is_interactive():
            console.print(f"[dim]  {i18n.t('cli.config.non_interactive_hint')}[/]")
            return

        self._interactive_select(targets, config)

    def _run_named(self, targets, name: str, config):
        """
        按名称定位目标并直接进入向导

        :param targets: ConfigTarget 列表
        :param name: 目标名（适配器平台名/模块名，或适配器配置键）
        :param config: ConfigManager 实例
        """
        for target in targets:
            if target.name == name or target.config_key == name:
                if not target.configurable:
                    console.print(f"[warning]  {i18n.t('cli.config.no_declaration', name=target.name)}[/]")
                    return
                config_wizard.run_wizard(target, config)
                return
        console.print(f"[error]  {i18n.t('cli.config.not_found', name=name)}[/]")

    def _status_text(self, status: str) -> str:
        """
        将状态常量渲染为带颜色的显示文本

        :param status: get_target_status 返回的状态常量
        :return: rich 标记的状态文本
        """
        mapping = {
            STATUS_OK: ("cli.config.status_ok", "green"),
            STATUS_INCOMPLETE: ("cli.config.status_incomplete", "yellow"),
            STATUS_UNCONFIGURED: ("cli.config.status_unconfigured", "cyan"),
            STATUS_NONE: ("cli.config.status_none", "dim"),
        }
        key, style = mapping.get(status, ("cli.config.status_none", "dim"))
        return f"[{style}]{i18n.t(key)}[/]"

    def _print_status_table(self, targets, config):
        """
        打印全部目标及其配置状态表

        :param targets: ConfigTarget 列表
        :param config: ConfigManager 实例
        """
        table = Table(box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False)
        table.add_column(i18n.t("cli.config.header_kind"), width=8)
        table.add_column(i18n.t("cli.config.header_name"), min_width=12)
        table.add_column(i18n.t("cli.config.header_status"), width=10)
        table.add_column(i18n.t("cli.config.header_detail"))

        for target in sorted(targets, key=lambda t: (t.kind != "adapter", t.name.lower())):
            status, errors = config_wizard.get_target_status(target, config)
            detail = "；".join(errors[:3])
            if len(errors) > 3:
                detail += f" (+{len(errors) - 3})"
            kind_style = "adapter" if target.kind == "adapter" else "module"
            table.add_row(
                f"[{kind_style}]{target.kind_label}[/]",
                target.name,
                self._status_text(status),
                detail,
            )

        console.print(table)

    def _interactive_select(self, targets, config):
        """
        交互式选择目标并进入向导（可连续配置多个）

        :param targets: ConfigTarget 列表
        :param config: ConfigManager 实例
        """
        selectable = [t for t in targets if t.configurable]
        if not selectable:
            console.print(f"[dim]  {i18n.t('cli.config.no_configurable')}[/]")
            return

        selectable.sort(key=lambda t: (t.kind != "adapter", t.name.lower()))

        while True:
            section_header(i18n.t("cli.config.select_section"))
            for idx, target in enumerate(selectable, 1):
                status, _ = config_wizard.get_target_status(target, config)
                kind_style = "adapter" if target.kind == "adapter" else "module"
                console.print(f"    [bold]{idx}.[/] [{kind_style}]{target.name}[/]  {self._status_text(status)}")

            try:
                raw = Prompt.ask(
                    f"  {i18n.t('cli.config.select_prompt')}",
                    default="",
                    show_default=False,
                )
            except (EOFError, KeyboardInterrupt):
                break

            raw = raw.strip()
            if not raw:
                break

            try:
                idx = int(raw)
            except ValueError:
                console.print(f"[warning]  {i18n.t('cli.config.invalid_index', idx=raw)}[/]")
                continue

            if not 1 <= idx <= len(selectable):
                console.print(f"[warning]  {i18n.t('cli.config.invalid_index', idx=idx)}[/]")
                continue

            config_wizard.run_wizard(selectable[idx - 1], config)
            # 向导结束后回到选择菜单（状态重新刷新），支持连续配置多个目标
