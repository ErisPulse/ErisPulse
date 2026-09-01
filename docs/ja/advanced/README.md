# 高級トピック

このディレクトリには、ErisPulseフレームワークの高度な機能と詳細なトピックが含まれています。

## ドキュメントリスト

- [起動プロセスと手動制御](startup.md) - 起動の流れを分解（Finder/Loader/Manager/Router）と手動による完全な起動
- [ラジロードシステム](lazy-loading.md) - ラジロードモジュールシステムの動作原理、設定、イベント駆動による遅延有効化（activate_on）
- [統一制御面（scope）](scope.md) - 5次元の権限制御：モジュールの可用性 / イベントのアクセス制限 / コマンド ACL / テキストフィルタ / パラメータの上書き
- [国際化 (i18n)](i8n.md) - 多言語サポート、翻訳の登録、言語の検出
- [ライフサイクル管理](lifecycle.md) - ライフサイクルイベントシステムの使用方法
- [ルーティングマネージャー](router.md) - HTTP および WebSocket のルーティング管理
- [HTTP クライアント](http-client.md) - 統一された HTTP リクエストクライアント
- [MessageBuilder 詳解](message-builder.md) - OneBot12 メッセージセグメントビルダの二つのモードの使い方
- [SQL クエリビルダ](sql-builder.md) - 一般的な SQL チェーン式クエリビルダおよびストレージバックエンドの抽象化
- [セッションタイプシステム](../standards/session-types.md) - セッションタイプの定義、マッピング、カスタムタイプの登録
- [Conversation 多段対話](conversation.md) - 多段対話コンテキストのインタラクション方法

> [!NOTE]
> Dashboard 視窗の登録、Takumi による画像レンダリングなどの**サードパーティエコシステムモジュール**のドキュメントは、[エコシステムモジュール](../ecosystem/README.md)ディレクトリに移動しました。

## 対象読者

これらのドキュメントは以下の開発者向けです：

- ErisPulseの基本機能に精通している開発者
- フレームワークの内部メカニズムを深く理解したい開発者
- 性能を最適化したり、複雑な機能を実装したい開発者

## 前提知識

このディレクトリのドキュメントを読む前に、以下の内容を理解しておくことをお勧めします：

- [基礎概念](../getting-started/basic-concepts.md)
- [イベント処理入門](../getting-started/event-handling.md)
- [モジュール開発ガイド](../developer-guide/modules/)