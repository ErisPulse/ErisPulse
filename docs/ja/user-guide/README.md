# ユーザーガイド

このガイドは、ErisPulse プロジェクトのインストール、設定、および管理を支援します。

## 目次

| ドキュメント | 説明 |
|------|------|
| [インストールと設定](installation.md) | システム要件、インストール方法（pip/uv/Docker）、インストールの確認 |
| [CLI コマンドリファレンス](cli-reference.md) | `epsdk` コマンドラインツールの完全な使用説明 |
| [設定ファイル説明](configuration.md) | `config/config.toml` 各設定項目の詳細説明 |
| [デプロイメントガイド](deployment.md) | Docker 部署、systemd サービス、SSL 設定 |

## クイックリファレンス

### 一般的なコマンド

| コマンド | 説明 |
|------|------|
| `epsdk init` | プロジェクトの初期化（`-q` はクイックモード、`-n` は名前を指定） |
| `epsdk install <パッケージ名>` | モジュール/アダプターのインストール（引数なしで対話モードに入ります） |
| `epsdk run main.py` | プロジェクトの実行（`--reload` はリロードモード） |
| `epsdk list` | インストール済みのモジュール/アダプターを一覧表示 |
| `epsdk upgrade <パッケージ名>` | モジュール/アダプターのアップグレード |
| `epsdk doctor` | 環境の診断（Python/バックエンド/設定/PyPI 連通性） |

> 完全なコマンドリストとパラメータの説明については、[CLI コマンドリファレンス](cli-reference.md)を参照してください。

### 一般的な設定場所

| 設定項目 | 説明 | 詳細 |
|--------|------|------|
| `[ErisPulse.server]` | サーバー設定（ホスト、ポート） | [設定ファイル説明](configuration.md#サーバー設定) |
| `[ErisPulse.logger]` | ログ設定（レベル、出力ファイル） | [設定ファイル説明](configuration.md#ログ設定) |
| `[ErisPulse.framework]` | フレームワーク設定（遅延読み込み） | [設定ファイル説明](configuration.md#フレームワーク設定) |
| `[ErisPulse.event.command]` | コマンドイベント設定（プレフィックス） | [設定ファイル説明](configuration.md#イベント設定) |
| `[アダプター名]` | 各アダプターの固有設定 | [プラットフォームガイド](../platform-guide/) |

## 関連ドキュメント

- [クイックスタート](../quick-start.md) - クイックスタートガイド
- [初心者入門](../getting-started/) - 入門チュートリアル
- [開発者ガイド](../developer-guide/) - カスタムモジュールとアダプターの開発
- [API リファレンス](../api-reference/) - API ドキュメント