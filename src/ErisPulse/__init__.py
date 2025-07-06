"""
# SDK 核心初始化

提供SDK全局对象构建和初始化功能。

## 主要功能
- 构建全局sdk对象
- 预注册核心错误类型
- 提供SDK初始化入口
- 集成各核心模块

## API 文档
### 核心对象：
    - sdk: 全局SDK命名空间对象
    - sdk.init(): SDK初始化入口函数

### 预注册错误类型：
    - CaughtExternalError: 外部捕获异常
    - InitError: 初始化错误
    - MissingDependencyError: 缺少依赖错误  
    - InvalidDependencyError: 无效依赖错误
    - CycleDependencyError: 循环依赖错误
    - ModuleLoadError: 模块加载错误

### 示例用法：

```
from ErisPulse import sdk

# 初始化SDK
sdk.init()

# 访问各模块功能
sdk.logger.info("SDK已初始化")
"""

import os
import sys
import toml
import importlib.metadata
from typing import Tuple, Dict, List, Any, Optional, Set, Union, Type, FrozenSet

# BaseModules: SDK核心模块
from .Core import util
from .Core import raiserr
from .Core import logger
from .Core import env
from .Core import mods
from .Core import adapter, AdapterFather, SendDSL

# 这里不能删，确保windows下的shell能正确显示颜色
os.system('')

sdk = sys.modules[__name__]

BaseModules = {
    "util"          : util,
    "logger"        : logger,
    "raiserr"       : raiserr,
    "env"           : env,
    "mods"          : mods,
    "adapter"       : adapter,
    "SendDSL"       : SendDSL,          # 链式发送基类 - 兼容原 sdk.SendDSL | 待弃用, 需要在 Adapter继承类中手动创建嵌套类并集成 super().SendDSL()
    "AdapterFather" : AdapterFather,
    "BaseAdapter"   : AdapterFather
}

BaseErrors = {
    "ExternalError"             : "外部捕获异常",
    "CaughtExternalError"       : "捕获的非SDK抛出的异常", 
    "InitError"                 : "SDK初始化错误",
    "MissingDependencyError"    : "缺少依赖错误",
    "InvalidDependencyError"    : "依赖无效错误",
    "CycleDependencyError"      : "依赖循环错误",
    "ModuleLoadError"           : "模块加载错误"
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
# 本文件由 SDK 自动创建，请勿随意删除
# 配置项可通过 sdk.env.get(key, default) 获取，或使用 sdk.env.set(key, value) 设置
# 你也可以像写普通变量一样直接定义配置项，例如：
#
#     MY_CONFIG = "value"
#     MY_CONFIG_2 = {"key": "value"}
#     MY_CONFIG_3 = [1, 2, 3]
#
#     sdk.env.set("MY_CONFIG", "value")
#     sdk.env.set("MY_CONFIG_2", {"key": "value"})
#     sdk.env.set("MY_CONFIG_3", [1, 2, 3])
#
# 这些变量会自动被加载到 SDK 的配置系统中，可通过 sdk.env.MY_CONFIG 或 sdk.env.get("MY_CONFIG") 访问。

from ErisPulse import sdk
'''
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(env_content)
            env_init = True
        if not main_file.exists():
            main_content = '''# main.py
# ErisPulse 主程序文件
# 本文件由 SDK 自动创建，您可随意修改
import asyncio
from ErisPulse import sdk

async def main():
    try:
        sdk.init()
        await sdk.adapter.startup()
        
        # 保持程序运行(不建议修改)
        await asyncio.Event().wait()
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
        return False

def _prepare_environment() -> bool:
    logger.info("[Init] 准备初始化环境...")
    try:
        env_init, main_init = init_progress()
        if env_init:
            logger.info("[Init] 项目首次初始化，建议先配置环境变量")
            if input("是否立即退出？(y/n): ").strip().lower() == "y":
                return False
        if main_init:
            logger.info("[Init] 项目入口已生成, 建议您在 main.py 中编写主程序")
            if input("是否立即退出？(y/n): ").strip().lower() == "y":
                return False
        env.load_env_file()
        return True
    except Exception as e:
        logger.error(f"环境准备失败: {e}")
        return False
def _load_from_entry_points() -> Tuple[Dict, List, List]:
    # 从entry-points加载PyPI包中的模块
    module_objs = {}
    enabled_modules = []
    disabled_modules = []
    package_map = {}  # 记录模块名到包名的映射
    
    try:
        # 加载模块entry-points
        entry_points = importlib.metadata.entry_points()
        # 处理Python 3.10+的API变化
        if hasattr(entry_points, 'select'):
            module_entries = entry_points.select(group='erispulse.module')
        else:
            module_entries = entry_points.get('erispulse.module', [])
        
        for entry_point in module_entries:
            try:
                module_main = entry_point.load()
                moduleObj = sys.modules[module_main.__module__]
                dist = importlib.metadata.distribution(entry_point.dist.name)
                
                # 从pyproject.toml读取依赖配置
                requires = []
                optional = []
                pip_deps = []
                
                # 读取tool.erispulse.dependencies配置
                if dist is not None:
                    pyproject = dist.read_text("pyproject.toml")
                    if pyproject:
                        try:
                            import toml
                            config = toml.loads(pyproject)
                            erispulse_deps = config.get("tool", {}).get("erispulse", {}).get("dependencies", {})
                            requires = erispulse_deps.get("requires", [])
                            optional = erispulse_deps.get("optional", [])
                            
                            # 读取项目依赖作为pip依赖
                            project_deps = config.get("project", {}).get("dependencies", [])
                            pip_deps = [dep.split(';')[0].strip() for dep in project_deps]
                        except Exception as e:
                            logger.warning(f"解析 {entry_point.dist.name} 的pyproject.toml失败: {e}")
                
                # 自动推断依赖：检查依赖包中的erispulse模块
                auto_requires = set()
                if dist is not None:
                    for dep in (dist.requires or []):
                        dep_name = dep.split(';')[0].strip().split('>')[0].split('<')[0].split('=')[0].split('~')[0]
                        try:
                            dep_dist = importlib.metadata.distribution(dep_name)
                            if dep_dist:
                                for ep in dep_dist.entry_points:
                                    if ep.group in ('erispulse.module', 'erispulse.adapter'):
                                        auto_requires.add(ep.name)
                        except:
                            continue

                # 合并显式和自动推断的依赖
                all_requires = list(set(requires + list(auto_requires)))

                # 为兼容性创建moduleInfo
                moduleObj.moduleInfo = {
                    "meta": {
                        "name": entry_point.name,
                        "version": getattr(moduleObj, "__version__", dist.version if dist else "1.0.0"),
                        "description": getattr(moduleObj, "__description__", ""),
                        "author": getattr(moduleObj, "__author__", ""),
                        "license": getattr(moduleObj, "__license__", ""),
                        "package": entry_point.dist.name
                    },
                    "dependencies": {
                        "requires": all_requires,
                        "optional": optional,
                        "pip": pip_deps
                    }
                }
                
                meta_name = entry_point.name
                module_info = mods.get_module(meta_name) or {
                    "status": True,
                    "info": moduleObj.moduleInfo
                }
                mods.set_module(meta_name, module_info)
                
                if not module_info.get('status', True):
                    disabled_modules.append(meta_name)
                    logger.warning(f"模块 {meta_name} 已禁用，跳过加载")
                    continue
                    
                module_objs[meta_name] = moduleObj
                enabled_modules.append(meta_name)
                
            except Exception as e:
                logger.warning(f"从entry-point加载模块 {entry_point.name} 失败: {e}")
                
        # 加载适配器entry-points
        entry_points = importlib.metadata.entry_points()
        # 处理Python 3.10+的API变化
        if hasattr(entry_points, 'select'):
            adapter_entries = entry_points.select(group='erispulse.adapter')
        else:
            adapter_entries = entry_points.get('erispulse.adapter', [])
            
        for entry_point in adapter_entries:
            try:
                adapter_class = entry_point.load()
                moduleObj = sys.modules[adapter_class.__module__]
                dist = importlib.metadata.distribution(entry_point.dist.name)
                
                # 从pyproject.toml读取依赖配置
                requires = []
                optional = []
                pip_deps = []
                
                # 读取tool.erispulse.dependencies配置
                if dist is not None:
                    pyproject = dist.read_text("pyproject.toml")
                    if pyproject:
                        try:
                            config = toml.loads(pyproject)
                            erispulse_deps = config.get("tool", {}).get("erispulse", {}).get("dependencies", {})
                            requires = erispulse_deps.get("requires", [])
                            optional = erispulse_deps.get("optional", [])
                            
                            # 读取项目依赖作为pip依赖
                            project_deps = config.get("project", {}).get("dependencies", [])
                            pip_deps = [dep.split(';')[0].strip() for dep in project_deps]
                        except Exception as e:
                            logger.warning(f"解析 {entry_point.dist.name} 的pyproject.toml失败: {e}")
                
                # 自动推断依赖：检查依赖包中的erispulse模块
                auto_requires = set()
                if dist is not None:
                    for dep in (dist.requires or []):
                        dep_name = dep.split(';')[0].strip().split('>')[0].split('<')[0].split('=')[0].split('~')[0]
                        try:
                            dep_dist = importlib.metadata.distribution(dep_name)
                            if dep_dist:
                                for ep in dep_dist.entry_points:
                                    if ep.group in ('erispulse.module', 'erispulse.adapter'):
                                        auto_requires.add(ep.name)
                        except:
                            continue

                # 合并显式和自动推断的依赖
                all_requires = list(set(requires + list(auto_requires)))

                # 为兼容性创建moduleInfo和adapterInfo
                moduleObj.moduleInfo = {
                    "meta": {
                        "name": entry_point.name,
                        "version": getattr(moduleObj, "__version__", dist.version if dist else "1.0.0"),
                        "description": getattr(moduleObj, "__description__", ""),
                        "author": getattr(moduleObj, "__author__", ""),
                        "license": getattr(moduleObj, "__license__", ""),
                        "package": entry_point.dist.name
                    },
                    "dependencies": {
                        "requires": all_requires,
                        "optional": optional,
                        "pip": pip_deps
                    }
                }
                
                if not hasattr(moduleObj, 'adapterInfo'):
                    moduleObj.adapterInfo = {}
                moduleObj.adapterInfo[entry_point.name] = adapter_class
                
                meta_name = entry_point.name
                module_info = mods.get_module(meta_name) or {
                    "status": True,
                    "info": moduleObj.moduleInfo
                }
                mods.set_module(meta_name, module_info)
                
                if not module_info.get('status', True):
                    disabled_modules.append(meta_name)
                    logger.warning(f"适配器 {meta_name} 已禁用，跳过加载")
                    continue
                    
                module_objs[meta_name] = moduleObj
                enabled_modules.append(meta_name)
                
            except Exception as e:
                logger.warning(f"从entry-point加载适配器 {entry_point.name} 失败: {e}")
                
    except Exception as e:
        logger.error(f"加载entry-points失败: {e}")
        
    return module_objs, enabled_modules, disabled_modules

def _scan_modules(module_path: str) -> Tuple[Dict, List, List]:
    """扫描并验证模块目录中的模块(兼容旧方式)"""
    module_objs = {}
    enabled_modules = []
    disabled_modules = []
    
    if not os.path.exists(module_path):
        os.makedirs(module_path)
    sys.path.append(module_path)

    for module_name in os.listdir(module_path):
        if not os.path.isdir(os.path.join(module_path, module_name)):
            continue
            
        try:
            moduleObj = __import__(module_name)
            if not _validate_module(moduleObj, module_name):
                continue
                
            meta_name = moduleObj.moduleInfo["meta"]["name"]
            module_info = mods.get_module(meta_name) or {
                "status": True,
                "info": moduleObj.moduleInfo
            }
            mods.set_module(meta_name, module_info)
            
            if not module_info.get('status', True):
                disabled_modules.append(module_name)
                logger.warning(f"模块 {meta_name} 已禁用，跳过加载")
                continue
                
            _check_dependencies(moduleObj, module_name, os.listdir(module_path))
            module_objs[module_name] = moduleObj
            enabled_modules.append(module_name)
            
        except Exception as e:
            logger.warning(f"模块 {module_name} 加载失败: {e}")
            
    return module_objs, enabled_modules, disabled_modules

def _validate_module(moduleObj, module_name: str) -> bool:
    # 验证模块基本结构
    if not hasattr(moduleObj, "moduleInfo") or not isinstance(moduleObj.moduleInfo, dict):
        logger.warning(f"模块 {module_name} 缺少有效的 'moduleInfo' 字典")
        return False
    if "name" not in moduleObj.moduleInfo.get("meta", {}):
        logger.warning(f"模块 {module_name} 缺少必要 'name' 键")
        return False
    if not hasattr(moduleObj, "Main"):
        logger.warning(f"模块 {module_name} 缺少 'Main' 类")
        return False
    return True

def _check_dependencies(moduleObj, module_name: str, available_modules: list) -> None:
    # 检查模块依赖关系
    required_deps = moduleObj.moduleInfo.get("dependencies", {}).get("requires", [])
    if missing := [dep for dep in required_deps if dep not in available_modules]:
        logger.error(f"模块 {module_name} 缺少必需依赖: {missing}")
        raiserr.MissingDependencyError(f"模块 {module_name} 缺少必需依赖: {missing}")

    optional_deps = moduleObj.moduleInfo.get("dependencies", {}).get("optional", [])
    available_optional = [
        dep for dep in optional_deps 
        if (isinstance(dep, list) and any(d in available_modules for d in dep)) 
        or (not isinstance(dep, list) and dep in available_modules)
    ]
    if optional_deps and not available_optional:
        logger.warning(f"模块 {module_name} 缺少所有可选依赖: {optional_deps}")

def _resolve_dependencies(modules: list, module_objs: dict) -> list:
    # 解析模块依赖关系并进行拓扑排序
    dependencies = {}
    package_deps = {}
    
    # 构建包名到模块名的映射
    pkg_to_mod = {}
    for mod_name in modules:
        pkg_name = module_objs[mod_name].moduleInfo["meta"].get("package")
        if pkg_name:
            pkg_to_mod[pkg_name] = mod_name
    
    for module_name in modules:
        moduleObj = module_objs[module_name]
        req_deps = moduleObj.moduleInfo.get("dependencies", {}).get("requires", [])
        opt_deps = moduleObj.moduleInfo.get("dependencies", {}).get("optional", [])
        available_opt = [dep for dep in opt_deps if dep in modules]
        
        # 添加包级别的依赖
        pkg_deps = []
        pkg_name = moduleObj.moduleInfo["meta"].get("package")
        if pkg_name:
            try:
                dist = importlib.metadata.distribution(pkg_name)
                for dep in (dist.requires or []):
                    dep_name = dep.split(';')[0].strip().split('>')[0].split('<')[0].split('=')[0].split('~')[0]
                    if dep_name in pkg_to_mod:
                        pkg_deps.append(pkg_to_mod[dep_name])
            except:
                pass
        
        dependencies[module_name] = list(set(req_deps + available_opt + pkg_deps))
        
    sorted_modules = sdk.util.topological_sort(modules, dependencies, raiserr.CycleDependencyError)
    env.set('module_dependencies', {
        'modules': sorted_modules,
        'dependencies': dependencies,
        'package_mapping': pkg_to_mod
    })
    return sorted_modules

def _register_adapters(modules: list, module_objs: dict) -> bool:
    # 注册适配器
    success = True
    logger.debug("[Init] 开始注册适配器...")
    for module_name in modules:
        moduleObj = module_objs[module_name]
        meta_name = moduleObj.moduleInfo["meta"]["name"]
        
        try:
            if hasattr(moduleObj, "adapterInfo") and isinstance(moduleObj.adapterInfo, dict):
                for platform, adapter_class in moduleObj.adapterInfo.items():
                    sdk.adapter.register(platform, adapter_class)
                    logger.info(f"模块 {meta_name} 注册适配器: {platform}")
        except Exception as e:
            logger.error(f"模块 {meta_name} 适配器注册失败: {e}")
            success = False
    return success

def _initialize_modules(modules: list, module_objs: dict) -> bool:
    # 初始化模块
    success = True
    logger.debug("[Init] 开始实例化模块...")
    for module_name in modules:
        moduleObj = module_objs[module_name]
        meta_name = moduleObj.moduleInfo["meta"]["name"]
        
        try:
            if mods.get_module_status(meta_name):
                moduleMain = moduleObj.Main(sdk)
                setattr(moduleMain, "moduleInfo", moduleObj.moduleInfo)
                setattr(sdk, meta_name, moduleMain)
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
            
        # 从entry-points加载PyPI包中的模块
        logger.debug("[Init] 正在从PyPI包entry-points加载模块...")
        pkg_objs, pkg_enabled, pkg_disabled = _load_from_entry_points()
        logger.info(f"[Init] 从PyPI包加载了 {len(pkg_enabled)} 个模块, {len(pkg_disabled)} 个模块被禁用")
        
        # 从modules目录加载传统模块(保持兼容)
        module_path = os.path.join(os.path.dirname(__file__), "modules")
        logger.debug(f"[Init] 正在从目录 {module_path} 扫描模块...")
        dir_objs, dir_enabled, dir_disabled = _scan_modules(module_path)
        logger.info(f"[Init] 从目录扫描加载了 {len(dir_enabled)} 个模块, {len(dir_disabled)} 个模块被禁用")
        
        # 合并模块(entry-points优先)
        module_objs = {**dir_objs, **pkg_objs}  # PyPI包中的模块会覆盖同名目录模块
        enabled_modules = list(set(pkg_enabled + dir_enabled))
        
        # 记录模块冲突情况
        conflicts = set(pkg_enabled) & set(dir_enabled)
        if conflicts:
            logger.warning(f"[Init] 发现 {len(conflicts)} 个模块冲突, PyPI包中的模块将优先使用: {', '.join(conflicts)}")
        
        if not enabled_modules:
            logger.warning("[Init] 没有找到可用的模块")
            return True
            
        logger.debug(f"[Init] 开始解析 {len(enabled_modules)} 个模块的依赖关系...")
        sorted_modules = _resolve_dependencies(enabled_modules, module_objs)
        logger.info(f"[Init] 模块加载顺序(拓扑排序): {', '.join(sorted_modules)}")
        
        # 注册适配器
        logger.debug("[Init] 正在注册适配器...")
        if not _register_adapters(sorted_modules, module_objs):
            return False
            
        # 初始化模块
        logger.debug("[Init] 正在初始化模块...")
        success = _initialize_modules(sorted_modules, module_objs)
        logger.info(f"[Init] SDK初始化{'成功' if success else '失败'}")
        return success
        
    except Exception as e:
        logger.critical(f"SDK初始化严重错误: {e}")
        raiserr.InitError(f"sdk初始化失败: {e}", exit=True)
        return False

sdk.init = init