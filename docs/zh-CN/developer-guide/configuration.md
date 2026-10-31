# 配置与 UI 元数据

> 适用范围：一切继承 `BaseConfig` / `BotAccountConfig` 的配置声明（适配器全局配置、账户配置、模块配置）。

ErisPulse 的配置体系是**声明式**的：开发者用 dataclass 字段 + 元数据描述配置项，框架的 `get_config_schema()` 将其转译为 JSON Schema，供任何消费方（Dashboard、第三方面板、CLI 向导等）渲染。本文是该元数据的**规范定义**——widget 语义、值形态、条件显隐、兼容性义务都以此为准；各消费方负责具体实现，语义必须与本文一致。

## 声明结构

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """适配器全局配置"""

@dataclass
class MyAccountConfig(BotAccountConfig):
    """账户配置（多账户适配器）"""
    token: str = field(
        default="",
        metadata={
            "description": "访问令牌",
            "required": True,
            "secret": True,
            "ui": {
                "widget": "password",
                "group": "basic",
                "order": 1,
                "placeholder": "粘贴平台令牌",
            },
        },
    )
```

## 基础元数据（metadata 顶层键）

| 键 | 类型 | 语义 |
|---|---|---|
| `description` | `str` 或 `{"i18n": key, "default": text}` | 配置项说明（支持 i18n 引用） |
| `required` | `bool` | 必填（校验与 UI 提示；账户必填为空时消费方可提示未完成配置） |
| `secret` | `bool` | 敏感值：UI 必须以密码形态呈现、日志中脱敏 |

## UI 元数据（`metadata["ui"]` 子表）

`ui` 为标准键；`webui` 为旧别名（等价，消费方须同时支持）。

### 通用键

| 键 | 语义 |
|---|---|
| `widget` | 控件类型（见 widget 名录）；缺省时按字段类型推断 |
| `group` | 分组名；同名分组由 `_schema_meta["group_labels"]` 提供显示名（同样支持 i18n 字典） |
| `order` | 组内排序权重（小者在前，缺省 100） |
| `options` | 枚举选项 `[{label, value}]`（`label` 支持 i18n 字典；用于 select/multiselect） |
| `placeholder` | 输入占位文本（支持 i18n 字典） |
| `min` / `max` / `step` | 数值范围与步长（number/slider） |
| `rows` | 多行文本行数（textarea） |

### 条件显隐/禁用（字段联动）

| 键 | 语义 |
|---|---|
| `show_if` | 条件不满足时**隐藏**该字段（值保留，不删除） |
| `disabled_if` | 条件满足时**禁用**该字段（置灰锁定，值保留） |

条件对象：`{"field": <同作用域字段名或完整配置键>, "op": <算子>, "value": <比较值>}`。算子集合：

| op | 语义 |
|---|---|
| `eq` / `ne` | 相等 / 不等（字符串化比较） |
| `in` / `nin` | `value` 为数组，成员 / 非成员 |
| `gt` / `gte` / `lt` / `lte` | 数值比较 |
| `truthy` | 真值（非空、非 `"false"`、非 `"0"`） |

`op` 缺省为 `eq`。字段解析：先按**同配置作用域短名**，再按完整键（如 `accounts.default.mode`）。

### 值形态（`value_type`，用于 `multiselect`）

| 值 | 存储形态 | 适用 |
|---|---|---|
| `json`（默认） | JSON 数组**字符串**（如 `"[0, 25]"`） | 字段类型为 `str`、以 JSON 文本存数组 |
| `array` | 原生数组 | 字段类型为 `list` |
| `mask` | 位掩码**整数**（勾选值按 `2^v` 求和） | 字段类型为 `int` 的位标志，`options[].value` 为位序号 |

**消费方义务**：`value_type` 缺省时必须按字段类型推断（`int` + 数字选项 → `mask`；`list` → `array`；否则 `json`），保证只声明 `widget: multiselect` 也能写入正确类型。

## widget 名录

消费方实现以下语义；**未识别的 widget 必须回退为单行文本**，不得报错。

| widget | 值类型 | 语义 |
|---|---|---|
| `text` | str | 单行文本（缺省回退目标） |
| `textarea` | str | 多行文本（`rows`） |
| `password` | str | 密码（`secret: True` 时自动推断） |
| `number` | int/float | 数字输入（`min`/`max`/`step`；数值类型字段自动推断） |
| `switch` | bool | 开关（bool 字段自动推断） |
| `select` | str | 单选下拉（`options`；有 options 的字符串字段自动推断） |
| `multiselect` | 见值形态 | 多选（复选组；`options` + `value_type`） |
| `slider` | int/float | 滑杆（`min`/`max`/`step`） |
| `color` | str | 颜色（`#rrggbb`） |
| `date` / `time` / `datetime` | str | 日期 / 时间 / 日期时间（ISO 字符串） |
| `kv` | dict | 键值对编辑器（`dict[str, str]`） |
| `list` | list | 列表编辑器（`item` 声明行内字段：`{"widget": ...}` 或 `{"fields": {...}}` 支持行内嵌套） |

## 兼容性契约（消费方必须遵守）

1. **忽略未知键**：元数据中出现规范外键（含未来新增）时静默忽略，不报错
2. **未知 widget 回退 text**：保证新声明在旧消费方上仍可编辑
3. **条件不满足 ≠ 值删除**：`show_if` 隐藏的字段值原样保留
4. **类型推断兜底**：`value_type` 等扩展键缺失时按字段类型推断正确存储形态

## 完整示例

```python
@dataclass
class OneBotAccountDemo(BotAccountConfig):
    mode: str = field(
        default="server",
        metadata={
            "description": "连接模式",
            "ui": {
                "widget": "select",
                "group": "connection",
                "order": 1,
                "options": [
                    {"label": "Server（被动）", "value": "server"},
                    {"label": "Client（主动）", "value": "client"},
                ],
            },
        },
    )
    url: str = field(
        default="ws://127.0.0.1:3001",
        metadata={
            "description": "WebSocket 地址",
            "ui": {
                "widget": "text",
                "group": "connection",
                "order": 2,
                "show_if": {"field": "mode", "op": "eq", "value": "client"},
            },
        },
    )
    intents: int = field(
        default=33281,
        metadata={
            "description": "位掩码多选（字段为 int，自动按 mask 存数）",
            "ui": {
                "widget": "multiselect",
                "group": "advanced",
                "order": 3,
                "options": [
                    {"label": "频道基础", "value": 0},
                    {"label": "频道消息", "value": 9},
                    {"label": "消息内容（特权）", "value": 15},
                ],
            },
        },
    )
```

## Schema 输出

`ErisPulse.Core.Bases.config_schema.get_config_schema(cls)` 输出 JSON Schema（`fields`/`groups`/`account_based`/`meta`），并**原样透传**本文定义的全部 `ui` 子表键，供消费方直接消费。
