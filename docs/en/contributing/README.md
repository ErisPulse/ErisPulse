# Contributing to ErisPulse

> **For those contributing for the first time**
> Open-source projects are never sustained solely by the "big moves" of one or two core developers. More often, it's the accumulation of countless small changes — a typo fix, a translation, a minor bug fix — that pushes ErisPulse forward. So, don't measure whether your contribution is "significant enough." As long as you're willing to submit a PR, you are already part of this journey.

## Ways You Can Contribute

Contributing isn't just about writing core code. Here are several ways you can help make ErisPulse better:

- **Improve Documentation** — Correct typos, clarify confusing descriptions, and add notes about pitfalls you've encountered. This has the lowest barrier to entry and you can start anytime.
- **Supplement Translations** — The framework supports 5 languages (zh-CN / en / zh-TW / ja / ru). If you find any missing or inaccurate translations, feel free to contribute.
- **Fix Bugs** — Pick a familiar issue from [Issues](https://github.com/ErisPulse/ErisPulse/issues), reproduce it, and fix it.
- **Write Examples** — Organize your usage experience into example code for others to reference.
- **Develop Modules / Adapters** — Add support for new platforms or capabilities to the framework. This is more challenging but also more rewarding.

> If you're unsure where to start, just say so in [Discussions](https://github.com/ErisPulse/ErisPulse/discussions), and maintainers will help you find a suitable direction.

## First Pull Request

If you have not submitted a PR before, it is recommended to read [First Contribution Practice](first-contribution.md). It covers the complete workflow from forking the repository to merging the PR. If you encounter any issues, you can raise them in Issues or Discussions.

## Development Environment

For the complete development guidelines, see the root directory [CONTRIBUTING.md](../../../CONTRIBUTING.md). To get started quickly:

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
uv sync                       # Set up the development environment
uv run pytest -m unit         # Run unit tests
uv run ruff check .           # Code linting
```

## Pull Request Process

In simple terms, the process is: fork the repository → create a branch based on `Develop/v2` → run tests after making changes → submit a PR to `Develop/v2`.

A few important points to note:

- Submit your PR to the **`Develop/v2`** branch, do not directly modify `main` or `Pre-Release/v2`
- Before submitting, ensure that `pytest` / `ruff` / `basedpyright` all pass (warnings such as `reportAny` / `Unknown*` in type checking are considered "types are still being refined" and will not block merging)
- If you modify a feature, make a note in `CHANGELOG.md`
- If you add methods to the public API, remember to add documentation comments (the guidelines are [here](../styleguide/docstring.md))

## Contributing Modules or Adapters

If you plan to create a new module or adapter, it is recommended to first briefly mention your idea in the [Issues](https://github.com/ErisPulse/ErisPulse/issues) section using the "New Adapter or Module" template. You don't need to write in great detail—just state your intention. Maintainers will help you clarify your ideas and align with the development standards, making the process smoother.

You can use the scaffolding tool to get started quickly:

```bash
epsdk create    # Choose module or adapter to generate a complete project structure
```

Then refer to [Getting Started with Module Development](../developer-guide/modules/getting-started.md) or [Getting Started with Adapter Development](../developer-guide/adapters/getting-started.md). After completion, you can also [publish to PyPI and the module store](../developer-guide/publishing.md).

> Modules and adapters are typically separate repositories and do not need to be merged into the main repository. Example projects under `examples/` can serve as references.

## Get Help

- [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) — Report issues, request features
- [GitHub Discussions](https://github.com/ErisPulse/ErisPulse/discussions) — Discuss ideas, ask questions
- Email: `erisdev@88.com`