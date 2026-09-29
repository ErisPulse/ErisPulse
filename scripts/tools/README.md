# scripts/tools 工具脚本索引

`scripts/` 与 `scripts/tools/` 下脚本的用途、调用方与 CI 地位一览。新增脚本请同步本表。

## CI 硬门禁（PR 必须通过）

| 脚本 | 用途 | 调用方 |
|------|------|--------|
| `check_i18n_locales.py` | i18n 五语言键一致性（自动发现 Core / CLI 两套 locales） | code-quality-check workflow `i18n-consistency` job |
| `check_docs_links.py` | docs/zh-CN 内部相对链接死链检查（自动排除 ai-support / auto_api 生成目录） | code-quality-check workflow `docs-links` job |

## 发布 / 文档管线（CI 自动执行，勿本地运行）

| 脚本 | 用途 | 调用方 |
|------|------|--------|
| `release_check.py` | 发布三面版本一致性校验（pyproject == CHANGELOG == tag） | pypi-publish / auto-tag-release workflow 首步 |
| `translate-docs.py` | AI 分块增量翻译（缓存续传 + 泄露防线） | auto-update-docs workflow |
| `check-translation.py` | 译文质量检查（缺失/截断/乱码/围栏/泄露），`--fix` 删问题缓存 | auto-update-docs workflow（翻译后自动 `--fix`） |
| `generate-ai-prompts.py` | 由 docs 生成 AI 提示词物料（ai-support/prompts/） | auto-update-docs / auto-tag-release workflow |
| `generate-api-docs.py` | 由源码 docstring 生成 api-reference/auto_api/ | auto-update-docs workflow |
| `generate-docs-index.py` | 生成 docs/_meta 索引（5 语言映射 + 搜索索引） | auto-update-docs workflow |

> 以上生成/翻译产物**入库由 CI 提交**；本地不要运行生成器（AGENTS.md 规则 17），
> 否则会污染提交。`_common.py` 为上述脚本的公共设施（Logger / 围栏计数 / LEAK 正则 /
> IGNORE_DIRS），改泄露特征或围栏语义只改这一处。

## 本地工具（手动按需）

| 脚本 | 用途 | 备注 |
|------|------|------|
| `check_i18n_locales.py` / `check_docs_links.py` / `release_check.py` | CI 门禁的本地等价命令，推送前建议先跑 | 纯标准库，无需装依赖 |
| `translate-docs.py` 等管线脚本 | 调试翻译管线时使用 | 需 API key 配置 |
| `generate-type-stubs.py` | .pyi 存根生成 | **已暂停使用**（生成器有缺陷，发布管线已停用），勿提交生成的 .pyi |

## 已删除

- `invalidate_fence_broken_cache.py`（围栏损坏缓存清理）——功能被 `check-translation.py --fix`
  完全覆盖，且全仓无引用（2026-09 移除）。
