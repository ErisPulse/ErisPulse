# 高度なトピック

このディレクトリには、ErisPulse フレームワークの高度な機能と詳細なトピックが含まれています。

## ドキュメント一覧

- [起動プロセスと手動制御](docs/ja/startup.md) - 起動フロー（Finder/Loader/Manager/Router）の分解と手動での完全な起動
- [遅延読み込みシステム](docs/ja/lazy-loading.md) - 遅延読み込みモジュールシステムの仕組みと設定
- [国際化 (i18n)](docs/ja/i18n.md) - 多言語サポート、翻訳登録、言語検出
- [ライフサイクル管理](docs/ja/lifecycle.md) - ライフサイクルイベントシステムの使用方法
- [ルーター管理](docs/ja/router.md) - HTTP および WebSocket ルーティング管理
- [HTTP クライアント](docs/ja/http-client.md) - 統合 HTTP リクエストクライアント
- [MessageBuilder の詳細](docs/ja/message-builder.md) - OneBot12 メッセージセグメントビルダーの二モード使用方法
- [SQL クエリビルダー](docs/ja/sql-builder.md) - 汎用的な SQL チェーンクエリビルダーおよびデータベース抽象化
- [セッションタイプシステム](docs/ja/session-types.md) - セッションタイプの定義、マッピング、カスタムタイプ登録
- [Conversation 多輪会話](docs/ja/conversation.md) - 多輪会話コンテキストのインタラクション方法
- [Dashboard ウィンドウ登録](docs/ja/dashboard-view.md) - モジュール管理ページを Dashboard サイドバーに登録する

## 対象読者

これらのドキュメントは以下の開発者に適しています：

- ErisPulse の基本機能に慣れ親しんだ開発者
- フレームワークの内部メカニズムを深く理解する必要がある開発者
- パフォーマンスの最適化や複雑な機能の実装が必要な開発者

## 前提知識

本ディレクトリのドキュメントを読む前に、以下を先に理解しておくことを推奨します。

- [基本概念](../getting-started/basic-concepts.md)
- [イベント処理の入門](../getting-started/event-handling.md)
- [モジュール開発ガイド](../developer-guide/modules/)