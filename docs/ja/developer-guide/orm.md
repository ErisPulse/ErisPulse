# データモデル層（ORM）

> [!TIP]
> **このドキュメントを読むべきとき**: データモデル、自動テーブル作成、リレーションマッピングが必要な場合です。不要であれば読み飛ばしても、他の機能の利用には影響しません。

> [!NOTE]
> **ORM は非同期ネイティブです**: すべての CRUD メソッド（`create` / `get` / `save` / `delete` / `create_table` / QuerySet の終端操作）は `async def` であり、イベントループ内でそのまま `await` して呼び出せます。低層ドライバーは aiosqlite / aiomysql / asyncpg（ストレージバックエンドに応じて切り替わります）で、同期ブロッキングは発生しません。KV ストレージの同期 `get`/`set` は互換レイヤーであり、ORM とは無関係です。

2.9.0 からフレームワークに宣言型データモデル層が組み込まれました: `Model` を継承し `Field` でフィールドを宣言するだけで、自動テーブル作成と CRUD（登録・照会・更新・削除）の能力が得られます。モデルは内蔵ストレージ層の上に直接構築されています。SQLite / MySQL / PostgreSQL のどれを使うかは `ErisPulse.storage.backend` の設定で決まり、**バックエンドを切り替えてもモデルコードは一切変更不要**です。

## モデルの宣言

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON カラム。読み書き時に自動シリアライズ
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "プロフィール"})
```

- テーブル名はデフォルトでクラス名を snake_case にしたもの（`UserProfile → user_profile`）になります。`__tablename__ = "xxx"` で上書き可能です
- `Field` の制約語彙は宣言型設定クラスと共通です（`choices` / `ge` / `le` / `max_length`。`description` も同様に i18n 辞書に対応）。バリデーターエンジンは設定検証と共通の実装です

## フィールドパラメータ

| パラメータ | 説明 |
|------|------|
| `default` | デフォルト値（未指定かつ自動増分でない場合 → NOT NULL 必須） |
| `default_factory` | ミュータブルなデフォルト値のファクトリ（例：`list`） |
| `primary_key` | 主キー（複数指定で複合主キーとなり、テーブルレベルの `PRIMARY KEY (a, b)` に集約される） |
| `autoincrement` | 自動増分主キー（暗黙的に主キーを含み、`create` 後に自動的に値が反映される。単一列主キー専用で、複合主キーとは排他） |
| `max_length` | 文字列の最大長（`VARCHAR(n)` を生成、書き込み時にバリデーション） |
| `nullable` | NULL を許可するかどうか（デフォルトは False） |
| `index` | 通常インデックスを生成 |
| `unique` | 一意制約 |
| `choices` / `ge` / `le` | 列挙 / 数値範囲（書き込み時にバリデーション） |
| `description` | 説明（i18n 辞書、設定クラスと同じ形式） |
| `column_type` | SQL の列型定義の上書き |
| `foreign_key` | 列レベルの外部キー制約（`"テーブル.列"`、`REFERENCES` を生成） |
| `on_delete` | 外部キーの削除アクション：`CASCADE` / `SET NULL` / `RESTRICT` / `NO ACTION` / `SET DEFAULT` |
| `auto_now_add` | 挿入時に現在のタイムスタンプ（浮動小数点型のエポック秒）を自動的に書き込む |
| `auto_now` | 挿入時およびインスタンスの `save()` による更新時に自動的に書き込む（`QuerySet.update` の一括パスでは発動しない） |

## 複合主キーと複合一意

複数の `primary_key=True` フィールドで複合主キーを構成し、`get` / `save` / `delete` はすべての主キー列を基にレコードを特定します。
`__unique_together__` で複合一意グループを宣言します（複数グループ可）：

```python
class Membership(Model):
    __tablename__ = "memberships"
    __unique_together__ = (("user_id", "group_id"),)

    user_id: int = Field(primary_key=True)
    group_id: int = Field(primary_key=True)
    role: str = Field(default="member")

m = await Membership.get(user_id=1, group_id=2)
```

- `autoincrement` は複合主キーと排他的であり、共存させるとモデル定義時にエラーが発生します
- `__unique_together__` は一意インデックスで実装されます（インデックス名に `uq_` プレフィックスを付与）：新規テーブルの場合はテーブル作成時に生成され、**既存テーブルに対しては `create_table()` の実行時に自動的に追加作成されます**。再作成は不要です
- 複合主キーのモデルは現時点ではリレーションマッピング（has-many / belongs-to）をサポートしていません。インスタンスアクセス時に明示的にエラーが発生します

## テーブル作成と CRUD

```python
await User.create_table()                      # 冪等（IF NOT EXISTS）

user = await User.create(name="Alice", age=20) # 挿入（オートインクリメント主キーは自動的にインスタンスへ反映）
got = await User.get(id=user.id)               # 等値条件で最初の1件を取得

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # 主キーによる更新（先に制約チェック）。主キーがない場合は挿入にフォールバック（オートインクリメント主キーも同様にインスタンスへ反映）
await user.save(update_fields=["age"])         # 部分カラム更新（ホワイトリスト。それ以外のカラムは書き込まれない）
await user.delete()                            # 主キーによる削除

user, created = await User.get_or_create({"age": 20}, name="Alice")      # 見つかればそのまま返す。なければ作成
user, created = await User.update_or_create({"age": 21}, name="Alice")   # 見つかれば defaults を更新して保存。なければ作成

await User.update_all(User.age > 18, role="adult")  # 一括更新
await User.delete_all(User.age > 100)               # 一括削除
```

> [!NOTE]
> `get_or_create` / `update_or_create` は並行競合下では、2つのコルーチンが同時に作成処理に進む可能性があります——一意制約（主キー / `unique` / `__unique_together__`）により、後から到達した側は `StorageOperationError` を受け取ります。冪等なセマンティクスが必要な場合は、例外を捕捉した後にもう一度再クエリを行ってください。

クエリ式は `> >= < <= == !=`、`in_([...])`、および `&`（AND）/ `|`（OR）の組み合わせをサポートしています：

```python
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all()
```

## トランザクション

ORM の読み書きはフレームワークのストレージ層と同じトランザクションルーティングを共有しています: `storage.atransaction()` のトランザクションコンテキスト内では、`create` / `save` / `delete` およびクエリが自動的にトランザクション接続を再利用し、トランザクションと一体でコミットまたはロールバックされます。単独でコミットされることはありません。

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # ブロック内で例外が発生すると、上の INSERT も一緒にロールバックされます
```

## 宣言型設定クラスとの関係

モデル宣言は `ConfigClass`（`@dataclass + field(metadata=...)`）と**同じ低層を共有**しています。制約語彙、バリデーターエンジン（`validate_field_constraints`）、型カテゴリレジストリ（`python_type_category`）がそれです。ただしクラスの基盤は意図的に分離されています: 設定フィールドはプレーンな値（TOML 往復、一度ロードしてホット更新）、モデルフィールドはカラムデスクリプタ（クラスアクセス = クエリ式、行ごとのインスタンス）。1 つの宣言構文から、それぞれの役割を担う 2 つの基盤が得られます。

### 2 つの宣言の使い分け

| 観点 | 設定クラス `field(metadata=...)` | モデルフィールド `Field()` |
|------|------------------------------|---------------------|
| 適用場面 | モジュールの動作パラメータ（少数、人が読める、ホット更新が必要） | ビジネスデータの記録（多数の行、プログラムによる読み書き、検索が必要） |
| 保存形式 | `config.toml`（コメント保持、TOML 往復） | データベーステーブル（自動テーブル作成、SQL 方言） |
| 値の形式 | プレーンな値（`dataclass` 属性を直接読み取り） | デスクリプタ（クラスアクセス = カラム式、インスタンスアクセス = 行の値） |
| 制約宣言 | `metadata={"choices": ..., "min": ..., "max": ...}` | `Field(choices=..., ge=..., le=..., max_length=...)` |
| 共有基盤 | バリデーターエンジン + 制約語彙 + 型カテゴリレジストリ（共通） | 同左 |

経験則: **「モジュールがどう動くか」は設定クラスで、「ユーザーがどんなデータを生み出したか」はモデルで**扱います。

## 境界と注意点

- バックエンドはグローバルなストレージ設定で決まります。モデルでは `__storage__` クラス属性でカスタム `BaseStorage` インスタンスに上書き可能です（テスト時の注入用）
- `list` / `dict` フィールド（`list[int]`、`dict[str, int]` などのパラメータ化ジェネリクスを含む）は、コンテナ種別ごとに JSON テキストカラムとして保存され、読み書き時に自動シリアライズされます
- 書き込み（`create` / `save`）の前に自動で制約検証が実行され、失敗すると `ValueError`（ローカライズ済みメッセージ）が送出されます
- 自動マイグレーションは**カラム追加**のシナリオに対応済みです（下記参照）。カラム型の変更とカラムの削除は手動で対応する必要があります
- ストレージ接続失敗時の挙動はストレージ層と共通です: フレームワークはクラッシュせず、クールダウン後に自動再接続します

## 自動マイグレーション（フェーズ 2）

`create_table()` はテーブルが既に存在する場合、既存カラムとモデルフィールドを自動的に比較し、**追加されたフィールド**に対して自動で
`ALTER TABLE ADD COLUMN` を実行します（マイグレーション対象カラムは `NOT NULL` 制約を取り除き、既存行には NULL を設定）。
`index=True` を宣言した新規フィールドは、インデックスも同時に作成します。マイグレーションスクリプトを手書きする必要はありません。

```python
# v1 リリース後のモデル進化: email / bio フィールドを追加
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # 追加: 次 の create_table() で自動的に ADD COLUMN
    bio: str = Field(default="")

await User.create_table()              # 冪等: 追加カラムのみをマイグレーション
```

**境界**: サポートしているのはカラム追加のみです。主キーの変更、カラム型の変更、カラム削除は手動で対応してください（破壊的な
ALTER 誤操作を避けるため）。

## 外部キー（リレーションマッピングの基礎）

`foreign_key="テーブル.カラム"` は列レベルの外部キー制約を宣言し、DDL には `REFERENCES` 句が生成されます。`on_delete` は削除時の動作を宣言します（例：`"CASCADE"` は参照行を連鎖的に削除します）：

```python
class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id", on_delete="CASCADE")

    content: str = Field(max_length=255)
```

## リレーションマッピング（relationship）

モデルクラスの本体の中で、クラス属性として `relationship()` を宣言します。**方向は、外部キーカラムがどちらのテーブルで宣言されているかによって自動的に判定されます**:

```python
from ErisPulse.Core.Bases import Model, Field, relationship

class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)

    posts = relationship("Post", foreign_key="author")   # 外部キーは相手側のテーブル → has-many

class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")
    content: str = Field(max_length=255)

    writer = relationship("User", foreign_key="author")  # 外部キーは自テーブル側 → belongs-to
```

**has-many**: インスタンス属性はクエリセットを返し、`QuerySet` の全チェーン機能が利用できます。
`create` を使うと、自テーブルの主キーが相手側の外部キーカラムへ自動的に書き込まれます:

```python
alice = await User.get(name="Alice")

posts = await alice.posts.all()                          # このユーザーの全記事
latest = await alice.posts.order_by("-id").first()
total = await alice.posts.count()
hot = await alice.posts.where(Post.content != "").all()  # 相手テーブルのフィールドに対する条件を追加
await alice.posts.delete()                               # このユーザーのものだけを削除

new_post = await alice.posts.create(content="hi")        # author は自動的に alice.id になる
```

**belongs-to**: `await` するだけで相手のインスタンスが得られます（一致がない場合や外部キーが NULL の場合は `None` を返します）:

```python
post = await Post.get(id=1)
writer = await post.writer          # User インスタンスまたは None
await writer.posts.count()          # 双方向で利用可能
```

**ポイント**:

- `related` にはクラス名の文字列を渡します（モデルクラス名レジストリによって遅延解決され、両側の定義順序は問いません）。モデルクラスを直接渡すことも可能です
- リレーションクエリは相手モデルとそれぞれのストレージバックエンドを使用します（バックエンドをまたぐ JOIN には対応していません。リレーションクエリは独立した 2 本の SQL です）
- リレーションクエリはキャッシュされず、アクセスごとに即時クエリが実行されます。`User.where(...)` を使えば任意のカスタムクエリも引き続き可能です

## 次のステップ

### データベースの変更やクラウドデータベースへのデプロイが必要な場合

- [ストレージバックエンド](../advanced/storage-backends.md) — SQLite / MySQL / PostgreSQL の設定と切り替え。モデルコードは一切変更不要です

### テーブル構造が不要で、少数のキーバリューを保存するだけの場合

- [モジュールのコア概念 - ストレージシステム](modules/core-concepts.md#ストレージシステム) — キーバリューストレージの軽量な使い方。モデルの宣言は不要です