"""
legacy.py - 旧版模块管理兼容实现

{!--< deprecated >!--} 
此模块仅用于兼容旧版模块管理方式，新代码应使用PyPI包管理方式
"""

import os
import sys
import json
import aiohttp
import asyncio
import zipfile
import shutil
import fnmatch
import subprocess
from typing import Dict, List, Optional
from ..Core import env, mods
from ..Core.shellprint import shellprint, Shell_Printer

class LegacyManager:
    """旧版模块管理器"""
    
    def __init__(self):
        self._init_sources()
        
    def _init_sources(self):
        """初始化源"""
        if not env.get('origins'):
            env.set('origins', [])
            
            primary_source = "https://erisdev.com/map.json"
            secondary_source = "https://raw.githubusercontent.com/ErisPulse/ErisPulse-ModuleRepo/refs/heads/main/map.json"
            
            shellprint.status("正在验证主源...")
            validated_url = asyncio.run(self._validate_url(primary_source))
            
            if validated_url:
                env.set('origins', [validated_url])
                shellprint.status(f"主源 {validated_url} 已成功添加")
            else:
                if secondary_source not in env.get('origins', []):
                    env.set('origins', [secondary_source])
                    shellprint.panel(
                        f"主源不可用，已添加备用源 {secondary_source}\n\n"
                        f"{Shell_Printer.YELLOW}提示:{Shell_Printer.RESET} 建议尽快升级 ErisPulse SDK 版本",
                        "源初始化", 
                        "warning"
                    )

    async def _validate_url(self, url):
        """验证URL有效性"""
        if not url.startswith(('http://', 'https://')):
            protocol = shellprint.ask("未指定协议，请输入使用的协议", choices=['http', 'https'], default="https")
            url = f"{protocol}://{url}"
        if not url.endswith('.json'):
            url = f"{url}/map.json"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    try:
                        content = await response.text()
                        json.loads(content)
                        return url
                    except (ValueError, json.JSONDecodeError) as e:
                        shellprint.panel(f"源 {url} 返回的内容不是有效的 JSON 格式: {e}", "错误", "error")
                        return None
        except Exception as e:
            shellprint.panel(f"访问源 {url} 失败: {e}", "错误", "error")
            return None

    def handle(self, args):
        """处理旧版命令"""
        if not hasattr(args, 'legacy_command'):
            shellprint.panel("缺少子命令", "错误", "error")
            return
            
        if args.legacy_command == 'enable':
            self.enable_module(args.module)
        elif args.legacy_command == 'disable':
            self.disable_module(args.module)
        elif args.legacy_command == 'install':
            self.install_module(args.module, args.force)
        elif args.legacy_command == 'uninstall':
            self.uninstall_module(args.module)
        elif args.legacy_command == 'update':
            self.update_sources()
        elif args.legacy_command == 'upgrade':
            self.upgrade_all_modules(args.force)
        elif args.legacy_command == 'origin':
            self.handle_origin(args)
        else:
            shellprint.panel("未知的旧版命令", "错误", "error")

    def handle_origin(self, args):
        """处理源管理命令"""
        if not hasattr(args, 'origin_command'):
            shellprint.panel("缺少源子命令", "错误", "error")
            return
            
        if args.origin_command == 'add':
            self.add_source(args.url)
        elif args.origin_command == 'list':
            self.list_sources()
        elif args.origin_command == 'del':
            self.del_source(args.url)
        else:
            shellprint.panel("未知的源命令", "错误", "error")

    def add_source(self, value):
        """添加源"""
        shellprint.status(f"验证源: {value}")
        validated_url = asyncio.run(self._validate_url(value))
        if not validated_url:
            shellprint.panel("提供的源不是一个有效源，请检查后重试", "错误", "error")
            return False
            
        origins = env.get('origins')
        if validated_url not in origins:
            origins.append(validated_url)
            env.set('origins', origins)
            shellprint.panel(f"源 {validated_url} 已成功添加", "成功", "success")
            return True
        else:
            shellprint.panel(f"源 {validated_url} 已存在，无需重复添加", "提示", "info")
            return False

    def update_sources(self):
        """更新源"""
        shellprint.status("更新模块源...")
        origins = env.get('origins')
        providers = {}
        modules = {}
        module_alias = {}
        table_rows = []
        
        async def fetch_source_data():
            for i, origin in enumerate(origins):
                shellprint.status(f"获取源数据 ({i+1}/{len(origins)}): {origin}")
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(origin) as response:
                            response.raise_for_status()
                            try:
                                text = await response.text()
                                content = json.loads(text)
                                providers[content["name"]] = content["base"]
                                for module in content["modules"].keys():
                                    module_content = content["modules"][module]
                                    modules[f'{module}@{content["name"]}'] = module_content
                                    module_origin_name = module_content["path"]
                                    module_alias[f'{module_origin_name}@{content["name"]}'] = module
                                    table_rows.append([
                                        content['name'],
                                        module,
                                        f"{providers[content['name']]}{module_origin_name}"
                                    ])
                            except (ValueError, json.JSONDecodeError) as e:
                                shellprint.panel(f"源 {origin} 返回的内容不是有效的 JSON 格式: {e}", "错误", "error")
                except Exception as e:
                    shellprint.panel(f"获取 {origin} 时出错: {e}", "错误", "error")
                    
        asyncio.run(fetch_source_data())
        shellprint.table(["源", "模块", "地址"], table_rows, "源更新状态", "success")
        from datetime import datetime
        env.set('providers', providers)
        env.set('modules', modules)
        env.set('module_alias', module_alias)
        env.set('last_origin_update_time', datetime.now().isoformat())
        shellprint.panel("源更新完成", "成功", "success")

    def list_sources(self):
        """列出源"""
        origins = env.get('origins')
        if not origins:
            shellprint.panel("当前没有配置任何源", "提示", "info")
            return
            
        rows = [[str(idx), origin] for idx, origin in enumerate(origins, 1)]
        shellprint.table(["序号", "源地址"], rows, "已配置的源", "info")

    def del_source(self, value):
        """删除源"""
        origins = env.get('origins')
        if value in origins:
            origins.remove(value)
            env.set('origins', origins)
            shellprint.panel(f"源 {value} 已成功删除", "成功", "success")
        else:
            shellprint.panel(f"源 {value} 不存在", "错误", "error")

    def enable_module(self, module_name):
        """启用模块"""
        shellprint.status(f"启用模块: {module_name}")
        module_info = mods.get_module(module_name)
        if module_info:
            mods.set_module_status(module_name, True)
            shellprint.panel(f"模块 {module_name} 已成功启用", "成功", "success")
        else:
            shellprint.panel(f"模块 {module_name} 不存在", "错误", "error")

    def disable_module(self, module_name):
        """禁用模块"""
        shellprint.status(f"禁用模块: {module_name}")
        module_info = mods.get_module(module_name)
        if module_info:
            mods.set_module_status(module_name, False)
            shellprint.panel(f"模块 {module_name} 已成功禁用", "成功", "success")
        else:
            shellprint.panel(f"模块 {module_name} 不存在", "错误", "error")

    def install_module(self, module_name, force=False):
        """安装模块"""
        if module_name.startswith('.') or os.path.isabs(module_name):
            return self.install_local_module(module_name, force)
            
        shellprint.panel(f"准备安装模块: {Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET}", "安装摘要", "info")
        last_update_time = env.get('last_origin_update_time', None)
        if last_update_time:
            from datetime import datetime, timedelta
            last_update = datetime.fromisoformat(last_update_time)
            if datetime.now() - last_update > timedelta(hours=720):
                shellprint.panel("距离上次源更新已超过30天，源内可能有新模块或更新。", "提示", "warning")
                if shellprint.confirm("是否在安装模块前更新源？", default=True):
                    self.update_sources()
                    env.set('last_origin_update_time', datetime.now().isoformat())
                    shellprint.status("源更新完成")
    
        module_info = mods.get_module(module_name)
        if module_info and not force:
            meta = module_info.get('info', {}).get('meta', {})
            shellprint.panel(
                f"{Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET}\n版本: {meta.get('version', '未知')}\n描述: {meta.get('description', '无描述')}",
                "模块已存在",
                "info"
            )
            if not shellprint.confirm("是否要强制重新安装？", default=False):
                return
                
        providers = env.get('providers', {})
        if isinstance(providers, str):
            providers = json.loads(providers)
        module_info_list = []
        
        for provider, url in providers.items():
            module_key = f"{module_name}@{provider}"
            modules_data = env.get('modules', {})
            if isinstance(modules_data, str):
                modules_data = json.loads(modules_data)
            if module_key in modules_data:
                module_data = modules_data[module_key]
                meta = module_data.get("meta", {})
                depsinfo = module_data.get("dependencies", {})
                module_info_list.append({
                    'provider': provider,
                    'url': url,
                    'path': module_data.get('path', ''),
                    'version': meta.get('version', '未知'),
                    'description': meta.get('description', '无描述'),
                    'author': meta.get('author', '未知'),
                    'dependencies': depsinfo.get("requires", []),
                    'optional_dependencies': depsinfo.get("optional", []),
                    'pip_dependencies': depsinfo.get("pip", [])
                })
                
        if not module_info_list:
            shellprint.panel(f"未找到模块 {module_name}", "错误", "error")
            if providers:
                print(f"{Shell_Printer.BOLD}当前可用源:{Shell_Printer.RESET}")
                for provider in providers:
                    print(f"  {Shell_Printer.CYAN}- {provider}{Shell_Printer.RESET}")
            return
            
        if len(module_info_list) > 1:
            print(f"找到 {Shell_Printer.BOLD}{len(module_info_list)}{Shell_Printer.RESET} 个源的 {Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET} 模块：")
            rows = []
            for i, info in enumerate(module_info_list):
                rows.append([
                    f"{Shell_Printer.CYAN}{i+1}{Shell_Printer.RESET}", 
                    info['provider'], 
                    info['version'], 
                    info['description'], 
                    info['author']
                ])
            shellprint.table(["编号", "源", "版本", "描述", "作者"], rows, "可选模块源", "info")
            
            while True:
                choice = shellprint.ask("请选择要安装的源 (输入编号)", [str(i) for i in range(1, len(module_info_list)+1)])
                if choice and 1 <= int(choice) <= len(module_info_list):
                    selected_module = module_info_list[int(choice)-1]
                    break
                else:
                    print(f"{Shell_Printer.YELLOW}输入无效，请重新选择{Shell_Printer.RESET}")
        else:
            selected_module = module_info_list[0]
            
        # 安装依赖
        for dep in selected_module['dependencies']:
            print(f"\n{Shell_Printer.BOLD}处理依赖: {dep}{Shell_Printer.RESET}")
            self.install_module(dep)
            
        # 安装pip依赖
        third_party_deps = selected_module.get('pip_dependencies', [])
        if third_party_deps:
            print(f"{Shell_Printer.YELLOW}模块 {module_name} 需要以下pip依赖: {', '.join(third_party_deps)}{Shell_Printer.RESET}")
            if not self.install_pip_dependencies(third_party_deps):
                print(f"{Shell_Printer.RED}无法安装模块 {module_name} 的pip依赖，安装终止{Shell_Printer.RESET}")
                return
                
        # 下载并安装模块
        module_url = selected_module['url'] + selected_module['path']
        script_dir = os.path.dirname(os.path.abspath(__file__))
        module_dir = os.path.join(script_dir, 'modules', module_name)
        zip_path = os.path.join(script_dir, f"{module_name}.zip")
        
        if not self.extract_and_setup_module(
            module_name=module_name,
            module_url=module_url,
            zip_path=zip_path,
            module_dir=module_dir
        ):
            return
            
        # 注册模块信息
        mods.set_module(module_name, {
            'status': True,
            'info': {
                'meta': {
                    'version': selected_module['version'],
                    'description': selected_module['description'],
                    'author': selected_module['author'],
                    'pip_dependencies': selected_module['pip_dependencies']
                },
                'dependencies': {
                    'requires': selected_module['dependencies'],
                    'optional': selected_module['optional_dependencies'],
                    'pip': selected_module['pip_dependencies']
                }
            }
        })
        
        shellprint.panel(f"模块 {Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET} 安装成功", "成功", "success")

    def install_local_module(self, module_path, force=False):
        """安装本地模块"""
        try:
            module_path = os.path.abspath(module_path)
            if not os.path.exists(module_path):
                shellprint.panel(f"路径不存在: {module_path}", "错误", "error")
                return False
            
            module_name = os.path.basename(module_path.rstrip('/\\'))
            init_py = os.path.join(module_path, '__init__.py')
            
            if not os.path.exists(init_py):
                shellprint.panel(f"目录 {module_path} 不是一个有效的Python模块", "错误", "error")
                return False
            import sys
            sys.path.insert(0, os.path.dirname(module_path))
            try:
                module = __import__(module_name)
                if not hasattr(module, 'moduleInfo'):
                    shellprint.panel(f"模块 {module_name} 缺少 moduleInfo 定义", "错误", "error")
                    return False
            finally:
                sys.path.remove(os.path.dirname(module_path))
        except Exception as e:
            shellprint.panel(f"导入模块 {module_name} 失败: {e}", "错误", "error")
            return False
        
        module_info = mods.get_module(module_name)
        if module_info and not force:
            meta = module_info.get('info', {}).get('meta', {})
            shellprint.panel(
                f"{Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET}\n版本: {meta.get('version', '未知')}\n描述: {meta.get('description', '无描述')}",
                "模块已存在",
                "info"
            )
            if not shellprint.confirm("是否要强制重新安装？", default=False):
                return False
    
        # 复制模块到modules目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.join(script_dir, 'modules', module_name)
        
        try:
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            shutil.copytree(module_path, target_dir)
        except Exception as e:
            shellprint.panel(f"复制模块文件失败: {e}", "错误", "error")
            return False
        
        # 安装依赖
        dependencies = module.moduleInfo.get('dependencies', {})
        for dep in dependencies.get('requires', []):
            print(f"\n{Shell_Printer.BOLD}处理依赖: {dep}{Shell_Printer.RESET}")
            self.install_module(dep)
            
        # 安装pip依赖
        pip_dependencies = dependencies.get('pip', [])
        if pip_dependencies:
            print(f"{Shell_Printer.YELLOW}模块 {module_name} 需要以下pip依赖: {', '.join(pip_dependencies)}{Shell_Printer.RESET}")
            if not self.install_pip_dependencies(pip_dependencies):
                print(f"{Shell_Printer.RED}无法安装模块 {module_name} 的pip依赖，安装终止{Shell_Printer.RESET}")
                return False
                
        # 注册模块信息
        mods.set_module(module_name, {
            'status': True,
            'info': {
                'meta': module.moduleInfo.get('meta', {}),
                'dependencies': module.moduleInfo.get('dependencies', {})
            }
        })
        
        shellprint.panel(f"本地模块 {Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET} 安装成功", "成功", "success")
        return True

    def install_pip_dependencies(self, dependencies):
        """安装pip依赖"""
        if not dependencies:
            return True
            
        print(f"{Shell_Printer.CYAN}正在安装pip依赖: {', '.join(dependencies)}{Shell_Printer.RESET}")
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "pip", "install"] + dependencies,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"{Shell_Printer.DIM}{output.strip()}{Shell_Printer.RESET}")
                    
            return process.returncode == 0
            
        except subprocess.CalledProcessError as e:
            shellprint.panel(f"安装pip依赖失败: {e.stderr}", "错误", "error")
            return False

    def extract_and_setup_module(self, module_name, module_url, zip_path, module_dir):
        """解压并设置模块"""
        try:
            print(f"正在下载模块: {Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET}")
            current_downloaded = [0]
            total_size = [0]
            
            def progress_callback(downloaded, total):
                if total > 0 and total_size[0] == 0:
                    total_size[0] = total
                if downloaded > current_downloaded[0]:
                    current_downloaded[0] = downloaded
                    prefix = f"{Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET} {Shell_Printer.DIM}下载中{Shell_Printer.RESET}"
                    suffix = f"{downloaded/1024:.1f}KB/{total/1024:.1f}KB" if total > 0 else f"{downloaded/1024:.1f}KB"
                    shellprint.progress_bar(downloaded, total or downloaded, prefix, suffix, 40)
                    
            async def download_module():
                async with aiohttp.ClientSession() as session:
                    content = await self.fetch_url(session, module_url, progress_callback)
                    if content is None:
                        return False
                        
                    with open(zip_path, 'wb') as zip_file:
                        zip_file.write(content)
                        
                    if total_size[0] > 0:
                        shellprint.progress_bar(total_size[0], total_size[0], 
                                             f"{Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET}",
                                             "下载完成", 40)
                        
                    if not os.path.exists(module_dir):
                        os.makedirs(module_dir)
                        
                    shellprint.status(f"解压模块: {module_name}")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        file_list = zip_ref.namelist()
                        for i, file in enumerate(file_list):
                            zip_ref.extract(file, module_dir)
                            if len(file_list) > 10 and i % (len(file_list) // 10) == 0:
                                shellprint.progress_bar(i, len(file_list), 
                                                     f"{Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET}",
                                                     "解压中", 30)
                        if len(file_list) > 10:
                            shellprint.progress_bar(len(file_list), len(file_list), 
                                                 f"{Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET}",
                                                 "解压完成", 30)
                    print()
                    
                    init_file_path = os.path.join(module_dir, '__init__.py')
                    if not os.path.exists(init_file_path):
                        sub_module_dir = os.path.join(module_dir, module_name)
                        m_sub_module_dir = os.path.join(module_dir, f"m_{module_name}")
                        for sub_dir in [sub_module_dir, m_sub_module_dir]:
                            if os.path.exists(sub_dir) and os.path.isdir(sub_dir):
                                for item in os.listdir(sub_dir):
                                    source_item = os.path.join(sub_dir, item)
                                    target_item = os.path.join(module_dir, item)
                                    if os.path.exists(target_item):
                                        os.remove(target_item)
                                    shutil.move(source_item, module_dir)
                                os.rmdir(sub_dir)
                    print(f"模块 {module_name} 文件已成功解压并设置")
                    return True
                    
            return asyncio.run(download_module())
        except Exception as e:
            shellprint.panel(f"处理模块 {module_name} 文件失败: {e}", "错误", "error")
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception as cleanup_error:
                    print(f"清理失败: {cleanup_error}")
            return False
        finally:
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception as cleanup_error:
                    print(f"清理失败: {cleanup_error}")

    async def fetch_url(self, session, url, progress_callback=None):
        """获取URL内容"""
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                data = b''
                
                async for chunk in response.content.iter_any():
                    data += chunk
                    downloaded += len(chunk)
                    if total_size and progress_callback:
                        progress_callback(downloaded, total_size)
                        
                return data
        except Exception as e:
            print(f"请求失败: {e}")
            return None

    def uninstall_module(self, module_name):
        """卸载模块"""
        shellprint.panel(f"准备卸载模块: {Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET}", "卸载摘要", "warning")
        module_info = mods.get_module(module_name)
        if not module_info:
            shellprint.panel(f"模块 {module_name} 不存在", "错误", "error")
            return
            
        meta = module_info.get('info', {}).get('meta', {})
        depsinfo = module_info.get('info', {}).get('dependencies', {})
        shellprint.panel(
            f"版本: {Shell_Printer.BOLD}{meta.get('version', '未知')}{Shell_Printer.RESET}\n"
            f"描述: {meta.get('description', '无描述')}\n"
            f"pip依赖: {Shell_Printer.YELLOW}{', '.join(depsinfo.get('pip', [])) or '无'}{Shell_Printer.RESET}",
            "模块信息",
            "info"
        )
        
        if not shellprint.confirm("确认要卸载此模块吗？", default=False):
            print(f"{Shell_Printer.BLUE}卸载已取消{Shell_Printer.RESET}")
            return
            
        script_dir = os.path.dirname(os.path.abspath(__file__))
        module_path = os.path.join(script_dir, 'modules', module_name)
        module_file_path = module_path + '.py'
        
        if os.path.exists(module_file_path):
            try:
                shellprint.status(f"删除模块文件: {module_name}.py")
                os.remove(module_file_path)
            except Exception as e:
                shellprint.panel(f"删除模块文件 {module_name} 时出错: {e}", "错误", "error")
        elif os.path.exists(module_path) and os.path.isdir(module_path):
            try:
                shellprint.status(f"删除模块目录: {module_name}")
                shutil.rmtree(module_path)
            except Exception as e:
                shellprint.panel(f"删除模块目录 {module_name} 时出错: {e}", "错误", "error")
        else:
            shellprint.panel(f"模块 {module_name} 文件不存在", "错误", "error")
            return
            
        pip_dependencies = depsinfo.get('pip', [])
        if pip_dependencies:
            all_modules = mods.get_all_modules()
            unused_pip_dependencies = []
            essential_packages = {'aiohttp'}
            for dep in pip_dependencies:
                if dep in essential_packages:
                    print(f"{Shell_Printer.CYAN}跳过必要模块 {dep} 的卸载{Shell_Printer.RESET}")
                    continue
                    
                is_dependency_used = False
                for name, info in all_modules.items():
                    if name != module_name and dep in info.get('info', {}).get('dependencies', {}).get('pip', []):
                        is_dependency_used = True
                        break
                        
                if not is_dependency_used:
                    unused_pip_dependencies.append(dep)
                    
            if unused_pip_dependencies:
                shellprint.panel(
                    f"以下 pip 依赖不再被其他模块使用:\n{Shell_Printer.YELLOW}{', '.join(unused_pip_dependencies)}{Shell_Printer.RESET}",
                    "可卸载依赖",
                    "info"
                )
                if shellprint.confirm("是否卸载这些 pip 依赖？", default=False):
                    try:
                        shellprint.status(f"卸载pip依赖: {', '.join(unused_pip_dependencies)}")
                        subprocess.run(
                            [sys.executable, "-m", "pip", "uninstall", "-y"] + unused_pip_dependencies,
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        shellprint.panel(
                            f"成功卸载 pip 依赖: {', '.join(unused_pip_dependencies)}",
                            "成功",
                            "success"
                        )
                    except subprocess.CalledProcessError as e:
                        shellprint.panel(
                            f"卸载 pip 依赖失败: {e.stderr.decode()}",
                            "错误",
                            "error"
                        )
                        
        if mods.remove_module(module_name):
            shellprint.panel(f"模块 {Shell_Printer.BOLD}{module_name}{Shell_Printer.RESET} 已成功卸载", "成功", "success")
        else:
            shellprint.panel(f"模块 {module_name} 不存在", "错误", "error")

    def upgrade_all_modules(self, force=False):
        """升级所有模块"""
        all_modules = mods.get_all_modules()
        if not all_modules:
            print(f"{Shell_Printer.YELLOW}未找到任何模块，无法更新{Shell_Printer.RESET}")
            return
            
        providers = env.get('providers', {})
        if isinstance(providers, str):
            providers = json.loads(providers)
        modules_data = env.get('modules', {})
        if isinstance(modules_data, str):
            modules_data = json.loads(modules_data)
            
        updates_available = []
        for module_name, module_info in all_modules.items():
            shellprint.status(f"检查更新: {module_name}")
            local_version = module_info.get('info', {}).get('meta', {}).get('version', '0.0.0')
            for provider, url in providers.items():
                module_key = f"{module_name}@{provider}"
                if module_key in modules_data:
                    remote_module = modules_data[module_key]
                    remote_version = remote_module.get('meta', {}).get('version', '1.14.514')
                    if remote_version > local_version:
                        updates_available.append({
                            'name': module_name,
                            'local_version': local_version,
                            'remote_version': remote_version,
                            'provider': provider,
                            'url': url,
                            'path': remote_module.get('path', ''),
                        })
                        
        if not updates_available:
            print(f"{Shell_Printer.GREEN}所有模块已是最新版本，无需更新{Shell_Printer.RESET}")
            return
            
        print(f"\n{Shell_Printer.BOLD}以下模块有可用更新：{Shell_Printer.RESET}")
        rows = []
        for update in updates_available:
            rows.append([
                update['name'], 
                update['local_version'], 
                f"{Shell_Printer.GREEN}{update['remote_version']}{Shell_Printer.RESET}", 
                update['provider']
            ])
        shellprint.table(["模块", "当前版本", "最新版本", "源"], rows, "可用更新", "info")
        
        if not force:
            warning_msg = (
                f"{Shell_Printer.BOLD}{Shell_Printer.RED}警告:{Shell_Printer.RESET} "
                "更新模块可能会导致兼容性问题，请在更新前查看插件作者的相关声明。\n"
                "是否继续？"
            )
            if not shellprint.confirm(warning_msg, default=False):
                print(f"{Shell_Printer.BLUE}更新已取消{Shell_Printer.RESET}")
                return
                
        for i, update in enumerate(updates_available, 1):
            print(f"\n{Shell_Printer.BOLD}[{i}/{len(updates_available)}]{Shell_Printer.RESET} 更新模块 {Shell_Printer.BOLD}{update['name']}{Shell_Printer.RESET}")
            
            # 检查新版本的依赖
            module_key = f"{update['name']}@{update['provider']}"
            new_module_info = modules_data[module_key]
            new_dependencies = new_module_info.get('dependencies', {}).get('requires', [])
            
            # 检查缺失的依赖
            missing_deps = []
            for dep in new_dependencies:
                if dep not in all_modules or not all_modules[dep].get('status', True):
                    missing_deps.append(dep)
                    
            if missing_deps:
                shellprint.panel(
                    f"模块 {update['name']} 需要以下依赖:\n{Shell_Printer.YELLOW}{', '.join(missing_deps)}{Shell_Printer.RESET}",
                    "缺失依赖",
                    "warning"
                )
                if not shellprint.confirm("是否安装这些依赖？", default=True):
                    print(f"{Shell_Printer.BLUE}跳过模块 {update['name']} 的更新{Shell_Printer.RESET}")
                    continue
                    
                for dep in missing_deps:
                    print(f"\n{Shell_Printer.BOLD}安装依赖: {dep}{Shell_Printer.RESET}")
                    self.install_module(dep)
            
            module_url = update['url'] + update['path']
            script_dir = os.path.dirname(os.path.abspath(__file__))
            module_dir = os.path.join(script_dir, 'modules', update['name'])
            zip_path = os.path.join(script_dir, f"{update['name']}.zip")
            
            # 检查新版本的pip依赖
            new_pip_deps = new_module_info.get('dependencies', {}).get('pip', [])
            current_pip_deps = all_modules[update['name']].get('info', {}).get('dependencies', {}).get('pip', [])
            added_pip_deps = [dep for dep in new_pip_deps if dep not in current_pip_deps]
            
            if added_pip_deps:
                shellprint.panel(
                    f"模块 {update['name']} 需要以下新的pip依赖:\n{Shell_Printer.YELLOW}{', '.join(added_pip_deps)}{Shell_Printer.RESET}",
                    "新增pip依赖",
                    "warning"
                )
                if not shellprint.confirm("是否安装这些pip依赖？", default=True):
                    print(f"{Shell_Printer.BLUE}跳过模块 {update['name']} 的更新{Shell_Printer.RESET}")
                    continue
                    
                if not self.install_pip_dependencies(added_pip_deps):
                    print(f"{Shell_Printer.RED}无法安装模块 {update['name']} 的pip依赖，更新终止{Shell_Printer.RESET}")
                    continue

            if not self.extract_and_setup_module(
                module_name=update['name'],
                module_url=module_url,
                zip_path=zip_path,
                module_dir=module_dir
            ):
                continue
                
            # 更新模块信息，包括新的依赖
            all_modules[update['name']]['info']['version'] = update['remote_version']
            all_modules[update['name']]['info']['dependencies'] = {
                'requires': new_dependencies,
                'pip': new_pip_deps
            }
            mods.set_all_modules(all_modules)
            print(f"{Shell_Printer.GREEN}模块 {update['name']} 已更新至版本 {update['remote_version']}{Shell_Printer.RESET}")
            
        shellprint.panel("所有可用更新已处理完成", "完成", "success")

    def list_modules(self, module_name=None):
        """列出模块"""
        all_modules = mods.get_all_modules()
        if not all_modules:
            shellprint.panel("未在数据库中发现注册模块,正在初始化模块列表...", "提示", "info")
            from .. import init as init_module
            init_module()
            all_modules = mods.get_all_modules()
            
        if not all_modules:
            shellprint.panel("未找到任何模块", "错误", "error")
            return
            
        shellprint.panel(f"找到 {Shell_Printer.BOLD}{len(all_modules)}{Shell_Printer.RESET} 个模块", "统计", "info")
        
        rows = []
        for name, info in all_modules.items():
            # 根据状态设置颜色
            status_color = Shell_Printer.GREEN if info.get("status", True) else Shell_Printer.RED
            status = f"{status_color}✓" if info.get("status", True) else f"{Shell_Printer.RED}✗"
            
            meta = info.get('info', {}).get('meta', {})
            depsinfo = info.get('info', {}).get('dependencies', {})
            optional_deps = depsinfo.get('optional', [])
            
            available_optional_deps = []
            missing_optional_deps = []
            if optional_deps:
                for dep in optional_deps:
                    if isinstance(dep, list):
                        available_deps = [d for d in dep if d in all_modules]
                        if available_deps:
                            available_optional_deps.extend(available_deps)
                        else:
                            missing_optional_deps.extend(dep)
                    elif dep in all_modules:
                        available_optional_deps.append(dep)
                    else:
                        missing_optional_deps.append(dep)
                        
                if missing_optional_deps:
                    optional_dependencies = f"可用: {', '.join(available_optional_deps)} 缺失: {Shell_Printer.RED}{', '.join(missing_optional_deps)}{Shell_Printer.RESET}"
                else:
                    optional_dependencies = ', '.join(available_optional_deps) or '无'
            else:
                optional_dependencies = '无'
                
            # 依赖项使用不同颜色标识
            dependencies = Shell_Printer.YELLOW + ', '.join(depsinfo.get('requires', [])) + Shell_Printer.RESET or '无'
            pip_dependencies = Shell_Printer.CYAN + ', '.join(depsinfo.get('pip', [])) + Shell_Printer.RESET or '无'
            
            rows.append([
                Shell_Printer.BOLD + name + Shell_Printer.RESET, 
                status, 
                Shell_Printer.BLUE + meta.get('version', '未知') + Shell_Printer.RESET, 
                meta.get('description', '无描述'),
                dependencies, 
                optional_dependencies, 
                pip_dependencies
            ])
            
        shellprint.table(
            ["模块名称", "状态", "版本", "描述", "依赖", "可选依赖", "pip依赖"],
            rows,
            "模块列表",
            "info"
        )
        
        enabled_count = sum(1 for m in all_modules.values() if m.get("status", True))
        disabled_count = len(all_modules) - enabled_count
        shellprint.panel(
            f"{Shell_Printer.GREEN}已启用: {enabled_count}{Shell_Printer.RESET}  "
            f"{Shell_Printer.RED}已禁用: {disabled_count}{Shell_Printer.RESET}",
            "模块状态统计",
            "info"
        )
