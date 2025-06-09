
import types
sdk = types.SimpleNamespace()
import os
import sys
from . import util
from .raiserr import raiserr
from .logger import logger
from .db import env
from .mods import mods
from .adapter import adapter, BaseAdapter, SendDSL

# 这里不能删，确保windows下的shell能正确显示颜色
os.system('')

setattr(sdk, "env", env)
setattr(sdk, "mods", mods)
setattr(sdk, "util", util)
setattr(sdk, "raiserr", raiserr)
setattr(sdk, "logger", logger)
setattr(sdk, "adapter", adapter)
setattr(sdk, "SendDSL", SendDSL)
setattr(sdk, "BaseAdapter", BaseAdapter)

env.load_env_file()

# 注册 ErrorHook 并预注册常用错误类型
raiserr.register("CaughtExternalError"      , doc="捕获的非SDK抛出的异常")
raiserr.register("InitError"               , doc="SDK初始化错误")
raiserr.register("MissingDependencyError"   , doc="缺少依赖错误")
raiserr.register("InvalidDependencyError"   , doc="依赖无效错误")
raiserr.register("CycleDependencyError"     , doc="依赖循环错误")
raiserr.register("ModuleLoadError"          , doc="模块加载错误")

def init():
    try:
        sdkModulePath = os.path.join(os.path.dirname(__file__), "modules")

        if not os.path.exists(sdkModulePath):
            os.makedirs(sdkModulePath)

        sys.path.append(sdkModulePath)

        TempModules = [
            x for x in os.listdir(sdkModulePath)
            if os.path.isdir(os.path.join(sdkModulePath, x))
        ]

        sdkInstalledModuleNames: list[str] = []
        disabledModules: list[str] = []

        # ==== 扫描模块并收集基本信息 ====
        module_objs = {}  # {module_name: moduleObj}
        for module_name in TempModules:
            try:
                moduleObj = __import__(module_name)
                if not hasattr(moduleObj, "moduleInfo") or not isinstance(moduleObj.moduleInfo, dict):
                    logger.warning(f"模块 {module_name} 缺少有效的 'moduleInfo' 字典.")
                    continue
                if "name" not in moduleObj.moduleInfo.get("meta", {}):
                    logger.warning(f"模块 {module_name} 的 'moduleInfo' 字典 缺少必要 'name' 键.")
                    continue
                if not hasattr(moduleObj, "Main"):
                    logger.warning(f"模块 {module_name} 缺少 'Main' 类.")
                    continue

                meta_name = moduleObj.moduleInfo["meta"]["name"]
                module_info = mods.get_module(meta_name)
                if module_info is None:
                    module_info = {
                        "status": True,
                        "info": moduleObj.moduleInfo
                    }
                    mods.set_module(meta_name, module_info)
                    logger.info(f"模块 {meta_name} 信息已初始化并存储到数据库")

                if not module_info.get('status', True):
                    disabledModules.append(module_name)
                    logger.warning(f"模块 {meta_name} 已禁用，跳过加载")
                    continue

                required_deps = moduleObj.moduleInfo.get("dependencies", {}).get("requires", [])
                missing_required_deps = [dep for dep in required_deps if dep not in TempModules]
                if missing_required_deps:
                    logger.error(f"模块 {module_name} 缺少必需依赖: {missing_required_deps}")
                    raiserr.MissingDependencyError(f"模块 {module_name} 缺少必需依赖: {missing_required_deps}")

                optional_deps = moduleObj.moduleInfo.get("dependencies", {}).get("optional", [])
                available_optional_deps = []
                for dep in optional_deps:
                    if isinstance(dep, list):
                        available_deps = [d for d in dep if d in TempModules]
                        if available_deps:
                            available_optional_deps.extend(available_deps)
                    elif dep in TempModules:
                        available_optional_deps.append(dep)

                if optional_deps and not available_optional_deps:
                    logger.warning(f"模块 {module_name} 缺少所有可选依赖: {optional_deps}")

                module_objs[module_name] = moduleObj
                sdkInstalledModuleNames.append(module_name)

            except Exception as e:
                logger.warning(f"模块 {module_name} 加载失败: {e}")
                continue

        # ==== 构建依赖图并进行拓扑排序 ====
        sdkModuleDependencies = {}
        for module_name in sdkInstalledModuleNames:
            moduleObj = module_objs[module_name]
            meta_name = moduleObj.moduleInfo["meta"]["name"]

            req_deps = moduleObj.moduleInfo.get("dependencies", {}).get("requires", [])
            opt_deps = moduleObj.moduleInfo.get("dependencies", {}).get("optional", [])

            available_optional_deps = [dep for dep in opt_deps if dep in sdkInstalledModuleNames]
            deps = req_deps + available_optional_deps

            for dep in deps:
                if dep in disabledModules:
                    logger.warning(f"模块 {meta_name} 的依赖模块 {dep} 已禁用，跳过加载")
                    continue

            if not all(dep in sdkInstalledModuleNames for dep in deps):
                raiserr.InvalidDependencyError(f"模块 {meta_name} 的依赖无效: {deps}")
            sdkModuleDependencies[module_name] = deps

        sdkInstalledModuleNames: list[str] = sdk.util.topological_sort(
            sdkInstalledModuleNames, sdkModuleDependencies, raiserr.CycleDependencyError
        )

        # ==== 注册适配器 ====
        logger.debug("[Init] 开始注册适配器...")
        for module_name in sdkInstalledModuleNames:
            moduleObj = module_objs[module_name]
            meta_name = moduleObj.moduleInfo["meta"]["name"]

            try:
                if hasattr(moduleObj, "adapterInfo") and isinstance(moduleObj.adapterInfo, dict):
                    for platform_name, adapter_class in moduleObj.adapterInfo.items():
                        sdk.adapter.register(platform_name, adapter_class)
                        logger.info(f"模块 {meta_name} 注册了适配器: {platform_name}")
            except Exception as e:
                logger.error(f"模块 {meta_name} 注册适配器失败: {e}")

        # ==== 存储模块信息到数据库 ====
        all_modules_info = {}
        for module_name in sdkInstalledModuleNames:
            moduleObj = module_objs[module_name]
            moduleInfo: dict = moduleObj.moduleInfo

            meta_name = moduleInfo.get("meta", {}).get("name", None)
            module_info = mods.get_module(meta_name)
            mods.set_module(meta_name, {
                "status": True,
                "info": moduleInfo
            })
        logger.debug("所有模块信息已加载并存储到数据库")

        # ==== 实例化 Main 类并挂载到 sdk ====
        logger.debug("[Init] 开始实例化模块 Main 类...")
        for module_name in sdkInstalledModuleNames:
            moduleObj = module_objs[module_name]
            meta_name = moduleObj.moduleInfo["meta"]["name"]

            module_status = mods.get_module_status(meta_name)
            if not module_status:
                continue

            moduleMain = moduleObj.Main(sdk)
            setattr(moduleMain, "moduleInfo", moduleObj.moduleInfo)
            setattr(sdk, meta_name, moduleMain)
            logger.debug(f"模块 {meta_name} 正在初始化")

    except Exception as e:
        raiserr.InitError(f"sdk初始化失败: {e}", exit=True)


sdk.init = init
