# `ErisPulse.CLI.hints` 模块

---

## 模块概述


ErisPulse CLI 友好提示引擎

CLI 完全独立于框架本体（包括 ``runtime.hints``）。本模块提供 CLI 专用的
模糊匹配 / 拼写建议能力，避免 CLI 反向依赖框架运行时。

> **提示**
> 1. best_match_with_prefix: 用于"未知命令 → 你是不是想用 xxx"场景，
> 对前缀匹配（如 ``ins`` → ``install``）给予加成。
> 2. 其余函数与框架 runtime.hints 行为一致，便于跨模块复用思路。

---

## 函数列表


### `suggest_similar(name: str, candidates: Sequence[str])`

找出与给定名称最相似的候选词

使用 difflib 进行模糊匹配，不区分大小写比较、返回原始大小写。

- **name** (`用户输入的（可能有误的）名称`): - **candidates**: 候选词列表
- **max_suggestions** (`最多返回的建议数量`): - **cutoff**: 相似度阈值 (0.0 ~ 1.0)，低于此值的候选会被过滤
**返回值**: 按相似度从高到低排序的建议列表（保留原始大小写）

---


### `best_match(name: str, candidates: Sequence[str])`

返回单个最佳匹配建议

- **name** (`用户输入的名称`): - **candidates**: 候选词列表
- **cutoff** (`相似度阈值（默认`): 0.6，确保只返回高置信度匹配）
**返回值** (`最佳匹配的候选词，无匹配时返回`): None

---


### `best_match_with_prefix(name: str, candidates: Sequence[str])`

带前缀加成的模糊匹配

当输入是候选词的前缀时（如 ins -> install），给予更高的相似度分数。
专用于 CLI 子命令拼写纠错场景。

- **name** (`用户输入的名称`): - **candidates**: 候选词列表
- **cutoff** (`基础相似度阈值`): - **prefix_bonus**: 当输入是候选前缀时使用的固定高分（应大于 cutoff）
**返回值** (`最佳匹配的候选词，无匹配时返回`): None

---


### `suggest_for_exception(exc: BaseException)`

为 CLI 命令执行中的异常生成场景化提示

根据 Python 异常类型返回对应的 i18n key，由调用方翻译为最终提示。
仅覆盖 CLI 场景下高频出现的异常类型，与框架 runtime.hints 的职责区分。

- **exc** (`捕获的异常实例`): **返回值** (`i18n`): key 字符串，不匹配时返回 None

---

