import argparse
import importlib.metadata
import sys
import os
import time
import asyncio
from typing import List, Dict, Optional, Any
from watchdog.observers import Observer

# Rich console setup
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.box import SIMPLE

from .console import console

class CLI:
    """
    ErisPulse命令行接口
    
    提供完整的命令行交互功能
    
    {!--< tips >!--}
    1. 支持动态加载第三方命令
    2. 支持模块化子命令系统
    {!--< /tips >!--}
    """
    
    def __init__(self):
        """初始化CLI"""
        from .package_manager import PackageManager
        self.parser = self._create_parser()
        self.package_manager = PackageManager()
        self.observer = None
        self.handler = None
        
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        创建命令行参数解析器
        
        :return: 配置好的ArgumentParser实例
        """
        parser = argparse.ArgumentParser(
            prog="epsdk",
            formatter_class=argparse.RawDescriptionHelpFormatter,
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
        
        # 安装命令
        install_parser = subparsers.add_parser(
            'install',
            help='安装模块/适配器包（支持多个，用空格分隔）'
        )
        install_parser.add_argument(
            'package',
            nargs='+',  # 改为接受多个参数
            help='要安装的包名或模块/适配器简称（可指定多个）'
        )
        install_parser.add_argument(
            '--upgrade', '-U',
            action='store_true',
            help='升级已安装的包'
        )
        install_parser.add_argument(
            '--pre',
            action='store_true',
            help='包含预发布版本'
        )
        
        # 卸载命令
        uninstall_parser = subparsers.add_parser(
            'uninstall',
            help='卸载模块/适配器包（支持多个，用空格分隔）'
        )
        uninstall_parser.add_argument(
            'package',
            nargs='+',  # 改为接受多个参数
            help='要卸载的包名（可指定多个）'
        )
        
        # 模块管理命令
        module_parser = subparsers.add_parser(
            'module',
            help='模块管理'
        )
        module_subparsers = module_parser.add_subparsers(
            dest='module_command',
            metavar="<子命令>"
        )
        
        # 启用模块
        enable_parser = module_subparsers.add_parser(
            'enable',
            help='启用模块'
        )
        enable_parser.add_argument(
            'module',
            help='要启用的模块名'
        )
        
        # 禁用模块
        disable_parser = module_subparsers.add_parser(
            'disable',
            help='禁用模块'
        )
        disable_parser.add_argument(
            'module',
            help='要禁用的模块名'
        )
        
        # 列表命令
        list_parser = subparsers.add_parser(
            'list',
            help='列出已安装的组件'
        )
        list_parser.add_argument(
            '--type', '-t',
            choices=['modules', 'adapters', 'cli', 'all'],
            default='all',
            help='列出类型 (默认: all)'
        )
        list_parser.add_argument(
            '--outdated', '-o',
            action='store_true',
            help='仅显示可升级的包'
        )
        
        # 远程列表命令
        list_remote_parser = subparsers.add_parser(
            'list-remote',
            help='列出远程可用的组件'
        )
        list_remote_parser.add_argument(
            '--type', '-t',
            choices=['modules', 'adapters', 'cli', 'all'],
            default='all',
            help='列出类型 (默认: all)'
        )
        list_remote_parser.add_argument(
            '--refresh', '-r',
            action='store_true',
            help='强制刷新远程包列表'
        )
        
        # 升级命令
        upgrade_parser = subparsers.add_parser(
            'upgrade',
            help='升级组件（支持多个，用空格分隔）'
        )
        upgrade_parser.add_argument(
            'package',
            nargs='*',  # 改为接受可选的多个参数
            help='要升级的包名 (可选，不指定则升级所有)'
        )
        upgrade_parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='跳过确认直接升级'
        )
        upgrade_parser.add_argument(
            '--pre',
            action='store_true',
            help='包含预发布版本'
        )
        
        # 搜索命令
        search_parser = subparsers.add_parser(
            'search',
            help='搜索模块/适配器包'
        )
        search_parser.add_argument(
            'query',
            help='搜索关键词'
        )
        search_parser.add_argument(
            '--installed', '-i',
            action='store_true',
            help='仅搜索已安装的包'
        )
        search_parser.add_argument(
            '--remote', '-r',
            action='store_true',
            help='仅搜索远程包'
        )
        
        # 自更新命令
        self_update_parser = subparsers.add_parser(
            'self-update',
            help='更新ErisPulse SDK本身'
        )
        self_update_parser.add_argument(
            'version',
            nargs='?',
            help='要更新到的版本号 (可选，默认为最新版本)'
        )
        self_update_parser.add_argument(
            '--pre',
            action='store_true',
            help='包含预发布版本'
        )
        self_update_parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='强制更新，即使版本相同'
        )
        
        # 运行命令
        run_parser = subparsers.add_parser(
            'run',
            help='运行主程序'
        )
        run_parser.add_argument(
            'script',
            nargs='?',
            help='要运行的主程序路径 (默认: main.py)'
        )
        run_parser.add_argument(
            '--reload',
            action='store_true',
            help='启用热重载模式'
        )
        run_parser.add_argument(
            '--no-reload',
            action='store_true',
            help='禁用热重载模式'
        )
        
        # 初始化命令
        init_parser = subparsers.add_parser(
            'init',
            help='交互式初始化ErisPulse项目'
        )
        init_parser.add_argument(
            '--project-name', '-n',
            help='项目名称 (可选，交互式初始化时将会询问)'
        )
        init_parser.add_argument(
            '--quick', '-q',
            action='store_true',
            help='快速模式，跳过交互式配置'
        )
        init_parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='强制覆盖现有配置'
        )
        
        # 状态命令
        status_parser = subparsers.add_parser(
            'status',
            help='显示ErisPulse系统状态'
        )
        status_parser.add_argument(
            '--type', '-t',
            choices=['modules', 'adapters', 'all'],
            default='all',
            help='显示类型 (默认: all)'
        )
        

        
        # 加载第三方命令
        self._load_external_commands(subparsers)
        
        return parser
    
    def _get_external_commands(self) -> List[str]:
        """
        获取所有已注册的第三方命令名称
        
        :return: 第三方命令名称列表
        """
        try:
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                cli_entries = entry_points.select(group='erispulse.cli')
            else:
                cli_entries = entry_points.get('erispulse.cli', [])
            return [entry.name for entry in cli_entries]
        except Exception:
            return []

    def _load_external_commands(self, subparsers):
        """
        加载第三方CLI命令
        
        :param subparsers: 子命令解析器
        
        :raises ImportError: 加载命令失败时抛出
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
                        cli_func(subparsers, console)
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
    
    def _print_installed_packages(self, pkg_type: str, outdated_only: bool = False):
        """
        打印已安装包信息
        
        :param pkg_type: 包类型 (modules/adapters/cli/all)
        :param outdated_only: 是否只显示可升级的包
        """
        installed = self.package_manager.get_installed_packages()
        
        if pkg_type == "modules" and installed["modules"]:
            table = Table(
                title="已安装模块",
                box=SIMPLE,
                header_style="module"
            )
            table.add_column("模块名", style="module")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("状态")
            table.add_column("描述")
            
            for name, info in installed["modules"].items():
                if outdated_only and not self._is_package_outdated(info["package"], info["version"]):
                    continue
                    
                status = "[green]已启用[/]" if info.get("enabled", True) else "[yellow]已禁用[/]"
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    status,
                    info["summary"]
                )
            
            console.print(table)
            
        if pkg_type == "adapters" and installed["adapters"]:
            table = Table(
                title="已安装适配器",
                box=SIMPLE,
                header_style="adapter"
            )
            table.add_column("适配器名", style="adapter")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("描述")
            
            for name, info in installed["adapters"].items():
                if outdated_only and not self._is_package_outdated(info["package"], info["version"]):
                    continue
                    
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["summary"]
                )
            
            console.print(table)
            
        if pkg_type == "cli" and installed["cli_extensions"]:
            table = Table(
                title="已安装CLI扩展",
                box=SIMPLE,
                header_style="cli"
            )
            table.add_column("命令名", style="cli")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("描述")
            
            for name, info in installed["cli_extensions"].items():
                if outdated_only and not self._is_package_outdated(info["package"], info["version"]):
                    continue
                    
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["summary"]
                )
            
            console.print(table)
    
    def _print_remote_packages(self, pkg_type: str):
        """
        打印远程包信息
        
        :param pkg_type: 包类型 (modules/adapters/cli/all)
        """
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        
        if pkg_type == "modules" and remote_packages["modules"]:
            table = Table(
                title="远程模块",
                box=SIMPLE,
                header_style="module"
            )
            table.add_column("模块名", style="module")
            table.add_column("包名")
            table.add_column("最新版本")
            table.add_column("描述")
            
            for name, info in remote_packages["modules"].items():
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["description"]
                )
            
            console.print(table)
            
        if pkg_type == "adapters" and remote_packages["adapters"]:
            table = Table(
                title="远程适配器",
                box=SIMPLE,
                header_style="adapter"
            )
            table.add_column("适配器名", style="adapter")
            table.add_column("包名")
            table.add_column("最新版本")
            table.add_column("描述")
            
            for name, info in remote_packages["adapters"].items():
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["description"]
                )
            
            console.print(table)
            
        if pkg_type == "cli" and remote_packages.get("cli_extensions"):
            table = Table(
                title="远程CLI扩展",
                box=SIMPLE,
                header_style="cli"
            )
            table.add_column("命令名", style="cli")
            table.add_column("包名")
            table.add_column("最新版本")
            table.add_column("描述")
            
            for name, info in remote_packages["cli_extensions"].items():
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["description"]
                )
            
            console.print(table)
    
    def _is_package_outdated(self, package_name: str, current_version: str) -> bool:
        """
        检查包是否过时
        
        :param package_name: 包名
        :param current_version: 当前版本
        :return: 是否有新版本可用
        """
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        
        # 检查模块
        for module_info in remote_packages["modules"].values():
            if module_info["package"] == package_name:
                return module_info["version"] != current_version
                
        # 检查适配器
        for adapter_info in remote_packages["adapters"].values():
            if adapter_info["package"] == package_name:
                return adapter_info["version"] != current_version
                
        # 检查CLI扩展
        for cli_info in remote_packages.get("cli_extensions", {}).values():
            if cli_info["package"] == package_name:
                return cli_info["version"] != current_version
                
        return False
    
    def _resolve_package_name(self, short_name: str) -> Optional[str]:
        """
        解析简称到完整包名（大小写不敏感）
        
        :param short_name: 模块/适配器简称
        :return: 完整包名，未找到返回None
        """
        normalized_name = self.package_manager._normalize_name(short_name)
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        
        # 检查模块
        for name, info in remote_packages["modules"].items():
            if self.package_manager._normalize_name(name) == normalized_name:
                return info["package"]
                
        # 检查适配器
        for name, info in remote_packages["adapters"].items():
            if self.package_manager._normalize_name(name) == normalized_name:
                return info["package"]
                
        return None
    
    def _print_search_results(self, query: str, results: Dict[str, List[Dict[str, str]]]):
        """
        打印搜索结果
        
        :param query: 搜索关键词
        :param results: 搜索结果
        """
        if not results["installed"] and not results["remote"]:
            console.print(f"[info]未找到与 '[bold]{query}[/]' 匹配的包[/]")
            return

        # 打印已安装的包
        if results["installed"]:
            table = Table(
                title="已安装的包",
                box=SIMPLE,
                header_style="info"
            )
            table.add_column("类型")
            table.add_column("名称")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("描述")
            
            for item in results["installed"]:
                table.add_row(
                    item["type"],
                    item["name"],
                    item["package"],
                    item["version"],
                    item["summary"]
                )
            
            console.print(table)
        
        # 打印远程包
        if results["remote"]:
            table = Table(
                title="远程包",
                box=SIMPLE,
                header_style="info"
            )
            table.add_column("类型")
            table.add_column("名称")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("描述")
            
            for item in results["remote"]:
                table.add_row(
                    item["type"],
                    item["name"],
                    item["package"],
                    item["version"],
                    item["summary"]
                )
            
            console.print(table)
    
    def _print_version_list(self, versions: List[Dict[str, Any]], include_pre: bool = False):
        """
        打印版本列表
        
        :param versions: 版本信息列表
        :param include_pre: 是否包含预发布版本
        """
        if not versions:
            console.print("[info]未找到可用版本[/]")
            return
        
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
            # 如果不包含预发布版本，则跳过预发布版本
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
            
            # 只显示前10个版本
            if displayed >= 10:
                break
        
        if displayed == 0:
            console.print("[info]没有找到符合条件的版本[/]")
        else:
            console.print(table)
        return version_list
    
    def _setup_watchdog(self, script_path: str, reload_mode: bool):
        """
        设置文件监控
        
        :param script_path: 要监控的脚本路径
        :param reload_mode: 是否启用重载模式
        """
        from .reload_handler import ReloadHandler

        watch_dirs = [
            os.path.dirname(os.path.abspath(script_path)),
        ]
        
        # 添加配置目录
        config_dir = os.path.abspath(os.getcwd())
        if config_dir not in watch_dirs:
            watch_dirs.append(config_dir)
            
        self.handler = ReloadHandler(script_path, reload_mode)
        self.observer = Observer()
        
        for d in watch_dirs:
            if os.path.exists(d):
                self.observer.schedule(
                    self.handler, 
                    d, 
                    recursive=reload_mode
                )
                console.print(f"[dim]监控目录: [path]{d}[/][/]")
        
        self.observer.start()
        
        mode_desc = "[bold]开发重载模式[/]" if reload_mode else "[bold]配置监控模式[/]"
        console.print(Panel(
            f"{mode_desc}\n监控目录: [path]{', '.join(watch_dirs)}[/]",
            title="热重载已启动",
            border_style="info"
        ))
    
    def _cleanup(self):
        """清理资源"""
        if self.observer:
            self.observer.stop()
            if self.handler and self.handler.process:
                self.handler._terminate_process()
            self.observer.join()
    
    def run(self):
        """
        运行CLI
        
        :raises KeyboardInterrupt: 用户中断时抛出
        :raises Exception: 命令执行失败时抛出
        """
        args = self.parser.parse_args()
        
        if args.version:
            self._print_version()
            return
            
        if not args.command:
            self.parser.print_help()
            return
            
        try:
            if args.command == "install":
                success = self.package_manager.install_package(
                    args.package,
                    upgrade=args.upgrade,
                    pre=args.pre
                )
                if not success:
                    sys.exit(1)
                    
            elif args.command == "uninstall":
                success = self.package_manager.uninstall_package(args.package)
                if not success:
                    sys.exit(1)
                    
            elif args.command == "module":
                from ErisPulse.Core import module as module_manager
                installed = self.package_manager.get_installed_packages()
                
                if args.module_command == "enable":
                    if args.module not in installed["modules"]:
                        console.print(f"[error]模块 [bold]{args.module}[/] 不存在或未安装[/]")
                    else:
                        module_manager.enable(args.module)
                        console.print(f"[success]模块 [bold]{args.module}[/] 已启用[/]")
                        
                elif args.module_command == "disable":
                    if args.module not in installed["modules"]:
                        console.print(f"[error]模块 [bold]{args.module}[/] 不存在或未安装[/]")
                    else:
                        module_manager.disable(args.module)
                        console.print(f"[warning]模块 [bold]{args.module}[/] 已禁用[/]")
                else:
                    self.parser.parse_args(["module", "--help"])
                    
            elif args.command == "list":
                pkg_type = args.type
                if pkg_type == "all":
                    self._print_installed_packages("modules", args.outdated)
                    self._print_installed_packages("adapters", args.outdated)
                    self._print_installed_packages("cli", args.outdated)
                else:
                    self._print_installed_packages(pkg_type, args.outdated)
                    
            elif args.command == "list-remote":
                pkg_type = args.type
                if pkg_type == "all":
                    self._print_remote_packages("modules")
                    self._print_remote_packages("adapters")
                    self._print_remote_packages("cli")
                else:
                    self._print_remote_packages(pkg_type)
                    
            elif args.command == "upgrade":
                if args.package:
                    success = self.package_manager.upgrade_package(
                        args.package,
                        pre=args.pre
                    )
                    if not success:
                        sys.exit(1)
                else:
                    if args.force or Confirm.ask("确定要升级所有ErisPulse组件吗？", default=False):
                        success = self.package_manager.upgrade_all()
                        if not success:
                            sys.exit(1)
                            
            elif args.command == "search":
                results = self.package_manager.search_package(args.query)
                
                # 根据选项过滤结果
                if args.installed:
                    results["remote"] = []
                elif args.remote:
                    results["installed"] = []
                    
                self._print_search_results(args.query, results)
                    
            elif args.command == "self-update":
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
                
                # 交互式选择更新选项
                if not args.version:
                    # 显示最新版本
                    stable_versions = [v for v in versions if not v["pre_release"]]
                    pre_versions = [v for v in versions if v["pre_release"]]
                    
                    latest_stable = stable_versions[0] if stable_versions else None
                    latest_pre = pre_versions[0] if pre_versions and args.pre else None
                    
                    choices = []
                    choice_versions = {}
                    choice_index = {}
                    
                    if latest_stable:
                        choice = f"最新稳定版 ({latest_stable['version']})"
                        choices.append(choice)
                        choice_versions[choice] = latest_stable['version']
                        choice_index[len(choices)] = choice
                        
                    if args.pre and latest_pre:
                        choice = f"最新预发布版 ({latest_pre['version']})"
                        choices.append(choice)
                        choice_versions[choice] = latest_pre['version']
                        choice_index[len(choices)] = choice
                        
                    # 添加其他选项
                    choices.append("查看所有版本")
                    choices.append("手动指定版本")
                    choices.append("取消")
                    
                    # 创建数字索引映射
                    for i, choice in enumerate(choices, 1):
                        choice_index[i] = choice
                    
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
                                if selected_index in choice_index:
                                    selected = choice_index[selected_index]
                                    break
                                else:
                                    console.print("[warning]请输入有效的选项编号[/]")
                            else:
                                # 检查是否是选项文本
                                if selected_input in choices:
                                    selected = selected_input
                                    break
                                else:
                                    console.print("[warning]请输入有效的选项编号或选项名称[/]")
                        except KeyboardInterrupt:
                            console.print("\n[info]操作已取消[/]")
                            sys.exit(0)
                    
                    if selected == "取消":
                        console.print("[info]操作已取消[/]")
                        sys.exit(0)
                    elif selected == "手动指定版本":
                        target_version = Prompt.ask("请输入要更新到的版本号")
                        if not any(v['version'] == target_version for v in versions):
                            console.print(f"[warning]版本 {target_version} 可能不存在[/]")
                            if not Confirm.ask("是否继续？", default=False):
                                sys.exit(0)
                    elif selected == "查看所有版本":
                        version_list = self._print_version_list(versions, include_pre=args.pre)
                        if not version_list:
                            console.print("[info]没有可用版本[/]")
                            sys.exit(0)
                            
                        # 显示版本选择
                        console.print("\n[info]请选择要更新到的版本:[/]")
                        while True:
                            try:
                                version_input = Prompt.ask("请输入版本序号或版本号")
                                if version_input.isdigit():
                                    version_index = int(version_input)
                                    if 1 <= version_index <= len(version_list):
                                        target_version = version_list[version_index - 1]['version']
                                        break
                                    else:
                                        console.print("[warning]请输入有效的版本序号[/]")
                                else:
                                    # 检查是否是有效的版本号
                                    if any(v['version'] == version_input for v in version_list):
                                        target_version = version_input
                                        break
                                    else:
                                        console.print("[warning]请输入有效的版本序号或版本号[/]")
                            except KeyboardInterrupt:
                                console.print("\n[info]操作已取消[/]")
                                sys.exit(0)
                    else:
                        target_version = choice_versions[selected]
                else:
                    target_version = args.version
                
                # 确认更新
                if target_version == current_version and not args.force:
                    console.print(f"[info]当前已是目标版本 [bold]{current_version}[/][/]")
                    sys.exit(0)
                elif not args.force:
                    if not Confirm.ask(f"确认将ErisPulse SDK从 [bold]{current_version}[/] 更新到 [bold]{target_version}[/] 吗？", default=False):
                        console.print("[info]操作已取消[/]")
                        sys.exit(0)
                
                # 执行更新
                success = self.package_manager.update_self(target_version, args.force)
                if not success:
                    sys.exit(1)
                    
            elif args.command == "run":
                script = args.script or "main.py"
                if not os.path.exists(script):
                    console.print(f"[error]找不到指定文件: [path]{script}[/][/]")
                    return
                    
                reload_mode = args.reload and not args.no_reload
                self._setup_watchdog(script, reload_mode)
                
                try:
                    while True:
                        time.sleep(0.5)
                except KeyboardInterrupt:
                    console.print("\n[info]正在安全关闭...[/]")
                    _cleanup_adapters()
                    _cleanup_modules()
                    self._cleanup()
                    console.print("[success]已安全退出[/]")
                    
            elif args.command == "init":
                from ErisPulse import ux
                
                # 显示欢迎信息
                try:
                    import importlib.metadata
                    version = importlib.metadata.version('ErisPulse')
                    ux.welcome(version)
                except Exception:
                    ux.welcome()
                
                # 使用交互式或快速模式初始化项目
                if args.quick and args.project_name:
                    # 快速模式：只创建项目，不进行交互配置
                    success = ux.init_project(args.project_name, [])
                else:
                    # 交互式模式：引导用户完成项目和配置设置
                    success = ux.interactive_init(args.project_name, args.force)
                
                if success:
                    console.print("[success]项目初始化完成[/]")
                else:
                    console.print("[error]项目初始化失败[/]")
                    sys.exit(1)
                    
            elif args.command == "status":
                from ErisPulse import ux
                
                # 显示状态概览
                ux.show_status()
                
                # 根据类型显示详细信息
                if args.type == "modules" or args.type == "all":
                    ux.list_modules(detailed=True)
                    
                if args.type == "adapters" or args.type == "all":
                    ux.list_adapters(detailed=True)
                    

                
            # 处理第三方命令
            elif args.command in self._get_external_commands():
                # 获取第三方命令的处理函数并执行
                entry_points = importlib.metadata.entry_points()
                if hasattr(entry_points, 'select'):
                    cli_entries = entry_points.select(group='erispulse.cli')
                else:
                    cli_entries = entry_points.get('erispulse.cli', [])
                
                for entry in cli_entries:
                    if entry.name == args.command:
                        cli_func = entry.load()
                        if callable(cli_func):
                            # 创建一个新的解析器来解析第三方命令的参数
                            subparser = self.parser._subparsers._group_actions[0].choices[args.command]
                            parsed_args = subparser.parse_args(sys.argv[2:])
                            # 调用第三方命令处理函数
                            parsed_args.func(parsed_args)
                        break
                
        except KeyboardInterrupt:
            console.print("\n[warning]操作被用户中断[/]")
            self._cleanup()
        except Exception as e:
            console.print(f"[error]执行命令时出错: {e}[/]")
            if args.verbose >= 1:
                import traceback
                console.print(traceback.format_exc())
            self._cleanup()
            sys.exit(1)

def _cleanup_adapters():
    """
    清理适配器资源
    """
    
    from ErisPulse import adapter
    try:
        import asyncio
        import threading
        
        # 检查是否有正在运行的适配器
        if adapter.list_adapters():
            
            console.print("[info]正在停止所有适配器...[/]") 
            
            if threading.current_thread() is threading.main_thread():
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        # 在新线程中运行
                        stop_thread = threading.Thread(
                            target=lambda: asyncio.run(adapter.shutdown())
                        )
                        stop_thread.start()
                        stop_thread.join(timeout=5)
                    else:
                        asyncio.run(adapter.shutdown())
                except RuntimeError:
                    asyncio.run(adapter.shutdown())
            else:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(adapter.shutdown())
                
            console.print("[success]适配器已全部停止[/]")
        else:
            console.print("[dim]没有需要停止的适配器[/]")
    except Exception as e:
        console.print(f"[error]清理适配器资源时出错: {e}[/]")

def _cleanup_modules():
    """
    清理模块资源
    """
    from ErisPulse import module
    try:
        import asyncio
        import threading
    
        console.print("[info]正在卸载所有模块...[/]")
        
        if threading.current_thread() is threading.main_thread():
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    stop_thread = threading.Thread(
                        target=lambda: asyncio.run(module.unload())
                    )
                    stop_thread.start()
                    stop_thread.join(timeout=5)
                else:
                    asyncio.run(module.unload())
            except RuntimeError:
                asyncio.run(module.unload())
        else:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(module.unload())
            
        console.print("[success]模块已全部卸载[/]")
    except Exception as e:
        console.print(f"[error]清理模块资源时出错: {e}[/]")
