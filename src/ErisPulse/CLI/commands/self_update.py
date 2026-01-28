"""
Self-Update 命令实现

更新 ErisPulse SDK 本身
"""

import sys
import asyncio
from argparse import ArgumentParser
from rich.prompt import Confirm, Prompt
from rich.panel import Panel

from ..utils import PackageManager
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
        console.print(Panel(
            f"[title]ErisPulse SDK 自更新[/]\n"
            f"当前版本: [bold]{current_version}[/]",
            title_align="left"
        ))
        
        # 获取可用版本
        with console.status("[bold green]正在获取版本信息...", spinner="dots"):
            versions = asyncio.run(self.package_manager.get_pypi_versions())
        
        if not versions:
            console.print("[error]无法获取版本信息[/]")
            sys.exit(1)
        
        # 确定目标版本
        target_version = self._select_target_version(versions, args.version, args.pre)
        
        if target_version is None:
            console.print("[info]操作已取消[/]")
            sys.exit(0)
        
        # 确认更新
        if target_version == current_version and not args.force:
            console.print(f"[info]当前已是目标版本 [bold]{current_version}[/][/]")
            sys.exit(0)
        elif not args.force:
            if not Confirm.ask(
                f"确认将ErisPulse SDK从 [bold]{current_version}[/] 更新到 [bold]{target_version}[/] 吗？",
                default=False
            ):
                console.print("[info]操作已取消[/]")
                sys.exit(0)
        
        # 执行更新
        success = self.package_manager.update_self(target_version, args.force)
        if not success:
            sys.exit(1)
    
    def _select_target_version(self, versions, specified_version: str = None, 
                            include_pre: bool = False) -> str:
        """
        选择目标版本
        
        :param versions: 版本列表
        :param specified_version: 用户指定的版本
        :param include_pre: 是否包含预发布版本
        :return: 目标版本号
        """
        if specified_version:
            # 用户已指定版本
            if not any(v['version'] == specified_version for v in versions):
                console.print(f"[warning]版本 {specified_version} 可能不存在[/]")
                if not Confirm.ask("是否继续？", default=False):
                    return None
            return specified_version
        
        # 交互式选择
        stable_versions = [v for v in versions if not v["pre_release"]]
        pre_versions = [v for v in versions if v["pre_release"]]
        
        latest_stable = stable_versions[0] if stable_versions else None
        latest_pre = pre_versions[0] if pre_versions and include_pre else None
        
        choices = []
        choice_versions = {}
        
        if latest_stable:
            choice = f"最新稳定版 ({latest_stable['version']})"
            choices.append(choice)
            choice_versions[choice] = latest_stable['version']
        
        if include_pre and latest_pre:
            choice = f"最新预发布版 ({latest_pre['version']})"
            choices.append(choice)
            choice_versions[choice] = latest_pre['version']
        
        # 添加其他选项
        choices.append("查看所有版本")
        choices.append("手动指定版本")
        choices.append("取消")
        
        # 显示选项
        console.print("\n[info]请选择更新选项:[/]")
        for i, choice in enumerate(choices, 1):
            console.print(f"  {i}. {choice}")
        
        while True:
            try:
                selected_input = Prompt.ask(
                    "请输入选项编号",
                    default="1"
                )
                
                if selected_input.isdigit():
                    selected_index = int(selected_input)
                    if 1 <= selected_index <= len(choices):
                        selected = choices[selected_index - 1]
                        break
                    else:
                        console.print("[warning]请输入有效的选项编号[/]")
                else:
                    if selected_input in choices:
                        selected = selected_input
                        break
                    else:
                        console.print("[warning]请输入有效的选项编号或选项名称[/]")
            except KeyboardInterrupt:
                console.print("\n[info]操作已取消[/]")
                return None
        
        if selected == "取消":
            return None
        elif selected == "手动指定版本":
            target_version = Prompt.ask("请输入要更新到的版本号")
            if not any(v['version'] == target_version for v in versions):
                console.print(f"[warning]版本 {target_version} 可能不存在[/]")
                if not Confirm.ask("是否继续？", default=False):
                    return None
            return target_version
        elif selected == "查看所有版本":
            return self._select_from_version_list(versions, include_pre)
        else:
            return choice_versions[selected]
    
    def _select_from_version_list(self, versions, include_pre: bool = False) -> str:
        """
        从版本列表中选择
        
        :param versions: 版本列表
        :param include_pre: 是否包含预发布版本
        :return: 选中的版本号
        """
        from rich.table import Table
        from rich.box import SIMPLE
        
        table = Table(
            title="可用版本",
            box=SIMPLE,
            header_style="info"
        )
        table.add_column("序号")
        table.add_column("版本")
        table.add_column("类型")
        table.add_column("上传时间")
        
        displayed = 0
        version_list = []
        for version_info in versions:
            if not include_pre and version_info["pre_release"]:
                continue
                
            version_list.append(version_info)
            version_type = "[yellow]预发布[/]" if version_info["pre_release"] else "[green]稳定版[/]"
            table.add_row(
                str(displayed + 1),
                version_info["version"],
                version_type,
                version_info["uploaded"][:10] if version_info["uploaded"] else "未知"
            )
            displayed += 1
            
            if displayed >= 10:
                break
        
        if displayed == 0:
            console.print("[info]没有找到符合条件的版本[/]")
            return None
        
        console.print(table)
        
        # 显示版本选择
        console.print("\n[info]请选择要更新到的版本:[/]")
        while True:
            try:
                version_input = Prompt.ask("请输入版本序号或版本号")
                if version_input.isdigit():
                    version_index = int(version_input)
                    if 1 <= version_index <= len(version_list):
                        return version_list[version_index - 1]['version']
                    else:
                        console.print("[warning]请输入有效的版本序号[/]")
                else:
                    if any(v['version'] == version_input for v in version_list):
                        return version_input
                    else:
                        console.print("[warning]请输入有效的版本序号或版本号[/]")
            except KeyboardInterrupt:
                console.print("\n[info]操作已取消[/]")
                return None
