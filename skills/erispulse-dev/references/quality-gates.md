# 质量门禁与测试纪律

## 三项门禁（与 CI 一致，提交前必须全绿）

```bash
uv sync --extra test                          # pytest 依赖（首次）
uv run pytest                                 # 全量测试
uv run ruff check .                           # lint
uv run basedpyright src/ErisPulse             # 类型检查（0 errors 才算过；warnings 为基线存量）
```

## ruff 配置要点（pyproject.toml [tool.ruff]）

- `target-version = "py310"`，`line-length = 120`，include 覆盖 src/tests/scripts/examples
- 规则集：`E W F I B C4 UP SIM RET PIE RUF PTH PERF FURB PL N`
- 关键 ignore 及原因（新代码遇到同类场景直接豁免，勿为绕开而改坏语义）：
  - `RUF001/002/003` 全角中文标点误报（中文项目必豁免）
  - `B008` 函数调用作默认参数——`Depends` 依赖注入的标准形态
  - `PLC0415` 顶层外 import——异步框架 lazy import 是必要模式
  - `PLR0911/0912/0913/0915/0917` 复杂度类——既有公共 API 签名不可破坏
  - `PLW0603` global——框架单例模式必要
  - `PERF203` try-in-loop——异步轮询/重试常见写法
  - `RUF012` 可变类默认——handlers/事件表是既有 API
  - `RUF022` __all__ 排序——按语义分组带注释，强制排序破坏可读性

## basedpyright 配置要点

- `typeCheckingMode = "standard"`，pythonVersion 3.10，include 仅 src
- "真实类型 bug" 提级为 error：`reportReturnType` / `reportArgumentType`（其余 report* 维持 warning 基线）
- 修类型误报的优先路径：声明哨兵返回 `Any`（pydantic v2 同款）+ `dataclass_transform`，而非 `# type: ignore` 满天飞

## 测试纪律

- **改行为必改测试；修 bug 必须先有能复现的红测试**
- 异常路径与边界（空输入/超时/重复调用/半初始化）与正常路径同等对待
- 核心模块（Bases / runtime / config / loaders）改动必须补充或更新 pytest 用例
- 存储引擎改动必须三后端跑通真机验证（sqlite / mysql / postgres 各 12 项，`tests/devs/test_storage_backend_verify.py`）
- 测试可访问内部结构但访问点集中；存量覆盖缺口以基线呈现，文件被触碰时升级为阻断
- 脚手架模板（`CLI/commands/create.py`）改动后 `.format()` + `compile()` 验证

## 供应链与依赖

- 修改源码前确认供应链上下游正常；新增 import 确认无循环依赖
- 新增功能检查 `.github/workflows` 是否需要同步
