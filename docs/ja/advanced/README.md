# 高度なトピック

このディレクトリには、ErisPulse フレームワークの高度な機能と詳細なトピックが含まれています。

## ドキュメント一覧

- [起動プロセスと手動制御](startup.md) - 起動経路の分解（Finder/Loader/Manager/Router）と手動による完全起動
- [ラジロードシステム](lazy-loading.md) - ラジロードモジュールシステムの動作原理、設定、イベント駆動による遅延活性化（activate_on）
- [スコープ（scope）](scope.md) - 3次元スコープ制御：モジュールの可用性 / イベントのアクセス制限 / 出力アクション制限（メソッドレベルの細かいルールとバインディング継承 merge を含む）
- [所有権（owner）システム](ownership.md) - リソースの所有権と自動回収：ownerコンテキストメカニズム、所有リソースの全体像、アンロードクリーンアップシーケンス、設計境界
- [国際化 (i18n)](i18n.md) - 多言語サポート、翻訳登録、言語検出
- [ライフサイクル管理](lifecycle.md) - ライフサイクルイベントシステムの使用方法
- [ルートマネージャー](router.md) - HTTP および WebSocket ルート管理
- [HTTP クライアント](http-client.md) - 統一された HTTP リクエストクライアント
- [MessageBuilder 詳解](message-builder.md) - OneBot12 メッセージセグメントビルダーの二つのモードの使い方
- [SQL クエリビルダー](sql-builder.md) - 一般的な SQL チェーン式クエリビルダーとストレージバックエンドの抽象化
- [セッションタイプシステム](../standards/session-types.md) - セッションタイプの定義、マッピング、およびカスタムタイプの登録
- [Conversation 多段対話](conversation.md) - 多段対話コンテキストのインタラクション方法

> [!NOTE]
> Dashboard 視窗登録、Takumi 画像レンダリングなどの **サードパーティエコシステムモジュール** のドキュメントは、[エコシステムモジュール](../ecosystem/README.md) 目録に移動しました。

## 対象読者

このドキュメントは以下の開発者を対象としています：

- ErisPulse の基本機能に精通している開発者
- フレームワークの内部メカニズムを深く理解したい開発者
- 性能を最適化したり、複雑な機能を実装したい開発者

## 前提知識

このディレクトリのドキュメントを読む前に、以下の内容を事前に理解しておくことを推奨します：

- [基本概念](../getting-started/basic-concepts.md)
- [イベント処理の入門](../getting-started/event-handling.md)
- [モジュール開発ガイド](../developer-guide/modules/)