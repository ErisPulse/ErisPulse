# ストレージバックエンド

ErisPulse には、構成を変更するだけで簡単に切り替えられる 3 つの非同期ネイティブストレージバックエンドが内蔵されています。**API は完全に同一で、コードの変更は一切不要**です。

| バックエンド | ドライバー | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | インストール不要 | 零設定、単一ファイル、WAL による並行処理 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存の MySQL インフラストラクチャに適しており、複数インスタンスで共有可能 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | トランザクション能力が高く、JSONB エコシステム、高並行処理対応 |

{!--< tips >!--}
1. 非同期はネイティブの主インターフェース（`aget/aset/atransaction/aExecute`）であり、同期 API は互換性層です。
2. フレームワーク自身の設定の永続化、会話の受信箱、対話のチェックポイントなどはすべて同一のストレージバックエンドを経由します。バックエンドを切り替えることで、全体の移行が可能です。
3. `[mysql]` extra には `cryptography` が含まれています。MySQL 8 ではデフォルトの `caching_sha2_password` 認証に必要であり、これが欠如している場合、接続プールの初期化時に失敗します。
{!--< /tips >!--}

## バックエンドの選択

`config/config.toml` で設定します：

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite"（デフォルト）/ "mysql" / "postgres"
use_global_db = false     # SQLite のみ有効：パッケージ内のグローバルデータベース data/config.db を使用
```

また、Docker / 12-factor アプリケーション仕様に準拠した環境変数による上書きもサポートしています：

```bash
ERISPULSE_STORAGE_BACKEND=postgres
ERISPULSE_STORAGE_POSTGRES_HOST=db.example.com
ERISPULSE_STORAGE_POSTGRES_PASSWORD=secret
```

環境変数の命名規則は、設定パスを大文字にし、ドットをアンダースコアに変換します。
（`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`）。

## 接続パラメータ

### MySQL（`ErisPulse.storage.mysql`）

```toml
[ErisPulse.storage.mysql]
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
charset = "utf8mb4"
pool_min = 1
pool_max = 10
```

### PostgreSQL（`ErisPulse.storage.postgres`）

```toml
[ErisPulse.storage.postgres]
host = "127.0.0.1"
port = 5432
user = "erispulse"
password = ""
database = "erispulse"
pool_min = 1
pool_max = 10
```

> [!NOTE]
> 接続パラメータを変更した後は、フレームワークを再起動する必要があります（設定のホット更新時に再起動のリマインダーログが出力されます）。
> 接続プールはイベントループに従って惰性作成され、作成時に瞬間的な失敗（ネットワークの揺れ / データベースの再起動期間）が発生した場合、自動的に指数型の退避再試行が行われます。

## 接続失敗時の動作

フレームワークの起動と実行は**データベースの利用可能性に依存しません**。MySQL / PostgreSQL への接続失敗は、フレームワークのクラッシュや起動不能を引き起こしません。

1. プール作成時の瞬時失敗は、指数関数的退避再試行（デフォルト 3 回）で自動的に処理されます。
2. 再試行回数をすべて使用した場合 → WARNING ログを記録（原因とクールダウン期間を含む）、フレームワークは通常通り起動 / 継続的に動作しますが、ストレージ操作は一時的に利用できません。
3. クールダウン期間（デフォルト 30 秒）内では、その後のストレージ操作は**即時失敗**します（ブロックされず、他の機能の遅延もありません）。
4. クールダウン終了後は自動的に再接続を試みます。データベースが復旧するとストレージも復旧し、フレームワークの再起動は不要です。

ログ例: `mysql 接続プールの作成が最終的に失敗しました（再試行を 3 回行いました）。30 秒後に自動的に再接続を試みます。この間、ストレージ操作は即時失敗しますが、フレームワークの他の機能には影響しません。`

## 異スレッド API

```python
# KV 操作
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()

# 表操作
await sdk.storage.aCreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})
rows = await sdk.storage.Table("users").Select("name").ToDict().aExecute()

# 異スレッドトランザクション
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.Table("users").Insert({"name": "Alice"}).aExecute()
```

同期 API (`get/set/transaction/Table(...).Execute()`) は引き続き使用可能です。内部では `AsyncBridge` がバックグラウンドイベントループを橋渡しして実行しています。非同期ハンドラ内で同期 API を呼び出すと、イベントループが一時的にブロックされます。**初回呼び出し時に一回限りの警告**（「a 前置きの非同期メソッドの使用を推奨」）が出力されます。非同期メソッドの使用を推奨します。以下の境界条件に注意してください：

- **橋渡しスレッド内では再び同期インターフェースを呼び出せない**：同期インターフェースは橋渡しスレッド内で実行され、この状態で再度同期インターフェースを呼び出すと `RuntimeError` が発生します（再入防止の保護により、自己デッドロックを回避します）。
- **橋渡し対象のループが閉じた後に呼び出すと失敗する**：`uninit()` の後にストレージインターフェースを呼び出さないでください。

完全なメソッド対照は [SQL クエリビルダ](sql-builder.md) を参照してください。

## 方言の動作の違い

方言の違いはすべてフレームワーク内部で吸収され、呼び出し元のコードはその違いを意識する必要はありません。

| 差異点 | SQLite | MySQL | PostgreSQL |
|------|------|------|------|
| プレースホルダ | `?` | `%s`（自動変換） | `$1..$n`（自動変換） |
| KV UPSERT | `INSERT OR REPLACE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| KV 値の列型 | `TEXT` | `LONGTEXT` | `TEXT` |
| 自動増分主キー | 原生サポート | `AUTO_INCREMENT`（自動変換） | `SERIAL`（自動変換） |

列の定義はすべて SQLite のスタイルを使用します（例: `"INTEGER PRIMARY KEY AUTOINCREMENT"`、`"TEXT NOT NULL"`、`"DOUBLE DEFAULT 0.0"`）。これらの定義は、後端のデータベースに等価な形式に自動的に変換されます。

## 自定义 SQL バックエンド

純粋な SQL バックエンドは、共有基底クラスを継承し、接続管理と方言実行ファネルを提供するだけです。

```python
from ErisPulse.Core.Bases.sql_base import SQLDialect, SQLStorageBase

class MyDialect(SQLDialect):
    name = "mydb"
    # オーバーライド: プレースホルダ翻訳 / イデンティファイア引用 / UPSERT / タイプマッピング ...

class MyStorage(SQLStorageBase):
    dialect = MyDialect()

    async def _create_loop_resource(self): ...   # 接続プール
    async def _destroy_loop_resource(self, r): ...
    async def _acquire_resource_conn(self, r): ...
    async def _release_resource_conn(self, r, c): ...
    async def _open_txn_conn(self): ...
    async def _close_txn_conn(self, c): ...
    async def _exec_query_on(self, kind, sql, params, conn): ...  # 実行ファネル
```

非 SQL バックエンド（例: Redis）は `BaseStorage` を継承して KV 非同期インターフェースを実装した後、
`KVQueryBuilder` を使ってチェーン式の表クエリ機能（メモリ内フィルタ、中小データ量に適している）を直接利用できます。

## 関連ドキュメント

- [SQL クエリビルダー](sql-builder.md) - チェーン式クエリ構文と非同期 API の対照表
- [コアモジュール API](../api-reference/core-modules.md) - Storage モジュールの完全な API
- [ストレージ基底クラス API](../api-reference/auto_api/ErisPulse/Core/Bases/sql_base.md) - SQLStorageBase / SQLDialect 抽象インターフェース