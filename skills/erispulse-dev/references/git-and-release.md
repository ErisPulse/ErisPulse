# Git 关联与提交发版规范

## 仓库版图

- 本地工作区：`ErisPulse-devs/` 下分 `SDK/`（框架与周边）、`Adapters/`（协议适配器）、`Module/`（模块与 Dashboard）、`App/`（应用壳）
- GitHub 组织 `ErisPulse`：主仓 `ErisPulse/ErisPulse`（SDK）、`ErisPulse-Dashboard`（Web 面板）、各适配器独立仓库、`ErisPulse-ModuleRepo`（模块索引）
- 主仓分支模型：`Develop/v2` 为开发主线（PR 默认目标）→ `Pre-Release/v2`（预发布浸泡）→ `main`（正式，tag 触发 PyPI/Docker 发布）
- dev 流程：推送 Develop/v2 → PR 到 Pre-Release/v2 → 等远程文档翻译 CI 完成并 rebase → 正式版收口时合并 main

## 提交信息（强约束）

- 只说「提交了什么」：一行主题 = conventional commits 类型前缀 + 中文概述，**不写改动细节、动机、影响面**（细节归 CHANGELOG）
- **禁止小括号做介绍性后缀**：主题不挂 `（为了xxx，实现xxx）` 式罗列——类型前缀 + 干净中文概述，要点展开留给正文或 CHANGELOG
- 常用类型：`feat` / `fix` / `docs` / `refactor` / `perf` / `ci` / `chore`

```
# 好
feat: ORM 复合主键、联合唯一与声明能力补全
fix: ORM Field 声明赋值侧类型检查误报

# 坏（细节进主题、括号罗列）
fix: 修复类型检查（哨兵返回 Any + dataclass_transform 双清零）
```

- 顺带的无关小修改不写进提交主题；同一主题的多次提交在推送前可 squash 重写（`reset --hard` + cherry-pick 重放 + `push --force-with-lease`），强推前 stash 保护未提交改动

## CHANGELOG（强约束）

- 用户可感知的变更必须更新 `CHANGELOG.md` 当前开发版本条目，贡献标注 `@Github用户名`
- 记录**发布状态之间的净差异**，不记开发过程：同一主题多次修改更新既有条目为最终形态（禁止"后期迭代/不再…"式过程记录）；版内引入又版内修复的不单列；纯测试/内部微调不记
- 条目一行一条（模块/领域 + 干了什么），不粘贴 API 签名与参数列表；`版本摘要` ≤ 2 句话
- 正式版条目 = 全部 dev 条目的净差异总结（凝练式），dev 条目保留为历史

## 发版流程

1. `pyproject.toml` 版本号收口（`x.y.z-dev.N` → `x.y.z`；本项目一般不打 rc，dev 浸泡后直接正式版）
2. CHANGELOG 新增 `[x.y.z]` 正式条目（dev 净差异总结）
3. 合并 `Develop/v2` → `main`（auto-tag）→ tag 触发 `pypi-publish` 与 `docker-publish`
4. 生态组件（Dashboard、核心适配器）配套发版并验证兼容
