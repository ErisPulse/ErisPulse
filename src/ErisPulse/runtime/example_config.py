"""
config.full.example 完整配置参考生成器（runtime / CLI 共用）

框架运行（``sdk.run`` / ``epsdk run``）与 ``epsdk init`` 都通过本模块
生成 ``config/config.full.example``：静态框架配置段 + 已安装适配器/模块的
声明式配置段（含 ``example`` 字段），为用户提供完整配置参考。

文件自维护约定（首行标记控制刷新）：
- 首行为本模块写出的 ``gen=`` 标记行 → 每次框架启动检测到生成器版本变化时
  自动刷新（新增配置项 / 新装组件的配置段会补进来）
- 用户删除/改动首行标记 → 视为手动接管，框架不再触碰该文件

{!--< internal-use >!--}
{!--< /internal-use >!--}
"""

import re
from pathlib import Path

FULL_EXAMPLE_FILENAME = "config.full.example"

# 生成器版本：模板/静态段结构变化时递增，驱动带标记文件的一次性刷新
_GEN = 1

# 首行标记前缀（语言无关，供自动刷新判定）
_MARKER_PREFIX = "# ErisPulse full config reference (auto-maintained by framework, gen="
_MARKER = f"{_MARKER_PREFIX}{_GEN}). Remove or edit this line to take manual control."
_MARKER_RE = re.compile(r"gen=(\d+)\)")


def _scaffold_text():
    """获取文案工具实例（CLI 上下文；惰性导入避免拉高 CLI 包）"""
    from ErisPulse.CLI.utils.scaffold_text import ScaffoldText

    return ScaffoldText()


def render_full_example(adapter_list=None, st=None) -> str:
    """
    生成完整的配置示例文本

    首行为自维护标记（供运行时按 gen 刷新判定）；其后为静态框架配置段
    （文案跟随 CLI / Core 语言，缺失回退英文）与已安装组件声明式配置段。
    无适配器列表时给出通用示例适配器注释。

    :param adapter_list: 适配器名称列表（``epsdk init`` 从商店抓取；None 用示例）
    :param st: ScaffoldText 实例（None 时按当前语言构造）
    :return: 完整配置示例字符串
    """
    if st is None:
        st = _scaffold_text()

    lines = [_MARKER, ""]

    # ---- 静态框架配置段 ----
    lines.extend(
        [
            st.t("cfg.header.title"),
            st.t("cfg.header.desc"),
            st.t("cfg.header.usage"),
            "",
            st.t("cfg.section.server"),
            "",
            "[ErisPulse.server]",
            f'host = "0.0.0.0"              # {st.t("cfg.server.host")}',
            f"port = 8000                   # {st.t('cfg.server.port')}",
            f"auto_start = true             # {st.t('cfg.server.auto_start')}",
            f'ssl_certfile = "config/ssl/cert.pem"   # {st.t("cfg.server.ssl_certfile")}',
            f'ssl_keyfile = "config/ssl/key.pem"    # {st.t("cfg.server.ssl_keyfile")}',
            st.t("cfg.server.ssl_inline_hint"),
            '# ssl_cert = """-----BEGIN CERTIFICATE-----',
            "# ...",
            '# -----END CERTIFICATE-----"""',
            '# ssl_key = """-----BEGIN PRIVATE KEY-----',
            "# ...",
            '# -----END PRIVATE KEY-----"""',
            "",
            st.t("cfg.section.logger"),
            "",
            "[ErisPulse.logger]",
            f'level = "INFO"                # {st.t("cfg.logger.level")}',
            f"log_files = []                # {st.t('cfg.logger.log_files')}",
            f'log_dir = ""                  # {st.t("cfg.logger.log_dir")}',
            f'log_rotation = "size"         # {st.t("cfg.logger.log_rotation")}',
            f"log_max_size_mb = 10          # {st.t('cfg.logger.log_max_size_mb')}",
            f"log_backup_count = 5          # {st.t('cfg.logger.log_backup_count')}",
            f'log_rotation_when = "midnight"  # {st.t("cfg.logger.log_rotation_when")}',
            f"memory_limit = 1000           # {st.t('cfg.logger.memory_limit')}",
            "",
            st.t("cfg.section.storage"),
            "",
            "[ErisPulse.storage]",
            f'backend = "sqlite"           # {st.t("cfg.storage.backend")}',
            f"use_global_db = false         # {st.t('cfg.storage.use_global_db')}",
            "",
            f"[ErisPulse.storage.mysql]     # {st.t('cfg.storage.mysql')}",
            'host = "127.0.0.1"',
            "port = 3306",
            'user = "erispulse"',
            'password = ""',
            'database = "erispulse"',
            "",
            f"[ErisPulse.storage.postgres]  # {st.t('cfg.storage.postgres')}",
            'host = "127.0.0.1"',
            "port = 5432",
            'user = "erispulse"',
            'password = ""',
            'database = "erispulse"',
            "",
            st.t("cfg.section.event"),
            "",
            "[ErisPulse.event.message]",
            f"ignore_self = true            # {st.t('cfg.event.ignore_self')}",
            "",
            "[ErisPulse.event.command]",
            f'prefix = "/"                  # {st.t("cfg.command.prefix")}',
            f"case_sensitive = true         # {st.t('cfg.command.case_sensitive')}",
            f"allow_space_prefix = false    # {st.t('cfg.command.allow_space_prefix')}",
            f"must_at_bot = false           # {st.t('cfg.command.must_at_bot')}",
            "",
            st.t("cfg.section.framework"),
            "",
            "[ErisPulse.framework]",
            f"enable_lazy_loading = true     # {st.t('cfg.framework.enable_lazy_loading')}",
            f'plugins_dir = "plugins"        # {st.t("cfg.framework.plugins_dir")}',
            f"uninit_timeout = 30            # {st.t('cfg.framework.uninit_timeout')}",
            f"                                {st.t('cfg.framework.uninit_timeout_line1')}",
            f"                                {st.t('cfg.framework.uninit_timeout_line2')}",
            f"strict_mode = false            # {st.t('cfg.framework.strict_mode')}",
            f"strict_mode_exceptions = {{ modules = [], adapters = [] }}  # {st.t('cfg.framework.strict_mode_exceptions')}",
            f"handler_max_concurrency = 64   # {st.t('cfg.framework.handler_max_concurrency')}",
            f"proactive_gc_interval = 300    # {st.t('cfg.framework.proactive_gc_interval')}",
            f"proactive_gc_generation = 2    # {st.t('cfg.framework.proactive_gc_generation')}",
            f"proactive_gc_full_every = 10   # {st.t('cfg.framework.proactive_gc_full_every')}",
            f"proactive_gc_memory_growth_mb = 100  # {st.t('cfg.framework.proactive_gc_memory_growth_mb')}",
            f"proactive_gc_idle_only = true  # {st.t('cfg.framework.proactive_gc_idle_only')}",
            f"proactive_gc_gen0_min = 100    # {st.t('cfg.framework.proactive_gc_gen0_min')}",
            f"offline_bot_expiry = 3600      # {st.t('cfg.framework.offline_bot_expiry')}",
            "",
            st.t("cfg.section.router"),
            "",
            "[ErisPulse.router.cors]",
            "enabled = false",
            'allow_origins = ["*"]',
            'allow_methods = ["*"]',
            'allow_headers = ["*"]',
            "allow_credentials = false",
            "max_age = 600",
            "",
            "[ErisPulse.router.security]",
            "enabled = false",
            "",
            "[ErisPulse.router.security.headers]",
            'X-Content-Type-Options = "nosniff"',
            'X-Frame-Options = "DENY"',
            "",
            st.t("cfg.section.adapter_status"),
            "",
            "[ErisPulse.adapters.status]",
        ]
    )

    if adapter_list:
        lines.extend(f"# {adapter} = false" for adapter in adapter_list)
    else:
        lines.extend(
            [
                "# yunhu = false",
                "# telegram = false",
                "# onebot11 = false",
            ]
        )

    lines.extend(
        [
            "",
            st.t("cfg.section.module_status"),
            "",
            "[ErisPulse.modules.status]",
            "# MyModule = true",
            "",
        ]
    )

    # ---- 已安装组件声明式配置段 ----
    lines.extend(_component_sections(st))

    return "\n".join(lines)


def _component_sections(st) -> list[str]:
    """
    渲染已安装适配器/模块的声明式配置段（追加到 full.example 末尾）

    复用配置向导的发现机制（entry-points + 本地插件目录），
    对声明了 ConfigClass 的组件用 ``dataclass_to_toml_with_comments(include_example=True)``
    渲染带注释模板——含 ``example`` 字段（这类字段不自动写入 config.toml，
    仅记录在本示例文件中供用户按需启用）。

    :param st: ScaffoldText 文案工具实例
    :return: 行列表（无已配置组件时为空）
    """
    try:
        from ErisPulse.CLI.utils.config_wizard import load_config_targets
        from ErisPulse.Core.Bases.config_schema import dataclass_to_toml_with_comments

        configured = [t for t in load_config_targets() if t.config_class is not None]
    except Exception:
        return []

    if not configured:
        return []

    lines = [st.t("cfg.section.components"), "", st.t("cfg.section.components_hint"), ""]
    for target in configured:
        cfg_cls = target.config_class
        if cfg_cls is None:
            continue
        try:
            body = dataclass_to_toml_with_comments(cfg_cls, include_example=True)
        except Exception:
            continue
        if not body.strip():
            continue
        lines.append(f"[{target.config_key}]")
        lines.append(body.rstrip())
        lines.append("")

    # 无成功渲染的组件时不出现在示例中
    return lines if len(lines) > 4 else []


def ensure_full_example(config_dir: str | Path | None = None) -> Path | None:
    """
    确保 config.full.example 存在 / 随生成器版本刷新

    - 文件不存在 → 生成（覆盖"直接 run / 未 init"用户没有配置参考的问题）
    - 首行为本模块标记且 ``gen`` 与当前不一致 → 刷新（补新增配置项与组件段）
    - 首行非本模块标记（用户手动接管）或 gen 一致 → 不触碰

    :param config_dir: 配置目录（None 时取 ``cwd/config``）
    :return: 被写入的路径；无需写入时返回 None
    """
    base = Path(config_dir) if config_dir else Path.cwd() / "config"
    base.mkdir(parents=True, exist_ok=True)
    path = base / FULL_EXAMPLE_FILENAME

    need_write = not path.exists()
    if not need_write:
        first = None
        try:
            with path.open(encoding="utf-8", errors="ignore") as f:
                first = f.readline()
        except OSError:
            first = None
        if first and first.startswith(_MARKER_PREFIX):
            match = _MARKER_RE.search(first)
            if match:
                need_write = int(match.group(1)) != _GEN
        # 无标记或标记 gen 一致 → 用户手动接管 / 已最新，跳过

    if not need_write:
        return None

    path.write_text(render_full_example(), encoding="utf-8")
    return path
