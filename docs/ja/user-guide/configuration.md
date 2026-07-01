# 設定ファイルの説明
> このドキュメントでは、フレームワークの設定ファイルについて説明します。サードパーティのモジュールに設定が必要な場合は、モジュールのドキュメントを参照してください。

ErisPulse は、TOML 形式の設定ファイル `config/config.toml` を使用してプロジェクトの設定を管理します。

## 設定ファイルの位置

設定ファイルはプロジェクトのルートディレクトリの `config/` フォルダ内にあります：

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
strict_mode = 0

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
| host | string | 0.0.0.0 | 監視するアドレス。0.0.0.0 はすべてのインターフェースを意味します |
| port | integer | 8000 | 監視するポート番号 |
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
| level | string | INFO | ログレベル：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE は最低レベルで、フレームワーク内部の詳細なデバッグ情報を出力します） |
| format | string | rich | ログ出力フォーマット。デフォルトでは rich 彩色出力を使用します |
| log_files | array | 空 | ログ出力ファイルのリスト |
| memory_limit | integer | 1000 | メモリ内に保持するログの件数 |

## フレームワーク設定

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | モジュールのラジーロードを有効にするかどうか |
| uninit_timeout | integer | 30 | エレガントなシャットダウンの総タイムアウト時間（秒）。超過すると強制終了します。0 はタイムアウトを設定しないことを意味します |
| strict_mode | integer | 0 | 厳密モードのレベル。下記「厳密モード」の説明を参照してください |

### 厳密モード

厳密モードは、モジュール/アダプターがロード段階で不正または失敗した場合の処理戦略を制御します。現代のモジュール/アダプターはすべて対応する基底クラス（`BaseModule`/`BaseAdapter`）を継承する必要があります。基底クラスを継承していないコンポーネントは、フレームワークのコンテキストシステムとバックアップクリーンアップに影響を与え、リソースリークを引き起こす可能性があります。

> **2.5.2 変更**：デフォルトのレベルは `1`（スキップ）から `0`（緩和）に変更され、新規ユーザーが初めて使用する際に発生するロード問題を減らしました。基底クラスを継承していないコンポーネントは、WARNING ログとして警告を表示し、直接拒否するのではなく、ロードを試みます。旧来の動作を復元するには、`strict_mode = 1` と明示的に設定してください。

| レベル | 名称 | 行動 |
|------|------|------|
| 0 | 緩和（デフォルト） | 不正は警告のみ。基底クラスを継承していないコンポーネントもロードを試みます（旧コンポーネントとの互換性） |
| 1 | 厳密-スキップ | 基底クラスを継承していないコンポーネントを拒否し、スキップします。それ以外は正常に起動します |
| 2 | 厳密-致命 | すべての不正を収集し、一括で報告して起動を中止します |

各レベルにおいて、「ロード/登録/初期化段階でのエラー」はコンポーネント自身のクラッシュとして常にスキップされます。違いは以下の通りです：

- **0 → 1**：唯一の動作変化は「基底クラスを継承していない」が「ロードを試みる」から「スキップ」に変わる点です。
- **1 → 2**：すべての不正（基底クラスを継承していない、ロード失敗、登録失敗、初期化失敗など）が致命的になり、起動チェックポイントで一括して不正リストを出力し、中止します。

#### 裁量リスト

一部のコンポーネントが一時的に移行できない場合（依存する旧モジュールなど）、そのコンポーネントを裁量リストに追加できます。リストに含まれるコンポーネントは、不正であっても緩和モードで扱われ、ロードを続けます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> 厳密モードによってコンポーネントが拒否された場合、ログには明確にどのようにロードを回復するか（裁量リストに追加するか、レベルを下げること）が示されます。

## ストレージ設定

```toml
[ErisPulse.storage]
use_global_db = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| use_global_db | boolean | false | プロジェクトデータベースではなく、ErisPulse パッケージ内のグローバルデータベースを使用するかどうか。`true` の場合、すべてのプロジェクトは ErisPulse パッケージ内の SQLite データベースを共有します。`false`（デフォルト）の場合は、各プロジェクトは `config/` ディレクトリ内の独立したデータベースを使用します |

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
| case_sensitive | boolean | true | 大文字小文字を区別するかどうか（`/Help` と `/help` が異なるコマンドになるかどうか） |
| allow_space_prefix | boolean | false | スペースをプレフィックスとして許可するかどうか |
| must_at_bot | boolean | false | コマンドをトリガーする際に必ず@ボットを指定する必要があるかどうか（プライベートチャットは制限されません） |

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
| language | string | auto | フレームワーク内に含まれるテキストの表示言語。`auto` に設定するとシステム言語を自動検出します。具体的な言語コード（`zh-CN`、`zh-TW`、`en`、`ja`、`ru`）を指定することもできます |

## モジュール設定

各モジュールは、設定ファイル内で独自の設定を定義できます：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

モジュール内で設定を読み取り、書き込みます：

```python
from ErisPulse import sdk

# 設定を読み取る
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 実行時に設定を書き込む（遅延保存）
sdk.config.setConfig("MyModule.timeout", 60)

# ファイルに即時保存
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（約 5 秒ごとにバッチ保存）を使用します。`immediate=True` を設定すると即時永続化されます。設定の変更は `config.set` ライフサイクルイベントをトリガーします。

## 次に進む

- [CLI コマンドリファレンス](cli-reference.md) - すべてのコマンドラインコマンドを理解する
- [開発者ガイド](../developer-guide/) - 自作モジュールの開発方法を学ぶ