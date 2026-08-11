"""
ErisPulse 文档索引生成器

自动扫描 docs/ 目录，生成文档映射索引和搜索索引

特性：
- 多语言分类映射（zh-CN / zh-TW / en / ja / ru）
- 按优先级排序分类与文档
- 支持子分组（如 "模块开发" / "适配器开发"）
- 同时输出映射索引（docs-mapping.json）与搜索索引（docs-search-index.json）

使用方法:
    python scripts/tools/generate-docs-index.py
    python scripts/tools/generate-docs-index.py --lang zh-CN
    python scripts/tools/generate-docs-index.py --docs docs --output docs/_meta
"""

import os
import re
import json
import argparse
import sys
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path


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
    def progress(cls, rel_path: str, status: str, detail: str = ""):
        """
        输出单条文档解析进度

        :param rel_path: 文件相对路径
        :param status: 状态标识（parse/skip/warn/done 等）
        :param detail: 附加详情，可选
        """
        tag = {
            "parse": "[PARSE]",
            "skip": "[SKIP]",
            "warn": "[WARN]",
            "done": "[DONE]",
        }.get(status, f"[{status.upper()}]")
        line = f"  {tag} {rel_path}"
        if detail:
            line += f"  {detail}"
        cls.log(line)


class DocsIndexGenerator:
    """文档索引生成器

    根据语言生成 Markdown 文档的映射索引与搜索索引，
    支持多语言分类映射、优先级排序以及子分组展示。
    """

    # 多语言分类映射配置
    CATEGORY_TRANSLATIONS = {
        # 中文 (zh-CN)
        "zh-CN": {
            "category_map": {
                "getting-started": "入门指南",
                "user-guide": "用户使用指南",
                "developer-guide": "开发者指南",
                "platform-guide": "平台特性指南",
                "api-reference": "API 参考",
                "advanced": "高级主题",
                "ecosystem": "生态模块",
                "ai-support": "AI 辅助开发",
                "standards": "技术标准",
                "styleguide": "风格指南",
                "contributing": "贡献指南",
            },
            "descriptions": {
                "快速开始": "ErisPulse 快速入门指南",
                "入门指南": "ErisPulse 基础概念和使用教程",
                "用户使用指南": "ErisPulse 配置和命令参考",
                "开发者指南": "模块和适配器开发指南",
                "平台特性指南": "各平台特性和适配器说明",
                "API 参考": "核心 API 和接口文档",
                "高级主题": "深入理解框架的高级特性",
                "生态模块": "社区维护的第三方扩展模块",
                "AI 辅助开发": "使用 AI 辅助开发 ErisPulse",
                "技术标准": "框架的技术规范和标准",
                "风格指南": "代码和文档风格规范",
                "贡献指南": "参与 ErisPulse 项目共建",
            },
            "priority": {
                "快速开始": 1,
                "入门指南": 2,
                "用户使用指南": 3,
                "开发者指南": 4,
                "平台特性指南": 5,
                "API 参考": 6,
                "高级主题": 7,
                "生态模块": 8,
                "AI 辅助开发": 9,
                "技术标准": 10,
                "风格指南": 11,
                "贡献指南": 12,
            },
        },
        # 英文 (en)
        "en": {
            "category_map": {
                "getting-started": "Getting Started",
                "user-guide": "User Guide",
                "developer-guide": "Developer Guide",
                "platform-guide": "Platform Guide",
                "api-reference": "API Reference",
                "advanced": "Advanced Topics",
                "ecosystem": "Ecosystem Modules",
                "ai-support": "AI-Assisted Development",
                "standards": "Technical Standards",
                "styleguide": "Style Guide",
                "contributing": "Contributing",
            },
            "descriptions": {
                "Quick Start": "ErisPulse Quick Start Guide",
                "Getting Started": "ErisPulse basic concepts and tutorials",
                "User Guide": "ErisPulse configuration and command reference",
                "Developer Guide": "Module and adapter development guides",
                "Platform Guide": "Platform features and adapter documentation",
                "API Reference": "Core API and interface documentation",
                "Advanced Topics": "Deep dive into advanced framework features",
                "Ecosystem Modules": "Community-maintained third-party modules",
                "AI-Assisted Development": "Using AI to assist ErisPulse development",
                "Technical Standards": "Framework technical specifications and standards",
                "Style Guide": "Code and documentation style guidelines",
                "Contributing": "Contribute to ErisPulse",
            },
            "priority": {
                "Quick Start": 1,
                "Getting Started": 2,
                "User Guide": 3,
                "Developer Guide": 4,
                "Platform Guide": 5,
                "API Reference": 6,
                "Advanced Topics": 7,
                "Ecosystem Modules": 8,
                "AI-Assisted Development": 9,
                "Technical Standards": 10,
                "Style Guide": 11,
                "Contributing": 12,
            },
        },
        # 繁体中文 (zh-TW)
        "zh-TW": {
            "category_map": {
                "getting-started": "入門指南",
                "user-guide": "使用者指南",
                "developer-guide": "開發者指南",
                "platform-guide": "平台特性指南",
                "api-reference": "API 參考",
                "advanced": "進階主題",
                "ecosystem": "生態模組",
                "ai-support": "AI 輔助開發",
                "standards": "技術標準",
                "styleguide": "風格指南",
                "contributing": "貢獻指南",
            },
            "descriptions": {
                "快速開始": "ErisPulse 快速入門指南",
                "入門指南": "ErisPulse 基礎概念和使用教程",
                "使用者指南": "ErisPulse 配置和命令參考",
                "開發者指南": "模組和適配器開發指南",
                "平台特性指南": "各平台特性和適配器說明",
                "API 參考": "核心 API 和介面文檔",
                "進階主題": "深入理解框架的進階特性",
                "生態模組": "社群維護的第三方擴展模組",
                "AI 輔助開發": "使用 AI 輔助開發 ErisPulse",
                "技術標準": "框架的技術規範和標準",
                "風格指南": "代碼和文檔風格規範",
                "貢獻指南": "參與 ErisPulse 專案共建",
            },
            "priority": {
                "快速開始": 1,
                "入門指南": 2,
                "使用者指南": 3,
                "開發者指南": 4,
                "平台特性指南": 5,
                "API 參考": 6,
                "進階主題": 7,
                "生態模組": 8,
                "AI 輔助開發": 9,
                "技術標準": 10,
                "風格指南": 11,
                "貢獻指南": 12,
            },
        },
        # 日语 (ja)
        "ja": {
            "category_map": {
                "getting-started": "入門ガイド",
                "user-guide": "ユーザーガイド",
                "developer-guide": "開発者ガイド",
                "platform-guide": "プラットフォームガイド",
                "api-reference": "API リファレンス",
                "advanced": "高度なトピック",
                "ecosystem": "エコシステムモジュール",
                "ai-support": "AI 支援開発",
                "standards": "技術標準",
                "styleguide": "スタイルガイド",
                "contributing": "コントリビュート",
            },
            "descriptions": {
                "クイックスタート": "ErisPulse クイックスタートガイド",
                "入門ガイド": "ErisPulse の基本概念とチュートリアル",
                "ユーザーガイド": "ErisPulse の設定とコマンドリファレンス",
                "開発者ガイド": "モジュールとアダプターの開発ガイド",
                "プラットフォームガイド": "各プラットフォームの機能とアダプターの説明",
                "API リファレンス": "コア API とインターフェースドキュメント",
                "高度なトピック": "フレームワークの高度な機能を深く理解する",
                "エコシステムモジュール": "コミュニティが保守するサードパーティモジュール",
                "AI 支援開発": "AI を活用した ErisPulse 開発",
                "技術標準": "フレームワークの技術仕様と標準",
                "スタイルガイド": "コードとドキュメントのスタイルガイドライン",
                "コントリビュート": "ErisPulse への貢献",
            },
            "priority": {
                "クイックスタート": 1,
                "入門ガイド": 2,
                "ユーザーガイド": 3,
                "開発者ガイド": 4,
                "プラットフォームガイド": 5,
                "API リファレンス": 6,
                "高度なトピック": 7,
                "エコシステムモジュール": 8,
                "AI 支援開発": 9,
                "技術標準": 10,
                "スタイルガイド": 11,
                "コントリビュート": 12,
            },
        },
        # 俄语 (ru)
        "ru": {
            "category_map": {
                "getting-started": "Начало работы",
                "user-guide": "Руководство пользователя",
                "developer-guide": "Руководство разработчика",
                "platform-guide": "Руководство по платформам",
                "api-reference": "Справочник API",
                "advanced": "Продвинутые темы",
                "ecosystem": "Модули экосистемы",
                "ai-support": "Разработка с ИИ",
                "standards": "Технические стандарты",
                "styleguide": "Руководство по стилю",
                "contributing": "Вклад",
            },
            "descriptions": {
                "Быстрый старт": "Краткое руководство по ErisPulse",
                "Начало работы": "Основные концепции и учебные материалы ErisPulse",
                "Руководство пользователя": "Настройка и справочник команд ErisPulse",
                "Руководство разработчика": "Руководство по разработке модулей и адаптеров",
                "Руководство по платформам": "Возможности платформ и документация адаптеров",
                "Справочник API": "Документация по основному API и интерфейсам",
                "Продвинутые темы": "Глубокое изучение продвинутых функций фреймворка",
                "Модули экосистемы": "Сторонние модули, поддерживаемые сообществом",
                "Разработка с ИИ": "Использование ИИ для разработки ErisPulse",
                "Технические стандарты": "Технические спецификации и стандарты фреймворка",
                "Руководство по стилю": "Руководство по стилю кода и документации",
                "Вклад": "Вклад в проект ErisPulse",
            },
            "priority": {
                "Быстрый старт": 1,
                "Начало работы": 2,
                "Руководство пользователя": 3,
                "Руководство разработчика": 4,
                "Руководство по платформам": 5,
                "Справочник API": 6,
                "Продвинутые темы": 7,
                "Модули экосистемы": 8,
                "Разработка с ИИ": 9,
                "Технические стандарты": 10,
                "Руководство по стилю": 11,
                "Вклад": 12,
            },
        },
    }

    # 文档优先级（数值越小越靠前）
    DOC_PRIORITY = {
        # 快速开始 / 根目录
        "README.md": 1,
        "quick-start.md": 2,
        "architecture.md": 3,
        "bug-tracker.md": 99,
        # 入门指南
        "getting-started/first-bot.md": 1,
        "getting-started/README.md": 2,
        "getting-started/basic-concepts.md": 3,
        "getting-started/common-tasks.md": 4,
        "getting-started/event-handling.md": 5,
        "getting-started/ide-completion.md": 6,
        # 用户使用指南
        "user-guide/README.md": 1,
        "user-guide/installation.md": 2,
        "user-guide/configuration.md": 3,
        "user-guide/cli-reference.md": 4,
        "user-guide/deployment.md": 5,
        # 开发者指南
        "developer-guide/README.md": 1,
        "developer-guide/modules/getting-started.md": 2,
        "developer-guide/modules/core-concepts.md": 3,
        "developer-guide/modules/event-wrapper.md": 4,
        "developer-guide/modules/best-practices.md": 5,
        "developer-guide/adapters/getting-started.md": 6,
        "developer-guide/adapters/core-concepts.md": 7,
        "developer-guide/adapters/send-dsl.md": 8,
        "developer-guide/adapters/best-practices.md": 9,
        "developer-guide/publishing.md": 10,
        "developer-guide/adapters/converter.md": 11,
        # 平台特性指南
        "platform-guide/README.md": 1,
        "platform-guide/onebot11.md": 2,
        "platform-guide/onebot12.md": 3,
        "platform-guide/telegram.md": 4,
        "platform-guide/email.md": 5,
        "platform-guide/yunhu.md": 6,
        "platform-guide/yunhu_user.md": 7,
        "platform-guide/qqbot.md": 8,
        "platform-guide/kook.md": 9,
        "platform-guide/matrix.md": 10,
        "platform-guide/discord.md": 11,
        "platform-guide/wechatmp.md": 12,
        "platform-guide/webhook.md": 13,
        "platform-guide/ideaura.md": 14,
        "platform-guide/maintain-notes.md": 99,
        # API 参考
        "api-reference/README.md": 1,
        "api-reference/adapter-system.md": 2,
        "api-reference/core-modules.md": 3,
        "api-reference/event-system.md": 4,
        # 高级主题
        "advanced/README.md": 1,
        "advanced/lifecycle.md": 2,
        "advanced/lazy-loading.md": 3,
        "advanced/router.md": 4,
        "advanced/message-builder.md": 5,
        "advanced/session-types.md": 6,
        "advanced/conversation.md": 7,
        "advanced/dashboard-view.md": 8,
        "advanced/http-client.md": 9,
        "advanced/sql-builder.md": 10,
        "advanced/i18n.md": 11,
        # AI 辅助开发
        "ai-support/README.md": 1,
        # 技术标准
        "standards/README.md": 1,
        "standards/session-types.md": 2,
        "standards/api-response.md": 3,
        "standards/event-conversion.md": 4,
        "standards/send-method-spec.md": 5,
        "standards/request-action-spec.md": 6,
        "standards/api-action-spec.md": 7,
        # 风格指南
        "styleguide/README.md": 1,
        "styleguide/docstring.md": 2,
        # 贡献指南
        "contributing/README.md": 1,
        "contributing/first-contribution.md": 2,
    }

    # 需要忽略的目录
    # - ai-support/prompts: 提示词模板，非用户文档
    # - api-reference/auto_api: 自动生成的 API 文档，单独生成独立索引（generate_auto_api_index）
    # - styleguide / contributing: 框架自身使用的规范，不进入面向用户的 docs_meta
    IGNORE_DIRS = {
        "ai-support/prompts",
        "api-reference/auto_api",
        "styleguide",
        "contributing",
    }

    # 子分组显示名称（按语言映射）
    SUBGROUP_NAMES = {
        "modules": {
            "zh-CN": "模块开发",
            "en": "Modules",
            "zh-TW": "模組開發",
            "ja": "モジュール開発",
            "ru": "Разработка модулей",
        },
        "adapters": {
            "zh-CN": "适配器开发",
            "en": "Adapters",
            "zh-TW": "適配器開發",
            "ja": "アダプター開発",
            "ru": "Разработка адаптеров",
        },
        "prompts": {
            "zh-CN": "提示词模板",
            "en": "Prompt Templates",
            "zh-TW": "提示詞模板",
            "ja": "プロンプトテンプレート",
            "ru": "Шаблоны промптов",
        },
    }

    # 分类图标（按目录名，跨语言统一，使用 Font Awesome 类名）
    # 未配置的分类回退到 fa-folder
    CATEGORY_ICONS = {
        "getting-started": "fa-rocket",
        "user-guide": "fa-book-open",
        "developer-guide": "fa-code",
        "platform-guide": "fa-plug",
        "api-reference": "fa-book",
        "advanced": "fa-fire",
        "ecosystem": "fa-cubes",
        "ai-support": "fa-robot",
        "standards": "fa-gavel",
    }

    # 子分组图标（与 SUBGROUP_NAMES 同 key）
    SUBGROUP_ICONS = {
        "modules": "fa-puzzle-piece",
        "adapters": "fa-network-wired",
        "prompts": "fa-comment-dots",
    }

    # 文档项图标（按精确相对路径，未配置则按所在分类目录回退）
    DOC_ICONS = {
        # 根目录 / 快速开始
        "README.md": "fa-flag",
        "quick-start.md": "fa-bolt",
        "architecture.md": "fa-sitemap",
        "bug-tracker.md": "fa-bug",
        # 入门指南
        "getting-started/README.md": "fa-door-open",
        "getting-started/first-bot.md": "fa-robot",
        "getting-started/basic-concepts.md": "fa-lightbulb",
        "getting-started/common-tasks.md": "fa-list-check",
        "getting-started/event-handling.md": "fa-bolt-lightning",
        "getting-started/ide-completion.md": "fa-keyboard",
        # 用户使用指南
        "user-guide/README.md": "fa-book-open",
        "user-guide/installation.md": "fa-download",
        "user-guide/configuration.md": "fa-sliders",
        "user-guide/cli-reference.md": "fa-terminal",
        "user-guide/deployment.md": "fa-cloud-arrow-up",
        # 开发者指南
        "developer-guide/README.md": "fa-code",
        "developer-guide/modules/getting-started.md": "fa-puzzle-piece",
        "developer-guide/modules/core-concepts.md": "fa-cubes-stacked",
        "developer-guide/modules/event-wrapper.md": "fa-bolt-lightning",
        "developer-guide/modules/best-practices.md": "fa-award",
        "developer-guide/adapters/getting-started.md": "fa-network-wired",
        "developer-guide/adapters/core-concepts.md": "fa-microchip",
        "developer-guide/adapters/send-dsl.md": "fa-code-branch",
        "developer-guide/adapters/best-practices.md": "fa-medal",
        "developer-guide/adapters/converter.md": "fa-exchange-alt",
        "developer-guide/publishing.md": "fa-upload",
        # 平台特性指南
        "platform-guide/README.md": "fa-server",
        "platform-guide/onebot11.md": "fa-comments",
        "platform-guide/onebot12.md": "fa-comments",
        "platform-guide/telegram.md": "fa-paper-plane",
        "platform-guide/email.md": "fa-envelope",
        "platform-guide/yunhu.md": "fa-cloud",
        "platform-guide/yunhu_user.md": "fa-user",
        "platform-guide/qqbot.md": "fa-comment-dots",
        "platform-guide/kook.md": "fa-headset",
        "platform-guide/matrix.md": "fa-th-large",
        "platform-guide/discord.md": "fa-gamepad",
        "platform-guide/wechatmp.md": "fa-mobile-screen",
        "platform-guide/webhook.md": "fa-link",
        "platform-guide/ideaura.md": "fa-wand-magic-sparkles",
        "platform-guide/maintain-notes.md": "fa-wrench",
        # API 参考
        "api-reference/README.md": "fa-book",
        "api-reference/adapter-system.md": "fa-network-wired",
        "api-reference/core-modules.md": "fa-cubes-stacked",
        "api-reference/event-system.md": "fa-bolt-lightning",
        # 高级主题
        "advanced/README.md": "fa-fire",
        "advanced/lifecycle.md": "fa-clock-rotate-left",
        "advanced/lazy-loading.md": "fa-hourglass-half",
        "advanced/router.md": "fa-route",
        "advanced/message-builder.md": "fa-comment-dots",
        "advanced/session-types.md": "fa-layer-group",
        "advanced/conversation.md": "fa-comments",
        "advanced/dashboard-view.md": "fa-table-columns",
        "advanced/http-client.md": "fa-globe",
        "advanced/sql-builder.md": "fa-database",
        "advanced/i18n.md": "fa-language",
        # AI 辅助开发
        "ai-support/README.md": "fa-robot",
        # 技术标准
        "standards/README.md": "fa-gavel",
        "standards/session-types.md": "fa-layer-group",
        "standards/api-response.md": "fa-arrow-right-arrow-left",
        "standards/event-conversion.md": "fa-shuffle",
        "standards/send-method-spec.md": "fa-paper-plane",
        "standards/request-action-spec.md": "fa-hand-paper",
        "standards/api-action-spec.md": "fa-bolt",
    }

    # ==================== auto_api 独立索引配置 ====================
    # auto_api 已在 IGNORE_DIRS 中，不进入主索引；通过 run_auto_api() 单独生成
    # AUTO_API_CATEGORY_NAMES: 独立索引中的"分类名"（按语言）
    AUTO_API_CATEGORY_NAMES = {
        "zh-CN": "自动生成 API",
        "en": "Auto-generated API",
        "zh-TW": "自動生成 API",
        "ja": "自動生成 API",
        "ru": "Автосгенерированный API",
    }

    # AUTO_API_SUBGROUP_NAMES: 按 ErisPulse/ 下的第一级子目录分组
    AUTO_API_SUBGROUP_NAMES = {
        "CLI": {
            "zh-CN": "CLI 命令行",
            "en": "CLI",
            "zh-TW": "CLI 命令列",
            "ja": "CLI コマンド",
            "ru": "CLI",
        },
        "Core": {
            "zh-CN": "核心模块",
            "en": "Core",
            "zh-TW": "核心模組",
            "ja": "コアモジュール",
            "ru": "Ядро",
        },
        "finders": {
            "zh-CN": "模块查找器",
            "en": "Finders",
            "zh-TW": "模組尋找器",
            "ja": "モジュールファインダー",
            "ru": "Поисковики",
        },
        "loaders": {
            "zh-CN": "模块加载器",
            "en": "Loaders",
            "zh-TW": "模組載入器",
            "ja": "モジュールローダー",
            "ru": "Загрузчики",
        },
        "runtime": {
            "zh-CN": "运行时",
            "en": "Runtime",
            "zh-TW": "執行時",
            "ja": "ランタイム",
            "ru": "Среда выполнения",
        },
    }

    # AUTO_API_SUBGROUP_ICONS: 子分组图标
    AUTO_API_SUBGROUP_ICONS = {
        "CLI": "fa-terminal",
        "Core": "fa-microchip",
        "finders": "fa-search",
        "loaders": "fa-download",
        "runtime": "fa-gears",
    }

    def __init__(self, docs_dir: str, output_dir: str, lang: Optional[str] = None):
        """
        初始化索引生成器

        :param docs_dir: 文档根目录
        :param output_dir: 索引输出目录
        :param lang: 语言代码（None 表示根目录模式）
        """
        self.docs_dir = Path(docs_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.lang = lang
        self.docs_mapping: Dict = {}
        self.docs_search_index: Dict = {}

        # 如果指定了语言，实际文档目录是 docs/{lang}
        if self.lang:
            self.actual_docs_dir = self.docs_dir / self.lang
        else:
            self.actual_docs_dir = self.docs_dir

        # 根据语言初始化分类映射
        self._init_category_mappings()

    def _init_category_mappings(self):
        """根据语言初始化分类映射表、描述与优先级

        未匹配语言时回退到中文映射。"""
        if self.lang and self.lang in self.CATEGORY_TRANSLATIONS:
            # 使用指定语言的映射
            lang_config = self.CATEGORY_TRANSLATIONS[self.lang]
            self.CATEGORY_MAP = lang_config["category_map"]
            self.CATEGORY_DESCRIPTIONS = lang_config["descriptions"]
            self.CATEGORY_PRIORITY = lang_config["priority"]
        else:
            # 默认使用中文映射
            lang_config = self.CATEGORY_TRANSLATIONS["zh-CN"]
            self.CATEGORY_MAP = lang_config["category_map"]
            self.CATEGORY_DESCRIPTIONS = lang_config["descriptions"]
            self.CATEGORY_PRIORITY = lang_config["priority"]

    @staticmethod
    def get_available_languages(docs_dir: Path) -> List[str]:
        """
        获取可用的语言列表

        :param docs_dir: 文档根目录
        :return: 语言代码列表
        """
        langs = []
        for item in docs_dir.iterdir():
            # 排除 _meta 和 README.md
            if item.is_dir() and item.name not in ["_meta"]:
                langs.append(item.name)
        return sorted(langs)

    def normalize_path(self, path: Path) -> str:
        """
        规范化路径，将反斜杠转换为正斜杠

        :param path: 文件路径
        :return: 规范化后的路径字符串（相对于语言目录）
        """
        # 获取相对于实际文档目录的路径（不包含语言代码）
        rel_path = path.relative_to(self.actual_docs_dir)
        # 使用 / 作为分隔符
        return str(rel_path).replace("\\", "/")

    def get_category(self, file_path: Path) -> str:
        """
        根据文件路径获取分类

        :param file_path: 文件路径
        :return: 分类名称
        """
        # 获取相对于实际文档目录的路径
        rel_path = file_path.relative_to(self.actual_docs_dir)

        # 根目录文件归类为快速开始（根据语言）
        if len(rel_path.parts) == 1:
            # 从优先级配置中获取第一个分类键（即"快速开始"的本地化名称）
            if self.CATEGORY_PRIORITY:
                return list(self.CATEGORY_PRIORITY.keys())[0]
            return "Quick Start"

        # 根据目录名称分类
        dir_name = rel_path.parts[0]
        if dir_name in self.CATEGORY_MAP:
            return self.CATEGORY_MAP[dir_name]

        # 默认分类
        return "Other"

    def get_category_dir(self, category_name: str) -> str:
        """
        根据本地化分类名反查目录名（用于图标查询）

        :param category_name: 本地化分类名（如 "入门指南"）
        :return: 目录名（如 "getting-started"），未匹配返回空串
        """
        reverse_map = {v: k for k, v in self.CATEGORY_MAP.items()}
        return reverse_map.get(category_name, "")

    def get_category_icon(self, category_name: str) -> str:
        """
        根据分类名获取图标类名

        :param category_name: 本地化分类名
        :return: Font Awesome 图标类名（未配置返回 fa-folder）
        """
        category_dir = self.get_category_dir(category_name)
        # 根目录文档（快速开始类）回退到 rocket
        if not category_dir:
            return self.CATEGORY_ICONS.get("getting-started", "fa-folder")
        return self.CATEGORY_ICONS.get(category_dir, "fa-folder")

    def get_doc_icon(self, doc_path: str, category_name: str, subgroup_key: Optional[str] = None) -> str:
        """
        根据文档路径获取图标类名

        解析顺序：精确路径 → 子分组 → 分类 → 默认

        :param doc_path: 文档相对路径
        :param category_name: 所属本地化分类名
        :param subgroup_key: 子分组 key（可选）
        :return: Font Awesome 图标类名
        """
        # 1. 精确路径
        if doc_path in self.DOC_ICONS:
            return self.DOC_ICONS[doc_path]
        # 2. 子分组图标
        if subgroup_key and subgroup_key in self.SUBGROUP_ICONS:
            return self.SUBGROUP_ICONS[subgroup_key]
        # 3. 分类图标
        category_icon = self.get_category_icon(category_name)
        if category_icon != "fa-folder":
            return category_icon
        # 4. 默认
        return "fa-file-alt"

    def get_subgroup_icon(self, subgroup_key: str) -> str:
        """
        根据子分组 key 获取图标类名

        :param subgroup_key: 子分组 key（如 "modules"）
        :return: Font Awesome 图标类名（未配置返回 fa-folder）
        """
        return self.SUBGROUP_ICONS.get(subgroup_key, "fa-folder")

    def parse_headings(self, content: str) -> List[Dict]:
        """
        解析 Markdown 文档中的标题

        :param content: Markdown 内容
        :return: 标题列表，每个标题包含 level, text, line
        """
        headings = []
        lines = content.split("\n")

        in_code_block = False
        code_block_pattern = re.compile(r"^```")

        for line_num, line in enumerate(lines, start=1):
            # 检测代码块开始/结束
            if code_block_pattern.match(line):
                in_code_block = not in_code_block
                continue

            # 跳过代码块内的内容
            if in_code_block:
                continue

            # 匹配 # 到 ###### 的标题
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({"level": level, "text": text, "line": line_num})

        return headings

    def get_document_title(self, headings: List[Dict], file_path: Path) -> str:
        """
        获取文档标题（第一个一级标题）

        :param headings: 标题列表
        :param file_path: 文件路径（备用）
        :return: 文档标题
        """
        if not headings:
            # 如果没有标题，使用文件名
            return file_path.stem.replace("-", " ").replace("_", " ").title()

        # 查找第一个一级标题
        for heading in headings:
            if heading["level"] == 1:
                return heading["text"]

        # 如果没有一级标题，使用第一个标题
        return headings[0]["text"]

    def scan_docs(self) -> List[Dict]:
        """
        扫描文档目录，收集所有 Markdown 文件

        :return: 文件信息列表
        """
        files = []

        # 使用 actual_docs_dir 作为扫描根目录
        if not self.actual_docs_dir.exists():
            return files

        for root, dirs, filenames in os.walk(self.actual_docs_dir):
            # 过滤需要忽略的目录
            dirs[:] = [
                d
                for d in dirs
                if not any(
                    Path(root) / d
                    == self.actual_docs_dir / ignored_dir.replace("/", os.sep)
                    for ignored_dir in self.IGNORE_DIRS
                )
            ]

            for filename in filenames:
                if filename.endswith(".md"):
                    file_path = Path(root) / filename
                    file_info = {
                        "path": file_path,
                        "relative_path": self.normalize_path(file_path),
                        "category": self.get_category(file_path),
                    }
                    files.append(file_info)

        # 按相对路径排序，确保每次生成的顺序一致
        files.sort(key=lambda x: x["relative_path"])

        return files

    def parse_document(self, file_info: Dict) -> Optional[Dict]:
        """
        解析单个文档

        :param file_info: 文件信息
        :return: 解析后的文档信息
        """
        file_path = file_info["path"]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            Logger.progress(file_info["relative_path"], "warn", f"读取失败: {e}")
            return None

        # 解析标题
        headings = self.parse_headings(content)

        if not headings:
            Logger.progress(file_info["relative_path"], "skip", "无标题")
            return None

        # 获取文档标题
        title = self.get_document_title(headings, file_path)

        # 获取文件修改时间
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()

        Logger.progress(file_info["relative_path"], "parse", title)

        return {
            "title": title,
            "path": file_info["relative_path"],
            "category": file_info["category"],
            "level": 1,  # 默认等级
            "headings": headings,
            "last_modified": mod_time,
        }

    def generate_mapping_index(
        self, documents: List[Dict], deprecated: bool = False
    ) -> Dict:
        """
        生成文档映射索引

        :param documents: 文档列表
        :param deprecated: 是否为弃用索引
        :return: 映射索引
        """
        categories = {}
        reverse_category_map = {v: k for k, v in self.CATEGORY_MAP.items()}

        for doc in documents:
            category = doc["category"]

            # 初始化分类（含图标）
            if category not in categories:
                categories[category] = {
                    "description": self.CATEGORY_DESCRIPTIONS.get(category, ""),
                    "icon": self.get_category_icon(category),
                    "count": 0,
                    "documents": [],
                    "_subgroups": {},
                }

            category_dir = reverse_category_map.get(category, "")
            subgroup_key = None

            if category_dir:
                prefix = category_dir + "/"
                if doc["path"].startswith(prefix):
                    remainder = doc["path"][len(prefix) :]
                    parts = remainder.split("/")
                    if len(parts) > 1:
                        subgroup_key = parts[0]

            doc_entry = {
                "title": doc["title"],
                "path": doc["path"],
                "level": doc["level"],
                "icon": self.get_doc_icon(doc["path"], category, subgroup_key),
            }

            if subgroup_key:
                if subgroup_key not in categories[category]["_subgroups"]:
                    lang = self.lang or "zh-CN"
                    subgroup_name = self.SUBGROUP_NAMES.get(subgroup_key, {}).get(
                        lang, subgroup_key.replace("-", " ").replace("_", " ").title()
                    )

                    categories[category]["_subgroups"][subgroup_key] = {
                        "name": subgroup_name,
                        "icon": self.get_subgroup_icon(subgroup_key),
                        "documents": [],
                    }
                categories[category]["_subgroups"][subgroup_key]["documents"].append(
                    doc_entry
                )
            else:
                categories[category]["documents"].append(doc_entry)

            categories[category]["count"] += 1

        # 按分类优先级排序（数值越小越靠前），未定义的分类排最后
        def sort_category(item):
            category_name = item[0]
            priority = self.CATEGORY_PRIORITY.get(
                category_name, 9999
            )  # 未定义的优先级设为 9999
            return (priority, category_name)

        sorted_categories = dict(sorted(categories.items(), key=sort_category))

        # 对每个分类内的文档按优先级排序
        for category_data in sorted_categories.values():

            def sort_document(doc):
                path = doc["path"]
                priority = self.DOC_PRIORITY.get(path, 9999)  # 未定义的优先级设为 9999
                return (priority, path)

            category_data["documents"].sort(key=sort_document)

            if category_data["_subgroups"]:
                for sg_data in category_data["_subgroups"].values():
                    sg_data["documents"].sort(key=sort_document)

                def subgroup_sort_key(item):
                    sg_docs = item[1]["documents"]
                    if sg_docs:
                        first_path = sg_docs[0]["path"]
                        return self.DOC_PRIORITY.get(first_path, 9999)
                    return 9999

                category_data["subgroups"] = dict(
                    sorted(category_data["_subgroups"].items(), key=subgroup_sort_key)
                )
            else:
                category_data["subgroups"] = {}

            del category_data["_subgroups"]

        result = {
            "version": "1.2",
            # "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_categories": len(sorted_categories),
            "categories": sorted_categories,
        }

        # 如果是弃用索引，添加弃用标记
        if deprecated:
            result["_deprecated"] = True
            result["_note"] = (
                "此索引已弃用，请使用 docs/_meta/{lang}/ 目录下的语言特定索引"
            )

        return result

    def generate_search_index(self, documents: List[Dict]) -> Dict:
        """
        生成文档搜索索引

        :param documents: 文档列表
        :return: 搜索索引
        """
        keywords = {}

        for doc in documents:
            for heading in doc["headings"]:
                text = heading["text"]

                # 添加到索引
                if text not in keywords:
                    keywords[text] = []

                keywords[text].append(
                    {
                        "document": doc["path"],
                        "line": heading["line"],
                        "level": heading["level"],
                        "title": text,
                    }
                )

        # 按关键词排序，确保每次生成的顺序一致
        sorted_keywords = dict(sorted(keywords.items()))

        return {
            "version": "1.0",
            # "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_keywords": len(sorted_keywords),
            "keywords": sorted_keywords,
        }

    def save_index(self, index: Dict, filename: str):
        """
        保存索引到文件

        :param index: 索引数据
        :param filename: 文件名
        """
        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        Logger.progress(filename, "done")

    def run(self, deprecated: bool = False):
        """
        运行索引生成器

        :param deprecated: 是否为弃用模式
        """
        Logger.log("=" * 60)
        Logger.log("ErisPulse 文档索引生成器")
        Logger.log("=" * 60)
        if self.lang:
            Logger.log(f"语言: {self.lang}")
        Logger.log(f"文档目录: {self.actual_docs_dir}")
        Logger.log(f"输出目录: {self.output_dir}")
        Logger.log("")

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 扫描文档
        file_infos = self.scan_docs()
        Logger.log(f"发现 {len(file_infos)} 个 Markdown 文件")
        Logger.log("")

        # 解析文档
        Logger.log("解析文档内容...")
        documents = []
        for file_info in file_infos:
            doc = self.parse_document(file_info)
            if doc:
                documents.append(doc)
        Logger.log(f"成功解析 {len(documents)} 个文档")
        Logger.log("")

        # 生成映射索引
        Logger.log("生成文档映射索引...")
        mapping_index = self.generate_mapping_index(documents, deprecated=deprecated)
        Logger.log(f"生成 {len(mapping_index['categories'])} 个分类")
        Logger.log("")

        # 生成搜索索引
        Logger.log("生成文档搜索索引...")
        search_index = self.generate_search_index(documents)
        Logger.log(f"生成 {len(search_index['keywords'])} 个关键词")
        Logger.log("")

        # 保存索引
        Logger.log("保存索引文件...")
        self.save_index(mapping_index, "docs-mapping.json")
        self.save_index(search_index, "docs-search-index.json")
        Logger.log("")

        # 完成统计
        Logger.log("=" * 60)
        Logger.log(f"文档总数: {len(documents)}")
        Logger.log(f"分类总数: {len(mapping_index['categories'])}")
        Logger.log(f"关键词总数: {len(search_index['keywords'])}")
        Logger.log(f"输出目录: {self.output_dir}")
        Logger.log("=" * 60)

    def run_auto_api(self):
        """
        生成 api-reference/auto_api 的独立索引

        主索引（IGNORE_DIRS）会跳过 auto_api 目录，本方法单独扫描它并输出
        docs-auto-api-mapping.json 与 docs-auto-api-search-index.json。
        前端按需懒加载这两个文件，以保持主索引不被 auto_api 污染。
        """
        Logger.log("-" * 60)
        Logger.log("生成 auto_api 独立索引")
        Logger.log("-" * 60)

        auto_api_dir = self.actual_docs_dir / "api-reference" / "auto_api"
        if not auto_api_dir.exists():
            Logger.log(f"目录不存在，跳过: {auto_api_dir}")
            Logger.log("")
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 扫描所有 .md 文件
        files = []
        for root, _, filenames in os.walk(auto_api_dir):
            for filename in filenames:
                if filename.endswith(".md"):
                    files.append(Path(root) / filename)
        files.sort()

        Logger.log(f"发现 {len(files)} 个 Markdown 文件")

        # 解析文档
        parsed = []
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                Logger.progress(
                    str(file_path.relative_to(self.actual_docs_dir)),
                    "warn",
                    f"读取失败: {e}",
                )
                continue

            headings = self.parse_headings(content)
            if not headings:
                continue

            title = self.get_document_title(headings, file_path)
            rel_path = str(file_path.relative_to(self.actual_docs_dir)).replace(
                "\\", "/"
            )
            rel_to_auto = str(file_path.relative_to(auto_api_dir)).replace("\\", "/")

            api_category = self.CATEGORY_MAP.get("api-reference", "API Reference")
            parsed.append(
                {
                    "title": title,
                    "path": rel_path,
                    "level": 1,
                    "icon": self.get_doc_icon(rel_path, api_category, None),
                    "headings": headings,
                    "rel_to_auto": rel_to_auto,
                }
            )

        Logger.log(f"成功解析 {len(parsed)} 个文档")

        # 按 ErisPulse/ 下第一级子目录分组
        top_docs = []
        subgroups_temp = {}
        for doc in parsed:
            parts = doc["rel_to_auto"].split("/")
            subgroup_key = None
            if len(parts) >= 3 and parts[0] == "ErisPulse":
                subgroup_key = parts[1]

            if subgroup_key:
                subgroups_temp.setdefault(subgroup_key, []).append(doc)
            else:
                top_docs.append(doc)

        # 构建子分组
        lang = self.lang or "zh-CN"
        subgroups_out = {}
        for key, docs in subgroups_temp.items():
            sg_name = self.AUTO_API_SUBGROUP_NAMES.get(key, {}).get(
                lang, key.replace("-", " ").replace("_", " ").title()
            )
            sg_icon = self.AUTO_API_SUBGROUP_ICONS.get(key, "fa-folder")
            sorted_docs = sorted(
                [
                    {k: v for k, v in d.items() if k not in ("headings", "rel_to_auto")}
                    for d in docs
                ],
                key=lambda x: x["path"],
            )
            subgroups_out[key] = {
                "name": sg_name,
                "icon": sg_icon,
                "documents": sorted_docs,
            }

        # 子分组按文档数从多到少排序（核心在前）
        subgroups_out = dict(
            sorted(subgroups_out.items(), key=lambda kv: -len(kv[1]["documents"]))
        )

        top_entries = sorted(
            [
                {k: v for k, v in d.items() if k not in ("headings", "rel_to_auto")}
                for d in top_docs
            ],
            key=lambda x: x["path"],
        )

        # 本地化分类名
        category_name = self.AUTO_API_CATEGORY_NAMES.get(lang, "Auto-generated API")
        api_ref_desc = self.CATEGORY_DESCRIPTIONS.get(
            self.CATEGORY_MAP.get("api-reference", ""), ""
        )

        mapping_index = {
            "version": "1.0",
            "total_categories": 1,
            "total_documents": len(parsed),
            "categories": {
                category_name: {
                    "description": api_ref_desc,
                    "icon": "fa-microchip",
                    "count": len(parsed),
                    "documents": top_entries,
                    "subgroups": subgroups_out,
                }
            },
        }

        # 搜索索引（与主搜索索引格式一致）
        keywords = {}
        for doc in parsed:
            for heading in doc["headings"]:
                text = heading["text"]
                if text not in keywords:
                    keywords[text] = []
                keywords[text].append(
                    {
                        "document": doc["path"],
                        "line": heading["line"],
                        "level": heading["level"],
                        "title": text,
                    }
                )
        sorted_keywords = dict(sorted(keywords.items()))
        search_index = {
            "version": "1.0",
            "total_keywords": len(sorted_keywords),
            "keywords": sorted_keywords,
        }

        # 保存
        self.save_index(mapping_index, "docs-auto-api-mapping.json")
        self.save_index(search_index, "docs-auto-api-search-index.json")

        Logger.log(
            f"生成 1 个分类, {len(parsed)} 个文档, {len(sorted_keywords)} 个关键词"
        )
        Logger.log(f"输出目录: {self.output_dir}")
        Logger.log("-" * 60)
        Logger.log("")


def main():
    """命令行入口：解析参数并运行文档索引生成器"""
    parser = argparse.ArgumentParser(
        description="ErisPulse 文档索引生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  # 使用默认设置（为所有语言生成索引）
  python scripts/tools/generate-docs-index.py

  # 只为特定语言生成索引
  python scripts/tools/generate-docs-index.py --lang zh-CN

  # 自定义文档目录和输出目录
  python scripts/tools/generate-docs-index.py --docs docs --output docs/_meta
        """,
    )

    parser.add_argument("--docs", default="docs", help="文档目录 (默认: docs)")
    parser.add_argument(
        "--output", default="docs/_meta", help="索引输出目录 (默认: docs/_meta)"
    )
    parser.add_argument(
        "--lang", help="指定语言代码（如: zh-CN, en, zh-TW），不指定则为所有语言生成"
    )

    args = parser.parse_args()

    docs_dir = Path(args.docs).resolve()

    # 如果指定了语言，只为该语言生成索引
    if args.lang:
        lang_output_dir = Path(args.output) / args.lang
        generator = DocsIndexGenerator(str(docs_dir), str(lang_output_dir), args.lang)
        generator.run(deprecated=False)
        # auto_api 只在 zh-CN 生成（其它语言的 auto_api 是中文副本，不重复生成）
        if args.lang == "zh-CN":
            generator.run_auto_api()
    else:
        # 为所有语言生成索引
        langs = DocsIndexGenerator.get_available_languages(docs_dir)
        Logger.log(f"发现 {len(langs)} 个语言: {', '.join(langs)}")
        Logger.log("")

        for lang in langs:
            Logger.log(f"--- {lang} ---")

            lang_output_dir = Path(args.output) / lang
            generator = DocsIndexGenerator(str(docs_dir), str(lang_output_dir), lang)
            generator.run(deprecated=False)
            # auto_api 仅在 zh-CN 生成（其它语言为中文副本）
            if lang == "zh-CN":
                generator.run_auto_api()
            Logger.log("")

        # 生成语言索引
        Logger.log("=" * 60)
        Logger.log("生成语言索引...")
        Logger.log("=" * 60)

        languages_index = {
            "version": "1.0",
            "total_languages": len(langs),
            "languages": {},
        }

        # 为每种语言添加信息
        for lang in langs:
            lang_index_path = f"_meta/{lang}/docs-mapping.json"
            lang_mapping_file = docs_dir / "_meta" / lang / "docs-mapping.json"

            # 读取该语言的映射文件获取文档数量
            total_docs = 0
            if lang_mapping_file.exists():
                try:
                    with open(lang_mapping_file, "r", encoding="utf-8") as f:
                        lang_data = json.load(f)
                        total_docs = sum(
                            cat.get("count", 0)
                            for cat in lang_data.get("categories", {}).values()
                        )
                except Exception as e:
                    Logger.progress(lang, "warn", f"无法读取映射文件: {e}")

            languages_index["languages"][lang] = {
                "docs_count": total_docs,
                "mapping_path": lang_index_path,
            }
            Logger.log(f"  {lang}: {total_docs} 个文档")

        # 保存语言索引
        output_file = Path(args.output) / "docs-mapping.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(languages_index, f, ensure_ascii=False, indent=2)
        Logger.log("")
        Logger.progress(str(output_file), "done", "语言索引已保存")


if __name__ == "__main__":
    main()
