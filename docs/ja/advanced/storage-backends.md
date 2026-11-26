# ストレージバックエンド

> [!TIP]
> **この記事を読む必要があるのはいつか**：sqlite / mysql / postgres またはカスタムストレージバックエンドに切り替える場合。必要なければスキップしても、他の機能の使用に影響はありません。

ErisPulse には、3 種類の非同期ネイティブストレージバックエンドが内蔵されており、設定で簡単に切り替えが可能です。**API は完全に一致しており、コードの変更はゼロです**：

| バックエンド | ドライバ | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | オープン即座に使用可能 | 零設定、単一ファイル、WAL 並行処理 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存の MySQL インフラストラクチャに適し、複数インスタンスで共有可能 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | トランザクション能力が強く、JSONB エコシステム、高並行処理対応 |

{!--< tips >!--}
1. 非同期はネイティブ主インターフェース（`aget/aset/atransaction/aExecute`）で、同期 API は互換性層です。
2. フレームワーク自身の設定の永続化、セッション受信箱、対話チェックポイントなどはすべて同一のストレージバックエンドを経由します。バックエンドを切り替えると、全体の移行になります。
3. `[mysql]` extra には `cryptography` が含まれています。MySQL 8 のデフォルトの `caching_sha2_password` 認証には必須で、不足すると接続プールの初期化時に失敗します。
{!--< /tips >!--}

## バックエンドの選択

`config/config.toml` で設定します：

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite"（デフォルト）/ "mysql" / "postgres"
use_global_db = false     # SQLite 僅か：パッケージ内のグローバルデータベース data/config.db を使用
```

環境変数で上書きすることもできます（Docker / 12-factor）：

```bash
ERISPULSE_STORAGE_BACKEND=postgres
ERISPULSE_STORAGE_POSTGRES_HOST=db.example.com
ERISPULSE_STORAGE_POSTGRES_PASSWORD=secret
```

環境変数の命名規則：設定パスを大文字にし、ドットをアンダースコアに変換します。
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
> 接続パラメータを変更した後は、フレームワークを再起動する必要があります（設定のホットアップデート時に再起動のリマインダーログが出力されます）。
> 接続プールはイベントループに惰性で作成され、作成時の瞬間的な失敗（ネットワークの揺れ / データベースの再起動窓）は指数関数的に再試行します。

## 接続失敗時の動作

フレームワークの起動と実行は**データベースの到達性に依存しません**。MySQL / PostgreSQL の接続失敗は、フレームワークのクラッシュや起動不能にはなりません：

1. 建立プールの瞬間的な失敗は指数関数的に再試行します（デフォルト 3 回）。
2. 再試行が尽きたら、WARNING ログを記録します（原因とクールダウン時間付き）、フレームワークは通常通り起動 / 継続実行し、ストレージ操作は一時的に利用できません。
3. クールダウン期間（デフォルト 30 秒）内に、その後のストレージ操作は**迅速に失敗**します（ブロックされず、他の機能を遅らせません）。
4. クールダウン終了後に自動的に再接続を試みます。データベースが復旧するとストレージも復旧し、再起動は不要です。

ログ例：`mysql 接続プールの作成が最終的に失敗しました（再試行 3 回）30 秒後に自動的に再接続します。この間、ストレージ操作は迅速に失敗しますが、フレームワークの他の機能には影響しません。`

## プロセスの終了

`sdk.uninit()` を呼び出さずに終了したプロセス（独立したスクリプト、中断後の終了）は、インタプリタ終了段階でストレージを自動的に閉じます。依存するストレージの終了フラッシュ（受信箱バッファ）を完了した後、すべてのデータベース接続を停止し、バックグラウンドブリッジループを停止します。SQLite の接続スレッドはプロセス終了時に自動的に終了しません。フレームワークはインタプリタがスレッドを回収する前にこの 3 つのステップを完了します。`atexit` コールバックはスレッド回収より遅く、ストレージにアクセスしないでください。

## 失敗の意味（2.12 以降）

| ステージ | 動作 |
|------|------|
| 操作の実行失敗（書き込みロックのタイムアウト / SQL エラー / 制約違反） | **`StorageOperationError` をスロー**（書き込み経路：aset / adelete / aclear / set_multi および同期ブリッジの同経路）——静かに `False` を返すのではなく、重要な書き込み失敗は可視化されるべきです |
| 接続レベルでの不可達（クールダウン期間中の迅速失敗） | `False` / `None` を返す（接続レベルでの不可達時は迅速失敗、`storage.unreachable` / `storage.recovered` イベント付き） |
| トランザクション開始のタイムアウト（>30s） | `StorageOperationError` をスロー（`STORAGE_TXN_BEGIN_TIMEOUT_SECS`） |

重要な書き込みは try/except で囲み、補償処理を行うべきです。トランザクションブロック内には純粋な DB 操作のみを入れてください。

## 非同期ネイティブ API

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

# 非同期トランザクション
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.Table("users").Insert({"name": "Alice"}).aExecute()
```

## 同期メソッド（慎重に使用）

`a` 前置の非同期メソッドには、同期形式の対応するものがあります（`aget`→`get`、`aset`→`set`、`atransaction`→`transaction`、`aExecute`→`Execute`）。内部ではバックグラウンドイベントループをブリッジして実行します。**これらは呼び出し元のスレッドをブロックします**：

- **非同期ハンドラ内で呼び出すと、ストレージ操作が完了するまでイベントループ全体がブロックされます**。頻繁に呼び出すとハンドラがタイムアウトし、イベント処理が停止し、web が遅滞し、`database is locked`（書き込み待ちのタイムアウト）が連鎖的に発生する可能性があります。フレームワークは各呼び出しポイントに制限頻度の警告を出力します（`ファイル:行番号 (関数名)` 付き）、警告を受け取ったら、対応する呼び出しを `a` 前置の非同期メソッドに移行するべきです。
- 開発期に `ErisPulse.framework.strict.sync_in_async = true` を有効にすると、同期呼び出しは許可されず、`StrictModeError` をスローします（呼び出しポイントと移行ガイド付き）、実行時に遅延を推測するのではなく、直ちに暴露されます。
- 実行時の対処：非同期コンテキスト内のブリッジ待ちのデフォルト上限は 10 秒です（`ErisPulse.framework.sync_in_async_bridge_wait`）。超えた場合、呼び出し元は fail-soft の意味で `None` を返します。待ち行列中の書き込み操作は**破棄されません**（バックグラウンドで完了し、事後に失敗は WARNING 警告で通知されます）、同期トランザクションのコミット / 接続返却も完了します。トランザクション開始のタイムアウトは `StorageOperationError` をスローします——しかし、これはバックアップ措置であり、許可ではありません。

**何をしているかを確認し、不要な場合は同期形式を使用しないでください**。イベントループのない純粋な同期スレッド（無イベントループ）で呼び出すのは制限されません。これは合法なシナリオです（同期エントリスクリプト、ブリッジ待ちトランザクションのコミット）。

`asyncio.to_thread` / スレッドプールで同期ドライバを実行する場合も同様であり、特定のシナリオでは効果的です：**バックエンドが真の並行接続をサポートしている場合**（PostgreSQL / MySQL——各スレッドが独立した接続、サーバ側 MVCC 並行）、同期ドライバをイベントループから外すのは合理的な手段です。しかし SQLite の場合は**しないでください**——スレッド接続はフレームワークの aiosqlite 接続と同一の書き込みロックを競合し、競合面が広がり、書き込み失敗やデータの損失を引き起こす可能性があります。

**MySQL / PostgreSQL バックエンドでは、手動で to_thread を行う必要はありません**：フレームワークは真の並行バックエンド（`_SUPPORTS_THREAD_BRIDGE` 機能）に対して、非同期コンテキスト内の同期呼び出しを有界スレッドプールにルーティングします（各ワーカーが独立したイベントループを持ち、互いに待ちません）、主ループのブロック時間は操作自体の所要時間です。待機上限と fail-soft の意味は上記と同じです。SQLite バックエンドは単一のブリッジループでシリアライズされます（書き込みロックモデルの要請）。カスタムバックエンドは、書き込みロックモデルに応じてその機能を宣言します（単一の書き込みエンジンはデフォルトで False です）。

完全なメソッド対照は [SQL クエリビルダー](sql-builder.md) を参照してください。

## ダイアレクトの動作差異

ダイアレクトの差異はすべてフレームワーク内部に集約されており、呼び出しコードは認識する必要がありません：

| 差異点 | SQLite | MySQL | PostgreSQL |
|------|------|------|------|
| パラメータプレースホルダ | `?` | `%s`（自動翻訳） | `$1..$n`（自動翻訳） |
| KV UPSERT | `INSERT OR REPLACE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| KV 値列の型 | `TEXT` | `LONGTEXT` | `TEXT` |
| 自動増分主キー | 原生サポート | `AUTO_INCREMENT`（自動翻訳） | `SERIAL`（自動翻訳） |

テーブル定義の列タイプはすべて SQLite 風に統一して定義します（例：`"INTEGER PRIMARY KEY AUTOINCREMENT"`、`"TEXT NOT NULL"`、`"DOUBLE DEFAULT 0.0"`）、ダイアレクトによって自動的に対応するバックエンドの等価な書き込み形式に翻訳されます。

## SQLite "database is locked" のトラブルシューティング

ErisPulse の SQLite バックエンドは、**WAL ログモード**（読み書きが互いに排他されない）+ **busy_timeout**（書き込みロック競合時に自動で待機、デフォルト 5000ms、設定項目は下記）+ 自動コミット接続 + 複数のイベントループが共有接続を持つ + **トランザクション `BEGIN IMMEDIATE`**（2.12 以降——トランザクション開始時に書き込みロックを取得し、deferred トランザクションの「先読み後書き込み」の昇格時の `SQLITE_BUSY_SNAPSHOT` を削除、この busy は再試行せず、`busy_timeout` で緩和できない、高頻度の読み書き混合で間欠的に locked が発生するフレームワーク内の根本原因）を内蔵しています。

2.12+ の純粋なフレームワーク使用（ストレージ / ORM / 混合双経路の交差書き込み）では、locked は発生しないはずです。それでも発生する場合は、以下の順序でトラブルシューティングを行ってください：

| シナリオ | 判定 | 対処 |
|------|------|------|
| トランザクション内の遅い操作 | `atransaction` ブロック内に遅い処理（外部 HTTP、大規模計算）があり、ロック保持時間が busy_timeout を超える——フレームワークはロック保持時間が 1 秒を超える（`STORAGE_TXN_SLOW_WARN_SECS`）トランザクションに対して、開始位置を付けて警告を出力し、直接位置を特定できる | トランザクションブロック内ではデータベース操作のみを行い、遅い処理は外に出す |
| 同期 API がイベントループをブロック | イベントハンドラが大量にタイムアウトし、呼び出しポイントの「ストレージ同期 API が非同期コンテキストで呼び出された」警告 | 警告で指摘された呼び出しポイントを a 前置の非同期メソッドに移行（`set` → `aset` など） |
| 第二の ORM を混用 | 同一プロセス内で sqlmodel / SQLAlchemy / 裸の sqlite3 が独自に接続して同じデータベースファイルを書き込む | **同一のデータベースファイルには 1 つの ORM だけを使用する**（内蔵は非同期ネイティブ）、混用は避ける |
| 複数プロセスが同じファイルを共有 | 複数のインスタンス / Dashboard / データベースツールが同じ sqlite を開く | 各インスタンスは独立した `config/` ディレクトリを使用する；管理ツールは読み取り専用モードで開く；高頻度の書き込みシナリオでは mysql / postgres に切り替える（設定を変更するだけでコードは変更不要） |
| 古いバージョンのフレームワーク | `<2.12` の deferred トランザクションの昇格問題 | フレームワークをアップグレードする |

ロックの排他行列（WAL モード）：**読み込みと読み込み、読み込みと書き込みは排他されない**；排他は**書き込みと書き込み**の間だけ発生する——トランザクション専用接続（`BEGIN IMMEDIATE` はコミットまでロック保持）と各イベントループの共有接続の書き込み操作は、同一の書き込みロックを競合し、長時間のトランザクションが書き込み待ちのタイムアウトの最初の疑いになります。

> `busy_timeout` は `ErisPulse.storage.sqlite.busy_timeout` で設定（ミリ秒、デフォルト 5000）；値を大きくすると書き込みロックの待ち時間の忍耐が長くなり、変更は再起動で有効になる（PRAGMA は接続確立時に適用される）。

## バックエンドの登録（プラグイン対応）

バックエンドは登録表で発見され、内蔵の 3 種類に限りません：

```python
from ErisPulse.Core.storage import get_registered_backends

print(get_registered_backends())   # ['mysql', 'postgres', 'sqlite', ...外部登録のバックエンド]
```

| 項目 | 説明 |
|---|---|
| 登録 / Register | 外部パッケージはモジュールのインポート時に `register_storage_backend(name, cls)` を呼び出す；`ErisPulse.storage.backend` に登録名を記入して有効化 |
| 発見 / Discovery | 外部パッケージは `pyproject.toml` で entry-points グループ `erispulse.storage.backends` を宣言し、フレームワークがストレージインスタンスを作成する前にスキャンして読み込む |
| ドライバ宣言 / Driver | ダイアレクトは `driver_module` でドライバのインポート名を宣言（空 = 零依存の内蔵ドライバ）。**ドライバの依存はバックエンドパッケージ自身の `pyproject.toml` で宣言され、パッケージのインストールに伴ってインストールされる**——フレームワークは実行時に依存をインストールせず、不足するとエラーをスローしてインストールの指示を付ける |
| 機能宣言 / Capability | バックエンドはクラス属性で機能を宣言し、フレームワークはこれに基づいてルーティングする：`_SUPPORTS_THREAD_BRIDGE`（真の並行バックエンド、sync-in-async は有界スレッドプール経由）、`_SUPPORTS_CONN_ROUTING`（同期トランザクション接続ルーティング） |
| 未登録のバックエンド | エラーをスローして現在利用可能なバックエンドをリストアップ |

内蔵バックエンドも同様に登録表を経由します（`sqlite` / `mysql` / `postgres` はインポート時に自動登録）、外部バックエンドと内蔵バックエンドは同等の地位です。

## カスタム SQL バックエンド

純粋な SQL バックエンドは共有基底クラスを継承し、接続管理とダイアレクト実行の漏斗を提供するだけで済みます：

```python
from ErisPulse.Core.Bases.sql_base import SQLDialect, SQLStorageBase

class MyDialect(SQLDialect):
    name = "mydb"
    # オーバーライド：パラメータプレースホルダの翻訳 / インデントの引用 / UPSERT / タイプのマッピング ...

class MyStorage(SQLStorageBase):
    dialect = MyDialect()

    async def _create_loop_resource(self): ...   # 接続プール
    async def _destroy_loop_resource(self, r): ...
    async def _acquire_resource_conn(self, r): ...
    async def _release_resource_conn(self, r, c): ...
    async def _open_txn_conn(self): ...
    async def _close_txn_conn(self, c): ...
    async def _exec_query_on(self, kind, sql, params, conn): ...  # 実行の漏斗
```

非 SQL バックエンド（例：Redis）は `BaseStorage` を継承して KV 非同期インターフェースを実装した後、`KVQueryBuilder` を直接使用してチェーン式の表クエリ操作能力（メモリフィルタリング、中小データ量に適する）を得ることができます。

## 関連ドキュメント

- [SQL クエリビルダー](sql-builder.md) - チェーン式クエリ構文と非同期 API の対照
- [コアモジュール API](../api-reference/core-modules.md) - Storage モジュールの完全な API
- [ストレージ基底クラス API](../api-reference/auto_api/ErisPulse/Core/Bases/sql_base.md) - SQLStorageBase / SQLDialect 抽象インターフェース