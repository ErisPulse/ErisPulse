# 配置與 UI 元數據

> 適用範圍：所有繼承 `BaseConfig` / `BotAccountConfig` 的配置宣告（適配器全域配置、帳戶配置、模組配置）。

ErisPulse 的配置體系是**宣告式**的：開發者使用 dataclass 欄位 + 元數據描述配置項，框架的 `get_config_schema()` 將其轉譯為 JSON Schema，供任何消費方（Dashboard、第三方介面、CLI 導覽器等）渲染。本文是該元數據的**規範定義**——widget 語義、值形態、條件顯示隱藏、相容性義務皆以此為準；各消費方負責具體實現，語義必須與本文一致。

## 聲明結構

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """適配器全域設定"""

@dataclass
class MyAccountConfig(BotAccountConfig):
    """帳戶設定（多帳戶適配器）"""
    token: str = field(
        default="",
        metadata={
            "description": "存取令牌",
            "required": True,
            "secret": True,
            "ui": {
                "widget": "password",
                "group": "basic",
                "order": 1,
                "placeholder": "貼上平台令牌",
            },
        },
    )
```

## 基礎元數據（metadata 頂層鍵）

| 鍵 | 類型 | 語義 |
|---|---|---|
| `description` | `str` 或 `{"i18n": key, "default": text}` | 配置項說明（支援 i18n 引用） |
| `required` | `bool` | 必填（校驗與 UI 提示；帳戶必填為空時消費方可提示未完成配置） |
| `secret` | `bool` | 敏感值：UI 必須以密碼形態呈現、日誌中脫敏 |

## UI 元數據（`metadata["ui"]` 子表）

`ui` 為標準鍵；`webui` 為舊別名（等價，消費方須同時支援）。

### 通用鍵

| 鍵 | 語義 |
|---|---|
| `widget` | 控件類型（見 widget 名錄）；缺省時按欄位類型推斷 |
| `group` | 分組名；同名分組由 `_schema_meta["group_labels"]` 提供顯示名（同樣支援 i18n 字典） |
| `order` | 組內排序權重（小者在前，缺省 100） |
| `options` | 枚舉選項 `[{label, value}]`（`label` 支援 i18n 字典；用於 select/multiselect） |
| `placeholder` | 輸入占位文字（支援 i18n 字典） |
| `min` / `max` / `step` | 數值範圍與步長（number/slider） |
| `rows` | 多行文字行數（textarea） |

### 條件顯示/禁用（欄位聯動）

| 鍵 | 語義 |
|---|---|
| `show_if` | 條件不滿足時**隱藏**該欄位（值保留，不刪除） |
| `disabled_if` | 條件滿足時**禁用**該欄位（置灰鎖定，值保留） |

條件物件：`{"field": <同作用域欄位名或完整配置鍵>, "op": <算子>, "value": <比較值>}`。算子集合：

| op | 語義 |
|---|---|
| `eq` / `ne` | 相等 / 不等（字串化比較） |
| `in` / `nin` | `value` 為陣列，成員 / 非成員 |
| `gt` / `gte` / `lt` / `lte` | 數值比較 |
| `truthy` | 真值（非空、非 `"false"`、非 `"0"`） |

`op` 缺省為 `eq`。欄位解析：先按**同配置作用域短名**，再按完整鍵（如 `accounts.default.mode`）。

### 值形態（`value_type`，用於 `multiselect`）

| 值 | 存儲形態 | 適用 |
|---|---|---|
| `json`（預設） | JSON 陣列**字串**（如 `"[0, 25]"`） | 欄位類型為 `str`、以 JSON 文本存陣列 |
| `array` | 原生陣列 | 欄位類型為 `list` |
| `mask` | 位遮罩**整數**（勾選值按 `2^v` 求和） | 欄位類型為 `int` 的位標誌，`options[].value` 為位序號 |

**消費方義務**：`value_type` 缺省時必須按欄位類型推斷（`int` + 數字選項 → `mask`；`list` → `array`；否則 `json`），保證只聲明 `widget: multiselect` 也能寫入正確類型。

## widget 名錄

消費方需實現以下語義；**未識別的 widget 必須回退為單行文本**，不得報錯。

| widget | 值類型 | 語義 |
|---|---|---|
| `text` | str | 單行文本（預設回退目標） |
| `textarea` | str | 多行文本（`rows`） |
| `password` | str | 密碼（`secret: True` 時自動推斷） |
| `number` | int/float | 數字輸入（`min`/`max`/`step`；數值類型字段自動推斷） |
| `switch` | bool | 開關（bool 字段自動推斷） |
| `select` | str | 單選下拉（`options`；有 options 的字串字段自動推斷） |
| `multiselect` | 見值形態 | 多選（複選組；`options` + `value_type`） |
| `slider` | int/float | 滑杆（`min`/`max`/`step`） |
| `color` | str | 顏色（`#rrggbb`） |
| `date` / `time` / `datetime` | str | 日期 / 時間 / 日期時間（ISO 字符串） |
| `kv` | dict | 鍵值對編輯器（`dict[str, str]`） |
| `list` | list | 列表編輯器（`item` 聲明行內字段：`{"widget": ...}` 或 `{"fields": {...}}` 支持行內嵌套） |

## 兼容性契約（消費方必須遵守）

1. **忽略未知鍵**：元數據中出現規範外鍵（含未來新增）時靜默忽略，不報錯
2. **未知 widget 回退 text**：保證新聲明在舊消費方上仍可編輯
3. **條件不滿足 ≠ 值刪除**：`show_if` 隱藏的欄位值原樣保留
4. **類型推斷兜底**：`value_type` 等擴展鍵缺失時按欄位類型推斷正確儲存形態

## 完整示例

```python
@dataclass
class OneBotAccountDemo(BotAccountConfig):
    mode: str = field(
        default="server",
        metadata={
            "description": "連接模式",
            "ui": {
                "widget": "select",
                "group": "connection",
                "order": 1,
                "options": [
                    {"label": "Server（被動）", "value": "server"},
                    {"label": "Client（主動）", "value": "client"},
                ],
            },
        },
    )
    url: str = field(
        default="ws://127.0.0.1:3001",
        metadata={
            "description": "WebSocket 位址",
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
            "description": "位元遮罩多選（欄位為 int，自動按 mask 存數）",
            "ui": {
                "widget": "multiselect",
                "group": "advanced",
                "order": 3,
                "options": [
                    {"label": "頻道基礎", "value": 0},
                    {"label": "頻道訊息", "value": 9},
                    {"label": "訊息內容（特權）", "value": 15},
                ],
            },
        },
    )
```

## Schema 輸出

`ErisPulse.Core.Bases.config_schema.get_config_schema(cls)` 輸出 JSON Schema（`fields`/`groups`/`account_based`/`meta`），並**原樣透傳**本文定義的全部 `ui` 子表鍵，供消費方直接消費。