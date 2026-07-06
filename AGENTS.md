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

## 测试与检查
- 5. 修改完毕后必须进行 pytest 测试，必须进行 python check 检查
- 6. 涉及核心模块（Bases、runtime、config、loaders）的修改，必须补充或更新对应的 pytest 用例
- 7. 修改 `src/ErisPulse/CLI/commands/create.py` 中的模板后，须运行 `.format()` 并 `compile()` 验证生成代码合法

## CI/CD
- 8. 合并前必须确认 GitHub Actions / 流水线通过
- 9. 新增功能时检查是否需要修改 CI/CD 配置
- 10. 新增 Python `import` 依赖时确认无循环依赖风险

## 国际化（i18n）
- 11. 新增翻译键时，必须同步更新所有语言文件（zh-CN / zh-TW / en / ja / ru）
- 12. 翻译键命名使用点号分隔：`<模块>.<类别>.<描述>`（如 `core.sdk.init.starting`）
- 13. 配置字段的 `description` 使用 i18n 字典格式：`{"i18n": "key.path", "default": "兜底文本"}`

## 文档
- 14. 只需要修改 `docs/zh-CN` 下的相关文档，其余文档会自动更新
- 15. 以下文档路径请务必不要读取/修改！
  - 不要读取或修改任何语言 `ai-support/prompts` 下的文档，这是自动生成的AI提示词
  - 不要读取或修改任何语言 `api-reference/auto_api` 下的文档，这是自动生成的API文档

## 模板与示例同步
- 16. 修改适配器/模块的基类或配置规范时，必须同步更新 `src/ErisPulse/CLI/commands/create.py` 中的 `_ADAPTER_CORE` 和 `_MODULE_CORE` 模板
- 17. 修改适配器/模块的公共 API 时，同步更新 `examples/` 下的示例项目

## Dashboard 同步
- 18. ErisPulse-Dashboard 是独立仓库（https://github.com/ErisPulse/ErisPulse-Dashboard），修改适配器/模块的配置 API 或新增后端接口时，需同步查看是否需要对其发起 PR