# 開発者ガイド

このガイドは、ErisPulse の機能を拡張するためのカスタムモジュールやアダプターを開発する方法を説明します。

## 内容リスト

### モジュール開発

1. [モジュール開発入門](modules/getting-started.md) - 最初のモジュールを作成する
2. [モジュールのコアコンセプト](modules/core-concepts.md) - モジュールのコアコンセプトとアーキテクチャ
3. [Event ウェラーラップの詳細](modules/event-wrapper.md) - Event オブジェクトの完全な説明
4. [モジュールのベストプラクティス](modules/best-practices.md) - 高品質なモジュールを開発するための提案

### アダプター開発

1. [アダプター開発入門](adapters/getting-started.md) - 最初のアダプターを作成する
2. [アダプターのコアコンセプト](adapters/core-concepts.md) - アダプターのコアコンセプト
3. [SendDSL 詳解](adapters/send-dsl.md) - Send メッセージ送信 DSL の完全な説明
4. [イベントコンバーター](adapters/converter.md) - イベントコンバーターの実装
5. [アダプターのベストプラクティス](adapters/best-practices.md) - 高品質なアダプターを開発するための提案

### リリースガイド

- [リリースとモジュールストアガイド](publishing.md) - あなたの作品を PyPI と ErisPulse モジュールストアに公開する方法

## 開発の準備

開発を始める前に、以下の点を確認してください：

1. [基本概念](../getting-started/basic-concepts.md) を読みましたか。
2. [イベント処理](../getting-started/event-handling.md) に精通していますか。
3. 開発環境をインストールしました（Python >= 3.10）。
4. ErisPulse SDK をインストールしました。

## 開発タイプの選択

ニーズに応じて、適切な開発タイプを選択してください。

| 開発タイプ | 適用シーン | 入門ガイド |
|---------|---------|---------|
| **モジュール開発** | ロボット機能の拡張、ビジネスロジックの実装、コマンドやメッセージ処理の提供 | [モジュール開発入門](modules/getting-started.md) |
| **アダプタ開発** | 新しいメッセージプラットフォームへの接続、クロスプラットフォーム通信の実現、プラットフォーム固有機能の提供 | [アダプタ開発入門](adapters/getting-started.md) |

> ロボットの機能を拡張したい場合（コマンドの追加やメッセージ処理など）、**モジュール開発**を選択してください。ロボットを新しいプラットフォームに接続したい場合は、**アダプタ開発**を選択してください。

## 開発ツール

### プロジェクトテンプレート

ErisPulse には、参考用のサンプルプロジェクトが用意されています：

- [モジュールの例](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module) - モジュールの完全なプロジェクト構造
- [アダプターの例](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter) - アダプターの完全なプロジェクト構造

### 開発モード

ホットリロードモードを使用して開発を行い、コードの変更後は自動的に再読み込みされます：

```bash
epsdk run main.py --reload
```

### デバッグのコツ

`config/config.toml` で DEBUG または TRACE レベルのログを有効にします：

```toml
[ErisPulse.logger]
# DEBUG: モジュールのロード、ルートの登録などの開発デバッグ情報を出力
# TRACE: 最低レベルで、イベントの配信、ストレージへの書き込み、遅延ロードなどのフレームワーク内部の詳細なフローを出力
level = "DEBUG"
```

## モジュールの公開

完全な公開フローについては、[公開とモジュールストアのガイド](publishing.md)を参照してください。PyPI での公開手順や ErisPulse モジュールストアへの提出プロセスなども含まれています。

## 関連ドキュメント

- [標準規格](../standards/) - 兼容性を確保するための技術基準
- [プラットフォーム特性ガイド](../platform-guide/) - 各プラットフォームアダプタの特性について学ぶ