"""
ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

{!--< tips >!--}
1. 使用前请确保已正确安装所有依赖
2. 调用sdk.init()进行初始化
3. 模块加载顺序由依赖关系决定
{!--< /tips >!--}
"""

import os
import sys
import toml
import importlib.metadata
from typing import Dict, List, Tuple, Optional, Set, Type, Any
from pathlib import Path

# BaseModules: SDK核心模块
from .Core import util
from .Core import raiserr
from .Core import logger
from .Core import env
from .Core import mods
from .Core import adapter, AdapterFather, SendDSL

# 确保windows下的shell能正确显示颜色
os.system('')

sdk = sys.modules[__name__]

BaseModules = {
    "util": util,
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
    setattr(sdk, module, moduleObj)

for error, doc in BaseErrors.items():
    raiserr.register(error, doc=doc)


class PyPIModuleLoader:
    """
    PyPI包模块加载器

    依赖entry-points加载PyPI包中的模块和适配器
    
    {!--< tips >!--} 
    不支持使用"setup.py"进行模块加载, 请使用"pyproject.toml"进行ep-pypi包加载
    {!--< /tips >!--}
    """
    
    @staticmethod
    def load() -> Tuple[Dict[str, object], List[str], List[str]]:
        """
        从PyPI包entry-points加载模块

        :return: 
            Dict[str, object]: 模块对象字典
            List[str]: 启用的模块列表
            List[str]: 停用的模块列表
        """
        module_objs = {}
        enabled_modules = []
        disabled_modules = []
        
        try:
            # 加载模块entry-points
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                module_entries = entry_points.select(group='erispulse.module')
                adapter_entries = entry_points.select(group='erispulse.adapter')
            else:
                module_entries = entry_points.get('erispulse.module', [])
                adapter_entries = entry_points.get('erispulse.adapter', [])
            
            # 处理模块
            for entry_point in module_entries:
                module_objs, enabled_modules, disabled_modules = PyPIModuleLoader._process_entry_point(
                    entry_point, module_objs, enabled_modules, disabled_modules, is_adapter=False)
            
            # 处理适配器
            for entry_point in adapter_entries:
                module_objs, enabled_modules, disabled_modules = PyPIModuleLoader._process_entry_point(
                    entry_point, module_objs, enabled_modules, disabled_modules, is_adapter=True)
                    
        except Exception as e:
            logger.error(f"加载PyPI包entry-points失败: {e}")
            
        return module_objs, enabled_modules, disabled_modules
    
    @staticmethod
    def _process_entry_point(
        entry_point: Any,
        module_objs: Dict[str, object],
        enabled_modules: List[str],
        disabled_modules: List[str],
        is_adapter: bool = False
    ) -> Tuple[Dict[str, object], List[str], List[str]]:
        """
        {!--< internal-use >!--}
        处理单个entry-point
        
        :param entry_point: entry-point对象
        :param module_objs: 模块对象字典
        :param enabled_modules: 启用的模块列表
        :param disabled_modules: 停用的模块列表
        :param is_adapter: 是否为适配器 (默认: False)
        
        :return: 
            Dict[str, object]: 模块对象字典
            List[str]: 启用的模块列表
            List[str]: 停用的模块列表
        """
        try:
            loaded_obj = entry_point.load()
            module_obj = sys.modules[loaded_obj.__module__]
            dist = importlib.metadata.distribution(entry_point.dist.name)
            
            # 从pyproject.toml读取依赖配置
            requires, optional, pip_deps = PyPIModuleLoader._read_dependencies(dist)
            
            # 自动推断依赖
            auto_requires = PyPIModuleLoader._infer_dependencies(dist)
            
            # 合并显式和自动推断的依赖
            all_requires = list(set(requires + list(auto_requires)))
            
            # 创建moduleInfo
            module_info = {
                "meta": {
                    "name": entry_point.name,
                    "version": getattr(module_obj, "__version__", dist.version if dist else "1.0.0"),
                    "description": getattr(module_obj, "__description__", ""),
                    "author": getattr(module_obj, "__author__", ""),
                    "license": getattr(module_obj, "__license__", ""),
                    "package": entry_point.dist.name
                },
                "dependencies": {
                    "requires": all_requires,
                    "optional": optional,
                    "pip": pip_deps
                }
            }
            
            # 适配器特殊处理
            if is_adapter:
                if not hasattr(module_obj, 'adapterInfo'):
                    module_obj.adapterInfo = {}
                module_obj.adapterInfo[entry_point.name] = loaded_obj
            
            module_obj.moduleInfo = module_info
            
            # 检查模块状态
            meta_name = entry_point.name
            stored_info = mods.get_module(meta_name) or {
                "status": True,
                "info": module_info
            }
            mods.set_module(meta_name, stored_info)
            
            if not stored_info.get('status', True):
                disabled_modules.append(meta_name)
                logger.warning(f"{'适配器' if is_adapter else '模块'} {meta_name} 已禁用，跳过加载")
                return module_objs, enabled_modules, disabled_modules
                
            module_objs[meta_name] = module_obj
            enabled_modules.append(meta_name)
            logger.debug(f"从PyPI包加载{'适配器' if is_adapter else '模块'}: {meta_name}")
            
        except Exception as e:
            logger.warning(f"从entry-point加载{'适配器' if is_adapter else '模块'} {entry_point.name} 失败: {e}")
            
        return module_objs, enabled_modules, disabled_modules
    
    @staticmethod
    def _read_dependencies(dist: Any) -> Tuple[List[str], List[str], List[str]]:
        """
        {!--< internal-use >!--}
        从pyproject.toml读取依赖配置

        :param dist: 包分发对象
        
        :return: 
            List[str]: 必选依赖列表
            List[str]: 可选依赖列表 
            List[str]: pip依赖列表
        """
        requires = []
        optional = []
        pip_deps = []
        
        if dist is not None:
            pyproject = dist.read_text("pyproject.toml")
            if pyproject:
                try:
                    config = toml.loads(pyproject)
                    # 读取erispulse依赖
                    erispulse_deps = config.get("tool", {}).get("erispulse", {}).get("dependencies", {})
                    requires = erispulse_deps.get("requires", [])
                    optional = erispulse_deps.get("optional", [])
                    # 读取项目依赖作为pip依赖
                    project_deps = config.get("project", {}).get("dependencies", [])
                    pip_deps = [dep.split(';')[0].strip() for dep in project_deps]
                except Exception as e:
                    logger.warning(f"解析 {dist.name} 的pyproject.toml失败: {e}")
        return requires, optional, pip_deps
    
    @staticmethod
    def _infer_dependencies(dist: Any) -> Set[str]:
        """
        {!--< internal-use >!--}
        自动推断依赖
        
        :param dist: 包分发对象
        
        :return: Set[str]: 自动推断的依赖集合
        """
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
        return auto_requires


class DirectoryModuleLoader:
    """
    {!--< deprecated >!--} 我们不再推荐在目录下放置模块, 这只是一个兼容性适配
    目录模块加载器
    从指定(或内部)目录加载模块
    """
    
    @staticmethod
    def load(module_path: str) -> Tuple[Dict[str, object], List[str], List[str]]:
        """
        {!--< deprecated >!--} 我们不再推荐在目录下放置模块, 这只是一个兼容性适配
        扫描并加载目录中的模块

        :param module_path: 模块目录路径
        
        :return: 
            Dict[str, object]: 模块对象字典
            List[str]: 启用的模块列表
            List[str]: 停用的模块列表
        """
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
                module_obj = __import__(module_name)
                if not DirectoryModuleLoader._validate_module(module_obj, module_name):
                    continue
                    
                meta_name = module_obj.moduleInfo["meta"]["name"]
                module_info = mods.get_module(meta_name) or {
                    "status": True,
                    "info": module_obj.moduleInfo
                }
                mods.set_module(meta_name, module_info)
                
                if not module_info.get('status', True):
                    disabled_modules.append(module_name)
                    logger.warning(f"模块 {meta_name} 已禁用，跳过加载")
                    continue
                    
                DirectoryModuleLoader._check_dependencies(module_obj, module_name, os.listdir(module_path))
                module_objs[module_name] = module_obj
                enabled_modules.append(module_name)
                logger.debug(f"从目录加载模块: {module_name}")
                
            except Exception as e:
                logger.warning(f"模块 {module_name} 加载失败: {e}")
                
        return module_objs, enabled_modules, disabled_modules
    
    @staticmethod
    def _validate_module(module_obj: Any, module_name: str) -> bool:
        """
        {!--< internal-use >!--}
        {!--< deprecated >!--} 我们不再推荐在目录下放置模块, 这只是一个兼容性适配
        验证模块基本结构
        
        :param module_obj: 模块对象
        :param module_name: 模块名称
        
        :return: bool: 验证是否通过
        """
        if not hasattr(module_obj, "moduleInfo") or not isinstance(module_obj.moduleInfo, dict):
            logger.warning(f"模块 {module_name} 缺少有效的 'moduleInfo' 字典")
            return False
        if "name" not in module_obj.moduleInfo.get("meta", {}):
            logger.warning(f"模块 {module_name} 缺少必要 'name' 键")
            return False
        if not hasattr(module_obj, "Main"):
            logger.warning(f"模块 {module_name} 缺少 'Main' 类")
            return False
        return True
    
    @staticmethod
    def _check_dependencies(module_obj: Any, module_name: str, available_modules: List[str]) -> bool:
        """
        {!--< internal-use >!--}
        {!--< deprecated >!--} 我们不再推荐在目录下放置模块, 这只是一个兼容性适配
        检查模块依赖关系
        
        :param module_obj: 模块对象
        :param module_name: 模块名称
        :param available_modules: 可用模块列表
        
        :return: bool: 依赖检查是否通过
        """
        required_deps = module_obj.moduleInfo.get("dependencies", {}).get("requires", [])
        if missing := [dep for dep in required_deps if dep not in available_modules]:
            logger.error(f"模块 {module_name} 缺少必需依赖: {missing}")
            raiserr.MissingDependencyError(f"模块 {module_name} 缺少必需依赖: {missing}")
            return False

        optional_deps = module_obj.moduleInfo.get("dependencies", {}).get("optional", [])
        available_optional = [
            dep for dep in optional_deps 
            if (isinstance(dep, list) and any(d in available_modules for d in dep)) 
            or (not isinstance(dep, list) and dep in available_modules)
        ]
        if optional_deps and not available_optional:
            logger.warning(f"模块 {module_name} 缺少所有可选依赖: {optional_deps}")
            return False
        return True

class ModuleInitializer:
    """
    模块初始化器

    {!--< tips >!--}
    该类用于初始化模块的总类, 用于初始化所有模块
    {!--< /tips >!--}
    """
    
    @staticmethod
    def init() -> bool:
        """
        初始化所有模块
        
        执行步骤:
        1. 从PyPI包和本地目录加载模块
        2. 解析模块依赖关系并进行拓扑排序
        3. 注册模块适配器
        4. 初始化各模块
        
        :return: bool: 模块初始化是否成功
        
        {!--< tips >!--}
        1. 此方法是SDK初始化的入口点
        2. 如果初始化失败会抛出InitError异常
        3. 初始化过程会自动处理模块依赖关系
        {!--< /tips >!--}
        """
        logger.info("[Init] SDK 正在初始化...")
        
        try:
            # 1. 加载PyPI包模块
            logger.debug("[Init] 正在从PyPI包entry-points加载模块...")
            pkg_objs, pkg_enabled, pkg_disabled = PyPIModuleLoader.load()
            logger.info(f"[Init] 从PyPI包加载了 {len(pkg_enabled)} 个模块, {len(pkg_disabled)} 个模块被禁用")
            
            # 2. 加载目录模块
            module_path = os.path.join(os.path.dirname(__file__), "modules")
            logger.debug(f"[Init] 正在从目录 {module_path} 扫描模块...")
            dir_objs, dir_enabled, dir_disabled = DirectoryModuleLoader.load(module_path)
            logger.info(f"[Init] 从目录扫描加载了 {len(dir_enabled)} 个模块, {len(dir_disabled)} 个模块被禁用")
            
            # 3. 合并模块(PyPI包优先)
            module_objs = {**dir_objs, **pkg_objs}
            enabled_modules = list(set(pkg_enabled + dir_enabled))
            
            # 4. 检查模块冲突
            conflicts = set(pkg_enabled) & set(dir_enabled)
            if conflicts:
                logger.warning(f"[Init] 发现 {len(conflicts)} 个模块冲突, PyPI包中的模块将优先使用: {', '.join(conflicts)}")
            
            if not enabled_modules:
                logger.warning("[Init] 没有找到可用的模块")
                return True
                
            # 5. 解析依赖关系
            logger.debug(f"[Init] 开始解析 {len(enabled_modules)} 个模块的依赖关系...")
            sorted_modules = ModuleInitializer._resolve_dependencies(enabled_modules, module_objs)
            logger.info(f"[Init] 模块加载顺序(拓扑排序): {', '.join(sorted_modules)}")
            
            # 6. 注册适配器
            logger.debug("[Init] 正在注册适配器...")
            if not ModuleInitializer._register_adapters(sorted_modules, module_objs):
                return False
                
            # 7. 初始化模块
            logger.debug("[Init] 正在初始化模块...")
            success = ModuleInitializer._initialize_modules(sorted_modules, module_objs)
            logger.info(f"[Init] SDK初始化{'成功' if success else '失败'}")
            return success
            
        except Exception as e:
            logger.critical(f"SDK初始化严重错误: {e}")
            raiserr.InitError(f"sdk初始化失败: {e}", exit=True)
            return False
    
    @staticmethod
    def _resolve_dependencies(modules: List[str], module_objs: Dict[str, Any]) -> List[str]:
        """
        {!--< internal-use >!--}
        解析模块依赖关系并进行拓扑排序
        
        :param modules: 模块名称列表
        :param module_objs: 模块对象字典
        
        :return: List[str]: 拓扑排序后的模块列表
        """
        dependencies = {}
        package_deps = {}
        
        # 构建包名到模块名的映射
        pkg_to_mod = {}
        for mod_name in modules:
            pkg_name = module_objs[mod_name].moduleInfo["meta"].get("package")
            if pkg_name:
                pkg_to_mod[pkg_name] = mod_name
        
        for module_name in modules:
            module_obj = module_objs[module_name]
            req_deps = module_obj.moduleInfo.get("dependencies", {}).get("requires", [])
            opt_deps = module_obj.moduleInfo.get("dependencies", {}).get("optional", [])
            available_opt = [dep for dep in opt_deps if dep in modules]
            
            # 添加包级别的依赖
            pkg_deps = []
            pkg_name = module_obj.moduleInfo["meta"].get("package")
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
    
    @staticmethod
    def _register_adapters(modules: List[str], module_objs: Dict[str, Any]) -> bool:
        """
        {!--< internal-use >!--}
        注册适配器
        
        :param modules: 模块名称列表
        :param module_objs: 模块对象字典
        
        :return: bool: 适配器注册是否成功
        """
        success = True
        for module_name in modules:
            module_obj = module_objs[module_name]
            meta_name = module_obj.moduleInfo["meta"]["name"]
            
            try:
                if hasattr(module_obj, "adapterInfo") and isinstance(module_obj.adapterInfo, dict):
                    for platform, adapter_class in module_obj.adapterInfo.items():
                        sdk.adapter.register(platform, adapter_class)
                        logger.info(f"模块 {meta_name} 注册适配器: {platform}")
            except Exception as e:
                logger.error(f"模块 {meta_name} 适配器注册失败: {e}")
                success = False
        return success
    
    @staticmethod
    def _initialize_modules(modules: List[str], module_objs: Dict[str, Any]) -> bool:
        """
        {!--< internal-use >!--}
        初始化模块
        
        :param modules: 模块名称列表
        :param module_objs: 模块对象字典
        
        :return: bool: 模块初始化是否成功
        """
        success = True
        for module_name in modules:
            module_obj = module_objs[module_name]
            meta_name = module_obj.moduleInfo["meta"]["name"]
            
            try:
                if mods.get_module_status(meta_name):
                    module_main = module_obj.Main(sdk)
                    setattr(module_main, "moduleInfo", module_obj.moduleInfo)
                    setattr(sdk, meta_name, module_main)
                    logger.debug(f"模块 {meta_name} 初始化完成")
            except Exception as e:
                logger.error(f"模块 {meta_name} 初始化失败: {e}")
                success = False
        return success


def init_progress() -> Tuple[bool, bool]:
    """
    初始化项目环境文件

    :return: 
        bool: 项目环境文件是否初始化成功(文件已存在时返回False)
        bool: 项目入口文件是否初始化成功(文件已存在时返回False)
    
    {!--< tips >!--}
    1. 如果文件已存在，函数会返回(False, False)
    2. 此函数通常由SDK内部调用，不建议直接使用
    {!--< /tips >!--}
    """
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
        return False, False


def _prepare_environment() -> bool:
    """
    {!--< internal-use >!--}
    准备运行环境
    
    1. 初始化项目环境文件(env.py)
    2. 初始化项目入口文件(main.py)
    3. 加载环境变量
    
    :return: bool: 环境准备是否成功
    """
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

def init() -> bool:
    """
    SDK初始化入口
    
    执行步骤:
    1. 准备运行环境(创建env.py和main.py)
    2. 加载环境变量
    3. 初始化所有模块
    
    :return: bool: SDK初始化是否成功
    
    {!--< tips >!--}
    1. 这是SDK的主要入口函数
    2. 如果初始化失败会抛出InitError异常
    3. 建议在main.py中调用此函数
    {!--< /tips >!--}
    """
    if not _prepare_environment():
        return False
    return ModuleInitializer.init()


sdk.init = init
