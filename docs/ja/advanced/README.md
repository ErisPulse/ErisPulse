# 高級トピック

このディレクトリには、ErisPulseフレームワークの高度な機能と詳細なトピックが含まれています。

## ドキュメントリスト

- [起動プロセスと手動制御](startup.md) - 起動フローの分解（Finder/Loader/Manager/Router）と手動による完全な起動
- [ラジロードシステム](lazy-loading.md) - ラジロードモジュールシステムの仕組み、設定、イベント駆動によるラジアクティベーション（activate_on）
- [統一制御面（scope）](scope.md) - 6次元の権限制御：モジュールの可用性 / イベントのアクセス制御 / コマンドACL / テキストフィルタ / パラメータの上書き / 出力アクション
- [国際化 (i18n)](i18n.md) - 多言語サポート、翻訳の登録と言語検出
- [ライフサイクル管理](lifecycle.md) - ライフサイクルイベントシステムの使用方法
- [ルートマネージャー](router.md) - HTTPとWebSocketのルート管理
- [HTTPクライアント](http-client.md) - 統一HTTPリクエストクライアント
- [MessageBuilderの詳細](message-builder.md) - OneBot12メッセージセグメントビルダーの二重モードの使い方
- [SQLクエリビルダー](sql-builder.md) - 一般的なSQLチェーンクエリビルダーとストレージバックエンドの抽象化
- [セッション型システム](../standards/session-types.md) - セッション型の定義、マッピング、およびカスタム型の登録
- [Conversationマルチラウンド会話](conversation.md) - マルチラウンド会話コンテキストの対話方法

> [!NOTE]
> Dashboard視窗の登録、Takumi画像レンダリングなどの**サードパーティエコシステムモジュール**のドキュメントは、[エコシステムモジュール](../ecosystem/README.md)ディレクトリに移動されました。

## 対象読者

これらのドキュメントは、以下の開発者向けです：

- ErisPulseの基本機能に精通している開発者
- フレームワークの内部メカニズムを深く理解したい開発者
- パフォーマンスを最適化または複雑な機能を実装したい開発者

## 前提知識

このディレクトリのドキュメントを読む前に、以下の内容を理解しておくことを推奨します：

- [基本概念](../getting-started/basic-concepts.md)
- [イベント処理入門](../getting-started/event-handling.md)
- [モジュール開発ガイド](../developer-guide/modules/README.md)