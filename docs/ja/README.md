# ErisPulse ドキュメント

ErisPulse は拡張可能なマルチプラットフォームメッセージ処理フレームワークです。アダプターを介した異なるプラットフォームとのやり取りをサポートし、機能拡張用の柔軟なモジュールシステムを提供します。

> 分からない用語がありますか？[用語集](terminology.md) で分かりやすい説明を確認してください。

## ドキュメントナビゲーション

### クイックスタート

- [クイックスタートガイド](quick-start.md) - ErisPulse のインストールと実行に関する入門ガイド

### アーキテクチャ概要

- [アーキテクチャ概要](architecture.md) - ビジュアル図を通じて SDK のコアアーキテクチャ、初期化プロセス、イベント処理、ライフサイクルを理解する

### 初心者向けガイド

初めて ErisPulse を使用する場合は、以下の順序で読むことをお勧めします：

1. [入門ガイド概要](getting-started/README.md)
2. [最初のボットを作成する](getting-started/first-bot.md)
3. [基本概念](getting-started/basic-concepts.md)
4. [イベント処理の入門](getting-started/event-handling.md)
5. [一般的なタスクの例](getting-started/common-tasks.md)

### ユーザーガイド

- [インストールと設定](user-guide/installation.md)
- [CLI コマンドリファレンス](user-guide/cli-reference.md)
- [設定ファイルの説明](user-guide/configuration.md)
- [デプロイガイド](user-guide/deployment.md)

### 開発者ガイド

#### モジュール開発

- [モジュール開発の入門](developer-guide/modules/getting-started.md)
- [モジュールのコア概念](developer-guide/modules/core-concepts.md)
- [Event ラッパークラスの詳細](developer-guide/modules/event-wrapper.md)
- [モジュール開発のベストプラクティス](developer-guide/modules/best-practices.md)

#### アダプター開発

- [アダプター開発の入門](developer-guide/adapters/getting-started.md)
- [アダプターのコア概念](developer-guide/adapters/core-concepts.md)
- [SendDSL の詳細](developer-guide/adapters/send-dsl.md)
- [アダプター開発のベストプラクティス](developer-guide/adapters/best-practices.md)


#### リリース

- [公開とモジュールストアのガイド](developer-guide/publishing.md) - モジュールやアダプターを ErisPulse モジュールストアに公開する

### プラットフォーム機能ガイド

- [プラットフォーム機能の説明](platform-guide/README.md)
- [雲湖 (Yunhu) プラットフォームの機能](platform-guide/yunhu.md)
- [Telegram プラットフォームの機能](platform-guide/telegram.md)
- [OneBot11 プラットフォームの機能](platform-guide/onebot11.md)
- [OneBot12 プラットフォームの機能](platform-guide/onebot12.md)
- [メールプラットフォームの機能](platform-guide/email.md)

### API リファレンス

- [コアモジュール API](api-reference/core-modules.md)
- [イベントシステム API](api-reference/event-system.md)
- [アダプターシステム API](api-reference/adapter-system.md)

### 技術標準

- [イベント変換の標準](standards/event-conversion.md)
- [API レスポンスの標準](standards/api-response.md)
- [送信メソッドの仕様](standards/send-method-spec.md)

### 高度なトピック

- [遅延読み込み (Lazy Loading) システム](advanced/lazy-loading.md)
- [ライフサイクル管理](advanced/lifecycle.md)
- [ルーティングシステム](advanced/router.md)
- [MessageBuilder の詳細](advanced/message-builder.md)
- [セッションタイプシステム](advanced/session-types.md)
- [Conversation マルチターン対話](advanced/conversation.md)

### AI サポート開発

- [AI サポート開発](ai-support/README.md)

### スタイルガイド

- [ドキュメントスタイルガイド](styleguide/docstring.md)

## 開発手法

ErisPulse は2つの開発手法をサポートしています：

### 1. モジュール開発（推奨）

独立したモジュールパッケージを作成し、パッケージマネージャーを介してインストールして使用します。この方法は配布や管理が容易で、一般に公開する機能に適しています。

### 2. 組み込み開発

ErisPulse のコードをプロジェクトに直接組み込み、独立したモジュールを作成する必要はありません。この方法は迅速なプロトタイピングやプロジェクト内部専用の機能に適しています。

例：

```python
# 直接組み込んで使用する
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

# コマンドハンドラを登録する
@command("hello")
async def hello_handler(event):
    await event.reply("こんにちは！")

# SDK を実行し、実行状態を維持する | 非同期環境で実行する必要があります
asyncio.run(sdk.run(keep_running=True))
```

## ヘルプの入手

- GitHub リポジトリ：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題報告：Issue を提出する
- 技術議論：Discussions を確認する

## 関連リンク

- [OneBot12 標準](https://12.onebot.dev/)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)