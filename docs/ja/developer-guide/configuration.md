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

## UI 元データ（`metadata["ui"]` サブテーブル）

`ui` は標準的なキーであり、`webui` は旧来の別名（同等）です。消費側は両方をサポートする必要があります。

### コンテナ型（`list[T]` / `dict[str, T]`）

フィールドの注釈が**型付きコンテナ**である場合、メンバーの型は自動的に schema に含まれます：

- `list[int]` / `list[str]` 等のスカラー配列：schema には `item`（メンバーのスカラー schema）が含まれ、`widget` が宣言されていない場合は自動的に `list` コントロールとして推論されます（パネルは動的行リストとしてレンダリングされます）。
- `list[SomeDataclass]`：`item` は `{"type": "object", "fields": {...}}` であり、パネルは**行内多フィールド**のオブジェクト行としてレンダリングされます（行内フィールドはすべてのコントロールとバインディングを再帰的にサポートします）。
- `dict[str, T]`：動的キー表、`item` は値の型を保持します；パネルはキーと値のエディタとしてレンダリングされます。
- 手動で `ui.item` を宣言した場合は、自動生成のものに優先されます（明示的な宣言が推論を上書きします）。

読み込み（`dict_to_dataclass`）の際、メンバーは宣言された型に従って正規化されます：スカラーは型変換されます（`["1", 2.0]` → `[1, 2]`）、dataclass メンバーはインスタンス化されます（非 dict スカラーは最初のフィールドとしてラップされます）、全体の JSON 文字列は先に解析されます（パネルの JSON 編集状態 / env による上書き）。
検証（`validate_config`）はメンバーの型と dataclass メンバーのネストされた制約を再帰的にチェックし、エラーメッセージにはメンバーのパス（`rules[0]` / `quotas.q`）が含まれます。

TOML テンプレートでは、要素 / 値が dataclass のコンテナは `[[表数组]]` / `[表.鍵]` ブロックとしてレンダリングされます（要素がある場合は逐次展開し、要素がない場合は注釈の骨格を出力します；空のコンテナは `鍵 = []` として出力されません——静的空配列と後続の `[[鍵]]` 追加は互いに排他的であり、ユーザーが表配列形式で追加できなくなります）。

```python
@dataclass
class RetryRule(BaseConfig):
    host: str = field(default="", metadata={"description": "ターゲットホスト"})
    port: int = field(default=0, metadata={"description": "ポート", "required": True})

@dataclass
class MyConfig(BaseConfig):
    rules: list[RetryRule] = field(default_factory=list)   # パネル：オブジェクト行リスト
    quotas: dict[str, RetryRule] = field(default_factory=dict)  # パネル：キー値表
    nums: list[int] = field(default_factory=list)          # パネル：スカラー行リスト
```

### 一般的なキー

| キー | 意味 |
|---|---|
| `widget` | コントロールの種類（widget 名録を参照）；省略時はフィールドの型に基づいて推論されます |
| `group` | グループ名；同名のグループは `_schema_meta["group_labels"]` によって表示名が提供されます（i18n 辞書もサポートします） |
| `order` | グループ内の並び順の重み（小さい方が先に表示されます；省略時は 100） |
| `options` | 列挙オプション `[{label, value}]`（`label` は i18n 辞書をサポートします；select/multiselect に使用されます） |
| `placeholder` | 入力用のプレースホルダーテキスト（i18n 辞書をサポートします） |
| `min` / `max` / `step` | 数値の範囲とステップ（number/slider） |
| `rows` | 複数行テキストの行数（textarea） |
| `presets` | 予設のカラーパレット（color；`["#rrggbb", ...]`、省略時は消費側の内蔵値を使用します） |

### 条件による表示/非表示・無効化（フィールドの連動）

| キー | 意味 |
|---|---|
| `show_if` | 条件が満たされない場合に**該当フィールドを非表示**します（値は保持され、削除されません） |
| `disabled_if` | 条件が満たされると**該当フィールドを無効化**します（グレーでロックされ、値は保持されます） |

条件オブジェクト：`{"field": <同作用域のフィールド名または完全な構成キー>, "op": <演算子>, "value": <比較値>}`。演算子の集合：

| op | 意味 |
|---|---|
| `eq` / `ne` | 等しい / 等しくない（文字列化して比較） |
| `in` / `nin` | `value` が配列の場合、メンバー / 非メンバー |
| `gt` / `gte` / `lt` / `lte` | 数値の比較 |
| `truthy` | 真値（空でなく、`"false"` でも `"0"` でもない） |

`op` は省略時に `eq` とします。フィールドの解析：まず**同じ構成作用域の短名**で、次に完全なキー（例：`accounts.default.mode`）で行います。

### 値の形態（`value_type`、`multiselect` 用）

| 値 | ストレージの形態 | 適用対象 |
|---|---|---|
| `json`（デフォルト） | JSON 配列**文字列**（例：`"[0, 25]"`） | フィールド型が `str` で、配列を JSON テキストとして保存する場合 |
| `array` | ネイティブ配列 | フィールド型が `list` の場合 |
| `mask` | ビットマスク**整数**（チェックされた値は `2^v` の和として計算されます） | フィールド型が `int` のビットフラグで、`options[].value` がビットの順番号である場合 |

**消費側の義務**：`value_type` が省略された場合、必ずフィールド型に基づいて推論する必要があります（`int` + 数字のオプション → `mask`；`list` → `array`；それ以外は `json`）、`widget: multiselect` だけを宣言しても正しい型で書き込むことができます。

## widget 名録

消費側は以下の意味を実装する必要があります。**認識できない widget は単行テキストにフォールバックし、エラーを報告してはなりません。**

| widget | 値の型 | 意味 |
|---|---|---|
| `text` | str | 単行テキスト（デフォルトのフォールバック対象） |
| `textarea` | str | 複数行テキスト（`rows`） |
| `password` | str | パスワード（`secret: True` の場合自動推論） |
| `number` | int/float | 数値入力（`min`/`max`/`step`；数値型フィールドは自動推論） |
| `switch` | bool | スイッチ（bool 型フィールドは自動推論） |
| `select` | str | 単一選択ドロップダウン（`options`；options がある文字列型フィールドは自動推論） |
| `multiselect` | 値の形態を参照 | 複数選択（チェックボックスグループ；`options` + `value_type`） |
| `slider` | int/float | スライダ（`min`/`max`/`step`） |
| `color` | str | 色（`#rrggbb`） |
| `date` / `time` / `datetime` | str | 日付 / 時間 / 日時（ISO 文字列） |
| `kv` | dict | キーバリューエディタ（`dict[str, str]`） |
| `list` | list | リストエディタ（`item` で行内フィールドを宣言：`{"widget": ...}` または `{"fields": {...}}` で行内ネストをサポート；型付き配列フィールドは自動推論） |

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