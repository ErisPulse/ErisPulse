"""
# SDK 核心初始化

提供SDK全局对象构建和初始化功能。

## 主要功能
- 构建全局sdk对象
- 预注册核心错误类型
- 提供SDK初始化入口
- 集成各核心模块
- 支持项目内模块加载（优先于SDK模块）

## 模块加载机制
- **SDK 内置模块**：位于 `src/ErisPulse/modules/`，会被写入数据库并支持状态管理。
- **项目自定义模块**：位于项目根目录下的 `modules/`，仅运行时加载，不会写入数据库。
- **冲突处理**：若同一模块存在于多个路径，选择权重更高的路径（项目模块 > SDK 模块）。

## API 文档
### 核心对象：
    - sdk: 全局SDK命名空间对象
    - sdk.init(): SDK初始化入口函数

### 预注册错误类型：
    - CaughtExternalError: 外部捕获异常
    - InitError: 初始化错误
    - MissingDependencyError: 缺少依赖错误  
    - InvalidDependencyError: 依赖无效错误
    - CycleDependencyError: 循环依赖错误
    - ModuleLoadError: 模块加载错误

### 示例用法：

```python
from ErisPulse import sdk

# 初始化SDK
sdk.init()

# 访问各模块功能
sdk.logger.info("SDK已初始化")
```

"""

import os
import sys
import logging
from types import SimpleNamespace

# 初始化全局 sdk 对象
sdk = SimpleNamespace()

# 导入内部依赖
from . import util
from .raiserr import raiserr
from .logger import logger
from .db import env
from .mods import mods
from .adapter import adapter, BaseAdapter, SendDSL

# Windows 下启用 ANSI 颜色输出
os.system('')

# 挂载基础组件
for name in ['env', 'mods', 'util', 'raiserr', 'logger', 'adapter', 'SendDSL', 'BaseAdapter']:
    setattr(sdk, name, eval(name))

# 注册错误类型
raiserr.register("CaughtExternalError", doc="捕获的非SDK抛出的异常")
raiserr.register("InitError", doc="SDK初始化错误")
raiserr.register("MissingDependencyError", doc="缺少依赖错误")
raiserr.register("InvalidDependencyError", doc="依赖无效错误")
raiserr.register("CycleDependencyError", doc="循环依赖错误")
raiserr.register("ModuleLoadError", doc="模块加载错误")

def init() -> None:
    try:
        logger.info("[Init] SDK 正在初始化...")

        if env.create_env_file_if_not_exists():
            logger.info("[Init] 项目首次初始化，建议先配置环境变量")
            if input("是否立即退出？(y/n): ").strip().lower() == "y":
                sys.exit(0)
        env.load_env_file()

        # 定义模块路径
        projectModulePath = os.path.join(os.getcwd(), "modules")  # 项目模块
        sdkModulePath = os.path.join(os.path.dirname(__file__), "modules")  # SDK 模块

        # 构建模块路径字典（权重控制）
        modulePaths = {
            projectModulePath: 100,  # 项目模块优先级更高
            sdkModulePath: 50        # SDK 内置模块次之
        }

        # 存储模块名到路径的映射
        moduleSourceMap = {}  # {module_name: [(path, weight), ...]}

        # 扫描模块并记录来源路径和权重
        for modulePath, weight in modulePaths.items():
            if os.path.exists(modulePath) and os.path.isdir(modulePath):
                modules = [
                    x for x in os.listdir(modulePath)
                    if os.path.isdir(os.path.join(modulePath, x))
                ]
                for module in modules:
                    if module not in moduleSourceMap:
                        moduleSourceMap[module] = []
                    moduleSourceMap[module].append((modulePath, weight))

        # 处理模块冲突（按权重选择）
        TempModules = []

        for module, sources in moduleSourceMap.items():
            if len(sources) > 1:
                # 按权重排序
                sources.sort(key=lambda x: x[1], reverse=True)

                selected_path = sources[0][0]
                logger.warning(f"模块 {module} 在多个路径存在，选择权重更高的: {selected_path}")

                # 确保选中的路径在 sys.path 最前面
                if selected_path in sys.path:
                    sys.path.remove(selected_path)
                sys.path.insert(0, selected_path)

            TempModules.append(module)

        # 动态导入模块（不存入数据库）
        module_objs = {}

        for module_name in TempModules:
            try:
                moduleObj = __import__(module_name)

                # 验证必要属性
                if not hasattr(moduleObj, "moduleInfo") or not isinstance(moduleObj.moduleInfo, dict):
                    logger.warning(f"模块 {module_name} 缺少有效的 'moduleInfo' 字典.")
                    continue
                if "name" not in moduleObj.moduleInfo.get("meta", {}):
                    logger.warning(f"模块 {module_name} 的 'moduleInfo' 缺少必要 'name' 键.")
                    continue
                if not hasattr(moduleObj, "Main"):
                    logger.warning(f"模块 {module_name} 缺少 'Main' 类.")
                    continue

                meta_name = moduleObj.moduleInfo["meta"]["name"]
                module_status = mods.get_module_status(meta_name)

                if not module_status:
                    logger.warning(f"模块 {meta_name} 已禁用，跳过加载")
                    continue

                required_deps = moduleObj.moduleInfo.get("dependencies", {}).get("requires", [])
                missing_required_deps = []

                for dep in required_deps:
                    dep_name, operator, version = util.parse_dependency_with_version(dep)

                    if dep_name not in TempModules:
                        missing_required_deps.append(dep)
                        continue

                    if operator and version:
                        try:
                            dep_module = __import__(dep_name)
                            if not hasattr(dep_module, "moduleInfo"):
                                missing_required_deps.append(dep)
                                continue

                            dep_version = dep_module.moduleInfo.get("meta", {}).get("version", "0.0.0")
                            if not util.check_version_requirement(dep_version, operator, version):
                                logger.error(
                                    f"模块 {module_name} 的依赖 {dep_name} 版本不匹配: 需要 {operator}{version}, 实际为 {dep_version}")
                                missing_required_deps.append(dep)
                        except Exception as e:
                            logger.error(f"检查模块 {dep_name} 版本时出错: {e}")
                            missing_required_deps.append(dep)

                if missing_required_deps:
                    logger.error(
                        f"模块 {module_name} 缺少必需依赖或版本不匹配: {missing_required_deps}")
                    raiserr.MissingDependencyError(
                        f"模块 {module_name} 缺少必需依赖或版本不匹配: {missing_required_deps}")

                optional_deps = moduleObj.moduleInfo.get("dependencies", {}).get("optional", [])
                available_optional_deps = []

                for dep in optional_deps:
                    d_name, operator, version = util.parse_dependency_with_version(dep)

                    if d_name not in TempModules:
                        continue

                    if operator and version:
                        try:
                            d_module = __import__(d_name)
                            if not hasattr(d_module, "moduleInfo"):
                                continue

                            d_version = d_module.moduleInfo.get("meta", {}).get("version", "0.0.0")
                            if not util.check_version_requirement(d_version, operator, version):
                                logger.warning(
                                    f"模块 {module_name} 的可选依赖 {d_name} 版本不匹配: 需要 {operator}{version}, 实际为 {d_version}")
                                continue
                        except Exception as e:
                            logger.warning(f"检查模块 {d_name} 版本时出错: {e}")
                            continue

                    available_optional_deps.append(d_name)

                if optional_deps and not available_optional_deps:
                    logger.warning(f"模块 {module_name} 缺少所有可选依赖: {optional_deps}")

                module_objs[module_name] = moduleObj

            except Exception as e:
                logger.warning(f"模块 {module_name} 加载失败: {e}")
                continue

        # ==== 创建 README 提示用户模块目录用途 ====
        readme_content = """# 项目模块目录

此目录 (`./modules`) 用于存放项目专属模块。这些模块会优先于 SDK 内置模块被加载，但不会写入数据库。

你可以将自定义模块放入此目录，SDK 会自动识别并加载它们。
"""

        if not os.path.exists(projectModulePath):
            os.makedirs(projectModulePath)

        readme_path = os.path.join(projectModulePath, "README.md")
        if not os.path.exists(readme_path):
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            logger.info(f"您的项目模块目录已创建 | 请查看 {readme_path} 了解如何使用")

        # ==== 实例化 Main 类并挂载到 sdk ====
        logger.debug("[Init] 开始实例化模块 Main 类...")

        for module_name in module_objs:
            moduleObj = module_objs[module_name]
            meta_name = moduleObj.moduleInfo["meta"]["name"]

            # 获取模块路径来源
            source_path = None
            for path, _ in moduleSourceMap.get(module_name, []):
                if module_name in os.listdir(path) and os.path.isdir(os.path.join(path, module_name)):
                    source_path = path
                    break
            
            # 判断是否是 SDK 模块（来自 sdkModulePath）
            is_sdk_module = source_path == sdkModulePath

            # 如果是 SDK 模块，检查是否已注册到数据库
            if is_sdk_module:
                module_info = mods.get_module(meta_name)
                if module_info is None:
                    # 首次加载，写入数据库
                    mods.set_module(meta_name, {
                        "status": True,
                        "info": moduleObj.moduleInfo
                    })
                    logger.info(f"模块 {meta_name} 信息已初始化并存储到数据库")
                else:
                    logger.debug(f"模块 {meta_name} 已存在于数据库中")

            # 实例化模块
            moduleMain = moduleObj.Main(sdk)
            setattr(moduleMain, "moduleInfo", moduleObj.moduleInfo)
            setattr(sdk, meta_name, moduleMain)
            logger.debug(f"模块 {meta_name} 正在初始化")

    except Exception as e:
        raiserr.InitError(f"sdk初始化失败: {e}", exit=True)

sdk.init = init