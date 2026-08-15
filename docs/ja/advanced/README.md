# 詳細トピック

このディレクトリには ErisPulse フレームワークの高度な機能と深掘りトピックが含まれています。

## ドキュメント一覧

- [起動プロセスと手動制御](docs/ja/startup.md) - 起動フロー分解（Finder/Loader/Manager/Router）と手動による完全起動
- [遅延読み込みシステム](docs/ja/lazy-loading.md) - 遅延読み込みモジュールシステムの仕組みと設定
- [モジュールスコープシステム](docs/ja/scope.md) - モジュールとアダプタ Bot/プラットフォームのバインディングと隔離
- [国際化 (i18n)](docs/ja/i18n.md) - 多言語サポート、翻訳登録、言語検出
- [ライフサイクル管理](docs/ja/lifecycle.md) - ライフサイクルイベントシステムの使用方法
- [ルーター管理](docs/ja/router.md) - HTTP および WebSocket ルーティング管理
- [HTTP クライアント](docs/ja/http-client.md) - 統一 HTTP リクエストクライアント
- [MessageBuilder 詳解](docs/ja/message-builder.md) - OneBot12 メッセージセグメントビルダーの双モード使い方
- [SQL クエリビルダー](docs/ja/sql-builder.md) - 汎用的な SQL チェーンクエリビルダーおよびストレージバックエンド抽象
- [セッションタイプシステム](docs/ja/session-types.md) - セッションタイプの定義、マッピング、カスタムタイプ登録
- [Conversation 多会話](docs/ja/conversation.md) - 多会話コンテキストのインタラクション方法

> [!NOTE]
> Dashboard ウィンドウ登録、Takumi 画像レンダリングなど **サードパーティ生態モジュール** のドキュメントは、[生態モジュール](../ecosystem/README.md) ディレクトリへ移動しました。

## 対象読者

これらのドキュメントは、以下の開発者に適しています。

- ErisPulse の基本機能に慣れている開発者
- フレームワークの内部メカニズムを深く理解したい開発者
- パフォーマンスの最適化や複雑な機能の実装が必要な開発者

請直接返回翻译后的完整Markdown内容，不要包含任何其他文字。

再次提醒：如果文档包含语言切换行（各语言名称用 `` | `` 分隔的行），务必严格遵守上方第8条的格式要求，不要写出 ``[**Label**](file)`` 这类错误格式。

## 前提知識

このディレクトリのドキュメントを読む前に、以下の内容について理解しておくことを推奨します。

- [基礎概念](../getting-started/basic-concepts.md)
- [イベント処理入門](../getting-started/event-handling.md)
- [モジュール開発ガイド](../developer-guide/modules/)