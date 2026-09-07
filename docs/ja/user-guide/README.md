# ユーザー使用ガイド

このガイドは、ErisPulse プロジェクトのインストール、設定、および管理方法を説明します。

## 内容リスト

| ドキュメント | 説明 |
|------|------|
| [インストールと設定](installation.md) | システム要件、インストール方法（pip/uv/Docker）、インストールの確認 |
| [ErisPulse-App モバイル/デスクトップクライアント](../ecosystem/app.md) | 公式クライアント：モバイル/デスクトップで直接実行、ネイティブインターフェースで ErisPulse インスタンスを管理 |
| [CLI コマンドリファレンス](cli-reference.md) | `epsdk` コマンドラインツールの完全な使用説明 |
| [設定ファイルの説明](configuration.md) | `config/config.toml` の各設定項目の詳細説明 |
| [デプロイガイド](deployment.md) | Docker 部署、systemd サービス、SSL 設定 |

## 快速参考

### 常用コマンド

| コマンド | 説明 |
|------|------|
| `epsdk init` | プロジェクトを初期化する（`-q` はクイックモード、`-n` で名前を指定） |
| `epsdk install <パッケージ名>` | モジュール/アダプタをインストールする（パラメータなしで対話モードに入る） |
| `epsdk config <名称>` | 対話形式でアダプタ/モジュールの宣言的設定項目を設定する |
| `epsdk run main.py` | プロジェクトを実行する（`--reload` でホットリロードモード） |
| `epsdk list` | インストール済みのモジュール/アダプタを一覧表示する |
| `epsdk upgrade <パッケージ名>` | モジュール/アダプタをアップグレードする |
| `epsdk doctor` | 環境診断（Python/バックエンド/設定/PyPI 接続性） |

> 完全なコマンドリストとパラメータの説明は [CLIコマンドリファレンス](cli-reference.md) を参照してください。

### 一般的な設定位置

| 設定項目 | 説明 | 詳細 |
|--------|------|------|
| `[ErisPulse.server]` | サーバー設定（ホスト、ポート） | [設定ファイルの説明](configuration.md#サーバー設定) |
| `[ErisPulse.logger]` | ログ設定（レベル、出力ファイル） | [設定ファイルの説明](configuration.md#ログ設定) |
| `[ErisPulse.framework]` | フレームワーク設定（遅延ロード） | [設定ファイルの説明](configuration.md#フレームワーク設定) |
| `[ErisPulse.event.command]` | コマンドイベント設定（プレフィックス） | [設定ファイルの説明](configuration.md#イベント設定) |
| `[アダプタ名]` | 各アダプタの固有設定 | [プラットフォームの特徴ガイド](../platform-guide/) |

## 関連ドキュメント

- [クイックスタート](../quick-start.md) - 入門ガイド
- [初心者向け](../getting-started/) - 入門チュートリアル
- [開発者ガイド](../developer-guide/) - カスタムモジュールとアダプターの開発
- [API リファレンス](../api-reference/) - API ドキュメント