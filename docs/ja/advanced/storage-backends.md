# ストレージバックエンド

ErisPulse には、3 種類の非同期ネイティブストレージバックエンドが内蔵されており、設定を変更することで簡単に切り替えることができます。**API は完全に同一であり、コードの変更は一切必要ありません**。

| バックエンド | ドライバー | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | インストール不要 | 零設定、単一ファイル、WAL による並行処理 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存の MySQL インフラストラクチャがある場合、複数インスタンスで共有するのに適しています |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | トランザクション処理が強力、JSONB エコシステム、高並行性 |

{!--< tips >!--}
1. 非同期はネイティブの主インターフェース（`aget/aset/atransaction/aExecute`）であり、同期 API は互換性層です。
2. フレームワーク自体の設定の永続化、会話の受信箱、対話のチェックポイントなどはすべて同じストレージバックエンドを経由します。バックエンドを切り替えることで、全体の移行が可能です。
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

## 異同步ネイティブAPI

```python
# KV操作
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()

# テーブル操作
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

同期API（`get/set/transaction/Table(...).Execute()`）は引き続き使用可能で、内部では
`AsyncBridge` がバックグラウンドイベントループをブリッジして実行します。非同期ハンドラ内で同期APIを呼び出すと、
イベントループが一時的にブロックされるため、a接頭辞の非同期メソッドを優先して使用することを推奨します。完全なメソッドの対照表は
[SQLクエリビルダー](sql-builder.md)をご覧ください。

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