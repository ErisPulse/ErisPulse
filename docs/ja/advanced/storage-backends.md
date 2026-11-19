# ストレージバックエンド

> [!TIP]
> **このドキュメントを読む必要があるケース**：sqlite / mysql / postgres を切り替えたり、カスタムストレージバックエンドを設定する場合。必要なければ読み飛ばしても、他の機能の利用には影響しません。


ErisPulse には 3 種類の非同期ネイティブストレージバックエンドが内蔵されており、設定だけで簡単に切り替えられます。**API は完全に同一で、切り替えにコード変更は一切不要**です：

| バックエンド | ドライバー | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | すぐに使える | ゼロ設定、単一ファイル、WAL 同時実行 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存の MySQL インフラ環境や複数インスタンス共有に最適 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | 強力なトランザクション、JSONB エコシステム、高同時実行性 |

{!--< tips >!--}
1. 非同期がネイティブのメインインターフェース（`aget/aset/atransaction/aExecute`）で、同期 API は互換レイヤーです
2. フレームワーク自身の設定永続化、セッション受信トレイ、対話チェックポイントなどは、すべて同一のストレージバックエンドを使用します——バックエンドを切り替えれば全体がまとめて移行されます
3. `[mysql]` extra には `cryptography` が含まれています——これは MySQL 8 のデフォルト認証 `caching_sha2_password` に必須で、欠落していると接続プールの初期化が失敗します
{!--< /tips >!--}

## バックエンドの選択

`config/config.toml` で設定します：

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite"（デフォルト）/ "mysql" / "postgres"
use_global_db = false     # SQLite のみ：パッケージ内グローバルデータベース data/config.db を使用
```

環境変数による上書きにも対応しています（Docker / 12-factor）：

```bash
ERISPULSE_STORAGE_BACKEND=postgres
ERISPULSE_STORAGE_POSTGRES_HOST=db.example.com
ERISPULSE_STORAGE_POSTGRES_PASSWORD=secret
```

環境変数の命名規則：設定パスを大文字にし、ドットをアンダースコアに置き換えます
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
> 接続パラメータの変更後は、フレームワークの再起動によって有効になります（設定ホットリロード時に再起動リマインダーのログが出力されます）。
> 接続プールはイベントループごとに遅延生成され、生成時の一時的な失敗（ネットワークの揺らぎ / データベース再起動のタイミング）では自動的に指数バックオフで再試行します。

## 接続失敗時の動作

フレームワークの起動と実行は**データベースの到達性に依存しません**——MySQL / PostgreSQL への接続に失敗しても、フレームワークがクラッシュしたり起動できなくなったりすることはありません：

1. プール生成時の一時的な失敗は自動的に指数バックオフで再試行します（デフォルト 3 回）
2. 再試行を使い切った場合 → WARNING を記録（原因とクールダウン時間を含む）。フレームワークは通常どおり起動 / 実行を継続し、ストレージ操作だけが一時的に利用不可になります
3. クールダウン期間（デフォルト 30 秒）中の後続のストレージ操作は**フェイルファスト**します（ブロックせず、他の機能も遅延させません）
4. クールダウン終了後に自動的に再接続を試みます——データベースが復旧すればストレージもそれに伴って復旧し、再起動は不要です

ログ例：`mysql 接続プールの作成に最終的に失敗（再試行 3 回済み）。30 秒後に自動再接続します。期間中のストレージ操作はフェイルファストとなり、フレームワークの他の機能には影響しません`

## 失敗セマンティクス（2.12 以降）

| シナリオ | 動作 |
|------|------|
| 操作実行の失敗（書き込みロックのタイムアウト / SQL エラー / 制約違反） | **`StorageOperationError` をスロー**（書き込みパス：aset / adelete / aclear / set_multi および同期ブリッジの同一パス）——サイレントに `False` を返すことはなく、重要な書き込みの失敗は必ず可視化されます |
| 接続レベルの到達不能（クールダウン期間のフェイルファスト） | `False` / `None` を返す（ルール 26 のフレームワークレジリエンスセマンティクス。`storage.unreachable` / `storage.recovered` イベントも発行） |
| トランザクション開始のタイムアウト（30 秒超） | `StorageOperationError` をスロー（`STORAGE_TXN_BEGIN_TIMEOUT_SECS`） |

重要な書き込みは try/except でラップして補償処理を行ってください。トランザクションブロック内には純粋な DB 操作のみを記述します。

## 非同期ネイティブ API

```python
# KV 操作
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()

# テーブル操作
await sdk.storage.aCreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})
rows = await sdk.storage.Table("users").Select("name").ToDict().aExecute()

# 非同期トランザクション
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.Table("users").Insert({"name": "Alice"}).aExecute()
```

同期 API（`get/set/transaction/Table(...).Execute()`）も引き続き利用可能で、内部的には `AsyncBridge` のバックグラウンドイベントループでブリッジ実行されます——**a 接頭辞付き非同期メソッドに統一することを推奨します**（`aget` / `aset` / `adelete` / `atransaction` / `aExecute`）：同期インターフェースを非同期 handler 内で呼び出すと、ストレージ操作が完了するまでそのイベントループがブロックされます（高頻度呼び出しでは handler のタイムアウト、イベント処理の停止として現れます）。フレームワークは呼び出し箇所ごとにレート制限付きの警告を出力し（`ファイル:行番号 (関数名)` の形式で呼び出し箇所を付記、箇所ごとのクールダウンでログの氾濫を防止）、警告を受け取ったら該当する呼び出しを a 接頭辞付き非同期メソッドへ移行してください。以下の 2 つの境界を必ず把握しておいてください：

- **ブリッジスレッド内での同期インターフェースの再呼び出しは禁止**：同期インターフェースはブリッジスレッド内で実行されるため、その中でさらに同期インターフェースを呼び出すと `RuntimeError` がスローされます（再入防止保護によるセルフデッドロックの回避）
- **ブリッジ先のループが閉じられた後の呼び出しは失敗します**：`uninit()` の後はストレージインターフェースを呼び出さないでください

完全なメソッド対応は [SQL クエリビルダー](sql-builder.md) を参照してください。

## ダイアレクトの動作差異

ダイアレクト間の差異はすべてフレームワーク内部に収束されており、呼び出し側のコードは意識する必要がありません：

| 差異ポイント | SQLite | MySQL | PostgreSQL |
|------|------|------|------|
| プレースホルダー | `?` | `%s`（自動翻訳） | `$1..$n`（自動翻訳） |
| KV UPSERT | `INSERT OR REPLACE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| KV 値カラムの型 | `TEXT` | `LONGTEXT` | `TEXT` |
| 自動増分主キー | ネイティブサポート | `AUTO_INCREMENT`（自動翻訳） | `SERIAL`（自動翻訳） |

テーブル作成時のカラム型は SQLite スタイルの定義に統一されており（例：`"INTEGER PRIMARY KEY AUTOINCREMENT"`、`"TEXT NOT NULL"`、`"DOUBLE DEFAULT 0.0"`）、ダイアレクトがターゲットバックエンドの等価な記述に自動的に翻訳します。

## SQLite "database is locked" のトラブルシューティング

フレームワークの SQLite バックエンドには以下が組み込まれています：**WAL ログモード**（読み書きは相互排他になりません）+ **busy_timeout**（書き込みロック競合時に自動待機、デフォルト 5000ms、設定項目は下記参照）+ autocommit 接続 + 複数イベントループがそれぞれ共有接続を保持 + **トランザクションの `BEGIN IMMEDIATE`**（2.12 以降——トランザクション開始時に即座に書き込みロックを取得し、deferred トランザクションが「先に読んでから書く」形で昇格する際の `SQLITE_BUSY_SNAPSHOT` を解消します。この busy は再試行されず、`busy_timeout` でも緩和できないため、高頻度の読み書き混在環境下で断続的に locked が発生するフレームワーク内の根本原因でした）。

2.12+ でのフレームワーク単体利用（ストレージ / ORM / 混合の 2 パスによる交互書き込み）では locked は再び発生しないはずです。それでも発生する場合は、以下の順序で切り分けてください：

| シナリオ | 判定 | 対処 |
|------|------|------|
| トランザクション内の低速操作 | `atransaction` ブロック内に時間のかかる処理（外部 HTTP、大規模計算）があり、busy_timeout を超えてロックを保持——フレームワークはロック保持が 1 秒（`STORAGE_TXN_SLOW_WARN_SECS`）を超えたトランザクションに対し、開始位置を付けて警告を出力するため、これで直接特定できます | トランザクションブロック内では DB 操作のみに限定し、低速な処理はブロック外へ移動 |
| 同期 API によるイベントループのブロック | イベント handler の大量タイムアウト + 呼び出し箇所単位の「非同期コンテキスト内でのストレージ同期 API 呼び出し」警告 | 警告で指摘された呼び出し箇所を a 接頭辞付き非同期メソッドへ移行（`set` → `aset` など） |
| 第二の ORM との混用 | 同一プロセス内で sqlmodel / SQLAlchemy / 生の sqlite3 が独自に接続を開いて同じ DB ファイルへ書き込み | **同一の DB ファイルには 1 つの ORM だけを使用**（内蔵のものはもともと非同期ネイティブです）。混用による過渡的な運用は避ける |
| マルチプロセスでの同一ファイル | 複数インスタンス / Dashboard / データベースツールが同一の sqlite を開いている | インスタンスごとに独立した `config/` ディレクトリを使う。管理ツールは読み取り専用モードで開く。高頻度書き込みのシナリオでは mysql / postgres に切り替える（設定変更だけでゼロコード移行） |
| 旧バージョンのフレームワーク | `<2.12` の deferred トランザクション昇格の問題 | フレームワークをアップグレードする |

ロック相互排他マトリクス（WAL モード）：**読み取りと読み取り、読み取りと書き込みは相互排他になりません**。相互排他は**書き込みと書き込み**の間でのみ発生します——トランザクション専用接続（`BEGIN IMMEDIATE` でコミットまでロックを保持）と各イベントループの共有接続による書き込み操作が、同一の書き込みロックを競合します。長時間のトランザクションは書き込み待機タイムアウトの第一容疑です。

> `busy_timeout` は `ErisPulse.storage.sqlite.busy_timeout` で設定します（ミリ秒、デフォルト 5000）。値を大きくすると書き込みロックの待機猶予を延長できます。変更には再起動が必要です（PRAGMA は接続確立時に適用されます）。

## カスタム SQL バックエンド

純粋な SQL バックエンドは共有基底クラスを継承でき、接続管理とダイアレクト実行ファンネルを提供するだけで済みます：

```python
from ErisPulse.Core.Bases.sql_base import SQLDialect, SQLStorageBase

class MyDialect(SQLDialect):
    name = "mydb"
    # オーバーライド：プレースホルダー翻訳 / 識別子のクォート / UPSERT / 型マッピング ...

class MyStorage(SQLStorageBase):
    dialect = MyDialect()

    async def _create_loop_resource(self): ...   # 接続プール
    async def _destroy_loop_resource(self, r): ...
    async def _acquire_resource_conn(self, r): ...
    async def _release_resource_conn(self, r, c): ...
    async def _open_txn_conn(self): ...
    async def _close_txn_conn(self, c): ...
    async def _exec_query_on(self, kind, sql, params, conn): ...  # 実行ファンネル
```

非 SQL バックエンド（Redis など）は `BaseStorage` を継承して KV 非同期インターフェースを実装すれば、`KVQueryBuilder` をそのまま利用してチェーン式テーブルクエリ機能を得られます（メモリ内フィルタリング、中小規模のデータ量に適しています）。

## 関連ドキュメント

- [SQL クエリビルダー](sql-builder.md) - チェーン式クエリ構文と非同期 API の対応
- [コアモジュール API](../api-reference/core-modules.md) - Storage モジュールの完全な API
- [ストレージ基底クラス API](../api-reference/auto_api/ErisPulse/Core/Bases/sql_base.md) - SQLStorageBase / SQLDialect 抽象インターフェース