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
import inspect
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


class AdapterLoader:
    """
    适配器加载器
    
    专门用于从PyPI包加载和初始化适配器

    {!--< tips >!--}
    1. 适配器必须通过entry-points机制注册到erispulse.adapter组
    2. 适配器类必须继承BaseAdapter
    {!--< /tips >!--}
    """
    
    @staticmethod
    def load() -> Tuple[Dict[str, object], List[str], List[str]]:
        """
        从PyPI包entry-points加载适配器

        :return: 
            Dict[str, object]: 适配器对象字典 {适配器名: 模块对象}
            List[str]: 启用的适配器名称列表
            List[str]: 停用的适配器名称列表
            
        :raises ImportError: 当无法加载适配器时抛出
        """
        adapter_objs = {}
        enabled_adapters = []
        disabled_adapters = []
        
        try:
            # 加载适配器entry-points
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                adapter_entries = entry_points.select(group='erispulse.adapter')
            else:
                adapter_entries = entry_points.get('erispulse.adapter', [])
            
            # 处理适配器
            for entry_point in adapter_entries:
                adapter_objs, enabled_adapters, disabled_adapters = AdapterLoader._process_adapter(
                    entry_point, adapter_objs, enabled_adapters, disabled_adapters)
                    
        except Exception as e:
            logger.error(f"加载适配器entry-points失败: {e}")
            raise ImportError(f"无法加载适配器: {e}")
            
        return adapter_objs, enabled_adapters, disabled_adapters
    
    @staticmethod
    def _process_adapter(
        entry_point: Any,
        adapter_objs: Dict[str, object],
        enabled_adapters: List[str],
        disabled_adapters: List[str]
    ) -> Tuple[Dict[str, object], List[str], List[str]]:
        """
        {!--< internal-use >!--}
        处理单个适配器entry-point
        
        :param entry_point: entry-point对象
        :param adapter_objs: 适配器对象字典
        :param enabled_adapters: 启用的适配器列表
        :param disabled_adapters: 停用的适配器列表
        
        :return: 
            Dict[str, object]: 更新后的适配器对象字典
            List[str]: 更新后的启用适配器列表 
            List[str]: 更新后的禁用适配器列表
            
        :raises ImportError: 当适配器加载失败时抛出
        """
        try:
            loaded_obj = entry_point.load()
            adapter_obj = sys.modules[loaded_obj.__module__]
            dist = importlib.metadata.distribution(entry_point.dist.name)
            
            # 从pyproject.toml读取依赖配置
            requires, optional, pip_deps = AdapterLoader._read_dependencies(dist)
            
            # 自动推断依赖
            auto_requires = AdapterLoader._infer_dependencies(dist)
            
            # 合并显式和自动推断的依赖
            all_requires = list(set(requires + list(auto_requires)))
            
            # 创建adapterInfo
            adapter_info = {
                "meta": {
                    "name": entry_point.name,
                    "version": getattr(adapter_obj, "__version__", dist.version if dist else "1.0.0"),
                    "description": getattr(adapter_obj, "__description__", ""),
                    "author": getattr(adapter_obj, "__author__", ""),
                    "license": getattr(adapter_obj, "__license__", ""),
                    "package": entry_point.dist.name
                },
                "dependencies": {
                    "requires": all_requires,
                    "optional": optional,
                    "pip": pip_deps
                },
                "adapter_class": loaded_obj
            }
            
            # 检查是否已经加载过这个适配器类
            existing_instance = None
            for existing_adapter in adapter_objs.values():
                if hasattr(existing_adapter, 'adapterInfo'):
                    for existing_adapter_info in existing_adapter.adapterInfo.values():
                        if isinstance(existing_adapter_info, dict) and existing_adapter_info["adapter_class"] == loaded_obj:
                            existing_instance = existing_adapter_info["adapter_class"]
                            break
            
            # 如果已经存在实例，则复用
            if existing_instance is not None:
                adapter_info["adapter_class"] = existing_instance
            
            if not hasattr(adapter_obj, 'adapterInfo'):
                adapter_obj.adapterInfo = {}
                
            adapter_obj.adapterInfo[entry_point.name] = adapter_info
            
            # 检查适配器状态
            meta_name = entry_point.name
            stored_info = mods.get_module(meta_name) or {
                "status": True,
                "info": adapter_info
            }
            mods.set_module(meta_name, stored_info)
            
            if not stored_info.get('status', True):
                disabled_adapters.append(meta_name)
                logger.warning(f"适配器 {meta_name} 已禁用，跳过加载")
                return adapter_objs, enabled_adapters, disabled_adapters
                
            adapter_objs[meta_name] = adapter_obj
            enabled_adapters.append(meta_name)
            logger.debug(f"从PyPI包加载适配器: {meta_name}")
            
        except Exception as e:
            logger.warning(f"从entry-point加载适配器 {entry_point.name} 失败: {e}")
            raise ImportError(f"无法加载适配器 {entry_point.name}: {e}")
            
        return adapter_objs, enabled_adapters, disabled_adapters
    
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
            
        :raises toml.TomlDecodeError: 当toml解析失败时抛出
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
                    raise toml.TomlDecodeError(f"无法解析pyproject.toml: {e}")
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


class ModuleLoader:
    """
    模块加载器
    
    专门用于从PyPI包加载和初始化普通模块

    {!--< tips >!--}
    1. 模块必须通过entry-points机制注册到erispulse.module组
    2. 模块类名应与entry-point名称一致
    {!--< /tips >!--}
    """
    
    @staticmethod
    def load() -> Tuple[Dict[str, object], List[str], List[str]]:
        """
        从PyPI包entry-points加载模块

        :return: 
            Dict[str, object]: 模块对象字典 {模块名: 模块对象}
            List[str]: 启用的模块名称列表
            List[str]: 停用的模块名称列表
            
        :raises ImportError: 当无法加载模块时抛出
        """
        module_objs = {}
        enabled_modules = []
        disabled_modules = []
        
        try:
            # 加载模块entry-points
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                module_entries = entry_points.select(group='erispulse.module')
            else:
                module_entries = entry_points.get('erispulse.module', [])
            
            # 处理模块
            for entry_point in module_entries:
                module_objs, enabled_modules, disabled_modules = ModuleLoader._process_module(
                    entry_point, module_objs, enabled_modules, disabled_modules)
                    
        except Exception as e:
            logger.error(f"加载模块entry-points失败: {e}")
            raise ImportError(f"无法加载模块: {e}")
            
        return module_objs, enabled_modules, disabled_modules
    
    @staticmethod
    def _process_module(
        entry_point: Any,
        module_objs: Dict[str, object],
        enabled_modules: List[str],
        disabled_modules: List[str]
    ) -> Tuple[Dict[str, object], List[str], List[str]]:
        """
        {!--< internal-use >!--}
        处理单个模块entry-point
        
        :param entry_point: entry-point对象
        :param module_objs: 模块对象字典
        :param enabled_modules: 启用的模块列表
        :param disabled_modules: 停用的模块列表
        
        :return: 
            Dict[str, object]: 更新后的模块对象字典
            List[str]: 更新后的启用模块列表 
            List[str]: 更新后的禁用模块列表
            
        :raises ImportError: 当模块加载失败时抛出
        """
        try:
            loaded_obj = entry_point.load()
            module_obj = sys.modules[loaded_obj.__module__]
            dist = importlib.metadata.distribution(entry_point.dist.name)
            
            # 从pyproject.toml读取依赖配置
            requires, optional, pip_deps = ModuleLoader._read_dependencies(dist)
            
            # 自动推断依赖
            auto_requires = ModuleLoader._infer_dependencies(dist)
            
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
                logger.warning(f"模块 {meta_name} 已禁用，跳过加载")
                return module_objs, enabled_modules, disabled_modules
                
            module_objs[meta_name] = module_obj
            enabled_modules.append(meta_name)
            logger.debug(f"从PyPI包加载模块: {meta_name}")
            
        except Exception as e:
            logger.warning(f"从entry-point加载模块 {entry_point.name} 失败: {e}")
            raise ImportError(f"无法加载模块 {entry_point.name}: {e}")
            
        return module_objs, enabled_modules, disabled_modules
    
    @staticmethod
    def _read_dependencies(dist: Any) -> Tuple[List[str], List[str], List[str]]:
        """同AdapterLoader._read_dependencies"""
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
                    raise toml.TomlDecodeError(f"无法解析pyproject.toml: {e}")
        return requires, optional, pip_deps
    
    @staticmethod
    def _infer_dependencies(dist: Any) -> Set[str]:
        """同AdapterLoader._infer_dependencies"""
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


class ModuleInitializer:
    """
    模块初始化器

    负责协调适配器和模块的初始化流程

    {!--< tips >!--}
    1. 初始化顺序：适配器 → 模块
    2. 模块初始化前会先解析依赖关系
    {!--< /tips >!--}
    """
    
    @staticmethod
    def init() -> bool:
        """
        初始化所有模块和适配器
        
        执行步骤:
        1. 从PyPI包加载适配器
        2. 从PyPI包加载模块
        3. 解析模块依赖关系并进行拓扑排序
        4. 注册适配器
        5. 初始化各模块
        
        :return: bool: 初始化是否成功
        
        :raises InitError: 当初始化失败时抛出
        """
        logger.info("[Init] SDK 正在初始化...")
        
        try:
            # 1. 先加载适配器
            adapter_objs, enabled_adapters, disabled_adapters = AdapterLoader.load()
            logger.info(f"[Init] 加载了 {len(enabled_adapters)} 个适配器, {len(disabled_adapters)} 个适配器被禁用")
            
            # 2. 再加载模块
            module_objs, enabled_modules, disabled_modules = ModuleLoader.load()
            logger.info(f"[Init] 加载了 {len(enabled_modules)} 个模块, {len(disabled_modules)} 个模块被禁用")
            
            if os.path.join(os.path.dirname(__file__), "modules"):
                logger.warning("[Warning] 你的项目使用了已经弃用的模块加载方式, 请尽快使用 PyPI 模块加载方式代替")
            
            if not enabled_modules and not enabled_adapters:
                logger.warning("[Init] 没有找到可用的模块和适配器")
                return True
            
            # 3. 解析依赖关系
            logger.debug(f"[Init] 开始解析 {len(enabled_modules)} 个模块的依赖关系...")
            sorted_modules = ModuleInitializer._resolve_dependencies(enabled_modules, module_objs)
            logger.info(f"[Init] 模块加载顺序(拓扑排序): {', '.join(sorted_modules)}")
            
            # 4. 注册适配器
            logger.debug("[Init] 正在注册适配器...")
            if not ModuleInitializer._register_adapters(enabled_adapters, adapter_objs):
                return False
            
            # 5. 初始化模块
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
        
        :raises CycleDependencyError: 当检测到循环依赖时抛出
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
    def _register_adapters(adapters: List[str], adapter_objs: Dict[str, Any]) -> bool:
        """
        {!--< internal-use >!--}
        注册适配器
        
        :param adapters: 适配器名称列表
        :param adapter_objs: 适配器对象字典
        
        :return: bool: 适配器注册是否成功
        """
        success = True
        # 存储平台名到适配器类的映射
        platform_to_adapter = {}
        # 存储已注册的适配器类到实例的映射
        registered_classes = {}

        for adapter_name in adapters:
            adapter_obj = adapter_objs[adapter_name]
            
            try:
                if hasattr(adapter_obj, "adapterInfo") and isinstance(adapter_obj.adapterInfo, dict):
                    for platform, adapter_info in adapter_obj.adapterInfo.items():
                        # 如果这个平台已经注册过，跳过
                        if platform in platform_to_adapter:
                            continue
                            
                        adapter_class = adapter_info["adapter_class"]
                        
                        # 检查是否已经注册过这个适配器类
                        if adapter_class in registered_classes:
                            # 获取已注册的实例
                            existing_instance = registered_classes[adapter_class]
                            # 将新平台名指向已有实例
                            sdk.adapter._adapters[platform] = existing_instance
                            sdk.adapter._platform_to_instance[platform] = existing_instance
                        else:
                            # 注册新适配器
                            sdk.adapter.register(platform, adapter_class)
                            # 记录已注册的类和实例
                            registered_classes[adapter_class] = sdk.adapter._adapters[platform]
                        
                        # 记录平台到适配器的映射
                        platform_to_adapter[platform] = adapter_class
                        logger.info(f"注册适配器: {platform}")
            except Exception as e:
                logger.error(f"适配器 {adapter_name} 注册失败: {e}")
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
                    # 获取entry point中指定的类对象
                    module_class = getattr(module_obj, meta_name)
                    
                    # 获取类的__init__参数信息
                    init_signature = inspect.signature(module_class.__init__)
                    params = init_signature.parameters
                    
                    # 根据参数决定是否传入sdk
                    if 'sdk' in params:
                        module_instance = module_class(sdk)
                    else:
                        module_instance = module_class()
                    
                    setattr(module_instance, "moduleInfo", module_obj.moduleInfo)
                    setattr(sdk, meta_name, module_instance)
                    logger.debug(f"模块 {meta_name} 初始化完成")
            except Exception as e:
                logger.error(f"模块 {meta_name} 初始化失败: {e}")
                success = False
        return success


def init_progress() -> bool:
    """
    初始化项目环境文件
    
    1. 检查并创建main.py入口文件
    2. 确保基础目录结构存在

    :return: bool: 是否创建了新的main.py文件
    
    {!--< tips >!--}
    1. 如果main.py已存在则不会覆盖
    2. 此方法通常由SDK内部调用
    {!--< /tips >!--}
    """
    main_file = Path("main.py")
    main_init = False
    
    try:
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
            
        return main_init
    except Exception as e:
        sdk.logger.error(f"无法初始化项目环境: {e}")
        return False


def _prepare_environment() -> bool:
    """
    {!--< internal-use >!--}
    准备运行环境
    
    1. 初始化项目环境文件
    2. 加载环境变量配置

    :return: bool: 环境准备是否成功
    """
    logger.info("[Init] 准备初始化环境...")
    try:
        main_init = init_progress()
        if main_init:
            logger.info("[Init] 项目入口已生成, 你可以在 main.py 中编写一些代码")
        env.load_env_file()
        return True
    except Exception as e:
        logger.error(f"环境准备失败: {e}")
        return False


def init() -> bool:
    """
    SDK初始化入口
    
    执行步骤:
    1. 准备运行环境
    2. 初始化所有模块和适配器

    :return: bool: SDK初始化是否成功
    
    {!--< tips >!--}
    1. 这是SDK的主要入口函数
    2. 如果初始化失败会抛出InitError异常
    3. 建议在main.py中调用此函数
    {!--< /tips >!--}
    
    :raises InitError: 当初始化失败时抛出
    """
    if not _prepare_environment():
        return False
    return ModuleInitializer.init()


sdk.init = init
