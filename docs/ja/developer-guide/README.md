# 開発者ガイド

このガイドは、カスタムモジュールやアダプターを開発し、ErisPulse の機能を拡張する際に役立ちます。

## 内容リスト

### モジュール開発

1. [モジュール開発入門](modules/getting-started.md) - 最初のモジュールを作成
2. [モジュールのコア概念](modules/core-concepts.md) - モジュールのコア概念とアーキテクチャ
3. [Event ラッパークラスの詳細](modules/event-wrapper.md) - Event オブジェクトの完全な説明
4. [モジュールのベストプラクティス](modules/best-practices.md) - 高品質なモジュールを開発するためのアドバイス

### アダプター開発

1. [アダプター開発入門](adapters/getting-started.md) - 最初のアダプターを作成
2. [アダプターのコア概念](adapters/core-concepts.md) - アダプターのコア概念
3. [SendDSL 詳細](adapters/send-dsl.md) - Send メッセージ送信 DSL の完全な説明
4. [イベントコンバーター](adapters/converter.md) - イベントコンバーターの実装
5. [アダプターのベストプラクティス](adapters/best-practices.md) - 高品質なアダプターを開発するためのアドバイス

### 公開ガイド

- [公開とモジュールストアのガイド](publishing.md) - あなたの作品を PyPI と ErisPulse モジュールストアに公開

## 開発の準備

開発を始める前に、以下の準備ができていることを確認してください。

1. [基本概念](../getting-started/basic-concepts.md)を読んでいる
2. [イベント処理](../getting-started/event-handling.md)に慣れている
3. 開発環境（Python >= 3.10）がインストールされている
4. ErisPulse SDKがインストールされている

## 開発の種類の選択

あなたのニーズに合わせて、適切な開発の種類を選択してください。

| 開発の種類 | 適用シナリオ | 入門ガイド |
|---------|---------|---------|
| **モジュール開発** | ボットの機能拡張、特定のビジネスロジックの実装、コマンドとメッセージ処理の提供 | [モジュール開発入門](modules/getting-started.md) |
| **アダプター開発** | 新しいメッセージングプラットフォームへの接続、クロスプラットフォーム通信の実装、プラットフォーム固有機能の提供 | [アダプター開発入門](adapters/getting-started.md) |

> ボットの機能を拡張したい場合（コマンドやメッセージの処理など）、**モジュール開発**を選択してください。新しいプラットフォームにボットを接続したい場合は、**アダプター開発**を選択してください。

## 開発ツール

### プロジェクトテンプレート

ErisPulse は参考としてサンプルプロジェクトを提供しています。

- [モジュールの例](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module) - モジュールの完全なプロジェクト構造
- [アダプターの例](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter) - アダプターの完全なプロジェクト構造

### 開発モード

コードの変更後に自動的に再読み込みするホットリロードモードを使用して開発を行います。

```bash
epsdk run main.py --reload
```

### デバッグのコツ

`config/config.toml` で DEBUG レベルのログを有効にします。

```toml
[ErisPulse.logger]
level = "DEBUG"
```

### モジュール独自のロガーの使用

```python
from ErisPulse import sdk

logger = sdk.logger.get_child("MyModule")
logger.debug("デバッグ情報")
```

## モジュールの公開

公開の完全なフローについては、[公開とモジュールストアのガイド](publishing.md)を参照してください。以下が含まれます。

- PyPI への公開手順
- ErisPulse モジュールストアへの提出プロセス
- アダプターの公開

### クイックリファレンス

```bash
# ビルドして PyPI に公開
python -m build
python -m twine upload dist/*
```

その後、[ErisPulse-ModuleRepo](https://github.com/ErisPulse/ErisPulse-ModuleRepo/issues/new?template=module_submission.md) にアクセスして、モジュールストアに提出します。

## 関連ドキュメント

- [標準仕様](../standards/) - 互換性を確保するための技術標準
- [プラットフォーム特性ガイド](../platform-guide/) - 各プラットフォームのアダプターの特性を理解する