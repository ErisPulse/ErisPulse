# 为 ErisPulse 贡献

> **写给第一次贡献的你**
> 开源项目从来不是靠一两个核心开发者的「大动作」撑起来的，更多时候，是无数个细微的改动在累积——一处错别字、一句翻译、一个小 Bug 的修复，都在让 ErisPulse 往前走一点。所以不必去衡量自己的贡献「够不够分量」，只要你愿意提交 PR，就已经是这件事的一部分。

## 你可以参与的方式

贡献不只是写核心代码。下面这些事，都在让 ErisPulse 变得更好：

- **完善文档** —— 修正错别字、理顺绕口的描述、补充自己踩过的坑。门槛最低，随时可以开始。
- **补充翻译** —— 框架支持 5 种语言（zh-CN / en / zh-TW / ja / ru），翻译遗漏或不准确的地方，都欢迎来补。
- **修复 Bug** —— 在 [Issues](https://github.com/ErisPulse/ErisPulse/issues) 里挑一个你熟悉的问题，复现并修掉它。
- **编写示例** —— 把你的使用经验整理成示例代码，留给后来的人参考。
- **开发模块 / 适配器** —— 给框架接入新的平台或能力。难度高一些，但也更有成就感。

> 如果不确定从哪入手，可以在 [Discussions](https://github.com/ErisPulse/ErisPulse/discussions) 里说一声，维护者会帮你找到合适的方向。

## 第一次提交 PR

如果你还没有提交过 PR，建议先阅读 [首次贡献实战](first-contribution.md)。其中涵盖了从 fork 仓库到合并 PR 的完整流程，遇到问题可在 Issue 或 Discussions 中提出。

## 开发环境

完整的开发规范见根目录 [CONTRIBUTING.md](../../../CONTRIBUTING.md)。快速上手：

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
uv sync                       # 同步开发环境
uv run pytest -m unit         # 运行单元测试
uv run ruff check .           # 代码检查
```

## 提交流程

简单来说就是：fork 仓库 → 基于 `Develop/v2` 建分支 → 改完跑通测试 → 提 PR 到 `Develop/v2`。

几个要注意的点：

- PR 提到 **`Develop/v2`** 分支，别直接动 `main` 或 `Pre-Release/v2`
- 提交前确认 `pytest` / `ruff` / `basedpyright` 都过得去（类型检查里那些 `reportAny` / `Unknown*` 警告属于「类型还在逐步完善」，不会卡合并）
- 改了功能就在 `CHANGELOG.md` 里留一笔
- 给公共 API 加了方法，记得补文档注释（[规范在这里](../styleguide/docstring.md)）

## 贡献模块或适配器

如果你打算做新的模块或适配器，建议先在 [Issues](https://github.com/ErisPulse/ErisPulse/issues) 里用「新适配器或模块」模板简单说一句你的想法。不用写得很完整，说明意图就行——维护者会帮你理清思路、对接好开发标准，让后面顺一些。

使用脚手架工具可以快速起步：

```bash
epsdk create    # 选择 module 或 adapter，生成完整项目结构
```

随后参考 [模块开发入门](../developer-guide/modules/getting-started.md) 或 [适配器开发入门](../developer-guide/adapters/getting-started.md)，完成后还可[发布到 PyPI 与模块商店](../developer-guide/publishing.md)。

> 模块和适配器通常是独立仓库，不必并入主仓库。`examples/` 下的示例项目可供参考。

## 获取帮助

- [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) —— 报告问题、提出需求
- [GitHub Discussions](https://github.com/ErisPulse/ErisPulse/discussions) —— 讨论思路、提出疑问
- 邮件：`erisdev@88.com`
