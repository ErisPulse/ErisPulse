# 首次贡献实战

> 第一次提 PR 难免会有些不确定，这很正常。这篇教程把整个过程拆成了几个小步骤，跟着走就行。中间遇到任何问题都可以在 Issue 或 Discussions 里问——没有人会因为你的问题「太基础」而说什么，大家更在意的是你在往前走。

本文用「补一个 i18n 翻译键」当例子，因为它改动最小、最容易跑通。不过同样的流程，对其他类型的贡献也适用。

## 准备工作

开始前，你需要准备：

- 一个 GitHub 账户
- 本地装好 [uv](https://docs.astral.sh/uv/)（ErisPulse 的包管理器）
- Python 3.10+

## 1. Fork 并克隆仓库

前往 [ErisPulse 仓库](https://github.com/ErisPulse/ErisPulse)，点击右上角的 **Fork** 将其复制到你的账户，然后克隆到本地（将「你的用户名」替换为实际用户名）：

```bash
git clone -b Develop/v2 https://github.com/你的用户名/ErisPulse.git
cd ErisPulse
```

添加上游地址，便于日后同步主仓库的更新：

```bash
git remote add upstream https://github.com/ErisPulse/ErisPulse.git
```

## 2. 安装开发环境

```bash
uv sync                       # 安装依赖并创建 .venv
```

验证环境是否正常：

```bash
uv run pytest -m unit -q      # 测试应全部通过
```

## 3. 创建功能分支

始终从 `Develop/v2` 切分支：

```bash
git checkout Develop/v2
git pull upstream Develop/v2   # 先同步最新代码
git checkout -b docs/add-hello-translation
```

分支名随意，能看出来你要做什么就行。

## 4. 进行修改

以补一个翻译键为例，假设要新增一句 `mymodule.hello`。

规则只有一条：**新增翻译键，5 种语言（zh-CN / en / zh-TW / ja / ru）要一起补**，不然其他语言的用户会看到缺失。

打开 `src/ErisPulse/Core/i18n/locales/` 下的 5 个文件，分别添加一行：

```python
# zh_cn.py
"mymodule.hello": "你好",
# en.py
"mymodule.hello": "Hello",
# zh_tw.py
"mymodule.hello": "你好",
# ja.py
"mymodule.hello": "こんにちは",
# ru.py
"mymodule.hello": "Привет",
```

> 若这次改动涉及新的公共方法，记得给它补上文档注释，详见[文档注释规范](../styleguide/docstring.md)。

## 5. 本地验证

```bash
uv run ruff check .            # 代码风格检查
uv run basedpyright src/ErisPulse   # 类型检查（改了源码才需要） - 你可能遇到几百个warning（不用在意忽略就行...嘻..嘻嘻）
uv run pytest -m unit -q       # 跑测试
```

三条都过就行。类型检查里那些 `reportAny` / `Unknown*` 警告属于「类型还在逐步完善」，不会卡住合并。

> 如果动了核心模块（Bases / runtime / config / loaders），建议顺手补个对应的测试用例，方便后续维护。

## 6. 更新 CHANGELOG

打开 `CHANGELOG.md`，找到最上面那个还在开发的版本，在合适的分类下加一条记录：

```markdown
### 优化

- `Core/i18n/locales` 补充 `mymodule.hello` 翻译键（zh-CN / en / zh-TW / ja / ru）
```

## 7. 提交并推送

```bash
git add .
git commit -m "i18n: add mymodule.hello translation"
git push origin docs/add-hello-translation
```

## 8. 提交 Pull Request

推送之后，GitHub 会提示 **Compare & pull request**，点进去：

1. 确认目标分支是 **`Develop/v2`**（别选成 `main`）
2. 勾选变更类型，简单写写你改了什么
3. 提交，等维护者审查

审查提点意见很正常，不代表你做得不好——按建议改完再 push 一次就行。通过之后，你的改动就正式进 `Develop/v2`，下个版本就能用上。

---

## 贡献模块或适配器

模块和适配器是有完整结构的小包，用脚手架工具起步最省事：

```bash
epsdk create    # 选择 module 或 adapter
```

生成完之后，照着这些文档往下做就行：

- [模块开发入门](../developer-guide/modules/getting-started.md)
- [适配器开发入门](../developer-guide/adapters/getting-started.md)
- [发布到 PyPI 与模块商店](../developer-guide/publishing.md)

> 建议开发前先在 [Issues](https://github.com/ErisPulse/ErisPulse/issues) 里用「新适配器或模块」模板说一声你的计划，维护者能帮你对接标准、避开一些常见的坑。

模块和适配器一般是独立仓库，不必塞进主仓库。`examples/example-module/` 和 `examples/example-adapter/` 是给你参考的样板。

---

## 可能会遇到的问题

**PR 提了多久会有人看？**
一般几天内。维护者会留下 review 意见，你按需调整后再 push 一次就好。

**代码检查报错了？**
先试 `uv run ruff check . --fix`，能自动修掉一大半。

**跟主仓库冲突了？**
`git pull upstream Develop/v2`，解决冲突再 push。

**能直接提到 `main` 吗？**
不行，所有改动都走 `Develop/v2`，再由维护者统一发布到 `main`。
