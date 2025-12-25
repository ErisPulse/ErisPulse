"""
ErisPulse UX优化模块

提供更友好的初始化和API接口，简化常用操作
"""

import json
import asyncio
from typing import List, Dict
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

class UXManager:
    """
    UX优化管理器
    
    提供用户友好的界面和简化操作
    """
    
    def __init__(self):
        self.console = Console()
        self._adapter_cache = None
        self._adapter_cache_time = 0
        self._cache_duration = 300  # 缓存5分钟
    
    async def _fetch_available_adapters(self) -> Dict[str, str]:
        """
        从云端获取可用适配器列表
        
        :return: 适配器名称到描述的映射
        """
        # 检查缓存是否有效
        current_time = asyncio.get_event_loop().time()
        if self._adapter_cache and (current_time - self._adapter_cache_time) < self._cache_duration:
            return self._adapter_cache
        
        try:
            # 使用与 PackageManager 相同的机制获取远程包列表
            from ..utils.package_manager import PackageManager
            package_manager = PackageManager()
            remote_packages = await package_manager.get_remote_packages()
            
            adapters = {}
            for name, info in remote_packages.get("adapters", {}).items():
                adapters[name] = info.get("description", "")
            
            if adapters:
                # 更新缓存
                self._adapter_cache = adapters
                self._adapter_cache_time = current_time
                return adapters
            else:
                self.console.print("[yellow]从远程源获取的适配器列表为空[/yellow]")
        except Exception as e:
            self.console.print(f"[red]从远程源获取适配器列表时出错: {e}[/red]")
        
        # 如果云端请求失败，返回默认适配器列表
        self.console.print("[yellow]使用默认适配器列表[/yellow]")
        return {
            "yunhu": "云湖平台适配器",
            "telegram": "Telegram机器人适配器",
            "onebot11": "OneBot11标准适配器",
            "email": "邮件适配器"
        }
    
    def welcome(self, version: str = None) -> None:
        """
        显示欢迎信息
        
        :param version: 框架版本号
        """
        version_text = f" v{version}" if version else ""
        welcome_text = f"[bold blue]欢迎使用 ErisPulse{version_text}[/bold blue]\n"
        welcome_text += "[dim]异步机器人开发框架，让开发更简单[/dim]"
        
        panel = Panel(
            welcome_text,
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def show_status(self) -> None:
        """
        显示系统状态概览
        """
        table = Table(title="系统状态概览")
        table.add_column("组件", style="cyan", no_wrap=True)
        table.add_column("状态", style="magenta")
        table.add_column("详情", style="green")
        
        # 框架核心状态
        table.add_row("框架核心", "[green]运行中[/green]", "ErisPulse SDK 已加载")
        
        # 模块状态
        try:
            from .. import sdk
            loaded_modules = sdk.module.list_loaded()
            table.add_row(
                "模块系统", 
                "[green]运行中[/green]" if loaded_modules else "[yellow]空闲[/yellow]",
                f"已加载 {len(loaded_modules)} 个模块"
            )
        except Exception:
            table.add_row("模块系统", "[red]错误[/red]", "无法获取模块状态")
        
        # 适配器状态
        try:
            from .. import sdk
            adapter_list = sdk.adapter.list_adapters()
            enabled_count = sum(1 for status in adapter_list.values() if status)
            table.add_row(
                "适配器系统", 
                "[green]运行中[/green]" if adapter_list else "[yellow]空闲[/yellow]",
                f"已注册 {len(adapter_list)} 个适配器，{enabled_count} 个已启用"
            )
        except Exception:
            table.add_row("适配器系统", "[red]错误[/red]", "无法获取适配器状态")
        
        self.console.print(table)
    
    def list_modules(self, detailed: bool = False) -> None:
        """
        列出所有模块状态
        
        :param detailed: 是否显示详细信息
        """
        try:
            from .. import sdk
            modules = sdk.module.list_modules()
            
            if not modules:
                self.console.print("[yellow]没有找到任何模块[/yellow]")
                return
            
            table = Table(title="模块状态")
            table.add_column("模块名", style="cyan", no_wrap=True)
            table.add_column("状态", style="magenta")
            table.add_column("是否已加载", style="green")
            
            for module_name, enabled in modules.items():
                loaded = sdk.module.is_loaded(module_name)
                status = "[green]启用[/green]" if enabled else "[red]禁用[/red]"
                is_loaded = "[green]已加载[/green]" if loaded else "[red]未加载[/red]"
                
                table.add_row(module_name, status, is_loaded)
            
            self.console.print(table)
            
            if detailed:
                loaded_modules = sdk.module.list_loaded()
                if loaded_modules:
                    self.console.print("\n[bold]已加载模块详情:[/bold]")
                    for module_name in loaded_modules:
                        try:
                            module_instance = sdk.module.get(module_name)
                            info = getattr(module_instance, "moduleInfo", {})
                            if info:
                                self.console.print(f"[cyan]{module_name}:[/cyan] {json.dumps(info, indent=2, ensure_ascii=False)}")
                        except Exception as e:
                            self.console.print(f"[cyan]{module_name}:[/cyan] [red]获取信息失败: {e}[/red]")
        
        except Exception as e:
            self.console.print(f"[red]获取模块列表失败: {e}[/red]")
    
    def list_adapters(self, detailed: bool = False) -> None:
        """
        列出所有适配器状态
        
        :param detailed: 是否显示详细信息
        """
        try:
            from .. import sdk
            adapters = sdk.adapter.list_adapters()
            
            if not adapters:
                self.console.print("[yellow]没有找到任何适配器[/yellow]")
                return
            
            table = Table(title="适配器状态")
            table.add_column("适配器名", style="cyan", no_wrap=True)
            table.add_column("状态", style="magenta")
            
            for adapter_name, enabled in adapters.items():
                status = "[green]启用[/green]" if enabled else "[red]禁用[/red]"
                table.add_row(adapter_name, status)
            
            self.console.print(table)
            
            if detailed:
                self.console.print("\n[bold]已注册适配器详情:[/bold]")
                for adapter_name in adapters:
                    try:
                        adapter_instance = sdk.adapter.get(adapter_name)
                        if adapter_instance:
                            info = getattr(adapter_instance, "_adapter_info", {})
                            if info:
                                self.console.print(f"[cyan]{adapter_name}:[/cyan] {json.dumps(info, indent=2, ensure_ascii=False)}")
                    except Exception as e:
                        self.console.print(f"[cyan]{adapter_name}:[/cyan] [red]获取信息失败: {e}[/red]")
        
        except Exception as e:
            self.console.print(f"[red]获取适配器列表失败: {e}[/red]")

    
    def init_project(self, project_name: str, adapter_list: List[str] = None) -> bool:
        """
        初始化新项目
        
        :param project_name: 项目名称
        :param adapter_list: 需要初始化的适配器列表
        :return: 是否初始化成功
        """
        try:
            project_path = Path(project_name)
            if project_path.exists():
                if project_path.is_dir():
                    self.console.print(f"[yellow]目录 {project_name} 已存在[/yellow]")
                else:
                    self.console.print(f"[red]文件 {project_name} 已存在且不是目录[/red]")
                    return False
            else:
                project_path.mkdir()
                self.console.print(f"[green]创建项目目录: {project_name}[/green]")
            
            # 创建基本目录结构
            dirs = ["config", "logs"]
            for dir_name in dirs:
                dir_path = project_path / dir_name
                dir_path.mkdir(exist_ok=True)
                self.console.print(f"[green]创建目录: {dir_name}[/green]")
            
            # 创建配置文件
            config_file = project_path / "config.toml"
            if not config_file.exists():
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write("# ErisPulse 配置文件\n\n")
                    f.write("[ErisPulse]\n")
                    f.write("# 全局配置\n\n")
                    f.write("[ErisPulse.server]\n")
                    f.write('host = "0.0.0.0"\n')
                    f.write("port = 8000\n\n")
                    f.write("[ErisPulse.logger]\n")
                    f.write('level = "INFO"\n')
                    f.write("log_files = [\"logs/app.log\"]\n")
                    f.write("memory_limit = 1000\n\n")
                    
                    # 添加适配器配置
                    if adapter_list:
                        f.write("[ErisPulse.adapters]\n")
                        f.write("# 适配器配置\n\n")
                        f.write("[ErisPulse.adapters.status]\n")
                        for adapter in adapter_list:
                            f.write(f'{adapter} = false  # 默认禁用，需要时启用\n')
                        f.write("\n")
                
                self.console.print("[green]创建配置文件: config.toml[/green]")
            
            # 创建主程序文件
            main_file = project_path / "main.py"
            if not main_file.exists():
                with open(main_file, "w", encoding="utf-8") as f:
                    f.write('"""')
                    f.write(f"\n{project_name} 主程序\n\n")
                    f.write("这是 ErisPulse 自动生成的主程序文件\n")
                    f.write("您可以根据需要修改此文件\n")
                    f.write('"""\n\n')
                    f.write("import asyncio\n")
                    f.write("from ErisPulse import sdk\n\n")
                    f.write("async def main():\n")
                    f.write('    """主程序入口"""\n')
                    f.write("    # 初始化 SDK\n")
                    f.write("    await sdk.init()\n\n")
                    f.write("    # 启动适配器\n")
                    f.write("    await sdk.adapter.startup()\n\n")
                    f.write('    print("ErisPulse 已启动，按 Ctrl+C 退出")\n')
                    f.write("    try:\n")
                    f.write("        while True:\n")
                    f.write("            await asyncio.sleep(1)\n")
                    f.write("    except KeyboardInterrupt:\n")
                    f.write("        print(\"\\n正在关闭...\")\n")
                    f.write("        await sdk.adapter.shutdown()\n\n")
                    f.write("if __name__ == \"__main__\":\n")
                    f.write("    asyncio.run(main())\n")
                
                self.console.print("[green]创建主程序文件: main.py[/green]")
            
            self.console.print("\n[bold green]项目 {} 初始化成功![/bold green]".format(project_name))
            self.console.print("\n[cyan]接下来您可以:[/cyan]")
            self.console.print(f"1. 编辑 {project_name}/config.toml 配置适配器")
            self.console.print(f"2. 运行 [cyan]cd {project_name} \n     ep run[/cyan] 启动项目")
            self.console.print("\n访问 https://github.com/ErisPulse/ErisPulse/tree/main/docs 获取更多信息和文档")
            return True
            
        except Exception as e:
            self.console.print(f"[red]初始化项目失败: {e}[/red]")
            return False

    def interactive_init(self, project_name: str = None, force: bool = False) -> bool:
        """
        交互式初始化项目，包括项目创建和配置设置
        
        :param project_name: 项目名称，可为None
        :param force: 是否强制覆盖现有配置
        :return: 是否初始化成功
        """
        try:
            # 获取项目名称（如果未提供）
            if not project_name:
                project_name = self.console.input("[cyan]请输入项目名称 (默认: my_erispulse_project):[/cyan] ")
                if not project_name:
                    project_name = "my_erispulse_project"
            
            # 检查项目是否已存在
            project_path = Path(project_name)
            if project_path.exists() and not force:
                if not Confirm.ask("[yellow]目录 {} 已存在，是否覆盖？[/yellow]".format(project_name), default=False):
                    self.console.print("[info]操作已取消[/]")
                    return False
            
            # 创建项目
            if not self.init_project(project_name, []):
                return False
            
            # 加载项目配置
            from .. import config as config
            project_config_path = project_path / "config.toml"
            
            # 更新配置文件路径并重新加载配置
            config.CONFIG_FILE = str(project_config_path)
            config.reload()
            
            # 交互式配置向导
            self.console.print("\n[bold blue]现在进行基本配置:[/bold blue]")
            
            # 获取日志级别配置
            current_level = config.getConfig("ErisPulse.logger.level", "INFO")
            self.console.print("\n当前日志级别: [cyan]{}[/cyan]".format(current_level))
            new_level = self.console.input("[yellow]请输入新的日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)，回车保持当前值:[/yellow] ")
            
            if new_level and new_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                    config.setConfig("ErisPulse.logger.level", new_level.upper())
                    self.console.print("[green]日志级别已更新为: {}[/green]".format(new_level.upper()))
            elif new_level:
                self.console.print("[red]无效的日志级别: {}[/red]".format(new_level))
            
            # 获取服务器配置
            self.console.print("\n[bold]服务器配置[/bold]")
            current_host = config.getConfig("ErisPulse.server.host", "0.0.0.0")
            current_port = config.getConfig("ErisPulse.server.port", 8000)
            
            self.console.print("当前主机: [cyan]{}[/cyan]".format(current_host))
            new_host = self.console.input("[yellow]请输入主机地址，回车保持当前值:[/yellow] ")
            
            if new_host:
                config.setConfig("ErisPulse.server.host", new_host)
                self.console.print("[green]主机地址已更新为: {}[/green]".format(new_host))
            
            self.console.print("当前端口: [cyan]{}[/cyan]".format(current_port))
            new_port = self.console.input("[yellow]请输入端口号，回车保持当前值:[/yellow] ")
            
            if new_port:
                try:
                    port_int = int(new_port)
                    config.setConfig("ErisPulse.server.port", port_int)
                    self.console.print("[green]端口已更新为: {}[/green]".format(port_int))
                except ValueError:
                    self.console.print("[red]无效的端口号: {}[/red]".format(new_port))
            
            # 询问是否要配置适配器
            if Confirm.ask("\n[cyan]是否要配置适配器？[/cyan]", default=True):
                # 使用同步版本的适配器配置方法
                self._configure_adapters_interactive_sync(str(project_path))
            
            # 保存配置
            config.force_save()
            self.console.print("\n[bold green]项目和配置初始化完成![/bold green]")
            
            # 显示下一步操作
            self.console.print("\n[cyan]接下来您可以:[/cyan]")
            self.console.print("1. 编辑 {}/config.toml 进一步配置".format(project_name))
            self.console.print("2. 运行 [cyan]cd {} \n        ep run[/cyan] 启动项目".format(project_name))
            
            return True
            
        except Exception as e:
            self.console.print("[red]交互式初始化失败: {}[/red]".format(e))
            return False
    
    def _configure_adapters_interactive_sync(self, project_path: str = None) -> None:
        """
        交互式配置适配器的同步版本，从云端获取适配器列表
        
        :param project_path: 项目路径，用于加载项目特定的配置
        """
        from . import config
        from ..utils.package_manager import PackageManager
        
        # 如果提供了项目路径，则加载项目配置
        if project_path:
            project_config_path = Path(project_path) / "config.toml"
            if project_config_path.exists():
                # 更新配置文件路径并重新加载配置
                config.CONFIG_FILE = str(project_config_path)
                config.reload()
                self.console.print(f"[green]已加载项目配置: {project_config_path}[/green]")
        
        self.console.print("\n[bold]配置适配器[/bold]")
        self.console.print("[info]正在从云端获取可用适配器列表...[/info]")
        
        # 获取可用适配器列表（同步方式）
        try:
            # 使用线程池在同步上下文中运行异步函数
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._fetch_available_adapters())
                adapters = future.result(timeout=10)
        except Exception as e:
            self.console.print(f"[red]获取适配器列表失败: {e}[/red]")
            adapters = {}
        
        if not adapters:
            self.console.print("[red]未能获取到适配器列表[/red]")
            return
        
        # 显示可用适配器列表
        adapter_list = list(adapters.items())
        for i, (name, desc) in enumerate(adapter_list, 1):
            self.console.print(f"  {i}. {name} - {desc}")
        
        # 选择适配器
        selected_indices = self.console.input("\n[cyan]请输入要启用的适配器序号，多个用逗号分隔 (如: 1,3):[/cyan] ")
        if not selected_indices:
            self.console.print("[info]未选择任何适配器[/info]")
            return
        
        try:
            indices = [int(idx.strip()) for idx in selected_indices.split(",")]
            enabled_adapters = []
            
            for idx in indices:
                if 1 <= idx <= len(adapter_list):
                    adapter_name = adapter_list[idx-1][0]
                    enabled_adapters.append(adapter_name)
                    config.setConfig(f"ErisPulse.adapters.status.{adapter_name}", True)
                    self.console.print("[green]已启用适配器: {}[/green]".format(adapter_name))
                else:
                    self.console.print("[red]无效的序号: {}[/red]".format(idx))
            
            # 禁用未选择的适配器
            all_adapter_names = [name for name, _ in adapter_list]
            for name in all_adapter_names:
                if name not in enabled_adapters:
                    config.setConfig(f"ErisPulse.adapters.status.{name}", False)
            
            self.console.print("\n[info]已启用 {} 个适配器[/info]".format(len(enabled_adapters)))
            
            # 询问是否要安装适配器
            if enabled_adapters and Confirm.ask("\n[cyan]是否要安装选中的适配器？[/cyan]", default=True):
                package_manager = PackageManager()
                
                for adapter_name in enabled_adapters:
                    # 从适配器列表中获取包名
                    package_name = None
                    # 尝试通过 PackageManager 获取包名
                    try:
                        # 使用同步方式获取远程包信息
                        remote_packages = package_manager._cache.get("remote_packages", {})
                        if not remote_packages:
                            # 如果没有缓存，尝试同步获取
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, package_manager.get_remote_packages())
                                remote_packages = future.result(timeout=10)
                        
                        if adapter_name in remote_packages.get("adapters", {}):
                            package_name = remote_packages["adapters"][adapter_name].get("package")
                    except Exception:
                        pass
                    
                    # 如果没有找到包名，使用适配器名称作为包名
                    if not package_name:
                        package_name = adapter_name
                    
                    # 安装适配器
                    self.console.print(f"[info]正在安装适配器: {adapter_name} ({package_name})[/info]")
                    success = package_manager.install_package([package_name])
                    
                    if success:
                        self.console.print(f"[green]适配器 {adapter_name} 安装成功[/green]")
                    else:
                        # 如果标准安装失败，尝试使用 uv
                        self.console.print("[yellow]标准安装失败，尝试使用 uv 安装...[/yellow]")
                        try:
                            import subprocess
                            import sys
                            
                            # 尝试使用 uv pip install
                            result = subprocess.run(
                                [sys.executable, "-m", "uv", "pip", "install", package_name],
                                capture_output=True,
                                text=True,
                                timeout=300
                            )
                            
                            if result.returncode == 0:
                                self.console.print(f"[green]适配器 {adapter_name} 通过 uv 安装成功[/green]")
                                success = True
                            else:
                                self.console.print(f"[red]适配器 {adapter_name} 通过 uv 安装失败[/red]")
                                self.console.print(f"[dim]{result.stderr}[/dim]")
                        except Exception as e:
                            self.console.print(f"[red]适配器 {adapter_name} 通过 uv 安装时出错: {e}[/red]")
                            
                        # 如果 uv 也失败了，尝试直接使用 pip
                        if not success:
                            self.console.print("[yellow]尝试使用 pip 直接安装...[/yellow]")
                            try:
                                import subprocess
                                import sys
                                
                                # 尝试直接使用 pip
                                result = subprocess.run(
                                    [sys.executable, "-m", "pip", "install", package_name],
                                    capture_output=True,
                                    text=True,
                                    timeout=300
                                )
                                
                                if result.returncode == 0:
                                    self.console.print(f"[green]适配器 {adapter_name} 通过 pip 直接安装成功[/green]")
                                    success = True
                                else:
                                    self.console.print(f"[red]适配器 {adapter_name} 通过 pip 直接安装失败[/red]")
                                    self.console.print(f"[dim]{result.stderr}[/dim]")
                            except Exception as e:
                                self.console.print(f"[red]适配器 {adapter_name} 通过 pip 直接安装时出错: {e}[/red]")
                        
                        if not success:
                            self.console.print(f"[red]适配器 {adapter_name} 安装失败，请手动安装: pip install {package_name}[/red]")
            
            # 保存配置
            config.force_save()
            
        except ValueError:
            self.console.print("[red]输入格式错误，请输入数字序号[/red]")

    async def _configure_adapters_interactive(self, project_path: str = None) -> None:
        """
        交互式配置适配器，从云端获取适配器列表
        
        :param project_path: 项目路径，用于加载项目特定的配置
        """
        from .. import config
        from ..utils.package_manager import PackageManager
        package_manager = PackageManager()
        
        # 如果提供了项目路径，则加载项目配置
        if project_path:
            project_config_path = Path(project_path) / "config.toml"
            if project_config_path.exists():
                # 更新配置文件路径并重新加载配置
                config.CONFIG_FILE = str(project_config_path)
                config.reload()
                self.console.print(f"[green]已加载项目配置: {project_config_path}[/green]")
        
        self.console.print("\n[bold]配置适配器[/bold]")
        self.console.print("[info]正在从云端获取可用适配器列表...[/info]")
        
        # 从云端获取可用适配器列表
        adapters = await self._fetch_available_adapters()
        
        if not adapters:
            self.console.print("[red]未能获取到适配器列表[/red]")
            return
        
        # 显示可用适配器列表
        adapter_list = list(adapters.items())
        for i, (name, desc) in enumerate(adapter_list, 1):
            self.console.print(f"  {i}. {name} - {desc}")
        
        # 选择适配器
        selected_indices = self.console.input("\n[cyan]请输入要启用的适配器序号，多个用逗号分隔 (如: 1,3):[/cyan] ")
        if not selected_indices:
            self.console.print("[info]未选择任何适配器[/info]")
            return
        
        try:
            indices = [int(idx.strip()) for idx in selected_indices.split(",")]
            enabled_adapters = []
            
            for idx in indices:
                if 1 <= idx <= len(adapter_list):
                    adapter_name = adapter_list[idx-1][0]
                    enabled_adapters.append(adapter_name)
                    config.setConfig(f"ErisPulse.adapters.status.{adapter_name}", True)
                    self.console.print("[green]已启用适配器: {}[/green]".format(adapter_name))
                else:
                    self.console.print("[red]无效的序号: {}[/red]".format(idx))
            
            # 禁用未选择的适配器
            all_adapter_names = [name for name, _ in adapter_list]
            for name in all_adapter_names:
                if name not in enabled_adapters:
                    config.setConfig(f"ErisPulse.adapters.status.{name}", False)
            
            self.console.print("\n[info]已启用 {} 个适配器[/info]".format(len(enabled_adapters)))
            
            # 询问是否要安装适配器
            if enabled_adapters and Confirm.ask("\n[cyan]是否要安装选中的适配器？[/cyan]", default=True):
                # 直接使用CLI中的安装功能
                success = package_manager.install_package(enabled_adapters)
                
                if success:
                    self.console.print("[green]适配器安装成功[/green]")
                else:
                    self.console.print("[red]适配器安装失败，请手动安装或检查网络连接[/red]")
            
            # 保存配置
            config.force_save()
            
        except ValueError:
            self.console.print("[red]输入格式错误，请输入数字序号[/red]")


# 创建全局UX管理器实例
ux = UXManager()

__all__ = [
    "ux",
    "UXManager"
]