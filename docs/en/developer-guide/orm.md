# Data Model Layer (ORM)

> [!TIP]
> **When to read this**: When you need data models, automatic table creation, or relationship mapping. Skip it if not needed—it won't affect the use of other features.

> [!NOTE]
> **The ORM is async-native**: All CRUD methods (`create` / `get` / `save` / `delete` / `create_table` / QuerySet terminal operations) are `async def` and can simply be `await`ed inside the event loop—the underlying drivers are aiosqlite / aiomysql / asyncpg (switched along with the storage backend), so there is no synchronous blocking. The synchronous `get`/`set` of KV storage is a compatibility layer, unrelated to the ORM.

Since 2.9.0, the framework ships with a built-in declarative data model layer: inherit `Model` and declare fields with `Field` to gain automatic table creation and full CRUD capabilities. Models are built directly on top of the built-in storage layer—SQLite / MySQL / PostgreSQL is determined by the `ErisPulse.storage.backend` configuration, and **switching backends requires no changes to model code**.

## Declaring Models

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON column, automatically serialized on read/write
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "Bio"})
```

- The table name defaults to the snake_case form of the class name (`UserProfile → user_profile`); override it with `__tablename__ = "xxx"`
- The `Field` constraint vocabulary is identical to that of declarative config classes (`choices` / `ge` / `le` / `max_length`; `description` likewise supports i18n dictionaries); the validator engine shares the same origin as config validation

## Field Parameters

| Parameter | Description |
|------|------|
| `default` | Default value (when not provided and not autoincrement → required NOT NULL) |
| `default_factory` | Factory for mutable default values (e.g., `list`) |
| `primary_key` | Primary key (multiple ones form a composite primary key, consolidated into a table-level `PRIMARY KEY (a, b)`) |
| `autoincrement` | Auto-increment primary key (implies a primary key; automatically backfilled after `create`; dedicated to single-column primary keys, mutually exclusive with composite primary keys) |
| `max_length` | Maximum string length (generates `VARCHAR(n)`, validated on write) |
| `nullable` | Whether NULL is allowed (default False) |
| `index` | Creates a regular index |
| `unique` | Unique constraint |
| `choices` / `ge` / `le` | Enumeration / numeric range (validated on write) |
| `description` | Description (i18n dictionary, same format as config classes) |
| `column_type` | Overrides the SQL column type definition |
| `foreign_key` | Column-level foreign key constraint (`"table.column"`, generates `REFERENCES`) |
| `on_delete` | Foreign key delete action: `CASCADE` / `SET NULL` / `RESTRICT` / `NO ACTION` / `SET DEFAULT` |
| `auto_now_add` | Automatically writes the current timestamp (float epoch seconds) on insert |
| `auto_now` | Automatically written on both insert and instance `save()` updates (not triggered by the `QuerySet.update` bulk path) |

## Composite Primary Keys and Unique-Together Constraints

Multiple `primary_key=True` fields form a composite primary key; `get` / `save` / `delete` locate rows by all primary key columns;
`__unique_together__` declares unique-together groups (multiple groups allowed):

```python
class Membership(Model):
    __tablename__ = "memberships"
    __unique_together__ = (("user_id", "group_id"),)

    user_id: int = Field(primary_key=True)
    group_id: int = Field(primary_key=True)
    role: str = Field(default="member")

m = await Membership.get(user_id=1, group_id=2)
```

- `autoincrement` is mutually exclusive with composite primary keys; having both raises an error right at model definition
- `__unique_together__` is implemented as unique indexes (index names prefixed with `uq_`): generated together with newly created tables, and **for existing tables, running `create_table()` adds them automatically**—no rebuild needed
- Composite primary key models do not yet support relationship mapping (has-many / belongs-to); accessing relationships on their instances raises a clear error

## Table Creation and CRUD

```python
await User.create_table()                      # idempotent (IF NOT EXISTS)

user = await User.create(name="Alice", age=20) # insert (auto-increment primary key backfilled automatically)
got = await User.get(id=user.id)               # first row of an equality query

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # update by primary key (constraints validated first); falls back to insert when the primary key is missing (auto-increment keys are likewise backfilled onto the instance)
await user.save(update_fields=["age"])         # partial column update (whitelist; other columns are not written)
await user.delete()                            # delete by primary key

user, created = await User.get_or_create({"age": 20}, name="Alice")      # returns it if found; creates it otherwise
user, created = await User.update_or_create({"age": 21}, name="Alice")   # updates defaults and saves if found; creates otherwise

await User.update_all(User.age > 18, role="adult")  # bulk update
await User.delete_all(User.age > 100)               # bulk delete
```

> [!NOTE]
> Under concurrent contention, two coroutines in `get_or_create` / `update_or_create` may both reach the creation branch—unique constraints (primary key / `unique` / `__unique_together__`) will make the later one receive a `StorageOperationError`; when idempotent semantics are needed, catch it and re-query once.

Query expressions support `> >= < <= == !=`, `in_([...])`, and combinations with `&` (AND) / `|` (OR):

```python
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all()
```

## Transactions

ORM reads and writes share the same transaction routing as the framework's storage layer: when inside an ambient `storage.atransaction()` transaction, `create` / `save` / `delete` and queries automatically reuse the transaction connection and are committed or rolled back together with the transaction, never committing independently.

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # if an exception is raised inside the block, the INSERT above is rolled back as well
```

## Relationship with Declarative Config Classes

Model declarations and `ConfigClass` (`@dataclass + field(metadata=...)`) **share the same underlying machinery**—the constraint vocabulary, the validator engine (`validate_field_constraints`), and the type category registry (`python_type_category`); but the class foundations are deliberately separate: config fields are plain values (TOML round-trip, hot-reloaded on load), while model fields are column descriptors (class access = query expressions, one instance per row). One declaration syntax, two foundations each serving its own purpose.

### When to Use Which Declaration

| Dimension | Config class `field(metadata=...)` | Model field `Field()` |
|------|------------------------------|---------------------|
| Applicable scenarios | Module behavior parameters (few, human-readable, hot-reloadable) | Business data records (many rows, programmatic read/write, queryable) |
| Storage form | `config.toml` (comments preserved, TOML round-trip) | Database tables (automatic table creation, SQL dialects) |
| Value form | Plain values (read directly as `dataclass` attributes) | Descriptors (class access = column expression, instance access = row value) |
| Constraint declaration | `metadata={"choices": ..., "min": ..., "max": ...}` | `Field(choices=..., ge=..., le=..., max_length=...)` |
| Shared foundation | Validator engine + constraint vocabulary + type category registry (the same set) | Same as left |

Rule of thumb: **use config classes for "how a module behaves"; use models for "what data users produce"**.

## Boundaries and Caveats

- The backend is determined by the global storage configuration; a model may override it with a custom `BaseStorage` instance via the `__storage__` class attribute (for test injection)
- `list` / `dict` fields (including parameterized generics such as `list[int]`, `dict[str, int]`) are stored as JSON text columns by container category, automatically serialized on read/write
- Constraint validation runs automatically before writes (`create` / `save`); failures raise `ValueError` (localized messages)
- Automatic migration already covers the **add-column** scenario (see below); column type changes and column drops require manual handling
- Behavior on storage connection failure is consistent with the storage layer: the framework does not crash and automatically reconnects after a cooldown

## Automatic Migration (Phase Two)

When the table already exists, `create_table()` automatically compares the existing columns against the model fields: **newly added fields** are automatically applied via `ALTER TABLE ADD COLUMN` (migrated columns drop the `NOT NULL` constraint; existing rows are backfilled with NULL), and new fields declared with `index=True` get their indexes created at the same time. No need to write migration scripts by hand.

```python
# Model evolution after v1 ships: adding the email / bio fields
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # New: ADD COLUMN runs automatically on the next create_table()
    bio: str = Field(default="")

await User.create_table()              # idempotent: only migrates newly added columns
```

**Boundaries**: only adding columns is supported; primary key changes, column type changes, and column drops require manual handling (to avoid destructive ALTER mistakes).

## Foreign Keys (Foundation for Relationship Mapping)

`foreign_key="table.column"` declares a column-level foreign key constraint, and the DDL generates a `REFERENCES` clause; `on_delete` declares the delete action (e.g., `"CASCADE"` to cascade-delete referencing rows):

```python
class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id", on_delete="CASCADE")

    content: str = Field(max_length=255)
```

## Relationship Mapping (relationship)

Declare `relationship()` as class attributes in the model class body; **the direction is determined automatically by which table the foreign key column is declared in**:

```python
from ErisPulse.Core.Bases import Model, Field, relationship

class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)

    posts = relationship("Post", foreign_key="author")   # foreign key in the other table → has-many

class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")
    content: str = Field(max_length=255)

    writer = relationship("User", foreign_key="author")  # foreign key in this table → belongs-to
```

**has-many**: the instance attribute returns a queryset with all `QuerySet` chaining capabilities available, and `create` automatically backfills this table's primary key into the other table's foreign key column:

```python
alice = await User.get(name="Alice")

posts = await alice.posts.all()                          # all posts by this user
latest = await alice.posts.order_by("-id").first()
total = await alice.posts.count()
hot = await alice.posts.where(Post.content != "").all()  # appending conditions on the other table's fields
await alice.posts.delete()                               # deletes only this user's posts

new_post = await alice.posts.create(content="hi")        # author automatically = alice.id
```

**belongs-to**: directly `await` to obtain the other side's instance (returns `None` when there is no match or the foreign key is NULL):

```python
post = await Post.get(id=1)
writer = await post.writer          # a User instance or None
await writer.posts.count()          # works in both directions
```

**Key points**:

- `related` accepts a class-name string (resolved lazily via the model class-name registry, regardless of definition order on either side) or the model class directly
- Relationship queries and the related model each use their own storage backend (cross-backend JOIN is not supported—a relationship query is two independent SQL statements)
- Relationship queries are not cached; every access performs a live query. For arbitrary custom queries, you can still use `User.where(...)`

## Next Steps

### Switching Databases or Deploying to a Cloud Database

- [Storage Backends](../advanced/storage-backends.md) — Configuration and switching for SQLite / MySQL / PostgreSQL, with zero changes to model code

### No Table Schema Needed, Just Storing a Few Key-Value Pairs

- [Module Core Concepts - Storage System](modules/core-concepts.md#storage-system) — Lightweight key-value storage usage, no model declaration required