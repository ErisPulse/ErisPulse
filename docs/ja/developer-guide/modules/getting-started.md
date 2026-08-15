# モジュール開発入門

このガイドでは、ErisPulse モジュールをゼロから作成する方法を解説します。

## プロジェクト構造

標準的なモジュール構造：

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py

## pyproject.toml 設定

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "モジュールの機能説明"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = []

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"

## __init__.py

```python
from .Core import Main

## Core.py - 基本モジュール

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self.config = self._load_config()
    
    @staticmethod
    def get_load_strategy():
        """モジュール読み込み戦略を返す"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[]  # オプション：依存する他のモジュールのリスト
        )
    
    async def on_load(self, event):
        """モジュールが読み込まれたときに呼び出される"""
        @command("hello", help="挨拶を送信する")
        async def hello_command(event):
            name = event.get_user_nickname() or "友達"
            await event.reply(f"こんにちは、{name}！")
        
        self.logger.info("モジュールが読み込まれました")
    
    async def on_unload(self, event):
        """モジュールがアンロードされるときに呼び出される"""
        self.logger.info("モジュールがアンロードされました")
    
    def _load_config(self):
        """モジュール設定を読み込む"""
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = {
                "api_url": "https://api.example.com",
                "timeout": 30
            }
            self.sdk.config.setConfig("MyModule", default_config)
            return default_config
        return config

## テストモジュール

### ローカルテスト

```bash
# プロジェクトディレクトリでモジュールをインストール
epsdk install ./MyModule

# プロジェクトを実行
epsdk run main.py --reload
```

### テストコマンド

コマンド送信テスト：

```
/hello

## コアコンセプト

### BaseModule 基底クラス

すべてのモジュールは `BaseModule` を継承する必要があり、以下のメソッドを提供します：

| メソッド | 説明 | 必須 |
|------|------|------|
| `__init__(self)` | コンストラクタ | 否 |
| `get_load_strategy()` | ロード戦略を返す | 否 |
| `get_meta()` | モジュール紹介メタ情報（オプション）を返す | 否 |
| `on_load(self, event)` | モジュールロード時に呼び出される | 是 |
| `on_unload(self, event)` | モジュールアンロード時に呼び出される | 是 |

### モジュール紹介 meta

`get_meta()` を通じてモジュールの紹介メタ情報（このモジュールが何をするものか、どのカテゴリに属するかなど）を宣言します。
メタ情報はモジュールの**汎用紹介データ**であり、help モジュール、Dashboard モジュール一覧、モジュールストアなど、各種 UI/エコモジュールによって消費されます。

`get_load_strategy()` が `ModuleLoadStrategy` を返すのと同様に、**`ModuleMeta` 設定クラスのインスタンスを返すことを推奨**します（プロパティの型付け、IDE の補完機能）が、dict を直接返すことでも互換性があります：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天気",               # 表示名（デフォルトの登録名）
            description="都市の天気を照合",  # モジュールの概要
            version="1.0.0",
            author="ErisDev",
            group="ツール",               # 機能グループ
            tags=["天気", "照合"],
        )
```

互換性のある記法（dict）：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "天気",
            "description": "都市の天気を照合",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "ツール",
            "tags": ["天気", "照合"],
        }
```

- `module.get_meta("MyModule")` は解析済みのメタ情報を読み取ります（クラス宣言 > 登録 info、自動的にこのモジュールのコマンド名が補完されます）。
- `module.get_commands_overview()` は「モジュール meta + その登録されたコマンド（エイリアス/グループ/ヘルプ）」を集約し、モジュール単位で整理されたコマンドの概要です。
- コマンドが所属するモジュールは `cmd_info["owner"]` で取得できます（登録時にコンテキストシステムによって自動的に注入されます）。

#### meta フィールドの i18n サポート

メタ情報フィールドの値は純粋な文字列、または i18n 辞書 `{"i18n": "key.path", "default": "フォールバックテキスト"}`（設定 `description` と同様の規約に従います）を使用できます。
翻訳キーは `I18nClass` によって宣言および登録され、`module.get_meta()` が読み込まれた際に現在の言語のテキストとして自動的に解析されます：

```python
class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        meta_description: I18nKey = I18nKey(
            default="Weather lookup",
            zh_CN="都市の天気を照合",
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
sdk.adapter    # アダプタシステム
sdk.router     # ルーティングシステム
sdk.lifecycle  # ライフサイクルシステム

## 次のステップ

- [モジュールの基本概念](core-concepts.md) - モジュールのアーキテクチャについて深く理解する
- [Event ラッパークラスの詳細](event-wrapper.md) - Event オブジェクトの習得
- [モジュール開発のベストプラクティス](best-practices.md) - 高品質なモジュールの開発