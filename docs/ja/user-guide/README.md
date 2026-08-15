# ユーザー使用ガイド

本ガイドでは、ErisPulse プロジェクトのインストール、設定、および管理について案内します。

## コンテンツ一覧

| 文書 | 説明 |
|------|------|
| [インストールと設定](installation.md) | システム要件、インストール方法 (pip/uv/Docker)、インストールの検証 |
| [ErisPulse-App スマートフォン/デスクトップクライアント](../ecosystem/app.md) | 公式クライアント：スマートフォン / デスクトップ直接実行、ネイティブインターフェースでの ErisPulse インスタンス管理 |
| [CLI コマンドリファレンス](cli-reference.md) | `epsdk` コマンドラインツールの完全な使用説明 |
| [設定ファイルの説明](configuration.md) | `config/config.toml` 各設定項目の詳細説明 |
| [デプロイガイド](deployment.md) | Docker 部署、systemd サービス、SSL 設定 |

## クイックリファレンス

### コマンド

| コマンド | 説明 |
|------|------|
| `epsdk init` | プロジェクトを初期化する（`-q` で高速モード、`-n` で名前を指定） |
| `epsdk install <パッケージ名>` | モジュール/アダプターをインストールする（引数なしで対話モードに入る） |
| `epsdk run main.py` | プロジェクトを実行する（`--reload` でホットリロードモード） |
| `epsdk list` | インストール済みのモジュール/アダプターを一覧表示する |
| `epsdk upgrade <パッケージ名>` | モジュール/アダプターをアップグレードする |
| `epsdk doctor` | 環境を診断する（Python/バックエンド/設定/PyPI 接続性） |

> 完全なコマンドリストとパラメータの説明については、[CLI コマンドリファレンス](cli-reference.md)を参照してください。

### 共通設定の場所

| 設定項目 | 説明 | 詳細 |
|--------|------|------|
| `[ErisPulse.server]` | サーバー設定（ホスト、ポート） | [設定ファイルの説明](configuration.md#サーバー設定) |
| `[ErisPulse.logger]` | ログ設定（レベル、出力ファイル） | [設定ファイルの説明](configuration.md#ログ設定) |
| `[ErisPulse.framework]` | フレームワーク設定（遅延読み込み） | [設定ファイルの説明](configuration.md#フレームワーク設定) |
| `[ErisPulse.event.command]` | コマンドイベント設定（プレフィックス） | [設定ファイルの説明](configuration.md#イベント設定) |
| `[アダプター名]` | 各アダプターの固有設定 | [プラットフォーム特性ガイド](../platform-guide/) |

## 関連ドキュメント

- [クイックスタート](../quick-start.md) - 入門ガイド
- [初心者向けガイド](../getting-started/) - 入門チュートリアル
- [開発者向けガイド](../developer-guide/) - カスタムモジュールやアダプタの開発
- [API リファレンス](../api-reference/) - API ドキュメント