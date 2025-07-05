import os
import sys
import importlib
import pkg_resources
from typing import Tuple, Dict, List, Any, Optional, Set, Union, Type, FrozenSet
import types

# 依赖类型
from .core import utils
from .core.error_manager import raiserr
from .core.logger import logger
from .core.env_manager import env
from .core.module_manager import mods
from .core.adapter_system import adapter, AdapterFather, SendDSL

util = utils

# 确保Windows下的shell能正确显示颜色
os.system('')

# sdk = types.SimpleNamespace()

# 指针式定义
sdk = sys.modules[__name__]

BaseModules = {
    "util": utils,
    "logger": logger,
    "raiserr": raiserr,
    "env": env,
    "mods": mods,
    "adapter": adapter,
    "SendDSL": SendDSL,
    "AdapterFather": AdapterFather,
    "BaseAdapter": AdapterFather
}

BaseErrors = {
    "ExternalError": "外部捕获异常",
    "CaughtExternalError": "捕获的非SDK抛出的异常",
    "InitError": "SDK初始化错误",
    "MissingDependencyError": "缺少依赖错误",
    "InvalidDependencyError": "依赖无效错误",
    "CycleDependencyError": "依赖循环错误",
    "ModuleLoadError": "模块加载错误"
}

for module, moduleObj in BaseModules.items():
    try:
        setattr(sdk, module, moduleObj)
    except Exception as e:
        raise e

for error, doc in BaseErrors.items():
    try:
        raiserr.register(error, doc=doc)
    except Exception as e:
        raise e

def init_progress() -> Tuple[bool, bool]:
    from pathlib import Path
    env_file = Path("env.py")
    main_file = Path("main.py")
    env_init = False
    main_init = False
    
    try:
        if not env_file.exists():
            env_content = '''# env.py
# ErisPulse 环境配置文件
from ErisPulse import sdk

# 基础配置
DEBUG = True

# 模块配置
# MODULE_CONFIG = {
#     "key": "value"
# }
'''
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(env_content)
            env_init = True
            
        if not main_file.exists():
            main_content = '''# main.py
import asyncio
from ErisPulse import sdk

async def main():
    try:
        sdk.init()
        await sdk.adapter.startup()
        await asyncio.Event().wait()  # 保持运行
    except Exception as e:
        sdk.logger.error(e)
    except KeyboardInterrupt:
        sdk.logger.info("正在停止程序")
    finally:
        await sdk.adapter.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
'''
            with open(main_file, "w", encoding="utf-8") as f:
                f.write(main_content)
            main_init = True
            
        return env_init, main_init
    except Exception as e:
        sdk.logger.error(f"无法初始化项目环境: {e}")
        return False, False

def _prepare_environment() -> bool:
    logger.info("[Init] 准备初始化环境...")
    try:
        env_init, main_init = init_progress()
        if env_init:
            logger.info("[Init] 已生成 env.py 配置文件")
        if main_init:
            logger.info("[Init] 已生成 main.py 入口文件")
        env.load_env_file()
        return True
    except Exception as e:
        logger.error(f"环境准备失败: {e}")
        return False

def _get_installed_packages() -> Dict[str, str]:
    packages = {}
    for dist in pkg_resources.working_set:
        if dist.key.startswith('erispulse-'):
            module_name = dist.key[len('erispulse-'):]
            packages[module_name] = dist.version
    return packages

def _load_package_module(package_name: str) -> Any:
    try:
        module_name = f"erispulse_{package_name.replace('-', '_')}"
        module = importlib.import_module(module_name)
        return module
    except ImportError as e:
        logger.warning(f"无法加载模块包 {package_name}: {e}")
        return None

def _scan_modules() -> Tuple[Dict, List, List]:
    module_objs = {}
    enabled_modules = []
    disabled_modules = []
    
    # 1. 首先扫描PyPI安装的模块
    installed_packages = _get_installed_packages()
    for module_name, version in installed_packages.items():
        try:
            module = _load_package_module(module_name)
            if not module:
                continue
                
            if not _validate_module(module, module_name):
                continue
                
            meta_name = module.moduleInfo["meta"]["name"]
            module_info = mods.get_module(meta_name) or {
                "status": True,
                "info": module.moduleInfo
            }
            mods.set_module(meta_name, module_info)
            
            if not module_info.get('status', True):
                disabled_modules.append(module_name)
                logger.warning(f"模块 {meta_name} 已禁用，跳过加载")
                continue
                
            _check_dependencies(module, module_name, installed_packages.keys())
            module_objs[module_name] = module
            enabled_modules.append(module_name)
            
        except Exception as e:
            logger.warning(f"模块包 {module_name} 加载失败: {e}")

    legacy_module_path = os.path.join(os.path.dirname(__file__), "modules")
    if os.path.exists(legacy_module_path):
        logger.warning(f"检测到旧版模块目录结构，建议迁移到PyPI包 | 即将弃用当前结构")
        sys.path.append(legacy_module_path)
        
        for module_name in os.listdir(legacy_module_path):
            if not os.path.isdir(os.path.join(legacy_module_path, module_name)):
                continue
                
            try:
                module = __import__(module_name)
                if not _validate_module(module, module_name):
                    continue
                    
                meta_name = module.moduleInfo["meta"]["name"]
                if meta_name in module_objs:
                    continue
                    
                module_info = mods.get_module(meta_name) or {
                    "status": True,
                    "info": module.moduleInfo
                }
                mods.set_module(meta_name, module_info)
                
                if not module_info.get('status', True):
                    disabled_modules.append(module_name)
                    logger.warning(f"模块 {meta_name} 已禁用，跳过加载")
                    continue
                    
                _check_dependencies(module, module_name, installed_packages.keys())
                module_objs[module_name] = module
                enabled_modules.append(module_name)
                
            except Exception as e:
                logger.warning(f"模块 {module_name} 加载失败: {e}")

    return module_objs, enabled_modules, disabled_modules

def _validate_module(module, module_name: str) -> bool:
    if not hasattr(module, "moduleInfo") or not isinstance(module.moduleInfo, dict):
        logger.warning(f"模块 {module_name} 缺少有效的 'moduleInfo' 字典")
        return False
    if "name" not in module.moduleInfo.get("meta", {}):
        logger.warning(f"模块 {module_name} 缺少必要 'name' 键")
        return False
    if not hasattr(module, "Main"):
        logger.warning(f"模块 {module_name} 缺少 'Main' 类")
        return False
    return True

def _check_dependencies(module, module_name: str, available_modules: list) -> None:
    required_deps = module.moduleInfo.get("dependencies", {}).get("requires", [])
    if missing := [dep for dep in required_deps if dep not in available_modules]:
        logger.error(f"模块 {module_name} 缺少必需依赖: {missing}")
        raiserr.MissingDependencyError(f"模块 {module_name} 缺少必需依赖: {missing}")

    optional_deps = module.moduleInfo.get("dependencies", {}).get("optional", [])
    available_optional = [
        dep for dep in optional_deps 
        if (isinstance(dep, list) and any(d in available_modules for d in dep)) 
        or (not isinstance(dep, list) and dep in available_modules)
    ]
    if optional_deps and not available_optional:
        logger.warning(f"模块 {module_name} 缺少所有可选依赖: {optional_deps}")

def _resolve_dependencies(modules: list, module_objs: dict) -> list:
    dependencies = {}
    for module_name in modules:
        module = module_objs[module_name]
        req_deps = module.moduleInfo.get("dependencies", {}).get("requires", [])
        opt_deps = module.moduleInfo.get("dependencies", {}).get("optional", [])
        available_opt = [dep for dep in opt_deps if dep in modules]
        dependencies[module_name] = req_deps + available_opt
        
    sorted_modules = util.topological_sort(modules, dependencies, raiserr.CycleDependencyError)
    env.set('module_dependencies', {
        'modules': sorted_modules,
        'dependencies': dependencies
    })
    return sorted_modules

def _register_adapters(modules: list, module_objs: dict) -> bool:
    success = True
    logger.debug("[Init] 开始注册适配器...")
    for module_name in modules:
        module = module_objs[module_name]
        meta_name = module.moduleInfo["meta"]["name"]
        
        try:
            if hasattr(module, "adapterInfo") and isinstance(module.adapterInfo, dict):
                for platform, adapter_class in module.adapterInfo.items():
                    adapter.register(platform, adapter_class)
                    logger.info(f"模块 {meta_name} 注册适配器: {platform}")
        except Exception as e:
            logger.error(f"模块 {meta_name} 适配器注册失败: {e}")
            success = False
    return success

def _initialize_modules(modules: list, module_objs: dict) -> bool:
    success = True
    logger.debug("[Init] 开始实例化模块...")
    for module_name in modules:
        module = module_objs[module_name]
        meta_name = module.moduleInfo["meta"]["name"]
        
        try:
            if mods.get_module_status(meta_name):
                module_main = module.Main(sdk)
                setattr(module_main, "moduleInfo", module.moduleInfo)
                setattr(sdk, meta_name, module_main)
                logger.debug(f"模块 {meta_name} 初始化完成")
        except Exception as e:
            logger.error(f"模块 {meta_name} 初始化失败: {e}")
            success = False
    return success

def init() -> bool:
    logger.info("[Init] SDK 正在初始化...")
    try:
        if not _prepare_environment():
            return False
            
        module_objs, enabled_modules, _ = _scan_modules()
        
        if not enabled_modules:
            logger.warning("没有找到可用的模块")
            return True
            
        sorted_modules = _resolve_dependencies(enabled_modules, module_objs)
        if not _register_adapters(sorted_modules, module_objs):
            return False
            
        return _initialize_modules(sorted_modules, module_objs)
        
    except Exception as e:
        logger.critical(f"SDK初始化严重错误: {e}")
        raiserr.InitError(f"sdk初始化失败: {e}", exit=True)
        return False

sdk.init = init