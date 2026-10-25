# モジュール開発入門

> [!NOTE]
> **L1 コア必読**――トップページの「学習パス」にある5つのコアドキュメントの1つで、モジュール開発に必須です。


このドキュメントに沿って進めると、`/hello` コマンドに応答できる実行可能なモジュールが完成し、モジュールのプロジェクト構造、登録方法、ロード/アンロードフックについても理解できます。今後のすべてのモジュールドキュメントは、この骨組みの上に成り立っています。

## プロジェクト構造

標準的なモジュールの構造：

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py
```

## pyproject.toml 設定

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "モジュール機能の説明"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = []

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

## __init__.py

```python
from .Core import Main
```

## Core.py - 基本モジュール

```python
from ErisPulse import sdk
# ルートからのインポートを推奨（2.10+）：よく使うシンボルはルートパッケージから直接インポートでき、深いパスも引き続き互換
from ErisPulse import BaseModule, command

class Main(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
    
    @staticmethod
    def get_load_strategy():
        """モジュールのロード戦略を返します"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[],  # 任意：依存する他のモジュールのリスト
            # 任意：イベント駆動の遅延アクティベーション――トリガーを宣言すると、最初に一致するイベント/コマンドが到着した時点で自動的にロードされます
            # activate_on=[{"command": {"name": "hello", "help": "挨拶を送る"}}],
        )
    
    async def on_load(self, event):
        """モジュールのロード時に呼び出されます"""
        @command("hello", help="挨拶を送る")
        async def hello_command(event):
            name = event.get_user_nickname() or "フレンド"
            await event.reply(f"こんにちは、{name}さん！")
        
        self.logger.info("モジュールがロードされました")
    
    async def on_unload(self, event):
        """モジュールのアンロード時に呼び出されます"""
        self.logger.info("モジュールがアンロードされました")
```

> **設定の読み取り**：上記の基本例では設定を使用していません。設定を読み取る必要がある場合は、ネストした `ConfigClass` を宣言し、`self.cfg` 経由でリアルタイムに読み取る方法が推奨されます（詳細は [モジュールのコア概念](core-concepts.md#宣言的設定推奨) を参照）。`_load_config()` を手動で呼び出す旧式の書き方は非推奨となりました。

## モジュールのテスト

### ローカルテスト

```bash
# プロジェクトディレクトリでモジュールをインストール
epsdk install ./MyModule

# プロジェクトを実行
epsdk run main.py --reload
```

### コマンドのテスト

コマンドを送信してテストします：

```
/hello
```

## コア概念

### BaseModule 基底クラス

すべてのモジュールは `BaseModule` を継承する必要があり、以下のメソッドを提供します：

| メソッド | 説明 | 必須 |
|------|------|------|
| `__init__(self, sdk)` | コンストラクター（フレームワークが `sdk` インスタンスを渡します） | いいえ |
| `get_load_strategy()` | ロード戦略を返します | いいえ |
| `get_meta()` | モジュール紹介のメタ情報を返します（任意） | いいえ |
| `on_load(self, event)` | モジュールのロード時に呼び出されます | はい |
| `on_unload(self, event)` | モジュールのアンロード時に呼び出されます | はい |

### モジュール紹介 meta

> [!NOTE]
> この機能には ErisPulse **2.8.0+** が必要です。

`get_meta()` を通じて、モジュールの紹介メタ情報（このモジュールが何をするのか、どのカテゴリに属するのかなど）を宣言します。
メタ情報はモジュールの**汎用紹介データ**であり、help モジュール、Dashboard のモジュールリスト、モジュールストアなど、さまざまなインターフェース/エコシステムモジュールから利用されます。

`get_load_strategy()` が `ModuleLoadStrategy` を返すのと同様に、**`ModuleMeta` 設定クラスのインスタンスを返すことが推奨されます**（属性の型付け、IDE 補完）。dict を直接返すことにも対応しています：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天気",               # 表示名（デフォルトの登録名）
            description="都市の天気を照会",  # モジュールの概要
            version="1.0.0",
            author="ErisDev",
            group="ツール",               # 機能グループ
            tags=["天気", "照会"],
        )
```

互換的な書き方（dict）：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "天気",
            "description": "都市の天気を照会",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "ツール",
            "tags": ["天気", "照会"],
        }
```

- `module.get_meta("MyModule")` は解決済みのメタ情報を読み取ります（クラス宣言 > 登録 info の優先順位で、該当モジュールのコマンド名が自動補完されます）。
- `module.get_commands_overview()` は「モジュールの meta + その登録コマンド（エイリアス/グループ/ヘルプ）」を集約した、モジュール別に整理されたコマンドの一覧です。
- コマンドの所属モジュールは `cmd_info["owner"]` から取得できます（登録時にコンテキストシステムが自動的に注入します）。

#### meta フィールドの i18n サポート

メタ情報のフィールド値には、プレーンな文字列、または i18n 辞書 `{"i18n": "key.path", "default": "フォールバックテキスト"}`（設定の `description` と同じ規約）を使用できます。
翻訳キーは `I18nClass` で宣言・登録し、`module.get_meta()` が読み取る際に現在の言語のテキストへ自動的に解決されます：

```python
class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        meta_description: I18nKey = I18nKey(
            default="Weather lookup",
            zh_CN="查询城市天气",
            en="Weather lookup",
        )

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天気",
            description={"i18n": "MyModule.meta_description", "default": "Weather lookup"},
        )
```

### SDK オブジェクト

`sdk` オブジェクトを通じてコア機能にアクセスします：

```python
from ErisPulse import sdk

sdk.storage    # ストレージシステム
sdk.config     # 設定システム
sdk.logger     # ログシステム
sdk.adapter    # アダプターシステム
sdk.router     # ルーティングシステム
sdk.lifecycle  # ライフサイクルシステム
```

## 次のステップ

### 学習パスの続き

- [モジュールのコア概念](core-concepts.md) - モジュールアーキテクチャを深く理解する
- [Event ラッパークラス詳解](event-wrapper.md) - Event オブジェクトを学ぶ

### 作成後は

- [モジュールのベストプラクティス](best-practices.md) - 高品質なモジュールを開発する