"""
ErisPulse 文档翻译器

使用 AI 自动翻译文档到其他语言
"""

import os
import json
import hashlib
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import time
import asyncio
from openai import AsyncOpenAI

# 禁用输出缓冲
sys.stdout.reconfigure(line_buffering=True)


class DocsTranslator:
    
    # 语言配置
    LANG_CONFIG = {
        "zh-CN": {"name": "简体中文", "direction": "source"},
        "zh-TW": {"name": "繁体中文", "direction": "target"},
        "en": {"name": "English", "direction": "target"}
    }
    
    # 需要忽略的目录
    IGNORE_DIRS = ["ai-support/prompts", "api-reference/auto_api", "_meta"]
    
    def __init__(self, config_path: str):
        """
        初始化翻译器
        
        :param config_path: 配置文件路径
        """
        self.config = self.load_config(config_path)
        self.source_dir = Path("docs") / self.config["source_lang"]
        self.cache_dir = Path(self.config.get("cache_dir", ".translate_cache"))
        self.cache_dir.mkdir(exist_ok=True)
        
        # 初始化 OpenAI 客户端
        api_key = self.get_api_key()
        base_url = self.config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        # 统计信息
        self.stats = {
            "total_files": 0,
            "translated_files": 0,
            "skipped_files": 0,
            "failed_files": 0,
            "start_time": None,
            "end_time": None
        }
        
    def load_config(self, config_path: str) -> Dict:
        """
        加载配置文件
        
        :param config_path: 配置文件路径
        :return: 配置字典
        """
        config_file = Path(config_path)
        if not config_file.exists():
            # 返回默认配置
            return {
                "source_lang": "zh-CN",
                "target_langs": ["zh-TW", "en"],
                "ai_provider": "openai",
                "api_key_env": "OPENAI_API_KEY",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4",
                "concurrent": 5,
                "ignore_dirs": ["ai-support/prompts", "api-reference/auto_api"],
                "translate_code_comments": True,
                "cache_dir": ".translate_cache"
            }
        
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_api_key(self) -> str:
        """
        获取 API 密钥
        
        :return: API 密钥
        """
        env_var = self.config.get("api_key_env", "OPENAI_API_KEY")
        api_key = os.environ.get(env_var)
        if not api_key:
            raise ValueError(f"未找到 API 密钥，请设置环境变量 {env_var}")
        return api_key
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        计算文件的 MD5 哈希值
        
        :param file_path: 文件路径
        :return: 哈希值
        """
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def get_cache_key(self, file_path: Path, target_lang: str) -> Path:
        """
        获取缓存文件路径
        
        :param file_path: 源文件路径
        :param target_lang: 目标语言
        :return: 缓存文件路径
        """
        rel_path = file_path.relative_to(self.source_dir)
        cache_name = f"{rel_path}.{target_lang}.cache"
        return self.cache_dir / cache_name
    
    def is_file_changed(self, file_path: Path, target_lang: str) -> bool:
        """
        检查文件是否发生变化（需要重新翻译）
        
        :param file_path: 源文件路径
        :param target_lang: 目标语言
        :return: 是否需要重新翻译
        """
        cache_key = self.get_cache_key(file_path, target_lang)
        
        if not cache_key.exists():
            return True
        
        # 读取缓存
        with open(cache_key, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        # 比较哈希值
        current_hash = self.calculate_file_hash(file_path)
        return cache_data.get("hash") != current_hash
    
    def save_cache(self, file_path: Path, target_lang: str, hash_value: str):
        """
        保存翻译缓存
        
        :param file_path: 源文件路径
        :param target_lang: 目标语言
        :param hash_value: 文件哈希值
        """
        cache_key = self.get_cache_key(file_path, target_lang)
        cache_key.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_key, "w", encoding="utf-8") as f:
            json.dump({
                "hash": hash_value,
                "translated_at": datetime.now().isoformat(),
                "target_lang": target_lang
            }, f, ensure_ascii=False, indent=2)
    
    def build_translation_prompt(self, content: str, target_lang: str) -> str:
        """
        构建翻译提示词
        
        :param content: 要翻译的内容
        :param target_lang: 目标语言
        :return: 提示词
        """
        lang_name = self.LANG_CONFIG.get(target_lang, {}).get("name", target_lang)
        
        prompt = f"""你是一个专业的技术文档翻译专家。请将以下Markdown文档翻译成{lang_name}。

翻译要求：
1. 保持Markdown格式完整，包括标题、列表、代码块、链接、图片等
2. 准确翻译技术术语，保持专业性
3. 代码块中的代码不要翻译，但可以翻译代码中的注释
4. 保持原文档的结构和语气
5. 对于专业术语，如果{lang_name}中对应术语不确定，可以保留英文原词
6. 不要添加任何额外的解释或说明，只返回翻译后的内容

待翻译内容：

{content}

请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。"""
        
        return prompt
    
    async def call_translation_api(self, content: str, target_lang: str, file_name: str) -> Optional[str]:
        """
        调用翻译 API
        
        :param content: 要翻译的内容
        :param target_lang: 目标语言
        :param file_name: 文件名（用于显示）
        :return: 翻译后的内容
        """
        try:
            model = self.config.get("model", "gpt-4")
            prompt = self.build_translation_prompt(content, target_lang)
            
            translated_content = []
            char_count = 0
            
            # 使用 openai 库的流式 API
            stream = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的技术文档翻译专家。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=8000,
                stream=True
            )
            
            # 流式接收响应
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content_chunk = chunk.choices[0].delta.content
                    translated_content.append(content_chunk)
                    char_count += len(content_chunk)
                    
                    # 实时显示到终端
                    print(f"  [{file_name}] 已接收 {char_count} 字符...", end="\r", flush=True)
            
            # 清除进度显示
            print(" " * 80, end="\r", flush=True)
            
            # 合并所有chunk
            full_content = "".join(translated_content)
            
            if not full_content:
                print(f"  [警告] {file_name} 未接收到任何翻译内容")
                return None
            
            # 移除可能被 AI 添加的 markdown 代码块标记
            if full_content.startswith("```markdown") or full_content.startswith("```"):
                full_content = full_content.split("\n", 1)[-1]
            if full_content.endswith("```"):
                full_content = full_content.rsplit("\n", 1)[0]
            
            return full_content.strip()
            
        except Exception as e:
            print(f"  [错误] {file_name}: {e}")
            return None
    
    async def translate_file(self, file_path: Path, target_lang: str, force: bool = False) -> bool:
        """
        翻译单个文件
        
        :param file_path: 源文件路径
        :param target_lang: 目标语言
        :param force: 是否强制重新翻译
        :return: 是否成功
        """
        rel_path = file_path.relative_to(self.source_dir)
        
        try:
            # 读取源文件
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 检查是否需要翻译
            if not force and not self.is_file_changed(file_path, target_lang):
                self.stats["skipped_files"] += 1
                print(f"  [跳过] {rel_path} (未变化)")
                return True
            
            print(f"  [翻译] {rel_path} -> {target_lang}")
            
            # 调用翻译 API
            translated_content = await self.call_translation_api(content, target_lang, rel_path.name)
            
            if not translated_content:
                print(f"  [失败] {rel_path}")
                self.stats["failed_files"] += 1
                return False
            
            # 确保目标目录存在
            target_dir = Path("docs") / target_lang / rel_path.parent
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 写入翻译结果（接收完成后保存）
            target_file = target_dir / rel_path.name
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(translated_content)
            
            print(f"  [完成] {rel_path}")
            
            # 保存缓存
            file_hash = self.calculate_file_hash(file_path)
            self.save_cache(file_path, target_lang, file_hash)
            
            self.stats["translated_files"] += 1
            return True
            
        except Exception as e:
            print(f"  [错误] {rel_path}: {e}")
            self.stats["failed_files"] += 1
            return False
    
    def scan_files(self) -> List[Path]:
        """
        扫描需要翻译的文件
        
        :return: 文件路径列表
        """
        files = []
        
        for root, dirs, filenames in os.walk(self.source_dir):
            # 过滤需要忽略的目录
            dirs[:] = [d for d in dirs if not any(
                Path(root) / d == self.source_dir / ignored_dir.replace("/", os.sep)
                for ignored_dir in self.IGNORE_DIRS
            )]
            
            for filename in filenames:
                if filename.endswith(".md"):
                    file_path = Path(root) / filename
                    files.append(file_path)
        
        return files
    
    async def translate(self, target_langs: Optional[List[str]] = None, force: bool = False):
        """
        执行翻译
        
        :param target_langs: 目标语言列表，None 表示使用配置中的所有语言
        :param force: 是否强制重新翻译
        """
        self.stats["start_time"] = time.time()
        
        if target_langs is None:
            target_langs = self.config.get("target_langs", [])
        
        print("=" * 60)
        print("ErisPulse 文档翻译器")
        print("=" * 60)
        print()
        print(f"源语言: {self.config['source_lang']}")
        print(f"目标语言: {', '.join(target_langs)}")
        print(f"并发数: {self.config.get('concurrent', 5)}")
        print()
        
        # 扫描文件
        print("[1/3] 扫描文档文件...")
        files = self.scan_files()
        self.stats["total_files"] = len(files)
        print(f"  发现 {len(files)} 个 Markdown 文件")
        print()
        
        # 并发翻译
        print("[2/3] 开始翻译...")
        concurrent = self.config.get("concurrent", 5)
        
        for target_lang in target_langs:
            print(f"\n翻译到 {self.LANG_CONFIG.get(target_lang, {}).get('name', target_lang)}...")
            print("-" * 60)
            
            # 创建异步任务列表
            tasks = [
                self.translate_file(file_path, target_lang, force)
                for file_path in files
            ]
            
            # 控制并发数
            semaphore = asyncio.Semaphore(concurrent)
            
            async def translate_with_limit(task):
                async with semaphore:
                    return await task
            
            # 并发执行所有翻译任务
            results = await asyncio.gather(
                *[translate_with_limit(task) for task in tasks],
                return_exceptions=True
            )
            
            # 统计结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    file_path = files[i]
                    print(f"  [错误] {file_path}: {result}")
                    self.stats["failed_files"] += 1
        
        print()
        
        # 完成统计
        self.stats["end_time"] = time.time()
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        print("[3/3] 翻译完成！")
        print("=" * 60)
        print(f"总文件数: {self.stats['total_files']}")
        print(f"成功翻译: {self.stats['translated_files']}")
        print(f"跳过文件: {self.stats['skipped_files']}")
        print(f"失败文件: {self.stats['failed_files']}")
        print(f"耗时: {duration:.2f} 秒")
        if self.stats['translated_files'] > 0:
            print(f"速度: {self.stats['translated_files']/duration:.2f} 文件/秒")
        print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(
        description="ErisPulse 文档翻译器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置翻译所有语言
  python scripts/tools/translate-docs.py
  
  # 只翻译到英语
  python scripts/tools/translate-docs.py --lang en
  
  # 强制重新翻译
  python scripts/tools/translate-docs.py --force
  
  # 使用自定义配置文件
  python scripts/tools/translate-docs.py --config custom-config.json
        """
    )
    
    parser.add_argument(
        "--config",
        default="scripts/tools/translate-config.json",
        help="配置文件路径 (默认: scripts/tools/translate-config.json)"
    )
    parser.add_argument(
        "--lang",
        nargs="+",
        help="目标语言列表 (如: en ja)，默认翻译配置中的所有语言"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新翻译所有文件"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="ErisPulse 文档翻译器"
    )
    
    args = parser.parse_args()
    
    # 创建并运行翻译器
    translator = DocsTranslator(args.config)
    await translator.translate(target_langs=args.lang, force=args.force)


if __name__ == "__main__":
    asyncio.run(main())