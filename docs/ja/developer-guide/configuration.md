# 設定と UI メタデータ

> 適用範囲：`BaseConfig` / `BotAccountConfig` を継承するすべての設定宣言（アダプターのグローバル設定、アカウント設定、モジュール設定）。

ErisPulse の設定体系は**宣言的**です。開発者は dataclass のフィールド + メタデータで設定項目を記述し、フレームワークの `get_config_schema()` がそれを JSON Schema に変換して、あらゆるコンシューマー（Dashboard、サードパーティパネル、CLI ウィザードなど）でのレンダリングに供します。本文書はこのメタデータの**規範的定義**です——widget のセマンティクス、値の形式、条件による表示/非表示、互換性に関する義務は、すべてこれに準拠します。各コンシューマーは具体的な実装を担当し、そのセマンティクスは本文書と一致していなければなりません。

## 宣言構造

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """アダプターのグローバル設定"""

@dataclass
class MyAccountConfig(BotAccountConfig):
    """アカウント設定（マルチアカウントアダプター）"""
    token: str = field(
        default="",
        metadata={
            "description": "アクセストークン",
            "required": True,
            "secret": True,
            "ui": {
                "widget": "password",
                "group": "basic",
                "order": 1,
                "placeholder": "プラットフォームトークンを貼り付け",
            },
        },
    )
```

## 基本メタデータ（metadata のトップレベルキー）

| キー | 型 | 意味 |
|---|---|---|
| `description` | `str` または `{"i18n": key, "default": text}` | 設定項目の説明（i18n 参照に対応） |
| `required` | `bool` | 必須（検証と UI での表示；アカウントの必須項目が空の場合、利用側は設定未完了を通知できる） |
| `secret` | `bool` | 機密値：UI ではパスワード形式で表示し、ログではマスキングすること |

## UI メタデータ（`metadata["ui"]` サブテーブル）

`ui` は標準キーです。`webui` は旧エイリアスです（等価であり、コンシューマーは両方をサポートしなければなりません）。

### 共通キー

| キー | 意味 |
|---|---|
| `widget` | ウィジェットの種類（widget の一覧を参照）；デフォルトではフィールド型から推論されます |
| `group` | グループ名；同名グループの表示名は `_schema_meta["group_labels"]` で提供されます（同様に i18n 辞書をサポート） |
| `order` | グループ内のソート重み（小さいものが先、デフォルトは 100） |
| `options` | 列挙オプション `[{label, value}]`（`label` は i18n 辞書をサポート；select/multiselect で使用） |
| `placeholder` | 入力プレースホルダーテキスト（i18n 辞書をサポート） |
| `min` / `max` / `step` | 数値の範囲とステップ（number/slider） |
| `rows` | 複数行テキストの行数（textarea） |

### 条件による表示/非表示・無効化（フィールド連動）

| キー | 意味 |
|---|---|
| `show_if` | 条件が満たされない場合、該当フィールドを**非表示**にします（値は保持され、削除されません） |
| `disabled_if` | 条件が満たされた場合、該当フィールドを**無効化**します（グレーアウトしてロック、値は保持されます） |

条件オブジェクト：`{"field": <同じスコープのフィールド名または完全な設定キー>, "op": <演算子>, "value": <比較値>}`。演算子の一覧：

| op | 意味 |
|---|---|
| `eq` / `ne` | 等しい / 等しくない（文字列化して比較） |
| `in` / `nin` | `value` は配列であり、メンバー / 非メンバー |
| `gt` / `gte` / `lt` / `lte` | 数値比較 |
| `truthy` | 真値（空でない、`"false"` でない、`"0"` でない） |

`op` のデフォルトは `eq` です。フィールドの解決：まず**同じ設定スコープ内の短い名前**で解決し、次に完全なキー（例：`accounts.default.mode`）で解決します。

### 値の形式（`value_type`、`multiselect` 用）

| 値 | 保存形式 | 適用対象 |
|---|---|---|
| `json`（デフォルト） | JSON 配列の**文字列**（例：`"[0, 25]"`） | フィールド型が `str` で、JSON テキストとして配列を保存する場合 |
| `array` | ネイティブ配列 | フィールド型が `list` の場合 |
| `mask` | ビットマスクの**整数**（チェックされた値を `2^v` の総和として計算） | フィールド型が `int` のビットフラグで、`options[].value` はビット位置 |

**コンシューマーの義務**：`value_type` が省略された場合はフィールド型から推論しなければなりません（`int` + 数値オプション → `mask`；`list` → `array`；それ以外は `json`）。これにより、`widget: multiselect` のみを宣言した場合でも、正しい型で書き込むことが保証されます。

## widget カタログ

コンシューマーは以下のセマンティクスを実装します。**認識できない widget は単一行テキストにフォールバックしなければならず、エラーを出してはなりません。**

| widget | 値の型 | セマンティクス |
|---|---|---|
| `text` | str | 単一行テキスト（デフォルトのフォールバック先） |
| `textarea` | str | 複数行テキスト（`rows`） |
| `password` | str | パスワード（`secret: True` の場合に自動推論） |
| `number` | int/float | 数値入力（`min`/`max`/`step`。数値型フィールドは自動推論） |
| `switch` | bool | スイッチ（bool 型フィールドは自動推論） |
| `select` | str | 単一選択ドロップダウン（`options`。options を持つ文字列フィールドは自動推論） |
| `multiselect` | 値の形態を参照 | 複数選択（チェックボックスグループ。`options` + `value_type`） |
| `slider` | int/float | スライダー（`min`/`max`/`step`） |
| `color` | str | 色（`#rrggbb`） |
| `date` / `time` / `datetime` | str | 日付 / 時刻 / 日時（ISO 文字列） |
| `kv` | dict | キーバリューペアエディター（`dict[str, str]`） |
| `list` | list | リストエディター（`item` でインラインフィールドを宣言：`{"widget": ...}` または `{"fields": {...}}` でインラインのネストに対応） |

## 互換性契約（コンシューマーが遵守すべき事項）

1. **未知キーの無視**：メタデータに仕様外のキー（将来追加されるものを含む）が現れた場合は、エラーを出さずにサイレントに無視する
2. **未知 widget の text へのフォールバック**：新しい宣言が古いコンシューマー上でも編集可能であることを保証する
3. **条件未達成 ≠ 値の削除**：`show_if` で非表示にされたフィールドの値はそのまま保持される
4. **型推論によるフォールバック**：`value_type` などの拡張キーが欠落している場合は、フィールドの型に基づいて正しい保存形式を推論する

## 完全な例

```python
@dataclass
class OneBotAccountDemo(BotAccountConfig):
    mode: str = field(
        default="server",
        metadata={
            "description": "接続モード",
            "ui": {
                "widget": "select",
                "group": "connection",
                "order": 1,
                "options": [
                    {"label": "Server（パッシブ）", "value": "server"},
                    {"label": "Client（アクティブ）", "value": "client"},
                ],
            },
        },
    )
    url: str = field(
        default="ws://127.0.0.1:3001",
        metadata={
            "description": "WebSocket アドレス",
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
            "description": "ビットマスクによる複数選択（フィールドは int、mask に基づいて自動的に値を保存）",
            "ui": {
                "widget": "multiselect",
                "group": "advanced",
                "order": 3,
                "options": [
                    {"label": "チャンネル基本", "value": 0},
                    {"label": "チャンネルメッセージ", "value": 9},
                    {"label": "メッセージ内容（特権）", "value": 15},
                ],
            },
        },
    )
```

## スキーマ出力

`ErisPulse.Core.Bases.config_schema.get_config_schema(cls)` は JSON Schema（`fields`/`groups`/`account_based`/`meta`）を出力し、本文書で定義されたすべての `ui` サブテーブルキーを**そのまま透過**させて渡します。これにより、利用側は直接それらを消費できます。