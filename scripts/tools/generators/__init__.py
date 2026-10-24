"""文档生成器组：CI auto-update-docs / auto-tag-release 的子命令注册表。

键为 ``python -m scripts.tools gen <名>`` 的子命令名；
值为 ``(帮助文案, main 函数)``——main 接收 ``argv`` 列表（不含组名/子命令名）。
"""

from . import ai_prompts, api_docs, docs_index, skills, type_stubs

GENERATORS = {
    "api-docs": ("API 参考文档生成（源码 docstring → docs/*/api-reference）", api_docs.main),
    "ai-prompts": ("AI 提示词包生成（docs/*/ai-support/prompts）", ai_prompts.main),
    "docs-index": ("文档索引生成（meta / 导航 / README）", docs_index.main),
    "skills": ("Agent Skills 生成（docs/*/ai-support/skills）", skills.main),
    "type-stubs": ("类型存根生成（SendDSL 等 IDE 补全用）", type_stubs.main),
}

__all__ = ["GENERATORS"]
