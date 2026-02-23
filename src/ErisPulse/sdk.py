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

# 导入懒加载模块类和初始化协调器
from .loaders.module import LazyModule
from .loaders.initializer import Initializer


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
        self._initializer = Initializer(self)
        
        # 执行初始化
        self._initialized = await self._initializer.init()
        return self._initialized


    async def _prepare_environment(self) -> bool:
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

            main_init = await self._init_progress()
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


    async def _init_progress(self) -> bool:
        """
        {!--< internal-use >!--}
        初始化项目环境文件
        
        :return: bool 是否创建了新的 main.py 文件
        """
        main_file = Path("main.py")
        main_init = False
        
        try:
            if not main_file.exists():
                main_content = """# main.py
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
            
            self._initializer = Initializer(self)
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
        try:
            logger.info("[Uninit] 开始反初始化SDK...")
            
            # 1. 关闭所有适配器
            logger.debug("[Uninit] 正在关闭适配器...")
            await self.adapter.shutdown()
            
            # 2. 卸载所有模块
            logger.debug("[Uninit] 正在卸载模块...")
            await self.module.unload()
            
            # 3. 清理 Event 模块中的所有事件处理器
            logger.debug("[Uninit] 正在清理事件处理器...")
            Event._clear_all_handlers()
            
            # 4. 清理适配器管理器和模块管理器
            logger.debug("[Uninit] 正在清理适配器管理器...")
            self.adapter.clear()
            
            logger.debug("[Uninit] 正在清理模块管理器...")
            self.module.clear()
            
            # 5. 清理 SDK 对象上的模块属性（懒加载模块）
            logger.debug("[Uninit] 正在清理 SDK 对象上的模块属性...")
            from .Core.config import config
            module_status = config.getConfig("ErisPulse.modules.status", {})
            for module_name in module_status.keys():
                if hasattr(self, module_name):
                    delattr(self, module_name)
                    logger.debug(f"[Uninit] 已清理模块属性: {module_name}")
            
            # 6. 清理僵尸线程
            logger.debug("[Uninit] 正在清理线程...")
            # SDK 本身不创建线程，但可以记录可能的线程泄漏
            current_task = asyncio.current_task()
            logger.debug(f"[Uninit] 当前任务: {current_task}")
            
            # 重置初始化状态
            self._initialized = False
            self._initializer = None
            
            logger.info("[Uninit] SDK反初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"[Uninit] SDK反初始化失败: {e}")
            return False


# 创建全局 SDK 实例
sdk = SDK()

__all__ = [
    "SDK",
    "sdk"
]