# ErisPulse 智能体开发事项

你必须遵守以下规则：

## 代码修改
- 1. 修改源代码时必须确定供应链上下游正常
- 2. 必须参照 docstring 文档的注释风格来为ErisPulse方法添加方法注释/模块注释
- 3. 必须遵守 CONTRIBUTING.md 的内容
- 4. 新增或修改公共 API（导出符号、类属性、方法签名）时：
  - 同步更新对应模块的 `__all__` 列表
  - 同步更新 `src/ErisPulse/runtime/__init__.py` 等聚合导出文件
  - 同步更新示例项目（`examples/example-adapter/`、`examples/example-module/`）
- 5. 修改公共行为（配置热更新、事件路由、生命周期等）后，检查是否影响已发布的下游组件（适配器/模块/配置面板），必要时同步更新或记录兼容性说明

## 测试与检查
- 6. 修改完毕后必须进行 pytest 测试，必须进行 python check 检查
- 7. 涉及核心模块（Bases、runtime、config、loaders）的修改，必须补充或更新对应的 pytest 用例
- 8. 修改 `src/ErisPulse/CLI/commands/create.py` 中的模板后，须运行 `.format()` 并 `compile()` 验证生成代码合法

## CI/CD
- 9. 新增功能时检查是否需要修改 `.github/workflows` 配置
- 10. 新增 Python `import` 依赖时确认无循环依赖风险

## 国际化（i18n）
- 12. 新增翻译键时，必须同步更新所有语言文件（zh-CN / zh-TW / en / ja / ru）
- 13. 翻译键命名使用点号分隔：`<模块>.<类别>.<描述>`（如 `core.sdk.init.starting`）
- 14. 配置字段的 `description` 使用 i18n 字典格式：`{"i18n": "key.path", "default": "兜底文本"}`
- 15. 声明了 i18n key 的地方（如配置 `description`），必须确保对应翻译已注册；示例项目默认使用纯文本，不使用未注册的 i18n key

## 文档
- 16. 只需要修改 `docs/zh-CN` 下的相关文档，其余语言文档会由 CI/CD 翻译流程自动更新（**内容变更**会自动同步）
  - ⚠️ **删除/移动/重命名文档时，翻译流程不会自动清理其它语言**：`scripts/tools/translate-docs.py` 仅遍历源目录（`docs/zh-CN`），对源文件已不存在的目标文件不做删除，会留下死文件
  - 因此**删除或移动 `docs/zh-CN` 下的文档时，必须手动同步清理**：
    - 删除其它语言目录下的对应文件（`docs/en`、`docs/ja`、`docs/ru`、`docs/zh-TW`）
    - 删除 `.github/.translate_cache/<lang>/` 下对应的 `.cache` 文件
    - 检查各语言 `README.md` / 索引文件中是否有指向旧路径的死链接并修正
  - 同理，**重命名**文档时也要同步迁移其它语言版本与缓存，避免产生孤立文件
- 17. 以下文档路径请务必不要读取/修改！
  - 不要读取或修改任何语言 `ai-support/prompts` 下的文档，这是自动生成的AI提示词
  - 不要读取或修改任何语言 `api-reference/auto_api` 下的文档，这是自动生成的API文档
- 18. 每次修改都必须更新 `CHANGELOG.md`；严重 bug 修复需同步更新 `docs/zh-CN/bug-tracker.md`（影响微小时可不写）
- 19. 如果你有新增/重构文档，请务必进行以下两项任务：
  - 更新根文档README即相关总结性文档的内容，添加/修改新的文档的相关连接 
  - 更新文档相关生成脚本：`scripts/tools/generate-ai-prompts.py`, `scripts/tools/generate-docs-index.py` 是否需要更新
  
## 模板与示例同步
- 20. 修改适配器/模块的基类或配置规范时，必须同步更新 `src/ErisPulse/CLI/commands/create.py` 中的 `_ADAPTER_CORE` 和 `_MODULE_CORE` 模板
- 21. 修改适配器/模块的公共 API 时，同步更新 `examples/` 下的示例项目
- 22. `examples/` 示例项目应体现推荐写法（如配置类用嵌套类 `ConfigClass` 声明），作为开发者参考标准