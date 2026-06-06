# API リファレンス

このディレクトリには、ErisPulse フレームワークの API リファレンスドキュメントが含まれています。

## ドキュメント一覧

| ドキュメント | 説明 |
|------|------|
| [コアモジュール API](core-modules.md) | Storage、Config、Logger、Adapter、Module、Lifecycle、Router、HTTP Client の API クイックリファレンス |
| [イベントシステム API](event-system.md) | Command、Message、Notice、Request、Meta イベントモジュールの API リファレンス |
| [アダプターシステム API](adapter-system.md) | Adapter マネージャー、SendDSL、ミドルウェア、Bot ステータス管理の API リファレンス |
| [自動生成 API](auto_api/README.md) | ソースコード docstring から自動生成された完全な API ドキュメント |

> 手動作成された API ドキュメントは主に使用例とクイックリファレンスに重点を置いています。自動生成された API ドキュメントには完全なクラス/メソッドの署名が含まれており、両者は互いに補完し合います。

## モジュール概要

### コアモジュール

| モジュール | アクセスパス | 説明 |
|------|------|------|
| `sdk.storage` | `sdk.storage` | SQLite ベースのキーバリューストレージ + SQL チェーンクエリ |
| `sdk.config` | `sdk.config` | TOML 形式の設定管理 |
| `sdk.logger` | `sdk.logger` | モジュールログシステム、サブロガーをサポート |
| `sdk.adapter` | `sdk.adapter` | マルチプラットフォームアダプター管理 |
| `sdk.module` | `sdk.module` | モジュール登録、ロード、アンロード管理 |
| `sdk.lifecycle` | `sdk.lifecycle` | ライフサイクルイベント管理 |
| `sdk.router` | `sdk.router` | HTTP/WebSocket ルーティング管理 |
| `sdk.client` | `sdk.client` | 統一 HTTP/WS クライアント |

### イベントシステム

| モジュール | インポートパス | 説明 |
|------|------|------|
| `command` | `ErisPulse.Core.Event.command` | コマンド処理（プレフィックス解析、エイリアス） |
| `message` | `ErisPulse.Core.Event.message` | メッセージイベント（プライベートチャット、グループチャット、@メッセージ） |
| `notice` | `ErisPulse.Core.Event.notice` | 通知イベント（フレンド、グループメンバー変化） |
| `request` | `ErisPulse.Core.Event.request` | リクエストイベント（フレンドリクエスト、グループ招待） |
| `meta` | `ErisPulse.Core.Event.meta` | メタイベント（接続、切断、ハートビート） |

### 基底クラス

| 基底クラス | インポートパス | 説明 |
|------|------|------|
| `BaseModule` | `ErisPulse.Core.Bases.module.BaseModule` | モジュール基底クラス（on_load/on_unload） |
| `BaseAdapter` | `ErisPulse.Core.Bases.adapter.BaseAdapter` | アダプター基底クラス（start/shutdown/call_api） |

## 関連ドキュメント

- [コアコンセプト](../getting-started/basic-concepts.md) - フレームワークのコアコンセプトを理解する
- [モジュール開発ガイド](../developer-guide/modules/) - カスタムモジュールの開発
- [アダプター開発ガイド](../developer-guide/adapters/) - プラットフォームアダプターの開発
- [高度なトピック](../advanced/) - ルーティング、HTTP クライアント、SQL ビルダーなどの詳細なドキュメント