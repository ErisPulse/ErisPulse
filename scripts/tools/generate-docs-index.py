"""
ErisPulse 文档索引生成器

自动扫描 docs/ 目录，生成文档映射索引和搜索索引
"""

import os
import re
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path


class DocsIndexGenerator:
    """文档索引生成器"""
    
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
                "ai-support": "AI 辅助开发",
                "standards": "技术标准",
                "styleguide": "风格指南",
            },
            "descriptions": {
                "快速开始": "ErisPulse 快速入门指南",
                "入门指南": "ErisPulse 基础概念和使用教程",
                "用户使用指南": "ErisPulse 配置和命令参考",
                "开发者指南": "模块和适配器开发指南",
                "平台特性指南": "各平台特性和适配器说明",
                "API 参考": "核心 API 和接口文档",
                "高级主题": "深入理解框架的高级特性",
                "AI 辅助开发": "使用 AI 辅助开发 ErisPulse",
                "技术标准": "框架的技术规范和标准",
                "风格指南": "代码和文档风格规范",
            },
            "priority": {
                "快速开始": 1,
                "入门指南": 2,
                "用户使用指南": 3,
                "开发者指南": 4,
                "平台特性指南": 5,
                "API 参考": 6,
                "高级主题": 7,
                "AI 辅助开发": 8,
                "技术标准": 9,
                "风格指南": 10,
            }
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
                "ai-support": "AI-Assisted Development",
                "standards": "Technical Standards",
                "styleguide": "Style Guide",
            },
            "descriptions": {
                "Quick Start": "ErisPulse Quick Start Guide",
                "Getting Started": "ErisPulse basic concepts and tutorials",
                "User Guide": "ErisPulse configuration and command reference",
                "Developer Guide": "Module and adapter development guides",
                "Platform Guide": "Platform features and adapter documentation",
                "API Reference": "Core API and interface documentation",
                "Advanced Topics": "Deep dive into advanced framework features",
                "AI-Assisted Development": "Using AI to assist ErisPulse development",
                "Technical Standards": "Framework technical specifications and standards",
                "Style Guide": "Code and documentation style guidelines",
            },
            "priority": {
                "Quick Start": 1,
                "Getting Started": 2,
                "User Guide": 3,
                "Developer Guide": 4,
                "Platform Guide": 5,
                "API Reference": 6,
                "Advanced Topics": 7,
                "AI-Assisted Development": 8,
                "Technical Standards": 9,
                "Style Guide": 10,
            }
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
                "ai-support": "AI 輔助開發",
                "standards": "技術標準",
                "styleguide": "風格指南",
            },
            "descriptions": {
                "快速開始": "ErisPulse 快速入門指南",
                "入門指南": "ErisPulse 基礎概念和使用教程",
                "使用者指南": "ErisPulse 配置和命令參考",
                "開發者指南": "模組和適配器開發指南",
                "平台特性指南": "各平台特性和適配器說明",
                "API 參考": "核心 API 和介面文檔",
                "進階主題": "深入理解框架的進階特性",
                "AI 輔助開發": "使用 AI 輔助開發 ErisPulse",
                "技術標準": "框架的技術規範和標準",
                "風格指南": "代碼和文檔風格規範",
            },
            "priority": {
                "快速開始": 1,
                "入門指南": 2,
                "使用者指南": 3,
                "開發者指南": 4,
                "平台特性指南": 5,
                "API 參考": 6,
                "進階主題": 7,
                "AI 輔助開發": 8,
                "技術標準": 9,
                "風格指南": 10,
            }
        },
    }
    
    # 文档优先级（数值越小越靠前）
    DOC_PRIORITY = {
        # 快速开始
        "README.md": 1,
        "quick-start.md": 2,
        
        # 入门指南
        "getting-started/first-bot.md": 1,
        "getting-started/README.md": 2,
        "getting-started/basic-concepts.md": 3,
        "getting-started/common-tasks.md": 4,
        "getting-started/event-handling.md": 5,
        
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
        "platform-guide/maintain-notes.md": 7,
        
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
        
        # AI 辅助开发
        "ai-support/README.md": 1,
        
        # 技术标准
        "standards/README.md": 1,
        "standards/session-types.md": 2,
        "standards/api-response.md": 3,
        "standards/event-conversion.md": 4,
        "standards/send-method-spec.md": 5,
        
        # 风格指南
        "styleguide/README.md": 1,
        "styleguide/docstring.md": 2,
    }
    
    # 需要忽略的目录
    IGNORE_DIRS = {"ai-support/prompts", "api-reference/auto_api"}
    
    # 子分组显示名称（按语言映射）
    SUBGROUP_NAMES = {
        "modules": {
            "zh-CN": "模块开发",
            "en": "Modules",
            "zh-TW": "模組開發"
        },
        "adapters": {
            "zh-CN": "适配器开发",
            "en": "Adapters",
            "zh-TW": "適配器開發"
        },
        "prompts": {
            "zh-CN": "提示词模板",
            "en": "Prompt Templates",
            "zh-TW": "提示詞模板"
        }
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
        """根据语言初始化分类映射"""
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
            if item.is_dir() and item.name not in ['_meta']:
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
    
    def parse_headings(self, content: str) -> List[Dict]:
        """
        解析 Markdown 文档中的标题
        
        :param content: Markdown 内容
        :return: 标题列表，每个标题包含 level, text, line
        """
        headings = []
        lines = content.split('\n')
        
        in_code_block = False
        code_block_pattern = re.compile(r'^```')
        
        for line_num, line in enumerate(lines, start=1):
            # 检测代码块开始/结束
            if code_block_pattern.match(line):
                in_code_block = not in_code_block
                continue
            
            # 跳过代码块内的内容
            if in_code_block:
                continue
            
            # 匹配 # 到 ###### 的标题
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    "level": level,
                    "text": text,
                    "line": line_num
                })
        
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
            dirs[:] = [d for d in dirs if not any(
                Path(root) / d == self.actual_docs_dir / ignored_dir.replace("/", os.sep)
                for ignored_dir in self.IGNORE_DIRS
            )]
            
            for filename in filenames:
                if filename.endswith(".md"):
                    file_path = Path(root) / filename
                    file_info = {
                        "path": file_path,
                        "relative_path": self.normalize_path(file_path),
                        "category": self.get_category(file_path)
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
            print(f"  [警告] 无法读取文件 {file_info['relative_path']}: {e}")
            return None
        
        # 解析标题
        headings = self.parse_headings(content)
        
        if not headings:
            print(f"  [跳过] {file_info['relative_path']} (无标题)")
            return None
        
        # 获取文档标题
        title = self.get_document_title(headings, file_path)
        
        # 获取文件修改时间
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        
        return {
            "title": title,
            "path": file_info["relative_path"],
            "category": file_info["category"],
            "level": 1,  # 默认等级
            "headings": headings,
            "last_modified": mod_time
        }
    
    def generate_mapping_index(self, documents: List[Dict], deprecated: bool = False) -> Dict:
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
            
            # 初始化分类
            if category not in categories:
                categories[category] = {
                    "description": self.CATEGORY_DESCRIPTIONS.get(category, ""),
                    "count": 0,
                    "documents": [],
                    "_subgroups": {}
                }
            
            doc_entry = {
                "title": doc["title"],
                "path": doc["path"],
                "level": doc["level"]
            }
            
            category_dir = reverse_category_map.get(category, "")
            subgroup_key = None
            
            if category_dir:
                prefix = category_dir + "/"
                if doc["path"].startswith(prefix):
                    remainder = doc["path"][len(prefix):]
                    parts = remainder.split("/")
                    if len(parts) > 1:
                        subgroup_key = parts[0]
            
            if subgroup_key:
                if subgroup_key not in categories[category]["_subgroups"]:
                    lang = self.lang or "zh-CN"
                    subgroup_name = self.SUBGROUP_NAMES.get(
                        subgroup_key, {}
                    ).get(lang, subgroup_key.replace("-", " ").replace("_", " ").title())
                    
                    categories[category]["_subgroups"][subgroup_key] = {
                        "name": subgroup_name,
                        "documents": []
                    }
                categories[category]["_subgroups"][subgroup_key]["documents"].append(doc_entry)
            else:
                categories[category]["documents"].append(doc_entry)
            
            categories[category]["count"] += 1
        
            categories[category]["count"] += 1
        
        # 按分类优先级排序（数值越小越靠前），未定义的分类排最后
        def sort_category(item):
            category_name = item[0]
            priority = self.CATEGORY_PRIORITY.get(category_name, 9999)  # 未定义的优先级设为 9999
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
            "version": "1.1",
            # "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_categories": len(sorted_categories),
            "categories": sorted_categories
        }
        
        # 如果是弃用索引，添加弃用标记
        if deprecated:
            result["_deprecated"] = True
            result["_note"] = "此索引已弃用，请使用 docs/_meta/{lang}/ 目录下的语言特定索引"
        
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
                
                keywords[text].append({
                    "document": doc["path"],
                    "line": heading["line"],
                    "level": heading["level"],
                    "title": text
                })
        
        # 按关键词排序，确保每次生成的顺序一致
        sorted_keywords = dict(sorted(keywords.items()))
        
        return {
            "version": "1.0",
            # "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_keywords": len(sorted_keywords),
            "keywords": sorted_keywords
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
        
        print(f"  [完成] {filename}")
    
    def run(self, deprecated: bool = False):
        """
        运行索引生成器
        
        :param deprecated: 是否为弃用模式
        """
        print("=" * 60)
        print("ErisPulse 文档索引生成器 v1.0")
        print("=" * 60)
        print()
        if self.lang:
            print(f"语言: {self.lang}")
        print(f"文档目录: {self.actual_docs_dir}")
        print(f"输出目录: {self.output_dir}")
        print()
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 扫描文档
        print("[1/4] 扫描文档目录...")
        file_infos = self.scan_docs()
        print(f"  发现 {len(file_infos)} 个 Markdown 文件")
        print()
        
        # 解析文档
        print("[2/4] 解析文档内容...")
        documents = []
        for file_info in file_infos:
            doc = self.parse_document(file_info)
            if doc:
                documents.append(doc)
                print(f"  [解析] {doc['path']}")
        print(f"  成功解析 {len(documents)} 个文档")
        print()
        
        # 生成映射索引
        print("[3/4] 生成文档映射索引...")
        mapping_index = self.generate_mapping_index(documents, deprecated=deprecated)
        print(f"  生成 {len(mapping_index['categories'])} 个分类")
        print()
        
        # 生成搜索索引
        print("[4/4] 生成文档搜索索引...")
        search_index = self.generate_search_index(documents)
        print(f"  生成 {len(search_index['keywords'])} 个关键词")
        print()
        
        # 保存索引
        print("保存索引文件...")
        self.save_index(mapping_index, "docs-mapping.json")
        self.save_index(search_index, "docs-search-index.json")
        print()
        
        # 完成统计
        print("=" * 60)
        print("索引生成完成！")
        print(f"  文档总数: {len(documents)}")
        print(f"  分类总数: {len(mapping_index['categories'])}")
        print(f"  关键词总数: {len(search_index['keywords'])}")
        print(f"  输出目录: {self.output_dir}")
        print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ErisPulse 文档索引生成器 v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认设置（为所有语言生成索引）
  python scripts/tools/generate-docs-index.py
  
  # 只为特定语言生成索引
  python scripts/tools/generate-docs-index.py --lang zh-CN
  
  # 自定义文档目录和输出目录
  python scripts/tools/generate-docs-index.py --docs docs --output docs/_meta
        """
    )
    
    parser.add_argument(
        "--docs",
        default="docs",
        help="文档目录 (默认: docs)"
    )
    parser.add_argument(
        "--output",
        default="docs/_meta",
        help="索引输出目录 (默认: docs/_meta)"
    )
    parser.add_argument(
        "--lang",
        help="指定语言代码（如: zh-CN, en, zh-TW），不指定则为所有语言生成"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="ErisPulse 文档索引生成器 v1.0"
    )
    
    args = parser.parse_args()
    
    docs_dir = Path(args.docs).resolve()
    
    # 如果指定了语言，只为该语言生成索引
    if args.lang:
        print(f"为语言 {args.lang} 生成索引...")
        lang_output_dir = Path(args.output) / args.lang
        generator = DocsIndexGenerator(str(docs_dir), str(lang_output_dir), args.lang)
        generator.run(deprecated=False)
    else:
        # 为所有语言生成索引
        langs = DocsIndexGenerator.get_available_languages(docs_dir)
        print(f"发现 {len(langs)} 个语言: {', '.join(langs)}")
        print()
        
        for lang in langs:
            print(f"\n{'='*60}")
            print(f"处理语言: {lang}")
            print('='*60)
            
            lang_output_dir = Path(args.output) / lang
            generator = DocsIndexGenerator(str(docs_dir), str(lang_output_dir), lang)
            generator.run(deprecated=False)
        
        # 生成语言索引
        print(f"\n{'='*60}")
        print("生成语言索引...")
        print('='*60)
        
        languages_index = {
            "version": "1.0",
            "total_languages": len(langs),
            "languages": {}
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
                        total_docs = sum(cat.get("count", 0) for cat in lang_data.get("categories", {}).values())
                except Exception as e:
                    print(f"  [警告] 无法读取 {lang} 的映射文件: {e}")
            
            languages_index["languages"][lang] = {
                "docs_count": total_docs,
                "mapping_path": lang_index_path
            }
            print(f"  {lang}: {total_docs} 个文档")
        
        # 保存语言索引
        output_file = Path(args.output) / "docs-mapping.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(languages_index, f, ensure_ascii=False, indent=2)
        print(f"\n  [完成] 语言索引已保存到 {output_file}")


if __name__ == "__main__":
    main()