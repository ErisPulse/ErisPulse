# scripts/tools 工具集

ErisPulse 仓库的工程工具集：**工程棘轮检查 / 文档生成 / 翻译 / 发布闸门**，已包化为
统一 CLI 入口：

```bash
python -m scripts.tools <组> <名> [参数...]     # 或 uv run python -m scripts.tools ...
```

```
scripts/tools/
├── __main__.py            # 统一入口（组名 + 子命令分发，剩余参数透传）
├── common.py              # 共享设施：REPO_ROOT / Logger / IGNORE_DIRS / count_fences / LEAK_PATTERN
├── checks/                # 「check」组——工程棘轮与质检
│   ├── import_layers.py   #   导入分层禁区 + 懒导入棘轮
│   ├── bare_params.py     #   裸数字行为参数棘轮
│   ├── silent_except.py   #   静默吞异常棘轮
│   ├── i18n_locales.py    #   i18n 五语言键一致性
│   ├── docs_links.py      #   文档死链
│   ├── translation.py     #   翻译产物质检
│   └── release_check.py   #   发布闸门（版本号 / CHANGELOG 核对）
├── generators/            # 「gen」组——文档生成器
│   ├── spec.py            #   ★ 共享规格源：提示词包 + 技能库的文档清单唯一真相
│   ├── ai_prompts.py      #   AI 提示词包（docs/*/ai-support/prompts）
│   ├── skills.py          #   Agent Skills（docs/*/ai-support/skills）
│   ├── api_docs.py        #   API 参考（源码 docstring → docs/*/api-reference/auto_api）
│   ├── docs_index.py      #   文档索引（meta / 导航）
│   └── type_stubs.py      #   类型存根（SendDSL 等 IDE 补全）
├── translate.py           # 「translate」组——文档翻译器（zh-CN → 各语言）
├── baselines/             # 棘轮基线 JSON（只紧不松；--update-baseline 下调）
└── translate-config.json  # 翻译器配置（服务商 / 语言 / 预算）
```

## check 组（工程棘轮，CI 硬门禁）

| 子命令 | 用途 | 调用方 |
|--------|------|--------|
| `check i18n-locales` | i18n 五语言键集合一致性（自动发现 Core / CLI 两套 locales） | code-quality-check `i18n-consistency` job |
| `check docs-links` | docs/zh-CN 内部相对链接死链检查（自动排除生成目录） | code-quality-check `docs-links` job |
| `check import-layers` | 导入分层禁区 + 懒导入总数棘轮（基线 `baselines/import_layers_baseline.json`） | code-quality-check `Check import layers` 步骤 |
| `check bare-params` | 裸数字行为参数棘轮（基线 `baselines/check_bare_params_baseline.json`） | code-quality-check `Check bare numeric params` 步骤 |
| `check silent-except` | 静默吞异常总数棘轮（基线 `baselines/check_silent_except_baseline.json`） | code-quality-check `Check silent except ratchet` 步骤 |
| `check translation` | 翻译产物质检（提示词残留 / 围栏 / 长度比；`--fix` 剥离） | auto-update-docs 翻译前置与后置 |
| `check release-check` | 发布闸门：pyproject 版本 / CHANGELOG 条目 / tag 一致性（`--tag` 校验指定 tag） | auto-tag-release、pypi-publish |

### 棘轮基线

三个棘轮闸门共用同一机制：存量数量记入 `baselines/*.json`，**只紧不松**——
新增即红，消化存量后用 `--update-baseline` 下调。原则：重构应让基线单调下降。

## gen 组 / translate（CI 文档管线，勿本地运行产物入库）

- `gen api-docs` / `gen ai-prompts` / `gen docs-index` / `gen skills` 由 auto-update-docs
  workflow 调用，产物以 docs-generated 分支 + artifact 发布（不提交进开发分支，
  见 AGENTS.md 规则 17）
- `gen type-stubs` 由 pypi-publish 预留（当前注释态）
- `translate` 由 auto-update-docs 调用（时间预算分轮续译）；**含 stale 同步**：
  源文档删除后自动清理各目标语言的残留译文与翻译缓存（此前为规则 16 的人工步骤）

**增删文档清单**：只改 `generators/spec.py`——`PROMPT_SPECS`（提示词包）与
`SKILL_SPECS`（技能库）两份规格同源集中于此，两个渲染器（`ai_prompts` /
`skills`）只负责各自交付格式。

## 约定

- 各模块导出 `main(argv)`，argparse 以 `parse_args(argv)` 解析；直接运行模块文件
  （`python scripts/tools/checks/bare_params.py`）同样可用
- 共享设施一律 `from ..common import ...`（REPO_ROOT / Logger / IGNORE_DIRS /
  count_fences / LEAK_PATTERN）；禁止再造 sys.path hack 或复制这些实现
- 新增工具请同步：本 README、`checks/` 或 `generators/` 的注册表（`__init__.py`）、
  `__main__.py` 的 USAGE 文案
