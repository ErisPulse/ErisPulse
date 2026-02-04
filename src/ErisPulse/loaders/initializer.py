"""
ErisPulse 初始化协调器

负责协调适配器和模块的加载流程

{!--< tips >!--}
1. 初始化顺序：适配器 → 模块
2. 支持并行加载优化
3. 统一的错误处理和事件提交
{!--< /tips >!--}
"""

import asyncio
from typing import List, Dict, Any, Optional
from .adapter import AdapterLoader
from .module import ModuleLoader
from ..Core.logger import logger
from ..Core.lifecycle import lifecycle


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
        logger.info("[Init] SDK 正在初始化...")
        lifecycle.start_timer("core.init")
        
        try:
            # 1. 并行加载适配器和模块
            adapter_manager = self._sdk.adapter
            module_manager = self._sdk.module
            
            (adapter_result, module_result) = await asyncio.gather(
                self._adapter_loader.load(adapter_manager),
                self._module_loader.load(module_manager),
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
            adapter_objs, enabled_adapters, disabled_adapters = adapter_result  # type: ignore
            module_objs, enabled_modules, disabled_modules = module_result      # type: ignore
            
            logger.info(f"[Init] 加载了 {len(enabled_adapters)} 个适配器, {len(disabled_adapters)} 个适配器被禁用")
            logger.info(f"[Init] 加载了 {len(enabled_modules)} 个模块, {len(disabled_modules)} 个模块被禁用")
            
            # 2. 注册适配器
            logger.debug("[Init] 正在注册适配器...")
            if not await self._adapter_loader.register_to_manager(
                enabled_adapters, adapter_objs, adapter_manager
            ):
                return False
            
            # 3. 注册模块
            logger.debug("[Init] 正在注册模块...")
            if not await self._module_loader.register_to_manager(
                enabled_modules, module_objs, module_manager
            ):
                return False
            
            # 4. 初始化模块（创建实例并挂载到 SDK）
            logger.debug("[Init] 正在初始化模块...")
            success = await self._module_loader.initialize_modules(
                enabled_modules, module_objs, module_manager, self._sdk
            )
            
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


__all__ = [
    "Initializer"
]
