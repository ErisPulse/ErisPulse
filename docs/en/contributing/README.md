# Contributing to ErisPulse

> **For You, the First-Time Contributor**
> Open-source projects are never sustained solely by the "big moves" of one or two core developers. More often, it's countless small changes that accumulate—a typo fix, a translation, a small bug resolved—all of which move ErisPulse forward. So don't measure whether your contribution is "substantial enough." If you're willing to submit a PR, you're already a part of it.

## Ways You Can Contribute

Contributing goes beyond writing core code. The following tasks are all helping ErisPulse become better:

- **Improve Documentation** —— Fix typos, clarify confusing descriptions, and document pitfalls you've encountered. This has the lowest barrier to entry and can be started anytime.
- **Add Translations** —— The framework supports 5 languages (zh-CN / en / zh-TW / ja / ru). If you find missing or inaccurate translations, feel free to contribute.
- **Fix Bugs** —— Pick a familiar issue in [Issues](https://github.com/ErisPulse/ErisPulse/issues), reproduce it, and fix it.
- **Write Examples** —— Organize your usage experiences into example code for others to reference.
- **Develop Modules / Adapters** —— Add support for new platforms or capabilities to the framework. This is more challenging but also more rewarding.

> If you're unsure where to start, simply ask in [Discussions](https://github.com/ErisPulse/ErisPulse/discussions), and maintainers will help you find a suitable direction.

## First PR Submission

If you haven't submitted a PR before, it's recommended to read [First Contribution in Practice](first-contribution.md). It covers the entire workflow from forking the repository to merging the PR. If you encounter any issues, you can raise them in an Issue or Discussions.

## Development Environment

For complete development guidelines, see the root directory [CONTRIBUTING.md](../../../CONTRIBUTING.md). Quick start:

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
uv sync                       # Synchronize the development environment
uv run pytest -m unit         # Run unit tests
uv run ruff check .           # Code checking
```

## Pull Request Process

In short: fork the repository → create a branch based on `Develop/v2` → run tests after changes → submit a PR to `Develop/v2`.

A few points to note:

- Submit PRs to the **`Develop/v2`** branch; don't directly modify `main` or `Pre-Release/v2`.
- Before submitting, ensure `pytest` / `ruff` / `basedpyright` all pass (warnings like `reportAny` / `Unknown*` in type checking are considered "types are still being improved" and won't block merging).
- If you modify functionality, add a note in `CHANGELOG.md`.
- If you add methods to the public API, remember to add documentation comments (the [guidelines are here](../styleguide/docstring.md)).

## Contributing Modules or Adapters

If you plan to create a new module or adapter, it's recommended to briefly describe your idea in [Issues](https://github.com/ErisPulse/ErisPulse/issues) using the "New Adapter or Module" template. You don't need to be very detailed—just explain your intention. Maintainers will help you clarify your thoughts and align with development standards, making the process smoother.

You can use the scaffolding tool to get started quickly:

```bash
epsdk create    # Choose module or adapter to generate a complete project structure
```

Then refer to [Getting Started with Module Development](../developer-guide/modules/getting-started.md) or [Getting Started with Adapter Development](../developer-guide/adapters/getting-started.md). After completion, you can also [publish to PyPI and the module store](../developer-guide/publishing.md).

> Modules and adapters are usually separate repositories and don't need to be merged into the main repository. Example projects in `examples/` can be referenced.

## Get Help

- [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) —— Report issues, propose requirements
- [GitHub Discussions](https://github.com/ErisPulse/ErisPulse/discussions) —— Discuss ideas, ask questions
- Email: `erisdev@88.com`