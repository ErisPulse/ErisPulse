# ErisPulse ドキュメント

ErisPulse は、アダプターを介してさまざまなプラットフォームと相互作用し、拡張可能な多プラットフォームのメッセージ処理フレームワークです。機能拡張に柔軟なモジュールシステムを提供します。

> 用語が理解できない場合は、[用語集](terminology.md)を参照して分かりやすい説明をご覧ください。

## ドキュメントナビゲーション

### クイックスタート

- [クイックスタートガイド](quick-start.md) - ErisPulse のインストールと実行の入門ガイド

### アーキテクチャ概要

- [アーキテクチャ概要](architecture.md) - サンプル画像を用いた SDK のコアアーキテクチャ、初期化プロセス、イベント処理、およびライフサイクルの理解

### 初心者向け

ErisPulse を初めて使用する場合は、以下の順序で読むことをお勧めします：

1. [入門ガイド概要](getting-started/README.md)
2. [最初のロボットの作成](getting-started/first-bot.md)
3. [基本概念](getting-started/basic-concepts.md)
4. [イベント処理の入門](getting-started/event-handling.md)
5. [一般的なタスクの例](getting-started/common-tasks.md)

### ユーザー使用ガイド

- [インストールと設定](user-guide/installation.md)
- [CLI コマンドリファレンス](user-guide/cli-reference.md)
- [設定ファイルの説明](user-guide/configuration.md)
- [デプロイガイド](user-guide/deployment.md)

### デベロッパー向けガイド

#### モジュール開発

- [モジュール開発の入門](developer-guide/modules/getting-started.md)
- [モジュールのコアコンセプト](developer-guide/modules/core-concepts.md)
- [Event 包装クラスの詳細](developer-guide/modules/event-wrapper.md)
- [モジュール開発のベストプラクティス](developer-guide/modules/best-practices.md)

#### アダプター開発

- [アダプター開発の入門](developer-guide/adapters/getting-started.md)
- [アダプターのコアコンセプト](developer-guide/adapters/core-concepts.md)
- [SendDSL の詳細](developer-guide/adapters/send-dsl.md)
- [アダプター開発のベストプラクティス](developer-guide/adapters/best-practices.md)

#### リリース

- [リリースとモジュールストアガイド](developer-guide/publishing.md) - モジュールやアダプターを ErisPulse モジュールストアに公開する方法

### プラットフォーム機能ガイド

- [プラットフォーム機能説明](platform-guide/README.md)
- [雲湖プラットフォーム機能](platform-guide/yunhu.md)
- [Telegram プラットフォーム機能](platform-guide/telegram.md)
- [OneBot11 プラットフォーム機能](platform-guide/onebot11.md)
- [OneBot12 プラットフォーム機能](platform-guide/onebot12.md)
- [メールプラットフォーム機能](platform-guide/email.md)

### API リファレンス

- [コアモジュール API](api-reference/core-modules.md)
- [イベントシステム API](api-reference/event-system.md)
- [アダプターシステム API](api-reference/adapter-system.md)

### 技術標準

- [イベント変換標準](standards/event-conversion.md)
- [API レスポンス標準](standards/api-response.md)
- [送信メソッド規格](standards/send-method-spec.md)

### 高度なトピック

- [起動プロセスと手動制御](advanced/startup.md) - 起動プロセスの分解と完全な手動起動
- [遅延ロードシステム](advanced/lazy-loading.md)
- [ライフサイクル管理](advanced/lifecycle.md)
- [ルーティングシステム](advanced/router.md)
- [MessageBuilder の詳細](advanced/message-builder.md)
- [セッション型システム](advanced/session-types.md)
- [Conversation 多段対話](advanced/conversation.md)

### AI支援開発

- [AI支援開発](ai-support/README.md)

### スタイルガイド

- [ドキュメントスタイルガイド](styleguide/docstring.md)

## 開発方法

ErisPulse は、2 つの開発方法をサポートしています：

### 1. モジュール開発（推奨）

独立したモジュールパッケージを作成し、パッケージマネージャーを使ってインストールして使用します。この方法は、公開される機能の配布と管理に便利です。

### 2. インライン開発

ErisPulse のコードをプロジェクトに直接埋め込み、独立したモジュールを作成する必要はありません。この方法は、迅速なプロトタイピングやプロジェクト内専用機能に適しています。

例：

```python
# 直接埋め込み使用
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

# コマンドハンドラの登録
@command("hello")
async def hello_handler(event):
    await event.reply("こんにちは！")

# SDK を実行し、維持 | 異スレッド環境で実行する必要があります
asyncio.run(sdk.run(keep_running=True))
```

## ヘルプの取得

- GitHub リポジトリ: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題報告: Issue を送信
- 技術的な議論: Discussions をご覧ください

## 関連リンク

- [OneBot12 標準](https://12.onebot.dev/)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Русский](README.ru.md)