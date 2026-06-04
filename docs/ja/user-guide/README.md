# ユーザー使用ガイド

このガイドは、ErisPulse プロジェクトのインストール、設定、および管理を支援します。

## 目次

1. [インストールと設定](installation.md) - ErisPulse のインストールとプロジェクトの設定
2. [CLI コマンドリファレンス](cli-reference.md) - コマンドラインツールの完全な使用説明
3. [設定ファイルの説明](configuration.md) - 設定ファイルの詳細な説明

## クイックリファレンス

### 一般的なコマンド

| コマンド | 説明 | 例 |
|-------|------|------|
| `epsdk init` | プロジェクトの初期化 | `epsdk init -q -n my_bot` |
| `epsdk install` | モジュール/アダプターのインストール | `epsdk install Yunhu` |
| `epsdk run` | プロジェクトの実行 | `epsdk run main.py --reload` |
| `epsdk list` | インストール済みモジュールのリスト表示 | `epsdk list -t modules` |
| `epsdk upgrade` | モジュールのアップグレード | `epsdk upgrade Yunhu` |

### 一般的な設定の場所

| 設定項目 | 説明 |
|--------|------|
| `[ErisPulse.server]` | サーバー設定（ホスト、ポート） |
| `[ErisPulse.logger]` | ログ設定（レベル、出力ファイル） |
| `[ErisPulse.framework]` | フレームワーク設定（遅延読み込み） |
| `[ErisPulse.event.command]` | コマンドイベント設定（プレフィックス） |
| `[アダプター名]` | 各アダプターの固有の設定 |

### プロジェクトディレクトリ構造

```
project/
├── config/
│   └── config.toml          # プロジェクト設定ファイル
├── main.py                  # プロジェクトのエントリーポイント
└── requirements.txt          # 依存関係リスト
```

## 開発モード

### ホットリロードモード

開発中はホットリロードモードを使用すると、コードの変更後に自動的にリロードされます：

```bash
epsdk run main.py --reload
```

### 標準実行モード

本番環境では標準実行モードを使用します：

```bash
epsdk run main.py
```

## 一般的なタスク

### 新しいモジュールのインストール

```bash
# リモートリポジトリからインストール
epsdk install Yunhu Weather

# ローカルディレクトリからインストール
epsdk install ./my-module

# インタラクティブなインストール
epsdk install
```

### 使用可能なモジュールの表示

```bash
# すべてのモジュールを一覧表示
epsdk list

# アダプターのみを一覧表示
epsdk list -t adapters

# モジュールのみを一覧表示
epsdk list -t modules

# リモートで使用可能なモジュールを一覧表示
epsdk list-remote
```

### モジュールのアップグレード

```bash
# 指定されたモジュールをアップグレード
epsdk upgrade Yunhu

# すべてのモジュールをアップグレード
epsdk upgrade
```

### モジュールのアンインストール

```bash
# 指定されたモジュールをアンインストール
epsdk uninstall Yunhu

# 複数のモジュールをアンインストール
epsdk uninstall Yunhu Weather
```

## 関連ドキュメント

- [クイックスタート](../quick-start.md) - クイックスタートガイド
- [入門ガイド](../getting-started/) - 入門チュートリアル
- [開発者ガイド](../developer-guide/) - カスタムモジュールとアダプターの開発
- [API リファレンス](../api-reference/) - API ドキュメント