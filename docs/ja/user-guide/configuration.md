# 設定ファイルの説明
> このドキュメントでは、フレームワークの設定ファイルについて説明します。サードパーティのモジュールで設定が必要な場合は、モジュールのドキュメントを参照してください。

ErisPulse はプロジェクトの設定を管理するために、TOML 形式の設定ファイル `config/config.toml` を使用します。

## 設定ファイルの場所

設定ファイルはプロジェクトのルートディレクトリにある `config/` フォルダに配置されています：

```
project/
├── config/
│   └── config.toml
├── main.py
```

## 完全な設定例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
log_files = []
memory_limit = 1000

[ErisPulse.framework]
enable_lazy_loading = true

[ErisPulse.storage]
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true
```

## サーバー設定

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | リッスンするアドレス。0.0.0.0 はすべてのネットワークインターフェースを意味します |
| port | integer | 8000 | リッスンポート番号 |
| ssl_certfile | string | 空 | SSL 証明書ファイルのパス |
| ssl_keyfile | string | 空 | SSL 秘密鍵ファイルのパス |

## ログ設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル：DEBUG, INFO, WARNING, ERROR, CRITICAL |
| log_files | array | 空 | ログ出力ファイルのリスト |
| memory_limit | integer | 1000 | メモリに保持するログの件数 |

## フレームワーク設定

```toml
[ErisPulse.framework]
enable_lazy_loading = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | モジュールのレイジーローディングを有効にするかどうか |

## ストレージ設定

```toml
[ErisPulse.storage]
use_global_db = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| use_global_db | boolean | false | プロジェクトのデータベースではなく、パッケージ内のグローバルデータベースを使用するかどうか |

## イベント設定

### コマンド設定

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| prefix | string | / | コマンドのプレフィックス |
| case_sensitive | boolean | false | 大文字と小文字を区別するかどうか |
| allow_space_prefix | boolean | false | 空白をプレフィックスとして許可するかどうか |
| must_at_bot | boolean | false | コマンドをトリガーするために必ずロボットを @ する必要があるかどうか（プライベートメッセージでは制限されません） |

### メッセージ設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| ignore_self | boolean | true | ロボット自身のメッセージを無視するかどうか |

## モジュール設定

各モジュールは設定ファイルで独自の設定を定義できます：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

モジュール内で設定を読み取る方法：

```python
from ErisPulse import sdk

config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")
```

## 次のステップ

*   [CLI コマンドリファレンス](cli-reference.md) - すべてのコマンドラインコマンドを確認する
*   [開発者ガイド](../developer-guide/) - カスタムモジュールの開発を学ぶ