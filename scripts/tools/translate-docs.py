"""
ErisPulse 文档翻译器

使用 AI 自动翻译文档到其他语言

特性：
- 流式输出翻译结果
- 每个文档支持独立的审查备注
- 自动加载已有翻译作为参考
- 翻译后自检（长度、代码块、乱码）
- 429 限速自动指数退避重试
- 可配置是否启用推理/思考模式

使用方法:
    python scripts/tools/translate-docs.py
    python scripts/tools/translate-docs.py --lang en ja
    python scripts/tools/translate-docs.py --force
    python scripts/tools/translate-docs.py --no-check
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from openai import AsyncOpenAI


class RateLimitError(Exception):
    pass


class FatalApiError(Exception):
    pass


class Logger:
    _lock = threading.Lock()

    @classmethod
    def log(cls, msg: str):
        with cls._lock:
            sys.stdout.write(msg + "\n")
            sys.stdout.flush()

    @classmethod
    def write(cls, text: str):
        with cls._lock:
            sys.stdout.write(text)
            sys.stdout.flush()

    @classmethod
    def progress(cls, rel_path: str, target_lang: str, status: str, detail: str = ""):
        tag = {
            "skip": "[SKIP]",
            "trans": "[TRANS]",
            "done": "[DONE]",
            "fail": "[FAIL]",
            "retry": "[RETRY]",
            "check": "[CHECK]",
            "check_pass": "[PASS]",
            "check_fail": "[CHK!]",
            "rate_limit": "[429]",
        }.get(status, f"[{status.upper()}]")
        line = f"  {tag} {rel_path} -> {target_lang}"
        if detail:
            line += f"  {detail}"
        cls.log(line)


class FileBuffer:
    def __init__(self):
        self.parts: List[str] = []

    def write(self, text: str):
        self.parts.append(text)

    def flush(self):
        content = "".join(self.parts)
        self.parts.clear()
        if content:
            with Logger._lock:
                sys.stdout.write(content)
                sys.stdout.flush()


class DocsTranslator:
    LANG_CONFIG = {
        "zh-CN": {"name": "简体中文", "direction": "source"},
        "zh-TW": {"name": "繁体中文", "direction": "target"},
        "en": {"name": "English", "direction": "target"},
        "ja": {"name": "日本語", "direction": "target"},
        "ru": {"name": "Русский", "direction": "target"},
    }

    LANG_SWITCHER_ITEMS = [
        {"lang": "en", "label": "English", "file": "README.md"},
        {"lang": "zh-CN", "label": "简体中文", "file": "README.zh-CN.md"},
        {"lang": "zh-TW", "label": "繁體中文", "file": "README.zh-TW.md"},
        {"lang": "ja", "label": "日本語", "file": "README.ja.md"},
        {"lang": "ru", "label": "Русский", "file": "README.ru.md"},
    ]

    IGNORE_DIRS = ["ai-support/prompts", "api-reference/auto_api", "_meta"]
    REPLACEMENT_CHAR = "\ufffd"
    MIN_LENGTH_RATIO = 0.20

    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.source_dir = Path("docs") / self.config["source_lang"]

        base_dir = Path(self.config.get("cache_dir", ".github/.translate_cache")).parent
        self.cache_dir = base_dir / ".translate_cache"
        self.notes_dir = base_dir / ".translate_notes"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.notes_dir.mkdir(parents=True, exist_ok=True)

        self.providers: List[Dict] = []
        self.clients: List[AsyncOpenAI] = []
        self._init_providers()

        self.enable_reasoning = self._setting("enable_reasoning", False)
        self.enable_self_check = self._setting("self_check", True)
        self.self_check_retries = self._setting("self_check_retries", 1)
        self.max_retries = self._setting("max_retries", 5)
        self.retry_base_delay = self._setting("retry_base_delay", 10)
        self.request_delay = self._setting("request_delay", 2)
        self.max_tokens = self._setting("max_tokens", 8000)
        self.temperature = self._setting("temperature", 0.3)

        self.stats = {
            "total_files": 0,
            "translated_files": 0,
            "skipped_files": 0,
            "failed_files": 0,
            "validation_failed": [],
            "start_time": None,
            "end_time": None,
        }

    def _init_providers(self):
        providers_config = self.config.get("providers", [])
        if providers_config:
            for pc in providers_config:
                api_key = os.environ.get(pc.get("api_key_env", ""))
                if not api_key:
                    name = pc.get("name", pc.get("base_url", "unknown"))
                    Logger.log(
                        f"  [WARN] 服务商 {name} 未配置密钥 ({pc.get('api_key_env')}), 跳过"
                    )
                    continue
                base_url = pc.get("base_url", "https://api.openai.com/v1").rstrip("/")
                client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                self.providers.append(pc)
                self.clients.append(client)
        if not self.providers:
            api_key = os.environ.get(
                self.config.get("api_key_env", "OPENAI_API_KEY"), ""
            )
            if not api_key:
                raise ValueError("未找到任何可用的 API 密钥")
            base_url = self.config.get("base_url", "https://api.openai.com/v1").rstrip(
                "/"
            )
            model = self.config.get("model", "gpt-4")
            self.providers.append(
                {
                    "name": "default",
                    "base_url": base_url,
                    "model": model,
                }
            )
            self.clients.append(AsyncOpenAI(api_key=api_key, base_url=base_url))
        Logger.log(
            f"  可用服务商: {', '.join(p.get('name', p.get('base_url')) for p in self.providers)}"
        )

    def _setting(self, key: str, default=None, provider_index: int = -1):
        if provider_index >= 0 and provider_index < len(self.providers):
            val = self.providers[provider_index].get(key)
            if val is not None:
                return val
        defaults = self.config.get("default", {})
        val = defaults.get(key)
        if val is not None:
            return val
        return default

    def _pick_client(self, index: int):
        i = index % len(self.clients)
        return self.clients[i], self.providers[i]

    def load_config(self, config_path: str) -> Dict:
        config_file = Path(config_path)
        if not config_file.exists():
            return {
                "source_lang": "zh-CN",
                "target_langs": ["zh-TW", "en"],
                "providers": [
                    {
                        "name": "default",
                        "base_url": "https://api.openai.com/v1",
                        "api_key_env": "OPENAI_API_KEY",
                        "model": "gpt-4",
                    }
                ],
                "concurrent": 1,
                "request_delay": 2,
                "max_retries": 5,
                "retry_base_delay": 10,
                "max_tokens": 8000,
                "temperature": 0.3,
                "enable_reasoning": False,
                "self_check": True,
                "self_check_retries": 1,
                "ignore_dirs": ["ai-support/prompts", "api-reference/auto_api"],
                "translate_code_comments": True,
                "cache_dir": ".github/.translate_cache",
            }
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def calculate_file_hash(self, file_path: Path) -> str:
        with open(file_path, "rb") as f:
            content = f.read()
            content = content.replace(b"\r\n", b"\n")
            return hashlib.md5(content).hexdigest()

    def _get_rel_path(self, file_path: Path) -> str:
        if self._is_root_readme(file_path):
            return "README.md"
        return str(file_path.relative_to(self.source_dir)).replace("\\", "/")

    ROOT_README_SOURCE = "README.zh-CN.md"

    def _is_root_readme(self, file_path: Path) -> bool:
        return file_path.name == self.ROOT_README_SOURCE and file_path.parent == Path(
            "."
        )

    def _build_lang_switcher_hint(self, target_lang: str) -> str:
        parts = []
        for item in self.LANG_SWITCHER_ITEMS:
            if item["lang"] == target_lang:
                parts.append(f"**{item['label']}**")
            else:
                parts.append(f"[{item['label']}]({item['file']})")
        expected_line = " | ".join(parts)
        return (
            f"8. **重要：语言切换行本地化**\n"
            f"   - 必须将语言切换行替换为以下内容（不要修改）：\n"
            f"   `{expected_line}`\n"
            f"   - 规则：当前目标语言（{target_lang}）使用粗体，其他语言为链接"
        )

    def get_cache_key(self, file_path: Path, target_lang: str) -> Path:
        if self._is_root_readme(file_path):
            if target_lang == "en":
                return self.cache_dir / "README.md.cache"
            elif target_lang == "zh-CN":
                return self.cache_dir / "README.zh-CN.md.cache"
            return self.cache_dir / f"README.{target_lang}.md.cache"
        rel_path = self._get_rel_path(file_path)
        return self.cache_dir / target_lang / f"{rel_path}.cache"

    def is_file_changed(self, file_path: Path, target_lang: str) -> bool:
        cache_key = self.get_cache_key(file_path, target_lang)
        if not cache_key.exists():
            return True
        with open(cache_key, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        current_hash = self.calculate_file_hash(file_path)
        return cache_data.get("hash") != current_hash

    def save_cache(self, file_path: Path, target_lang: str, hash_value: str):
        cache_key = self.get_cache_key(file_path, target_lang)
        cache_key.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_key, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "hash": hash_value,
                    "translated_at": datetime.now().isoformat(),
                    "target_lang": target_lang,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def load_review_notes(self, file_path: Path, target_lang: str) -> List[str]:
        rel_path = self._get_rel_path(file_path)
        notes_file = self.notes_dir / target_lang / f"{rel_path}.notes.json"
        if not notes_file.exists():
            return []
        try:
            with open(notes_file, "r", encoding="utf-8") as f:
                notes = json.load(f)
            return notes if isinstance(notes, list) else []
        except Exception:
            return []

    def load_reference_translation(
        self, file_path: Path, target_lang: str
    ) -> Optional[str]:
        if self._is_root_readme(file_path):
            if target_lang == "en":
                ref_file = Path("README.md")
            else:
                ref_file = Path(f"README.{target_lang}.md")
        else:
            rel_path = file_path.relative_to(self.source_dir)
            ref_file = Path("docs") / target_lang / rel_path
        if not ref_file.exists():
            return None
        try:
            with open(ref_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def build_translation_prompt(
        self,
        content: str,
        target_lang: str,
        file_name: str,
        review_notes: List[str] = None,
        reference_translation: str = None,
    ) -> str:
        lang_name = self.LANG_CONFIG.get(target_lang, {}).get("name", target_lang)
        source_lang = self.config["source_lang"]

        base_rules = (
            f"翻译要求：\n"
            f"1. 保持Markdown格式完整，包括标题、列表、代码块、链接、图片等\n"
            f"2. 准确翻译技术术语，保持专业性\n"
            f"3. 代码块中的代码逻辑不要翻译，但代码中的中文注释、中文字符串必须翻译为{lang_name}\n"
            f"4. 保持原文档的结构和语气\n"
            f"5. 对于专业术语，如果{lang_name}中对应术语不确定，可以保留英文原词\n"
            f"6. 不要添加任何额外的解释或说明，只返回翻译后的内容\n"
            f"7. 确保翻译后文档中不残留任何中文（除专有名词外），包括代码块中的注释和字符串\n"
            f"8. 直接输出翻译后的Markdown内容，不要用```markdown等代码块包裹"
        )

        path_replacement_hint = ""
        if file_name == "README.md":
            lang_switcher_hint = self._build_lang_switcher_hint(target_lang)
            path_replacement_hint = (
                f"\n7. **重要：路径替换规则**\n"
                f"   - 将文档链接中的 `docs/{source_lang}/` 替换为 `docs/{target_lang}/`\n"
                f"   - 例如：`docs/{source_lang}/quick-start.md` 应改为 `docs/{target_lang}/quick-start.md`\n"
                f"   - 这确保了链接指向正确语言的文档版本\n"
                f"{lang_switcher_hint}"
            )

        review_section = ""
        if review_notes:
            notes_text = "\n".join(f"  - {note}" for note in review_notes)
            review_section = f"\n\n**人工审查备注（必须严格遵守）：**\n{notes_text}"

        reference_section = ""
        if reference_translation:
            reference_section = (
                f"\n\n**已有翻译参考（请保持术语和风格一致性）：**\n"
                f"```\n{reference_translation}\n```\n"
                f"\n"
                f"**重要 — 源文档与参考翻译冲突处理规则：**\n"
                f"1. 源文档中**被修改的部分**可能是人工修正过的内容，不应盲目恢复为参考翻译的旧版本\n"
                f"2. 术语、用词风格应与参考翻译保持一致，不要随意更换已有译法"
            )

        return (
            f"你是一个专业的技术文档翻译专家。请将以下Markdown文档翻译成{lang_name}。\n\n"
            f"{base_rules}{path_replacement_hint}{review_section}{reference_section}\n\n"
            f"待翻译内容：\n\n{content}\n\n"
            f"请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。"
        )

    def build_correction_prompt(
        self,
        source_content: str,
        translated_content: str,
        target_lang: str,
        file_name: str,
        issues: List[str],
    ) -> str:
        lang_name = self.LANG_CONFIG.get(target_lang, {}).get("name", target_lang)
        issues_text = "\n".join(f"  - {issue}" for issue in issues)
        return (
            f"你是一个专业的技术文档翻译专家。你之前翻译的一份文档存在以下问题，请修正后重新返回完整文档。\n\n"
            f"**目标语言**: {lang_name}\n\n"
            f"**检测到的问题**:\n{issues_text}\n\n"
            f"**原始文档**:\n\n{source_content}\n\n"
            f"**你之前的翻译（有问题的版本）**:\n\n{translated_content}\n\n"
            f"请修正上述问题，返回完整的修正后翻译文档。注意：\n"
            f"1. 修正所有指出的问题\n"
            f"2. 代码块中的中文注释和字符串也必须翻译为{lang_name}\n"
            f"3. 保持Markdown格式完整\n"
            f"4. 直接返回修正后的完整文档，不要解释修正了什么"
        )

    async def call_correction_api(
        self,
        source_content: str,
        translated_content: str,
        target_lang: str,
        file_name: str,
        issues: List[str],
        buffer: Optional[FileBuffer] = None,
        provider_index: int = 0,
    ) -> Optional[str]:
        try:
            client, provider = self._pick_client(provider_index)
            model = provider.get("model", "gpt-4")
            temperature = self._setting("temperature", 0.3, provider_index)
            max_tokens = self._setting("max_tokens", 8000, provider_index)
            enable_reasoning = self._setting("enable_reasoning", False, provider_index)
            prompt = self.build_correction_prompt(
                source_content, translated_content, target_lang, file_name, issues
            )
            translated = []
            create_kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }
            if not enable_reasoning:
                supports = provider.get("supports_thinking", True)
                if supports:
                    create_kwargs["extra_body"] = {"enable_thinking": False}

            stream = await client.chat.completions.create(**create_kwargs)
            finish_reason = None
            has_reasoning = False
            has_content = False
            out = buffer if buffer else Logger
            async for chunk in stream:
                choice = chunk.choices[0]
                if choice.finish_reason is not None:
                    finish_reason = choice.finish_reason

                reasoning = getattr(choice.delta, "reasoning_content", None)
                if reasoning:
                    if not has_reasoning:
                        out.write("    [推理过程-修正]\n")
                        has_reasoning = True
                    out.write(reasoning)

                if choice.delta.content is not None:
                    if not has_content:
                        if has_reasoning:
                            out.write("\n")
                        out.write("    [修正结果]\n")
                        has_content = True
                    out.write(choice.delta.content)
                    translated.append(choice.delta.content)

            if has_reasoning or has_content:
                out.write("\n")

            if finish_reason == "length":
                Logger.progress(
                    file_name,
                    target_lang,
                    "fail",
                    f"修正翻译被 max_tokens={self.max_tokens} 截断",
                )
                return None

            if not translated:
                return None

            full = "".join(translated)
            lines = full.split("\n")
            if lines and lines[0].strip() == "```":
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return "\n".join(lines).strip()

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate" in error_msg.lower() or "速率" in error_msg:
                raise RateLimitError(error_msg)
            if (
                "403" in error_msg
                or "401" in error_msg
                or "insufficient" in error_msg.lower()
            ):
                raise FatalApiError(error_msg)
            Logger.log(f"  [ERROR] correction {file_name}: {e}")
            return None

    async def call_translation_api(
        self,
        content: str,
        target_lang: str,
        file_name: str,
        review_notes: List[str] = None,
        reference_translation: str = None,
        buffer: Optional[FileBuffer] = None,
        provider_index: int = 0,
    ) -> Optional[str]:
        try:
            client, provider = self._pick_client(provider_index)
            model = provider.get("model", "gpt-4")
            enable_reasoning = self._setting("enable_reasoning", False, provider_index)
            max_tokens = self._setting("max_tokens", 8000, provider_index)
            temperature = self._setting("temperature", 0.3, provider_index)
            prompt = self.build_translation_prompt(
                content,
                target_lang,
                file_name,
                review_notes=review_notes,
                reference_translation=reference_translation,
            )

            translated_content = []

            create_kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的技术文档翻译专家。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }

            if not enable_reasoning:
                supports = provider.get("supports_thinking", True)
                if supports:
                    create_kwargs["extra_body"] = {"enable_thinking": False}

            stream = await client.chat.completions.create(**create_kwargs)

            finish_reason = None
            has_reasoning = False
            has_content = False
            out = buffer if buffer else Logger

            async for chunk in stream:
                choice = chunk.choices[0]
                if choice.finish_reason is not None:
                    finish_reason = choice.finish_reason

                reasoning = getattr(choice.delta, "reasoning_content", None)
                if reasoning:
                    if not has_reasoning:
                        out.write("    [推理过程]\n")
                        has_reasoning = True
                    out.write(reasoning)

                if choice.delta.content is not None:
                    if not has_content:
                        if has_reasoning:
                            out.write("\n")
                        out.write("    [翻译结果]\n")
                        has_content = True
                    out.write(choice.delta.content)
                    translated_content.append(choice.delta.content)

            if has_reasoning or has_content:
                out.write("\n")

            if finish_reason == "length":
                Logger.progress(
                    file_name,
                    target_lang,
                    "fail",
                    f"max_tokens={self.max_tokens} 不够，翻译被截断",
                )
                return None

            if not translated_content:
                return None

            full_content = "".join(translated_content)

            lines = full_content.split("\n")
            if lines:
                first = lines[0].strip()
                if first == "```markdown" or first == "```md" or first == "```":
                    lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            full_content = "\n".join(lines)

            return full_content.strip()

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate" in error_msg.lower() or "速率" in error_msg:
                raise RateLimitError(error_msg)
            if (
                "403" in error_msg
                or "401" in error_msg
                or "insufficient" in error_msg.lower()
                or "余额" in error_msg
            ):
                raise FatalApiError(error_msg)
            Logger.log(f"  [ERROR] {file_name}: {e}")
            return None

    async def _ai_validate_translation(
        self,
        source_content: str,
        translated_content: str,
        target_lang: str,
        rel_path: str,
        provider_index: int = 0,
    ) -> List[str]:
        lang_name = self.LANG_CONFIG.get(target_lang, {}).get("name", target_lang)
        source_lang = self.LANG_CONFIG.get(self.config["source_lang"], {}).get(
            "name", "中文"
        )

        prompt = (
            f"你是一个专业的多语言文档翻译质检员。请对比源文档（{source_lang}）和翻译后的文档（{lang_name}），"
            f'仔细检查翻译质量。如果没有任何问题，只返回以下字符串：{{"status": "ok"}}。\n\n'
            f"请重点检查以下可能存在的问题（仅报告明确的问题，不确定的不报）：\n"
            f"1. 源语言（{source_lang}）的纯文字内容未翻译（保留在目标文档中）\n"
            f"2. 目标文档中混入了不属于目标语言的文字（如：{lang_name}文档中出现{source_lang}文字）\n"
            f"3. Markdown 结构损坏：代码块未正确关闭（``` 不配对）\n"
            f"4. 标题层级不匹配：源文档和目标文档的 H1 标题数量不一致\n"
            f"5. 文档明显被截断（翻译长度远小于源文档）\n"
            f"6. 包含乱码字符（替换字符 \\ufffd）或编码错误\n"
            f"7. 代码块中的中文注释未翻译为{lang_name}（如果代码块完整可读）\n"
            f'8. 非目标语言的注释或字符串残留（如 C/C++/Java/Python 代码中的 print("中文")）\n\n'
            f"请注意：普通英文技术术语保留原样不算问题，仅报告真正的翻译质量问题。\n\n"
            f'如果没有问题，返回：{{"status": "ok"}}。'
            f"\n\n--- 源文档 ---\n{source_content[:8000]}\n\n"
            f"--- {lang_name}翻译文档 ---\n{translated_content[:8000]}\n\n"
        )

        try:
            client, provider = self._pick_client(provider_index % len(self.clients))
            model = provider.get("model", "gpt-4")
            temperature = self._setting(
                "temperature", 0.1, provider_index % len(self.providers)
            )
            max_tokens = self._setting(
                "max_tokens", 4000, provider_index % len(self.providers)
            )

            stream = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个文档翻译质量检查专家。只返回JSON数组，不要任何解释。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response = stream.choices[0].message.content.strip()
            json_match = re.search(r"\{.*?\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if isinstance(data, dict) and data.get("status") == "ok":
                    return []
                issues = data.get("issues", []) if isinstance(data, dict) else data
                if isinstance(issues, list) and issues:
                    Logger.progress(
                        rel_path,
                        target_lang,
                        "check_fail",
                        f"AI发现{len(issues)}个问题",
                    )
                return [str(i) for i in issues] if issues else []
            elif "ok" in response.lower():
                return []
            else:
                return []
        except Exception as e:
            Logger.log(f"  [WARN] AI检查失败: {e}")
            return []

    def _validate_translation(
        self,
        source_content: str,
        translated_content: str,
        target_lang: str,
        rel_path: str,
    ) -> List[str]:
        return []

    async def translate_file(
        self,
        file_path: Path,
        target_lang: str,
        force: bool = False,
        no_check: bool = False,
        file_index: int = 0,
    ) -> bool:
        rel_path = self._get_rel_path(file_path)
        concurrent = self.config.get("concurrent", 1)
        use_buffer = concurrent > 1
        buf = FileBuffer() if use_buffer else None
        pidx = file_index % len(self.clients) if self.clients else 0
        provider_name = self.providers[pidx].get("name", "?") if self.providers else "?"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if not force and not self.is_file_changed(file_path, target_lang):
                self.stats["skipped_files"] += 1
                Logger.progress(rel_path, target_lang, "skip")
                return True

            Logger.progress(rel_path, target_lang, "trans", f"[{provider_name}]")

            review_notes = self.load_review_notes(file_path, target_lang)
            reference_translation = self.load_reference_translation(
                file_path, target_lang
            )

            fatal = False
            translated_content = None

            for attempt in range(1, self.max_retries + 1):
                try:
                    translated_content = await self.call_translation_api(
                        content,
                        target_lang,
                        rel_path,
                        review_notes=review_notes,
                        reference_translation=reference_translation,
                        buffer=buf,
                        provider_index=pidx,
                    )
                except RateLimitError:
                    delay = min(self.retry_base_delay * (2 ** (attempt - 1)), 120)
                    Logger.progress(
                        rel_path,
                        target_lang,
                        "rate_limit",
                        f"等待{delay}s (第{attempt}次)",
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(delay)
                    continue
                except FatalApiError as e:
                    Logger.progress(rel_path, target_lang, "fail", f"不可重试: {e}")
                    self.stats["failed_files"] += 1
                    fatal = True
                    break

                if translated_content:
                    break

                if attempt < self.max_retries:
                    delay = min(self.retry_base_delay * (2 ** (attempt - 1)), 60)
                    Logger.progress(
                        rel_path,
                        target_lang,
                        "retry",
                        f"第{attempt + 1}/{self.max_retries}次, 等待{delay}s",
                    )
                    await asyncio.sleep(delay)

            if not translated_content:
                if not fatal:
                    Logger.progress(
                        rel_path, target_lang, "fail", f"重试{self.max_retries}次"
                    )
                    self.stats["failed_files"] += 1
                return False

            if self.enable_self_check and not no_check:
                Logger.progress(
                    rel_path, target_lang, "check", "正在 AI 自检翻译质量..."
                )
                issues = await self._ai_validate_translation(
                    content, translated_content, target_lang, rel_path, pidx
                )
                if issues:
                    check_passed = False
                    for vr in range(1, self.self_check_retries + 1):
                        Logger.progress(
                            rel_path,
                            target_lang,
                            "retry",
                            f"自检修正 {vr}/{self.self_check_retries}: {issues[0]}",
                        )
                        retry_content = None
                        try:
                            retry_content = await self.call_correction_api(
                                content,
                                translated_content,
                                target_lang,
                                rel_path,
                                issues,
                                buffer=buf,
                                provider_index=pidx,
                            )
                        except (RateLimitError, FatalApiError):
                            await asyncio.sleep(self.retry_base_delay)
                            continue

                        if retry_content:
                            retry_issues = await self._ai_validate_translation(
                                content, retry_content, target_lang, rel_path, pidx
                            )
                            if not retry_issues:
                                translated_content = retry_content
                                check_passed = True
                                break
                            issues = retry_issues
                            translated_content = retry_content
                        else:
                            continue

                    if not check_passed:
                        Logger.progress(
                            rel_path, target_lang, "check_fail", "自检未通过，仍保存"
                        )
                        self.stats["validation_failed"].append(
                            f"{rel_path} -> {target_lang}"
                        )

            if buf:
                buf.flush()

            if self._is_root_readme(file_path):
                if target_lang == "en":
                    target_file = Path("README.md")
                else:
                    target_file = Path(f"README.{target_lang}.md")
            else:
                target_dir = Path("docs") / target_lang / Path(rel_path).parent
                target_dir.mkdir(parents=True, exist_ok=True)
                target_file = target_dir / Path(rel_path).name

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(translated_content)

            file_hash = self.calculate_file_hash(file_path)
            self.save_cache(file_path, target_lang, file_hash)

            Logger.progress(rel_path, target_lang, "done")
            self.stats["translated_files"] += 1

            if self.request_delay > 0:
                await asyncio.sleep(self.request_delay)

            return True

        except Exception as e:
            Logger.progress(rel_path, target_lang, "fail", str(e))
            self.stats["failed_files"] += 1
            return False

    def scan_files(self) -> List[Path]:
        files = []
        readme_path = Path(self.ROOT_README_SOURCE)
        if readme_path.exists():
            files.append(readme_path)
        if self.source_dir.exists():
            for root, dirs, filenames in os.walk(self.source_dir):
                dirs[:] = [
                    d
                    for d in dirs
                    if not any(
                        Path(root) / d == self.source_dir / ignored.replace("/", os.sep)
                        for ignored in self.IGNORE_DIRS
                    )
                ]
                for filename in filenames:
                    if filename.endswith(".md"):
                        files.append(Path(root) / filename)
        return files

    async def translate(
        self,
        target_langs: Optional[List[str]] = None,
        force: bool = False,
        no_check: bool = False,
    ):
        self.stats["start_time"] = time.time()

        if target_langs is None:
            target_langs = self.config.get("target_langs", [])

        Logger.log("=" * 60)
        Logger.log("ErisPulse 文档翻译器")
        Logger.log("=" * 60)
        Logger.log(f"源语言: {self.config['source_lang']}")
        Logger.log(f"目标语言: {', '.join(target_langs)}")
        Logger.log(f"并发数: {self.config.get('concurrent', 1)}")
        Logger.log(f"服务商数: {len(self.providers)}")
        Logger.log(f"推理模式: {'开启' if self.enable_reasoning else '关闭'}")
        Logger.log(
            f"自检: {'开启' if self.enable_self_check and not no_check else '关闭'}"
        )
        Logger.log("")

        files = self.scan_files()
        self.stats["total_files"] = len(files)
        Logger.log(f"发现 {len(files)} 个文件")
        Logger.log("")

        concurrent = self.config.get("concurrent", 1)

        for target_lang in target_langs:
            lang_name = self.LANG_CONFIG.get(target_lang, {}).get("name", target_lang)
            Logger.log(f"--- {lang_name} ({target_lang}) ---")

            semaphore = asyncio.Semaphore(concurrent)

            async def _translate(file_path, idx):
                async with semaphore:
                    return await self.translate_file(
                        file_path, target_lang, force, no_check, file_index=idx
                    )

            results = await asyncio.gather(
                *[_translate(fp, i) for i, fp in enumerate(files)],
                return_exceptions=True,
            )

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    Logger.progress(
                        self._get_rel_path(files[i]), target_lang, "fail", str(result)
                    )
                    self.stats["failed_files"] += 1

        self.stats["end_time"] = time.time()
        duration = self.stats["end_time"] - self.stats["start_time"]

        Logger.log("")
        Logger.log("=" * 60)
        Logger.log(f"总文件: {self.stats['total_files']}")
        Logger.log(f"翻译: {self.stats['translated_files']}")
        Logger.log(f"跳过: {self.stats['skipped_files']}")
        Logger.log(f"失败: {self.stats['failed_files']}")
        Logger.log(f"耗时: {duration:.1f}s")
        if self.stats["translated_files"] > 0 and duration > 0:
            Logger.log(f"速度: {self.stats['translated_files'] / duration:.2f} 文件/秒")
        if self.stats["validation_failed"]:
            Logger.log(f"自检未通过: {len(self.stats['validation_failed'])} 个")
            for f in self.stats["validation_failed"]:
                Logger.log(f"  - {f}")
        Logger.log("=" * 60)


async def main():
    import signal

    def handle_sigint(sig, frame):
        raise KeyboardInterrupt("用户中断")

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    try:
        parser = argparse.ArgumentParser(
            description="ErisPulse 文档翻译器",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument("--config", default="scripts/tools/translate-config.json")
        parser.add_argument("--lang", nargs="+", help="目标语言 (如: en ja)")
        parser.add_argument("--force", action="store_true", help="强制重新翻译所有文件")
        parser.add_argument("--no-check", action="store_true", help="跳过翻译后自检")
        parser.add_argument(
            "--version", action="version", version="ErisPulse 文档翻译器"
        )

        args = parser.parse_args()
        translator = DocsTranslator(args.config)
        await translator.translate(
            target_langs=args.lang, force=args.force, no_check=args.no_check
        )
    except KeyboardInterrupt:
        Logger.log("")
        Logger.log("用户中断，正在退出...")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
