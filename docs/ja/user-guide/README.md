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

## 快速参考

### 常用コマンド

| コマンド | 説明 |
|------|------|
| `epsdk init` | プロジェクトを初期化（`-q` はクイックモード、`-n` は名前を指定） |
| `epsdk install <パッケージ名>` | モジュール/アダプターをインストール（パラメータなしで対話モードに入る） |
| `epsdk config <名前>` | 対話形式でアダプター/モジュールの宣言型設定項目を設定 |
| `epsdk run main.py` | プロジェクトを実行（`--reload` はホットリロードモード） |
| `epsdk list` | インストール済みのモジュール/アダプターを一覧表示 |
| `epsdk upgrade <パッケージ名>` | モジュール/アダプターをアップグレード |
| `epsdk doctor` | 環境診断（Python/バックエンド/設定/PyPI 接続性） |

> 完全なコマンドリストとパラメータの説明は [CLI コマンドリファレンス](cli-reference.md) を参照してください。

### 一般的な設定位置

| 設定項目 | 説明 | 詳細 |
|--------|------|------|
| `[ErisPulse.server]` | サーバー設定（ホスト、ポート） | [設定ファイルの説明](configuration.md#サーバー設定) |
| `[ErisPulse.logger]` | ログ設定（レベル、出力ファイル） | [設定ファイルの説明](configuration.md#ログ設定) |
| `[ErisPulse.framework]` | フレームワーク設定（遅延読み込み） | [設定ファイルの説明](configuration.md#フレームワーク設定) |
| `[ErisPulse.event.command]` | コマンドイベント設定（プレフィックス） | [設定ファイルの説明](configuration.md#イベント設定) |
| `[アダプター名]` | 各アダプターの固有設定 | [プラットフォーム機能ガイド](../platform-guide/) |

## 関連ドキュメント

- [クイックスタート](../quick-start.md) - 入門ガイド
- [初心者向けガイド](../getting-started/) - 入門チュートリアル
- [開発者向けガイド](../developer-guide/) - カスタムモジュールやアダプタの開発
- [API リファレンス](../api-reference/) - API ドキュメント