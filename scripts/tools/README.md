# scripts/tools 工具脚本索引

`scripts/` 与 `scripts/tools/` 下脚本的用途、调用方与 CI 地位一览。新增脚本请同步本表。

## CI 硬门禁（PR 必须通过）

| 脚本 | 用途 | 调用方 |
|------|------|--------|
| `check_i18n_locales.py` | i18n 五语言键一致性（自动发现 Core / CLI 两套 locales） | code-quality-check workflow `i18n-consistency` job |
| `check_docs_links.py` | docs/zh-CN 内部相对链接死链检查（自动排除 ai-support / auto_api 生成目录；`#锚点` 仅剥离不校验——CJK slug 离线不可复现） | code-quality-check workflow `docs-links` job |
| `check_import_layers.py` | 导入分层禁区 + 懒导入总数棘轮（基线 `baselines/import_layers_baseline.json`） | code-quality-check workflow `Check import layers` 步骤 |
| `check_bare_params.py` | 裸数字行为参数棘轮（基线 `baselines/check_bare_params_baseline.json`） | code-quality-check workflow `Check bare numeric params` 步骤 |
| `check_silent_except.py` | 静默吞异常总数棘轮（基线 `baselines/check_silent_except_baseline.json`） | code-quality-check workflow `Check silent except ratchet` 步骤 |

### 棘轮基线

三个棘轮闸门共用同一机制：存量数量记入 `baselines/*.json`，**只紧不松**——
新增即红，消化存量后用 `--update-baseline` 下调。原则：重构应让基线单调下降。

## 发布 / 文档管线（CI 自动执行，勿本地运行）

| 脚本 | 用途 | 调用方 |
|------|------|--------|
| `release_check.py` | 发布三面版本一致性校验（pyproject == CHANGELOG == tag） | pypi-publish / auto-tag-release workflow 首步 |
| `translate-docs.py` | AI 分块增量翻译（缓存续传 + 泄露防线） | auto-update-docs workflow |
| `check-translation.py` | 译文质量检查（缺失/截断/乱码/围栏/泄露），`--fix` 删问题缓存 | auto-update-docs workflow（翻译后自动 `--fix`） |
| `generate-ai-prompts.py` | 由 docs 生成 AI 提示词物料（ai-support/prompts/） | auto-update-docs / auto-tag-release workflow |
| `generate-api-docs.py` | 由源码 docstring 生成 api-reference/auto_api/ | auto-update-docs workflow |
| `generate-docs-index.py` | 生成 docs/_meta 索引（5 语言映射 + 搜索索引） | auto-update-docs workflow |

> 以上生成/翻译产物由 CI 以 **workflow artifact** 形式上传（保留 90 天），
> **不再提交进仓库**——仓库内现存产物为历史快照。本地不要运行生成器
> （AGENTS.md 规则 17）。`_common.py` 为上述脚本的公共设施（Logger / 围栏计数 /
> LEAK 正则 / IGNORE_DIRS），改泄露特征或围栏语义只改这一处。
> 翻译缓存 `.github/.translate_cache/` 同样不入库：跨运行由 `actions/cache`
> 持久化（workflow 内含坏缓存预清理 `check-translation.py --fix`）。

## 本地工具（手动按需）

| 脚本 | 用途 | 备注 |
|------|------|------|
| `check_i18n_locales.py` / `check_docs_links.py` / `release_check.py` | CI 门禁的本地等价命令，推送前建议先跑 | 纯标准库，无需装依赖 |
| `translate-docs.py` 等管线脚本 | 调试翻译管线时使用 | 需 API key 配置 |
| `generate-type-stubs.py` | .pyi 存根生成 | **已暂停使用**（生成器有缺陷，发布管线已停用），勿提交生成的 .pyi |

## 本轮新增（2026-10 架构重写配套）

| 脚本 | 用途 |
|------|------|
| `check_import_layers.py` | 分层禁区（Core 顶层禁导根包/loaders、runtime/loaders 禁导 CLI）+ 懒导入棘轮 |
| `check_bare_params.py` | 行为参数（超时/重试/冷却）必须进 `Core/constants.py` / `CLI/constants.py` |
| `check_silent_except.py` | 静默吞异常总量不回潮（分级处置规则见 `docs/zh-CN/styleguide/engineering.md`） |

## 已删除

- `invalidate_fence_broken_cache.py`（围栏损坏缓存清理）——功能被 `check-translation.py --fix`
  完全覆盖，且全仓无引用（2026-09 移除）。
- `generate-skills.py`（Agent Skills 自动构建，2026-10 起草后按需搁置）——如恢复实现，
  注意 kernel 同款约束：产物目录不提交、以 artifact 形式交付。
