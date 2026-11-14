---
name: erispulse-dev
description: ErisPulse 框架与官方周边项目的开发规范。写 ErisPulse 核心、适配器、模块、Dashboard 等官方项目代码时使用——覆盖注释与代码纪律、提交与发版、文档 i18n、质量门禁（ruff/basedpyright/pytest）与透感视觉风格。
---

# ErisPulse 开发规范

为 ErisPulse 官方仓库与周边项目（框架核心 / 适配器 / 模块 / Dashboard / 工具链）贡献代码时遵循本规范。规范凝缩自根目录 `AGENTS.md`（32 条完整规则，冲突时以它为准）与 `docs/zh-CN/styleguide/`。

## 硬规则速查（最高频违反项）

1. **注释只写客观事实**——禁止设计缘由/背景故事/改动动机，禁止"我们/本脚本"式叙述；公共方法必须有 `:param:/:return:/:raises:` docstring
2. **提交主题 = 类型前缀 + 干净中文概述**——禁止括号罗列（`fix: xxx（哨兵返回 Any）`是错的），细节归 CHANGELOG 不进主题
3. **提交前三门禁全绿**：`uv run pytest` + `uv run ruff check .` + `uv run basedpyright src/ErisPulse`（0 errors）
4. **公共 API 变更三同步**：`__all__` / 聚合导出文件 / `examples/` 示例项目
5. **文档只改 `docs/zh-CN`**（唯一维护源，其余语言 CI 生成）；`ai-support/prompts` 与 `api-reference/auto_api` 是 CI 生成物勿手改
6. **新翻译键同步全部五语言**：zh-CN / zh-TW / en / ja / ru
7. **用户可感知变更必须更新 CHANGELOG 当前 dev 条目**（净差异、一行一条、不记过程）
8. **行为参数集中 `Core/constants.py`**，实现文件禁止裸数字超时
9. **根目录不允许自由函数**；新异常挂 `ErisPulseError` 层级并聚合导出
10. **推送前 stash 保护未提交改动**；历史重写用 `reset --hard` + cherry-pick + `push --force-with-lease`

## 分主题详情（按需读取）

| 主题 | 文件 | 何时读 |
|------|------|--------|
| 注释/docstring 格式、异常留痕分级、日志纪律、API 契约、清理纪律、配置系统要点 | [references/code-style.md](references/code-style.md) | 写任何框架/适配器/模块代码前 |
| 仓库版图、分支模型、提交/CHANGELOG/发版流程 | [references/git-and-release.md](references/git-and-release.md) | 提交、PR、发版前 |
| 文档单一源、CI 生成物、行文规则、i18n、模板同步 | [references/docs-and-i18n.md](references/docs-and-i18n.md) | 改文档、加翻译键、改模板 |
| 三门禁细节、ruff ignore 及原因、basedpyright 提级、测试纪律 | [references/quality-gates.md](references/quality-gates.md) | 跑门禁、写测试、修类型 |
| 透感视觉风格（glass.css + index.html 活标本） | [style/README.md](style/README.md) | 写 Dashboard / Web 界面时 |

## 生态组件额外约定

- **适配器**：继承 `BaseAdapter`，账户字段用标准名 `account_id`；请求事件审批重写 `_do_accept`/`_do_reject`（勿动公开入口 `accept()`/`reject()`）；失败语义遵循规则 26（连接级不可达冷却快速失败，操作失败抛 `StorageOperationError`）
- **模块**：继承 `BaseModule`，配置用嵌套 `ConfigClass` 声明，推荐根导入 `from ErisPulse import ...`
- **Dashboard / Web 界面**：用 `style/glass.css` + `index.html` 活标本起步——透感 =
  根元素 `bg-image` + `data-bg-level`（soft/standard/strong）+ 必须提供背景层
  （玻璃没有东西可模糊就退化）；模糊统一 blur(14px) saturate(1.15)，浮层多一档；
  组件只用既有 class 词汇（.card/.badge-ok/.badge-er/.btn-accent），不发明新设计
  语言；布局给背景留可见空间。唯一真相源是 ErisPulse-Dashboard 仓库的 css 全链。
  详见 [style/README.md](style/README.md)
