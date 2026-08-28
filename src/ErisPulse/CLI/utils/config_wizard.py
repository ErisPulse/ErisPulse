"""
ErisPulse CLI 配置向导共享工具

基于声明式配置（ConfigClass / AccountConfigClass）生成 schema 驱动的
交互式表单，供 ``epsdk config`` 命令与 install / init 安装后衔接复用。

模块与适配器共用同一套渲染逻辑；适配器额外包含多账户（bot 账户）配置环节。

{!--< tips >!--}
1. load_config_targets() 发现所有可配置目标（entry-points + 本地 plugins/）
2. get_target_status() 检查目标的配置状态（未配置/必填缺失/就绪）
3. run_wizard() 对单个目标运行交互式配置向导并写入 config.toml
4. post_install_configure() 在安装包后衔接配置引导
{!--< /tips >!--}
"""

import importlib
import re
import sys
from types import SimpleNamespace
from typing import Literal

from rich.prompt import Confirm, Prompt

# Core i18n 单例：用于将字段 description/placeholder 解析为 CLI 同语言
from ErisPulse.Core.i18n import i18n as _core_i18n

from ..console import console
from ..i18n import i18n
from .display import section_header

# 配置状态常量
STATUS_OK = "ok"
STATUS_INCOMPLETE = "incomplete"
STATUS_UNCONFIGURED = "unconfigured"
STATUS_NONE = "none"


def _normalize_dist_name(name: str | None) -> str:
    """
    按 PEP 503 规范化 PyPI 发行包名称

    大小写不敏感，``-`` / ``_`` / ``.`` 连续序列统一为单个 ``-``，
    用于安装包名与 entry-point 所属包名的宽松匹配。

    :param name: 原始包名
    :return: 规范化后的包名
    """
    return re.sub(r"[-_.]+", "-", (name or "").strip()).lower()


def is_interactive() -> bool:
    """
    检测当前是否处于可交互的终端环境

    :return: stdin 与 stdout 均为 TTY 时返回 True
    """
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


class ConfigTarget:
    """
    可配置目标（适配器或模块）的元信息

    仅承载类级别的声明信息（ConfigClass / AccountConfigClass），
    不实例化目标类，避免在 CLI 上下文触发配置模板生成等副作用。
    """

    def __init__(
        self,
        kind: Literal["adapter", "module"],
        name: str,
        *,
        config_class=None,
        account_class=None,
        config_key: str = "",
        package: str | None = None,
        source: str = "entrypoint",
    ):
        """
        :param kind: 目标类型："adapter" | "module"
        :param name: 目标名（适配器为平台名，模块为注册名）
        :param config_class: ConfigClass 声明（未声明为 None）
        :param account_class: AccountConfigClass 声明（仅适配器，未声明为 None）
        :param config_key: 配置存储键（适配器默认类名，模块为注册名）
        :param package: 所属 PyPI 包名（本地插件为 None）
        :param source: 来源："entrypoint" | "plugins"
        """
        self.kind = kind
        self.name = name
        self.config_class = config_class
        self.account_class = account_class
        self.config_key = config_key or name
        self.package = package
        self.source = source

    @property
    def configurable(self) -> bool:
        """是否包含任何配置声明"""
        return self.config_class is not None or self.account_class is not None

    @property
    def kind_label(self) -> str:
        """目标类型显示名（适配器/模块）"""
        return i18n.t("cli.config.kind_adapter" if self.kind == "adapter" else "cli.config.kind_module")


def _resolve_adapter_config_key(cls) -> str:
    """
    在不实例化适配器类的前提下解析其配置键

    默认实现（继承自 BaseAdapter）返回类名；子类覆写 ``_get_config_key``
    时以伪 self 对象调用（大多数覆写是 self 属性的纯函数），
    调用失败则回退类名。

    :param cls: 适配器类
    :return: 配置键名字符串
    """
    from ErisPulse.Core.Bases.adapter import BaseAdapter

    if getattr(cls, "_get_config_key", None) is BaseAdapter._get_config_key:
        return cls.__name__
    try:
        sentinel = SimpleNamespace(__class__=cls)
        result = cls._get_config_key(sentinel)
        if isinstance(result, str) and result:
            return result
    except Exception:
        pass
    return cls.__name__


def _target_from_class(kind: str, name: str, cls, package=None, source="entrypoint") -> ConfigTarget | None:
    """
    从目标类构造 ConfigTarget（读取类属性声明，不实例化）

    :param kind: 目标类型
    :param name: 目标名
    :param cls: 适配器/模块类
    :param package: 所属包名
    :param source: 来源标识
    :return: ConfigTarget；类不合法时返回 None
    """
    try:
        config_class = getattr(cls, "ConfigClass", None)
        account_class = getattr(cls, "AccountConfigClass", None)
        if kind == "adapter":
            config_key = _resolve_adapter_config_key(cls)
        else:
            config_key = name
        return ConfigTarget(
            kind=kind,
            name=name,
            config_class=config_class,
            account_class=account_class,
            config_key=config_key,
            package=package,
            source=source,
        )
    except Exception:
        return None


def _plugin_module_class(module_obj) -> type | None:
    """
    从本地插件模块对象中提取模块类

    :param module_obj: 插件模块对象（声明 ``moduleInfo`` 字典）
    :return: 模块类；未声明或类型不合法时返回 None
    """
    module_info = getattr(module_obj, "moduleInfo", None)
    if not isinstance(module_info, dict):
        return None
    cls = module_info.get("module_class")
    return cls if isinstance(cls, type) else None


def load_config_targets() -> list[ConfigTarget]:
    """
    发现当前环境中所有可配置目标

    覆盖 entry-points（``erispulse.adapter`` / ``erispulse.module`` 组）
    与本地插件目录（``plugins/``）。加载失败的条目跳过并提示。

    :return: ConfigTarget 列表（含未声明配置的目标，调用方按需过滤）
    """
    targets: list[ConfigTarget] = []

    from ErisPulse.finders import AdapterFinder, ModuleFinder

    try:
        for entry in AdapterFinder().find_all():
            dist_name = getattr(entry.dist, "name", None) if getattr(entry, "dist", None) else None
            try:
                cls = entry.load()
            except Exception as e:
                console.print(f"[warning]  {i18n.t('cli.config.load_failed', name=entry.name, error=e)}[/]")
                continue
            target = _target_from_class("adapter", entry.name, cls, package=dist_name)
            if target is not None:
                targets.append(target)
    except Exception as e:
        console.print(f"[warning]  {i18n.t('cli.config.discover_failed', kind='adapter', error=e)}[/]")

    try:
        for entry in ModuleFinder().find_all():
            dist_name = getattr(entry.dist, "name", None) if getattr(entry, "dist", None) else None
            try:
                cls = entry.load()
            except Exception as e:
                console.print(f"[warning]  {i18n.t('cli.config.load_failed', name=entry.name, error=e)}[/]")
                continue
            target = _target_from_class("module", entry.name, cls, package=dist_name)
            if target is not None:
                targets.append(target)
    except Exception as e:
        console.print(f"[warning]  {i18n.t('cli.config.discover_failed', kind='module', error=e)}[/]")

    try:
        from ErisPulse.loaders.plugin_folder import PluginFolderLoader

        for name, module_obj in PluginFolderLoader().discover().items():
            module_class = _plugin_module_class(module_obj)
            if module_class is None:
                continue
            target = _target_from_class("module", name, module_class, source="plugins")
            if target is not None:
                targets.append(target)
    except Exception as e:
        console.print(f"[warning]  {i18n.t('cli.config.discover_failed', kind='plugins', error=e)}[/]")

    return targets


def get_target_status(target: ConfigTarget, config=None) -> tuple[str, list[str]]:
    """
    检查目标的配置状态

    :param target: ConfigTarget
    :param config: ConfigManager 实例（None 时使用全局单例）
    :return: (状态, 错误列表)。状态取值：
        - ok：已配置且校验通过
        - incomplete：必填项缺失或校验失败
        - unconfigured：配置键不存在（从未生成）
        - none：目标未声明任何配置
    """
    if not target.configurable:
        return STATUS_NONE, []

    if config is None:
        import ErisPulse

        config = ErisPulse.config

    errors: list[str] = []
    has_any_data = False

    if target.config_class is not None:
        from ErisPulse.Core.Bases.config_schema import dict_to_dataclass, validate_config

        data = config.getConfig(target.config_key)
        if data is None:
            return STATUS_UNCONFIGURED, []
        has_any_data = True
        errors.extend(validate_config(dict_to_dataclass(target.config_class, data)))

    if target.account_class is not None:
        from ErisPulse.Core.Bases.config_schema import dict_to_dataclass, validate_config

        key = f"{target.config_key}.accounts"
        if config.getConfig(key) is None:
            key = f"{target.config_key}.bots"
        accounts = config.getConfig(key)
        if accounts is None:
            accounts = {}
        else:
            has_any_data = True
        if not accounts:
            errors.append(i18n.t("cli.config.no_accounts"))
        for account_name, account_data in accounts.items():
            if not isinstance(account_data, dict):
                continue
            account_errors = validate_config(dict_to_dataclass(target.account_class, account_data))
            errors.extend(f"[{account_name}] {e}" for e in account_errors)

    if not has_any_data:
        return STATUS_UNCONFIGURED, []
    if errors:
        return STATUS_INCOMPLETE, errors
    return STATUS_OK, []


def _sort_fields(schema_fields: dict) -> list[tuple[str, dict]]:
    """
    按 schema 的 order 元数据稳定排序字段（未声明 order 的保持声明顺序靠前）

    :param schema_fields: get_config_schema()["fields"] 字典
    :return: (字段名, 字段 schema) 列表
    """
    indexed = list(enumerate(schema_fields.items()))
    indexed.sort(key=lambda pair: (pair[1][1].get("order", 10_000), pair[0]))
    return [item for _, item in indexed]


def _coerce_scalar(raw: str, type_name: str):
    """
    将用户输入字符串转换为目标类型的标量值

    :param raw: 原始输入
    :param type_name: TOML 类型名（integer/float/boolean/string）
    :return: 转换后的值；无法转换时抛出 ValueError
    """
    if type_name == "integer":
        return int(raw)
    if type_name == "float":
        return float(raw)
    if type_name == "boolean":
        return raw.lower() in ("true", "1", "yes", "on", "y", "t")
    return raw


def _plain_options(options: list) -> list:
    """
    提取 select 选项的纯值列表（兼容字符串与 {label, value} 字典两种格式）

    :param options: schema 中的 options 列表
    :return: 选项值列表
    """
    return [o.get("value") if isinstance(o, dict) else o for o in options]


def _option_label(option) -> str:
    """
    获取 select 选项的显示标签

    :param option: 单个选项（字符串或 {label, value} 字典）
    :return: 标签字符串
    """
    if isinstance(option, dict):
        label = option.get("label", "")
        value = option.get("value", "")
        return f"{label} ({value})" if label and str(label) != str(value) else str(value)
    return str(option)


def _with_source(label: str, source: str) -> str:
    """
    在 label 行尾追加来源标注（当前值 / 默认值）

    :param label: 已构造的字段标签行
    :param source: 来源标注文本（空则不追加）
    :return: 带标注的显示文本
    """
    if source:
        return f"{label} [dim]({source})[/]"
    return label


def _source_label(has_value: bool, value, bool_text: str = "") -> str:
    """
    生成字段值来源标注文本（当前值 / 默认值）

    :param has_value: 字段是否已有当前配置值（存储中存在）
    :param value: 值（布尔传入 bool_text 已本地化）
    :param bool_text: 布尔值本地化"是/否"文本
    :return: 标注字符串；无值则返回空串
    """
    if has_value:
        text = bool_text or (value if value not in (None, "") else "")
        if not text:
            return ""
        return i18n.t("cli.config.value_current", value=text)
    if value not in (None, ""):
        return i18n.t("cli.config.value_default", value=value)
    return ""


def _prompt_field(name: str, field_schema: dict, current, has_value: bool = False):
    """
    交互式询问单个配置字段的值

    按 widget / 类型渲染控件（password / select / switch / 数值 / 文本），
    输入即时校验（options / min / max / required），非法时重新询问；
    空输入表示保留当前值（secret 字段不回显当前值）。
    值来源（已有配置 / schema 默认）以 ``(当前：x)`` / ``(默认：x)`` 标注。

    :param name: 字段名
    :param field_schema: 字段 schema（来自 resolve_config_schema）
    :param current: 当前值（默认值兜底为 schema default）
    :param has_value: 字段是否已有当前配置值（决定标注"当前"/"默认"）
    :return: 用户确认后的字段值
    """
    type_name = field_schema.get("type", "string")
    widget = field_schema.get("widget", "")
    required = field_schema.get("required", False)
    secret = field_schema.get("secret", False)
    description = field_schema.get("description", "")
    placeholder = field_schema.get("placeholder", "")
    options = field_schema.get("options")

    if current is None or current == "":
        current = field_schema.get("default", "")
        if current is None:
            current = ""

    desc_parts = [name]
    if description:
        desc_parts.append(str(description))
    if required:
        desc_parts.append(i18n.t("cli.config.required_mark"))
    label = "  - " + "：".join(desc_parts)

    def _error(msg: str):
        console.print(f"[error]    {msg}[/]")

    while True:
        # switch / boolean → Confirm 控件
        if type_name == "boolean":
            bool_val = bool(current)
            bool_text = i18n.t("cli.config.yn_yes") if bool_val else i18n.t("cli.config.yn_no")
            print_label = _with_source(label, _source_label(has_value, current, bool_text))
            console.print(print_label)
            # prompt 用字段名（"是否启用 {name}？"），避免与 label 描述重复
            return Confirm.ask(
                f"    {i18n.t('cli.config.enable_prompt', name=name)}",
                default=bool_val,
            )

        # select → 编号选项
        if widget == "select" and options:
            plain = _plain_options(options)
            print_label = _with_source(label, _source_label(has_value, current))
            console.print(print_label)
            for idx, opt in enumerate(options, 1):
                marker = "[cyan]●[/] " if _values_equal(current, plain[idx - 1]) else "  "
                console.print(f"    {marker}{idx}. {_option_label(opt)}")
            default_idx = 1
            for idx, value in enumerate(plain, 1):
                if _values_equal(current, value):
                    default_idx = idx
                    break
            raw = Prompt.ask(
                f"    {i18n.t('cli.config.select_option')}",
                default=str(default_idx),
                choices=[str(i) for i in range(1, len(plain) + 1)],
            )
            return plain[int(raw) - 1]

        # password → 隐藏输入，空输入保留当前值
        if widget == "password" or (secret and type_name == "string"):
            hint = i18n.t("cli.config.secret_set") if str(current) else (placeholder or "")
            console.print(f"{label} [dim]{hint}[/]")
            raw = Prompt.ask(f"    {name}", password=True, default="", show_default=False)
            if raw:
                return raw
            if str(current):
                return current
            if not required:
                return current
            _error(i18n.t("cli.config.field_required_empty", field=name))
            continue

        # 数值 / 文本
        default_str = "" if current is None else str(current)
        source = _source_label(has_value, current)
        shown = source or placeholder or ""
        print_label = _with_source(label, shown)
        console.print(print_label)
        raw = Prompt.ask(f"    {name}", default=default_str, show_default=False)

        if raw == "":
            value = current
        else:
            try:
                value = _coerce_scalar(raw, type_name)
            except ValueError:
                _error(i18n.t("cli.config.field_type_invalid", field=name, expected=type_name))
                continue

        # options / min / max 校验（空值留给 required 检查）
        if value not in (None, ""):
            if options:
                plain = _plain_options(options)
                if not any(_values_equal(value, o) for o in plain):
                    _error(i18n.t("cli.config.field_option_invalid", field=name))
                    continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                min_val = field_schema.get("min")
                max_val = field_schema.get("max")
                if min_val is not None and value < min_val:
                    _error(i18n.t("cli.config.field_below_min", field=name, min=min_val))
                    continue
                if max_val is not None and value > max_val:
                    _error(i18n.t("cli.config.field_above_max", field=name, max=max_val))
                    continue

        if required and (value is None or value == ""):
            _error(i18n.t("cli.config.field_required_empty", field=name))
            continue

        return value


def _values_equal(a, b) -> bool:
    """
    宽松比较两个标量是否相等（容忍 int/str 形式差异）

    :param a: 值 a
    :param b: 值 b
    :return: 是否相等
    """
    if a == b:
        return True
    try:
        return str(a) == str(b)
    except Exception:
        return False


def fill_config_fields(config_class, current_values: dict) -> dict:
    """
    渲染整个配置类的表单并收集用户输入

    :param config_class: dataclass 配置类
    :param current_values: 当前存储的配置字典（作为各字段初值）
    :return: 收集后的配置字典
    """
    from ErisPulse.Core.Bases.config_schema import resolve_config_schema

    schema = resolve_config_schema(config_class)
    current_store = dict(current_values or {})
    values = dict(current_store)
    for name, field_schema in _sort_fields(schema.get("fields", {})):
        has_value = name in current_store
        values[name] = _prompt_field(name, field_schema, values.get(name), has_value)
    return values


def _validate_dataclass(config_class, data: dict) -> list[str]:
    """
    校验字典是否能通过配置类的完整约束

    :param config_class: dataclass 配置类
    :param data: 配置字典
    :return: 错误列表（空列表表示通过）
    """
    from ErisPulse.Core.Bases.config_schema import dict_to_dataclass, validate_config

    return validate_config(dict_to_dataclass(config_class, data))


def _prompt_account_name(existing: dict, default: str = "") -> str | None:
    """
    询问新的账户名（非空且不与现有账户重名）

    :param existing: 现有账户字典
    :param default: 默认账户名
    :return: 合法账户名；用户中断返回 None
    """
    while True:
        try:
            raw = Prompt.ask(
                f"    {i18n.t('cli.config.account_name_prompt')}",
                default=default,
                show_default=False,
            )
        except (EOFError, KeyboardInterrupt):
            return None
        name = raw.strip()
        if not name:
            # 空输入视为取消本次新增，返回菜单
            return None
        if name in existing:
            console.print(f"[error]    {i18n.t('cli.config.account_name_exists', name=name)}[/]")
            continue
        return name


def _pick_account_name(names: list[str]) -> str | None:
    """
    从账户名列表中交互选择一个账户

    显示 ``1. xxx`` 编号列表，输入序号选择；空输入返回（None），
    非法序号重新询问。

    :param names: 账户名列表
    :return: 选中的账户名；用户留空/中断返回 None
    """
    for idx, name in enumerate(names, 1):
        console.print(f"    {idx}. {name}")
    while True:
        try:
            raw = Prompt.ask(
                f"    {i18n.t('cli.config.account_select')}",
                default="",
                show_default=False,
            )
        except (EOFError, KeyboardInterrupt):
            return None
        if not raw.strip():
            return None
        try:
            idx = int(raw.strip())
        except ValueError:
            continue
        if 1 <= idx <= len(names):
            return names[idx - 1]


def _resolve_accounts_key(target: ConfigTarget, config) -> str:
    """
    解析适配器多账户配置的存储键

    新键为 ``<config_key>.accounts``；旧版使用 ``<config_key>.bots``，
    仅当新键不存在而旧键存在时回退（兼容既有 config.toml）。

    :param target: 适配器 ConfigTarget
    :param config: ConfigManager 实例
    :return: 账户配置存储键
    """
    accounts_key = f"{target.config_key}.accounts"
    if config.getConfig(accounts_key) is None and config.getConfig(f"{target.config_key}.bots") is not None:
        return f"{target.config_key}.bots"
    return accounts_key


def _run_accounts_section(target: ConfigTarget, config) -> dict:
    """
    运行多账户配置环节（添加 / 编辑 / 删除循环）

    :param target: 适配器 ConfigTarget
    :param config: ConfigManager 实例
    :return: 编辑后的账户字典 {账户名: 字段字典}
    """
    key = _resolve_accounts_key(target, config)

    accounts: dict = dict(config.getConfig(key) or {})
    # 规范类型：忽略非 dict 条目
    accounts = {n: dict(d) for n, d in accounts.items() if isinstance(d, dict)}

    while True:
        section_header(i18n.t("cli.config.accounts_section"))
        if accounts:
            for account_name, data in accounts.items():
                state = (
                    i18n.t("cli.config.account_on") if data.get("enabled", True) else i18n.t("cli.config.account_off")
                )
                console.print(f"    [cyan]{account_name}[/] [dim]({state})[/]")
        else:
            console.print(f"    [dim]{i18n.t('cli.config.no_accounts')}[/]")

        console.print(f"    1. {i18n.t('cli.config.accounts_add')}")
        console.print(f"    2. {i18n.t('cli.config.accounts_edit')}")
        console.print(f"    3. {i18n.t('cli.config.accounts_delete')}")
        console.print(f"    4. {i18n.t('cli.config.accounts_done')}")

        try:
            choice = Prompt.ask(
                f"  {i18n.t('cli.config.select_option')}",
                default="4",
                choices=["1", "2", "3", "4"],
            )
        except (EOFError, KeyboardInterrupt):
            choice = "4"

        if choice == "4" or (not accounts and choice in ("2", "3")):
            if choice in ("2", "3"):
                console.print(f"    [dim]{i18n.t('cli.config.no_accounts')}[/]")
                continue
            break

        if choice == "1":
            name = _prompt_account_name(accounts)
            if name is None:
                continue
            # 仅传入用户刚输入的账户名：name 标注"当前"，其余字段由 schema
            # default 兜底并标注"默认"（避免整包默认值被误标为已有配置）
            values = fill_config_fields(target.account_class, {"name": name})
            errors = _validate_dataclass(target.account_class, values)
            if errors:
                console.print(f"[error]    {i18n.t('cli.config.validation_failed', errors='; '.join(errors))}[/]")
                continue
            accounts[name] = values
            console.print(f"[success]    {i18n.t('cli.config.account_added', name=name)}[/]")

        elif choice == "2":
            account_name = _pick_account_name(list(accounts.keys()))
            if account_name is None:
                continue
            values = fill_config_fields(target.account_class, accounts[account_name])
            errors = _validate_dataclass(target.account_class, values)
            if errors:
                console.print(f"[error]    {i18n.t('cli.config.validation_failed', errors='; '.join(errors))}[/]")
                continue
            accounts[account_name] = values
            console.print(f"[success]    {i18n.t('cli.config.account_saved', name=account_name)}[/]")

        elif choice == "3":
            account_name = _pick_account_name(list(accounts.keys()))
            if account_name is None:
                continue
            if Confirm.ask(
                f"    {i18n.t('cli.config.account_delete_confirm', name=account_name)}",
                default=False,
            ):
                del accounts[account_name]
                console.print(f"[success]    {i18n.t('cli.config.account_deleted', name=account_name)}[/]")

    return accounts


def run_wizard(target: ConfigTarget, config=None) -> bool:
    """
    对单个目标运行交互式配置向导

    流程：同步字段 i18n 语言 → 就绪提示 → 全局配置表单 →（适配器）
    账户管理环节 →（适配器）启用开关 → 整体校验 → 写入 config.toml
    （立即落盘），末尾统一打印保存结果；全局表单校验失败且放弃重填
    时直接中止（不写入任何配置）。

    :param target: ConfigTarget
    :param config: ConfigManager 实例（None 时使用全局单例）
    :return: 是否成功写入了配置
    """
    if config is None:
        import ErisPulse

        config = ErisPulse.config

    if not target.configurable:
        console.print(f"[warning]  {i18n.t('cli.config.no_declaration', name=target.name)}[/]")
        return False

    # 同步 Core i18n 到 CLI 语言，使字段 description/placeholder 与框架词同语言
    # （仅本进程生效，不持久化，避免污染全局语言设置）
    _core_i18n.set_language(i18n.get_language(), persist=False)

    # 已就绪目标提示
    status, _ = get_target_status(target, config)
    if status == STATUS_OK:
        console.print(f"[info]  {i18n.t('cli.config.ready_hint', name=target.name)}[/]")

    try:
        section_header(
            i18n.t(
                "cli.config.wizard_title",
                kind=target.kind_label,
                name=target.name,
            )
        )
        console.print(f"  [dim]{i18n.t('cli.config.wizard_hint')}[/]")

        written_keys: list[str] = []
        written = False

        # 1) 全局配置表单
        if target.config_class is not None:
            section_header(i18n.t("cli.config.global_section"))
            current = config.getConfig(target.config_key) or {}
            while True:
                values = fill_config_fields(target.config_class, current)
                errors = _validate_dataclass(target.config_class, values)
                if not errors:
                    break
                console.print(f"[error]  {i18n.t('cli.config.validation_failed', errors='; '.join(errors))}[/]")
                if not Confirm.ask(f"  [cyan]{i18n.t('cli.config.retry_edit')}[/]", default=True):
                    # 放弃重填：中止整个向导，不写入任何配置（避免产生
                    # "已启用但配置不完整"的半成品状态）
                    console.print(f"[warning]  {i18n.t('cli.config.abandoned')}[/]")
                    return False
            config.setConfig(target.config_key, values, immediate=True)
            written_keys.append(target.config_key)
            written = True

        # 2) 多账户环节（仅适配器）
        if target.kind == "adapter" and target.account_class is not None:
            accounts = _run_accounts_section(target, config)
            accounts_key = _resolve_accounts_key(target, config)
            config.setConfig(accounts_key, accounts, immediate=True)
            written_keys.append(accounts_key)
            written = True

        # 3) 适配器启用开关
        if target.kind == "adapter":
            from ErisPulse.Core.config import parse_bool_config

            status_key = f"ErisPulse.adapters.status.{target.name}"
            current_status = config.getConfig(status_key)
            enabled = Confirm.ask(
                f"  [cyan]{i18n.t('cli.config.adapter_enable_prompt', name=target.name)}[/]",
                default=True if current_status is None else parse_bool_config(current_status),
            )
            config.setConfig(status_key, enabled, immediate=True)
            written = True

        if written:
            console.print(
                f"[success]  {i18n.t('cli.config.saved_file', path=getattr(config, 'CONFIG_FILE', ''))}[/]"
            )
            if written_keys:
                console.print(f"  [dim]{i18n.t('cli.config.saved_keys_header')}[/]")
                for config_key in written_keys:
                    console.print(f"    [dim][{config_key}][/]")
        return written

    except (EOFError, KeyboardInterrupt):
        console.print(f"\n[info]  {i18n.t('cli.config.cancelled')}[/]")
        return False


def post_install_configure(dist_names: list[str] | None, config=None, *, interactive: bool | None = None) -> None:
    """
    安装完成后衔接配置向导

    刷新 entry-points 缓存后，按 PyPI 名称规范化匹配刚安装的包，
    仅对包含配置声明的目标逐个询问是否立即配置。非交互环境跳过并
    打印 ``epsdk config <name>`` 指引。

    :param dist_names: 本次成功安装的发行包名列表
    :param config: ConfigManager 实例（None 时使用全局单例）
    :param interactive: 是否交互（None 时自动检测 TTY）
    """
    if not dist_names:
        return
    if interactive is None:
        interactive = is_interactive()
    if not interactive:
        return

    # 同进程内 pip 安装后必须刷新 import 缓存，否则新包 entry-points 不可见
    importlib.invalidate_caches()

    normalized = {_normalize_dist_name(name) for name in dist_names}
    candidates = [
        t
        for t in load_config_targets()
        if t.package and _normalize_dist_name(t.package) in normalized and t.configurable
    ]
    if not candidates:
        return

    try:
        section_header(i18n.t("cli.config.post_install_header"))
        for target in candidates:
            try:
                if not Confirm.ask(
                    f"  [cyan]{i18n.t('cli.config.post_install_prompt', kind=target.kind_label, name=target.name)}[/]",
                    default=True,
                ):
                    continue
                run_wizard(target, config)
            except (EOFError, KeyboardInterrupt):
                console.print(f"\n[info]  {i18n.t('cli.config.post_install_skip_rest')}[/]")
                break
    except Exception as e:
        console.print(f"[warning]  {i18n.t('cli.config.post_install_failed', error=e)}[/]")
