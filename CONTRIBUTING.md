**English** | [简体中文](#项目贡献指南) | [繁體中文](#專案貢獻指南) | [日本語](#プロジェクト貢献ガイド) | [Русский](#руководство-по-вкладу)

---

# Contribution Guide

Thank you for your interest in ErisPulse! ErisPulse aims to build an easy-to-use, efficient, and extensible multi-platform bot development framework. Every contribution — whether code, documentation, issue reports, or ideas — helps make this project better.

## Getting Started

If you're contributing to ErisPulse for the first time, here are some good starting points:

### Good First Issues

1. **Documentation Improvements**
   - Fix typos or unclear wording
   - Add missing code examples
   - Translate documentation to other languages

2. **i18n & Localization**
   - Fix translation errors in documentation, CLI output, installer scripts, Docker entrypoint, or Dashboard
   - Add missing translations for newly added features
   - Improve translation quality across all supported languages (zh-CN, en, zh-TW, ja, ru)
   - Help localize new components as they are added

3. **Bug Fixes**
   - Look for issues labeled "bug" in GitHub Issues
   - Choose an area you're familiar with or interested in
   - Submit a fix

4. **Example Improvements**
   - Improve existing example code
   - Add new usage scenario examples

### Simplified Contribution Flow

1. **Fork** this project to your GitHub account
2. **Create** a feature branch based on `Develop/v2`
3. **Make** changes with clear commit messages
4. **Submit** a Pull Request to the official `Develop/v2` branch
5. **Fill out** the PR template and wait for review

---

## Branch Management

### Branch Structure
- **main**: Main branch, stable release-ready code
- **Develop/v2**: Development branch, all features merge here first
- **Pre-Release/v2**: Pre-release branch for testing before release

> **Historical Archive**: V1 code has been migrated to [ErisPulse/Archive-v1](https://github.com/ErisPulse/Archive-v1) for reference only.

## Development Setup

### Clone

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
```

### Environment

Use `uv` to sync the project environment:

```bash
uv sync
# Activate venv: source .venv/bin/activate (macOS/Linux) or .venv\Scripts\activate (Windows)
```

> ErisPulse is developed with Python 3.13, compatible with Python 3.10+

### Project Structure

> Simplified structure showing key directories for quick navigation.

```
ErisPulse/
├── src/
│   └── ErisPulse/           # Core source code
│       ├── CLI/             # CLI tools (epsdk)
│       ├── Core/            # Core modules
│       │   ├── Bases/       # Base class definitions
│       │   ├── Event/       # Event system
│       │   └── ...          # Other core components
│       ├── finders/         # Module / adapter discovery
│       ├── loaders/         # Loaders (incl. lazy loading)
│       ├── runtime/         # Runtime
│       ├── sdk.py           # SDK entry
│       └── __init__.py      # Package entry
├── config/                  # Default config
├── docs/                    # Multilingual docs (zh-CN / en / ja / ru / zh-TW)
├── examples/                # Example code
├── tests/                   # Tests (unit / integration / performance / stress)
├── scripts/                 # Utility scripts
├── workers/                 # Background workers
├── pyproject.toml           # Project & dependency config
└── pytest.ini               # Test config
```

## Type Stub Generation

We have a script for generating `.pyi` stub files. You won't see `.pyi` files in the repository. If you need these annotations, run `python3 scripts/tools/generate-type-stubs.py` — it generates `.pyi` files locally. Before committing, clean them up with `python3 scripts/tools/generate-type-stubs.py --clean-only`.

## Testing & Linting

### Run Tests

The project uses `pytest` (config in `pytest.ini`, with coverage, `asyncio-mode=auto`, and test markers). Run in the virtual environment:

```bash
# All tests (with coverage report)
uv run pytest

# Unit / integration tests only
uv run pytest -m unit
uv run pytest -m integration

# Specific path or test case
uv run pytest tests/unit
uv run pytest tests/unit/test_xxx.py::TestClass::test_method
```

Filter by marker with `-m`. Common markers: `unit`, `integration`, `e2e`, `adapter`, `module`, `event`, `lifecycle`, `config`, `storage`, `logger`, `router`.

### Lint & Format

The project uses two checking tools:

1. **[Ruff](https://docs.astral.sh/ruff/)** — code style & lightweight static checks (config in `[tool.ruff]` of `pyproject.toml`)
2. **[Basedpyright](https://docs.basedpyright.com/)** — strict type checking (config in `[tool.basedpyright]` of `pyproject.toml`)

Ensure code passes both checks before committing:

```bash
# Lint & static analysis
uv run ruff check .

# Auto-fix
uv run ruff check . --fix

# Format
uv run ruff format .

# Type check
uv run basedpyright src/ErisPulse
```

> ⚠️ **Type checking rules**: `[tool.basedpyright]` uses `standard` (moderate) mode.
> Real type bugs (return type mismatch, argument type mismatch, optional member access, etc.) are elevated to **error**.
> Most `reportAny/Unknown*` warnings are gradual "incomplete types" — they won't block merging.

## Docstring Standards

> See [docs/en/styleguide/docstring.md](docs/en/styleguide/docstring.md) for detailed guidelines.

## Contribution Process

1. **Fork the repo** to your GitHub account.
2. **Create a feature branch** based on `Develop/v2` in your fork.
3. **Develop**
   - Keep commit messages clear (e.g., `feat: add user login`).
   - Follow [docstring standards](docs/en/styleguide/docstring.md) for all new public APIs.
   - Add changelog entries in `CHANGELOG.md`.
   - Regularly pull updates from `Develop/v2` to minimize conflicts.
4. **Submit a Pull Request** to the official `Develop/v2` branch.
   - Ensure the target repo is the original project and target branch is `Develop/v2`.
   - Fill out the PR template completely.
   - **4.1 Other branches (optional)**: For test releases or special operations, you may PR to other branches (e.g., `Pre-Release/v2`). Clearly state the reason in the PR title and description.
5. **Code Review**: Maintainers will review your PR — logic, style, comments, labels, etc.
6. **Merge & Release**: After approval, your code merges into `Develop/v2`. The release flow:
   - `Develop/v2` → `Pre-Release/v2` (integration testing)
   - After testing, maintainers release to `main`.

## Notes

- **Do not** commit or PR directly to `main` or `Pre-Release/v2`. All features go through PRs to `Develop/v2`.
- **Exception**: As described in step 4.1, PRs to `Pre-Release/v2` for specific purposes are allowed with clear justification.
- All public API methods must have complete docstrings — see [docstring standards](docs/en/styleguide/docstring.md).
- Questions? Contact `erisdev@88.com` or Yunhu group ID 635409929.

Thank you for contributing!

---

# 项目贡献指南

感谢您对 ErisPulse 的关注！ErisPulse 致力于打造一个易用、高效、可扩展的多平台机器人开发框架。每一个贡献，无论是代码、文档、问题报告还是想法建议，都帮助这个项目变得更好。

## 第一次为 ErisPulse 贡献需要什么

如果您是第一次为 ErisPulse 做贡献，这里有几个适合入手的方向：

### 适合入门的贡献

1. **文档改进**
   - 修正错别字或表达不当之处
   - 补充缺失的示例代码
   - 翻译文档到其他语言

2. **国际化与本地化 (i18n)**
   - 修正文档、CLI 输出、安装脚本、Docker entrypoint 或 Dashboard 中的翻译错误
   - 为新增功能补充缺失的翻译
   - 提升所有支持语言（zh-CN、en、zh-TW、ja、ru）的翻译质量
   - 协助本地化新增组件

3. **Bug 修复**
   - 在 GitHub Issues 中寻找标记为 "bug" 的问题
   - 选择您熟悉或感兴趣的领域
   - 提交修复方案

4. **完善示例**
   - 优化现有的示例代码
   - 添加新的使用场景示例

### 简化的贡献流程

1. **Fork** 本项目到您的 GitHub 账户
2. **基于** `Develop/v2` 分支创建您的功能分支
3. **进行修改**并提交清晰的提交信息
4. **提交 Pull Request** 到官方仓库的 `Develop/v2` 分支
5. **填写 PR 模板**，等待代码审查

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

> ErisPulse 使用 Python 3.13 开发，兼容 Python 3.10+

### 项目结构

> 以下为简化结构，仅列出关键目录，便于快速定位代码。

```
ErisPulse/
├── src/
│   └── ErisPulse/           # 核心源代码
│       ├── CLI/             # 命令行工具 (epsdk)
│       ├── Core/            # 核心模块
│       │   ├── Bases/       # 基础类定义
│       │   ├── Event/       # 事件系统
│       │   └── ...          # 其他核心组件
│       ├── finders/         # 模块 / 适配器发现
│       ├── loaders/         # 加载器（含懒加载策略）
│       ├── runtime/         # 运行时
│       ├── sdk.py           # SDK 入口实现
│       └── __init__.py      # 包入口
├── config/                  # 默认配置
├── docs/                    # 多语言文档 (zh-CN / en / ja / ru / zh-TW)
├── examples/                # 示例代码
├── tests/                   # 测试代码 (unit / integration / performance / stress)
├── scripts/                 # 工具脚本
├── workers/                 # 后台 Worker
├── pyproject.toml           # 项目与依赖配置
└── pytest.ini               # 测试配置
```

## 注解存根生成

我们有一个用于生成 `.pyi` 存根文件的脚本，在仓库中您看不到 `.pyi` 文件。如果您需要使用这些注解，请运行 `python3 scripts/tools/generate-type-stubs.py`，它将在本地生成 `.pyi` 文件。提交时，请确保已清理本地 `.pyi` 文件，使用 `python3 scripts/tools/generate-type-stubs.py --clean-only` 完成清理。

## 测试与代码检查

### 运行测试

项目使用 `pytest`，配置见 `pytest.ini`（已开启覆盖率、`asyncio-mode=auto` 及各类测试标记）。在虚拟环境中执行：

```bash
# 运行全部测试（含覆盖率报告）
uv run pytest

# 仅运行单元测试 / 集成测试
uv run pytest -m unit
uv run pytest -m integration

# 运行指定路径或单个用例
uv run pytest tests/unit
uv run pytest tests/unit/test_xxx.py::TestClass::test_method
```

可用 `-m` 按标记筛选，常用标记：`unit`、`integration`、`e2e`、`adapter`、`module`、`event`、`lifecycle`、`config`、`storage`、`logger`、`router`。

### 代码检查与格式化

项目使用两套检查工具：

1. **[Ruff](https://docs.astral.sh/ruff/)** — 代码风格与轻量级静态检查（配置见 `pyproject.toml` 的 `[tool.ruff]`）
2. **[Basedpyright](https://docs.basedpyright.com/)** — 严格的类型检查（配置见 `pyproject.toml` 的 `[tool.basedpyright]`）

提交前请确保代码通过两套检查：

```bash
# 代码检查
uv run ruff check .

# 自动修复可修复的问题
uv run ruff check . --fix

# 代码格式化
uv run ruff format .

# 类型检查
uv run basedpyright src/ErisPulse
```

> ⚠️ **类型检查规则**：`pyproject.toml` 的 `[tool.basedpyright]` 采用 `standard` 中等级模式，
> 已将“真实类型 bug”（如返回值与注解不匹配、参数类型不兼容、对可能 `None` 取属性等）提级为 error。
> 大量的 `reportAny/Unknown*` 警告属于“类型不完整”，不会阻止合并。

## 代码注释规范

> 详细注释规范请参考 [docs/zh-CN/styleguide/docstring.md](docs/zh-CN/styleguide/docstring.md)

## 贡献流程

1. **Fork 仓库**
   - 首先 fork 主仓库到您的个人 GitHub 账户。
2. **创建功能分支**
   - 在您**自己 Fork 的仓库**中，基于官方的 `Develop/v2` 分支创建功能分支。
3. **开发工作**
   - 在您的功能分支上进行开发。
   - 保持提交信息清晰明确（例如：`feat: 添加用户登录功能`）。
   - 严格遵守[文档注释规范](docs/zh-CN/styleguide/docstring.md)，为所有新增的公开 API 添加文档注释。
   - 提交前，确保在 `CHANGELOG.md` 中添加了变更描述。
   - 为了减少合并冲突，建议定期从**官方仓库的 `Develop/v2` 分支**拉取（`pull`）更新。
4. **提交 Pull Request (PR)**
   - 开发完成后，在 GitHub 上向**官方仓库的 `Develop/v2` 分支**发起 Pull Request。
   - 请确保 PR 的**目标仓库**是原始项目库，**目标分支**为 `Develop/v2`。
   - 在 PR 描述中，请完整填写提供的 PR 模板，勾选对应选项并添加必要的详情信息。
   - **4.1 提交到其他分支（可选）**
     - 如果您需要发布测试版本或进行其他特殊操作，也可以向官方仓库的**其他分支**（如 `Pre-Release/v2`）发起 PR。
     - 请在 PR 标题和描述中**明确说明**提交至此分支的原因和目的。
5. **代码审查**
   - 维护者将对您的 PR 进行代码审查。
   - 审查内容包括但不限于：代码逻辑、风格是否符合规范、注释是否完整、特殊标签使用是否正确等。
6. **合并与发布**
   - 审查通过后，您的代码将被合并到官方的 `Develop/v2` 分支。
   - 之后的官方发布流程为：
     - `Develop/v2` → `Pre-Release/v2`（进行集成测试）
     - 测试通过后，由维护者发布到 `main` 分支。

## 注意事项

- **请勿**直接向官方的 `main` 或 `Pre-Release/v2` 分支提交代码或 PR，所有功能开发应通过 PR 至 `Develop/v2` 的方式进入代码库。
- **例外情况**：如流程第 4.1 条所述，为特定目的（如发布测试版本）向 `Pre-Release/v2` 等分支提交 PR 是允许的，但需在 PR 中充分说明。
- 所有公开 API 方法必须包含完整注释，请参考[文档注释规范](docs/zh-CN/styleguide/docstring.md)。
- 如有疑问，请联系 `erisdev@88.com` 或云湖群 ID 635409929。

感谢您的贡献！

---

# 專案貢獻指南

感謝您對 ErisPulse 的關注！ErisPulse 致力於打造一個易用、高效、可擴充的多平台機器人開發框架。每一個貢獻，無論是程式碼、文件、問題回報還是想法建議，都幫助這個專案變得更好。

## 第一次為 ErisPulse 貢獻需要什麼

如果您是第一次為 ErisPulse 做貢獻，這裡有幾個適合入手的方向：

### 適合入門的貢獻

1. **文件改進**
   - 修正錯別字或表達不當之處
   - 補充缺失的範例程式碼
   - 翻譯文件到其他語言

2. **國際化與在地化 (i18n)**
   - 修正文件、CLI 輸出、安裝腳本、Docker entrypoint 或 Dashboard 中的翻譯錯誤
   - 為新增功能補充缺失的翻譯
   - 提升所有支援語言（zh-CN、en、zh-TW、ja、ru）的翻譯品質
   - 協助在地化新增元件

3. **Bug 修復**
   - 在 GitHub Issues 中尋找標記為「bug」的問題
   - 選擇您熟悉或感興趣的領域
   - 提交修復方案

4. **完善範例**
   - 優化現有的範例程式碼
   - 新增新的使用情境範例

### 簡化的貢獻流程

1. **Fork** 本專案到您的 GitHub 帳戶
2. **基於** `Develop/v2` 分支建立您的功能分支
3. **進行修改**並提交清晰的提交訊息
4. **提交 Pull Request** 到官方倉庫的 `Develop/v2` 分支
5. **填寫 PR 模板**，等待程式碼審查

---

## 分支管理規範

### 分支結構
- **main**: 主分支，存放穩定可發布的程式碼
- **Develop/v2**: 開發主分支，所有功能分支最終合併至此
- **Pre-Release/v2**: 預發布分支，用於版本發布前的測試

> **歷史版本封存**: V1 版本程式碼已遷移至獨立倉庫 [ErisPulse/Archive-v1](https://github.com/ErisPulse/Archive-v1)，僅供歷史參考。

## 開發環境搭建

### 複製專案

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
```

### 環境設定

使用 `uv` 同步專案環境：

```bash
uv sync
# 啟用虛擬環境: source .venv/bin/activate (macOS/Linux) 或 .venv\Scripts\activate (Windows)
```

> ErisPulse 使用 Python 3.13 開發，相容 Python 3.10+

### 專案結構

> 以下為簡化結構，僅列出關鍵目錄，便於快速定位程式碼。

```
ErisPulse/
├── src/
│   └── ErisPulse/           # 核心原始碼
│       ├── CLI/             # 命令列工具 (epsdk)
│       ├── Core/            # 核心模組
│       │   ├── Bases/       # 基礎類別定義
│       │   ├── Event/       # 事件系統
│       │   └── ...          # 其他核心元件
│       ├── finders/         # 模組 / 適配器發現
│       ├── loaders/         # 載入器（含延遲載入策略）
│       ├── runtime/         # 執行時期
│       ├── sdk.py           # SDK 入口實作
│       └── __init__.py      # 套件入口
├── config/                  # 預設設定
├── docs/                    # 多語言文件 (zh-CN / en / ja / ru / zh-TW)
├── examples/                # 範例程式碼
├── tests/                   # 測試程式碼 (unit / integration / performance / stress)
├── scripts/                 # 工具腳本
├── workers/                 # 背景 Worker
├── pyproject.toml           # 專案與相依性設定
└── pytest.ini               # 測試設定
```

## 型別存根生成

我們有一個用於生成 `.pyi` 存根檔案的腳本，在倉庫中您看不到 `.pyi` 檔案。如果您需要使用這些註解，請執行 `python3 scripts/tools/generate-type-stubs.py`，它將在本地生成 `.pyi` 檔案。提交時，請確保已清理本地 `.pyi` 檔案，使用 `python3 scripts/tools/generate-type-stubs.py --clean-only` 完成清理。

## 測試與程式碼檢查

### 執行測試

專案使用 `pytest`，設定見 `pytest.ini`（已開啟覆蓋率、`asyncio-mode=auto` 及各類測試標記）。在虛擬環境中執行：

```bash
# 執行全部測試（含覆蓋率報告）
uv run pytest

# 僅執行單元測試 / 整合測試
uv run pytest -m unit
uv run pytest -m integration

# 執行指定路徑或單一用例
uv run pytest tests/unit
uv run pytest tests/unit/test_xxx.py::TestClass::test_method
```

可用 `-m` 按標記篩選，常用標記：`unit`、`integration`、`e2e`、`adapter`、`module`、`event`、`lifecycle`、`config`、`storage`、`logger`、`router`。

### 程式碼檢查與格式化

專案使用兩套檢查工具：

1. **[Ruff](https://docs.astral.sh/ruff/)** — 程式碼風格與輕量級靜態檢查（設定見 `pyproject.toml` 的 `[tool.ruff]`）
2. **[Basedpyright](https://docs.basedpyright.com/)** — 嚴格的型別檢查（設定見 `pyproject.toml` 的 `[tool.basedpyright]`）

提交前請確保程式碼通過兩套檢查：

```bash
# 程式碼檢查
uv run ruff check .

# 自動修復可修復的問題
uv run ruff check . --fix

# 程式碼格式化
uv run ruff format .

# 型別檢查
uv run basedpyright src/ErisPulse
```

> ⚠️ **型別檢查規則**：`pyproject.toml` 的 `[tool.basedpyright]` 採用 `standard` 中等級模式，
> 已將「真實型別 bug」（如返回值與註解不匹配、參數型別不相容、對可能 `None` 取屬性等）提級為 error。
> 大量的 `reportAny/Unknown*` 警告屬於「型別不完整」，可漸進式修復，不會阻止合併。

## 程式碼註解規範

> 詳細註解規範請參考 [docs/zh-TW/styleguide/docstring.md](docs/zh-TW/styleguide/docstring.md)

## 貢獻流程

1. **Fork 倉庫**
   - 首先 fork 主倉庫到您的個人 GitHub 帳戶。
2. **建立功能分支**
   - 在您**自己 Fork 的倉庫**中，基於官方的 `Develop/v2` 分支建立功能分支。
3. **開發工作**
   - 在您的功能分支上進行開發。
   - 保持提交訊息清晰明確（例如：`feat: 新增使用者登入功能`）。
   - 嚴格遵守[文件註解規範](docs/zh-TW/styleguide/docstring.md)，為所有新增的公開 API 新增文件註解。
   - 提交前，確保在 `CHANGELOG.md` 中新增了變更描述。
   - 為了減少合併衝突，建議定期從**官方倉庫的 `Develop/v2` 分支**拉取（`pull`）更新。
4. **提交 Pull Request (PR)**
   - 開發完成後，在 GitHub 上向**官方倉庫的 `Develop/v2` 分支**發起 Pull Request。
   - 請確保 PR 的**目標倉庫**是原始專案庫，**目標分支**為 `Develop/v2`。
   - 在 PR 描述中，請完整填寫提供的 PR 模板，勾選對應選項並新增必要的詳情資訊。
   - **4.1 提交到其他分支（可選）**
     - 如果您需要發布測試版本或進行其他特殊操作，也可以向官方倉庫的**其他分支**（如 `Pre-Release/v2`）發起 PR。
     - 請在 PR 標題和描述中**明確說明**提交至此分支的原因和目的。
5. **程式碼審查**
   - 維護者將對您的 PR 進行程式碼審查。
   - 審查內容包括但不限於：程式碼邏輯、風格是否符合規範、註解是否完整、特殊標籤使用是否正確等。
6. **合併與發布**
   - 審查通過後，您的程式碼將被合併到官方的 `Develop/v2` 分支。
   - 之後的官方發布流程為：
     - `Develop/v2` → `Pre-Release/v2`（進行整合測試）
     - 測試通過後，由維護者發布到 `main` 分支。

## 注意事項

- **請勿**直接向官方的 `main` 或 `Pre-Release/v2` 分支提交程式碼或 PR，所有功能開發應透過 PR 至 `Develop/v2` 的方式進入程式庫。
- **例外情況**：如流程第 4.1 條所述，為特定目的（如發布測試版本）向 `Pre-Release/v2` 等分支提交 PR 是允許的，但需在 PR 中充分說明。
- 所有公開 API 方法必須包含完整註解，請參考[文件註解規範](docs/zh-TW/styleguide/docstring.md)。
- 如有疑問，請聯絡 `erisdev@88.com` 或雲湖群 ID 635409929。

感謝您的貢獻！

---

# プロジェクト貢献ガイド

ErisPulse に関心をお寄せいただきありがとうございます！ErisPulse は、使いやすく、効率的で、拡張性のあるマルチプラットフォームボット開発フレームワークの構築を目指しています。コード、ドキュメント、問題報告、アイデアなど、すべての貢献がこのプロジェクトをより良くします。

## 初めての貢献

初めて ErisPulse に貢献する場合、以下は良い出発点です：

### 初心者向けの貢献

1. **ドキュメントの改善**
   - 誤字や分かりにくい表現の修正
   - 不足しているコード例の追加
   - ドキュメントの他言語への翻訳

2. **国際化とローカライズ (i18n)**
   - ドキュメント、CLI 出力、インストールスクリプト、Docker entrypoint、Dashboard の翻訳エラーの修正
   - 新機能の翻訳漏れの補完
   - 全サポート言語（zh-CN、en、zh-TW、ja、ru）の翻訳品質の向上
   - 新規コンポーネントのローカライズ支援

3. **バグ修正**
   - GitHub Issues で「bug」ラベルの付いた問題を探す
   - 馴染みのある、または興味のある分野を選ぶ
   - 修正案を提出する

4. **サンプルの改善**
   - 既存のサンプルコードの改善
   - 新しい使用例の追加

### 簡易貢献フロー

1. このプロジェクトを GitHub アカウントに **Fork**
2. `Develop/v2` ブランチをベースに機能ブランチを**作成**
3. 明確なコミットメッセージで**変更をコミット**
4. 公式リポジトリの `Develop/v2` ブランチに **Pull Request** を提出
5. PR テンプレートに**記入**し、レビューを待つ

---

## ブランチ管理

### ブランチ構成
- **main**: メインブランチ、安定したリリース可能なコード
- **Develop/v2**: 開発メインブランチ、すべての機能が最初にマージされる
- **Pre-Release/v2**: リリース前テスト用のプレリリースブランチ

> **過去のアーカイブ**: V1 コードは [ErisPulse/Archive-v1](https://github.com/ErisPulse/Archive-v1) に移行済み、参照用のみ。

## 開発環境のセットアップ

### クローン

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
```

### 環境設定

`uv` を使ってプロジェクト環境を同期：

```bash
uv sync
# 仮想環境を有効化: source .venv/bin/activate (macOS/Linux) または .venv\Scripts\activate (Windows)
```

> ErisPulse は Python 3.13 で開発、Python 3.10+ と互換

### プロジェクト構成

> 簡略化した構成、主要ディレクトリのみ記載。

```
ErisPulse/
├── src/
│   └── ErisPulse/           # コアソースコード
│       ├── CLI/             # CLI ツール (epsdk)
│       ├── Core/            # コアモジュール
│       │   ├── Bases/       # 基底クラス定義
│       │   ├── Event/       # イベントシステム
│       │   └── ...          # その他のコアコンポーネント
│       ├── finders/         # モジュール / アダプター検出
│       ├── loaders/         # ローダー（遅延読み込み含む）
│       ├── runtime/         # ランタイム
│       ├── sdk.py           # SDK エントリ
│       └── __init__.py      # パッケージエントリ
├── config/                  # デフォルト設定
├── docs/                    # 多言語ドキュメント (zh-CN / en / ja / ru / zh-TW)
├── examples/                # サンプルコード
├── tests/                   # テストコード (unit / integration / performance / stress)
├── scripts/                 # ユーティリティスクリプト
├── workers/                 # バックグラウンド Worker
├── pyproject.toml           # プロジェクト & 依存関係設定
└── pytest.ini               # テスト設定
```

## 型スタブ生成

`.pyi` スタブファイルを生成するスクリプトがあります。リポジトリには `.pyi` ファイルは含まれません。これらの注釈が必要な場合は `python3 scripts/tools/generate-type-stubs.py` を実行すると、ローカルに `.pyi` ファイルが生成されます。コミット前に `python3 scripts/tools/generate-type-stubs.py --clean-only` でクリーンアップしてください。

## テストとリント

### テストの実行

プロジェクトは `pytest` を使用（設定は `pytest.ini`、カバレッジ、`asyncio-mode=auto`、各種テストマーカーあり）。仮想環境で実行：

```bash
# 全テスト実行（カバレッジレポート付き）
uv run pytest

# ユニット / 統合テストのみ
uv run pytest -m unit
uv run pytest -m integration

# 特定のパスやテストケース
uv run pytest tests/unit
uv run pytest tests/unit/test_xxx.py::TestClass::test_method
```

`-m` でマーカー絞り込み可能。主要マーカー：`unit`、`integration`、`e2e`、`adapter`、`module`、`event`、`lifecycle`、`config`、`storage`、`logger`、`router`。

### リントとフォーマット

プロジェクトは2つのチェックツールを使用：

1. **[Ruff](https://docs.astral.sh/ruff/)** — コードスタイルと軽量静的解析（設定は `pyproject.toml` の `[tool.ruff]`）
2. **[Basedpyright](https://docs.basedpyright.com/)** — 厳格な型チェック（設定は `pyproject.toml` の `[tool.basedpyright]`）

コミット前にコードが両方のチェックを通ることを確認：

```bash
# リント
uv run ruff check .

# 自動修正
uv run ruff check . --fix

# フォーマット
uv run ruff format .

# 型チェック
uv run basedpyright src/ErisPulse
```

> ⚠️ **型チェックルール**：`[tool.basedpyright]` は `standard`（中程度）モードを使用。
> 実際の型バグ（戻り値と注釈の不一致、引数型の不一致、`None` の可能性がある値へのアクセスなど）は **error** に昇格。
> 多くの `reportAny/Unknown*` 警告は「型の不十分さ」を示すもので、マージを妨げません。

## ドキュメント文字列規範

> 詳細は [docs/ja/styleguide/docstring.md](docs/ja/styleguide/docstring.md) を参照

## 貢献プロセス

1. **リポジトリを Fork** して GitHub アカウントに追加。
2. **機能ブランチを作成** — Fork したリポジトリで `Develop/v2` をベースに作成。
3. **開発**
   - コミットメッセージを明確に保つ（例：`feat: ユーザーログインを追加`）。
   - 新しい公開 API には[ドキュメント文字列規範](docs/ja/styleguide/docstring.md)に従う。
   - `CHANGELOG.md` に変更内容を追記。
   - コンフリクトを減らすため、定期的に `Develop/v2` から更新をプル。
4. **Pull Request を提出** — 公式リポジトリの `Develop/v2` ブランチへ。
   - ターゲットリポジトリが原本プロジェクト、ターゲットブランチが `Develop/v2` であることを確認。
   - PR テンプレートに完全に記入。
   - **4.1 他ブランチへ（任意）**: テストリリースなどの場合、他ブランチ（例：`Pre-Release/v2`）に PR 可能。PR のタイトルと説明で理由を明記。
5. **コードレビュー**: メンテナーが PR をレビュー — ロジック、スタイル、コメント、ラベルなど。
6. **マージとリリース**: 承認後、コードは `Develop/v2` にマージ。リリースフロー：
   - `Develop/v2` → `Pre-Release/v2`（統合テスト）
   - テスト通過後、メンテナーが `main` にリリース。

## 注意事項

- `main` や `Pre-Release/v2` に直接コミットや PR は**しないでください**。すべての機能開発は `Develop/v2` への PR 経由で行います。
- **例外**: 手順 4.1 の通り、特定目的での `Pre-Release/v2` 等への PR は明確な理由があれば可能。
- すべての公開 API メソッドには完全なドキュメント文字列が必要 — [ドキュメント文字列規範](docs/ja/styleguide/docstring.md)を参照。
- 質問は `erisdev@88.com` または雲湖グループ ID 635409929 まで。

貢献ありがとうございます！

---

# Руководство по вкладу

Благодарим за интерес к ErisPulse! ErisPulse стремится создать простой в использовании, эффективный и расширяемый фреймворк для разработки мультиплатформенных ботов. Каждый вклад — будь то код, документация, отчёты об ошибках или идеи — помогает сделать проект лучше.

## С чего начать

Если вы вносите вклад впервые, вот несколько хороших отправных точек:

### Простые задачи для начинающих

1. **Улучшение документации**
   - Исправление опечаток или неточных формулировок
   - Добавление недостающих примеров кода
   - Перевод документации на другие языки

2. **Интернационализация и локализация (i18n)**
   - Исправление ошибок перевода в документации, выводе CLI, скриптах установки, Docker entrypoint или Dashboard
   - Добавление отсутствующих переводов для новых функций
   - Повышение качества переводов для всех поддерживаемых языков (zh-CN, en, zh-TW, ja, ru)
   - Помощь в локализации новых компонентов

3. **Исправление багов**
   - Поиск задач с меткой «bug» в GitHub Issues
   - Выбор области, с которой вы знакомы или которая вам интересна
   - Отправка исправления

4. **Улучшение примеров**
   - Оптимизация существующего примера кода
   - Добавление новых сценариев использования

### Упрощённый процесс вклада

1. **Сделайте Fork** проекта в свой GitHub-аккаунт
2. **Создайте** ветку функции на основе `Develop/v2`
3. **Внесите** изменения с понятными сообщениями коммитов
4. **Отправьте Pull Request** в официальную ветку `Develop/v2`
5. **Заполните** шаблон PR и ожидайте ревью

---

## Управление ветками

### Структура веток
- **main**: Основная ветка, стабильный готовый к релизу код
- **Develop/v2**: Ветка разработки, сюда сливаются все функции
- **Pre-Release/v2**: Предрелизная ветка для тестирования перед релизом

> **Исторический архив**: Код V1 перенесён в [ErisPulse/Archive-v1](https://github.com/ErisPulse/Archive-v1), только для справки.

## Настройка среды разработки

### Клонирование

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
```

### Настройка окружения

Используйте `uv` для синхронизации среды проекта:

```bash
uv sync
# Активация venv: source .venv/bin/activate (macOS/Linux) или .venv\Scripts\activate (Windows)
```

> ErisPulse разрабатывается на Python 3.13, совместим с Python 3.10+

### Структура проекта

> Упрощённая структура с ключевыми директориями для быстрой навигации.

```
ErisPulse/
├── src/
│   └── ErisPulse/           # Исходный код ядра
│       ├── CLI/             # CLI-инструменты (epsdk)
│       ├── Core/            # Основные модули
│       │   ├── Bases/       # Базовые классы
│       │   ├── Event/       # Система событий
│       │   └── ...          # Другие компоненты ядра
│       ├── finders/         # Обнаружение модулей / адаптеров
│       ├── loaders/         # Загрузчики (вкл. ленивую загрузку)
│       ├── runtime/         # Среда выполнения
│       ├── sdk.py           # Точка входа SDK
│       └── __init__.py      # Точка входа пакета
├── config/                  # Конфигурация по умолчанию
├── docs/                    # Многоязычная документация (zh-CN / en / ja / ru / zh-TW)
├── examples/                # Примеры кода
├── tests/                   # Тесты (unit / integration / performance / stress)
├── scripts/                 # Вспомогательные скрипты
├── workers/                 # Фоновые Worker
├── pyproject.toml           # Конфигурация проекта и зависимостей
└── pytest.ini               # Конфигурация тестов
```

## Генерация заглушек типов

У нас есть скрипт для генерации файлов заглушек `.pyi`. В репозитории вы не найдёте `.pyi`-файлов. Если нужны эти аннотации, выполните `python3 scripts/tools/generate-type-stubs.py` — он сгенерирует `.pyi`-файлы локально. Перед коммитом очистите их командой `python3 scripts/tools/generate-type-stubs.py --clean-only`.

## Тестирование и линтинг

### Запуск тестов

Проект использует `pytest` (конфиг в `pytest.ini`, с покрытием, `asyncio-mode=auto` и тестовыми маркерами). Запускайте в виртуальном окружении:

```bash
# Все тесты (с отчётом покрытия)
uv run pytest

# Только unit / integration тесты
uv run pytest -m unit
uv run pytest -m integration

# Конкретный путь или тест-кейс
uv run pytest tests/unit
uv run pytest tests/unit/test_xxx.py::TestClass::test_method
```

Фильтрация по маркеру через `-m`. Основные маркеры: `unit`, `integration`, `e2e`, `adapter`, `module`, `event`, `lifecycle`, `config`, `storage`, `logger`, `router`.

### Линт и форматирование

Проект использует два инструмента проверки:

1. **[Ruff](https://docs.astral.sh/ruff/)** — стиль кода и лёгкий статический анализ (конфиг в `[tool.ruff]` файла `pyproject.toml`)
2. **[Basedpyright](https://docs.basedpyright.com/)** — строгая проверка типов (конфиг в `[tool.basedpyright]` файла `pyproject.toml`)

Перед коммитом убедитесь, что код проходит обе проверки:

```bash
# Линт
uv run ruff check .

# Автоисправление
uv run ruff check . --fix

# Форматирование
uv run ruff format .

# Проверка типов
uv run basedpyright src/ErisPulse
```

> ⚠️ **Правила проверки типов**: `[tool.basedpyright]` использует режим `standard` (умеренный).
> Реальные ошибки типов (несоответствие возвращаемого значения, несовместимость аргументов, обращение к `None` и т.д.) повышены до **error**.
> Большинство предупреждений `reportAny/Unknown*` — это «неполные типы», они не блокируют слияние.

## Стандарты документирования

> Подробные рекомендации см. в [docs/ru/styleguide/docstring.md](docs/ru/styleguide/docstring.md)

## Процесс внесения вклада

1. **Сделайте Fork** репозитория в свой GitHub-аккаунт.
2. **Создайте ветку функции** на основе `Develop/v2` в своём форке.
3. **Разработка**
   - Сообщения коммитов должны быть понятными (например, `feat: добавить вход пользователя`).
   - Следуйте [стандартам документирования](docs/ru/styleguide/docstring.md) для всех новых публичных API.
   - Добавляйте записи в `CHANGELOG.md`.
   - Регулярно подтягивайте обновления из `Develop/v2` для минимизации конфликтов.
4. **Отправьте Pull Request** в официальную ветку `Develop/v2`.
   - Убедитесь, что целевой репозиторий — исходный проект, целевая ветка — `Develop/v2`.
   - Полностью заполните шаблон PR.
   - **4.1 Другие ветки (опционально)**: Для тестовых релизов или специальных операций можно PR в другие ветки (например, `Pre-Release/v2`). Чётко укажите причину в заголовке и описании PR.
5. **Ревью кода**: Мейнтейнеры проверят ваш PR — логика, стиль, комментарии, метки и т.д.
6. **Слияние и релиз**: После одобрения ваш код вливается в `Develop/v2`. Процесс релиза:
   - `Develop/v2` → `Pre-Release/v2` (интеграционное тестирование)
   - После тестов мейнтейнеры релизят в `main`.

## Примечания

- **Не** коммитьте и не делайте PR напрямую в `main` или `Pre-Release/v2`. Все функции попадают через PR в `Develop/v2`.
- **Исключение**: Как описано в шаге 4.1, PR в `Pre-Release/v2` для определённых целей разрешены с чётким обоснованием.
- Все публичные методы API должны иметь полную документацию — см. [стандарты документирования](docs/ru/styleguide/docstring.md).
- Вопросы? Свяжитесь: `erisdev@88.com` или ID группы Yunhu 635409929.

Благодарим за ваш вклад!
