# 项目贡献指南

感谢您对 ErisPulse 的关注！ErisPulse 致力于打造一个易用、高效、可扩展的多平台机器人开发框架。每一个贡献，无论是代码、文档、问题报告还是想法建议，都帮助这个项目变得更好。

## 第一次为ErisPulse贡献需要什么

如果您是第一次为 ErisPulse 做贡献，这里有几个适合入手的方向：

### 适合入门的贡献

1. **文档改进**
   - 修正错别字或表达不当之处
   - 补充缺失的示例代码
   - 翻译文档到其他语言

2. **Bug 修复**
   - 在 GitHub Issues 中寻找标记为 "bug" 的问题
   - 选择您熟悉或感兴趣的领域
   - 提交修复方案

3. **完善示例**
   - 优化现有的示例代码
   - 添加新的使用场景示例

### 简化的贡献流程

1. **Fork 本项目到您的 GitHub 账户**
2. **基于 `Develop/v2` 分支创建您的功能分支**
3. **进行修改并提交清晰的提交信息**
4. **提交 Pull Request 到官方仓库的 `Develop/v2` 分支**
5. **填写 PR 模板，等待代码审查**

---

## 分支管理规范

### 分支结构
- **main**: 主分支，存放稳定可发布的代码
- **Develop/v2**: 开发主分支，所有功能分支最终合并至此
- **Pre-Release/v2**: 预发布分支，用于版本发布前的测试

> **历史版本归档**: V1 版本代码已迁移至独立仓库 [ErisPulse/Archive-v1](https://github.com/ErisPulse/Archive-v1)，仅供历史参考。


## 开发环境搭建

### 克隆项目

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
```

### 环境配置

使用 `uv` 同步项目环境：

```bash
uv sync
# 激活虚拟环境: source .venv/bin/activate (macOS/Linux) 或 .venv\Scripts\activate (Windows)
```

提示：ErisPulse 使用 Python 3.13 开发，兼容 Python 3.10+

### 项目结构

```
ErisPulse/
├── src/
│   └── ErisPulse/           # 核心源代码
│       ├── Core/            # 核心模块
│       │   ├── Bases/       # 基础类定义
│       │   ├── Event/       # 事件系统
│       │   └── ...          # 其他核心组件
│       └── __init__.py      # SDK入口点
├── examples/                # 示例代码
├── docs/                   # 文档
├── tests/                  # 测试代码
└── scripts/                # 脚本文件
```

## 注解存根通知
我们有一个用于生成pyi文件的脚本，在仓库中你是看不到pyi文件的
如果你需要使用这些注解，请运行 `python3 scripts/tools/generate-type-stubs.py` , 它将在本地生成pyi文件
提交时，请确保您本地的pyi文件已清除，使用 `python3 scripts/tools/generate-type-stubs.py --clean-only` 完成清理

## 代码注释规范

> 详细注释规范请参考 docs/styleguide/

## 贡献流程

1.  **Fork仓库**
    *   首先fork主仓库到您的个人GitHub账户。
2.  **创建功能分支**
    *   在您**自己Fork的仓库**中，基于官方的 `Develop/v2` 分支创建功能分支。

3.  **开发工作**
    *   在您的功能分支上进行开发。
    *   保持提交信息清晰明确（例如：`feat: 添加用户登录功能`）。
    *   严格遵守docs/styleguide/docstring_spec.md，为所有新增的公开API添加文档注释。
    *   提交前，确保在 `CHANGELOG.md` 中添加了变更描述。
    *   为了减少合并冲突，建议定期从**官方仓库的 `Develop/v2` 分支**拉取（`pull`）更新。

4.  **提交Pull Request (PR)**
    *   开发完成后，在GitHub上向**官方仓库的 `Develop/v2` 分支**发起Pull Request。
    *   请确保PR的**目标仓库**是原始项目库，**目标分支**为 `Develop/v2`。
    *   在PR描述中，请完整填写提供的PR模板，勾选对应选项并添加必要的详情信息。

    **4.1 提交到其他分支（可选）**
    *   如果您需要发布测试版本或进行其他特殊操作，也可以向官方仓库的**其他分支**（如 `Pre-Release/v2`）发起PR。
    *   请在PR标题和描述中**明确说明**提交至此分支的原因和目的。

5.  **代码审查**
    *   维护者将对您的PR进行代码审查。
    *   审查内容包括但不限于：代码逻辑、风格是否符合规范、注释是否完整、特殊标签使用是否正确等。

6.  **合并与发布**
    *   审查通过后，您的代码将被合并到官方的 `Develop/v2` 分支。
    *   之后的官方发布流程为：
        *   `Develop/v2` → `Pre-Release/v2` （进行集成测试）
        *   测试通过后，由维护者发布到 `main` 分支。

## 注意事项

*   **请勿**直接向官方的 `main` 或 `Pre-Release/v2` 分支提交代码或PR，所有功能开发应通过PR至 `Develop/v2` 的方式进入代码库。
*   **例外情况**：如流程第4.1条所述，为特定目的（如发布测试版本）向 `Pre-Release/v2` 等分支提交PR是允许的，但需在PR中充分说明。
*   所有公开API方法必须包含完整注释，请参考docs/styleguide/docstring_spec.md。
*   如有疑问，请联系 `erisdev@88.com` 或 云湖群ID 635409929

感谢您的贡献！
