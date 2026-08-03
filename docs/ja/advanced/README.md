# 高度なトピック

このディレクトリには、ErisPulse フレームワークの高度な機能と深掘りトピックが含まれています。

## ドキュメントリスト

- [起動プロセスと手動制御](startup.md) - 起動プロセスの分解（Finder/Loader/Manager/Router）と手動完全起動
- [遅延読み込みシステム](lazy-loading.md) - 遅延読み込みモジュールシステムの動作原理と設定
- [国際化 (i18n)](i18n.md) - 多言語サポート、翻訳登録、言語検出
- [ライフサイクル管理](lifecycle.md) - ライフサイクルイベントシステムの使用方法
- [ルーター管理器](router.md) - HTTP および WebSocket ルーティング管理
- [HTTP クライアント](http-client.md) - 統一 HTTP リクエストクライアント
- [MessageBuilder 详解](message-builder.md) - OneBot12 メッセージセグメントビルダーのダブルモードの使用法
- [SQL クエリビルダー](sql-builder.md) - 汎用 SQL チェーンクエリビルダーおよびストレージバックエンド抽象
- [セッション型システム](session-types.md) - セッション型の定義、マッピング、カスタム型の登録
- [Conversation 多輪対話](conversation.md) - 多輪対話のコンテキストとインタラクション方法

> [!NOTE]
> Dashboard ウィンドウ登録、Takumi 画像レンダリングなどの **サードパーティ生態モジュール** のドキュメントは、[生態モジュール](../ecosystem/README.md) ディレクトリへ移行されました。

## 対象読者

これらのドキュメントは、以下の開発者に適しています。

- ErisPulse の基本機能に慣れている開発者
- フレームワークの内部メカニズムを深く理解する必要がある開発者
- パフォーマンスを最適化したり、複雑な機能を実装したりする必要がある開発者

## 前提知識

このディレクトリのドキュメントを読む前に、以下の内容について理解しておくことを推奨します。

- [基本概念](../getting-started/basic-concepts.md)
- [イベント処理入門](../getting-started/event-handling.md)
- [モジュール開発ガイド](../developer-guide/modules/)