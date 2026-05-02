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
from typing import Any, TYPE_CHECKING
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

    async def load(
        self, manager_instance: Any
    ) -> tuple[dict[str, Any], list[str], list[str]]:
        """
        从 entry-points 加载对象（使用 ModuleFinder）

        :param manager_instance: 管理器实例
        :return:
            dict[str, Any]: 对象字典
            list[str]: 启用列表
            list[str]: 禁用列表

        :raises ImportError: 当加载失败时抛出
        """
        objs: dict[str, Any] = {}
        enabled_list: list[str] = []
        disabled_list: list[str] = []

        group_name = self._get_entry_point_group()

        try:
            # 使用 ModuleFinder 查找 entry-points
            if entries := self._finder.find_all():
                logger.print_info(f"发现 {len(entries)} 个模块", level=1)
                for i, entry in enumerate(entries):
                    is_last = i == len(entries) - 1
                    logger.print_tree_item(entry.name, level=1, is_last=is_last)
            else:
                logger.print_info("未发现模块", level=1)

            # 处理每个 entry-point
            for entry_point in entries:
                (
                    objs,
                    enabled_list,
                    disabled_list,
                    is_new,
                ) = await self._process_entry_point(
                    entry_point, objs, enabled_list, disabled_list, manager_instance
                )

            logger.print_section_separator()

        except Exception as e:
            logger.error(f"加载 {group_name} entry-points 失败: {e}")
            raise ImportError(f"无法加载 {group_name}: {e}")

        return objs, enabled_list, disabled_list

    async def _process_entry_point(
        self,
        entry_point: Any,
        objs: dict[str, Any],
        enabled_list: list[str],
        disabled_list: list[str],
        manager_instance: Any,
    ) -> tuple[dict[str, Any], list[str], list[str], bool]:
        """
        处理单个模块 entry-point

        :param entry_point: entry-point 对象
        :param objs: 模块对象字典
        :param enabled_list: 启用的模块列表
        :param disabled_list: 停用的模块列表
        :param manager_instance: 模块管理器实例

        :return:
            dict[str, Any]: 更新后的模块对象字典
            list[str]: 更新后的启用模块列表
            list[str]: 更新后的禁用模块列表
            bool: 是否为新模块

        :raises ImportError: 当模块加载失败时抛出
        """
        meta_name = entry_point.name
        is_new = False

        # 检查模块是否已经注册，如果未注册则进行注册（默认启用）
        if not manager_instance.exists(meta_name):
            manager_instance._config_register(meta_name, True)
            is_new = True

        # 获取模块当前状态
        if not (module_status := manager_instance.is_enabled(meta_name)):
            disabled_list.append(meta_name)
            return objs, enabled_list, disabled_list, is_new

        try:
            loaded_obj = entry_point.load()
            module_obj = sys.modules[loaded_obj.__module__]
            if dist := importlib.metadata.distribution(entry_point.dist.name):
                pass

            # 检查模块是否继承自 BaseModule
            from ..Core.Bases.module import BaseModule

            is_base_module = inspect.isclass(loaded_obj) and issubclass(
                loaded_obj, BaseModule
            )

            if not is_base_module:
                logger.warning(
                    f"模块 {meta_name} 未继承自 BaseModule，"
                    "如果你是这个模块的作者，请检查 ErisPulse 的文档更新并尽快迁移！"
                )

            # 获取模块加载策略
            strategy = self._get_load_strategy(loaded_obj)
            lazy_load = self._extract_strategy_value(strategy, "lazy_load", True)
            priority = self._extract_strategy_value(strategy, "priority", 0)

            module_info = {
                "meta": {
                    "name": meta_name,
                    "version": getattr(
                        module_obj, "__version__", dist.version if dist else "1.0.0"
                    ),
                    "description": getattr(module_obj, "__description__", ""),
                    "author": getattr(module_obj, "__author__", ""),
                    "license": getattr(module_obj, "__license__", ""),
                    "package": entry_point.dist.name,
                    "lazy_load": lazy_load,
                    "priority": priority,
                    "is_base_module": is_base_module,
                },
                "module_class": loaded_obj,
                "strategy": strategy,
            }

            setattr(module_obj, "moduleInfo", module_info)

            objs[meta_name] = module_obj
            enabled_list.append(meta_name)

        except Exception as e:
            logger.error(f"从 entry-point 加载模块 {meta_name} 失败，已跳过: {e}")

        return objs, enabled_list, disabled_list, is_new

    def _extract_strategy_value(self, strategy: Any, key: str, default: Any) -> Any:
        """
        从策略对象或字典中提取值

        :param strategy: 策略对象（dict 或 ModuleLoadStrategy）
        :param key: 键名
        :param default: 默认值
        :return: 提取到的值或默认值

        {!--< internal-use >!--}
        内部方法，统一处理 dict 和 ModuleLoadStrategy 两种策略类型
        {!--< /internal-use >!--}
        """
        if isinstance(strategy, dict):
            return strategy.get(key, default)
        if hasattr(strategy, "_data"):
            return strategy._data.get(key, default)
        return default

    def _get_global_lazy_loading(self) -> bool:
        """
        获取全局懒加载配置

        :return: 是否启用懒加载（默认 True）

        {!--< internal-use >!--}
        内部方法，用于获取全局懒加载配置
        {!--< /internal-use >!--}
        """
        try:
            from ..runtime import get_framework_config

            framework_config = get_framework_config()
            return framework_config.get("enable_lazy_loading", True)
        except Exception as e:
            logger.debug(f"获取框架配置失败: {e}，使用默认值 True")
            return True

    def _resolve_strategy(self, module_class: type) -> Any:
        """
        按优先级从模块类解析加载策略

        优先级：should_eager_load()（旧版兼容） → get_load_strategy()

        :param module_class: 模块类
        :return: 策略对象或 None

        {!--< internal-use >!--}
        内部方法，用于解析模块的加载策略
        {!--< /internal-use >!--}
        """
        # 优先检查旧方法 should_eager_load()
        if hasattr(module_class, "should_eager_load"):
            try:
                eager_load = module_class.should_eager_load()
                return {"lazy_load": not eager_load, "priority": 0}
            except Exception as e:
                logger.warning(
                    f"调用模块 {module_class.__name__} 的 should_eager_load() 失败: {e}"
                )

        # 检查新方法 get_load_strategy()
        if hasattr(module_class, "get_load_strategy"):
            try:
                return module_class.get_load_strategy()
            except Exception as e:
                logger.warning(
                    f"调用模块 {module_class.__name__} 的 get_load_strategy() 失败: {e}"
                )

        return None

    def _apply_global_lazy_loading(self, strategy: Any, lazy_load: bool) -> Any:
        """
        应用全局懒加载配置到策略

        :param strategy: 原始策略
        :param lazy_load: 懒加载值
        :return: 修改后的策略

        {!--< internal-use >!--}
        内部方法，用于应用全局配置覆盖
        {!--< /internal-use >!--}
        """
        if isinstance(strategy, dict):
            return dict(strategy, lazy_load=lazy_load)
        elif hasattr(strategy, "_data"):
            from .strategy import ModuleLoadStrategy

            data = dict(strategy._data)
            data["lazy_load"] = lazy_load
            return ModuleLoadStrategy(**data)
        return strategy

    def _get_load_strategy(self, module_class: type) -> Any:
        """
        获取模块加载策略

        优先级：
        1. 模块的 should_eager_load() 方法（旧版兼容）
        2. 模块的 get_load_strategy() 方法
        3. 全局配置
        4. 默认策略

        全局配置会覆盖模块策略中的 lazy_load 设置

        :param module_class: Type 模块类
        :return: 加载策略对象或字典

        {!--< internal-use >!--}
        内部方法，用于获取模块的加载策略
        {!--< /internal-use >!--}
        """
        global_lazy_loading = self._get_global_lazy_loading()
        strategy = self._resolve_strategy(module_class)

        # 全局配置覆盖策略中的 lazy_load 设置
        if strategy is not None and not global_lazy_loading:
            strategy = self._apply_global_lazy_loading(strategy, False)

        return (
            strategy
            if strategy is not None
            else {"lazy_load": global_lazy_loading, "priority": 0}
        )

    async def register_to_manager(
        self, modules: list[str], module_objs: dict[str, Any], manager_instance: Any
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
                    if entry_point := self._finder.find_by_name(name):
                        module_class = entry_point.load()

                        # 调用管理器的 register 方法
                        manager_instance.register(name, module_class, obj.moduleInfo)
                        return True
                    return False
                except Exception as e:
                    logger.error(f"注册模块 {name} 失败: {e}")
                    return False

            register_tasks.append(register_module(meta_name, module_obj))

        # 等待所有注册任务完成
        register_results = await asyncio.gather(*register_tasks, return_exceptions=True)

        # 检查是否有注册失败的情况
        return not any(
            isinstance(result, Exception) or result is False
            for result in register_results
        )

    async def initialize_modules(
        self,
        modules: list[str],
        module_objs: dict[str, Any],
        manager_instance: Any,
        sdk_instance: Any,
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
                    manager_instance,
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
        module_class: type,
        sdk_ref: Any,
        module_info: dict[str, Any],
        manager_instance: Any,
    ) -> None:
        """
        初始化懒加载包装器

        :param module_name: str 模块名称
        :param module_class: Type 模块类
        :param sdk_ref: Any SDK 引用
        :param module_info: dict[str, Any] 模块信息字典
        :param manager_instance: 模块管理器实例
        """
        object.__setattr__(self, "_module_name", module_name)
        object.__setattr__(self, "_module_class", module_class)
        object.__setattr__(self, "_sdk_ref", sdk_ref)
        object.__setattr__(self, "_module_info", module_info)
        object.__setattr__(self, "_instance", None)
        object.__setattr__(self, "_initialized", False)
        object.__setattr__(self, "_manager_instance", manager_instance)
        object.__setattr__(
            self,
            "_is_base_module",
            module_info.get("meta", {}).get("is_base_module", False),
        )

    async def _initialize(self) -> None:
        """
        实际初始化模块

        :raises Exception: 当模块初始化失败时抛出

        {!--< internal-use >!--}
        内部方法，执行实际的模块初始化
        {!--< /internal-use >!--}
        """
        if object.__getattribute__(self, "_initialized"):
            return

        module_name = object.__getattribute__(self, '_module_name')
        logger.debug(f"正在初始化懒加载模块 {module_name}...")

        try:
            is_base_module = object.__getattribute__(self, "_is_base_module")

            if is_base_module:
                # BaseModule: 通过 manager.load() 统一处理实例化和 on_load
                # 避免 LazyModule 自行创建实例导致双重实例化
                manager_instance = object.__getattribute__(self, "_manager_instance")
                success = await manager_instance.load(module_name)
                
                if not success:
                    raise RuntimeError(f"模块 {module_name} 通过 manager.load() 加载失败")
                
                # 使用 manager 中创建的实例（唯一的真实实例）
                instance = manager_instance.get(module_name)
                if instance is None:
                    raise RuntimeError(f"模块 {module_name} manager.load() 成功但 get() 返回 None")
                
                # 确保 moduleInfo 已设置
                module_info = object.__getattribute__(self, "_module_info")
                if not hasattr(instance, 'moduleInfo') or instance.moduleInfo is None:
                    setattr(instance, "moduleInfo", module_info)
                
                object.__setattr__(self, "_instance", instance)
            else:
                # 非 BaseModule: 保持原有行为，LazyModule 自行实例化
                init_signature = inspect.signature(
                    object.__getattribute__(self, "_module_class").__init__
                )
                params = init_signature.parameters

                if "sdk" in params:
                    instance = object.__getattribute__(self, "_module_class")(
                        object.__getattribute__(self, "_sdk_ref")
                    )
                else:
                    instance = object.__getattribute__(self, "_module_class")()

                setattr(
                    instance, "moduleInfo", object.__getattribute__(self, "_module_info")
                )

                object.__setattr__(self, "_instance", instance)

            object.__setattr__(self, "_initialized", True)

            await lifecycle.submit_event(
                "module.init",
                msg=f"模块 {object.__getattribute__(self, '_module_name')} 初始化完毕",
                data={
                    "module_name": object.__getattribute__(self, "_module_name"),
                    "success": True,
                },
            )
            logger.debug(
                f"懒加载模块 {object.__getattribute__(self, '_module_name')} 初始化完成"
            )

        except Exception as e:
            await lifecycle.submit_event(
                "module.init",
                msg=f"模块初始化失败: {e}",
                data={
                    "module_name": object.__getattribute__(self, "_module_name"),
                    "success": False,
                },
            )
            logger.error(
                f"懒加载模块 {object.__getattribute__(self, '_module_name')} 初始化失败: {e}"
            )
            raise e

    def _ensure_initialized(self) -> None:
        """
        确保模块已初始化

        {!--< internal-use >!--}
        内部方法，检查并确保模块已初始化
        {!--< /internal-use >!--}
        
        设计说明：
        - 支持同步/异步透明的懒加载机制，用户无需感知差异
        - BaseModule 在同步上下文中使用 asyncio.run() 确保初始化完成
        - 非 BaseModule 保持原有逻辑，支持同步初始化
        {!--< internal-use >!--}
        """
        if not object.__getattribute__(self, "_initialized"):
            try:
                loop = asyncio.get_running_loop()
                
                if object.__getattribute__(self, "_is_base_module"):
                    # BaseModule 必须通过 manager.load() 异步初始化
                    # 在同步上下文中，使用 asyncio.run() 确保初始化完成
                    # 在异步上下文中，使用 loop.create_task() 避免阻塞
                    if loop.is_running():
                        loop.create_task(self._initialize())
                    else:
                        asyncio.run(self._initialize())
                    return

                init_method = getattr(
                    object.__getattribute__(self, "_module_class"), "__init__", None
                )

                if inspect.iscoroutinefunction(init_method):
                    object.__setattr__(self, "_needs_async_init", True)
                    logger.warning(
                        f"模块 {object.__getattribute__(self, '_module_name')} 需要异步初始化，请在异步上下文中调用"
                    )
                    return
                else:
                    self._initialize_sync()
            except RuntimeError:
                asyncio.run(self._initialize())

    def _initialize_sync(self) -> None:
        """
        同步初始化模块

        {!--< internal-use >!--}
        内部方法，在同步上下文中初始化模块
        {!--< /internal-use >!--}
        """
        if object.__getattribute__(self, "_initialized"):
            return

        logger.debug(
            f"正在同步初始化懒加载模块 {object.__getattribute__(self, '_module_name')}..."
        )

        try:
            init_signature = inspect.signature(
                object.__getattribute__(self, "_module_class").__init__
            )
            params = init_signature.parameters

            if "sdk" in params:
                instance = object.__getattribute__(self, "_module_class")(
                    object.__getattribute__(self, "_sdk_ref")
                )
            else:
                instance = object.__getattribute__(self, "_module_class")()

            setattr(
                instance, "moduleInfo", object.__getattribute__(self, "_module_info")
            )
            object.__setattr__(self, "_instance", instance)
            object.__setattr__(self, "_initialized", True)

            logger.debug(
                f"懒加载模块 {object.__getattribute__(self, '_module_name')} 同步初始化完成"
            )

        except Exception as e:
            logger.error(
                f"懒加载模块 {object.__getattribute__(self, '_module_name')} 同步初始化失败: {e}"
            )
            raise e

    async def _complete_async_init(self) -> None:
        """
        完成异步初始化部分

        {!--< internal-use >!--}
        内部方法，处理模块的异步初始化部分
        {!--< /internal-use >!--}
        """
        if not object.__getattribute__(self, "_initialized"):
            return

        try:
            # _initialize 已经通过 manager.load() 完成了 BaseModule 的 on_load
            # 这里只需要提交生命周期事件即可
            await lifecycle.submit_event(
                "module.init",
                msg=f"模块 {object.__getattribute__(self, '_module_name')} 初始化完毕",
                data={
                    "module_name": object.__getattribute__(self, "_module_name"),
                    "success": True,
                },
            )
            logger.debug(
                f"懒加载模块 {object.__getattribute__(self, '_module_name')} 异步初始化部分完成"
            )
        except Exception as e:
            await lifecycle.submit_event(
                "module.init",
                msg=f"模块初始化失败: {e}",
                data={
                    "module_name": object.__getattribute__(self, "_module_name"),
                    "success": False,
                },
            )
            logger.error(
                f"懒加载模块 {object.__getattribute__(self, '_module_name')} 异步初始化部分失败: {e}"
            )

    def __getattr__(self, name: str) -> Any:
        """
        属性访问时触发初始化

        :param name: str 属性名
        :return: Any 属性值
        """
        logger.debug(
            f"正在访问懒加载模块 {object.__getattribute__(self, '_module_name')} 的属性 {name}..."
        )

        if hasattr(self, "_needs_async_init") and object.__getattribute__(
            self, "_needs_async_init"
        ):
            raise RuntimeError(
                f"模块 {object.__getattribute__(self, '_module_name')} 需要异步初始化，"
                f"请使用 'await sdk.load_module(\"{object.__getattribute__(self, '_module_name')}\")' 来初始化模块"
            )

        self._ensure_initialized()
        return getattr(object.__getattribute__(self, "_instance"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        属性设置

        :param name: str 属性名
        :param value: Any 属性值
        """
        logger.debug(
            f"正在设置懒加载模块 {object.__getattribute__(self, '_module_name')} 的属性 {name}..."
        )

        if name.startswith("_") or name in ("moduleInfo",):
            object.__setattr__(self, name, value)
        else:
            if (
                name == "_instance"
                or not hasattr(self, "_initialized")
                or not object.__getattribute__(self, "_initialized")
            ):
                object.__setattr__(self, name, value)
            else:
                setattr(object.__getattribute__(self, "_instance"), name, value)

    def __delattr__(self, name: str) -> None:
        """
        属性删除

        :param name: str 属性名
        """
        logger.debug(
            f"正在删除懒加载模块 {object.__getattribute__(self, '_module_name')} 的属性 {name}..."
        )
        self._ensure_initialized()
        delattr(object.__getattribute__(self, "_instance"), name)

    def __getattribute__(self, name: str) -> Any:
        """
        属性访问，初始化后直接委托给实际实例

        :param name: str 属性名
        :return: Any 属性值
        """
        if name.startswith("_") or name in ("moduleInfo",):
            return object.__getattribute__(self, name)

        try:
            initialized = object.__getattribute__(self, "_initialized")
        except AttributeError:
            return object.__getattribute__(self, name)

        if not initialized:
            self._ensure_initialized()
            initialized = object.__getattribute__(self, "_initialized")

        if initialized:
            instance = object.__getattribute__(self, "_instance")
            return getattr(instance, name)
        else:
            return object.__getattribute__(self, name)

    def __dir__(self) -> list[str]:
        """
        返回模块属性列表

        :return: list[str] 属性列表
        """
        logger.debug(
            f"正在获取懒加载模块 {object.__getattribute__(self, '_module_name')} 的属性列表..."
        )
        self._ensure_initialized()
        return dir(object.__getattribute__(self, "_instance"))

    def __repr__(self) -> str:
        """
        返回模块表示字符串

        :return: str 表示字符串
        """
        logger.debug(
            f"正在获取懒加载模块 {object.__getattribute__(self, '_module_name')} 的表示字符串..."
        )
        if object.__getattribute__(self, "_initialized"):
            return repr(object.__getattribute__(self, "_instance"))
        return f"<LazyModule {object.__getattribute__(self, '_module_name')} (not initialized)>"

    def __call__(self, *args, **kwargs):
        """
        代理函数调用

        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 调用结果
        """
        self._ensure_initialized()
        instance = object.__getattribute__(self, "_instance")
        return instance(*args, **kwargs)
