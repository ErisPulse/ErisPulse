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
    
    # 目录到分类的映射
    CATEGORY_MAP = {
        "getting-started": "入门指南",
        "user-guide": "用户使用指南",
        "developer-guide": "开发者指南",
        "platform-guide": "平台特性指南",
        "api-reference": "API 参考",
        "advanced": "高级主题",
        "ai-support": "AI 辅助开发",
        "standards": "技术标准",
        "styleguide": "风格指南",
    }
    
    # 分类描述
    CATEGORY_DESCRIPTIONS = {
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
    }
    
    # 分类优先级（数值越小越靠前）
    # 按照用户阅读逻辑排序：快速开始 → 入门指南 → 用户使用指南 → 开发者指南...
    CATEGORY_PRIORITY = {
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
        "developer-guide/extensions/cli-extensions.md": 10,
        
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
        
        # AI 辅助开发
        "ai-support/README.md": 1,
        
        # 技术标准
        "standards/README.md": 1,
        "standards/api-response.md": 2,
        "standards/event-conversion.md": 3,
        "standards/naming-conventions.md": 4,
        
        # 风格指南
        "styleguide/README.md": 1,
        "styleguide/docstring.md": 2,
    }
    
    # 需要忽略的目录
    IGNORE_DIRS = {"_meta", "ai-support/prompts", "api-reference/auto_api"}
    
    def __init__(self, docs_dir: str, output_dir: str):
        """
        初始化索引生成器
        
        :param docs_dir: 文档根目录
        :param output_dir: 索引输出目录
        """
        self.docs_dir = Path(docs_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.docs_mapping: Dict = {}
        self.docs_search_index: Dict = {}
        
    def normalize_path(self, path: Path) -> str:
        """
        规范化路径，将反斜杠转换为正斜杠
        
        :param path: 文件路径
        :return: 规范化后的路径字符串
        """
        # 获取相对于 docs 目录的路径
        rel_path = path.relative_to(self.docs_dir)
        # 使用 / 作为分隔符
        return str(rel_path).replace("\\", "/")
    
    def get_category(self, file_path: Path) -> str:
        """
        根据文件路径获取分类
        
        :param file_path: 文件路径
        :return: 分类名称
        """
        rel_path = file_path.relative_to(self.docs_dir)
        
        # 根目录文件归类为"快速开始"
        if len(rel_path.parts) == 1:
            return "快速开始"
        
        # 根据目录名称分类
        dir_name = rel_path.parts[0]
        if dir_name in self.CATEGORY_MAP:
            return self.CATEGORY_MAP[dir_name]
        
        # 默认分类
        return "其他"
    
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
        
        for root, dirs, filenames in os.walk(self.docs_dir):
            # 过滤需要忽略的目录
            dirs[:] = [d for d in dirs if not any(
                Path(root) / d == Path(self.docs_dir) / ignored_dir.replace("/", os.sep)
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
    
    def generate_mapping_index(self, documents: List[Dict]) -> Dict:
        """
        生成文档映射索引
        
        :param documents: 文档列表
        :return: 映射索引
        """
        categories = {}
        
        for doc in documents:
            category = doc["category"]
            
            # 初始化分类
            if category not in categories:
                categories[category] = {
                    "description": self.CATEGORY_DESCRIPTIONS.get(category, ""),
                    "count": 0,
                    "documents": []
                }
            
            # 添加文档
            categories[category]["documents"].append({
                "title": doc["title"],
                "path": doc["path"],
                "level": doc["level"]
            })
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
        
        return {
            "version": "1.0",
            # "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_categories": len(sorted_categories),
            "categories": sorted_categories
        }
    
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
    
    def run(self):
        """运行索引生成器"""
        print("=" * 60)
        print("ErisPulse 文档索引生成器 v1.0")
        print("=" * 60)
        print()
        print(f"文档目录: {self.docs_dir}")
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
        mapping_index = self.generate_mapping_index(documents)
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
  # 使用默认设置
  python scripts/tools/generate-docs-index.py
  
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
        "--version",
        action="version",
        version="ErisPulse 文档索引生成器 v1.0"
    )
    
    args = parser.parse_args()
    
    # 创建并运行生成器
    generator = DocsIndexGenerator(args.docs, args.output)
    generator.run()


if __name__ == "__main__":
    main()