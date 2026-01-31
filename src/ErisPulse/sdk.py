"""
ErisPulse SDK 主类

提供统一的 SDK 接口，整合所有核心模块和加载器

{!--< tips >!--}
使用方式：
    >>> from ErisPulse import sdk
    >>> await sdk.init()
    >>> await sdk.adapter.startup()
{!--< /tips >!--}
"""

import asyncio
from typing import Any
from .loaders.initializer import Initializer

# 导入核心模块
from .Core import Event
from .Core import lifecycle, logger, exceptions
from .Core import storage, env, config
from .Core import adapter, AdapterFather, BaseAdapter, SendDSL
from .Core import module
from .Core import router, adapter_server


class SDK:
    """
    ErisPulse SDK 主类
    
    整合所有核心模块和加载器，提供统一的初始化和管理接口
    
    {!--< tips >!--}
    SDK 提供以下核心属性：
    - Event: 事件系统
    - lifecycle: 生命周期管理器
    - logger: 日志管理器
    - exceptions: 异常处理模块
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
    
    exceptions: Any
    """异常处理模块"""
    
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
        self.exceptions = exceptions
        
        self.storage = storage
        self.env = env
        self.config = config
        
        self.adapter = adapter
        self.AdapterFather = AdapterFather
        self.BaseAdapter = BaseAdapter
        self.SendDSL = SendDSL
        
        self.module = module
        
        self.router = router
        self.adapter_server = adapter_server
        
        # 初始化协调器（在需要时创建）
        self._initializer: Initializer = None  # type: ignore
        self._initialized: bool = False
    
    # ==================== 初始化方法 ====================
    
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
        await lifecycle.submit_event(
            "core.init.start",
            msg="开始初始化"
        )

        logger.info("[Init] 准备初始化环境...")
        try:
            from .Core._self_config import get_erispulse_config
            get_erispulse_config()
            logger.info("[Init] 配置文件已加载")

            main_init = await self._init_progress()
            if main_init:
                logger.info("[Init] 项目入口已生成, 你可以在 main.py 中编写一些代码")
            return True
        except Exception as e:
            load_duration = self.lifecycle.stop_timer("core.init")
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
        from pathlib import Path
        
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
    
    # ==================== 模块加载方法 ====================
    
    async def load_module(self, module_name: str) -> bool:
        """
        手动加载指定模块
        
        :param module_name: str 要加载的模块名称
        :return: bool 加载是否成功
        
        :example:
        >>> await sdk.load_module("MyModule")
        """
        from .loaders.module_loader import LazyModule
        
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
    
    # ==================== 运行方法 ====================
    
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
    
    # ==================== 重启方法 ====================
    
    async def restart(self) -> bool:
        """
        SDK 重新启动
        
        执行完整的反初始化后再初始化过程
        
        :return: bool 重新加载是否成功
        
        :example:
        >>> await sdk.restart()
        """
        logger.info("[Reload] 开始重新加载SDK...")
        
        # 先执行反初始化
        if not await self.uninit():
            logger.error("[Reload] 反初始化失败，无法继续重新加载")
            return False
        
        # 再执行初始化
        logger.info("[Reload] 开始重新初始化SDK...")
        if not await self.init():
            logger.error("[Reload] 初始化失败，请检查日志")
            return False
        
        logger.info("[Reload] 正在启动适配器...")
        await self.adapter.startup()
        
        logger.info("[Reload] 重新加载完成")
        return True
    
    # ==================== 反初始化方法 ====================
    
    async def uninit(self) -> bool:
        """
        SDK 反初始化
        
        执行以下操作：
        1. 关闭所有适配器
        2. 卸载所有模块
        3. 清理所有事件处理器
        4. 清理僵尸线程
        
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
            Event._clear_all_handlers()
            
            # 4. 清理僵尸线程
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
    
    def __repr__(self) -> str:
        """
        返回 SDK 的字符串表示
        
        :return: str SDK 的字符串表示
        """
        return f"<ErisPulse SDK initialized={self._initialized}>"


# 创建全局 SDK 实例
sdk = SDK()

__all__ = [
    "SDK",
    "sdk"
]
