# 開発者ガイド

> [!TIP]
> **このドキュメントをいつ読むべきか**：ErisPulse 向けの拡張機能——ボットに機能（モジュール）を追加する、または新しいプラットフォーム（アダプター）に接続する——を開発する準備をしている時に読んでください。ボットを利用するだけなら読み飛ばして、[クイックスタート](../quick-start.md)を直接ご覧ください。

ここからあなたの開発パスを見つけましょう：**モジュール開発**ではコマンドやメッセージハンドラーでボットの機能を拡張でき、**アダプター開発**ではボットを新しいメッセージプラットフォームに接続できます。どちらのパスも、プロジェクトの作成からテスト、公開までの完全な流れを網羅しています。

## 目次

### モジュール開発

1. [モジュール開発入門](modules/getting-started.md) - 最初のモジュールを作成する
2. [モジュールのコア概念](modules/core-concepts.md) - モジュールの核心的な概念とアーキテクチャ
3. [Event ラッパークラス詳解](modules/event-wrapper.md) - Event オブジェクトの完全な説明
4. [モジュールのベストプラクティス](modules/best-practices.md) - 高品質なモジュールを開発するための提案
5. [データモデル層（ORM）](orm.md) - モジュール開発の応用編：宣言的モデル、自動テーブル作成と CRUD

### アダプター開発

1. [アダプター開発入門](adapters/getting-started.md) - 最初のアダプターを作成する
2. [アダプターのコア概念](adapters/core-concepts.md) - アダプターの核心的な概念（start() の2つの書き方と PollingAdapter / WebhookAdapter 接続モード基底クラスを含む）
3. [SendDSL 詳解](adapters/send-dsl.md) - Send メッセージ送信 DSL の完全な説明
4. [イベントコンバーター](adapters/converter.md) - イベントコンバーターの実装
5. [アダプターのベストプラクティス](adapters/best-practices.md) - 高品質なアダプターを開発するための提案

### テストとトラブルシューティング

1. [モジュールテスト（ErisPulse-Testing）](testing.md) - TestBot、イベントファクトリとアサーションインターフェース

### 一般的な規格

1. [設定と UI メタデータ](configuration.md) - 宣言的設定：widget / 条件付き表示・非表示 / 値の形式 / 互換性契約（アダプターとモジュール共通）

### 公開ガイド

- [公開とモジュールストアガイド](publishing.md) - あなたの作品を PyPI と ErisPulse モジュールストアに公開する

## 開発の準備

開発を始める前に、以下を確認してください：

1. [基本概念](../getting-started/basic-concepts.md)を読んでいること
2. [イベント処理](../getting-started/event-handling.md)に精通していること
3. 開発環境（Python >= 3.10）がインストールされていること
4. ErisPulse SDK がインストールされていること

## 開発タイプの選択

ニーズに応じて適切な開発タイプを選択してください：

| 開発タイプ | 適用シーン | 入門ガイド |
|---------|---------|---------|
| **モジュール開発** | ボット機能の拡張、ビジネスロジックの実装、コマンドとメッセージ処理の提供 | [モジュール開発入門](modules/getting-started.md) |
| **アダプター開発** | 新しいメッセージプラットフォームへの接続、クロスプラットフォーム通信の実現、プラットフォーム固有機能の提供 | [アダプター開発入門](adapters/getting-started.md) |

> ボットの機能を拡張したい場合（コマンドの追加やメッセージ処理など）は、**モジュール開発**を選択してください。ボットを新しいプラットフォームに接続する必要がある場合は、**アダプター開発**を選択してください。

## 開発ツール

### プロジェクトテンプレート

ErisPulse は参考としてサンプルプロジェクトを提供しています：

- [モジュールサンプル](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module) - モジュールの完全なプロジェクト構造（コマンド / 設定 / ORM / 依存性注入）
- [Web 機能サンプル](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module-web) - ルーティングデコレーター / ミドルウェア / WebSocket フック / router.app エスケープハッチ
- [インタラクション応用サンプル](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module-interactive) - メッセージトランザクションと受領確認 / ORM 複合一意制約とトランザクション / リクエスト承認 / 送信チェーン
- [運用ガバナンスサンプル](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module-ops) - スレッドタスクの帰属 / 遅延タスク / メモリチェック / プライバシースイッチ
- [アダプターサンプル](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter) - アダプターの完全なプロジェクト構造（[ポーリング](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter-polling) / [Webhook](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter-webhook) バリアントもあり）

### 開発モード

ホットリロードモードで開発すると、コード変更後に自動的にリロードされます：

```bash
epsdk run main.py --reload
```

### デバッグのコツ

`config/config.toml` で DEBUG または TRACE レベルのログを有効にします：

```toml
[ErisPulse.logger]
# DEBUG: モジュールのロード、ルート登録などの開発デバッグ情報を出力
# TRACE: 最低レベル。イベントディスパッチ、ストレージへの書き込み、遅延ロードなどフレームワーク内部の詳細な流れを出力
level = "DEBUG"
```

## モジュールの公開

完全な公開フローについては [公開とモジュールストアガイド](publishing.md) を参照してください。PyPI の公開手順や ErisPulse モジュールストアへの提出フローなどが含まれます。

## 関連ドキュメント

- [標準規格](../standards/) - 互換性を確保するための技術標準
- [プラットフォーム特性ガイド](../platform-guide/) - 各プラットフォームアダプターの特性を理解する