"""
ErisPulse 适配器加载器

专门用于从 PyPI 包加载和初始化适配器

{!--< tips >!--}
1. 适配器必须通过 entry-points 机制注册到 erispulse.adapter 组
2. 适配器类必须继承 BaseAdapter
3. 适配器不适用懒加载
{!--< /tips >!--}
"""

import sys
import asyncio
import importlib.metadata
from typing import Any
from .bases.loader import BaseLoader
from ..Core.logger import logger
from ..Core.lifecycle import lifecycle
from ..finders import AdapterFinder


class AdapterLoader(BaseLoader):
    """
    适配器加载器

    负责从 PyPI entry-points 加载适配器

    {!--< tips >!--}
    使用方式：
    >>> loader = AdapterLoader()
    >>> adapter_objs, enabled, disabled = await loader.load(adapter_manager)
    {!--< /tips >!--}
    """

    def __init__(self):
        """初始化适配器加载器"""
        super().__init__("ErisPulse.adapters")
        self._finder = AdapterFinder()

    def _get_entry_point_group(self) -> str:
        """
        获取 entry-point 组名

        :return: "erispulse.adapter"
        """
        return "erispulse.adapter"

    async def load(
        self, manager_instance: Any
    ) -> tuple[dict[str, Any], list[str], list[str]]:
        """
        从 entry-points 加载对象（使用 AdapterFinder）

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
            # 使用 AdapterFinder 查找 entry-points
            entries = self._finder.find_all()

            if entries:
                logger.print_info(f"发现 {len(entries)} 个适配器", level=1)
                for i, entry in enumerate(entries):
                    is_last = i == len(entries) - 1
                    logger.print_tree_item(entry.name, level=1, is_last=is_last)
            else:
                logger.print_info("未发现适配器", level=1)

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

        except KeyboardInterrupt:
            raise  # 允许用户中断
        except SystemExit as e:
            logger.error(
                f"加载 {group_name} 时触发 SystemExit({e.code})，已阻止进程退出。"
                f"请不要使用 sys.exit() 或 raise SystemExit"
            )
        except Exception as e:
            logger.error(f"加载 {group_name} entry-points 失败: {e}")

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
        处理单个适配器 entry-point

        :param entry_point: entry-point 对象
        :param objs: 适配器对象字典
        :param enabled_list: 启用的适配器列表
        :param disabled_list: 停用的适配器列表
        :param manager_instance: 适配器管理器实例

        :return:
            dict[str, Any]: 更新后的适配器对象字典
            list[str]: 更新后的启用适配器列表
            list[str]: 更新后的禁用适配器列表
            bool: 是否为新适配器

        :raises ImportError: 当适配器加载失败时抛出
        """
        meta_name = entry_point.name
        is_new = False

        # 检查适配器是否已经注册，如果未注册则进行注册（默认启用）
        if not manager_instance.exists(meta_name):
            manager_instance._config_register(meta_name, True)
            is_new = True

        # 获取适配器当前状态
        adapter_status = manager_instance.is_enabled(meta_name)

        if not adapter_status:
            disabled_list.append(meta_name)
            return objs, enabled_list, disabled_list, is_new

        try:
            loaded_class = entry_point.load()
            adapter_obj = sys.modules[loaded_class.__module__]
            dist = (
                importlib.metadata.distribution(entry_point.dist.name)
                if entry_point.dist
                else None
            )

            adapter_info = {
                "meta": {
                    "name": meta_name,
                    "version": getattr(
                        adapter_obj, "__version__", dist.version if dist else "1.0.0"
                    ),
                    "description": getattr(adapter_obj, "__description__", ""),
                    "author": getattr(adapter_obj, "__author__", ""),
                    "license": getattr(adapter_obj, "__license__", ""),
                    "package": entry_point.dist.name if entry_point.dist else None,
                    "top_level": self._finder.get_top_level_modules(
                        entry_point.dist.name
                    )
                    if entry_point.dist
                    else [],
                },
                "adapter_class": loaded_class,
            }

            if not hasattr(adapter_obj, "adapterInfo"):
                setattr(adapter_obj, "adapterInfo", {})

            adapter_obj.adapterInfo[meta_name] = adapter_info

            objs[meta_name] = adapter_obj
            enabled_list.append(meta_name)

        except SystemExit as e:
            logger.error(
                f"加载适配器 {meta_name} 时触发 SystemExit({e.code})，已跳过。"
                f"请不要在适配器中使用 sys.exit() 或 raise SystemExit"
            )
        except Exception as e:
            logger.error(f"加载适配器 {meta_name} 失败，已跳过: {e}")

        return objs, enabled_list, disabled_list, is_new

    async def register_to_manager(
        self, adapters: list[str], adapter_objs: dict[str, Any], manager_instance: Any
    ) -> bool:
        """
        将适配器注册到管理器

        :param adapters: 适配器名称列表
        :param adapter_objs: 适配器对象字典
        :param manager_instance: 适配器管理器实例
        :return: 适配器注册是否成功

        {!--< tips >!--}
        此方法由初始化协调器调用
        {!--< /tips >!--}
        """
        # 并行注册所有适配器
        register_tasks = []

        for adapter_name in adapters:
            adapter_obj = adapter_objs[adapter_name]

            async def register_single_adapter(name: str, obj: Any) -> bool:
                """注册单个适配器"""
                try:
                    success = True
                    if hasattr(obj, "adapterInfo") and isinstance(
                        obj.adapterInfo, dict
                    ):
                        for platform, adapter_info in obj.adapterInfo.items():
                            # 使用管理器的方法检查是否已存在
                            if platform in manager_instance._adapters:
                                continue

                            adapter_class = adapter_info["adapter_class"]

                            # 调用管理器的 register 方法
                            manager_instance.register(
                                platform, adapter_class, adapter_info
                            )

                            # 提交适配器加载完成事件
                            await lifecycle.submit_event(
                                "adapter.load",
                                msg=f"适配器 {platform} 加载完成",
                                data={"platform": platform, "success": True},
                            )
                    return success
                except SystemExit as e:
                    logger.error(
                        f"适配器 {name} 注册时尝试退出进程 (SystemExit({e.code}))，已跳过。"
                        f"请不要使用 sys.exit() 或 raise SystemExit"
                    )
                    await lifecycle.submit_event(
                        "adapter.load",
                        msg=f"适配器 {name} 注册时触发 SystemExit",
                        data={"platform": name, "success": False},
                    )
                    return False
                except Exception as e:
                    logger.error(f"适配器 {name} 注册失败: {e}")
                    # 提交适配器加载失败事件
                    await lifecycle.submit_event(
                        "adapter.load",
                        msg=f"适配器 {name} 加载失败: {e}",
                        data={"platform": name, "success": False},
                    )
                    return False

            register_tasks.append(register_single_adapter(adapter_name, adapter_obj))

        # 等待所有注册任务完成
        register_results = await asyncio.gather(*register_tasks, return_exceptions=True)

        # 记录失败的适配器并从列表中移除
        failed_adapters = []
        for i, result in enumerate(register_results):
            adapter_name = adapters[i]
            if isinstance(result, BaseException) or result is False:
                logger.warning(f"适配器 {adapter_name} 注册失败，已跳过")
                failed_adapters.append(adapter_name)

        for name in failed_adapters:
            if name in adapters:
                adapters.remove(name)

        return True
