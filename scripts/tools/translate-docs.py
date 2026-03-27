"""
ErisPulse 文档翻译器

使用 AI 自动翻译文档到其他语言

特性：
- 流式输出推理过程和翻译结果
- 每个文档支持独立的审查备注，按语言目录集中存储，避免重复犯错
- 自动加载已有翻译作为参考，确保翻译一致性
- 翻译缓存按语言代码目录分级管理

目录结构：
  .github/
  ├── .translate_cache/          # 翻译缓存
  │   ├── README.en.md.cache    # 根目录 README 英文缓存
  │   ├── README.zh-TW.md.cache # 根目录 README 繁中缓存
  │   ├── en/                   # 英文缓存（docs 下文档）
  │   │   └── getting-started/first-bot.md.cache
  │   └── zh-TW/                # 繁中缓存（docs 下文档）
  │       └── ...
  └── .translate_notes/         # 人工审查备注
      ├── en/                   # 英文审查备注
      │   ├── README.md.notes.json
      │   └── getting-started/first-bot.md.notes.json
      └── zh-TW/                # 繁中审查备注
          └── ...
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
        
        base_dir = Path(self.config.get("cache_dir", ".github/.translate_cache")).parent
        self.cache_dir = base_dir / ".translate_cache"
        self.notes_dir = base_dir / ".translate_notes"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        
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
                "cache_dir": ".github/.translate_cache"
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
        计算文件的 MD5 哈希值（统一转换为 LF 行尾符）
        
        :param file_path: 文件路径
        :return: 哈希值
        """
        with open(file_path, "rb") as f:
            content = f.read()
            content = content.replace(b'\r\n', b'\n')
            return hashlib.md5(content).hexdigest()
    
    def _get_rel_path(self, file_path: Path) -> str:
        """
        获取源文件相对于 source_dir 的路径（用于缓存和备注定位）

        根目录 README.md 返回 "README.md"，
        其他文件返回相对于 source_dir 的路径如 "getting-started/first-bot.md"

        :param file_path: 源文件路径
        :return: 相对路径字符串
        """
        if file_path.name == "README.md" and file_path.parent == Path("."):
            return "README.md"
        return str(file_path.relative_to(self.source_dir))
    
    def _is_root_readme(self, file_path: Path) -> bool:
        """
        判断是否为根目录的 README.md

        :param file_path: 文件路径
        :return: 是否为根目录 README
        """
        return file_path.name == "README.md" and file_path.parent == Path(".")

    def get_cache_key(self, file_path: Path, target_lang: str) -> Path:
        """
        获取缓存文件路径

        根目录 README.md -> .github/.translate_cache/README.{lang}.md.cache
        docs 下文档 -> .github/.translate_cache/{lang}/{rel_path}.cache

        :param file_path: 源文件路径
        :param target_lang: 目标语言
        :return: 缓存文件路径
        """
        if self._is_root_readme(file_path):
            # 根目录 README 直接放在 cache_dir 下，用目标文件名命名
            return self.cache_dir / f"README.{target_lang}.md.cache"
        rel_path = self._get_rel_path(file_path)
        return self.cache_dir / target_lang / f"{rel_path}.cache"
    
    def is_file_changed(self, file_path: Path, target_lang: str) -> bool:
        """
        检查文件是否发生变化（需要重新翻译）
        
        :param file_path: 源文件路径
        :param target_lang: 目标语言
        :return: 是否需要重新翻译
        """
        cache_key = self.get_cache_key(file_path, target_lang)
        
        if os.environ.get("DEBUG_TRANSLATE"):
            print(f"    [DEBUG] 源文件: {file_path}")
            print(f"    [DEBUG] 缓存文件: {cache_key}")
            print(f"    [DEBUG] 缓存存在: {cache_key.exists()}")
        
        if not cache_key.exists():
            if os.environ.get("DEBUG_TRANSLATE"):
                print(f"    [DEBUG] 缓存文件不存在，需要翻译")
            return True
        
        with open(cache_key, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        current_hash = self.calculate_file_hash(file_path)
        cached_hash = cache_data.get("hash")
        
        if os.environ.get("DEBUG_TRANSLATE"):
            print(f"    [DEBUG] 当前文件哈希: {current_hash}")
            print(f"    [DEBUG] 缓存中的哈希: {cached_hash}")
            print(f"    [DEBUG] 哈希匹配: {current_hash == cached_hash}")
        
        return cached_hash != current_hash
    
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
    
    def load_review_notes(self, file_path: Path, target_lang: str) -> List[str]:
        """
        加载文档的人工审查备注

        审查备注按语言目录集中存储：
        .github/.translate_notes/{lang}/{rel_path}.notes.json

        文件内容为字符串数组：
        ["备注1", "备注2", ...]

        :param file_path: 源文件路径
        :param target_lang: 目标语言
        :return: 审查备注列表
        """
        rel_path = self._get_rel_path(file_path)
        notes_file = self.notes_dir / target_lang / f"{rel_path}.notes.json"
        
        if not notes_file.exists():
            return []
        
        try:
            with open(notes_file, "r", encoding="utf-8") as f:
                notes = json.load(f)
            
            if not isinstance(notes, list):
                return []
            
            if notes and os.environ.get("DEBUG_TRANSLATE"):
                print(f"    [DEBUG] 加载审查备注: {notes_file} ({len(notes)} 条)")
            return notes
        except Exception as e:
            print(f"    [警告] 读取审查备注失败 {notes_file}: {e}")
            return []
    
    def load_reference_translation(self, file_path: Path, target_lang: str) -> Optional[str]:
        """
        加载已有的翻译作为参考

        读取 docs/{target_lang}/ 下对应的翻译文件，
        为 AI 提供翻译一致性参考。

        :param file_path: 源文件路径
        :param target_lang: 目标语言
        :return: 已有翻译内容，不存在则返回 None
        """
        if file_path.name == "README.md" and file_path.parent == Path("."):
            ref_file = Path(f"README.{target_lang}.md")
        else:
            rel_path = file_path.relative_to(self.source_dir)
            ref_file = Path("docs") / target_lang / rel_path
        
        if not ref_file.exists():
            return None
        
        try:
            with open(ref_file, "r", encoding="utf-8") as f:
                ref_content = f.read()
            
            if os.environ.get("DEBUG_TRANSLATE"):
                print(f"    [DEBUG] 加载参考翻译: {ref_file} ({len(ref_content)} 字符)")
            return ref_content
        except Exception as e:
            print(f"    [警告] 读取参考翻译失败 {ref_file}: {e}")
            return None
    
    def build_translation_prompt(self, content: str, target_lang: str, file_name: str,
                                  review_notes: List[str] = None,
                                  reference_translation: str = None) -> str:
        """
        构建翻译提示词
        
        :param content: 要翻译的内容
        :param target_lang: 目标语言
        :param file_name: 文件名（用于特殊处理）
        :param review_notes: 人工审查备注列表
        :param reference_translation: 已有翻译（参考用）
        :return: 提示词
        """
        lang_name = self.LANG_CONFIG.get(target_lang, {}).get("name", target_lang)
        source_lang = self.config["source_lang"]
        
        base_rules = """翻译要求：
1. 保持Markdown格式完整，包括标题、列表、代码块、链接、图片等
2. 准确翻译技术术语，保持专业性
3. 代码块中的代码不要翻译，但可以翻译代码中的注释
4. 保持原文档的结构和语气
5. 对于专业术语，如果{lang}中对应术语不确定，可以保留英文原词
6. 不要添加任何额外的解释或说明，只返回翻译后的内容""".format(lang=lang_name)
        
        path_replacement_hint = ""
        if file_name == "README.md":
            path_replacement_hint = f"""
7. **重要：路径替换规则**
   - 将文档链接中的 `docs/{source_lang}/` 替换为 `docs/{target_lang}/`
   - 例如：`docs/{source_lang}/quick-start.md` 应改为 `docs/{target_lang}/quick-start.md`
   - 这确保了链接指向正确语言的文档版本"""
        
        review_section = ""
        if review_notes:
            notes_text = "\n".join(f"  - {note}" for note in review_notes)
            review_section = f"""

**⚠️ 人工审查备注（必须严格遵守，这是之前翻译中发现并修正的问题）：**
{notes_text}"""
        
        reference_section = ""
        if reference_translation:
            reference_section = f"""

**📖 已有翻译参考（请保持与以下翻译的术语和风格一致性）：**
```
{reference_translation}
```
注意：源文档可能有更新，请以源文档为准进行翻译，但术语、用词风格应与参考翻译保持一致。"""
        
        prompt = f"""你是一个专业的技术文档翻译专家。请将以下Markdown文档翻译成{lang_name}。

{base_rules}{path_replacement_hint}{review_section}{reference_section}

待翻译内容：

{content}

请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。"""
        
        return prompt
    
    async def call_translation_api(self, content: str, target_lang: str, file_name: str,
                                    review_notes: List[str] = None,
                                    reference_translation: str = None) -> Optional[str]:
        """
        调用翻译 API
        
        :param content: 要翻译的内容
        :param target_lang: 目标语言
        :param file_name: 文件名（用于显示和特殊处理）
        :param review_notes: 人工审查备注列表
        :param reference_translation: 已有翻译（参考用）
        :return: 翻译后的内容
        """
        try:
            model = self.config.get("model", "gpt-4")
            prompt = self.build_translation_prompt(
                content, target_lang, file_name,
                review_notes=review_notes,
                reference_translation=reference_translation
            )
            
            translated_content = []
            
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
            
            has_reasoning = False
            has_content = False

            print(f"\n    正在翻译 {file_name} 到 {target_lang} 中...", flush=True)

            async for chunk in stream:
                reasoning = getattr(chunk.choices[0].delta, 'reasoning_content', None)
                if reasoning:
                    if not has_reasoning:
                        print(f"\n    📝 [推理过程]", flush=True)
                        has_reasoning = True
                    print(reasoning, end='', flush=True)

                if chunk.choices[0].delta.content is not None:
                    content_chunk = chunk.choices[0].delta.content
                    if not has_content:
                        print()
                        print(f"    📄 [翻译结果]", flush=True)
                        has_content = True
                    print(content_chunk, end='', flush=True)
                    translated_content.append(content_chunk)

            if has_reasoning or has_content:
                print()
            
            full_content = "".join(translated_content)
            
            if not full_content:
                print(f"  [警告] {file_name} 未接收到任何翻译内容")
                return None
            
            if full_content.startswith("```"):
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
        rel_path = self._get_rel_path(file_path)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not force and not self.is_file_changed(file_path, target_lang):
                self.stats["skipped_files"] += 1
                print(f"  [跳过] {rel_path} (未变化)")
                return True
            
            # 哈希比对信息
            cache_key = self.get_cache_key(file_path, target_lang)
            current_hash = self.calculate_file_hash(file_path)
            if cache_key.exists():
                with open(cache_key, "r", encoding="utf-8") as f:
                    cached_hash = json.load(f).get("hash", "N/A")
                print(f"  [翻译] {rel_path} -> {target_lang} (哈希不匹配: 源={current_hash}, 缓存={cached_hash})")
            else:
                print(f"  [翻译] {rel_path} -> {target_lang} (无缓存, 源哈希={current_hash})")
            
            # 加载人工审查备注
            review_notes = self.load_review_notes(file_path, target_lang)
            if review_notes:
                print(f"    📋 已加载 {len(review_notes)} 条审查备注")
            
            # 加载已有翻译作为参考
            reference_translation = self.load_reference_translation(file_path, target_lang)
            if reference_translation:
                print(f"    📖 已加载参考翻译 ({len(reference_translation)} 字符)")
            
            # 调用翻译 API
            translated_content = await self.call_translation_api(
                content, target_lang, rel_path,
                review_notes=review_notes,
                reference_translation=reference_translation
            )
            
            if not translated_content:
                print(f"  [失败] {rel_path}")
                self.stats["failed_files"] += 1
                return False
            
            # 确定目标路径
            if file_path.name == "README.md" and file_path.parent == Path("."):
                target_file = Path(f"README.{target_lang}.md")
            else:
                target_dir = Path("docs") / target_lang / Path(rel_path).parent
                target_dir.mkdir(parents=True, exist_ok=True)
                target_file = target_dir / Path(rel_path).name
            
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(translated_content)
            
            print(f"  [完成] {rel_path}")
            
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
        
        readme_path = Path("README.md")
        if readme_path.exists():
            files.append(readme_path)
        
        if self.source_dir.exists():
            for root, dirs, filenames in os.walk(self.source_dir):
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
        print(f"审查备注目录: {self.notes_dir}")
        print()
        
        print("[1/3] 扫描文档文件...")
        files = self.scan_files()
        self.stats["total_files"] = len(files)
        print(f"  发现 {len(files)} 个 Markdown 文件")
        print()
        
        print("[2/3] 开始翻译...")
        concurrent = self.config.get("concurrent", 5)
        
        for target_lang in target_langs:
            print(f"\n翻译到 {self.LANG_CONFIG.get(target_lang, {}).get('name', target_lang)}...")
            print("-" * 60)
            
            tasks = [
                self.translate_file(file_path, target_lang, force)
                for file_path in files
            ]
            
            semaphore = asyncio.Semaphore(concurrent)
            
            async def translate_with_limit(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(
                *[translate_with_limit(task) for task in tasks],
                return_exceptions=True
            )
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    file_path = files[i]
                    print(f"  [错误] {file_path}: {result}")
                    self.stats["failed_files"] += 1
        
        print()
        
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

审查备注:
  在 .github/.translate_notes/{语言代码}/ 下创建备注文件，
  文件名与源文档路径对应（扩展名改为 .notes.json）。
  详见 docs/translate-workflow.md
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
    
    translator = DocsTranslator(args.config)
    await translator.translate(target_langs=args.lang, force=args.force)


if __name__ == "__main__":
    asyncio.run(main())