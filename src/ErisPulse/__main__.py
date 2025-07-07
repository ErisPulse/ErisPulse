"""
# CLI 入口 (PyPI包管理版本)

提供命令行界面(CLI)用于PyPI包管理、源管理和开发调试。

## 主要功能
- PyPI包管理: 查找/安装/卸载/更新模块和适配器
- 开发调试: 热重载
- 彩色终端输出

## 主要命令
### 包管理:
    search: 搜索PyPI上的ErisPulse模块
    install: 安装模块/适配器包
    uninstall: 卸载模块/适配器包
    list: 列出已安装的模块/适配器
    upgrade: 升级所有模块/适配器

### 开发调试:
    run: 运行脚本
    --reload: 启用热重载

### 兼容性子命令(旧方式):
    legacy: 旧版模块管理命令

### 示例用法:
```
# 搜索模块
epsdk search MyModule

# 安装模块
epsdk install ErisPulse-MyModule

# 启用热重载
epsdk run main.py --reload
```
"""

import argparse
import importlib.metadata
import subprocess
import sys
import os
import time
import json
from typing import List, Dict, Tuple, Optional
from importlib.metadata import version, PackageNotFoundError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .Core.shellprint import shellprint, Shell_Printer

class PyPIManager:
    """管理PyPI上的ErisPulse模块和适配器"""
    
    @staticmethod
    def search_packages(query: str) -> List[Dict[str, str]]:
        """搜索PyPI上的ErisPulse相关包"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "search", query],
                capture_output=True,
                text=True
            )
            
            packages = []
            for line in result.stdout.split('\n'):
                if "ErisPulse-" in line:
                    parts = line.split(' ', 1)
                    if len(parts) >= 1:
                        name = parts[0].strip()
                        desc = parts[1].strip() if len(parts) > 1 else ""
                        packages.append({"name": name, "description": desc})
            return packages
        except Exception as e:
            shellprint.panel(f"搜索PyPI包失败: {e}", "错误", "error")
            return []
    
    @staticmethod
    def get_installed_packages() -> Dict[str, Dict[str, str]]:
        """获取已安装的ErisPulse模块和适配器"""
        packages = {
            "modules": {},
            "adapters": {}
        }
        
        try:
            # 查找模块
            for dist in importlib.metadata.distributions():
                if "ErisPulse-" in dist.metadata["Name"]:
                    entry_points = dist.entry_points
                    for ep in entry_points:
                        if ep.group == "erispulse.module":
                            packages["modules"][ep.name] = {
                                "package": dist.metadata["Name"],
                                "version": dist.version,
                                "summary": dist.metadata["Summary"]
                            }
                        elif ep.group == "erispulse.adapter":
                            packages["adapters"][ep.name] = {
                                "package": dist.metadata["Name"],
                                "version": dist.version,
                                "summary": dist.metadata["Summary"]
                            }
        except Exception as e:
            shellprint.panel(f"获取已安装包信息失败: {e}", "错误", "error")
        
        return packages
    
    @staticmethod
    def install_package(package_name: str, upgrade: bool = False) -> bool:
        """安装或升级PyPI包"""
        try:
            cmd = [sys.executable, "-m", "pip", "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.append(package_name)
            
            shellprint.status(f"正在安装 {package_name}...")
            result = subprocess.run(cmd, check=True)
            if result.returncode == 0:
                shellprint.panel(f"包 {package_name} 安装成功", "成功", "success")
                return True
            return False
        except subprocess.CalledProcessError as e:
            shellprint.panel(f"安装包 {package_name} 失败: {e}", "错误", "error")
            return False
    
    @staticmethod
    def uninstall_package(package_name: str) -> bool:
        """卸载PyPI包"""
        try:
            shellprint.status(f"正在卸载 {package_name}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
                check=True
            )
            if result.returncode == 0:
                shellprint.panel(f"包 {package_name} 卸载成功", "成功", "success")
                return True
            return False
        except subprocess.CalledProcessError as e:
            shellprint.panel(f"卸载包 {package_name} 失败: {e}", "错误", "error")
            return False
    
    @staticmethod
    def upgrade_all() -> bool:
        """升级所有ErisPulse相关包"""
        try:
            installed = PyPIManager.get_installed_packages()
            all_packages = set()
            
            for pkg_type in ["modules", "adapters"]:
                for pkg_info in installed[pkg_type].values():
                    all_packages.add(pkg_info["package"])
            
            if not all_packages:
                shellprint.panel("没有找到可升级的ErisPulse包", "提示", "info")
                return False
                
            shellprint.panel(
                f"找到 {len(all_packages)} 个可升级的包:\n" + 
                "\n".join(f"  - {pkg}" for pkg in all_packages),
                "升级列表",
                "info"
            )
            
            if not shellprint.confirm("确认升级所有包吗？", default=False):
                return False
                
            for pkg in all_packages:
                PyPIManager.install_package(pkg, upgrade=True)
                
            return True
        except Exception as e:
            shellprint.panel(f"升级包失败: {e}", "错误", "error")
            return False

class ReloadHandler(FileSystemEventHandler):
    """热重载处理器"""
    def __init__(self, script_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.script_path = script_path
        self.process = None
        self.last_reload = time.time()
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            
        shellprint.status(f"启动进程: {self.script_path}")
        self.process = subprocess.Popen([sys.executable, self.script_path])
        self.last_reload = time.time()

    def on_modified(self, event):
        now = time.time()
        if now - self.last_reload < 1.0:
            return
            
        if event.src_path.endswith(".py"):
            print(f"\n{Shell_Printer.CYAN}[热重载] 检测到文件变动: {event.src_path}{Shell_Printer.RESET}")
            self.start_process()

def start_reloader(script_path):
    """启动热重载监视器"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    watch_dirs = [
        os.path.dirname(os.path.abspath(script_path)),
        os.path.join(project_root, "modules")
    ]

    handler = ReloadHandler(script_path)
    observer = Observer()

    for d in watch_dirs:
        if os.path.exists(d):
            observer.schedule(handler, d, recursive=True)

    observer.start()
    print(f"\n{Shell_Printer.GREEN}{Shell_Printer.BOLD}[热重载] 已启动{Shell_Printer.RESET}")
    print(f"{Shell_Printer.DIM}监控目录: {', '.join(watch_dirs)}{Shell_Printer.RESET}\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if handler.process:
            handler.process.terminate()
    observer.join()

def run_script(script_path: str, reload: bool = False):
    """运行指定脚本"""
    if not os.path.exists(script_path):
        shellprint.panel(f"找不到指定文件: {script_path}", "错误", "error")
        return

    if reload:
        start_reloader(script_path)
    else:
        shellprint.panel(f"运行脚本: {Shell_Printer.BOLD}{script_path}{Shell_Printer.RESET}", "执行", "info")
        import runpy
        try:
            runpy.run_path(script_path, run_name="__main__")
        except KeyboardInterrupt:
            shellprint.panel("脚本执行已中断", "中断", "info")

def legacy_command(args):
    """旧版模块管理命令"""
    from ErisPulse.CLI.legacy import LegacyManager
    legacy = LegacyManager()
    legacy.handle(args)

def get_erispulse_version():
    try:
        return version("ErisPulse")
    except PackageNotFoundError:
        return "unknown version"

def main():
    parser = argparse.ArgumentParser(
        prog="epsdk",
        formatter_class=argparse.RawTextHelpFormatter,
        description=f"{Shell_Printer.BOLD}ErisPulse SDK 命令行工具 {get_erispulse_version()}{Shell_Printer.RESET}"
    )
    parser._positionals.title = f"{Shell_Printer.BOLD}{Shell_Printer.CYAN}基本命令{Shell_Printer.RESET}"
    parser._optionals.title = f"{Shell_Printer.BOLD}{Shell_Printer.MAGENTA}可选参数{Shell_Printer.RESET}"
    
    parser.add_argument("--version", action="store_true", help="显示版本信息并退出")
    
    subparsers = parser.add_subparsers(
        dest='command', 
        title='可用的命令',
        metavar=f"{Shell_Printer.GREEN}<命令>{Shell_Printer.RESET}",
        help='具体命令的帮助信息'
    )
    
    # 搜索命令
    search_parser = subparsers.add_parser('search', help='搜索PyPI上的ErisPulse模块')
    search_parser.add_argument('query', type=str, help='搜索关键词')
    
    # 安装命令
    install_parser = subparsers.add_parser('install', help='安装模块/适配器包')
    install_parser.add_argument('package', type=str, help='要安装的包名')
    install_parser.add_argument('--upgrade', '-U', action='store_true', help='升级已安装的包')
    
    # 卸载命令
    uninstall_parser = subparsers.add_parser('uninstall', help='卸载模块/适配器包')
    uninstall_parser.add_argument('package', type=str, help='要卸载的包名')
    
    # 列表命令
    list_parser = subparsers.add_parser('list', help='列出已安装的模块/适配器')
    list_parser.add_argument('--type', '-t', choices=['modules', 'adapters', 'all'], default='all', 
                           help='列出类型 (modules: 仅模块, adapters: 仅适配器, all: 全部)')
    
    # 升级命令
    upgrade_parser = subparsers.add_parser('upgrade', help='升级所有模块/适配器')
    upgrade_parser.add_argument('--force', '-f', action='store_true', help='跳过确认直接升级')
    
    # 运行命令
    run_parser = subparsers.add_parser('run', help='运行指定主程序')
    run_parser.add_argument('script', type=str, help='要运行的主程序路径')
    run_parser.add_argument('--reload', action='store_true', help='启用热重载模式')
    
    # 旧版命令
    legacy_parser = subparsers.add_parser('legacy', help='旧版模块管理命令')
    legacy_subparsers = legacy_parser.add_subparsers(dest='legacy_command')
    
    # 旧版子命令
    legacy_enable = legacy_subparsers.add_parser('enable', help='启用模块')
    legacy_enable.add_argument('module', type=str, help='模块名称')
    
    legacy_disable = legacy_subparsers.add_parser('disable', help='禁用模块')
    legacy_disable.add_argument('module', type=str, help='模块名称')
    
    legacy_install = legacy_subparsers.add_parser('install', help='安装模块')
    legacy_install.add_argument('module', type=str, help='模块名称或路径')
    legacy_install.add_argument('--force', action='store_true', help='强制重新安装')
    
    legacy_uninstall = legacy_subparsers.add_parser('uninstall', help='卸载模块')
    legacy_uninstall.add_argument('module', type=str, help='模块名称')
    
    legacy_update = legacy_subparsers.add_parser('update', help='更新模块列表')
    
    legacy_upgrade = legacy_subparsers.add_parser('upgrade', help='升级模块')
    legacy_upgrade.add_argument('--force', action='store_true', help='跳过确认直接升级')
    
    legacy_origin = legacy_subparsers.add_parser('origin', help='管理模块源')
    legacy_origin_sub = legacy_origin.add_subparsers(dest='origin_command')
    legacy_origin_add = legacy_origin_sub.add_parser('add', help='添加源')
    legacy_origin_add.add_argument('url', type=str, help='源URL')
    legacy_origin_list = legacy_origin_sub.add_parser('list', help='列出源')
    legacy_origin_del = legacy_origin_sub.add_parser('del', help='删除源')
    legacy_origin_del.add_argument('url', type=str, help='源URL')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"{Shell_Printer.GREEN}ErisPulse {get_erispulse_version()}{Shell_Printer.RESET}")
        return
        
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "search":
            packages = PyPIManager.search_packages(args.query)
            if packages:
                rows = [
                    [
                        f"{Shell_Printer.BLUE}{pkg['name']}{Shell_Printer.RESET}",
                        pkg['description']
                    ] for pkg in packages
                ]
                shellprint.table(["包名", "描述"], rows, "搜索结果", "info")
            else:
                shellprint.panel(f"未找到匹配 '{args.query}' 的ErisPulse包", "提示", "info")
                
        elif args.command == "install":
            PyPIManager.install_package(args.package, args.upgrade)
            
        elif args.command == "uninstall":
            PyPIManager.uninstall_package(args.package)
            
        elif args.command == "list":
            installed = PyPIManager.get_installed_packages()
            
            if args.type in ["modules", "all"] and installed["modules"]:
                rows = [
                    [
                        f"{Shell_Printer.GREEN}{name}{Shell_Printer.RESET}",
                        f"{Shell_Printer.BLUE}{info['package']}{Shell_Printer.RESET}",
                        info["version"],
                        info["summary"]
                    ] for name, info in installed["modules"].items()
                ]
                shellprint.table(["模块名", "包名", "版本", "描述"], rows, "已安装模块", "info")
                
            if args.type in ["adapters", "all"] and installed["adapters"]:
                rows = [
                    [
                        f"{Shell_Printer.YELLOW}{name}{Shell_Printer.RESET}",
                        f"{Shell_Printer.BLUE}{info['package']}{Shell_Printer.RESET}",
                        info["version"],
                        info["summary"]
                    ] for name, info in installed["adapters"].items()
                ]
                shellprint.table(["适配器名", "包名", "版本", "描述"], rows, "已安装适配器", "info")
                
            if not installed["modules"] and not installed["adapters"]:
                shellprint.panel("没有安装任何ErisPulse模块或适配器", "提示", "info")
                
        elif args.command == "upgrade":
            if args.force or shellprint.confirm("确定要升级所有ErisPulse模块和适配器吗？", default=False):
                PyPIManager.upgrade_all()
                
        elif args.command == "run":
            run_script(args.script, args.reload)
            
        elif args.command == "legacy":
            legacy_command(args)
            
    except Exception as e:
        shellprint.panel(f"执行命令时出错: {e}", "错误", "error")

if __name__ == "__main__":
    main()