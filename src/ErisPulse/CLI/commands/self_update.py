"""
Self-Update 命令实现

更新 ErisPulse SDK 本身
"""

import asyncio
import sys
from argparse import ArgumentParser

from rich.box import SIMPLE
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils import PackageManager
from ..utils.display import _input, section_header


class SelfUpdateCommand(Command):
    """
    self-update 命令

    更新 ErisPulse SDK 本身
    """

    name = "self-update"
    description = i18n.t("cli.self_update.description")
    aliases = ["su", "update"]

    def __init__(self):
        """
        初始化 SelfUpdateCommand，创建包管理器实例
        """
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "version", nargs="?", help=i18n.t("cli.self_update.version_help")
        )
        parser.add_argument(
            "--pre", action="store_true", help=i18n.t("cli.self_update.pre_help")
        )
        parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help=i18n.t("cli.self_update.force_help"),
        )
        parser.add_argument(
            "--no-uv", action="store_true", help=i18n.t("cli.self_update.no_uv_help")
        )

    def execute(self, args):
        self.package_manager.no_uv = getattr(args, "no_uv", False)
        current_version = self.package_manager.get_installed_version()
        console.print(
            i18n.t("cli.self_update.current_version", version=current_version)
        )

        with console.status(
            f"[bold green]{i18n.t('cli.self_update.fetching')}[/]", spinner="dots"
        ):
            versions = asyncio.run(self.package_manager.get_pypi_versions())

        if not versions:
            console.print(f"[error]{i18n.t('cli.self_update.fetch_failed')}[/]")
            sys.exit(1)

        target_version = self._select_target_version(versions, args.version, args.pre)

        if target_version is None:
            console.print(f"[info]{i18n.t('cli.self_update.cancelled')}[/]")
            sys.exit(0)

        if target_version == current_version and not args.force:
            console.print(
                f"[info]{i18n.t('cli.self_update.already_latest', version=current_version)}[/]"
            )
            sys.exit(0)
        elif not args.force:
            if not Confirm.ask(
                i18n.t(
                    "cli.self_update.confirm_update",
                    current=current_version,
                    target=target_version,
                ),
                default=False,
            ):
                console.print(f"[info]{i18n.t('cli.self_update.cancelled')}[/]")
                sys.exit(0)

        success = self.package_manager.update_self(target_version, args.force)
        if not success:
            sys.exit(1)

    def _select_target_version(
        self, versions, specified_version: str = None, include_pre: bool = False
    ) -> str:
        """
        交互式选择目标更新版本

        :param versions: [list] 可用版本信息列表
        :param specified_version: [str] 指定的版本号 (默认: None)
        :param include_pre: [bool] 是否包含预发布版本 (默认: False)

        :return: [str] 选定的目标版本号，取消时返回 None
        """
        if specified_version:
            if not any(v["version"] == specified_version for v in versions):
                console.print(
                    f"[warning]{i18n.t('cli.self_update.version_not_found', version=specified_version)}[/]"
                )
                if not Confirm.ask(
                    i18n.t("cli.self_update.confirm_continue"), default=False
                ):
                    return None
            return specified_version

        stable_versions = [v for v in versions if not v["pre_release"]]
        pre_versions = [v for v in versions if v["pre_release"]]

        latest_stable = stable_versions[0] if stable_versions else None
        latest_pre = pre_versions[0] if pre_versions and include_pre else None

        section_header(i18n.t("cli.self_update.section_title"))

        options = []
        if latest_stable:
            console.print(
                Text(
                    f"    1.  {i18n.t('cli.self_update.latest_stable', version=latest_stable['version'])}",
                    style="success",
                )
            )
            options.append(latest_stable["version"])
        if include_pre and latest_pre:
            idx = len(options) + 1
            console.print(
                Text(
                    f"    {idx}.  {i18n.t('cli.self_update.latest_pre', version=latest_pre['version'])}",
                    style="warning",
                )
            )
            options.append(latest_pre["version"])

        next_idx = len(options) + 1
        console.print(
            Text(f"    {next_idx}.  {i18n.t('cli.self_update.view_all')}", style="info")
        )
        options.append("all")

        next_idx2 = len(options) + 1
        console.print(
            Text(
                f"    {next_idx2}.  {i18n.t('cli.self_update.manual_version')}",
                style="info",
            )
        )
        options.append("manual")

        cancel_idx = len(options) + 1
        console.print(
            Text(f"    {cancel_idx}.  {i18n.t('cli.self_update.cancel')}", style="dim")
        )
        options.append("cancel")

        while True:
            try:
                selected_input = Prompt.ask(
                    f"\n  {i18n.t('cli.self_update.enter_option')}", default="1"
                )
                if selected_input.isdigit():
                    idx = int(selected_input)
                    if 1 <= idx <= len(options):
                        selected = options[idx - 1]
                        break
                    else:
                        console.print(
                            f"[warning]{i18n.t('cli.self_update.invalid_option')}[/]"
                        )
                else:
                    console.print(
                        f"[warning]{i18n.t('cli.self_update.enter_number')}[/]"
                    )
            except KeyboardInterrupt:
                console.print(f"\n[info]{i18n.t('cli.self_update.cancelled')}[/]")
                return None

        if selected == "cancel":
            return None
        elif selected == "manual":
            target_version = Prompt.ask(f"  {i18n.t('cli.self_update.enter_version')}")
            if not any(v["version"] == target_version for v in versions):
                console.print(
                    f"[warning]{i18n.t('cli.self_update.version_not_found', version=target_version)}[/]"
                )
                if not Confirm.ask(
                    i18n.t("cli.self_update.confirm_continue"), default=False
                ):
                    return None
            return target_version
        elif selected == "all":
            return self._select_from_version_list(versions, include_pre)
        else:
            return selected

    def _select_from_version_list(self, versions, include_pre: bool = False) -> str:
        """
        以分页列表形式展示版本并供用户选择

        :param versions: [list] 可用版本信息列表
        :param include_pre: [bool] 是否包含预发布版本 (默认: False)

        :return: [str] 选定的目标版本号，返回时返回 None
        """
        from ..utils.display import _page_size

        filtered = [v for v in versions if include_pre or not v["pre_release"]]

        if not filtered:
            console.print(f"[info]{i18n.t('cli.self_update.no_versions')}[/]")
            return None

        ps = _page_size()
        total = len(filtered)
        page_start = 0

        while True:
            table = Table(
                box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False
            )
            table.add_column(
                i18n.t("cli.self_update.header_index"), width=4, style="#A0B0C0"
            )
            table.add_column(i18n.t("cli.self_update.header_version"), min_width=14)
            table.add_column(i18n.t("cli.self_update.header_type"), width=8)
            table.add_column(i18n.t("cli.self_update.header_upload"), width=12)

            batch = filtered[page_start : page_start + ps]
            for i, v in enumerate(batch):
                vtype = (
                    f"[warning]{i18n.t('cli.self_update.type_pre')}[/]"
                    if v["pre_release"]
                    else f"[success]{i18n.t('cli.self_update.type_stable')}[/]"
                )
                table.add_row(
                    str(page_start + i + 1),
                    v["version"],
                    vtype,
                    v["uploaded"][:10]
                    if v["uploaded"]
                    else i18n.t("cli.self_update.unknown_upload"),
                )
            console.print(table)
            console.print(
                f"[dim]  {i18n.t('cli.self_update.total_versions', total=total)}[/]"
            )

            has_prev = page_start > 0
            has_next = page_start + ps < total
            nav = []
            if has_prev:
                nav.append(i18n.t("cli.self_update.nav_prev"))
            if has_next:
                nav.append(i18n.t("cli.self_update.nav_next"))
            nav_text = ", ".join(nav) + ", " if nav else ""
            version_input = _input(
                f"{nav_text}{i18n.t('cli.self_update.nav_return')} >"
            )

            if version_input.lower() == "q":
                return None
            if version_input.lower() == "n" and has_next:
                page_start += ps
                continue
            if version_input.lower() == "p" and has_prev:
                page_start = max(0, page_start - ps)
                continue
            if version_input.strip():
                result = self._parse_version_input(version_input, filtered)
                if result is not None:
                    return result
                console.print(
                    f"[warning]{i18n.t('cli.self_update.invalid_selection')}[/]"
                )

    def _parse_version_input(self, user_input: str, version_list: list) -> str:
        """
        解析用户输入的版本序号或版本号字符串

        :param user_input: [str] 用户输入内容
        :param version_list: [list] 可用版本信息列表

        :return: [str] 匹配到的版本号，无匹配时返回 None
        """
        text = user_input.strip()
        if not text:
            return None
        if text.isdigit():
            idx = int(text)
            if 1 <= idx <= len(version_list):
                return version_list[idx - 1]["version"]
            return None
        if any(v["version"] == text for v in version_list):
            return text
        return None
