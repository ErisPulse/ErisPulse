# ErisPulse 智能体开发事项

你必须遵守以下规则：

## 代码修改
- 1. 修改源代码时必须确定供应链上下游正常
- 2. 必须参照 docstring 文档的注释风格来为ErisPulse方法添加方法注释/模块注释；工程健壮性纪律（异常留痕分级、日志分级、行为参数集中、API 契约等）见 `docs/zh-CN/styleguide/engineering.md`
- 3. 必须遵守 CONTRIBUTING.md 的内容
- 4. 新增或修改公共 API（导出符号、类属性、方法签名）时：
  - 同步更新对应模块的 `__all__` 列表
  - 同步更新 `src/ErisPulse/runtime/__init__.py` 等聚合导出文件
  - 同步更新示例项目（`examples/example-adapter/`、`examples/example-module/`）
- 5. 修改公共行为（配置热更新、事件路由、生命周期等）后，检查是否影响已发布的下游组件（适配器/模块/配置面板），必要时同步更新或记录兼容性说明
- 6. 遇到问题必须定位根因、从架构层面修复，而非不断叠加补丁绕过。优先根本解决，禁止补丁式更新。

## 测试与检查
- 7. 修改完毕后必须通过 `uv run pytest`、`uv run ruff check .`、`uv run basedpyright src/ErisPulse` 三项检查（与 CI 门禁一致；pytest 需先 `uv sync --extra test`）
- 8. 涉及核心模块（Bases、runtime、config、loaders）的修改，必须补充或更新对应的 pytest 用例
- 9. 修改 `src/ErisPulse/CLI/commands/create.py` 中的模板后，须运行 `.format()` 并 `compile()` 验证生成代码合法

## CI/CD
- 10. 新增功能时检查是否需要修改 `.github/workflows` 配置
- 11. 新增 Python `import` 依赖时确认无循环依赖风险

## 国际化（i18n）
- 12. 新增翻译键时，必须同步更新所有语言文件（zh-CN / zh-TW / en / ja / ru）
- 13. 翻译键命名使用点号分隔：`<模块>.<类别>.<描述>`（如 `core.sdk.init.starting`）
- 14. 配置字段的 `description` 使用 i18n 字典格式：`{"i18n": "key.path", "default": "兜底文本"}`
- 15. 声明了 i18n key 的地方（如配置 `description`），必须确保对应翻译已注册；示例项目默认使用纯文本，不使用未注册的 i18n key

## 文档
- 16. 只需要修改 `docs/zh-CN` 下的相关文档。**zh-CN 是唯一维护源**；其余语言由 CI 翻译流程生成并**自动提交回开发分支**（克隆/pull 即得最新多语言文档；另有 `docs-generated` 分支 + workflow artifact 作查验副本）。源文档删除后各语言残留由翻译器 stale 同步自动清理（随 CI 提交生效），本地无需手动清理
  - ⚠️ **删除/移动/重命名 `docs/zh-CN` 文档时**：CI 翻译器的 stale 同步会自动清理各目标语言的残留译文与缓存并随产物提交生效，本地无需手动清理；仅需检查 `docs/zh-CN` 内部的死链接
- 17. 以下文档路径由 CI 生成、自动提交回开发分支（勿手改，改动会被下轮 CI 覆盖），也**不要在本地运行生成脚本**（源码 docstring 与 `docs/zh-CN` 是唯一内容来源）：
  - 不要读取或修改任何语言 `ai-support/prompts` 下的文档（自动生成的AI提示词；生成脚本 `scripts/tools/generators/ai_prompts.py`（统一入口 `python -m scripts.tools gen ai-prompts`））
  - 不要读取或修改任何语言 `api-reference/auto_api` 下的文档（自动生成的API文档；生成脚本 `scripts/tools/generators/api_docs.py`（统一入口 `python -m scripts.tools gen api-docs`））
- 18. 用户可感知的变更必须更新 `CHANGELOG.md` **当前开发版本**条目，并遵循其头部「写作规范」：
  - 同一主题的多次修改应**更新既有条目为最终形态**，而非追加新条目（禁止"后期迭代 / 修正 / 不再…"式过程记录）
  - 本版本内引入又在本版本内修复 / 回退的内容不单独记录（并入特性条目或不记）
  - 纯测试补充、内部微调等无用户感知的变更可不记
  - 严重 bug 修复需同步更新 `docs/zh-CN/bug-tracker.md`（影响微小时可不写）
  - **摘要从简**：`**版本摘要**` 控制在 2–3 句话，只说清"本版本主题 + 最重磅的 1–3 项变更"，不逐条罗列子功能、不粘贴 API / 配置 / 参数细节（细节归入下方变更分类）；`**升级建议**` / `**注意事项**` 只给结论与行动项，不复述正文
- 19. 如果你有新增/重构文档，请务必进行以下两项任务：
  - 更新根文档README即相关总结性文档的内容，添加/修改新的文档的相关连接 
  - 更新文档相关生成脚本是否需要同步（清单集中在 `scripts/tools/generators/spec.py`，改清单只动它）：`python -m scripts.tools gen ai-prompts` / `gen docs-index` / `gen skills`
  - 行文与对外页面写作遵循 `docs/zh-CN/styleguide/docs-writing.md`（注意：`styleguide/` 不进入 AI 提示词生成包）
  
## 模板与示例同步
- 20. 修改适配器/模块的基类或配置规范时，必须同步更新 `src/ErisPulse/CLI/commands/create.py` 中的 `_ADAPTER_CORE` 和 `_MODULE_CORE` 模板
- 21. 修改适配器/模块的公共 API 时，同步更新 `examples/` 下的示例项目
- 22. `examples/` 示例项目应体现推荐写法（如配置类用嵌套类 `ConfigClass` 声明），作为开发者参考标准

## 配置系统修改同步清单

- 23. 修改配置系统时按改动范围逐项同步：
  - **框架默认配置项**：唯一真相源是 `runtime/frame_config.py` 的 `DEFAULT_ERISPULSE_CONFIG`（默认值仅内存合并返回、不落盘；`ErisPulse.<path>` → `ERISPULSE_<PATH>` 环境变量覆盖自动生效，无需额外代码）
  - **`config.full.example`**：生成器唯一源在 `runtime/example_config.py`；静态段 `cfg.*` 文案键在 `CLI/utils/scaffold_text.py`（en 兜底 + zh-CN）；静态段结构变化时递增该文件 `_GEN`，框架启动会自动刷新带标记的用户文件（用户删除首行标记即手动接管）
  - **声明式配置（ConfigClass）行为**：全部消费逻辑在 `Core/Bases/config_schema.py`，五处消费点语义必须一致（schema / TOML 模板 / 默认值 / dict 填充 / 校验）：下划线前缀字段一律排除、`example` 字段仅进 full.example、嵌套 dataclass 递归；`_schema_meta` 必须声明为 `ClassVar[dict]`
  - **配置写入**：必须走 tomlclass 无损编辑路径（`ConfigManager._flush_config` / `setConfigTemplate`，注释/顺序/行尾逐字节保真），禁止引入 `toml.dump`/`tomli_w` 等纯 dict 序列化（会抹掉用户注释与顺序）
  - **配置事件消费者**（`Core/scope.py`、`Core/Event/overrides.py` 等）：遵循"精确失效"——仅本模块相关配置节实际变化时才重建状态；运行时 `persist=False` 写入走覆盖层记录 + 配置重载后重放（#432 模式）
  - **文档同步**：`user-guide/configuration.md`（配置节说明）、相关 advanced 文档（如 `storage-backends.md`）
- 24. 行为参数（重试次数、超时、冷却期、阈值等）**必须定义在 `Core/constants.py`** 并注明使用位置与修改影响，禁止散落在实现文件内部硬编码；实现文件以类属性/局部引用常量导入使用
- 25. 存储后端行为约定：连接失败**不阻塞、不崩溃框架**——建池重试耗尽后进入冷却期，期间存储操作快速失败（操作层吞异常记日志返回 `False/None`），冷却结束自动重连试探；异常类型 `StorageUnreachableError`（已从 `ErisPulse.Core` 导出）；真机验证脚本 `tests/devs/test_storage_backend_verify.py`（sqlite/mysql/postgres 各 12 项，修改存储引擎后必须三后端跑通）
- 26. 框架异常：新增异常必须挂在 `Core/Bases/errors.py` 的 `ErisPulseError` 层级下、从 `ErisPulse.Core` 聚合导出，并同步 `docs/zh-CN/advanced/errors.md`（异常总览树与发生位置表）
- 28. 模块顶部不允许直接定义自由函数：仅在单个类内部使用的能力用私有方法/闭包收进类内；跨类复用的能力才提升为模块级函数（公共 API，需进 `__all__`）或独立工具类

## 提交信息

- 29. 提交信息只说「提交了什么」：一行主题（conventional commits + 中文概述），不写改动细节、动机、影响面——细节归 CHANGELOG；CHANGELOG 同样只记用户可感知的净差异、不记噪声；顺带的无关小修改不写

## 发布流程

- 27. 版本发布（本项目一般不打 rc，dev 浸泡后直接正式版）：
  - `pyproject.toml` 版本号收口（如 `x.y.z-dev.N` → `x.y.z`）
  - CHANGELOG 新增 `[x.y.z]` 正式条目 = **全部 dev 条目的净差异总结**（凝练式：版本摘要 + 升级建议 + 注意事项，细节保留在 dev 条目中作为历史）
  - 合并 `Develop/v2` → `main`（auto-tag 生效）→ 打 tag 触发 `pypi-publish`（stable tag 走正式发布）与 `docker-publish`（production stable 镜像）
  - 生态组件（ErisPulse-Dashboard、核心适配器）需配套发版并验证兼容