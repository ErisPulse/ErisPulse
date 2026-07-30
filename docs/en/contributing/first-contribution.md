# First Contribution Walkthrough

> It's normal to feel uncertain the first time you submit a PR. This tutorial breaks the process down into small steps, just follow along. If you encounter any problems, feel free to ask in Issues or Discussions—nobody will mind if your question is "too basic"; people care more that you are making progress.

For this example, we will use "Adding an i18n translation key" because it involves the least change and is easiest to get right. However, the same process applies to other types of contributions.

## Prerequisites

Before starting, you need to prepare:

- A GitHub account
- [uv](https://docs.astral.sh/uv/) installed locally (ErisPulse's package manager)
- Python 3.10+

## 1. Fork and Clone the Repository

Go to the [ErisPulse repository](https://github.com/ErisPulse/ErisPulse), click **Fork** in the top right to copy it to your account, then clone it locally (replace "Your Username" with the actual username):

```bash
git clone -b Develop/v2 https://github.com/你的用户名/ErisPulse.git
cd ErisPulse
```

Add the upstream address for easier future synchronization with the main repository:

```bash
git remote add upstream https://github.com/ErisPulse/ErisPulse.git
```

## 2. Install the Development Environment

```bash
uv sync                       # Install dependencies and create .venv
```

Verify the environment is working:

```bash
uv run pytest -m unit -q      # Tests should all pass
```

## 3. Create a Feature Branch

Always branch off `Develop/v2`:

```bash
git checkout Develop/v2
git pull upstream Develop/v2   # Sync latest code first
git checkout -b docs/add-hello-translation
```

The branch name is arbitrary as long as it's clear what you are doing.

## 4. Make Changes

Taking adding a translation key as an example, suppose you want to add a new one for `mymodule.hello`.

There is only one rule: **When adding a new translation key, you must provide it for all 5 languages (zh-CN / en / zh-TW / ja / ru)**, otherwise users of other languages will see missing text.

Open the 5 files under `src/ErisPulse/Core/i18n/locales/` and add a line to each:

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

> If this change involves new public methods, remember to add a docstring to them. See [Docstring Style Guide](../styleguide/docstring.md) for details.

## 5. Local Verification

```bash
uv run ruff check .            # Code style check
uv run basedpyright src/ErisPulse   # Type checking (only needed if you changed source code) - You might encounter hundreds of warnings (just ignore them...hehe..hehe)
uv run pytest -m unit -q       # Run tests
```

As long as these three pass, you are good to go. The `reportAny` / `Unknown*` warnings in type checking are due to "types still being gradually improved" and won't block a merge.

> If you modify core modules (Bases / runtime / config / loaders), it is recommended to add corresponding test cases to make maintenance easier later.

## 6. Update CHANGELOG

Open `CHANGELOG.md`, find the development version at the top, and add a record under the appropriate category:

```markdown
### Optimization

- `Core/i18n/locales` added `mymodule.hello` translation keys (zh-CN / en / zh-TW / ja / ru)
```

## 7. Commit and Push

```bash
git add .
git commit -m "i18n: add mymodule.hello translation"
git push origin docs/add-hello-translation
```

## 8. Submit a Pull Request

After pushing, GitHub will prompt you to **Compare & pull request**. Click it:

1. Confirm that the target branch is **`Develop/v2`** (don't choose `main`)
2. Check the change type and briefly describe what you changed
3. Submit and wait for the maintainers to review

It is normal to receive review comments; it doesn't mean you did a bad job—just make the suggested changes and push again. Once approved, your changes will officially go into `Develop/v2` and will be available in the next release.

---

## Contributing a Module or Adapter

Modules and adapters are small packages with a complete structure; using a scaffolding tool is the easiest way to start:

```bash
epsdk create    # Choose module or adapter
```

After generating, you can simply follow the documentation:

- [Getting Started with Modules](../developer-guide/modules/getting-started.md)
- [Getting Started with Adapters](../developer-guide/adapters/getting-started.md)
- [Publishing to PyPI and Module Store](../developer-guide/publishing.md)

> It is recommended to mention your plan in [Issues](https://github.com/ErisPulse/ErisPulse/issues) using the "New adapter or module" template before starting development. Maintainers can help you align with standards and avoid some common pitfalls.

Modules and adapters are generally independent repositories and don't need to be stuffed into the main repository. `examples/example-module/` and `examples/example-adapter/` are reference templates for you.

---

## Common Questions

**How long will it take for someone to look at my PR?**
Usually within a few days. The maintainer will leave review comments; you just need to adjust as needed and push again.

**Code checks failing?**
Try `uv run ruff check . --fix` first; it can automatically fix most issues.

**Conflicts with the main repository?**
Run `git pull upstream Develop/v2`, resolve the conflicts, and then push.

**Can I merge directly into `main`?**
No, all changes go through `Develop/v2`, and maintainers will release them to `main` uniformly.