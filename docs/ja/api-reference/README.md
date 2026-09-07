# API リファレンス

このディレクトリには、ErisPulse フレームワークの API リファレンスドキュメントが含まれています。

## ドキュメントリスト

| ドキュメント | 説明 |
|------|------|
| [コアモジュール API](core-modules.md) | Storage、Config、Logger、Adapter、Module、Lifecycle、Router、HTTP Client の API 速見リファレンス |
| [イベントシステム API](event-system.md) | Command、Message、Notice、Request、Meta イベントモジュールの API リファレンス |
| [アダプターシステム API](adapter-system.md) | Adapter マネージャー、SendDSL、ミドルウェア、Bot 状態管理の API リファレンス |
| [自動生成 API](auto_api/README.md) | ソースコードの docstring から自動生成された完全な API ドキュメント |

> 手動で書かれた API ドキュメントは、使い方の例と速見リファレンスに重点を置いています。一方、自動生成された API ドキュメントは、完全なクラス/メソッドのシグネチャを含んでおり、両者は補完し合います。

## モジュール概要

### コアモジュール

| モジュール | アクセスパス | 説明 |
|------|---------|------|
| `sdk.storage` | `sdk.storage` | SQLite を基にしたキー/値ストア + SQL チェインクエリ |
| `sdk.config` | `sdk.config` | TOML 形式の設定管理 |
| `sdk.logger` | `sdk.logger` | モジュール化されたログシステム、サブロガーをサポート |
| `sdk.adapter` | `sdk.adapter` | 複数プラットフォームのアダプタ管理 |
| `sdk.module` | `sdk.module` | モジュールの登録、ロード、アンロード管理 |
| `sdk.lifecycle` | `sdk.lifecycle` | ライフサイクルイベント管理 |
| `sdk.router` | `sdk.router` | HTTP/WebSocket ルーティング管理 |
| `sdk.client` | `sdk.client` | 統一された HTTP/WS クライアント |

### イベントシステム

| モジュール | インポートパス | 説明 |
|------|---------|------|
| `command` | `ErisPulse.Core.Event.command` | コマンド処理（プレフィックス解析、エイリアス） |
| `message` | `ErisPulse.Core.Event.message` | メッセージイベント（プライベートチャット、グループチャット、メンション） |
| `notice` | `ErisPulse.Core.Event.notice` | 通知イベント（友達、グループメンバーの変更） |
| `request` | `ErisPulse.Core.Event.request` | リクエストイベント（友達リクエスト、グループ招待） |
| `meta` | `ErisPulse.Core.Event.meta` | メタイベント（接続、切断、ハートビート） |

### 基底クラス

| 基底クラス | インポートパス | 説明 |
|------|---------|------|
| `BaseModule` | `ErisPulse.Core.Bases.module.BaseModule` | モジュールの基底クラス（on_load/on_unload） |
| `BaseAdapter` | `ErisPulse.Core.Bases.adapter.BaseAdapter` | アダプタの基底クラス（start/shutdown/call_api） |

## 関連ドキュメント

- [基本概念](../getting-started/basic-concepts.md) - フレームワークの基本概念を理解する
- [モジュール開発ガイド](../developer-guide/modules/) - カスタムモジュールの開発
- [アダプタ開発ガイド](../developer-guide/adapters/) - プラットフォームアダプタの開発
- [高度なトピック](../advanced/) - ルーティング、HTTPクライアント、SQLビルダーなどに関する詳細ドキュメント