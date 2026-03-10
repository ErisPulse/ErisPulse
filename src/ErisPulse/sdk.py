"""
ErisPulse SDK 主类

提供统一的 SDK 接口，整合所有核心模块和加载器

{!--< tips >!--}
example:
    >>> from ErisPulse import sdk
    >>> await sdk.init()
    >>> await sdk.adapter.startup()
{!--< /tips >!--}
"""

import asyncio
from pathlib import Path
from typing import Any

# 导入核心模块
from .Core import Event, lifecycle, logger
from .Core import storage, env, config
from .Core import adapter, AdapterFather, BaseAdapter, SendDSL
from .Core import module, router, adapter_server

# 导入懒加载模块类
from .loaders.module import LazyModule
# 导入加载器类
from .loaders.adapter import AdapterLoader
from .loaders.module import ModuleLoader


class SDK:
    """
    ErisPulse SDK 主类
    
    整合所有核心模块和加载器，提供统一的初始化和管理接口
    
    {!--< tips >!--}
    SDK 提供以下核心属性：
    - Event: 事件系统
    - lifecycle: 生命周期管理器
    - logger: 日志管理器
    - storage: 存储管理器
    - env: 存储管理器别名
    - config: 配置管理器
    - adapter: 适配器管理器
    - AdapterFather: 适配器基类别名
    - BaseAdapter: 适配器基类
    - SendDSL: DSL 发送接口基类
    - module: 模块管理器
    - router: 路由管理器
    - adapter_server: 路由管理器别名
    {!--< /tips >!--}
    """
    
    # ==================== 核心模块属性 ====================
    
    Event: Any
    """事件系统"""
    
    lifecycle: Any
    """生命周期管理器"""
    
    logger: Any
    """日志管理器"""
    
    storage: Any
    """存储管理器"""
    
    env: Any
    """存储管理器别名"""
    
    config: Any
    """配置管理器"""
    
    adapter: Any
    """适配器管理器"""
    
    AdapterFather: Any
    """适配器基类别名"""
    
    BaseAdapter: Any
    """适配器基类"""
    
    SendDSL: Any
    """DSL 发送接口基类"""
    
    module: Any
    """模块管理器"""
    
    router: Any
    """路由管理器"""
    
    adapter_server: Any
    """路由管理器别名"""
    
    def __init__(self):
        """
        初始化 SDK 实例
        
        挂载所有核心模块到 SDK 实例
        """
        # 挂载核心模块
        self.Event = Event
        self.lifecycle = lifecycle
        self.logger = logger
        
        self.storage = storage
        self.env = env
        self.config = config
        
        self.adapter = adapter
        # 设置 adapter 的 SDK 引用
        adapter.set_sdk_ref(self)

        self.AdapterFather = AdapterFather
        self.BaseAdapter = BaseAdapter
        self.SendDSL = SendDSL
        
        self.module = module
        # 设置 module 的 SDK 引用
        module.set_sdk_ref(self)
        
        self.router = router
        self.adapter_server = adapter_server
        
        # 初始化协调器（在需要时创建）
        self._initializer: Any = None  # type: ignore
        self._initialized: bool = False
    
    def __getattribute__(self, name: str):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            logger.error(f"[SDK] 未找到属性 {name}, 您可能使用了错误的SDK注册对象")
            return None

    def __repr__(self) -> str:
        """
        返回 SDK 的字符串表示
        
        :return: str SDK 的字符串表示
        """
        return f"<ErisPulse SDK initialized={self._initialized}>"

    # ==================== 内部协调器类 ====================

    class Initializer:
        """
        初始化协调器
        
        协调适配器和模块的加载流程，提供统一的初始化接口
        
        {!--< tips >!--}
        使用方式：
        >>> initializer = Initializer(sdk_instance)
        >>> success = await initializer.init()
        {!--< /tips >!--}
        """
        
        def __init__(self, sdk_instance: Any):
            """
            初始化协调器
            
            :param sdk_instance: SDK 实例
            """
            self._sdk = sdk_instance
            self._adapter_loader = AdapterLoader()
            self._module_loader = ModuleLoader()
        
        async def init(self) -> bool:
            """
            初始化所有模块和适配器
            
            执行步骤:
            1. 从 PyPI 包加载适配器
            2. 从 PyPI 包加载模块
            3. 注册适配器
            4. 注册模块
            5. 初始化模块
            
            :return: bool 初始化是否成功
            
            :raises ImportError: 当加载失败时抛出
            """
            logger.info("SDK 正在初始化...")
            lifecycle.start_timer("core.init")
            
            try:
                # 1. 并行加载适配器和模块
                adapter_manager = self._sdk.adapter
                module_manager = self._sdk.module
                
                # 适配器发现阶段
                logger.print_section_header("适配器发现阶段")
                
                (adapter_result, module_result) = await asyncio.gather(
                    self._adapter_loader.load(adapter_manager),
                    self._module_loader.load(module_manager),
                    return_exceptions=True
                )
                
                # 检查是否有异常
                if isinstance(adapter_result, Exception):
                    logger.error(f"适配器加载失败: {adapter_result}")
                    return False
                    
                if isinstance(module_result, Exception):
                    logger.error(f"模块加载失败: {module_result}")
                    return False
                
                # 解包结果
                adapter_objs, enabled_adapters, disabled_adapters = adapter_result  # type: ignore
                module_objs, enabled_modules, disabled_modules = module_result      # type: ignore
                
                # 2. 注册适配器
                logger.print_section_header("适配器注册阶段")
                if not await self._adapter_loader.register_to_manager(
                    enabled_adapters, adapter_objs, adapter_manager
                ):
                    return False
                
                # 3. 注册模块
                logger.print_section_header("模块注册阶段")
                if not await self._module_loader.register_to_manager(
                    enabled_modules, module_objs, module_manager
                ):
                    return False
                
                # 4. 初始化模块（创建实例并挂载到 SDK）
                logger.print_section_header("模块初始化阶段")
                if enabled_modules:
                    success = await self._module_loader.initialize_modules(
                        enabled_modules, module_objs, module_manager, self._sdk
                    )
                else:
                    success = True
                
                # 获取加载耗时
                load_duration = lifecycle.stop_timer("core.init")
                
                # 总结
                logger.print_section_header("初始化完成")
                
                # 显示耗时
                duration_str = f"{load_duration:.2f}s" if load_duration >= 1 else f"{load_duration*1000:.0f}ms"
                logger.print_info(f"耗时: {duration_str}", level=1)
                
                if enabled_adapters:
                    logger.print_info(f"适配器: {len(enabled_adapters)} 个", level=1)
                    for i, adapter in enumerate(enabled_adapters):
                        is_last = i == len(enabled_adapters) - 1
                        logger.print_tree_item(adapter, level=1, is_last=is_last)
                else:
                    logger.print_info("适配器: 无", level=1)
                
                if enabled_modules:
                    logger.print_info(f"模块: {len(enabled_modules)} 个", level=1)
                    for i, module in enumerate(enabled_modules):
                        is_last = i == len(enabled_modules) - 1
                        logger.print_tree_item(module, level=1, is_last=is_last)
                else:
                    logger.print_info("模块: 无", level=1)
                
                logger.print_section_footer()
                
                logger.info(f"SDK初始化成功 (耗时: {duration_str})")
                
                await lifecycle.submit_event(
                    "core.init.complete",
                    msg="模块初始化完成" if success else "模块初始化失败",
                    data={
                        "duration": load_duration,
                        "success": success,
                        "adapters": {
                            "enabled": enabled_adapters,
                            "disabled": disabled_adapters
                        },
                        "modules": {
                            "enabled": enabled_modules,
                            "disabled": disabled_modules
                        }
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
                        "success": False,
                        "error": str(e)
                    }
                )
                logger.critical(f"SDK初始化严重错误: {e}")
                return False

    class Uninitializer:
        """
        反初始化协调器
        
        协调适配器和模块的卸载流程，提供统一的反初始化接口
        
        {!--< tips >!--}
        使用方式：
        >>> uninitializer = Uninitializer(sdk_instance)
        >>> success = await uninitializer.uninit()
        {!--< /tips >!--}
        """
        
        def __init__(self, sdk_instance: Any):
            """
            反初始化协调器
            
            :param sdk_instance: SDK 实例
            """
            self._sdk = sdk_instance
        
        async def uninit(self) -> bool:
            """
            执行反初始化
            
            执行步骤:
            1. 关闭所有适配器
            2. 卸载所有模块
            3. 清理事件处理器
            4. 清理管理器
            5. 清理 SDK 模块属性
            
            :return: bool 反初始化是否成功
            """
            lifecycle.start_timer("core.uninit")
            
            try:
                adapter_manager = self._sdk.adapter
                module_manager = self._sdk.module
                
                # 1. 关闭所有适配器
                registered_adapters = adapter_manager.list_registered()
                if registered_adapters:
                    await adapter_manager.shutdown()
                
                # 2. 卸载所有模块
                loaded_modules = module_manager.list_loaded()
                if loaded_modules:
                    await module_manager.unload()
                
                # 3. 清理所有事件处理器
                Event._clear_all_handlers()
                
                # 4. 清理管理器
                adapter_manager.clear()
                module_manager.clear()
                
                # 5. 清理 SDK 对象上的模块属性
                module_properties_cleared = 0
                for module_name in module_manager.list_loaded():
                    try:
                        instance_dict = object.__getattribute__(self._sdk, '__dict__')
                        if module_name in instance_dict:
                            del instance_dict[module_name]
                            module_properties_cleared += 1
                    except Exception:
                        pass
                
                # 6. 重置初始化状态
                self._sdk._initialized = False
                self._sdk._initializer = None
                
                # 获取清理耗时
                uninit_duration = lifecycle.stop_timer("core.uninit")
                duration_str = f"{uninit_duration:.2f}s" if uninit_duration >= 1 else f"{uninit_duration*1000:.0f}ms"
                
                # 提交生命周期事件
                await lifecycle.submit_event(
                    "core.uninit.complete",
                    msg="SDK反初始化完成",
                    data={
                        "duration": uninit_duration,
                        "success": True,
                        "adapters_closed": len(registered_adapters),
                        "modules_unloaded": len(loaded_modules),
                        "module_properties_cleared": module_properties_cleared
                    }
                )
                
                logger.info(f"SDK反初始化成功 (耗时: {duration_str})")
                return True
                
            except Exception as e:
                uninit_duration = lifecycle.stop_timer("core.uninit")
                await lifecycle.submit_event(
                    "core.uninit.complete",
                    msg="SDK反初始化失败",
                    data={
                        "duration": uninit_duration,
                        "success": False,
                        "error": str(e)
                    }
                )
                if "attached to a different loop" in str(e):
                    # 这是一个常见的错误，通常是由于SDK在另一个事件循环中运行而导致的。
                    # 在这种情况下，我们直接返回True即可
                    return True
                logger.error(f"SDK反初始化严重错误: {e}")
                return False

    # ==================== SDK 逻辑方法 ====================

    async def init(self) -> bool:
        """
        SDK 初始化入口
        
        :return: bool SDK 初始化是否成功
        
        :example:
        >>> success = await sdk.init()
        >>> if success:
        >>>     await sdk.adapter.startup()
        """
        if not await self._prepare_environment():
            return False
        
        # 创建初始化协调器
        self._initializer = self.Initializer(self)
        
        # 执行初始化
        self._initialized = await self._initializer.init()
        return self._initialized


    async def _prepare_environment(self, script_path: str = "main.py") -> bool:
        """
        {!--< internal-use >!--}
        准备运行环境
        
        初始化项目环境文件和配置
        
        :return: bool 环境准备是否成功
        """
        # 设置全局异常处理
        from .runtime import setup_exception_handling
        setup_exception_handling()
        
        await lifecycle.submit_event(
            "core.init.start",
            msg="开始初始化"
        )

        logger.info("准备初始化环境...")
        try:
            from .runtime import get_erispulse_config
            get_erispulse_config()
            logger.info("配置文件已加载")

            main_init = await self._init_progress(script_path)
            if main_init:
                logger.info("项目入口已生成, 你可以在 main.py 中编写一些代码")
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


    async def _init_progress(self, script_path: str = "main.py") -> bool:
        """
        {!--< internal-use >!--}
        初始化项目环境文件
        
        :return: bool 是否创建了新的 main.py 文件
        """
        main_file = Path(f"{script_path}")
        main_init = False
        
        try:
            if not main_file.exists():
                main_content = """# ErisPulse 主程序文件
# 本文件由 SDK 自动创建，您可随意修改
import asyncio
from ErisPulse import sdk

async def main():
    try:
        # 使用 SDK 的 run 方法
        # 如果你需要更加精细的控制，可以参考查阅 `我的第一个机器人` 文档中的示例代码
        # SDK 会自动：
        # - 初始化和启动适配器
        # - 保持程序运行
        await sdk.run(keep_running=True)
    except Exception as e:
        sdk.logger.error(e)
    except KeyboardInterrupt:
        sdk.logger.info("正在停止程序")
    finally:
        await sdk.uninit()

if __name__ == "__main__":
    asyncio.run(main())
"""
                with open(main_file, "w", encoding="utf-8") as f:
                    f.write(main_content)
                main_init = True
                
            return main_init
        except Exception as e:
            logger.error(f"无法初始化项目环境: {e}")
            return False


    def init_sync(self) -> bool:
        """
        SDK 初始化入口（同步版本）
        
        用于命令行直接调用，自动在事件循环中运行异步初始化
        
        :return: bool SDK 初始化是否成功
        """
        return asyncio.run(self.init())


    def init_task(self) -> asyncio.Task:
        """
        SDK 初始化入口，返回 Task 对象
        
        :return: asyncio.Task 初始化任务
        """
        async def _async_init():
            if not await self._prepare_environment():
                return False
            
            self._initializer = self.Initializer(self)
            self._initialized = await self._initializer.init()
            return self._initialized
        
        try:
            return asyncio.create_task(_async_init())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.create_task(_async_init())


    async def load_module(self, module_name: str) -> bool:
        """
        手动加载指定模块
        
        :param module_name: str 要加载的模块名称
        :return: bool 加载是否成功
        
        :example:
        >>> await sdk.load_module("MyModule")
        """
        try:
            module_instance = getattr(self, module_name, None)
            if isinstance(module_instance, LazyModule):
                # 检查模块是否需要异步初始化
                if hasattr(module_instance, '_needs_async_init') and object.__getattribute__(module_instance, '_needs_async_init'):
                    # 对于需要异步初始化的模块，执行完整异步初始化
                    await module_instance._initialize()
                    object.__setattr__(module_instance, '_needs_async_init', False)
                    return True
                # 检查模块是否已经同步初始化但未完成异步部分
                elif (object.__getattribute__(module_instance, '_initialized') and 
                      object.__getattribute__(module_instance, '_is_base_module')):
                    # 如果是 BaseModule 子类且已同步初始化，只需完成异步部分
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


    async def run(self, keep_running: bool = True) -> None:
        """
        无头模式运行 ErisPulse
        
        :param keep_running: bool 是否保持运行
        
        :example:
        >>> await sdk.run(keep_running=True)
        """
        try:
            isInit = await self.init()
            
            if not isInit:
                logger.error("ErisPulse 初始化失败，请检查日志")
                return
            
            await self.adapter.startup()
            
            if keep_running:
                # 保持程序运行
                await asyncio.Event().wait()
        except Exception as e:
            logger.error(e)
        finally:
            await self.module.unload()
            await self.adapter.shutdown()


    async def _restart_task(self) -> bool:
        """
        {!--< internal-use >!--}
        实际执行重启逻辑的独立任务
        
        此函数在后台任务中运行，与调用 restart() 的事件处理器解耦
        确保即使调用者被取消，重启流程也能完整执行
        
        :return: bool 重新加载是否成功
        """
        try:
            # 先执行反初始化
            uninit_success = await self.uninit()
            if not uninit_success:
                logger.warning("[Reload] 反初始化不完全，将继续尝试重新初始化")
            
            # 再执行初始化
            logger.info("[Reload] 开始重新初始化SDK...")
            if not await self.init():
                logger.error("[Reload] 初始化失败，请检查日志")
                return False
            
            logger.info("[Reload] 正在启动适配器...")
            await self.adapter.startup()
            
            logger.info("[Reload] 重新加载完成")
            logger.info(f"[Reload] "+"-"*50+" [Reload]")
            return True
        except Exception as e:
            logger.error(f"[Reload] 重启失败: {e}")
            return False


    async def restart(self) -> bool:
        """
        SDK 重新启动
        
        执行完整的反初始化后再初始化过程
        
        注意：此函数使用后台任务执行重启流程，确保即使当前事件处理器被取消，
        重启流程仍能完整执行。因此调用此函数后，重启会在后台异步进行。
        
        :return: bool 重新加载是否成功（后台任务完成时返回）
        
        :example:
        >>> await sdk.restart()
        """
        logger.info("[Reload] 开始重新加载SDK...")
        
        # 创建后台任务执行重启，与当前事件处理器解耦
        task = asyncio.create_task(self._restart_task())
        
        # 使用 shield 确保任务不被取消
        try:
            result = await asyncio.shield(task)
            return result
        except asyncio.CancelledError:
            logger.info("[Reload] 重启任务被外部取消，但将在后台继续执行")
            # 任务会在后台继续执行，我们返回 True 表示重启已启动
            # 注意：这是异步启动，实际重启结果需要查看日志
            return True
        
    async def uninit(self) -> bool:
        """
        SDK 反初始化
        
        执行以下操作：
        1. 关闭所有适配器
        2. 卸载所有模块
        3. 清理所有事件处理器
        4. 清理适配器管理器和模块管理器
        5. 清理 SDK 对象上的模块属性
        
        :return: bool 反初始化是否成功
        
        :example:
        >>> await sdk.uninit()
        """
        # 创建反初始化协调器
        uninitializer = self.Uninitializer(self)
        
        # 执行反初始化
        return await uninitializer.uninit()


# 创建全局 SDK 实例
sdk = SDK()

__all__ = [
    "SDK",
    "sdk"
]