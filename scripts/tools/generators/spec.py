"""AI 提示词与技能库的共享规格源（单一真相）

``ai_prompts``（整段注入提示词）与 ``skills``（Agent Skills 技能库）两个渲染器
的文档清单此前各维护一份硬编码列表——同批文档增删要在两处（加 docs-index 共
三处）同步。本模块把两份清单集中为唯一数据源：

- :data:`PROMPT_SPECS` / ``SECTION_*`` / ``SYSTEM_PROMPTS`` —— 提示词包规格
- :data:`SKILL_SPECS` —— 技能库规格

改「哪篇文档进提示词 / 技能」只动本文件；渲染格式在两个生成器各自的渲染器里。
"""

from dataclasses import dataclass, field


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
    # 接地前导保持极简：能力清单是文档内容的复述（模型读完文档自然具备），
    # 对被注入提示词的模型没有信息量——真正要传递的只有「文档边界」与「不编造」
    # 两条纪律；领域差异（模块 / 适配器 / 全栈）由下方 SECTION 清单本身体现。
    "module": """\
以下是 ErisPulse SDK 模块开发文档（知识库）。请基于文档内容回答；
文档未覆盖的 API 以 SDK 源码 docstring 为准，不要编造不存在的接口或行为。
""",
    "adapter": """\
以下是 ErisPulse SDK 适配器开发文档（知识库）。请基于文档内容回答；
文档未覆盖的 API 以 SDK 源码 docstring 为准，不要编造不存在的接口或行为。
""",
    "full": """\
以下是 ErisPulse SDK 开发文档（模块与适配器开发全量知识库）。请基于文档内容回答；
文档未覆盖的 API 以 SDK 源码 docstring 为准，不要编造不存在的接口或行为。
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
        DocEntry("模块测试（ErisPulse-Testing）", "developer-guide/testing.md"),
        DocEntry("CLI 命令参考", "user-guide/cli-reference.md"),
    ],
)

SECTION_ADVANCED_MODULE = Section(
    title="高级主题",
    entries=[
        DocEntry("Conversation 多轮对话", "advanced/conversation.md"),
        DocEntry("交互会话系统", "advanced/interaction.md"),
        DocEntry("模块间通信", "advanced/module-communication.md"),
        DocEntry("MessageBuilder 详解", "advanced/message-builder.md"),
        DocEntry("HTTP 客户端", "advanced/http-client.md"),
        DocEntry("SQL 查询构建器", "advanced/sql-builder.md"),
        DocEntry("路由系统", "advanced/router.md"),
        DocEntry("生命周期管理", "advanced/lifecycle.md"),
        DocEntry("懶加载系统", "advanced/lazy-loading.md"),
        DocEntry("国际化（i18n）系统", "advanced/i18n.md"),
        DocEntry("统一控制面（scope）", "advanced/scope.md"),
        DocEntry("归属权（owner）系统", "advanced/ownership.md"),
        DocEntry("影子模块与灰度转正", "advanced/shadow.md"),
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
        DocEntry("归属权（owner）系统", "advanced/ownership.md"),
        DocEntry("影子模块与灰度转正", "advanced/shadow.md"),
        DocEntry("模块间通信", "advanced/module-communication.md"),
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
        DocEntry("交互会话系统", "advanced/interaction.md"),
        DocEntry("模块间通信", "advanced/module-communication.md"),
        DocEntry("国际化（i18n）系统", "advanced/i18n.md"),
        DocEntry("统一控制面（scope）", "advanced/scope.md"),
        DocEntry("归属权（owner）系统", "advanced/ownership.md"),
        DocEntry("影子模块与灰度转正", "advanced/shadow.md"),
        DocEntry("启动流程与手动控制", "advanced/startup.md"),
    ],
)

SECTION_ECOSYSTEM = Section(
    title="生态模块",
    entries=[
        DocEntry("ErisPulse-App 安装与使用", "ecosystem/app.md"),
        DocEntry("Dashboard 使用与视窗注册", "ecosystem/dashboard.md"),
        DocEntry("Cron 定时任务", "ecosystem/cron.md"),
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
                    DocEntry("数据模型层（ORM）", "developer-guide/orm.md"),
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
                    DocEntry("数据模型层（ORM）", "developer-guide/orm.md"),
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
        ],
    ),
]


# ============================================================================
# Agent Skills 规格（与提示词包同源不同形：整段注入 vs frontmatter 按需加载）
# ============================================================================

@dataclass
class SkillDoc:
    """技能内的单篇文档条目"""

    title: str
    path: str  # 相对语言文档目录的路径


@dataclass
class SkillSpec:
    """技能定义：一个主题技能 = 多篇文档的聚合"""

    name: str  # kebab-case 技能名
    title: str  # 技能标题
    audience: str  # 一句话定位（写给谁、解决什么）
    docs: list[SkillDoc]


SKILL_SPECS: list[SkillSpec] = [
    SkillSpec(
        name="erispulse-getting-started",
        title="快速上手与核心概念",
        audience="第一次接触 ErisPulse，想从零跑起一个机器人并理解核心概念",
        docs=[
            SkillDoc("文档总入口与阅读路径", "README.md"),
            SkillDoc("快速开始", "quick-start.md"),
            SkillDoc("第一个机器人", "getting-started/first-bot.md"),
            SkillDoc("基础概念", "getting-started/basic-concepts.md"),
            SkillDoc("事件处理", "getting-started/event-handling.md"),
            SkillDoc("常见任务", "getting-started/common-tasks.md"),
            SkillDoc("IDE 补全", "getting-started/ide-completion.md"),
        ],
    ),
    SkillSpec(
        name="erispulse-module-dev",
        title="模块开发",
        audience="要开发 ErisPulse 模块（业务逻辑载体）：命令、事件、多轮对话、ORM",
        docs=[
            SkillDoc("模块开发入门", "developer-guide/modules/getting-started.md"),
            SkillDoc("模块核心概念", "developer-guide/modules/core-concepts.md"),
            SkillDoc("Event 包装类", "developer-guide/modules/event-wrapper.md"),
            SkillDoc("模块最佳实践", "developer-guide/modules/best-practices.md"),
            SkillDoc("ORM 数据模型", "developer-guide/orm.md"),
            SkillDoc("多轮对话", "advanced/conversation.md"),
            SkillDoc("交互会话", "advanced/interaction.md"),
        ],
    ),
    SkillSpec(
        name="erispulse-adapter-dev",
        title="适配器开发",
        audience="要把一个聊天平台接入 ErisPulse：协议转换、发送规范、发布流程",
        docs=[
            SkillDoc("适配器开发入门", "developer-guide/adapters/getting-started.md"),
            SkillDoc("适配器核心概念", "developer-guide/adapters/core-concepts.md"),
            SkillDoc("发送 DSL", "developer-guide/adapters/send-dsl.md"),
            SkillDoc("转换器", "developer-guide/adapters/converter.md"),
            SkillDoc("适配器最佳实践", "developer-guide/adapters/best-practices.md"),
            SkillDoc("适配器发布", "developer-guide/adapters/publishing.md"),
            SkillDoc("平台接入指南索引", "platform-guide/README.md"),
        ],
    ),
    SkillSpec(
        name="erispulse-adapter-standards",
        title="适配器技术标准",
        audience="实现/评审适配器时需要对照的硬性技术规范",
        docs=[
            SkillDoc("标准化总纲", "standards/standardization-guide.md"),
            SkillDoc("会话类型", "standards/session-types.md"),
            SkillDoc("事件转换", "standards/event-conversion.md"),
            SkillDoc("发送方法规范", "standards/send-method-spec.md"),
            SkillDoc("API 动作规范", "standards/api-action-spec.md"),
            SkillDoc("API 响应规范", "standards/api-response.md"),
            SkillDoc("请求动作规范", "standards/request-action-spec.md"),
        ],
    ),
    SkillSpec(
        name="erispulse-config-cli",
        title="配置系统与 CLI 工具链",
        audience="配置声明式 schema、排查配置问题、使用 epsdk 命令行与部署",
        docs=[
            SkillDoc("配置系统", "user-guide/configuration.md"),
            SkillDoc("CLI 参考", "user-guide/cli-reference.md"),
            SkillDoc("安装", "user-guide/installation.md"),
            SkillDoc("部署", "user-guide/deployment.md"),
        ],
    ),
    SkillSpec(
        name="erispulse-hot-reload",
        title="热重载与懒加载休眠",
        audience="改代码不重启（热重载）、闲置自动归眠（dormant_after）、运行时注册模块",
        docs=[
            SkillDoc("懒加载与休眠", "advanced/lazy-loading.md"),
            SkillDoc("模块开发入门（加载策略）", "developer-guide/modules/getting-started.md"),
        ],
    ),
    SkillSpec(
        name="erispulse-scope-ownership",
        title="权限作用域与归属权",
        audience="写生产级模块绕不开的两套机制：谁能收到什么（scope）、资源归谁怎么回收（ownership）",
        docs=[
            SkillDoc("作用域", "advanced/scope.md"),
            SkillDoc("归属权", "advanced/ownership.md"),
            SkillDoc("生命周期", "advanced/lifecycle.md"),
        ],
    ),
    SkillSpec(
        name="erispulse-communication",
        title="通信与连接",
        audience="模块间通信（RPC/定向/广播）、HTTP/WS 客户端、连接管理",
        docs=[
            SkillDoc("模块间通信", "advanced/module-communication.md"),
            SkillDoc("连接管理", "advanced/connections.md"),
            SkillDoc("HTTP 客户端", "advanced/http-client.md"),
            SkillDoc("路由", "advanced/router.md"),
        ],
    ),
    SkillSpec(
        name="erispulse-shadow-transcript",
        title="影子灰度与消息追踪",
        audience="新旧版本灰度对照（shadow）、消息收件箱与行为追踪（transcript）",
        docs=[
            SkillDoc("影子模块", "advanced/shadow.md"),
            SkillDoc("消息追踪", "advanced/transcript.md"),
        ],
    ),
    SkillSpec(
        name="erispulse-errors-troubleshooting",
        title="异常体系与排障",
        audience="遇到异常/组件不工作时的诊断路径：异常总览、排障指南、bug 追踪",
        docs=[
            SkillDoc("异常捕获总览", "advanced/errors.md"),
            SkillDoc("已知问题追踪", "bug-tracker.md"),
        ],
    ),
    SkillSpec(
        name="erispulse-ecosystem",
        title="生态与多平台",
        audience="了解生态组件（Dashboard/Cron/AI 模块等）与各平台适配器的接入差异",
        docs=[
            SkillDoc("生态总览", "ecosystem/README.md"),
            SkillDoc("Dashboard", "ecosystem/dashboard.md"),
            SkillDoc("定时任务", "ecosystem/cron.md"),
            SkillDoc("AI 对话模块", "ecosystem/qvqchat.md"),
            SkillDoc("MCP 桥", "ecosystem/apimcp.md"),
            SkillDoc("平台指南索引", "platform-guide/README.md"),
        ],
    ),
]

