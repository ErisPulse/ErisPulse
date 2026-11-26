# データモデル層（ORM）

> [!TIP]
> **読むタイミング**：データモデル、自動テーブル作成、関係マッピングが必要な場合。不要な場合はスキップしても、他の機能の使用に影響はありません。

> [!NOTE]
> **ORM は非同期ネイティブ**：すべての CRUD 操作（`create` / `get` / `save` / `delete` / `create_table` / QuerySet 終端操作）は `async def` で、イベントループ内で `await` で直接呼び出すだけです。内部ドライバーは aiosqlite / aiomysql / asyncpg（ストレージバックエンドに応じて切り替え）で、同期的なブロッキングは存在しません。KV ストレージの同期 `get`/`set` は互換性層であり、ORM とは無関係です。

2.9.0 以降、フレームワークは宣言的なデータモデル層を内蔵しています。`Model` を継承し、`Field` でフィールドを宣言することで、自動テーブル作成と CRUD 機能が得られます。モデルは内部ストレージ層の上に構築されています。SQLite / MySQL / PostgreSQL は `ErisPulse.storage.backend` で設定され、**バックエンドの切り替えにはモデルコードの変更は不要です**。

## モデルの宣言

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON 列、読み書き時に自動シリアライズ
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "简介"})
```

- テーブル名はデフォルトでクラス名の snake_case（`UserProfile → user_profile`）で、`__tablename__ = "xxx"` で上書き可能
- `Field` の制約語は宣言的設定クラスと同じ（`choices` / `ge` / `le` / `max_length`、`description` は i18n 辞書もサポート）；バリデータエンジンは設定検証と同じソース

## フィールドパラメータ

| パラメータ | 説明 |
|------|------|
| `default` | デフォルト値（指定されておらず、かつ自動インクリメントでない場合 → NOT NULL が必須） |
| `default_factory` | 変更可能なデフォルト値工場（例：`list`） |
| `primary_key` | 主キー（複数ある場合、複合主キーとなり、表レベルの `PRIMARY KEY (a, b)` に収束） |
| `autoincrement` | 自動インクリメント主キー（暗黙の主キー、`create` 後に自動的に戻り値を戻す；単列主キー専用、複合主キーとは互換性がない） |
| `max_length` | 文字列の最大長さ（`VARCHAR(n)` 生成、書き込み時に検証） |
| `nullable` | NULL を許可するかどうか（デフォルトは False） |
| `index` | 普通のインデックスを生成 |
| `unique` | 唯一制約 |
| `choices` / `ge` / `le` | 列挙 / 数値範囲（書き込み時に検証） |
| `description` | 説明（i18n 辞書、設定クラスと同じ形式） |
| `column_type` | SQL 列型定義の上書き |
| `foreign_key` | 列レベルの外部キー制約（`"テーブル.列"`、`REFERENCES` を生成） |
| `on_delete` | 外部キー削除時の動作：`CASCADE` / `SET NULL` / `RESTRICT` / `NO ACTION` / `SET DEFAULT` |
| `auto_now_add` | 挿入時に自動的に現在のタイムスタンプ（秒単位の浮動小数）を書き込む |
| `auto_now` | 挿入時とインスタンス `save()` 更新時、両方で自動的に書き込む（`QuerySet.update` バッチ経路ではトリガーされない） |

## 複合主キーと複合一意

複数の `primary_key=True` フィールドが複合主キーを構成し、`get` / `save` / `delete` はすべての主キー列で位置を特定します。
`__unique_together__` で複合一意グループ（複数可能）を宣言します：

```python
class Membership(Model):
    __tablename__ = "memberships"
    __unique_together__ = (("user_id", "group_id"),)

    user_id: int = Field(primary_key=True)
    group_id: int = Field(primary_key=True)
    role: str = Field(default="member")

m = await Membership.get(user_id=1, group_id=2)
```

- `autoincrement` と複合主キーは互換性がなく、両方を定義するとモデル定義時にエラーになります
- `__unique_together__` は一意インデックスで実現（`uq_` で始まるインデックス名）：新規テーブルではテーブル作成時に自動生成され、**既存のテーブルでは `create_table()` を実行して自動的に補完**されます。再作成は不要です
- 複合主キーを持つモデルは、関係マッピング（has-many / belongs-to）はサポートしておらず、インスタンスアクセス時に明確にエラーになります

## テーブル作成と CRUD

```python
await User.create_table()                      # 幂等（IF NOT EXISTS）

user = await User.create(name="Alice", age=20) # 挿入（自動インクリメント主キーは自動的に戻り値を戻す）
got = await User.get(id=user.id)               # 等価検索で最初のレコードを取得

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # 主キーに基づいて更新（事前制約検証）；主キーが欠落している場合は挿入に退化する（自動インクリメント主キーもインスタンスに戻り値を戻す）
await user.save(update_fields=["age"])         # 部分列更新（ホワイトリスト、他の列は書き込まれない）
await user.delete()                            # 主キーに基づいて削除

user, created = await User.get_or_create({"age": 20}, name="Alice")      # 見つかった場合は戻す；なければ作成
user, created = await User.update_or_create({"age": 21}, name="Alice")   # 見つかったら defaults を更新して保存；なければ作成

await User.update_all(User.age > 18, role="adult")  # バッチ更新
await User.delete_all(User.age > 100)               # バッチ削除
```

> [!NOTE]
> `get_or_create` / `update_or_create` は、並行競合下で2つのコルーチンが同時に作成の分岐に到達する可能性があります。唯一制約（主キー / `unique` / `__unique_together__`）により、後到着者は `StorageOperationError` を受けるでしょう。冪等性が必要な場合は、エラーをキャッチして再度検索してください。

クエリ式は `> >= < <= == !=` をサポートし、`&`（AND）/ `|`（OR）で組み合わせが可能です。IN 条件には `where_in` を使用します：

```python
await User.where(User.age > 18).all()
await User.where_in("name", ["Alice", "Bob"]).all()                       # IN 条件（型チェックに優しい）
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all() # IN と他の条件の組み合わせ（in_ は実行時機能）
```

> [!TIP]
> **型チェックに優しい**：フィールドは値の型注釈（`age: int = Field(...)`）で宣言され、クラスアクセス比較（`User.age > 18`）は mypy / pyright / ty の視点では `bool` ですが、実行時の実際の結果は条件オブジェクトです。条件のエントリポイント（`where` / `count` / `delete_all` / `update_all`）はこの形態を既に互換性を持っています。実際のブール値の引数（SQL にコンパイルできない）は実行時に明確に拒否されます。クエリの戻り値は静的に型付けされています：`first()` / `all()` / `get()` / `create()` の結果はモデルインスタンスであり、フィールドアクセスには完全な型ヒントがあります。
>
> 条件オブジェクトは真偽値評価ができない（`if User.age > 18:` はエラーを投げる）、複数条件の組み合わせは `and` / `or` ではなく `&` / `|` を使用してください。条件構築補助関数の戻り値は `Condition | bool` と注釈することを推奨します。

## トランザクション

ORM の読み書きはフレームワークのストレージ層と同じトランザクションルートを使用します：`storage.atransaction()` 環境内にいる場合、`create` / `save` / `delete` とクエリは自動的にトランザクション接続を再利用し、トランザクションと共にコミットまたはロールバックされます。個別にコミットされることはありません。

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # ブロック内で例外が発生した場合、上の INSERT もロールバックされる
```

## 宣言的設定クラスとの関係

モデルの宣言と `ConfigClass`（`@dataclass + field(metadata=...)`）は**同じ下層を共有**しています。制約語、バリデータエンジン（`validate_field_constraints`）、型カテゴリレジストリ（`python_type_category`）です。しかし、クラスの基盤は意図的に分離されています。設定フィールドは普通の値（TOML との往復、一度のロード後のホットアップデート）であり、モデルフィールドは列の記述子（クラスアクセス = クエリ式、各行のインスタンス）です。同じ宣言構文で、それぞれ異なる役割の基盤です。

### どちらの宣言を使うか

| 維度 | 設定クラス `field(metadata=...)` | モデルフィールド `Field()` |
|------|------------------------------|---------------------|
| 適用場面 | モジュール動作パラメータ（少量、人間が読みやすい、ホットアップデートが必要） | 業務データレコード（複数行、プログラムによる読み書き、クエリが必要） |
| ストレージ形態 | `config.toml`（コメントが保持され、TOML との往復） | データベーステーブル（自動テーブル作成、SQL バリアント） |
| 値形態 | 普通の値（`dataclass` 属性の直読み） | 記述子（クラスアクセス = 列式、インスタンスアクセス = 行値） |
| 制約宣言 | `metadata={"choices": ..., "min": ..., "max": ...}` | `Field(choices=..., ge=..., le=..., max_length=...)` |
| 共有下層 | バリデータエンジン + 制約語 + 型カテゴリレジストリ（同じもの） | 同左 |

経験則：**「モジュールがどのように動作するか」は設定クラス、「ユーザーが生成したデータ」はモデル**。

## バウンダリと注意事項

- バックエンドはグローバルなストレージ設定によって決定されます。モデルは `__storage__` クラス属性でカスタム SQL ストレージバックエンドインスタンス（`SQLStorageBase`）に上書きして使用できます（テスト注入用）
- `list` / `dict` フィールド（パラメータ化されたジェネリック `list[int]`、`dict[str, int]` を含む）はコンテナのカテゴリに応じて JSON テキスト列として保存され、読み書き時に自動的にシリアライズされます
- 書き込み（`create` / `save`）の前に自動的に制約検証が実行され、失敗すると `ValueError`（ローカライズされたメッセージ）が送出されます
- 自動移行は**追加列**のシナリオに提供されています（下記参照）；列の型変更や削除は手動で処理する必要があります
- ストレージ接続の失敗時に発生する動作は、ストレージ層と同じです：フレームワークはクラッシュせず、冷却後に自動的に再接続されます

## 自動移行（段階2）

`create_table()` は、テーブルが存在する場合、既存の列とモデルフィールドを自動的に比較します。**追加されたフィールド**は、`ALTER TABLE ADD COLUMN` を実行し、移行列の `NOT NULL` 制約を削除し、既存の行に NULL を戻します。宣言された `index=True` の新しいフィールドは、同期的にインデックスを構築します。手動で移行スクリプトを書く必要はありません。

```python
# v1 上線後のモデル進化：email / bio フィールドの追加
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # 追加：次回の create_table() で自動 ADD COLUMN
    bio: str = Field(default="")

await User.create_table()              # 幂等：追加された列のみを移行
```

**バウンダリ**：追加列のみをサポートします。主キーの変更、列の型変更、列の削除は手動で処理する必要があります（破壊的な ALTER の誤操作を避けるため）。

## 外部キー（関係マッピングの基礎）

`foreign_key="テーブル.列"` で列レベルの外部キー制約を宣言し、DDL で `REFERENCES` 子句を生成します。`on_delete` で削除時の動作を宣言します（例：`"CASCADE"` で参照行を連鎖削除）：

```python
class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id", on_delete="CASCADE")

    content: str = Field(max_length=255)
```

## 関係マッピング（relationship）

モデルクラス内で `relationship()` をクラス属性として宣言することで、**方向は外部キー列がどのテーブルに宣言されているかによって自動的に判定されます**：

```python
from ErisPulse.Core.Bases import Model, Field, relationship

class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)

    posts = relationship("Post", foreign_key="author")   # 外部キーが相手のテーブルにある → has-many

class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")
    content: str = Field(max_length=255)

    writer = relationship("User", foreign_key="author")  # 外部キーがこのテーブルにある → belongs-to
```

**has-many**：インスタンス属性はクエリセットを返し、`QuerySet` のすべてのチェーン操作が利用可能。`create` は自動的にこのテーブルの主キーを相手の外部キー列に回填します：

```python
alice = await User.get(name="Alice")

posts = await alice.posts.all()                          # このユーザーのすべての記事
latest = await alice.posts.order_by("-id").first()
total = await alice.posts.count()
hot = await alice.posts.where(Post.content != "").all()  # 相手のテーブルのフィールド条件を追加
await alice.posts.delete()                               # このユーザーの記事だけを削除
new_post = await alice.posts.create(content="hi")        # author は自動的に alice.id に設定される
```

**belongs-to**：`await` で相手のインスタンスを得る（一致するものがないか、外部キーが NULL の場合は `None` を返す）：

```python
post = await Post.get(id=1)
writer = await post.writer          # User インスタンスまたは None
await writer.posts.count()          # 双方向にアクセス可能
```

**ポイント**：

- `related` にはクラス名の文字列（モデルクラス名の登録表に惰性で解析、両方の定義順序は無関係）または直接モデルクラスを渡す
- 関係クエリと相手のモデルはそれぞれのストレージバックエンドを使用する（バックエンド間の JOIN はサポートしない——関係クエリは独立した2つの SQL である）
- 関係クエリはキャッシュされず、毎回アクセス時に即時クエリが実行される；`User.where(...)` を使って任意のカスタムクエリを実行することも可能

## 次に進む

### データベースを変更する、またはクラウドデータベースにデプロイする必要がある

- [ストレージバックエンド](../advanced/storage-backends.md) — SQLite / MySQL / PostgreSQL の設定と切り替え、モデルコードの変更は不要

### テーブル構造は必要なく、いくつかのキー値だけを保存したい

- [モジュールのコアコンセプト - ストレージシステム](modules/core-concepts.md#ストレージシステム) — キーバリューストレージの軽量な使い方、モデルの宣言は不要