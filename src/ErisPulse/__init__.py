"""
ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

{!--< tips >!--}
1. 使用前请确保已正确安装所有依赖
2. 调用await sdk.init()进行初始化
3. 模块加载采用懒加载机制
{!--< /tips >!--}
"""

import asyncio
from pathlib import Path

import importlib.metadata

# 导入核心模块
from .Core import (
    Event,
    lifecycle,
    logger,
    exceptions,
    storage,
    env,
    config,
    adapter,
    AdapterFather,
    BaseAdapter,
    SendDSL,
    module,
    router,
    adapter_server,
)

# 导入实际的SDK对象
from .sdk import sdk

# 导入懒加载模块类
from .loaders.module import LazyModule
from .loaders.initializer import Initializer


# ==================== SDK 逻辑方法 ====================

async def init() -> bool:
    """
    SDK 初始化入口
    
    :return: bool SDK 初始化是否成功
    
    :example:
    >>> success = await sdk.init()
    >>> if success:
    >>>     await sdk.adapter.startup()
    """
    if not await _prepare_environment():
        return False
    
    # 创建初始化协调器
    sdk._initializer = Initializer(sdk)
    
    # 执行初始化
    sdk._initialized = await sdk._initializer.init()
    return sdk._initialized


async def _prepare_environment() -> bool:
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

        main_init = await _init_progress()
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


async def _init_progress() -> bool:
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


def init_sync() -> bool:
    """
    SDK 初始化入口（同步版本）
    
    用于命令行直接调用，自动在事件循环中运行异步初始化
    
    :return: bool SDK 初始化是否成功
    """
    return asyncio.run(init())


def init_task() -> asyncio.Task:
    """
    SDK 初始化入口，返回 Task 对象
    
    :return: asyncio.Task 初始化任务
    """
    async def _async_init():
        if not await _prepare_environment():
            return False
        
        sdk._initializer = Initializer(sdk)
        sdk._initialized = await sdk._initializer.init()
        return sdk._initialized
    
    try:
        return asyncio.create_task(_async_init())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.create_task(_async_init())


async def load_module(module_name: str) -> bool:
    """
    手动加载指定模块
    
    :param module_name: str 要加载的模块名称
    :return: bool 加载是否成功
    
    :example:
    >>> await sdk.load_module("MyModule")
    """
    try:
        module_instance = getattr(sdk, module_name, None)
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


async def run(keep_running: bool = True) -> None:
    """
    无头模式运行 ErisPulse
    
    :param keep_running: bool 是否保持运行
    
    :example:
    >>> await sdk.run(keep_running=True)
    """
    try:
        isInit = await init()
        
        if not isInit:
            logger.error("ErisPulse 初始化失败，请检查日志")
            return
        
        await sdk.adapter.startup()
        
        if keep_running:
            # 保持程序运行
            await asyncio.Event().wait()
    except Exception as e:
        logger.error(e)
    finally:
        await sdk.module.unload()
        await sdk.adapter.shutdown()


async def _restart_task() -> bool:
    """
    {!--< internal-use >!--}
    实际执行重启逻辑的独立任务
    
    此函数在后台任务中运行，与调用 restart() 的事件处理器解耦
    确保即使调用者被取消，重启流程也能完整执行
    
    :return: bool 重新加载是否成功
    """
    try:
        # 先执行反初始化
        uninit_success = await uninit()
        if not uninit_success:
            logger.warning("[Reload] 反初始化不完全，将继续尝试重新初始化")
        
        # 再执行初始化
        logger.info("[Reload] 开始重新初始化SDK...")
        if not await init():
            logger.error("[Reload] 初始化失败，请检查日志")
            return False
        
        logger.info("[Reload] 正在启动适配器...")
        await sdk.adapter.startup()
        
        logger.info("[Reload] 重新加载完成")
        logger.info(f"[Reload] "+"-"*50+" [Reload]")
        return True
    except Exception as e:
        logger.error(f"[Reload] 重启失败: {e}")
        return False


async def restart() -> bool:
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
    task = asyncio.create_task(_restart_task())
    
    # 使用 shield 确保任务不被取消
    try:
        result = await asyncio.shield(task)
        return result
    except asyncio.CancelledError:
        logger.info("[Reload] 重启任务被外部取消，但将在后台继续执行")
        # 任务会在后台继续执行，我们返回 True 表示重启已启动
        # 注意：这是异步启动，实际重启结果需要查看日志
        return True
    
async def uninit() -> bool:
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
        await sdk.adapter.shutdown()
        
        # 2. 卸载所有模块
        logger.debug("[Uninit] 正在卸载模块...")
        await sdk.module.unload()
        
        # 3. 清理 Event 模块中的所有事件处理器
        logger.debug("[Uninit] 正在清理事件处理器...")
        Event._clear_all_handlers()
        
        # 4. 清理适配器管理器和模块管理器
        logger.debug("[Uninit] 正在清理适配器管理器...")
        sdk.adapter.clear()
        
        logger.debug("[Uninit] 正在清理模块管理器...")
        sdk.module.clear()
        
        # 5. 清理 SDK 对象上的模块属性（懒加载模块）
        logger.debug("[Uninit] 正在清理 SDK 对象上的模块属性...")
        from .Core.config import config
        module_status = config.getConfig("ErisPulse.modules.status", {})
        for module_name in module_status.keys():
            if hasattr(sdk, module_name):
                delattr(sdk, module_name)
                logger.debug(f"[Uninit] 已清理模块属性: {module_name}")
        
        # 6. 清理僵尸线程
        logger.debug("[Uninit] 正在清理线程...")
        # SDK 本身不创建线程，但可以记录可能的线程泄漏
        current_task = asyncio.current_task()
        logger.debug(f"[Uninit] 当前任务: {current_task}")
        
        # 重置初始化状态
        sdk._initialized = False
        sdk._initializer = None
        
        logger.info("[Uninit] SDK反初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"[Uninit] SDK反初始化失败: {e}")
        return False


# ==================== 将方法绑定到 SDK 对象 ====================

sdk.init = init
sdk._prepare_environment = _prepare_environment
sdk._init_progress = _init_progress
sdk.init_sync = init_sync
sdk.init_task = init_task
sdk.load_module = load_module
sdk.run = run
sdk.restart = restart
sdk.uninit = uninit


# ==================== 版本信息 ====================

__version__ = "UnknownVersion"
__author__ = "ErisPulse"

try:
    __version__ = importlib.metadata.version('ErisPulse')
except importlib.metadata.PackageNotFoundError:
    pass


# 导出对象
__all__ = [
    "sdk",
    "__version__",
    "__author__",
    "LazyModule",
    "init",
    "init_sync",
    "init_task",
    "load_module",
    "run",
    "restart",
    "uninit",
]
