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


__all__ = [
    "Initializer"
]
