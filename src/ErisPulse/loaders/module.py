"""
ErisPulse 模块加载器

专门用于从 PyPI 包加载和初始化普通模块

{!--< tips >!--}
1. 模块必须通过 entry-points 机制注册到 erispulse.module 组
2. 模块类名应与 entry-point 名称一致
3. 模块支持懒加载机制
{!--< /tips >!--}
"""

import sys
import asyncio
import inspect
import importlib.metadata
from typing import Dict, List, Any, Tuple, Type, TYPE_CHECKING
from .bases.loader import BaseLoader
from ..Core.logger import logger
from ..Core.lifecycle import lifecycle
from ..finders import ModuleFinder

if TYPE_CHECKING:
    from ..Core.Bases.module import BaseModule

class ModuleLoader(BaseLoader):
    """
    模块加载器
    
    负责从 PyPI entry-points 加载模块，支持懒加载
    
    {!--< tips >!--}
    使用方式：
    >>> loader = ModuleLoader()
    >>> module_objs, enabled, disabled = await loader.load(module_manager)
    {!--< /tips >!--}
    """
    
    def __init__(self):
        """初始化模块加载器"""
        super().__init__("ErisPulse.modules")
        self._finder = ModuleFinder()
    
    def _get_entry_point_group(self) -> str:
        """
        获取 entry-point 组名
        
        :return: "erispulse.module"
        """
        return "erispulse.module"
    
    async def load(self, manager_instance: Any) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        从 entry-points 加载对象（使用 ModuleFinder）
        
        :param manager_instance: 管理器实例
        :return: 
            Dict[str, Any]: 对象字典
            List[str]: 启用列表
            List[str]: 禁用列表
            
        :raises ImportError: 当加载失败时抛出
        """
        objs: Dict[str, Any] = {}
        enabled_list: List[str] = []
        disabled_list: List[str] = []
        
        group_name = self._get_entry_point_group()
        logger.info(f"正在加载 {group_name} entry-points...")
        
        try:
            # 使用 ModuleFinder 查找 entry-points
            entries = self._finder.find_all()
            
            # 处理每个 entry-point
            for entry_point in entries:
                objs, enabled_list, disabled_list = await self._process_entry_point(
                    entry_point, objs, enabled_list, disabled_list, manager_instance
                )
            
            logger.info(f"{group_name} 加载完成")
            
        except Exception as e:
            logger.error(f"加载 {group_name} entry-points 失败: {e}")
            raise ImportError(f"无法加载 {group_name}: {e}")
        
        return objs, enabled_list, disabled_list
    
    async def _process_entry_point(
        self,
        entry_point: Any,
        objs: Dict[str, Any],
        enabled_list: List[str],
        disabled_list: List[str],
        manager_instance: Any
    ) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        处理单个模块 entry-point
        
        :param entry_point: entry-point 对象
        :param objs: 模块对象字典
        :param enabled_list: 启用的模块列表
        :param disabled_list: 停用的模块列表
        :param manager_instance: 模块管理器实例
        
        :return: 
            Dict[str, Any]: 更新后的模块对象字典
            List[str]: 更新后的启用模块列表 
            List[str]: 更新后的禁用模块列表
            
        :raises ImportError: 当模块加载失败时抛出
        """
        meta_name = entry_point.name
        
        logger.debug(f"正在处理模块: {meta_name}")
        
        # 检查模块是否已经注册，如果未注册则进行注册（默认启用）
        if not manager_instance.exists(meta_name):
            manager_instance._config_register(meta_name, True)
            logger.info(f"发现新模块 {meta_name}，默认已启用。如需禁用，请在配置文件中设置 ErisPulse.modules.status.{meta_name} = false")
            
        # 获取模块当前状态
        module_status = manager_instance.is_enabled(meta_name)
        logger.debug(f"模块 {meta_name} 状态: {module_status}")
        
        if not module_status:
            disabled_list.append(meta_name)
            return objs, enabled_list, disabled_list
            
        try:
            loaded_obj = entry_point.load()
            module_obj = sys.modules[loaded_obj.__module__]
            dist = importlib.metadata.distribution(entry_point.dist.name)
            
            # 检查模块是否继承自 BaseModule
            from ..Core.Bases.module import BaseModule
            is_base_module = inspect.isclass(loaded_obj) and issubclass(loaded_obj, BaseModule)
            
            if not is_base_module:
                logger.warning(f"模块 {meta_name} 未继承自 BaseModule，"\
                            "如果你是这个模块的作者，请检查 ErisPulse 的文档更新并尽快迁移！")
            
            # 获取模块加载策略
            strategy = self._get_load_strategy(loaded_obj)
            lazy_load = strategy.get('lazy_load', True) if isinstance(strategy, dict) else strategy.lazy_load if 'lazy_load' in strategy else True
            priority = strategy.get('priority', 0) if isinstance(strategy, dict) else strategy.priority if 'priority' in strategy else 0
            
            module_info = {
                "meta": {
                    "name": meta_name,
                    "version": getattr(module_obj, "__version__", dist.version if dist else "1.0.0"),
                    "description": getattr(module_obj, "__description__", ""),
                    "author": getattr(module_obj, "__author__", ""),
                    "license": getattr(module_obj, "__license__", ""),
                    "package": entry_point.dist.name,
                    "lazy_load": lazy_load,
                    "priority": priority,
                    "is_base_module": is_base_module
                },
                "module_class": loaded_obj,
                "strategy": strategy
            }
            
            setattr(module_obj, "moduleInfo", module_info)
            
            objs[meta_name] = module_obj
            enabled_list.append(meta_name)
            logger.debug(f"从 PyPI 包加载模块: {meta_name}")
            
        except Exception as e:
            logger.warning(f"从 entry-point 加载模块 {meta_name} 失败: {e}")
            raise ImportError(f"无法加载模块 {meta_name}: {e}")
            
        return objs, enabled_list, disabled_list
    
    def _get_load_strategy(self, module_class: Type) -> Any:
        """
        获取模块加载策略
        
        :param module_class: Type 模块类
        :return: 加载策略对象或字典
        
        {!--< internal-use >!--}
        内部方法，用于获取模块的加载策略
        {!--< /internal-use >!--}
        """
        # 首先检查全局懒加载配置
        global_lazy_loading = True
        try:
            from ..Core._self_config import get_framework_config
            framework_config = get_framework_config()
            global_lazy_loading = framework_config.get("enable_lazy_loading", True)
        except Exception as e:
            logger.warning(f"获取框架配置失败: {e}，将使用模块默认配置")
        
        # 检查模块是否定义了 get_load_strategy() 方法
        if hasattr(module_class, "get_load_strategy"):
            try:
                strategy = module_class.get_load_strategy()
                
                # 如果全局禁用懒加载，则覆盖策略中的 lazy_load 设置
                if not global_lazy_loading:
                    if isinstance(strategy, dict):
                        strategy = dict(strategy, lazy_load=False)
                    elif 'lazy_load' in strategy:
                        strategy = self._strategy_with_lazy_load(strategy, False)
                
                return strategy
            except Exception as e:
                logger.warning(f"调用模块 {module_class.__name__} 的 get_load_strategy() 失败: {e}")
        
        # 检查模块是否定义了 should_eager_load() 方法（兼容旧方法）
        if hasattr(module_class, "should_eager_load"):
            try:
                eager_load = module_class.should_eager_load()
                return {"lazy_load": not eager_load, "priority": 0}
            except Exception as e:
                logger.warning(f"调用模块 {module_class.__name__} 的 should_eager_load() 失败: {e}")
        
        # 默认策略
        return {"lazy_load": global_lazy_loading, "priority": 0}
    
    def _strategy_with_lazy_load(self, strategy: Any, lazy_load: bool) -> Any:
        """
        创建修改 lazy_load 的新策略副本
        
        :param strategy: 原始策略
        :param lazy_load: 懒加载值
        :return: 新策略
        
        {!--< internal-use >!--}
        内部方法，用于创建修改后的策略副本
        {!--< /internal-use >!--}
        """
        # 由于 ModuleLoadStrategy 使用 _data 存储，我们需要创建新实例
        from .strategy import ModuleLoadStrategy
        data = dict(strategy._data)
        data['lazy_load'] = lazy_load
        return ModuleLoadStrategy(**data)
    
    async def register_to_manager(
        self,
        modules: List[str],
        module_objs: Dict[str, Any],
        manager_instance: Any
    ) -> bool:
        """
        将模块类注册到管理器
        
        :param modules: 模块名称列表
        :param module_objs: 模块对象字典
        :param manager_instance: 模块管理器实例
        :return: 模块注册是否成功
        
        {!--< tips >!--}
        此方法由初始化协调器调用，仅注册模块类，不进行实例化
        {!--< /tips >!--}
        """
        register_tasks = []
        
        for module_name in modules:
            module_obj = module_objs[module_name]
            meta_name = module_obj.moduleInfo["meta"]["name"]
            
            async def register_module(name: str, obj: Any) -> bool:
                """注册单个模块"""
                try:
                    # 使用 ModuleFinder 获取 entry-point
                    entry_point = self._finder.find_by_name(name)
                    if entry_point:
                        module_class = entry_point.load()
                        
                        # 调用管理器的 register 方法
                        manager_instance.register(name, module_class, obj.moduleInfo)
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
        return not any(isinstance(result, Exception) or result is False for result in register_results)
    
    async def initialize_modules(
        self,
        modules: List[str],
        module_objs: Dict[str, Any],
        manager_instance: Any,
        sdk_instance: Any
    ) -> bool:
        """
        初始化模块（创建实例并挂载到 SDK）
        
        :param modules: 模块名称列表
        :param module_objs: 模块对象字典
        :param manager_instance: 模块管理器实例
        :param sdk_instance: SDK 实例
        :return: 模块初始化是否成功
        
        {!--< tips >!--}
        此方法处理模块的实际初始化和挂载
        {!--< /tips >!--}
        
        并行注册所有模块类（已在 register_to_manager 中完成）
        这里处理模块的实例化和挂载
        """
        for module_name in modules:
            module_obj = module_objs[module_name]
            meta_name = module_obj.moduleInfo["meta"]["name"]
            lazy_load = module_obj.moduleInfo["meta"].get("lazy_load", True)
            
            if lazy_load:
                # 使用懒加载方式挂载
                lazy_module = LazyModule(
                    meta_name,
                    module_obj.moduleInfo["module_class"],
                    sdk_instance,
                    module_obj.moduleInfo,
                    manager_instance
                )
                setattr(sdk_instance, meta_name, lazy_module)
                logger.debug(f"挂载懒加载模块到 sdk: {meta_name}")
            else:
                # 立即加载的模块
                result = await manager_instance.load(meta_name)
                if result:
                    setattr(sdk_instance, meta_name, manager_instance.get(meta_name))
                    logger.debug(f"挂载立即加载模块到 sdk: {meta_name}")
                else:
                    logger.error(f"立即加载模块 {meta_name} 失败")
                    return False
        
        return True

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
    
    def __init__(
        self,
        module_name: str,
        module_class: Type,
        sdk_ref: Any,
        module_info: Dict[str, Any],
        manager_instance: Any
    ) -> None:
        """
        初始化懒加载包装器
        
        :param module_name: str 模块名称
        :param module_class: Type 模块类
        :param sdk_ref: Any SDK 引用
        :param module_info: Dict[str, Any] 模块信息字典
        :param manager_instance: 模块管理器实例
        """
        object.__setattr__(self, '_module_name', module_name)
        object.__setattr__(self, '_module_class', module_class)
        object.__setattr__(self, '_sdk_ref', sdk_ref)
        object.__setattr__(self, '_module_info', module_info)
        object.__setattr__(self, '_instance', None)
        object.__setattr__(self, '_initialized', False)
        object.__setattr__(self, '_manager_instance', manager_instance)
        object.__setattr__(self, '_is_base_module', module_info.get("meta", {}).get("is_base_module", False))
    
    async def _initialize(self) -> None:
        """
        实际初始化模块
        
        :raises Exception: 当模块初始化失败时抛出
        
        {!--< internal-use >!--}
        内部方法，执行实际的模块初始化
        {!--< /internal-use >!--}
        """
        if object.__getattribute__(self, '_initialized'):
            return
            
        logger.debug(f"正在初始化懒加载模块 {object.__getattribute__(self, '_module_name')}...")

        try:
            # 获取类的 __init__ 参数信息
            logger.debug(f"正在获取模块 {object.__getattribute__(self, '_module_name')} 的 __init__ 参数信息...")
            init_signature = inspect.signature(object.__getattribute__(self, '_module_class').__init__)
            params = init_signature.parameters
            
            # 根据参数决定是否传入 sdk
            if 'sdk' in params:
                logger.debug(f"模块 {object.__getattribute__(self, '_module_name')} 需要传入 sdk 参数")
                instance = object.__getattribute__(self, '_module_class')(object.__getattribute__(self, '_sdk_ref'))
            else:
                logger.debug(f"模块 {object.__getattribute__(self, '_module_name')} 不需要传入 sdk 参数")
                instance = object.__getattribute__(self, '_module_class')()

            logger.debug(f"正在设置模块 {object.__getattribute__(self, '_module_name')} 的 moduleInfo 属性...")
            setattr(instance, "moduleInfo", object.__getattribute__(self, '_module_info'))
            
            object.__setattr__(self, '_instance', instance)
            object.__setattr__(self, '_initialized', True)
            
            # 如果是 BaseModule 子类，在初始化后调用 on_load 方法
            if object.__getattribute__(self, '_is_base_module'):
                logger.debug(f"正在调用模块 {object.__getattribute__(self, '_module_name')} 的 on_load 方法...")
                
                try:
                    await object.__getattribute__(self, '_manager_instance').load(object.__getattribute__(self, '_module_name'))
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
    
    def _ensure_initialized(self) -> None:
        """
        确保模块已初始化
        
        :raises RuntimeError: 当模块需要异步初始化时抛出
        
        {!--< internal-use >!--}
        内部方法，检查并确保模块已初始化
        {!--< /internal-use >!--}
        """
        if not object.__getattribute__(self, '_initialized'):
            try:
                loop = asyncio.get_running_loop()
                init_method = getattr(object.__getattribute__(self, '_module_class'), '__init__', None)
                
                if asyncio.iscoroutinefunction(init_method):
                    object.__setattr__(self, '_needs_async_init', True)
                    logger.warning(f"模块 {object.__getattribute__(self, '_module_name')} 需要异步初始化，请在异步上下文中调用")
                    return
                else:
                    self._initialize_sync()
                    
                    if object.__getattribute__(self, '_is_base_module'):
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(self._complete_async_init())
                        except Exception as e:
                            logger.warning(f"无法调度异步初始化任务: {e}")
            except RuntimeError:
                asyncio.run(self._initialize())
    
    def _initialize_sync(self) -> None:
        """
        同步初始化模块
        
        {!--< internal-use >!--}
        内部方法，在同步上下文中初始化模块
        {!--< /internal-use >!--}
        """
        if object.__getattribute__(self, '_initialized'):
            return
            
        logger.debug(f"正在同步初始化懒加载模块 {object.__getattribute__(self, '_module_name')}...")

        try:
            init_signature = inspect.signature(object.__getattribute__(self, '_module_class').__init__)
            params = init_signature.parameters
            
            if 'sdk' in params:
                instance = object.__getattribute__(self, '_module_class')(object.__getattribute__(self, '_sdk_ref'))
            else:
                instance = object.__getattribute__(self, '_module_class')()

            setattr(instance, "moduleInfo", object.__getattribute__(self, '_module_info'))
            object.__setattr__(self, '_instance', instance)
            object.__setattr__(self, '_initialized', True)
            
            logger.debug(f"懒加载模块 {object.__getattribute__(self, '_module_name')} 同步初始化完成")
            
        except Exception as e:
            logger.error(f"懒加载模块 {object.__getattribute__(self, '_module_name')} 同步初始化失败: {e}")
            raise e
    
    async def _complete_async_init(self) -> None:
        """
        完成异步初始化部分
        
        {!--< internal-use >!--}
        内部方法，处理模块的异步初始化部分
        {!--< /internal-use >!--}
        """
        if not object.__getattribute__(self, '_initialized'):
            return
            
        try:
            if object.__getattribute__(self, '_is_base_module'):
                logger.debug(f"正在异步调用模块 {object.__getattribute__(self, '_module_name')} 的 on_load 方法...")
                
                try:
                    await object.__getattribute__(self, '_manager_instance').load(object.__getattribute__(self, '_module_name'))
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
    
    def __getattr__(self, name: str) -> Any:
        """
        属性访问时触发初始化
        
        :param name: str 属性名
        :return: Any 属性值
        """
        logger.debug(f"正在访问懒加载模块 {object.__getattribute__(self, '_module_name')} 的属性 {name}...")
        
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

        if name.startswith('_') or name in ('moduleInfo',):
            object.__setattr__(self, name, value)
        else:
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
        if name.startswith('_') or name in ('moduleInfo',):
            return object.__getattribute__(self, name)
            
        try:
            initialized = object.__getattribute__(self, '_initialized')
        except AttributeError:
            return object.__getattribute__(self, name)
            
        if not initialized:
            self._ensure_initialized()
            initialized = object.__getattribute__(self, '_initialized')
            
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
    
    def __call__(self, *args, **kwargs):
        """
        代理函数调用
        
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 调用结果
        """
        self._ensure_initialized()
        instance = object.__getattribute__(self, '_instance')
        return instance(*args, **kwargs)
