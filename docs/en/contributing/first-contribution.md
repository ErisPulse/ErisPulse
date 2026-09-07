# First Contribution in Practice

> It's normal to feel uncertain when submitting your first PR. This tutorial breaks the entire process into several small steps—just follow along. If you encounter any issues, feel free to ask in Issues or Discussions. No one will say anything about your questions being "too basic." What matters most is that you're moving forward.

This article uses the example of "adding an i18n translation key" because it involves the smallest change and is the easiest to complete successfully. However, the same process applies to other types of contributions as well.

## Prerequisites

Before you begin, you need to prepare:

- A GitHub account
- [uv](https://docs.astral.sh/uv/) installed locally (ErisPulse's package manager)
- Python 3.10+

## 1. Fork and Clone the Repository

Go to the [ErisPulse repository](https://github.com/ErisPulse/ErisPulse), click **Fork** in the top-right corner to copy it to your account, and then clone it locally (replace "your-username" with your actual username):

```bash
git clone -b Develop/v2 https://github.com/your-username/ErisPulse.git
cd ErisPulse
```

Add the upstream remote to easily sync updates from the main repository in the future:

```bash
git remote add upstream https://github.com/ErisPulse/ErisPulse.git
```

## 2. Install Development Environment

```bash
uv sync                       # Install dependencies and create .venv
```

Verify that the environment is working correctly:

```bash
uv run pytest -m unit -q      # All tests should pass
```

## 3. Create a Feature Branch

Always branch off from `Develop/v2`:

```bash
git checkout Develop/v2
git pull upstream Develop/v2   # First, sync the latest code
git checkout -b docs/add-hello-translation
```

The branch name can be arbitrary as long as it reflects what you're working on.

## 4. Make Changes

To add a new translation key as an example, suppose you need to add the phrase `mymodule.hello`.

There is only one rule: **When adding a new translation key, you must add it in all five languages (zh-CN / en / zh-TW / ja / ru)**, otherwise users of other languages will see missing content.

Open the five files under `src/ErisPulse/Core/i18n/locales/` and add one line to each:

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

> If this change involves new public methods, remember to add documentation comments. See [Documentation Comment Guidelines](../styleguide/docstring.md) for details.

## 5. Local Validation

```bash
uv run ruff check .            # Code style check
uv run basedpyright src/ErisPulse   # Type checking (only needed if you modified the source code) - you might encounter hundreds of warnings (just ignore them... hehe.. hehehe)
uv run pytest -m unit -q       # Run tests
```

Passing all three checks is sufficient. The `reportAny` / `Unknown*` warnings in type checking are due to "types still being gradually improved" and won't block merging.

> If you modify core modules (Bases / runtime / config / loaders), it's recommended to add corresponding test cases for easier future maintenance.

## 6. Update CHANGELOG

Open `CHANGELOG.md`, find the topmost version that is still under development, and add a new entry under the appropriate category:

```markdown
### Enhancements

- Added `mymodule.hello` translation key to `Core/i18n/locales` (zh-CN / en / zh-TW / ja / ru)
```

## 7. Commit and Push

```bash
git add .
git commit -m "i18n: add mymodule.hello translation"
git push origin docs/add-hello-translation
```

## 8. Submit a Pull Request

After pushing, GitHub will prompt you with **Compare & pull request**. Click on it:

1. Confirm the target branch is **`Develop/v2`** (don't select `main`)
2. Check the type of changes and briefly describe what you modified
3. Submit it and wait for the maintainer's review.

It's normal to receive review comments—they don't mean you did something wrong. Just make the suggested changes and push again. Once approved, your changes will be officially merged into `Develop/v2`, and will be available in the next release.

## Contributing Modules or Adapters

Modules and adapters are small packages with a complete structure, and it's easiest to start with a scaffolding tool:

```bash
epsdk create    # Choose module or adapter
```

After generation, just follow these documents:

- [Getting Started with Module Development](../developer-guide/modules/getting-started.md)
- [Getting Started with Adapter Development](../developer-guide/adapters/getting-started.md)
- [Publishing to PyPI and the Module Store](../developer-guide/publishing.md)

> It is recommended to announce your plan using the "New Adapter or Module" template in [Issues](https://github.com/ErisPulse/ErisPulse/issues) before development. Maintainers can help you align with standards and avoid common pitfalls.

Modules and adapters are generally separate repositories and do not need to be included in the main repository. `examples/example-module/` and `examples/example-adapter/` are templates for your reference.

---

## Possible Issues

**How long will it take for someone to review my PR?**  
It usually takes a few days. Maintainers will leave review comments, and you can make adjustments as needed and push again.

**The code check failed?**  
First, try `uv run ruff check . --fix`, which can automatically fix most issues.

**There is a conflict with the main repository?**  
Use `git pull upstream Develop/v2`, resolve the conflicts, and then push again.

**Can I directly submit to `main`?**  
No, all changes must go through `Develop/v2`, and then maintainers will release them to `main` collectively.