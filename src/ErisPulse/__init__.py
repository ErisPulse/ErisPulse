"""
ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

{!--< tips >!--}
1. 使用前请确保已正确安装所有依赖
2. 调用sdk.init()进行初始化
3. 模块加载采用懒加载机制
{!--< /tips >!--}
"""

__version__ = "2.1.13rc3"
__author__  = "ErisPulse"

import os
import sys
import importlib
import inspect
import importlib.metadata
from typing import Dict, List, Tuple, Type, Any
from pathlib import Path

# BaseModules: SDK核心模块
from .Core import util
from .Core import raiserr
from .Core import logger
from .Core import env
from .Core import mods
from .Core import adapter, AdapterFather, SendDSL
from .Core import adapter_server

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

for module, moduleObj in BaseModules.items():
    setattr(sdk, module, moduleObj)

class LazyModule:
    """
    懒加载模块包装器
    
    当模块第一次被访问时才进行实例化
    
    {!--< tips >!--}
    1. 模块的实际实例化会在第一次属性访问时进行
    2. 依赖模块会在被使用时自动初始化
    {!--< /tips >!--}
    """
    
    def __init__(self, module_name: str, module_class: Type, sdk_ref: Any, module_info: Dict[str, Any]) -> None:
        """
        初始化懒加载包装器
        
        :param module_name: str 模块名称
        :param module_class: Type 模块类
        :param sdk_ref: Any SDK引用
        :param module_info: Dict[str, Any] 模块信息字典
        """
        self._module_name = module_name
        self._module_class = module_class
        self._sdk_ref = sdk_ref
        self._module_info = module_info
        self._instance = None
        self._initialized = False
    
    def _initialize(self):
        """
        实际初始化模块
        
        :raises LazyLoadError: 当模块初始化失败时抛出
        """
        try:
            # 获取类的__init__参数信息
            init_signature = inspect.signature(self._module_class.__init__)
            params = init_signature.parameters
            
            # 根据参数决定是否传入sdk
            if 'sdk' in params:
                self._instance = self._module_class(self._sdk_ref)
            else:
                self._instance = self._module_class()
            
            setattr(self._instance, "moduleInfo", self._module_info)
            self._initialized = True
            logger.debug(f"模块 {self._module_name} 初始化完成")
        except Exception as e:
            logger.error(f"模块 {self._module_name} 初始化失败: {e}")
            raise 
    
    def __getattr__(self, name: str) -> Any:
        """
        属性访问时触发初始化
        
        :param name: str 要访问的属性名
        :return: Any 模块属性值
        """
        if not self._initialized:
            self._initialize()
        return getattr(self._instance, name)
    
    def __call__(self, *args, **kwargs) -> Any:
        """
        调用时触发初始化
        
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: Any 模块调用结果
        """
        if not self._initialized:
            self._initialize()
        return self._instance(*args, **kwargs)
    
    def __bool__(self) -> bool:
        """
        判断模块布尔值时触发初始化

        :return: bool 模块布尔值
        """
        if not self._initialized:
            self._initialize()
        return bool(self._instance)
    
    def __str__(self) -> str:
        """
        转换为字符串时触发初始化
        
        :return: str 模块字符串表示
        """
        if not self._initialized:
            self._initialize()
            return str(self._instance)
        return str(self._instance)
    
    # 确保模块在被赋值给变量后仍然能正确工作
    def __getattribute__(self, name: str) -> Any:
        try:
            # 首先尝试获取常规属性
            return super().__getattribute__(name)
        except AttributeError:
            # 如果常规属性不存在，触发初始化
            if name != '_initialized' and not self._initialized:
                self._initialize()
                return getattr(self._instance, name)
            raise
        
    def __copy__(self):
        """
        浅拷贝时返回自身，保持懒加载特性

        :return: self
        """
        return self

    def __deepcopy__(self, memo):
        """
        深拷贝时返回自身，保持懒加载特性

        :param memo: memo
        :return: self
        """
        return self


class AdapterLoader:
    """
    适配器加载器
    
    专门用于从PyPI包加载和初始化适配器

    {!--< tips >!--}
    1. 适配器必须通过entry-points机制注册到erispulse.adapter组
    2. 适配器类必须继承BaseAdapter
    3. 适配器不适用懒加载
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
        meta_name = entry_point.name
        adapter_status = mods.get_module_status(meta_name)
        logger.debug(f"适配器 {meta_name} 状态: {adapter_status}")
        
        if adapter_status is False:
            disabled_adapters.append(meta_name)
            logger.warning(f"适配器 {meta_name} 已禁用，跳过加载")
            return adapter_objs, enabled_adapters, disabled_adapters
            
        try:
            loaded_class = entry_point.load()
            adapter_obj = sys.modules[loaded_class.__module__]
            dist = importlib.metadata.distribution(entry_point.dist.name)
            
            adapter_info = {
                "meta": {
                    "name": meta_name,
                    "version": getattr(adapter_obj, "__version__", dist.version if dist else "1.0.0"),
                    "description": getattr(adapter_obj, "__description__", ""),
                    "author": getattr(adapter_obj, "__author__", ""),
                    "license": getattr(adapter_obj, "__license__", ""),
                    "package": entry_point.dist.name
                },
                "adapter_class": loaded_class
            }
            
            if not hasattr(adapter_obj, 'adapterInfo'):
                adapter_obj.adapterInfo = {}
                
            adapter_obj.adapterInfo[meta_name] = adapter_info
            
            # 存储适配器信息
            mods.set_module(meta_name, adapter_info)
                
            adapter_objs[meta_name] = adapter_obj
            enabled_adapters.append(meta_name)
            logger.debug(f"从PyPI包发现适配器: {meta_name}")
            
        except Exception as e:
            logger.warning(f"从entry-point加载适配器 {meta_name} 失败: {e}")
            raise ImportError(f"无法加载适配器 {meta_name}: {e}")
            
        return adapter_objs, enabled_adapters, disabled_adapters


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
        meta_name = entry_point.name
        module_status = mods.get_module_status(meta_name)
        logger.debug(f"模块 {meta_name} 状态: {module_status}")
        
        # 首先检查模块状态，如果明确为False则直接跳过
        if module_status is False:
            disabled_modules.append(meta_name)
            logger.warning(f"模块 {meta_name} 已禁用，跳过加载")
            return module_objs, enabled_modules, disabled_modules
            
        try:
            loaded_obj = entry_point.load()
            module_obj = sys.modules[loaded_obj.__module__]
            dist = importlib.metadata.distribution(entry_point.dist.name)
            
            lazy_load = ModuleLoader._should_lazy_load(loaded_obj)
            
            module_info = {
                "meta": {
                    "name": meta_name,
                    "version": getattr(module_obj, "__version__", dist.version if dist else "1.0.0"),
                    "description": getattr(module_obj, "__description__", ""),
                    "author": getattr(module_obj, "__author__", ""),
                    "license": getattr(module_obj, "__license__", ""),
                    "package": entry_point.dist.name,
                    "lazy_load": lazy_load
                },
                "module_class": loaded_obj
            }
            
            module_obj.moduleInfo = module_info
            
            # 存储模块信息
            mods.set_module(meta_name, module_info)
                
            module_objs[meta_name] = module_obj
            enabled_modules.append(meta_name)
            logger.debug(f"从PyPI包加载模块: {meta_name}")
            
        except Exception as e:
            logger.warning(f"从entry-point加载模块 {meta_name} 失败: {e}")
            raise ImportError(f"无法加载模块 {meta_name}: {e}")
            
        return module_objs, enabled_modules, disabled_modules
    
    @staticmethod
    def _should_lazy_load(module_class: Type) -> bool:
        """
        检查模块是否应该懒加载
        
        :param module_class: Type 模块类
        :return: bool 如果返回 False，则立即加载；否则懒加载
        """
        # 检查模块是否定义了 should_eager_load() 方法
        if hasattr(module_class, "should_eager_load"):
            try:
                # 调用静态方法，如果返回 True，则禁用懒加载（立即加载）
                return not module_class.should_eager_load()
            except Exception as e:
                logger.warning(f"调用模块 {module_class.__name__} 的 should_eager_load() 失败: {e}")
        
        # 默认启用懒加载
        return True

class ModuleInitializer:
    """
    模块初始化器

    负责协调适配器和模块的初始化流程

    {!--< tips >!--}
    1. 初始化顺序：适配器 → 模块
    2. 模块初始化采用懒加载机制
    {!--< /tips >!--}
    """
    
    @staticmethod
    def init() -> bool:
        """
        初始化所有模块和适配器
        
        执行步骤:
        1. 从PyPI包加载适配器
        2. 从PyPI包加载模块
        3. 预记录所有模块信息
        4. 注册适配器
        5. 初始化各模块
        
        :return: bool 初始化是否成功
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
            
            modules_dir = os.path.join(os.path.dirname(__file__), "modules")
            if os.path.exists(modules_dir) and os.listdir(modules_dir):
                logger.warning("[Warning] 你的项目使用了已经弃用的模块加载方式, 请尽快使用 PyPI 模块加载方式代替")
            
            if not enabled_modules and not enabled_adapters:
                logger.warning("[Init] 没有找到可用的模块和适配器")
                return True
            
            # 3. 注册适配器
            logger.debug("[Init] 正在注册适配器...")
            if not ModuleInitializer._register_adapters(enabled_adapters, adapter_objs):
                return False
            
            # 4. 初始化模块
            logger.debug("[Init] 正在初始化模块...")
            success = ModuleInitializer._initialize_modules(enabled_modules, module_objs)
            logger.info(f"[Init] SDK初始化{'成功' if success else '失败'}")
            return success
            
        except Exception as e:
            logger.critical(f"SDK初始化严重错误: {e}")
            return False
    
    @staticmethod
    def _initialize_modules(modules: List[str], module_objs: Dict[str, Any]) -> bool:
        """
        {!--< internal-use >!--}
        初始化模块
        
        :param modules: List[str] 模块名称列表
        :param module_objs: Dict[str, Any] 模块对象字典
        
        :return: bool 模块初始化是否成功
        """
        # 将所有模块挂载到LazyModule代理上
        for module_name in modules:
            module_obj = module_objs[module_name]
            meta_name = module_obj.moduleInfo["meta"]["name"]
            
            if hasattr(sdk, meta_name):
                continue
                
            try:
                entry_points = importlib.metadata.entry_points()
                if hasattr(entry_points, 'select'):
                    module_entries = entry_points.select(group='erispulse.module')
                    module_entry_map = {entry.name: entry for entry in module_entries}
                else:
                    module_entries = entry_points.get('erispulse.module', [])
                    module_entry_map = {entry.name: entry for entry in module_entries}
                
                entry_point = module_entry_map.get(meta_name)
                if entry_point:
                    module_class = entry_point.load()
                    
                    # 创建LazyModule代理
                    lazy_module = LazyModule(meta_name, module_class, sdk, module_obj.moduleInfo)
                    setattr(sdk, meta_name, lazy_module)
                    
                    logger.debug(f"预注册模块: {meta_name}")
                    
            except Exception as e:
                logger.error(f"预注册模块 {meta_name} 失败: {e}")
                setattr(sdk, meta_name, None)
                return False
        
        # 检查并初始化需要立即加载的模块
        for module_name in modules:
            module_obj = module_objs[module_name]
            meta_name = module_obj.moduleInfo["meta"]["name"]
            
            if not hasattr(sdk, meta_name):
                continue
                
            try:
                entry_points = importlib.metadata.entry_points()
                if hasattr(entry_points, 'select'):
                    module_entries = entry_points.select(group='erispulse.module')
                    module_entry_map = {entry.name: entry for entry in module_entries}
                else:
                    module_entries = entry_points.get('erispulse.module', [])
                    module_entry_map = {entry.name: entry for entry in module_entries}
                
                entry_point = module_entry_map.get(meta_name)
                if entry_point:
                    module_class = entry_point.load()
                    
                    # 检查是否需要立即加载
                    lazy_load = ModuleLoader._should_lazy_load(module_class)
                    if not lazy_load:
                        # 触发LazyModule的初始化
                        getattr(sdk, meta_name)._initialize()
                        logger.debug(f"立即初始化模块: {meta_name}")
                        
            except Exception as e:
                logger.error(f"初始化模块 {meta_name} 失败: {e}")
                return False
                
        return True
    @staticmethod
    def _register_adapters(adapters: List[str], adapter_objs: Dict[str, Any]) -> bool:
        """
        {!--< internal-use >!--}
        注册适配器
        
        :param adapters: List[str] 适配器名称列表
        :param adapter_objs: Dict[str, Any] 适配器对象字典
        
        :return: bool 适配器注册是否成功
        """
        success = True
        registered_classes = {}

        for adapter_name in adapters:
            adapter_obj = adapter_objs[adapter_name]
            
            try:
                if hasattr(adapter_obj, "adapterInfo") and isinstance(adapter_obj.adapterInfo, dict):
                    for platform, adapter_info in adapter_obj.adapterInfo.items():
                        if platform in sdk.adapter._adapters:
                            continue
                            
                        adapter_class = adapter_info["adapter_class"]
                        
                        if adapter_class in registered_classes:
                            instance = registered_classes[adapter_class]
                            # 改为直接操作适配器字典而不是调用register
                            sdk.adapter._adapters[platform] = instance
                            sdk.adapter._platform_to_instance[platform] = instance
                            logger.debug(f"复用适配器实例 {adapter_class.__name__} 到平台别称 {platform}")
                        else:
                            init_signature = inspect.signature(adapter_class.__init__)
                            params = init_signature.parameters
                            
                            if 'sdk' in params:
                                instance = adapter_class(sdk)
                            else:
                                instance = adapter_class()
                            
                            # 直接操作适配器字典
                            sdk.adapter._adapters[platform] = instance
                            sdk.adapter._platform_to_instance[platform] = instance
                            registered_classes[adapter_class] = instance
                            logger.info(f"注册适配器: {platform} ({adapter_class.__name__})")
            except Exception as e:
                logger.error(f"适配器 {adapter_name} 注册失败: {e}")
                success = False
        return success
    
def init_progress() -> bool:
    """
    初始化项目环境文件
    
    1. 检查并创建main.py入口文件
    2. 确保基础目录结构存在

    :return: bool 是否创建了新的main.py文件
    
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

    :return: bool 环境准备是否成功
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

    :return: bool SDK初始化是否成功
    
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


def load_module(module_name: str) -> bool:
    """
    手动加载指定模块
    
    :param module_name: str 要加载的模块名称
    :return: bool 加载是否成功
    
    {!--< tips >!--}
    1. 可用于手动触发懒加载模块的初始化
    2. 如果模块不存在或已加载会返回False
    {!--< /tips >!--}
    """
    try:
        module = getattr(sdk, module_name, None)
        if isinstance(module, LazyModule):
            # 触发懒加载模块的初始化
            module._initialize()
            return True
        elif module is not None:
            logger.warning(f"模块 {module_name} 已经加载")
            return False
        else:
            logger.error(f"模块 {module_name} 不存在")
            return False
    except Exception as e:
        logger.error(f"加载模块 {module_name} 失败: {e}")
        return False


sdk.init = init
sdk.load_module = load_module
