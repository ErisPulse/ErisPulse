"""
ErisPulse AI Prompt 生成器

从 docs/ 目录读取文档，数据驱动地生成 AI 辅助开发用的 prompt 文档。
支持三种 prompt 类型：模块开发、适配器开发、全栈开发。

使用方法:
    python scripts/tools/generate-ai-prompts.py

    # 只为特定语言生成
    python scripts/tools/generate-ai-prompts.py --lang en

    # 启用详细输出（显示缺失文件警告）
    python scripts/tools/generate-ai-prompts.py --verbose
"""

import argparse
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 日志器
# ---------------------------------------------------------------------------


class Logger:
    """线程安全的标准输出日志器"""

    _lock = threading.Lock()

    @classmethod
    def log(cls, msg: str):
        """
        输出一行日志

        :param msg: 日志内容
        """
        with cls._lock:
            sys.stdout.write(msg + "\n")
            sys.stdout.flush()

    @classmethod
    def progress(cls, filename: str, status: str, detail: str = ""):
        """
        输出单条 prompt 生成进度

        :param filename: 输出文件名
        :param status: 状态标识（gen/skip/fail/miss 等）
        :param detail: 附加详情，可选
        """
        tag = {
            "gen": "[GEN]",
            "skip": "[SKIP]",
            "fail": "[FAIL]",
            "miss": "[MISS]",
        }.get(status, f"[{status.upper()}]")
        line = f"  {tag} {filename}"
        if detail:
            line += f"  {detail}"
        cls.log(line)

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class DocEntry:
    """单个文档条目，对应 docs/ 下的一个 .md 文件

    :ivar title: 条目标题
    :ivar path: 相对文档根目录的路径
    """

    title: str
    path: str


@dataclass
class Section:
    """一个章节，包含标题和若干文档条目

    :ivar title: 章节标题
    :ivar entries: 章节包含的文档条目列表
    :ivar subgroup: 子分组标签（如 "模块开发"、"适配器开发"），仅用于 full 类型的二级标题
    """

    title: str
    entries: list[DocEntry] = field(default_factory=list)
    subgroup: str = ""


@dataclass
class PromptSpec:
    """一种 prompt 类型的完整定义

    :ivar name: prompt 类型名称（如 ``module`` / ``adapter`` / ``full``）
    :ivar filename: 输出文件名
    :ivar system_prompt: System prompt 内容
    :ivar header: 最外层标题（空字符串表示不输出）
    :ivar preamble: 仅用于 full 类型的前置说明
    :ivar sections: 包含的章节列表
    """

    name: str
    filename: str
    system_prompt: str
    header: str
    preamble: str = ""
    sections: list[Section] = field(default_factory=list)


# ---------------------------------------------------------------------------
# System Prompt 定义
# ---------------------------------------------------------------------------

SYSTEM_PROMPTS: dict[str, str] = {
    "module": """\
你是一个 ErisPulse 模块开发专家，精通以下领域：

- 异步编程 (async/await)
- 事件驱动架构设计
- Python 包开发和模块化设计
- OneBot12 事件标准
- ErisPulse SDK 的核心模块 (Storage, Config, Logger, Router)
- Event 包装类和事件处理机制
- 多轮对话、消息构建、路由等高级功能
- 模块发布流程和 CLI 命令

你擅长：
- 编写高质量的异步代码
- 设计模块化、可扩展的模块架构
- 实现事件处理器和命令系统
- 使用存储系统和配置管理
- 使用 Conversation、MessageBuilder、Router 等高级功能
- 通过 CLI 管理模块和发布到模块商店
- 遵循 ErisPulse 最佳实践

**使用以下文档作为知识库，回答问题时请优先参考文档内容。**
""",
    "adapter": """\
你是一个 ErisPulse 适配器开发专家，精通以下领域：

- 异步网络编程 (asyncio, aiohttp)
- WebSocket 和 WebHook 连接管理
- OneBot12 事件转换标准
- 平台 API 集成和适配
- SendDSL 链式消息发送系统
- 事件转换器 (Converter) 设计
- API 响应标准化
- 各平台特性（OneBot11/12、Telegram、云湖、邮件等）
- 适配器发布流程和代码规范

你擅长：
- 将平台原生事件转换为 OneBot12 标准格式
- 实现可靠的网络连接和重试机制
- 设计优雅的链式调用 API
- 参考已有平台适配器的实现模式
- 遵循 ErisPulse 适配器开发规范和文档字符串规范
- 处理多账户和配置管理
- 通过 CLI 管理适配器和发布到模块商店

**使用以下文档作为知识库，回答问题时请优先参考文档内容。**
""",
    "full": """\
你是一个 ErisPulse 全栈开发专家，精通以下领域：

- ErisPulse 框架的核心架构和设计理念
- 模块开发和适配器开发
- 异步编程和事件驱动架构
- OneBot12 事件标准和平台适配
- SDK 核心模块 (Storage, Config, Logger, Router, Lifecycle)
- Event 包装类和事件处理系统
- 懒加载系统和生命周期管理
- SendDSL 消息发送系统
- 路由系统和 FastAPI 集成
- 各平台特性指南（OneBot11/12、Telegram、云湖、邮件等）
- 模块/适配器发布流程和模块商店
- 代码规范和文档字符串规范

你擅长：
- 编写高质量的异步 Python 代码
- 设计模块化、可扩展的架构
- 开发模块、适配器
- 使用 ErisPulse 的所有核心功能
- 遵循 ErisPulse 的最佳实践和代码规范
- 解决跨平台兼容性问题
- 通过 CLI 管理项目和发布

**使用以下文档作为知识库，回答问题时请优先参考文档内容。**
""",
}

# ---------------------------------------------------------------------------
# 通用文档片段（被多种 prompt 类型复用）
# ---------------------------------------------------------------------------

SECTION_FRAMEWORK = Section(
    title="框架理解",
    entries=[
        DocEntry("架构概览", "architecture.md"),
    ],
)

SECTION_QUICK_START = Section(
    title="快速上手",
    entries=[
        DocEntry("快速开始", "quick-start.md"),
        DocEntry("创建第一个机器人", "getting-started/first-bot.md"),
        DocEntry("基础概念", "getting-started/basic-concepts.md"),
        DocEntry("事件处理入门", "getting-started/event-handling.md"),
        DocEntry("IDE 补全", "getting-started/ide-completion.md"),
    ],
)

SECTION_GETTING_STARTED = Section(
    title="快速开始",
    entries=[
        DocEntry("入门指南总览", "getting-started/README.md"),
        DocEntry("创建第一个模块", "getting-started/first-bot.md"),
        DocEntry("基础概念", "getting-started/basic-concepts.md"),
        DocEntry("事件处理入门", "getting-started/event-handling.md"),
        DocEntry("常见任务示例", "getting-started/common-tasks.md"),
    ],
)

SECTION_GETTING_STARTED_BASIC = Section(
    title="基础概念",
    entries=[
        DocEntry("入门指南总览", "getting-started/README.md"),
        DocEntry("基础概念", "getting-started/basic-concepts.md"),
        DocEntry("事件处理入门", "getting-started/event-handling.md"),
    ],
)

SECTION_PUBLISH_AND_TOOLS = Section(
    title="发布与工具",
    entries=[
        DocEntry("发布模块到模块商店", "developer-guide/publishing.md"),
        DocEntry("CLI 命令参考", "user-guide/cli-reference.md"),
    ],
)

SECTION_ADVANCED_MODULE = Section(
    title="高级主题",
    entries=[
        DocEntry("Conversation 多轮对话", "advanced/conversation.md"),
        DocEntry("MessageBuilder 详解", "advanced/message-builder.md"),
        DocEntry("HTTP 客户端", "advanced/http-client.md"),
        DocEntry("SQL 查询构建器", "advanced/sql-builder.md"),
        DocEntry("路由系统", "advanced/router.md"),
        DocEntry("生命周期管理", "advanced/lifecycle.md"),
        DocEntry("懶加载系统", "advanced/lazy-loading.md"),
        DocEntry("国际化（i18n）系统", "advanced/i18n.md"),
        DocEntry("统一控制面（scope）", "advanced/scope.md"),
        DocEntry("启动流程与手动控制", "advanced/startup.md"),
    ],
)

SECTION_ADVANCED_ADAPTER = Section(
    title="高级主题",
    entries=[
        DocEntry("HTTP 客户端", "advanced/http-client.md"),
        DocEntry("SQL 查询构建器", "advanced/sql-builder.md"),
        DocEntry("生命周期管理", "advanced/lifecycle.md"),
        DocEntry("懶加载系统", "advanced/lazy-loading.md"),
        DocEntry("国际化（i18n）系统", "advanced/i18n.md"),
        DocEntry("统一控制面（scope）", "advanced/scope.md"),
        DocEntry("启动流程与手动控制", "advanced/startup.md"),
    ],
)

SECTION_ADVANCED_FULL = Section(
    title="高级主题",
    entries=[
        DocEntry("HTTP 客户端", "advanced/http-client.md"),
        DocEntry("SQL 查询构建器", "advanced/sql-builder.md"),
        DocEntry("懶加载系统", "advanced/lazy-loading.md"),
        DocEntry("生命周期管理", "advanced/lifecycle.md"),
        DocEntry("路由系统", "advanced/router.md"),
        DocEntry("MessageBuilder 详解", "advanced/message-builder.md"),
        DocEntry("Conversation 多轮对话", "advanced/conversation.md"),
        DocEntry("国际化（i18n）系统", "advanced/i18n.md"),
        DocEntry("统一控制面（scope）", "advanced/scope.md"),
        DocEntry("启动流程与手动控制", "advanced/startup.md"),
    ],
)

SECTION_ECOSYSTEM = Section(
    title="生态模块",
    entries=[
        DocEntry("ErisPulse-App 安装与使用", "ecosystem/app.md"),
        DocEntry("Dashboard 使用与视窗注册", "ecosystem/dashboard.md"),
        DocEntry("Takumi 图片渲染", "ecosystem/takumi.md"),
    ],
)

SECTION_STANDARDS_MODULE = Section(
    title="技术标准",
    entries=[
        DocEntry("会话类型标准", "standards/session-types.md"),
    ],
)

SECTION_STANDARDS_ADAPTER = Section(
    title="技术标准",
    entries=[
        DocEntry("会话类型标准", "standards/session-types.md"),
        DocEntry("事件转换标准", "standards/event-conversion.md"),
        DocEntry("API 响应标准", "standards/api-response.md"),
        DocEntry("发送方法规范", "standards/send-method-spec.md"),
        DocEntry("请求操作规范", "standards/request-action-spec.md"),
        DocEntry("API 动作标准", "standards/api-action-spec.md"),
    ],
)

SECTION_STANDARDS_FULL = Section(
    title="技术标准",
    entries=[
        DocEntry("会话类型标准", "standards/session-types.md"),
        DocEntry("事件转换标准", "standards/event-conversion.md"),
        DocEntry("API 响应标准", "standards/api-response.md"),
        DocEntry("发送方法规范", "standards/send-method-spec.md"),
        DocEntry("请求操作规范", "standards/request-action-spec.md"),
        DocEntry("API 动作标准", "standards/api-action-spec.md"),
    ],
)

SECTION_PLATFORM_OVERVIEW = Section(
    title="平台概览",
    entries=[
        DocEntry("平台特性与 SendDSL 通用语法", "platform-guide/README.md"),
    ],
)

SECTION_PLATFORM_FULL = Section(
    title="平台特性指南",
    entries=[
        DocEntry("平台特性总览", "platform-guide/README.md"),
        DocEntry("OneBot11 适配", "platform-guide/onebot11.md"),
        DocEntry("OneBot12 适配", "platform-guide/onebot12.md"),
        DocEntry("Telegram 适配", "platform-guide/telegram.md"),
        DocEntry("云湖适配", "platform-guide/yunhu.md"),
        DocEntry("邮件适配", "platform-guide/email.md"),
        DocEntry("Kook 适配", "platform-guide/kook.md"),
        DocEntry("Matrix 适配", "platform-guide/matrix.md"),
        DocEntry("QQBot 适配", "platform-guide/qqbot.md"),
        DocEntry("云湖用户端适配", "platform-guide/yunhu_user.md"),
        DocEntry("平台文档维护说明", "platform-guide/maintain-notes.md"),
        DocEntry("花枫咖啡馆适配", "platform-guide/ideaura.md"),
        DocEntry("Discord 适配", "platform-guide/discord.md"),
        DocEntry("Webhook 适配", "platform-guide/webhook.md"),
        DocEntry("微信公众号适配", "platform-guide/wechatmp.md"),
    ],
)

SECTION_STYLEGUIDE = Section(
    title="代码规范",
    entries=[
        DocEntry("文档字符串规范", "styleguide/docstring.md"),
    ],
)

# ---------------------------------------------------------------------------
# 三种 Prompt 类型的完整定义
# ---------------------------------------------------------------------------

PROMPT_SPECS: list[PromptSpec] = [
    # ---- 模块开发 ----
    PromptSpec(
        name="module",
        filename="ErisPulse-ModuleDev.md",
        system_prompt=SYSTEM_PROMPTS["module"],
        header="ErisPulse 模块开发指南",
        sections=[
            SECTION_FRAMEWORK,
            SECTION_QUICK_START,
            Section(
                title="模块开发",
                entries=[
                    DocEntry(
                        "模块开发入门", "developer-guide/modules/getting-started.md"
                    ),
                    DocEntry(
                        "模块核心概念", "developer-guide/modules/core-concepts.md"
                    ),
                    DocEntry(
                        "Event 包装类详解", "developer-guide/modules/event-wrapper.md"
                    ),
                    DocEntry(
                        "模块开发最佳实践", "developer-guide/modules/best-practices.md"
                    ),
                ],
            ),
            SECTION_PUBLISH_AND_TOOLS,
            Section(
                title="API 参考",
                entries=[
                    DocEntry("核心模块 API", "api-reference/core-modules.md"),
                    DocEntry("事件系统 API", "api-reference/event-system.md"),
                ],
            ),
            SECTION_ADVANCED_MODULE,
            SECTION_STANDARDS_MODULE,
            SECTION_ECOSYSTEM,
            SECTION_PLATFORM_OVERVIEW,
        ],
    ),
    # ---- 适配器开发 ----
    PromptSpec(
        name="adapter",
        filename="ErisPulse-AdapterDev.md",
        system_prompt=SYSTEM_PROMPTS["adapter"],
        header="ErisPulse 适配器开发指南",
        sections=[
            SECTION_FRAMEWORK,
            SECTION_QUICK_START,
            Section(
                title="适配器开发",
                entries=[
                    DocEntry(
                        "适配器开发入门", "developer-guide/adapters/getting-started.md"
                    ),
                    DocEntry(
                        "适配器核心概念", "developer-guide/adapters/core-concepts.md"
                    ),
                    DocEntry("SendDSL 详解", "developer-guide/adapters/send-dsl.md"),
                    DocEntry(
                        "适配器开发最佳实践",
                        "developer-guide/adapters/best-practices.md",
                    ),
                    DocEntry("事件转换器", "developer-guide/adapters/converter.md"),
                ],
            ),
            SECTION_PUBLISH_AND_TOOLS,
            Section(
                title="API 参考",
                entries=[
                    DocEntry("适配器系统 API", "api-reference/adapter-system.md"),
                    DocEntry("核心模块 API", "api-reference/core-modules.md"),
                ],
            ),
            SECTION_ADVANCED_ADAPTER,
            SECTION_STANDARDS_ADAPTER,
            SECTION_ECOSYSTEM,
            SECTION_PLATFORM_FULL,
            SECTION_STYLEGUIDE,
        ],
    ),
    # ---- 全栈开发 ----
    PromptSpec(
        name="full",
        filename="ErisPulse-Full.md",
        system_prompt=SYSTEM_PROMPTS["full"],
        header="",
        preamble=(
            "# ErisPulse 完整开发物料\n"
            "> **注意**：本文档内容较多，建议仅用于具有强大上下文能力的 AI 模型\n\n"
        ),
        sections=[
            SECTION_FRAMEWORK,
            Section(
                title="快速开始",
                entries=[
                    DocEntry("", "quick-start.md"),
                ],
            ),
            Section(
                title="入门指南",
                entries=[
                    DocEntry("入门指南总览", "getting-started/README.md"),
                    DocEntry("创建第一个机器人", "getting-started/first-bot.md"),
                    DocEntry("基础概念", "getting-started/basic-concepts.md"),
                    DocEntry("事件处理入门", "getting-started/event-handling.md"),
                    DocEntry("常见任务示例", "getting-started/common-tasks.md"),
                    DocEntry("IDE 补全", "getting-started/ide-completion.md"),
                ],
            ),
            Section(
                title="用户指南",
                entries=[
                    DocEntry("安装和配置", "user-guide/installation.md"),
                    DocEntry("CLI 命令参考", "user-guide/cli-reference.md"),
                    DocEntry("配置文件说明", "user-guide/configuration.md"),
                    DocEntry("部署指南", "user-guide/deployment.md"),
                ],
            ),
            Section(
                title="开发者指南",
                entries=[
                    DocEntry("开发者指南总览", "developer-guide/README.md"),
                ],
                subgroup="",
            ),
            Section(
                title="模块开发",
                subgroup="模块开发",
                entries=[
                    DocEntry(
                        "模块开发入门", "developer-guide/modules/getting-started.md"
                    ),
                    DocEntry(
                        "模块核心概念", "developer-guide/modules/core-concepts.md"
                    ),
                    DocEntry(
                        "Event 包装类详解", "developer-guide/modules/event-wrapper.md"
                    ),
                    DocEntry(
                        "模块开发最佳实践", "developer-guide/modules/best-practices.md"
                    ),
                ],
            ),
            Section(
                title="适配器开发",
                subgroup="适配器开发",
                entries=[
                    DocEntry(
                        "适配器开发入门", "developer-guide/adapters/getting-started.md"
                    ),
                    DocEntry(
                        "适配器核心概念", "developer-guide/adapters/core-concepts.md"
                    ),
                    DocEntry("SendDSL 详解", "developer-guide/adapters/send-dsl.md"),
                    DocEntry(
                        "适配器开发最佳实践",
                        "developer-guide/adapters/best-practices.md",
                    ),
                    DocEntry("事件转换器", "developer-guide/adapters/converter.md"),
                ],
            ),
            Section(
                title="",
                entries=[
                    DocEntry("发布与模块商店指南", "developer-guide/publishing.md"),
                ],
            ),
            Section(
                title="API 参考",
                entries=[
                    DocEntry("核心模块 API", "api-reference/core-modules.md"),
                    DocEntry("事件系统 API", "api-reference/event-system.md"),
                    DocEntry("适配器系统 API", "api-reference/adapter-system.md"),
                ],
            ),
            SECTION_STANDARDS_FULL,
            SECTION_ADVANCED_FULL,
            SECTION_ECOSYSTEM,
            SECTION_PLATFORM_FULL,
            SECTION_STYLEGUIDE,
        ],
    ),
]


# ---------------------------------------------------------------------------
# 生成引擎
# ---------------------------------------------------------------------------


class PromptGenerator:
    """AI Prompt 生成器

    数据驱动设计：从 ``PROMPT_SPECS`` 配置逐个读取文档内容并拼接为完整的 prompt 文档。
    """

    def __init__(
        self,
        docs_dir: str | Path,
        output_dir: str | Path,
        lang: Optional[str] = None,
        *,
        verbose: bool = False,
    ):
        """
        初始化 Prompt 生成器

        :param docs_dir: 文档根目录
        :param output_dir: prompt 输出目录
        :param lang: 指定语言代码，未指定时直接使用 ``docs_dir``
        :param verbose: 是否输出缺失文件的警告信息
        """
        self.docs_dir = Path(docs_dir)
        self.lang = lang
        self.actual_docs_dir = self.docs_dir / lang if lang else self.docs_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose

    # ---- 公开接口 ----

    @staticmethod
    def get_available_languages(docs_dir: Path) -> list[str]:
        """
        获取 docs/ 下可用的语言目录

        :param docs_dir: 文档根目录
        :return: 排序后的语言代码列表
        """
        return sorted(
            item.name
            for item in docs_dir.iterdir()
            if item.is_dir() and item.name != "_meta"
        )

    def generate_all(self) -> None:
        """生成 ``PROMPT_SPECS`` 中定义的所有 prompt 文档"""
        for spec in PROMPT_SPECS:
            content = self._generate(spec)
            self._write_prompt(spec.filename, content)
            Logger.progress(spec.filename, "gen", f"{len(content):,} 字符")

    # ---- 核心生成逻辑 ----

    def _generate(self, spec: PromptSpec) -> str:
        """
        根据单个 ``PromptSpec`` 配置生成 prompt 文档

        拼接顺序：System Prompt -> 前置说明（可选）-> 外层标题（可选）-> 所有章节。

        :param spec: Prompt 配置
        :return: 完整 prompt 文本
        """
        parts: list[str] = []

        # 1. System prompt + 分隔线
        parts.append(spec.system_prompt)
        parts.append("\n---\n\n")

        # 2. 前置说明（仅 full 类型）
        if spec.preamble:
            parts.append(spec.preamble)
            parts.append("---\n\n")

        # 3. 最外层标题（非 full 类型）
        if spec.header:
            parts.append(self._section_header(spec.header))
            parts.append("\n")

        # 4. 遍历所有章节
        for section in spec.sections:
            self._render_section(parts, section)

        return "\n".join(parts)

    def _render_section(self, parts: list[str], section: Section) -> None:
        """
        渲染单个章节（含标题、可选子分组标签、文档条目）

        空标题的章节仅输出条目内容（用于 full 类型中的孤立条目）。

        :param parts: 用于拼接的可变字符串列表
        :param section: 待渲染的章节
        """
        if section.title:
            parts.append(self._section_header(section.title))

        # 子分组标签（仅 full 类型中的 "模块开发" / "适配器开发"）
        if section.subgroup:
            parts.append(self._subheader(section.subgroup))

        for entry in section.entries:
            if entry.title:
                parts.append(self._subsection_header(entry.title))
            content = self._read_file(entry.path)
            parts.append(content)
            parts.append("")

    # ---- 文件读取 ----

    # 纯导航尾段标题（多语言）—— 在 prompt 拼接时剥离以减少噪音
    _NAV_SECTION_TITLES = frozenset({
        # zh-CN / zh-TW
        "相关文档", "相关链接", "下一步", "接下来",
        "相關文檔", "相關連結",
        # en
        "Related Documentation", "Related Documents", "Related Links",
        "Next Steps", "See Also", "Further Reading",
        # ja
        "関連ドキュメント", "関連文書", "関連リンク", "参考リンク", "参考ドキュメント",
        # ru
        "Связанные документы", "Связанная документация",
        "Связанные ссылки", "Далее",
    })

    def _read_file(self, rel_path: str) -> str:
        """
        读取文档文件，缺失时返回空字符串并可选输出警告

        读取后剥离纯导航尾段（"相关文档"/"下一步" 等多语言变体），
        这些段落在拼接 prompt 时是纯链接噪音，剥离可降低 token、提升生成质量。
        手写文档不受影响，仅作用于 prompt 生成。

        :param rel_path: 相对于文档根目录的路径
        :return: 文件文本内容，文件不存在时返回空字符串
        """
        full_path = self.actual_docs_dir / rel_path
        if not full_path.exists():
            if self.verbose:
                Logger.progress(rel_path, "miss", "文件不存在")
            return ""
        content = full_path.read_text(encoding="utf-8")
        return self._strip_nav_sections(content)

    @staticmethod
    def _strip_nav_sections(content: str) -> str:
        """
        剥离纯导航尾段（``## 相关文档`` / ``## 下一步`` 等多语言变体）

        从匹配的 ``##`` 标题行开始、到下一个 ``##`` 标题或文件结尾为止的全部内容，
        均从结果中移除。

        :param content: 原始 Markdown 文本
        :return: 剥离导航段后的文本
        """
        titles = PromptGenerator._NAV_SECTION_TITLES
        lines = content.split("\n")
        result: list[str] = []
        in_nav = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## ") and not stripped.startswith("### "):
                title = stripped[3:].strip()
                in_nav = title in titles
            if not in_nav:
                result.append(line)
        # 移除末尾多余空行
        return "\n".join(result).rstrip() + "\n" if result else ""

    # ---- 格式化辅助 ----

    @staticmethod
    def _section_header(title: str) -> str:
        """
        生成章节标题（带 ``=`` 分隔线）

        :param title: 章节标题
        :return: Markdown 文本
        """
        return f"\n{'=' * len(title)}\n{title}\n{'=' * len(title)}\n"

    @staticmethod
    def _subheader(title: str) -> str:
        """
        生成二级标题（带 ``-`` 分隔线）

        :param title: 二级标题文本
        :return: Markdown 文本
        """
        return f"\n{title}\n{'-' * len(title)}\n"

    @staticmethod
    def _subsection_header(title: str) -> str:
        """
        生成三级标题（``###`` 前缀）

        :param title: 三级标题文本
        :return: Markdown 文本
        """
        return f"\n### {title}\n"

    # ---- 输出 ----

    def _write_prompt(self, filename: str, content: str) -> None:
        """
        写入 prompt 文件

        :param filename: 输出文件名
        :param content: prompt 文本内容
        """
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main() -> None:
    """命令行入口：解析参数并为指定语言或全部语言生成 prompt"""
    parser = argparse.ArgumentParser(
        description="ErisPulse AI Prompt 生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  # 使用默认设置（为所有语言生成）
  python scripts/tools/generate-ai-prompts.py

  # 只为特定语言生成
  python scripts/tools/generate-ai-prompts.py --lang en

  # 启用详细输出（显示缺失文件警告）
  python scripts/tools/generate-ai-prompts.py --verbose
        """,
    )
    parser.add_argument("--docs", default="docs", help="文档目录 (默认: docs)")
    parser.add_argument(
        "--lang", help="指定语言代码（如: zh-CN, en, zh-TW），不指定则为所有语言生成"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="显示缺失文件警告")

    args = parser.parse_args()
    script_dir = Path(__file__).parent
    docs_dir = script_dir.parent.parent / args.docs

    Logger.log("=" * 60)
    Logger.log("ErisPulse AI Prompt 生成器")
    Logger.log("=" * 60)
    Logger.log(f"文档目录: {docs_dir}")
    Logger.log(f"语言: {args.lang if args.lang else '全部'}")
    Logger.log(f"详细模式: {'开启' if args.verbose else '关闭'}")
    Logger.log("")

    if args.lang:
        _process_language(docs_dir, args.lang, verbose=args.verbose)
    else:
        langs = PromptGenerator.get_available_languages(docs_dir)
        Logger.log(f"发现 {len(langs)} 个语言: {', '.join(langs)}")
        Logger.log("")
        for lang in langs:
            _process_language(docs_dir, lang, verbose=args.verbose)

    Logger.log("")
    Logger.log("=" * 60)
    Logger.log("所有语言的 AI prompt 文档生成完成")
    Logger.log("=" * 60)


def _process_language(docs_dir: Path, lang: str, *, verbose: bool = False) -> None:
    """
    处理单个语言的 prompt 生成

    :param docs_dir: 文档根目录
    :param lang: 语言代码
    :param verbose: 是否输出缺失文件警告
    """
    Logger.log(f"--- {lang} ---")
    Logger.log(f"  文档目录: {docs_dir / lang}")

    output_dir = docs_dir / lang / "ai-support" / "prompts"
    Logger.log(f"  输出目录: {output_dir}")
    Logger.log("")

    generator = PromptGenerator(docs_dir, output_dir, lang, verbose=verbose)
    generator.generate_all()
    Logger.log("")


if __name__ == "__main__":
    main()
