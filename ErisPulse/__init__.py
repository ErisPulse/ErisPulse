import os
import sys
import types
from . import util
from .raiserr import raiserr
from .logger import logger
from .db import env
from .mods import mods

# 注册 ErrorHook 并预注册常用错误类型
raiserr.register("MissingDependencyError", doc="缺少依赖错误")
raiserr.register("InvalidDependencyError", doc="依赖无效错误")
raiserr.register("CycleDependencyError"  , doc="依赖循环错误")
raiserr.register("ModuleLoadError"       , doc="模块加载错误")

sdk = types.SimpleNamespace()
setattr(sdk, "env", env)
setattr(sdk, "mods", mods)
setattr(sdk, "raiserr", raiserr)
setattr(sdk, "logger", logger)
setattr(sdk, "util", util)

env.load_env_file()

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
                
                module_info = mods.get_module(moduleObj.moduleInfo.get("meta", {}).get("name", None))
                if module_info is None:
                    module_info = {
                        "status": True,
                        "info": moduleObj.moduleInfo
                    }
                    mods.set_module(moduleObj.moduleInfo.get("meta", {}).get("name", None), module_info)
                    logger.info(f"模块 {moduleObj.moduleInfo.get('meta', {}).get('name', None)} 信息已初始化并存储到数据库")
                
                if not module_info.get('status', True):
                    disabledModules.append(module_name)
                    logger.warning(f"模块 {moduleObj.moduleInfo.get('meta', {}).get('name', None)} 已禁用，跳过加载")
                    continue
                    
                required_deps = moduleObj.moduleInfo.get("dependencies", []).get("requires", [])
                missing_required_deps = [dep for dep in required_deps if dep not in TempModules]
                if missing_required_deps:
                    logger.error(f"模块 {module_name} 缺少必需依赖: {missing_required_deps}")
                    raiserr.MissingDependencyError(f"模块 {module_name} 缺少必需依赖: {missing_required_deps}")

                # 检查可选依赖部分
                optional_deps = moduleObj.moduleInfo.get("dependencies", []).get("optional", [])
                if optional_deps:
                    available_optional_deps = []
                    for dep in optional_deps:
                        if isinstance(dep, list):
                            available_deps = [d for d in dep if d in TempModules]
                            if available_deps:
                                available_optional_deps.extend(available_deps)
                        elif dep in TempModules:
                            available_optional_deps.append(dep)

                    if available_optional_deps:
                        logger.info(f"模块 {module_name} 加载了部分可选依赖: {available_optional_deps}")
                    else:
                        logger.warning(f"模块 {module_name} 缺少所有可选依赖: {optional_deps}")

                sdkInstalledModuleNames.append(module_name)
            except Exception as e:
                logger.warning(f"模块 {module_name} 加载失败: {e}")
                continue

        sdkModuleDependencies = {}
        for module_name in sdkInstalledModuleNames:
            moduleObj = __import__(module_name)
            moduleDependecies: list[str] = moduleObj.moduleInfo.get("dependencies", []).get("requires", [])

            optional_deps = moduleObj.moduleInfo.get("dependencies", []).get("optional", [])
            available_optional_deps = [dep for dep in optional_deps if dep in sdkInstalledModuleNames]
            moduleDependecies.extend(available_optional_deps)

            for dep in moduleDependecies:
                if dep in disabledModules:
                    logger.warning(f"模块 {module_name} 的依赖模块 {dep} 已禁用，跳过加载")
                    continue
            
            if not all(dep in sdkInstalledModuleNames for dep in moduleDependecies):
                raiserr.InvalidDependencyError(
                    f"模块 {module_name} 的依赖无效: {moduleDependecies}"
                )
            sdkModuleDependencies[module_name] = moduleDependecies

        sdkInstalledModuleNames: list[str] = sdk.util.topological_sort(
            sdkInstalledModuleNames, sdkModuleDependencies, raiserr.CycleDependencyError
        )

        all_modules_info = {}
        for module_name in sdkInstalledModuleNames:
            moduleObj = __import__(module_name)
            moduleInfo: dict = moduleObj.moduleInfo

            module_info = mods.get_module(moduleInfo.get("meta", {}).get("name", None))
            mods.set_module(moduleInfo.get("meta", {}).get("name", None), {
                "status": True,
                "info": moduleInfo
            })
        logger.debug("所有模块信息已加载并存储到数据库")

        for module_name in sdkInstalledModuleNames:
            moduleObj = __import__(module_name)
            moduleInfo = moduleObj.moduleInfo
            module_status = mods.get_module_status(moduleInfo.get("meta", {}).get("name", None))
            if not module_status:
                continue
            
            moduleMain = moduleObj.Main(sdk)
            setattr(moduleMain, "moduleInfo", moduleInfo)
            setattr(sdk, moduleInfo.get("meta", {}).get("name", None), moduleMain)
            logger.debug(f"模块 {moduleInfo.get('meta', {}).get('name', None)} 正在初始化")
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise e

sdk.init = init