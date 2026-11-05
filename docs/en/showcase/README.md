# Selection Guide

> [!TIP]
> **When to read this**: Read this when you're choosing between several bot frameworks / AI bot platforms and want to know who ErisPulse is—and isn't—suited for. If you're already using ErisPulse, skip this.

We don't believe there is a "best framework"—only a "framework that matches your scenario." This directory uses comparison tables to clarify the design differences between ErisPulse and common alternatives, helping you make a decision—including when you should **not** choose us.

| What you're comparing | Read this | Audience |
|---|---|---|
| ErisPulse vs NoneBot2 | [Comparison: NoneBot2](comparison-nonebot.md) | Developers |
| ErisPulse (+QvQChat) vs AstrBot / LangBot | [Comparison: AstrBot and LangBot](comparison-agent-platforms.md) | Users who want an "AI assistant in group chats" |
| Migrating from AstrBot to ErisPulse | [Migration Guide: From AstrBot to ErisPulse](migrate-from-astrbot.md) | Existing AstrBot users |

## Scenario Quick Reference

- **Want an out-of-the-box AI chatbot without writing code**: AstrBot / LangBot offer a faster getting-started experience; if you value hot reload, the module marketplace, and 16-platform coverage, ErisPulse + [QvQChat](../ecosystem/qvqchat.md) + [Dashboard](../ecosystem/dashboard.md) can reach the same destination, with about half an hour extra for initialization
- **Writing business code with cross-platform reuse**: ErisPulse's OneBot12 unified event model lets a single handler work naturally across platforms, with no need to write adaptation branches for platform differences
- **Building an ecosystem for your own modules/AI**: ErisPulse modules that declare services become AI tools ([QvQChat](../ecosystem/qvqchat.md) discovers them automatically), with the ecosystem natively integrated with agents
- **Heavily reliant on existing NoneBot plugins**: NoneBot2's decade-plus plugin ecosystem is an objective advantage; the migration cost needs to be weighed on your own

## Reading Discipline

The comparison content is compiled from each party's publicly available documentation and may become outdated as versions evolve—**please defer to the official documentation of the respective parties before making any decisions**. If you spot any inaccurate or outdated descriptions, feel free to open an Issue or submit a PR for correction. We do not remove reasonable criticism.