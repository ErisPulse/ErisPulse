"""
ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

{!--< tips >!--}
1. 使用前请确保已正确安装所有依赖
2. 调用await sdk.init()进行初始化
3. 模块加载采用懒加载机制
{!--< /tips >!--}
"""

import os
import sys
import types
import importlib
import asyncio
import inspect
import importlib.metadata
from typing import Dict, List, Tuple, Type, Any
from pathlib import Path

# BaseModules: SDK核心模块
# 事件处理模块
from .Core import Event
# 基础设施
from .Core import lifecycle, logger, exceptions
# 存储和配置相关
from .Core import storage, env, config
# 适配器相关
from .Core import adapter, AdapterFather, BaseAdapter, SendDSL
# 模块相关
from .Core import module
# 路由相关
from .Core import router, adapter_server
# 用户体验相关
from .Core import ux, UXManager

# SDK统一对外接口
sdk = types.ModuleType('sdk')

try:
    __version__ = importlib.metadata.version('ErisPulse')
except importlib.metadata.PackageNotFoundError:
    logger.critical("未找到ErisPulse版本信息，请检查是否正确安装ErisPulse")
__author__  = "ErisPulse"

logger.debug("ErisPulse 正在挂载SDK核心模块...")

BaseModules = {
    "Event"         : Event,

    "lifecycle"     : lifecycle,
    "logger"        : logger,
    "exceptions"    : exceptions,

    "storage"       : storage,
    "env"           : env,
    "config"        : config,
    
    "adapter"       : adapter,
    "AdapterFather" : AdapterFather,
    "BaseAdapter"   : BaseAdapter,
    "SendDSL"       : SendDSL,

    "module"        : module,
    
    "router": router,
    "adapter_server": adapter_server,
    "ux": ux,
    "UXManager": UXManager,
}

for module_name, moduleObj in BaseModules.items():
    setattr(sdk, module_name, moduleObj)

logger.debug("ErisPulse 正在挂载loop循环器...")

# 设置默认loop循环捕捉器
asyncio_loop = asyncio.get_event_loop()
exceptions.setup_async_loop(asyncio_loop)

logger.debug("SDK核心模块挂载完毕")

class LazyModule:
    """
    懒加载模块包装器
    
    当模块第一次被访问时才进行实例化
    
    {!--< tips >!--}
    1. 模块的实际实例化会在第一次属性访问时进行
    2. 依赖模块会在被使用时自动初始化
    3. 对于继承自 BaseModule 的模块，会自动调用生命周期方法
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
        # 使用object.__setattr__避免触发自定义的__setattr__
        object.__setattr__(self, '_module_name', module_name)
        object.__setattr__(self, '_module_class', module_class)
        object.__setattr__(self, '_sdk_ref', sdk_ref)
        object.__setattr__(self, '_module_info', module_info)
        object.__setattr__(self, '_instance', None)
        object.__setattr__(self, '_initialized', False)
        object.__setattr__(self, '_is_base_module', module_info.get("meta", {}).get("is_base_module", False))
    
    async def _initialize(self):
        """
        实际初始化模块
        
        :raises LazyLoadError: 当模块初始化失败时抛出
        """
        # 避免重复初始化
        if object.__getattribute__(self, '_initialized'):
            return
            
        logger.debug(f"正在初始化懒加载模块 {object.__getattribute__(self, '_module_name')}...")

        try:
            # 获取类的__init__参数信息
            logger.debug(f"正在获取模块 {object.__getattribute__(self, '_module_name')} 的 __init__ 参数信息...")
            init_signature = inspect.signature(object.__getattribute__(self, '_module_class').__init__)
            params = init_signature.parameters
            
            # 根据参数决定是否传入sdk
            if 'sdk' in params:
                logger.debug(f"模块 {object.__getattribute__(self, '_module_name')} 需要传入 sdk 参数")
                instance = object.__getattribute__(self, '_module_class')(object.__getattribute__(self, '_sdk_ref'))
            else:
                logger.debug(f"模块 {object.__getattribute__(self, '_module_name')} 不需要传入 sdk 参数")
                instance = object.__getattribute__(self, '_module_class')()

            logger.debug(f"正在设置模块 {object.__getattribute__(self, '_module_name')} 的 moduleInfo 属性...")
            setattr(instance, "moduleInfo", object.__getattribute__(self, '_module_info'))
            
            # 使用object.__setattr__避免触发自定义的__setattr__
            object.__setattr__(self, '_instance', instance)
            object.__setattr__(self, '_initialized', True)
            
            # 如果是 BaseModule 子类，在初始化后调用 on_load 方法
            if object.__getattribute__(self, '_is_base_module'):
                logger.debug(f"正在调用模块 {object.__getattribute__(self, '_module_name')} 的 on_load 方法...")
                
                try:
                    await module.load(object.__getattribute__(self, '_module_name'))
                except Exception as e:
                    logger.error(f"调用模块 {object.__getattribute__(self, '_module_name')} 的 on_load 方法时出错: {e}")

            await lifecycle.submit_event(
                    "module.init",
                    msg=f"模块 {object.__getattribute__(self, '_module_name')} 初始化完毕",
                    data={
                        "module_name": object.__getattribute__(self, '_module_name'),
                        "success": True,
                    }
                )
            logger.debug(f"懒加载模块 {object.__getattribute__(self, '_module_name')} 初始化完成")
            
        except Exception as e:
            await lifecycle.submit_event(
                    "module.init",
                    msg=f"模块初始化失败: {e}",
                    data={
                        "module_name": object.__getattribute__(self, '_module_name'),
                        "success": False,
                    }
                )
            logger.error(f"懒加载模块 {object.__getattribute__(self, '_module_name')} 初始化失败: {e}")
            raise e
    
    def _initialize_sync(self):
        """
        同步初始化模块，用于在异步上下文中进行同步调用
        
        :raises LazyLoadError: 当模块初始化失败时抛出
        """
        # 避免重复初始化
        if object.__getattribute__(self, '_initialized'):
            return
            
        logger.debug(f"正在同步初始化懒加载模块 {object.__getattribute__(self, '_module_name')}...")

        try:
            # 获取类的__init__参数信息
            logger.debug(f"正在获取模块 {object.__getattribute__(self, '_module_name')} 的 __init__ 参数信息...")
            init_signature = inspect.signature(object.__getattribute__(self, '_module_class').__init__)
            params = init_signature.parameters
            
            # 根据参数决定是否传入sdk
            if 'sdk' in params:
                logger.debug(f"模块 {object.__getattribute__(self, '_module_name')} 需要传入 sdk 参数")
                instance = object.__getattribute__(self, '_module_class')(object.__getattribute__(self, '_sdk_ref'))
            else:
                logger.debug(f"模块 {object.__getattribute__(self, '_module_name')} 不需要传入 sdk 参数")
                instance = object.__getattribute__(self, '_module_class')()

            logger.debug(f"正在设置模块 {object.__getattribute__(self, '_module_name')} 的 moduleInfo 属性...")
            setattr(instance, "moduleInfo", object.__getattribute__(self, '_module_info'))
            
            # 使用object.__setattr__避免触发自定义的__setattr__
            object.__setattr__(self, '_instance', instance)
            object.__setattr__(self, '_initialized', True)
            object.__setattr__(self, '_needs_async_init', False)  # 确保清除异步初始化标志
            
            # 注意：在同步初始化中，我们不能调用异步的 module.load 和 lifecycle.submit_event
            # 这些将在异步上下文中延迟处理
            
            logger.debug(f"懒加载模块 {object.__getattribute__(self, '_module_name')} 同步初始化完成")
            
        except Exception as e:
            logger.error(f"懒加载模块 {object.__getattribute__(self, '_module_name')} 同步初始化失败: {e}")
            raise e
    
    async def _complete_async_init(self):
        """
        完成异步初始化部分，用于同步初始化后的异步处理
        
        这个方法用于处理 module.load 和事件提交等异步操作
        """
        if not object.__getattribute__(self, '_initialized'):
            return
            
        try:
            # 如果是 BaseModule 子类，在初始化后调用 on_load 方法
            if object.__getattribute__(self, '_is_base_module'):
                logger.debug(f"正在异步调用模块 {object.__getattribute__(self, '_module_name')} 的 on_load 方法...")
                
                try:
                    await module.load(object.__getattribute__(self, '_module_name'))
                except Exception as e:
                    logger.error(f"异步调用模块 {object.__getattribute__(self, '_module_name')} 的 on_load 方法时出错: {e}")

            await lifecycle.submit_event(
                    "module.init",
                    msg=f"模块 {object.__getattribute__(self, '_module_name')} 初始化完毕",
                    data={
                        "module_name": object.__getattribute__(self, '_module_name'),
                        "success": True,
                    }
                )
            logger.debug(f"懒加载模块 {object.__getattribute__(self, '_module_name')} 异步初始化部分完成")
        except Exception as e:
            await lifecycle.submit_event(
                    "module.init",
                    msg=f"模块初始化失败: {e}",
                    data={
                        "module_name": object.__getattribute__(self, '_module_name'),
                        "success": False,
                    }
                )
            logger.error(f"懒加载模块 {object.__getattribute__(self, '_module_name')} 异步初始化部分失败: {e}")
    
    def _ensure_initialized(self) -> None:
        """
        确保模块已初始化
        
        :raises LazyLoadError: 当模块未初始化时抛出
        """
        if not object.__getattribute__(self, '_initialized'):
            # 检查当前是否在异步上下文中
            try:
                loop = asyncio.get_running_loop()
                # 如果在异步上下文中，我们需要检查模块初始化方法是否需要异步
                init_method = getattr(object.__getattribute__(self, '_module_class'), '__init__', None)
                
                # 检查__init__方法是否是协程函数
                if asyncio.iscoroutinefunction(init_method):
                    # 对于需要异步初始化的模块，我们只能设置一个标志，提示需要异步初始化
                    object.__setattr__(self, '_needs_async_init', True)
                    logger.warning(f"模块 {object.__getattribute__(self, '_module_name')} 需要异步初始化，请在异步上下文中调用")
                    return
                else:
                    # 对于同步初始化的模块，使用同步初始化方式
                    self._initialize_sync()
                    
                    # 异步处理需要在初始化后完成的事件
                    if object.__getattribute__(self, '_is_base_module'):
                        # 调度异步任务来处理 module.load 和事件提交
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(self._complete_async_init())
                        except Exception as e:
                            logger.warning(f"无法调度异步初始化任务: {e}")
            except RuntimeError:
                # 没有运行中的事件循环，可以安全地创建新的事件循环
                asyncio.run(self._initialize())
    
    def __getattr__(self, name: str) -> Any:
        """
        属性访问时触发初始化
        
        :param name: str 属性名
        :return: Any 属性值
        """
        logger.debug(f"正在访问懒加载模块 {object.__getattribute__(self, '_module_name')} 的属性 {name}...")
        
        # 检查是否需要异步初始化
        if hasattr(self, '_needs_async_init') and object.__getattribute__(self, '_needs_async_init'):
            raise RuntimeError(
                f"模块 {object.__getattribute__(self, '_module_name')} 需要异步初始化，"
                f"请使用 'await sdk.load_module(\"{object.__getattribute__(self, '_module_name')}\")' 来初始化模块"
            )
        
        self._ensure_initialized()
        return getattr(object.__getattribute__(self, '_instance'), name)
    
    def __setattr__(self, name: str, value: Any) -> None:
        """
        属性设置
        
        :param name: str 属性名
        :param value: Any 属性值
        """
        logger.debug(f"正在设置懒加载模块 {object.__getattribute__(self, '_module_name')} 的属性 {name}...")

        # 特殊属性直接设置到包装器上
        if name.startswith('_') or name in ('moduleInfo',):
            object.__setattr__(self, name, value)
        else:
            # 其他属性在初始化前设置到包装器上，初始化后设置到实际模块实例上
            if name == '_instance' or not hasattr(self, '_initialized') or not object.__getattribute__(self, '_initialized'):
                object.__setattr__(self, name, value)
            else:
                setattr(object.__getattribute__(self, '_instance'), name, value)
    
    def __delattr__(self, name: str) -> None:
        """
        属性删除
        
        :param name: str 属性名
        """
        logger.debug(f"正在删除懒加载模块 {object.__getattribute__(self, '_module_name')} 的属性 {name}...")

        self._ensure_initialized()
        delattr(object.__getattribute__(self, '_instance'), name)
    
    def __getattribute__(self, name: str) -> Any:
        """
        属性访问，初始化后直接委托给实际实例
        
        :param name: str 属性名
        :return: Any 属性值
        """
        # 特殊属性直接从包装器获取
        if name.startswith('_') or name in ('moduleInfo',):
            return object.__getattribute__(self, name)
            
        # 检查是否已初始化
        try:
            initialized = object.__getattribute__(self, '_initialized')
        except AttributeError:
            # 避免在初始化过程中访问_initialized时出现递归
            return object.__getattribute__(self, name)
            
        if not initialized:
            # 确保初始化
            self._ensure_initialized()
            # 重新获取initialized状态
            initialized = object.__getattribute__(self, '_initialized')
            
        # 初始化后直接委托给实际实例
        if initialized:
            instance = object.__getattribute__(self, '_instance')
            return getattr(instance, name)
        else:
            return object.__getattribute__(self, name)
    
    def __dir__(self) -> List[str]:
        """
        返回模块属性列表
        
        :return: List[str] 属性列表
        """
        logger.debug(f"正在获取懒加载模块 {object.__getattribute__(self, '_module_name')} 的属性列表...")

        self._ensure_initialized()
        return dir(object.__getattribute__(self, '_instance'))
    
    def __repr__(self) -> str:
        """
        返回模块表示字符串
        
        :return: str 表示字符串
        """
        logger.debug(f"正在获取懒加载模块 {object.__getattribute__(self, '_module_name')} 的表示字符串...")

        if object.__getattribute__(self, '_initialized'):
            return repr(object.__getattribute__(self, '_instance'))
        return f"<LazyModule {object.__getattribute__(self, '_module_name')} (not initialized)>"
    
    # 代理所有其他魔术方法到实际模块实例
    def __call__(self, *args, **kwargs):
        """代理函数调用"""
        self._ensure_initialized()
        return object.__getattribute__(self, '_instance')(*args, **kwargs)
    

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
    async def load() -> Tuple[Dict[str, object], List[str], List[str]]:
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
        
        logger.info("正在加载适配器entry-points...")

        try:
            # 加载适配器entry-points
            logger.debug("正在获取适配器entry-points...")
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                adapter_entries = entry_points.select(group='erispulse.adapter')
            else:
                adapter_entries = entry_points.get('erispulse.adapter', [])     # type: ignore[attr-defined] || 原因: 3.10.0后entry_points不再支持select方法
            
            # 处理适配器
            logger.debug("正在处理适配器entry-points...")
            for entry_point in adapter_entries:
                adapter_objs, enabled_adapters, disabled_adapters = await AdapterLoader._process_adapter(
                    entry_point, adapter_objs, enabled_adapters, disabled_adapters)
            
            logger.info("适配器加载完成")

        except Exception as e:
            logger.error(f"加载适配器entry-points失败: {e}")
            raise ImportError(f"无法加载适配器: {e}")
        
        return adapter_objs, enabled_adapters, disabled_adapters
    
    @staticmethod
    async def _process_adapter(
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

        # # 检查适配器是否已经注册，如果未注册则进行注册（默认禁用）
        # if not sdk.adapter.exists(meta_name):
        #     sdk.adapter._config_register(meta_name, False)
        #     logger.info(f"发现新适配器 {meta_name}，默认已禁用，请在配置文件中配置适配器并决定是否启用")
        if not sdk.adapter.exists(meta_name):
            sdk.adapter._config_register(meta_name, True)
            logger.info(f"发现新适配器 {meta_name}，默认已启用")
        
        # 获取适配器当前状态
        adapter_status = sdk.adapter.is_enabled(meta_name)
        logger.debug(f"适配器 {meta_name} 状态: {adapter_status}")
        
        if not adapter_status:
            disabled_adapters.append(meta_name)
            logger.debug(f"适配器 {meta_name} 已禁用, 跳过...")
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
                setattr(adapter_obj, 'adapterInfo', {})
                
            adapter_obj.adapterInfo[meta_name] = adapter_info
                
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
    async def load() -> Tuple[Dict[str, object], List[str], List[str]]:
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
        
        logger.info("正在加载模块entry-points...")

        try:
            # 加载模块entry-points
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                module_entries = entry_points.select(group='erispulse.module')
            else:
                module_entries = entry_points.get('erispulse.module', [])     # type: ignore[attr-defined] || 原因: 3.10.0后entry_points不再支持select方法
            
            # 处理模块
            for entry_point in module_entries:
                module_objs, enabled_modules, disabled_modules = await ModuleLoader._process_module(
                    entry_point, module_objs, enabled_modules, disabled_modules)
            
            logger.info("模块加载完成")

        except Exception as e:
            logger.error(f"加载模块entry-points失败: {e}")
            raise ImportError(f"无法加载模块: {e}")
            
        return module_objs, enabled_modules, disabled_modules
    
    @staticmethod
    async def _process_module(
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

        logger.debug(f"正在处理模块: {meta_name}")
        # # 检查模块是否已经注册，如果未注册则进行注册（默认禁用）
        # if not sdk.module.exists(meta_name):
        #     sdk.module._config_register(meta_name, False)  # 默认禁用
        #     logger.info(f"发现新模块 {meta_name}，默认已禁用，请在配置文件中手动启用")

        if not sdk.module.exists(meta_name):
            sdk.module._config_register(meta_name, True)  # 默认启用
            logger.info(f"发现新模块 {meta_name}，默认已启用。如需禁用，请在配置文件中设置 ErisPulse.modules.status.{meta_name} = false")
            
        # 获取模块当前状态
        module_status = sdk.module.is_enabled(meta_name)
        logger.debug(f"模块 {meta_name} 状态: {module_status}")
        
        if not module_status:
            disabled_modules.append(meta_name)
            return module_objs, enabled_modules, disabled_modules
            
        try:
            loaded_obj = entry_point.load()
            module_obj = sys.modules[loaded_obj.__module__]
            dist = importlib.metadata.distribution(entry_point.dist.name)
            
            # 检查模块是否继承自 BaseModule
            from .Core.Bases.module import BaseModule
            is_base_module = inspect.isclass(loaded_obj) and issubclass(loaded_obj, BaseModule)
            
            if not is_base_module:
                logger.warning(f"模块 {meta_name} 未继承自 BaseModule，"\
                            "如果你是这个模块的作者，请检查 ErisPulse 的文档更新 并尽快迁移！")
            
            lazy_load = ModuleLoader._should_lazy_load(loaded_obj)
            
            module_info = {
                "meta": {
                    "name": meta_name,
                    "version": getattr(module_obj, "__version__", dist.version if dist else "1.0.0"),
                    "description": getattr(module_obj, "__description__", ""),
                    "author": getattr(module_obj, "__author__", ""),
                    "license": getattr(module_obj, "__license__", ""),
                    "package": entry_point.dist.name,
                    "lazy_load": lazy_load,
                    "is_base_module": is_base_module
                },
                "module_class": loaded_obj
            }
            
            setattr(module_obj, "moduleInfo", module_info)
            
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

        logger.debug(f"检查模块 {module_class.__name__} 是否应该懒加载")
        
        # 首先检查全局懒加载配置
        try:
            from .Core._self_config import get_framework_config
            framework_config = get_framework_config()
            global_lazy_loading = framework_config.get("enable_lazy_loading", True)
            
            # 如果全局禁用懒加载，则直接返回False
            if not global_lazy_loading:
                logger.debug(f"全局懒加载已禁用，模块 {module_class.__name__} 将立即加载")
                return False
        except Exception as e:
            logger.warning(f"获取框架配置失败: {e}，将使用模块默认配置")
        
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
    模块初始化器（注意：适配器是一个特殊的模块）

    负责协调适配器和模块的初始化流程

    {!--< tips >!--}
    1. 初始化顺序：适配器 → 模块
    2. 模块初始化采用懒加载机制
    {!--< /tips >!--}
    """
    
    @staticmethod
    async def init() -> bool:
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
            # 1. 并行加载适配器和模块
            (adapter_result, module_result) = await asyncio.gather(
                AdapterLoader.load(),
                ModuleLoader.load(),
                return_exceptions=True
            )
            
            # 检查是否有异常
            if isinstance(adapter_result, Exception):
                logger.error(f"[Init] 适配器加载失败: {adapter_result}")
                return False
                
            if isinstance(module_result, Exception):
                logger.error(f"[Init] 模块加载失败: {module_result}")
                return False
            
            # 解包结果
            if not isinstance(adapter_result, Exception):
                adapter_objs, enabled_adapters, disabled_adapters = adapter_result  # type: ignore[assignment]  ||  原因: 已经在方法中进行了类型检查
            else:
                return False
                
            if not isinstance(module_result, Exception):
                module_objs, enabled_modules, disabled_modules = module_result      # type: ignore[assignment]  ||  原因: 已经在方法中进行了类型检查
            else:
                return False
            
            logger.info(f"[Init] 加载了 {len(enabled_adapters)} 个适配器, {len(disabled_adapters)} 个适配器被禁用")
            logger.info(f"[Init] 加载了 {len(enabled_modules)} 个模块, {len(disabled_modules)} 个模块被禁用")

            modules_dir = os.path.join(os.path.dirname(__file__), "modules")
            if os.path.exists(modules_dir) and os.listdir(modules_dir):
                logger.warning("[Warning] 你的项目使用了已经弃用的模块加载方式, 请尽快使用 PyPI 模块加载方式代替")
            
            if not enabled_modules and not enabled_adapters:
                logger.warning("[Init] 没有找到可用的模块和适配器")
                return True
            
            # 3. 注册适配器
            logger.debug("[Init] 正在注册适配器...")
            if not await ModuleInitializer._register_adapters(enabled_adapters, adapter_objs):
                return False
                
            # 4. 初始化模块
            logger.debug("[Init] 正在初始化模块...")
            success = await ModuleInitializer._initialize_modules(enabled_modules, module_objs)
            
            if success:
                logger.info("[Init] SDK初始化成功")
            else:
                logger.error("[Init] SDK初始化失败")
            
            load_duration = lifecycle.stop_timer("core.init")
            await lifecycle.submit_event(
                "core.init.complete",
                msg="模块初始化完成" if success else "模块初始化失败",
                data={
                    "duration": load_duration,
                    "success": success
                }
            )
            return success
            
        except Exception as e:
            load_duration = lifecycle.stop_timer("core.init")
            await lifecycle.submit_event(
                "core.init.complete",
                msg="模块初始化失败",
                data={
                    "duration": load_duration,
                    "success": False
                }
            )
            logger.critical(f"SDK初始化严重错误: {e}")
            return False
    @staticmethod
    async def _initialize_modules(modules: List[str], module_objs: Dict[str, Any]) -> bool:
        """
        {!--< internal-use >!--}
        初始化模块
        
        :param modules: List[str] 模块名称列表
        :param module_objs: Dict[str, Any] 模块对象字典
        
        :return: bool 模块初始化是否成功
        """
        # 并行注册所有模块类
        register_tasks = []
        for module_name in modules:
            module_obj = module_objs[module_name]
            meta_name = module_obj.moduleInfo["meta"]["name"]
            
            async def register_module(name, obj):
                try:
                    entry_points = importlib.metadata.entry_points()
                    if hasattr(entry_points, 'select'):
                        module_entries = entry_points.select(group='erispulse.module')
                        module_entry_map = {entry.name: entry for entry in module_entries}
                    else:
                        module_entries = entry_points.get('erispulse.module', [])         # type: ignore[assignment]    ||  原因: 已经在方法中进行了类型检查，这是一个兼容性的写法
                        module_entry_map = {entry.name: entry for entry in module_entries}
                    
                    entry_point = module_entry_map.get(name)
                    if entry_point:
                        module_class = entry_point.load()
                        
                        module.register(name, module_class, obj.moduleInfo)
                        logger.debug(f"注册模块类: {name}")
                        return True
                    return False
                except Exception as e:
                    logger.error(f"注册模块 {name} 失败: {e}")
                    return False
            
            register_tasks.append(register_module(meta_name, module_obj))
        
        # 等待所有注册任务完成
        register_results = await asyncio.gather(*register_tasks, return_exceptions=True)
        
        # 检查是否有注册失败的情况
        if any(isinstance(result, Exception) or result is False for result in register_results):
            return False
        
        # 将所有模块挂载到sdk对象上
        for module_name in modules:
            module_obj = module_objs[module_name]
            meta_name = module_obj.moduleInfo["meta"]["name"]
            lazy_load = module_obj.moduleInfo["meta"].get("lazy_load", True)
            
            if lazy_load:
                # 使用懒加载方式挂载
                lazy_module = LazyModule(
                    meta_name,
                    module_obj.moduleInfo["module_class"],
                    sdk,
                    module_obj.moduleInfo
                )
                setattr(sdk, meta_name, lazy_module)
                logger.debug(f"挂载懒加载模块到sdk: {meta_name}")
            else:
                # 立即加载的模块暂时挂载为None，稍后会加载
                setattr(sdk, meta_name, None)
                logger.debug(f"预挂载立即加载模块到sdk: {meta_name}")

        # 并行初始化需要立即加载的模块
        eager_load_tasks = []
        for module_name in modules:
            module_obj = module_objs[module_name]
            meta_name = module_obj.moduleInfo["meta"]["name"]
            
            async def load_module_if_eager(name, obj):
                try:
                    # 检查是否需要立即加载
                    entry_points = importlib.metadata.entry_points()
                    if hasattr(entry_points, 'select'):
                        module_entries = entry_points.select(group='erispulse.module')
                        module_entry_map = {entry.name: entry for entry in module_entries}
                    else:
                        module_entries = entry_points.get('erispulse.module', [])         # type: ignore[assignment]    ||  原因: 已经在方法中进行了类型检查，这是一个兼容性的写法
                        module_entry_map = {entry.name: entry for entry in module_entries}
                    
                    entry_point = module_entry_map.get(name)
                    if entry_point:
                        module_class = entry_point.load()
                        
                        # 检查是否需要立即加载
                        lazy_load = ModuleLoader._should_lazy_load(module_class)
                        if not lazy_load:
                            # 立即加载模块
                            result = await module.load(name)
                            if not result:
                                logger.error(f"加载模块 {name} 失败")
                            else:
                                logger.debug(f"立即加载模块: {name}")
                                # 更新sdk上的引用
                                setattr(sdk, name, module.get(name))
                            return result
                    return True  # 不需要立即加载的模块返回True
                except Exception as e:
                    logger.error(f"初始化模块 {name} 失败: {e}")
                    return False
            
            eager_load_tasks.append(load_module_if_eager(meta_name, module_obj))
        
        # 等待所有立即加载任务完成
        load_results = await asyncio.gather(*eager_load_tasks, return_exceptions=True)
        
        # 检查是否有加载失败的情况
        return not any(isinstance(result, Exception) or result is False for result in load_results)
    
    @staticmethod
    async def _register_adapters(adapters: List[str], adapter_objs: Dict[str, Any]) -> bool:
        """
        {!--< internal-use >!--}
        注册适配器
        
        :param adapters: List[str] 适配器名称列表
        :param adapter_objs: Dict[str, Any] 适配器对象字典
        
        :return: bool 适配器注册是否成功
        """
        # 并行注册所有适配器
        register_tasks = []
        
        for adapter_name in adapters:
            adapter_obj = adapter_objs[adapter_name]
            
            async def register_single_adapter(name, obj):
                try:
                    success = True
                    if hasattr(obj, "adapterInfo") and isinstance(obj.adapterInfo, dict):
                        for platform, adapter_info in obj.adapterInfo.items():
                            if platform in adapter._adapters:
                                continue
                                
                            adapter_class = adapter_info["adapter_class"]
                            
                            adapter.register(platform, adapter_class, adapter_info)
                            logger.info(f"注册适配器: {platform} ({adapter_class.__name__})")
                            
                            # 提交适配器加载完成事件
                            await lifecycle.submit_event(
                                "adapter.load",
                                msg=f"适配器 {platform} 加载完成",
                                data={
                                    "platform": platform,
                                    "success": True
                                }
                            )
                    return success
                except Exception as e:
                    logger.error(f"适配器 {name} 注册失败: {e}")
                    # 提交适配器加载失败事件
                    await lifecycle.submit_event(
                        "adapter.load",
                        msg=f"适配器 {name} 加载失败: {e}",
                        data={
                            "platform": name,
                            "success": False
                        }
                    )
                    return False
            
            register_tasks.append(register_single_adapter(adapter_name, adapter_obj))
        
        # 等待所有注册任务完成
        register_results = await asyncio.gather(*register_tasks, return_exceptions=True)
        
        # 检查是否有注册失败的情况
        return not any(isinstance(result, Exception) or result is False for result in register_results)

async def init_progress() -> bool:
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
        isInit = await sdk.init()
        
        if not isInit:
            sdk.logger.error("ErisPulse 初始化失败，请检查日志")
            return
        
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
        logger.error(f"无法初始化项目环境: {e}")
        return False

async def _prepare_environment() -> bool:
    """
    {!--< internal-use >!--}
    准备运行环境
    
    初始化项目环境文件

    :return: bool 环境准备是否成功
    """
    await lifecycle.submit_event(
        "core.init.start",
        msg="开始初始化"
    )
    lifecycle.start_timer("core.init")

    logger.info("[Init] 准备初始化环境...")
    try:
        from .Core._self_config import get_erispulse_config
        get_erispulse_config()
        logger.info("[Init] 配置文件已加载")

        main_init = await init_progress()
        if main_init:
            logger.info("[Init] 项目入口已生成, 你可以在 main.py 中编写一些代码")
        return True
    except Exception as e:
        load_duration = lifecycle.stop_timer("core.init")
        await lifecycle.submit_event(
            "core.init.complete",
            msg="模块初始化失败",
            data={
                "duration": load_duration,
                "success": False
            }
        )
        logger.error(f"环境准备失败: {e}")
        return False

async def init() -> bool:
    """
    SDK初始化入口
    
    :return: bool SDK初始化是否成功
    """
    if not await _prepare_environment():
        return False

    return await ModuleInitializer.init()

def init_sync() -> bool:
    """
    SDK初始化入口（同步版本）

    用于命令行直接调用，自动在事件循环中运行异步初始化

    :return: bool SDK初始化是否成功
    """
    return asyncio.run(init())

def init_task() -> asyncio.Task:
    """
    SDK初始化入口，返回Task对象
    
    :return: asyncio.Task 初始化任务
    """
    async def _async_init():
        if not await _prepare_environment():
            return False
        return await ModuleInitializer.init()
    
    try:
        return asyncio.create_task(_async_init())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.create_task(_async_init())

async def uninit() -> bool:
    """
    SDK反初始化
    
    执行以下操作：
    1. 关闭所有适配器
    2. 卸载所有模块
    3. 清理所有事件处理器
    4. 清理僵尸线程
    
    :return: bool 反初始化是否成功
    """
    try:
        logger.info("[Uninit] 开始反初始化SDK...")
        
        # 1. 关闭所有适配器
        logger.debug("[Uninit] 正在关闭适配器...")
        await adapter.shutdown()
        
        # 2. 卸载所有模块
        logger.debug("[Uninit] 正在卸载模块...")
        await module.unload()

        # 3. 清理Event模块中的所有事件处理器
        Event._clear_all_handlers()
        
        # 4. 清理僵尸线程
        logger.debug("[Uninit] 正在清理线程...")
        # SDK本身不创建线程，但可以记录可能的线程泄漏
        current_task = asyncio.current_task()
        logger.debug(f"[Uninit] 当前任务: {current_task}")
        
        logger.info("[Uninit] SDK反初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"[Uninit] SDK反初始化失败: {e}")
        return False

async def restart() -> bool:
    """
    SDK重新启动
    
    执行完整的反初始化后再初始化过程
    
    :return: bool 重新加载是否成功
    """
    logger.info("[Reload] 开始重新加载SDK...")
    
    # 先执行反初始化
    if not await uninit():
        logger.error("[Reload] 反初始化失败，无法继续重新加载")
        return False
    
    # 再执行初始化
    logger.info("[Reload] 开始重新初始化SDK...")
    if not await init():
        logger.error("[Reload] 初始化失败，请检查日志")
        return False
    
    logger.info("[Reload] 正在启动适配器...")
    await adapter.startup()
    
    logger.info("[Reload] 重新加载完成")
    return True

async def run() -> None:
    """
    无头模式运行ErisPulse
    
    此方法提供了一种无需入口启动的方式，适用于与其它框架集成的场景
    """
    try:
        isInit = await init()
        
        if not isInit:
            logger.error("ErisPulse 初始化失败，请检查日志")
            return
        
        await adapter.startup()
        
        # 保持程序运行
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(e)
    finally:
        await module.unload()
        await adapter.shutdown()

async def load_module(module_name: str) -> bool:
    """
    手动加载指定模块
    
    :param module_name: str 要加载的模块名称
    :return: bool 加载是否成功
    
    {!--< tips >!--}
    1. 可用于手动触发懒加载模块的初始化
    2. 如果模块不存在或已加载会返回False
    3. 对于需要异步初始化的模块，这是唯一的加载方式
    {!--< /tips >!--}
    """
    try:
        module_instance = getattr(sdk, module_name, None)
        if isinstance(module_instance, LazyModule):
            # 检查模块是否需要异步初始化
            if hasattr(module_instance, '_needs_async_init') and object.__getattribute__(module_instance, '_needs_async_init'):
                # 对于需要异步初始化的模块，执行完整异步初始化
                await module_instance._initialize()
                object.__setattr__(module_instance, '_needs_async_init', False)  # 清除标志
                return True
            # 检查模块是否已经同步初始化但未完成异步部分
            elif (object.__getattribute__(module_instance, '_initialized') and 
                  object.__getattribute__(module_instance, '_is_base_module')):
                # 如果是BaseModule子类且已同步初始化，只需完成异步部分
                await module_instance._complete_async_init()
                return True
            else:
                # 触发懒加载模块的完整初始化
                await module_instance._initialize()
                return True
        elif module_instance is not None:
            logger.warning(f"模块 {module_name} 已经加载")
            return False
        else:
            logger.error(f"模块 {module_name} 不存在")
            return False
    except Exception as e:
        logger.error(f"加载模块 {module_name} 失败: {e}")
        return False
    
logger.debug("ErisPulse 正在挂载必要的入口方法")
setattr(sdk, "init", init)
setattr(sdk, "init_task", init_task)
setattr(sdk, "load_module", load_module)
setattr(sdk, "run", run)
setattr(sdk, "restart", restart)
setattr(sdk, "uninit", uninit)
