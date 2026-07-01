# 開発者ガイド

このガイドは、ErisPulse の機能を拡張するためのカスタムモジュールやアダプターを開発する方法を説明します。

## 目次

### モジュール開発

1. [モジュール開発の入門](modules/getting-started.md) - 最初のモジュールを作成する
2. [モジュールの基本概念](modules/core-concepts.md) - モジュールの基本的な概念とアーキテクチャ
3. [Event クラスの詳細](modules/event-wrapper.md) - Event オブジェクトの完全な説明
4. [モジュールのベストプラクティス](modules/best-practices.md) - 高品質なモジュール開発に関する提案

### アダプター開発

1. [アダプター開発の入門](adapters/getting-started.md) - 最初のアダプターを作成する
2. [アダプターの基本概念](adapters/core-concepts.md) - アダプターの基本的な概念
3. [SendDSL の詳細](adapters/send-dsl.md) - Send メッセージ送信 DSL の完全な説明
4. [イベント変換器](adapters/converter.md) - イベント変換器の実装
5. [アダプターのベストプラクティス](adapters/best-practices.md) - 高品質なアダプター開発に関する提案

### リリースガイド

- [リリースとモジュールストアのガイド](publishing.md) - あなたの作品を PyPI と ErisPulse モジュールストアにリリースする方法

## 開発準備

開発を開始する前に、以下の事項を確認してください：

1. [基本概念](../getting-started/basic-concepts.md) を読んでいること
2. [イベント処理](../getting-started/event-handling.md) に精通していること
3. 開発環境のインストール（Python >= 3.10）
4. ErisPulse SDK のインストール

## 開発タイプの選択

ニーズに応じて、適切な開発タイプを選択してください：

| 開発タイプ | 適用シーン | 入門ガイド |
|---------|---------|---------|
| **モジュール開発** | ロボット機能の拡張、ビジネスロジックの実装、コマンドやメッセージ処理の提供 | [モジュール開発の入門](modules/getting-started.md) |
| **アダプター開発** | 新しいメッセージプラットフォームへの接続、クロスプラットフォーム通信の実現、プラットフォーム固有の機能の提供 | [アダプター開発の入門](adapters/getting-started.md) |

> ロボットの機能を拡張したい場合（コマンドの追加、メッセージの処理など）は、**モジュール開発**を選択してください。ロボットを新しいプラットフォームに接続したい場合は、**アダプター開発**を選択してください。

## 開発ツール

### プロジェクトテンプレート

ErisPulse は、参考用のサンプルプロジェクトを提供しています：

- [モジュールの例](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module) - モジュールの完全なプロジェクト構造
- [アダプターの例](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter) - アダプターの完全なプロジェクト構造

### 開発モード

コードを変更すると自動的に再読み込みされるホットリロードモードを使用して開発を行います：

```bash
epsdk run main.py --reload
```

### デバッグのヒント

`config/config.toml` で DEBUG または TRACE レベルのログを有効化します：

```toml
[ErisPulse.logger]
# DEBUG: モジュールのロード、ルーティングの登録などの開発用デバッグ情報を出力
# TRACE: 最低レベル、イベントの配信、ストレージへの書き込み、遅延読み込みなどのフレームワーク内部の詳細なフローを出力
level = "DEBUG"
```

## あなたのモジュールをリリースする

完全なリリースプロセスについては、[リリースとモジュールストアのガイド](publishing.md)を参照してください。PyPI へのリリース手順や、ErisPulse モジュールストアへの提出プロセスなどが含まれています。

## 関連ドキュメント

- [標準規格](../standards/) - 互換性を確保するための技術的規格
- [プラットフォーム特性ガイド](../platform-guide/) - 各プラットフォームアダプターの特性について理解する