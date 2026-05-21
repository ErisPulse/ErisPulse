"""
Self-Update 命令实现

更新 ErisPulse SDK 本身
"""

import sys
import asyncio
from argparse import ArgumentParser

from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.box import SIMPLE
from rich.text import Text

from ..utils import PackageManager
from ..utils.display import section_header, _input
from ..console import console
from ..base import Command


class SelfUpdateCommand(Command):
    name = "self-update"
    description = "更新 ErisPulse SDK 本身"
    
    def __init__(self):
        self.package_manager = PackageManager()
    
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            'version',
            nargs='?',
            help='要更新到的版本号 (可选，默认为最新版本)'
        )
        parser.add_argument(
            '--pre',
            action='store_true',
            help='包含预发布版本'
        )
        parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='强制更新，即使版本相同'
        )
    
    def execute(self, args):
        current_version = self.package_manager.get_installed_version()
        console.print(f"  当前版本: [bold]{current_version}[/]")
        
        with console.status("[bold green]正在获取版本信息...", spinner="dots"):
            versions = asyncio.run(self.package_manager.get_pypi_versions())
        
        if not versions:
            console.print("[error]  无法获取版本信息[/]")
            sys.exit(1)
        
        target_version = self._select_target_version(versions, args.version, args.pre)
        
        if target_version is None:
            console.print("[info]  操作已取消[/]")
            sys.exit(0)
        
        if target_version == current_version and not args.force:
            console.print(f"[info]  当前已是目标版本 [bold]{current_version}[/][/]")
            sys.exit(0)
        elif not args.force:
            if not Confirm.ask(
                f"  确认将 SDK 从 [bold]{current_version}[/] 更新到 [bold]{target_version}[/] 吗？",
                default=False
            ):
                console.print("[info]  操作已取消[/]")
                sys.exit(0)
        
        success = self.package_manager.update_self(target_version, args.force)
        if not success:
            sys.exit(1)
    
    def _select_target_version(self, versions, specified_version: str = None, 
                            include_pre: bool = False) -> str:
        if specified_version:
            if not any(v['version'] == specified_version for v in versions):
                console.print(f"[warning]  版本 {specified_version} 可能不存在[/]")
                if not Confirm.ask("  是否继续？", default=False):
                    return None
            return specified_version
        
        stable_versions = [v for v in versions if not v["pre_release"]]
        pre_versions = [v for v in versions if v["pre_release"]]
        
        latest_stable = stable_versions[0] if stable_versions else None
        latest_pre = pre_versions[0] if pre_versions and include_pre else None
        
        section_header("更新选项")
        
        options = []
        if latest_stable:
            console.print(Text(f"    1.  最新稳定版 ({latest_stable['version']})", style="success"))
            options.append(latest_stable['version'])
        if include_pre and latest_pre:
            idx = len(options) + 1
            console.print(Text(f"    {idx}.  最新预发布版 ({latest_pre['version']})", style="warning"))
            options.append(latest_pre['version'])
        
        next_idx = len(options) + 1
        console.print(Text(f"    {next_idx}.  查看所有版本", style="info"))
        options.append("all")
        
        next_idx2 = len(options) + 1
        console.print(Text(f"    {next_idx2}.  手动指定版本", style="info"))
        options.append("manual")
        
        cancel_idx = len(options) + 1
        console.print(Text(f"    {cancel_idx}.  取消", style="dim"))
        options.append("cancel")
        
        while True:
            try:
                selected_input = Prompt.ask("\n  请输入选项编号", default="1")
                if selected_input.isdigit():
                    idx = int(selected_input)
                    if 1 <= idx <= len(options):
                        selected = options[idx - 1]
                        break
                    else:
                        console.print("[warning]  请输入有效的选项编号[/]")
                else:
                    console.print("[warning]  请输入数字编号[/]")
            except KeyboardInterrupt:
                console.print("\n[info]  操作已取消[/]")
                return None
        
        if selected == "cancel":
            return None
        elif selected == "manual":
            target_version = Prompt.ask("  请输入要更新到的版本号")
            if not any(v['version'] == target_version for v in versions):
                console.print(f"[warning]  版本 {target_version} 可能不存在[/]")
                if not Confirm.ask("  是否继续？", default=False):
                    return None
            return target_version
        elif selected == "all":
            return self._select_from_version_list(versions, include_pre)
        else:
            return selected
    
    def _select_from_version_list(self, versions, include_pre: bool = False) -> str:
        from ..utils.display import _page_size
        
        filtered = [v for v in versions if include_pre or not v["pre_release"]]
        
        if not filtered:
            console.print("[info]  没有找到符合条件的版本[/]")
            return None

        ps = _page_size()
        total = len(filtered)
        page_start = 0

        while True:
            table = Table(box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False)
            table.add_column("序号", width=4, style="#A0B0C0")
            table.add_column("版本", min_width=14)
            table.add_column("类型", width=8)
            table.add_column("上传时间", width=12)

            batch = filtered[page_start:page_start + ps]
            for i, v in enumerate(batch):
                vtype = "[warning]预发布[/]" if v["pre_release"] else "[success]稳定版[/]"
                table.add_row(
                    str(page_start + i + 1),
                    v["version"],
                    vtype,
                    v["uploaded"][:10] if v["uploaded"] else "未知",
                )
            console.print(table)
            console.print(f"[dim]  共 {total} 个版本[/]")

            has_prev = page_start > 0
            has_next = page_start + ps < total
            nav = []
            if has_prev:
                nav.append("p 上一页")
            if has_next:
                nav.append("n 下一页")
            nav_text = ", ".join(nav) + ", " if nav else ""
            version_input = _input(f"{nav_text}版本序号, q 返回 >")

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
                console.print("[warning]  无效的版本序号或版本号[/]")
    
    def _parse_version_input(self, user_input: str, version_list: list) -> str:
        text = user_input.strip()
        if not text:
            return None
        if text.isdigit():
            idx = int(text)
            if 1 <= idx <= len(version_list):
                return version_list[idx - 1]['version']
            return None
        if any(v['version'] == text for v in version_list):
            return text
        return None
