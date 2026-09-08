# 高級トピック

このディレクトリには、ErisPulse フレームワークの高度な機能と詳細なトピックが含まれています。

## ドキュメントリスト

- [起動プロセスと手動制御](startup.md) - 起動リンクの分解（Finder/Loader/Manager/Router）と手動での完全起動
- [遅延読み込みシステム](lazy-loading.md) - 遅延読み込みモジュールシステムの動作原理、設定、イベント駆動による遅延アクティベーション（activate_on）
- [スコープ（scope）](scope.md) - 3次元スコープ制御：モジュールの可用性 / イベントのアクセス制御 / 出力アクションの制限（メソッドレベルの細かいルールとバインディング継承 merge を含む）
- [所有権（owner）システム](ownership.md) - リソースの所有権と自動回収：owner コンテキストメカニズム、所有リソースの全体像、アンロード時のクリーンアップシーケンスと設計の境界
- [国際化 (i18n)](i18n.md) - 多言語サポート、翻訳の登録と言語の検出
- [ライフサイクル管理](lifecycle.md) - ライフサイクルイベントシステムの使用方法
- [ルートマネージャー](router.md) - HTTP および WebSocket ルートの管理
- [HTTP クライアント](http-client.md) - 統一された HTTP リクエストクライアント
- [MessageBuilder 詳解](message-builder.md) - OneBot12 メッセージセグメントビルダーの二重モードの使用法
- [SQL クエリビルダー](sql-builder.md) - 一般的な SQL チェーン式クエリビルダーとストレージバックエンドの抽象化
- [ストレージバックエンド](storage-backends.md) - sqlite / mysql / postgres の非同期ネイティブストレージバックエンドの選択、設定、切り替え
- [セッションタイプシステム](../standards/session-types.md) - セッションタイプの定義、マッピング、およびカスタムタイプの登録
- [Conversation 多段対話](conversation.md) - 多段対話コンテキストの対話メソッド

> [!NOTE]
> Dashboard 視窗の登録、Takumi 画像のレンダリングなどの **サードパーティエコシステムモジュール** のドキュメントは、[エコシステムモジュール](../ecosystem/README.md) ディレクトリに移動されました。

## 対象読者

これらのドキュメントは以下の開発者向けです：

- ErisPulse の基本機能に既に精通している開発者
- フレームワークの内部メカニズムを深く理解したい開発者
- パフォーマンスの最適化や複雑な機能の実装を必要とする開発者

## 前提知識

このディレクトリのドキュメントを読む前に、以下の内容を理解しておくことをお勧めします：

- [基本概念](../getting-started/basic-concepts.md)
- [イベント処理の入門](../getting-started/event-handling.md)
- [モジュール開発ガイド](../developer-guide/modules/)