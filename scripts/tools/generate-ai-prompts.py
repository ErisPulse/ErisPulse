"""
生成 AI 辅助开发物料文档

从 docs/ 目录读取文档，生成 AI 辅助开发用的 prompt 文档

使用方法:
    python scripts/tools/generate-ai-prompts.py

    # 只为特定语言生成
    python scripts/tools/generate-ai-prompts.py --lang en
"""

import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional


class PromptGenerator:
    """AI Prompt 生成器"""
    
    def __init__(self, docs_dir: str, output_dir: str, lang: Optional[str] = None):
        self.docs_dir = Path(docs_dir)
        self.lang = lang
        if self.lang:
            self.actual_docs_dir = self.docs_dir / self.lang
        else:
            self.actual_docs_dir = self.docs_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_available_languages(docs_dir: Path) -> List[str]:
        langs = []
        for item in docs_dir.iterdir():
            if item.is_dir() and item.name not in ['_meta']:
                langs.append(item.name)
        return sorted(langs)
    
    def _system_prompt(self, prompt_type: str) -> str:
        prompts = {
            "module": """你是一个 ErisPulse 模块开发专家，精通以下领域：

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
            "adapter": """你是一个 ErisPulse 适配器开发专家，精通以下领域：

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
            "full": """你是一个 ErisPulse 全栈开发专家，精通以下领域：

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
- 已知问题追踪和历史 Bug 记录

你擅长：
- 编写高质量的异步 Python 代码
- 设计模块化、可扩展的架构
- 开发模块、适配器
- 使用 ErisPulse 的所有核心功能
- 遵循 ErisPulse 的最佳实践和代码规范
- 解决跨平台兼容性问题
- 通过 CLI 管理项目和发布

**使用以下文档作为知识库，回答问题时请优先参考文档内容。**
"""
        }
        
        return prompts.get(prompt_type, "")
    
    def read_file(self, filepath: str) -> str:
        file_path = self.actual_docs_dir / filepath
        if not file_path.exists():
            return ""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def read_all_files(self, file_patterns: List[str]) -> Dict[str, str]:
        contents = {}
        for pattern in file_patterns:
            file_path = self.actual_docs_dir / pattern
            if file_path.exists():
                relative_path = pattern.replace('\\', '/')
                contents[relative_path] = self.read_file(pattern)
        return contents
    
    def generate_module_dev_prompt(self) -> str:
        sections = []
        
        sections.append(self._system_prompt("module"))
        sections.append("\n")
        sections.append("---\n\n")
        
        sections.append(self._section_header("ErisPulse 模块开发指南"))
        sections.append("\n")
        
        sections.append(self._section_header("框架理解"))
        sections.append(self._subsection_header("架构概览"))
        sections.append(self.read_file('architecture.md'))
        sections.append("\n")
        sections.append(self._subsection_header("术语表"))
        sections.append(self.read_file('terminology.md'))
        sections.append("\n")
        
        sections.append(self._section_header("快速开始"))
        sections.append(self._subsection_header("入门指南总览"))
        sections.append(self.read_file('getting-started/README.md'))
        sections.append("\n")
        sections.append(self._subsection_header("创建第一个模块"))
        sections.append(self.read_file('getting-started/first-bot.md'))
        sections.append("\n")
        sections.append(self._subsection_header("基础概念"))
        sections.append(self.read_file('getting-started/basic-concepts.md'))
        sections.append("\n")
        sections.append(self._subsection_header("事件处理入门"))
        sections.append(self.read_file('getting-started/event-handling.md'))
        sections.append("\n")
        sections.append(self._subsection_header("常见任务示例"))
        sections.append(self.read_file('getting-started/common-tasks.md'))
        sections.append("\n")
        
        sections.append(self._section_header("模块开发"))
        sections.append(self._subsection_header("模块开发入门"))
        sections.append(self.read_file('developer-guide/modules/getting-started.md'))
        sections.append("\n")
        sections.append(self._subsection_header("模块核心概念"))
        sections.append(self.read_file('developer-guide/modules/core-concepts.md'))
        sections.append("\n")
        sections.append(self._subsection_header("Event 包装类详解"))
        sections.append(self.read_file('developer-guide/modules/event-wrapper.md'))
        sections.append("\n")
        sections.append(self._subsection_header("模块开发最佳实践"))
        sections.append(self.read_file('developer-guide/modules/best-practices.md'))
        sections.append("\n")
        
        sections.append(self._section_header("发布与工具"))
        sections.append(self._subsection_header("发布模块到模块商店"))
        sections.append(self.read_file('developer-guide/publishing.md'))
        sections.append("\n")
        sections.append(self._subsection_header("CLI 命令参考"))
        sections.append(self.read_file('user-guide/cli-reference.md'))
        sections.append("\n")
        
        sections.append(self._section_header("API 参考"))
        sections.append(self._subsection_header("核心模块 API"))
        sections.append(self.read_file('api-reference/core-modules.md'))
        sections.append("\n")
        sections.append(self._subsection_header("事件系统 API"))
        sections.append(self.read_file('api-reference/event-system.md'))
        sections.append("\n")
        
        sections.append(self._section_header("高级主题"))
        sections.append(self._subsection_header("Conversation 多轮对话"))
        sections.append(self.read_file('advanced/conversation.md'))
        sections.append("\n")
        sections.append(self._subsection_header("MessageBuilder 详解"))
        sections.append(self.read_file('advanced/message-builder.md'))
        sections.append("\n")
        sections.append(self._subsection_header("路由系统"))
        sections.append(self.read_file('advanced/router.md'))
        sections.append("\n")
        sections.append(self._subsection_header("生命周期管理"))
        sections.append(self.read_file('advanced/lifecycle.md'))
        sections.append("\n")
        sections.append(self._subsection_header("懒加载系统"))
        sections.append(self.read_file('advanced/lazy-loading.md'))
        sections.append("\n")
        sections.append(self._subsection_header("会话类型系统"))
        sections.append(self.read_file('advanced/session-types.md'))
        sections.append("\n")
        
        sections.append(self._section_header("技术标准"))
        sections.append(self._subsection_header("会话类型标准"))
        sections.append(self.read_file('standards/session-types.md'))
        sections.append("\n")
        
        sections.append(self._section_header("平台概览"))
        sections.append(self._subsection_header("平台特性与 SendDSL 通用语法"))
        sections.append(self.read_file('platform-guide/README.md'))
        sections.append("\n")
        
        return "\n".join(sections)
    
    def generate_adapter_dev_prompt(self) -> str:
        sections = []
        
        sections.append(self._system_prompt("adapter"))
        sections.append("\n")
        sections.append("---\n\n")
        
        sections.append(self._section_header("ErisPulse 适配器开发指南"))
        sections.append("\n")
        
        sections.append(self._section_header("框架理解"))
        sections.append(self._subsection_header("架构概览"))
        sections.append(self.read_file('architecture.md'))
        sections.append("\n")
        sections.append(self._subsection_header("术语表"))
        sections.append(self.read_file('terminology.md'))
        sections.append("\n")
        
        sections.append(self._section_header("基础概念"))
        sections.append(self._subsection_header("入门指南总览"))
        sections.append(self.read_file('getting-started/README.md'))
        sections.append("\n")
        sections.append(self._subsection_header("基础概念"))
        sections.append(self.read_file('getting-started/basic-concepts.md'))
        sections.append("\n")
        sections.append(self._subsection_header("事件处理入门"))
        sections.append(self.read_file('getting-started/event-handling.md'))
        sections.append("\n")
        
        sections.append(self._section_header("适配器开发"))
        sections.append(self._subsection_header("适配器开发入门"))
        sections.append(self.read_file('developer-guide/adapters/getting-started.md'))
        sections.append("\n")
        sections.append(self._subsection_header("适配器核心概念"))
        sections.append(self.read_file('developer-guide/adapters/core-concepts.md'))
        sections.append("\n")
        sections.append(self._subsection_header("SendDSL 详解"))
        sections.append(self.read_file('developer-guide/adapters/send-dsl.md'))
        sections.append("\n")
        sections.append(self._subsection_header("适配器开发最佳实践"))
        sections.append(self.read_file('developer-guide/adapters/best-practices.md'))
        sections.append("\n")
        sections.append(self._subsection_header("事件转换器"))
        sections.append(self.read_file('developer-guide/adapters/converter.md'))
        sections.append("\n")
        
        sections.append(self._section_header("发布与工具"))
        sections.append(self._subsection_header("发布适配器到模块商店"))
        sections.append(self.read_file('developer-guide/publishing.md'))
        sections.append("\n")
        sections.append(self._subsection_header("CLI 命令参考"))
        sections.append(self.read_file('user-guide/cli-reference.md'))
        sections.append("\n")
        
        sections.append(self._section_header("API 参考"))
        sections.append(self._subsection_header("适配器系统 API"))
        sections.append(self.read_file('api-reference/adapter-system.md'))
        sections.append("\n")
        sections.append(self._subsection_header("核心模块 API"))
        sections.append(self.read_file('api-reference/core-modules.md'))
        sections.append("\n")
        
        sections.append(self._section_header("高级主题"))
        sections.append(self._subsection_header("生命周期管理"))
        sections.append(self.read_file('advanced/lifecycle.md'))
        sections.append("\n")
        sections.append(self._subsection_header("懒加载系统"))
        sections.append(self.read_file('advanced/lazy-loading.md'))
        sections.append("\n")
        
        sections.append(self._section_header("技术标准"))
        sections.append(self._subsection_header("会话类型标准"))
        sections.append(self.read_file('standards/session-types.md'))
        sections.append("\n")
        sections.append(self._subsection_header("事件转换标准"))
        sections.append(self.read_file('standards/event-conversion.md'))
        sections.append("\n")
        sections.append(self._subsection_header("API 响应标准"))
        sections.append(self.read_file('standards/api-response.md'))
        sections.append("\n")
        sections.append(self._subsection_header("发送方法规范"))
        sections.append(self.read_file('standards/send-method-spec.md'))
        sections.append("\n")
        
        sections.append(self._section_header("平台特性指南"))
        sections.append(self._subsection_header("平台特性总览"))
        sections.append(self.read_file('platform-guide/README.md'))
        sections.append("\n")
        sections.append(self._subsection_header("OneBot11 适配"))
        sections.append(self.read_file('platform-guide/onebot11.md'))
        sections.append("\n")
        sections.append(self._subsection_header("OneBot12 适配"))
        sections.append(self.read_file('platform-guide/onebot12.md'))
        sections.append("\n")
        sections.append(self._subsection_header("Telegram 适配"))
        sections.append(self.read_file('platform-guide/telegram.md'))
        sections.append("\n")
        sections.append(self._subsection_header("云湖适配"))
        sections.append(self.read_file('platform-guide/yunhu.md'))
        sections.append("\n")
        sections.append(self._subsection_header("邮件适配"))
        sections.append(self.read_file('platform-guide/email.md'))
        sections.append("\n")
        sections.append(self._subsection_header("Kook 适配"))
        sections.append(self.read_file('platform-guide/kook.md'))
        sections.append("\n")
        sections.append(self._subsection_header("Matrix 适配"))
        sections.append(self.read_file('platform-guide/matrix.md'))
        sections.append("\n")
        sections.append(self._subsection_header("QQBot 适配"))
        sections.append(self.read_file('platform-guide/qqbot.md'))
        sections.append("\n")
        sections.append(self._subsection_header("云湖用户端适配"))
        sections.append(self.read_file('platform-guide/yunhu_user.md'))
        sections.append("\n")
        sections.append(self._subsection_header("平台文档维护说明"))
        sections.append(self.read_file('platform-guide/maintain-notes.md'))
        sections.append("\n")
        
        sections.append(self._section_header("代码规范"))
        sections.append(self._subsection_header("文档字符串规范"))
        sections.append(self.read_file('styleguide/docstring.md'))
        sections.append("\n")
        
        return "\n".join(sections)
    
    def generate_full_dev_prompt(self) -> str:
        sections = []
        
        sections.append(self._system_prompt("full"))
        sections.append("\n")
        sections.append("---\n\n")
        
        sections.append("# ErisPulse 完整开发物料\n")
        sections.append("> **注意**：本文档内容较多，建议仅用于具有强大上下文能力的 AI 模型\n\n")
        sections.append("---\n\n")
        
        sections.append(self._section_header("框架理解"))
        sections.append(self._subsection_header("架构概览"))
        sections.append(self.read_file('architecture.md'))
        sections.append("\n")
        sections.append(self._subsection_header("术语表"))
        sections.append(self.read_file('terminology.md'))
        sections.append("\n")
        
        sections.append(self._section_header("快速开始"))
        sections.append(self.read_file('quick-start.md'))
        sections.append("\n")
        
        sections.append(self._section_header("入门指南"))
        sections.append(self._subsection_header("入门指南总览"))
        sections.append(self.read_file('getting-started/README.md'))
        sections.append("\n")
        sections.append(self._subsection_header("创建第一个机器人"))
        sections.append(self.read_file('getting-started/first-bot.md'))
        sections.append("\n")
        sections.append(self._subsection_header("基础概念"))
        sections.append(self.read_file('getting-started/basic-concepts.md'))
        sections.append("\n")
        sections.append(self._subsection_header("事件处理入门"))
        sections.append(self.read_file('getting-started/event-handling.md'))
        sections.append("\n")
        sections.append(self._subsection_header("常见任务示例"))
        sections.append(self.read_file('getting-started/common-tasks.md'))
        sections.append("\n")
        
        sections.append(self._section_header("用户指南"))
        sections.append(self._subsection_header("安装和配置"))
        sections.append(self.read_file('user-guide/installation.md'))
        sections.append("\n")
        sections.append(self._subsection_header("CLI 命令参考"))
        sections.append(self.read_file('user-guide/cli-reference.md'))
        sections.append("\n")
        sections.append(self._subsection_header("配置文件说明"))
        sections.append(self.read_file('user-guide/configuration.md'))
        sections.append("\n")
        sections.append(self._subsection_header("部署指南"))
        sections.append(self.read_file('user-guide/deployment.md'))
        sections.append("\n")
        
        sections.append(self._section_header("开发者指南"))
        sections.append(self._subsection_header("开发者指南总览"))
        sections.append(self.read_file('developer-guide/README.md'))
        sections.append("\n")
        
        sections.append(self._subheader("模块开发"))
        sections.append("\n")
        
        sections.append(self._subsection_header("模块开发入门"))
        sections.append(self.read_file('developer-guide/modules/getting-started.md'))
        sections.append("\n")
        sections.append(self._subsection_header("模块核心概念"))
        sections.append(self.read_file('developer-guide/modules/core-concepts.md'))
        sections.append("\n")
        sections.append(self._subsection_header("Event 包装类详解"))
        sections.append(self.read_file('developer-guide/modules/event-wrapper.md'))
        sections.append("\n")
        sections.append(self._subsection_header("模块开发最佳实践"))
        sections.append(self.read_file('developer-guide/modules/best-practices.md'))
        sections.append("\n")
        
        sections.append(self._subheader("适配器开发"))
        sections.append("\n")
        
        sections.append(self._subsection_header("适配器开发入门"))
        sections.append(self.read_file('developer-guide/adapters/getting-started.md'))
        sections.append("\n")
        sections.append(self._subsection_header("适配器核心概念"))
        sections.append(self.read_file('developer-guide/adapters/core-concepts.md'))
        sections.append("\n")
        sections.append(self._subsection_header("SendDSL 详解"))
        sections.append(self.read_file('developer-guide/adapters/send-dsl.md'))
        sections.append("\n")
        sections.append(self._subsection_header("适配器开发最佳实践"))
        sections.append(self.read_file('developer-guide/adapters/best-practices.md'))
        sections.append("\n")
        sections.append(self._subsection_header("事件转换器"))
        sections.append(self.read_file('developer-guide/adapters/converter.md'))
        sections.append("\n")
        
        sections.append(self._subsection_header("发布与模块商店指南"))
        sections.append(self.read_file('developer-guide/publishing.md'))
        sections.append("\n")
        
        sections.append(self._section_header("API 参考"))
        sections.append(self._subsection_header("核心模块 API"))
        sections.append(self.read_file('api-reference/core-modules.md'))
        sections.append("\n")
        sections.append(self._subsection_header("事件系统 API"))
        sections.append(self.read_file('api-reference/event-system.md'))
        sections.append("\n")
        sections.append(self._subsection_header("适配器系统 API"))
        sections.append(self.read_file('api-reference/adapter-system.md'))
        sections.append("\n")
        
        sections.append(self._section_header("技术标准"))
        sections.append(self._subsection_header("会话类型标准"))
        sections.append(self.read_file('standards/session-types.md'))
        sections.append("\n")
        sections.append(self._subsection_header("事件转换标准"))
        sections.append(self.read_file('standards/event-conversion.md'))
        sections.append("\n")
        sections.append(self._subsection_header("API 响应标准"))
        sections.append(self.read_file('standards/api-response.md'))
        sections.append("\n")
        sections.append(self._subsection_header("发送方法规范"))
        sections.append(self.read_file('standards/send-method-spec.md'))
        sections.append("\n")
        
        sections.append(self._section_header("高级主题"))
        sections.append(self._subsection_header("懒加载系统"))
        sections.append(self.read_file('advanced/lazy-loading.md'))
        sections.append("\n")
        sections.append(self._subsection_header("生命周期管理"))
        sections.append(self.read_file('advanced/lifecycle.md'))
        sections.append("\n")
        sections.append(self._subsection_header("路由系统"))
        sections.append(self.read_file('advanced/router.md'))
        sections.append("\n")
        sections.append(self._subsection_header("MessageBuilder 详解"))
        sections.append(self.read_file('advanced/message-builder.md'))
        sections.append("\n")
        sections.append(self._subsection_header("会话类型系统"))
        sections.append(self.read_file('advanced/session-types.md'))
        sections.append("\n")
        sections.append(self._subsection_header("Conversation 多轮对话"))
        sections.append(self.read_file('advanced/conversation.md'))
        sections.append("\n")
        
        sections.append(self._section_header("平台特性指南"))
        sections.append(self._subsection_header("平台特性总览"))
        sections.append(self.read_file('platform-guide/README.md'))
        sections.append("\n")
        sections.append(self._subsection_header("OneBot11 适配"))
        sections.append(self.read_file('platform-guide/onebot11.md'))
        sections.append("\n")
        sections.append(self._subsection_header("OneBot12 适配"))
        sections.append(self.read_file('platform-guide/onebot12.md'))
        sections.append("\n")
        sections.append(self._subsection_header("Telegram 适配"))
        sections.append(self.read_file('platform-guide/telegram.md'))
        sections.append("\n")
        sections.append(self._subsection_header("云湖适配"))
        sections.append(self.read_file('platform-guide/yunhu.md'))
        sections.append("\n")
        sections.append(self._subsection_header("邮件适配"))
        sections.append(self.read_file('platform-guide/email.md'))
        sections.append("\n")
        sections.append(self._subsection_header("平台文档维护说明"))
        sections.append(self.read_file('platform-guide/maintain-notes.md'))
        sections.append("\n")
        
        sections.append(self._section_header("代码规范"))
        sections.append(self._subsection_header("文档字符串规范"))
        sections.append(self.read_file('styleguide/docstring.md'))
        sections.append("\n")
        
        sections.append(self._section_header("已知问题追踪"))
        sections.append(self._subsection_header("历史 Bug 记录"))
        sections.append(self.read_file('bug-tracker.md'))
        sections.append("\n")
        
        return "\n".join(sections)
    
    def _section_header(self, title: str) -> str:
        return f"\n{'=' * len(title)}\n{title}\n{'=' * len(title)}\n"
    
    def _subheader(self, title: str) -> str:
        return f"\n{title}\n{'-' * len(title)}\n"
    
    def _subsection_header(self, title: str) -> str:
        return f"\n### {title}\n"
    
    def generate_all(self):
        print("开始生成 AI prompt 文档...")
        
        print("  生成 ErisPulse-ModuleDev.md...")
        module_content = self.generate_module_dev_prompt()
        self._write_prompt("ErisPulse-ModuleDev.md", module_content)
        
        print("  生成 ErisPulse-AdapterDev.md...")
        adapter_content = self.generate_adapter_dev_prompt()
        self._write_prompt("ErisPulse-AdapterDev.md", adapter_content)
        
        print("  生成 ErisPulse-Full.md...")
        full_content = self.generate_full_dev_prompt()
        self._write_prompt("ErisPulse-Full.md", full_content)
        
        print("\n所有 AI prompt 文档生成完成！")
        print(f"   输出目录: {self.output_dir}")
    
    def _write_prompt(self, filename: str, content: str):
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)


def main():
    parser = argparse.ArgumentParser(
        description="ErisPulse AI Prompt 生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认设置（为所有语言生成）
  python scripts/tools/generate-ai-prompts.py
  
  # 只为特定语言生成
  python scripts/tools/generate-ai-prompts.py --lang en
        """
    )
    
    parser.add_argument(
        "--docs",
        default="docs",
        help="文档目录 (默认: docs)"
    )
    parser.add_argument(
        "--lang",
        help="指定语言代码（如: zh-CN, en, zh-TW），不指定则为所有语言生成"
    )
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    docs_dir = script_dir.parent.parent / args.docs
    
    if args.lang:
        print(f"为语言 {args.lang} 生成 AI prompt 文档...")
        print(f"文档目录: {docs_dir / args.lang}")
        
        output_dir = docs_dir / args.lang / "ai-support" / "prompts"
        
        print(f"输出目录: {output_dir}\n")
        
        generator = PromptGenerator(str(docs_dir), str(output_dir), args.lang)
        generator.generate_all()
    else:
        langs = PromptGenerator.get_available_languages(docs_dir)
        print(f"发现 {len(langs)} 个语言: {', '.join(langs)}")
        print()
        
        for lang in langs:
            print(f"\n{'='*60}")
            print(f"处理语言: {lang}")
            print('='*60)
            
            print(f"文档目录: {docs_dir / lang}")
            
            output_dir = docs_dir / lang / "ai-support" / "prompts"
            
            print(f"输出目录: {output_dir}\n")
            
            generator = PromptGenerator(str(docs_dir), str(output_dir), lang)
            generator.generate_all()
        
        print(f"\n{'='*60}")
        print("所有语言的 AI prompt 文档生成完成！")
        print('='*60)


if __name__ == "__main__":
    main()
