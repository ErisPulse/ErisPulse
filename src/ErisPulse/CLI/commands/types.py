"""
Types 命令实现

扫描已安装的模块/适配器，生成带类型提示的存根文件，
让 IDE 能补全平台特有的发送方法和模块方法。

{!--< tips >!--}
1. 通过 entry-points 发现所有已安装的模块/适配器
2. 导入类并内省其公开方法（适配器含 Send 子类）
3. 在当前目录生成 ``_ep_types.py``，提供类型化的访问器
4. 用户 ``from _ep_types import adapter, module`` 即可获得精确补全
{!--< /tips >!--}
"""

from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from rich.panel import Panel

from ..base import Command
from ..console import console
from ..constants import ADAPTER_ENTRY_POINT_GROUP, MODULE_ENTRY_POINT_GROUP
from ..i18n import i18n

# 生成文件名（带前导下划线，避免与用户业务模块冲突）
STUB_FILENAME = "_ep_types.py"

# 存根文件头部说明
_STUB_HEADER = '''"""
ErisPulse 类型存根（自动生成，请勿手动编辑）

由 `epsdk types` 命令根据已安装的模块/适配器生成。
仅导出类型供用户代码作为变量标注使用，**不提供任何运行时实例**。
所有导入都在 ``TYPE_CHECKING`` 下，运行时零开销、零行为改变。

使用方式：
    from _ep_types import MyModule, Yunhu
    from ErisPulse import sdk

    # 用导入的类型标注变量，即可获得 IDE 补全
    my_mod: MyModule = sdk.module.get("MyModule")
    my_mod.hello()                       # ← IDE 能补全 hello

    my_adapter: Yunhu = sdk.adapter.get("yunhu")
    await my_adapter.Send.To("group", "123").Board(...)  # ← 补全平台特有方法

说明：
    - 类型名采用 entry-point 名的 PascalCase 形式（如 ``yunhu`` → ``Yunhu``），
      与传入 ``sdk.adapter.get()`` / ``sdk.module.get()`` 的名称对应
    - 存根仅用于静态类型检查，不含运行时实现
    - 安装/卸载模块/适配器后请重新生成：``epsdk types``
"""
'''

# 排除内省的方法名（来自基类、Python 内置、下划线开头）
_EXCLUDE_METHOD_NAMES = frozenset({
    # SendDSL 链式修饰方法（基类已有，无需在存根重复声明）
    "At", "AtAll", "Reply", "To", "Using", "Account",
    "Hook", "Retry", "Timeout", "Defer", "Priority", "PriorityThreshold",
    "OnProgress", "OnError", "Build",
    # 基类标准发送方法（已在 SendDSL 声明）
    "Text", "Image", "Voice", "Video", "File", "Raw_ob12", "Example",
    # 非发送成员
    "send_context", "Raw",
})


def _is_send_method(name: str, func: Any) -> bool:
    """
    判断一个类属性是否是"发送方法"

    发送方法的特征：公开（非下划线开头）、可调用、不在排除集合中。

    :param name: 属性名
    :param func: 属性值
    :return: 是否为发送方法
    """
    if name.startswith("_"):
        return False
    if name in _EXCLUDE_METHOD_NAMES:
        return False
    return callable(func)


def _is_module_method(name: str, func: Any) -> bool:
    """
    判断一个类属性是否是模块的公开方法

    :param name: 属性名
    :param func: 属性值
    :return: 是否为公开方法
    """
    if name.startswith("_"):
        return False
    if name in ("cfg", "sdk", "logger", "storage", "adapter", "router",
                "on_load", "on_unload", "on_config_update", "get_load_strategy"):
        return False
    return callable(func)


def _safe_type_name(cls: type, fallback: str) -> str:
    """
    获取类的类型名用于存根导入，处理无法导入的情况

    :param cls: 类对象
    :param fallback: 无法确定时的兜底名
    :return: 存根中使用的类型名
    """
    module = getattr(cls, "__module__", None)
    qualname = getattr(cls, "__qualname__", None)
    if module and qualname and "<" not in qualname:
        # 模块名 + 限定名，用于 import
        return f"{module}:{qualname}"
    return fallback


def _build_send_class_stub(send_cls: type) -> str:
    """
    为适配器的 Send 子类构造存根代码

    扫描 Send 类的平台特有方法，生成继承 SendDSL 的子类声明。

    :param send_cls: Send 类对象
    :return: 存根代码片段
    """
    # 收集平台特有的发送方法
    platform_methods = []
    for name in dir(send_cls):
        if name in _EXCLUDE_METHOD_NAMES:
            continue
        if name.startswith("_"):
            continue
        try:
            func = getattr(send_cls, name)
        except Exception:
            continue
        if not callable(func):
            continue
        platform_methods.append(name)

    if not platform_methods:
        return ""

    # 生成方法签名（使用 Any 简化，重点在于让 IDE 知道方法存在）
    lines = [
        f"    def {name}(self, *args: Any, **kwargs: Any) -> Any: ..."
        for name in sorted(platform_methods)
    ]
    return "\n".join(lines)


def _pascal_case_ep_name(name: str) -> str:
    """
    将 entry-point 名转换为 PascalCase 类型名

    处理各种命名风格：
    - ``yunhu`` → ``Yunhu``
    - ``MyModule`` → ``MyModule``（保持原样）
    - ``my_adapter`` → ``MyAdapter``
    - ``ErisPulse-Dashboard`` → ``ErisPulseDashboard``

    :param name: entry-point 名称
    :return: PascalCase 类型名
    """
    # 先按非字母数字字符分割，再按内部小写-大写边界分割
    parts: list[str] = []
    for raw_part in name.replace("-", "_").replace(".", "_").split("_"):
        if not raw_part:
            continue
        # 处理 "ErisPulse" 这样的驼峰：拆分为 Eris / Pulse
        sub_parts: list[str] = []
        current = ""
        prev_lower = False
        for ch in raw_part:
            if ch.isupper() and prev_lower:
                if current:
                    sub_parts.append(current)
                current = ch
            else:
                current += ch
            prev_lower = ch.islower()
        if current:
            sub_parts.append(current)
        parts.extend(sub_parts)

    if not parts:
        # 兑底：首字母大写
        return name[:1].upper() + name[1:]

    return "".join(p[:1].upper() + p[1:] for p in parts if p)


class TypesCommand(Command):
    """
    types 命令

    生成 ErisPulse 模块/适配器的类型存根文件，启用 IDE 补全。
    """

    name = "types"
    description = i18n.t("cli.types.description")
    aliases = ["t", "stub"]

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--output", "-o",
            default=None,
            help=i18n.t("cli.types.output_help"),
        )
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help=i18n.t("cli.types.force_help"),
        )
        parser.add_argument(
            "--adapters-only",
            action="store_true",
            default=False,
            help=i18n.t("cli.types.adapters_only_help"),
        )
        parser.add_argument(
            "--modules-only",
            action="store_true",
            default=False,
            help=i18n.t("cli.types.modules_only_help"),
        )

    def execute(self, args):
        output_path = Path(args.output) if args.output else Path.cwd() / STUB_FILENAME

        # 检查文件是否已存在
        if output_path.exists() and not args.force:
            console.print(
                f"[warning]{i18n.t('cli.types.exists', path=output_path)}[/]"
            )
            console.print(
                f"[info]{i18n.t('cli.types.use_force')}[/]"
            )
            return

        scan_adapters = not args.modules_only
        scan_modules = not args.adapters_only

        # 收集适配器与模块信息
        adapters_info = []
        modules_info = []

        if scan_adapters:
            adapters_info = self._collect_adapters()

        if scan_modules:
            modules_info = self._collect_modules()

        if not adapters_info and not modules_info:
            console.print(f"[warning]{i18n.t('cli.types.no_components')}[/]")
            return

        # 生成存根内容
        stub_content = self._generate_stub(adapters_info, modules_info)

        # 写入文件
        try:
            with output_path.open("w", encoding="utf-8") as f:
                f.write(stub_content)
        except OSError as e:
            console.print(
                f"[error]{i18n.t('cli.types.write_failed', error=e)}[/]"
            )
            return

        # 输出结果
        adapter_count = len(adapters_info)
        module_count = len(modules_info)
        console.print(
            Panel(
                i18n.t(
                    "cli.types.success_panel",
                    path=output_path,
                    adapters=adapter_count,
                    modules=module_count,
                ),
                title=i18n.t("cli.types.success_title"),
                border_style="success",
            )
        )

        # 提示用法
        console.print(f"\n[info]{i18n.t('cli.types.usage_hint')}[/]")
        console.print(f"  [dim]{i18n.t('cli.types.usage_example')}[/]")

    def _collect_adapters(self) -> list[dict]:
        """
        扫描所有已安装的适配器，收集类型信息

        :return: 适配器信息列表
            [{"name": str, "class": type, "module_path": str, "qualname": str}, ...]
        """
        from ..utils import PackageManager

        target_python = PackageManager()._get_target_python()
        raw_entries = self._introspect_remote(
            target_python, ADAPTER_ENTRY_POINT_GROUP, kind="adapter"
        )
        results = [
            {
                "name": d["name"],
                "class": None,  # 跨环境下不加载实际类，使用下述字段生成存根
                "module_path": d["module_path"],
                "qualname": d["qualname"],
                "send_methods": d.get("send_methods", []),
            }
            for d in raw_entries
        ]
        return results

    def _collect_modules(self) -> list[dict]:
        """
        扫描所有已安装的模块，收集类型信息

        :return: 模块信息列表
            [{"name": str, "class": type, "module_path": str, "qualname": str, "methods": list[str]}, ...]
        """
        from ..utils import PackageManager

        target_python = PackageManager()._get_target_python()
        raw_entries = self._introspect_remote(
            target_python, MODULE_ENTRY_POINT_GROUP, kind="module"
        )
        results = [
            {
                "name": d["name"],
                "class": None,
                "module_path": d["module_path"],
                "qualname": d["qualname"],
                "methods": d.get("methods", []),
            }
            for d in raw_entries
        ]
        return results

    def _introspect_remote(
        self, python_executable: str, group: str, kind: str
    ) -> list[dict]:
        """
        在目标 Python 环境中内省 entry-points 及其类信息

        通过子进程在目标环境中加载 entry-point 引用的类，提取内省信息
        （模块路径、限定名、平台特有的发送方法名、模块的公开方法名）。
        这样无论是当前环境还是跨环境场景，都能正确采集类型信息。

        :param python_executable: [str] 目标 Python 解释器路径
        :param group: [str] entry-point 组名
        :param kind: [str] "adapter" 或 "module"，决定内省内容
        :return: [list[dict]] 内省结果列表
        """
        import json
        import subprocess

        script = self._build_introspect_script(group, kind)
        try:
            result = subprocess.run(
                [python_executable, "-c", script],
                capture_output=True,
                timeout=60,
                text=True,
                check=False,
            )
        except Exception as e:
            console.print(
                f"[error]{i18n.t('cli.types.introspect_failed', error=e)}[/]"
            )
            return []

        if result.returncode != 0:
            console.print(
                f"[error]{i18n.t('cli.types.introspect_failed', error=result.stderr.strip())}[/]"
            )
            return []

        try:
            return json.loads(result.stdout)
        except Exception as e:
            console.print(
                f"[error]{i18n.t('cli.types.introspect_failed', error=e)}[/]"
            )
            return []

    @staticmethod
    def _build_introspect_script(group: str, kind: str) -> str:
        """
        构造在目标环境中运行的内省脚本

        :param group: [str] entry-point 组名
        :param kind: [str] "adapter" 或 "module"
        :return: [str] Python 脚本字符串
        """
        # 排除基类已有或不应作为公开 API 的属性名
        excludes = [
            "At", "AtAll", "Reply", "To", "Using", "Account",
            "Hook", "Retry", "Timeout", "Defer", "Priority", "PriorityThreshold",
            "OnProgress", "OnError", "Build",
            "Text", "Image", "Voice", "Video", "File", "Raw_ob12", "Example",
            "send_context", "Raw",
            "cfg", "sdk", "logger", "storage", "adapter", "router",
            "on_load", "on_unload", "on_config_update", "get_load_strategy",
        ]

        # 根据类型决定附加内省逻辑（在 for 循环体内、4 空格缩进处插入）
        if kind == "adapter":
            extra_block = (
                "    send_methods = []\n"
                "    send_cls = getattr(loaded, 'Send', None)\n"
                "    if send_cls is not None:\n"
                "        for n in dir(send_cls):\n"
                "            if n.startswith('_') or n in excludes:\n"
                "                continue\n"
                "            try:\n"
                "                attr = getattr(send_cls, n)\n"
                "            except Exception:\n"
                "                continue\n"
                "            if callable(attr):\n"
                "                send_methods.append(n)\n"
                "    item['send_methods'] = sorted(send_methods)\n"
            )
        else:
            extra_block = (
                "    methods = []\n"
                "    for n in dir(loaded):\n"
                "        if n.startswith('_') or n in excludes:\n"
                "            continue\n"
                "        try:\n"
                "            attr = getattr(loaded, n)\n"
                "        except Exception:\n"
                "            continue\n"
                "        if callable(attr):\n"
                "            methods.append(n)\n"
                "    item['methods'] = sorted(methods)\n"
            )

        # 脚本主体：所有循环体使用 4/8/12 空格缩进
        return "\n".join([
            "import json, importlib.metadata",
            f"excludes = {excludes!r}",
            "eps = importlib.metadata.entry_points()",
            "if hasattr(eps, 'select'):",
            f"    entries = list(eps.select(group={group!r}))",
            "else:",
            f"    entries = list(eps.get({group!r}, []))",
            "out = []",
            "for e in entries:",
            "    item = {'name': e.name, 'value': e.value}",
            "    try:",
            "        loaded = e.load()",
            "    except Exception as ex:",
            "        item['error'] = str(ex)",
            "        item['module_path'] = e.value.split(':')[0] if ':' in e.value else ''",
            "        item['qualname'] = e.value.split(':')[-1] if ':' in e.value else e.name",
            "        out.append(item)",
            "        continue",
            "    import inspect as _inspect",
            "    if not _inspect.isclass(loaded):",
            "        continue",
            "    item['module_path'] = getattr(loaded, '__module__', '')",
            "    item['qualname'] = getattr(loaded, '__qualname__', e.name)",
            # 以下是类型相关的内省逻辑（4 空格缩进内的语句，内级语句需要 12 空格）
            extra_block.rstrip("\n"),
            "    out.append(item)",
            "print(json.dumps(out))",
            "",  # 末尾换行
        ])

    def _generate_stub(
        self,
        adapters_info: list[dict],
        modules_info: list[dict],
    ) -> str:
        """
        生成完整的存根文件内容

        仅提供类型导入供用户作为变量标注使用，不导出任何实例。
        用户自行调用 ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` 获取实例，
        并用本文件导入的类型作为变量类型注解，从而获得 IDE 补全。

        所有导入都在 ``TYPE_CHECKING`` 下，运行时零开销、零行为改变。

        :param adapters_info: 适配器信息
        :param modules_info: 模块信息
        :return: 存根文件内容
        """
        lines = [_STUB_HEADER.rstrip(), ""]
        lines.append("from typing import TYPE_CHECKING")
        lines.append("")
        lines.append("if TYPE_CHECKING:")
        lines.append("    # 以下类型导入仅在 IDE / 类型检查器中生效，不会被运行时执行。")
        lines.append("    # 在用户代码中通过 ``from _ep_types import XxxModule`` 获取类型，")
        lines.append("    # 配合 ``my_mod: XxxModule = sdk.module.get('XxxModule')`` 获得补全。")
        lines.append("")

        export_names: list[str] = []
        seen_imports: set[str] = set()  # 去重完全相同的导入语句

        def _add_import(module_path: str, qualname: str, ep_name: str):
            """添加一个类型导入行，自动跳过重复"""
            class_name = qualname.rsplit(".", maxsplit=1)[-1]
            alias = _pascal_case_ep_name(ep_name)
            stmt = f"    from {module_path} import {class_name} as {alias}"
            if stmt in seen_imports:
                return  # 完全相同的导入已存在，跳过
            seen_imports.add(stmt)
            lines.append(stmt)
            export_names.append(alias)

        # ==================== 导入适配器类 ====================
        if adapters_info:
            lines.append("    # ===== 适配器（名称与 sdk.adapter.get() 参数一致）=====")
            for info in adapters_info:
                if info["module_path"]:
                    _add_import(info["module_path"], info["qualname"], info["name"])
            lines.append("")

        # ==================== 导入模块类 ====================
        if modules_info:
            lines.append("    # ===== 模块（名称与 sdk.module.get() 参数一致）=====")
            for info in modules_info:
                if info["module_path"]:
                    _add_import(info["module_path"], info["qualname"], info["name"])
            lines.append("")

        # __all__ 提示导出名称，IDE 会优先提示这些名称
        if export_names:
            # 去重（多个入口点可能映射到同一个类，例如同名适配器与模块）
            seen = set()
            unique_names = []
            for n in export_names:
                if n not in seen:
                    seen.add(n)
                    unique_names.append(n)
            quoted = ", ".join(repr(n) for n in unique_names)
            lines.append(f"    __all__ = [{quoted}]")
            lines.append("")

        return "\n".join(lines)
