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
format = "rich"
log_files = []
memory_limit = 1000

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 1

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true

[ErisPulse.i18n]
language = "auto"
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
| format | string | rich | ログ出力フォーマット。デフォルトで rich を使用してカラフルな出力を提供します |
| log_files | array | 空 | ログ出力ファイルのリスト |
| memory_limit | integer | 1000 | メモリに保持するログの件数 |

## フレームワーク設定

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 1

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | モジュールのレイジーローディングを有効にするかどうか |
| uninit_timeout | integer | 30 | エレガントなシャットダウンの総タイムアウト時間（秒）。超えた場合は強制終了します。0 はタイムアウトを設定しないことを意味します |
| strict_mode | integer | 1 | 严格模式レベル。下記「厳格モード」の説明を参照してください |

### 厳格モード

厳格モードは、モジュール/アダプタがロード段階で不正または失敗した場合の処理戦略を制御します。現代のモジュール/アダプタはすべて対応する基底クラス（`BaseModule`/`BaseAdapter`）を継承する必要があります。基底クラスを継承していないコンポーネントはフレームワークのコンテキストシステムとリソースのクリーンアップに影響を与え、リソースリークを引き起こす可能性があります。厳格モードはデフォルトで有効になっており、このようなコンポーネントを遮断します。

| レベル | 名称 | 行動 |
|------|------|------|
| 0 | フレキシブル | 不正は警告のみ。基底クラスを継承していないコンポーネントもロードを試みます（旧コンポーネントの互換性） |
| 1 | 厳格-スキップ（デフォルト） | 基底クラスを継承していないコンポーネントを拒否してスキップし、他のコンポーネントは正常に起動します |
| 2 | 厳格-致命 | すべての不正を収集して一括で報告し、起動を中止します |

各レベルにおいて、「ロード/登録/初期化段階でのエラー」は常にそのコンポーネント自身のクラッシュとしてスキップされます。違いは以下の通りです：

- **0 → 1**: 唯一の動作変化は「基底クラスを継承していない」コンポーネントが「ロードされる」から「スキップされる」ようになることです。
- **1 → 2**: すべての不正（基底クラスを継承していない、ロード失敗、登録失敗、初期化失敗など）が致命的となり、起動チェックポイントで一括で不正リストを出力して中止されます。

#### 豁免リスト

もし特定のコンポーネントが一時的に移行できない場合（例えば依存する旧モジュールなど）、そのコンポーネントを豁免リストに追加することで、不正なコンポーネントでもフレキシブルモードとして扱い、ロードを継続させることができます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> 厳格モードによってコンポーネントが拒否された場合、ログには明確にそのコンポーネントをロードを回復する方法（豁免リストに追加するか、レベルを下げること）が表示されます。

## ストレージ設定

```toml
[ErisPulse.storage]
use_global_db = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| use_global_db | boolean | false | プロジェクトのデータベースではなく、パッケージ内のグローバルデータベースを使用するかどうか。`true` の場合、すべてのプロジェクトで ErisPulse パッケージ内の SQLite データベースが共有されます。`false`（デフォルト）の場合、各プロジェクトは `config/` ディレクトリで独立したデータベースを使用します |

## イベント設定

### コマンド設定

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
must_at_bot = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| prefix | string | / | コマンドのプレフィックス |
| case_sensitive | boolean | true | 大文字と小文字を区別するかどうか（`/Help` と `/help` が異なるコマンドかどうか） |
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

## 国際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| language | string | auto | フレームワークの内蔵テキストの表示言語。`auto` に設定するとシステム言語を自動検出します。具体的な言語コード（`zh-CN`、`zh-TW`、`en`、`ja`、`ru`）を設定することもできます |

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

# 读取配置
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 运行时写入配置（延迟保存）
sdk.config.setConfig("MyModule.timeout", 60)

# 立即保存到文件
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（約 5 秒ごとにファイルへのバッチ保存）を採用します。`immediate=True` を設定すると、即座に永続化できます。設定の変更は `config.set` ライフサイクルイベントをトリガーします。

## 次のステップ

- [CLI コマンドリファレンス](cli-reference.md) - すべてのコマンドラインコマンドを確認する
- [開発者ガイド](../developer-guide/) - カスタムモジュールの開発を学ぶ