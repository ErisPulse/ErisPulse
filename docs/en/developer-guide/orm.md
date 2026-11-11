# Data Model Layer (ORM)

> [!TIP]
> **When to read this**: When you need data models, automatic table creation, or relationship mapping. Otherwise skip it—doing so won't affect any other features.

> [!NOTE]
> **The ORM is async-native**: All CRUD methods (`create` / `get` / `save` / `delete` / `create_table` / QuerySet terminal operations) are `async def`; simply `await` them inside the event loop—the underlying drivers are aiosqlite / aiomysql / asyncpg (switched along with the storage backend), so there is no synchronous blocking. The synchronous `get`/`set` of the KV storage is a compatibility layer and has nothing to do with the ORM.


Starting with 2.9.0, the framework ships with a built-in declarative data model layer: inherit from `Model` and declare fields with `Field` to gain automatic table creation and full CRUD capabilities. Models are built directly on top of the built-in storage layer—SQLite / MySQL / PostgreSQL is determined by the `ErisPulse.storage.backend` configuration, and **switching backends requires no changes to model code**.

## Declaring Models

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON column, auto-serialized on read/write
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "Bio"})
```

- The table name defaults to the class name in snake_case (`UserProfile → user_profile`); override it with `__tablename__ = "xxx"`
- The `Field` constraint vocabulary matches that of declarative config classes (`choices` / `ge` / `le` / `max_length`; `description` likewise supports i18n dictionaries); the validator engine shares the same origin as config validation

## Field Parameters

| Parameter | Description |
|------|------|
| `default` | Default value (required NOT NULL if omitted and not auto-increment) |
| `default_factory` | Factory for mutable defaults (e.g., `list`) |
| `primary_key` | Primary key |
| `autoincrement` | Auto-increment primary key (implies primary key; auto-populated after `create`) |
| `max_length` | Maximum string length (generates `VARCHAR(n)`, validated on write) |
| `nullable` | Whether NULL is allowed (defaults to False) |
| `index` | Creates a regular index |
| `unique` | Unique constraint |
| `choices` / `ge` / `le` | Enumeration / numeric range (validated on write) |
| `description` | Description (i18n dictionary, same format as config classes) |
| `column_type` | Overrides the SQL column type definition |

## Table Creation and CRUD

```python
await User.create_table()                      # Idempotent (IF NOT EXISTS)

user = await User.create(name="Alice", age=20) # Insert (auto-increment primary key auto-populated)
got = await User.get(id=user.id)               # First row of an equality query

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # Update by primary key (constraint-validated first); falls back to insert when the primary key is missing (auto-increment primary keys are likewise backfilled to the instance)
await user.delete()                            # Delete by primary key

await User.update_all(User.age > 18, role="adult")  # Bulk update
await User.delete_all(User.age > 100)               # Bulk delete
```

Query expressions support `> >= < <= == !=`, `in_([...])`, and combination via `&` (AND) / `|` (OR):

```python
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all()
```

## Transactions

ORM reads and writes share the same transaction routing as the framework's storage layer: when inside an ambient transaction from `storage.atransaction()`, `create` / `save` / `delete` and queries automatically reuse the transaction connection, committing or rolling back together with the transaction instead of committing independently.

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # If an exception is raised inside the block, the INSERT above is rolled back as well
```

## Relationship with Declarative Config Classes

Model declarations and `ConfigClass` (`@dataclass + field(metadata=...)`) **share the same underlying machinery**—the constraint vocabulary, the validator engine (`validate_field_constraints`), and the type category registry (`python_type_category`); but the class bases are deliberately kept separate: config fields are plain values (TOML round-trip, hot reload on a single load), while model fields are column descriptors (class access = query expression, one instance per row). One declaration syntax, two bases, each serving its own purpose.

### When to Use Which Declaration

| Dimension | Config class `field(metadata=...)` | Model field `Field()` |
|------|------------------------------|---------------------|
| Use case | Module behavior parameters (few, human-readable, hot-reloadable) | Business data records (many rows, read/written programmatically, queryable) |
| Storage form | `config.toml` (comments preserved, TOML round-trip) | Database table (automatic table creation, SQL dialects) |
| Value form | Plain values (read directly as `dataclass` attributes) | Descriptors (class access = column expression, instance access = row value) |
| Constraint declaration | `metadata={"choices": ..., "min": ..., "max": ...}` | `Field(choices=..., ge=..., le=..., max_length=...)` |
| Shared foundation | Validator engine + constraint vocabulary + type category registry (one and the same) | Same as left |

Rule of thumb: **use config classes for "how the module runs," and models for "what data the user produces."**

## Boundaries and Caveats

- The backend is determined by the global storage configuration; a model can override it via the `__storage__` class attribute with a custom `BaseStorage` instance (for test injection)
- `list` / `dict` fields (including parameterized generics such as `list[int]`, `dict[str, int]`) are stored as JSON text columns by container category, auto-serialized on read/write
- Constraint validation runs automatically before writes (`create` / `save`); failure raises `ValueError` (with localized messages)
- Automatic migration covers the **add column** scenario (see below); column type changes and column drops must be handled manually
- Behavior on storage connection failure is consistent with the storage layer: it does not crash the framework and automatically reconnects after a cooldown

## Automatic Migration (Phase Two)

When the table already exists, `create_table()` automatically compares the existing columns against the model fields: **newly added fields** are automatically applied via
`ALTER TABLE ADD COLUMN` (migrated columns drop the `NOT NULL` constraint, and existing rows are backfilled with NULL),
and new fields declared with `index=True` get their indexes created in sync. No need to hand-write migration scripts.

```python
# Model evolution after v1 launch: add email / bio fields
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # New: the next create_table() automatically runs ADD COLUMN
    bio: str = Field(default="")

await User.create_table()              # Idempotent: migrates only newly added columns
```

**Boundaries**: Only adding columns is supported; primary key changes, column type changes, and column drops must be handled manually (to avoid accidental destructive
ALTER operations).

## Foreign Keys (Foundation for Relationship Mapping)

`foreign_key="table.column"` declares a column-level foreign key constraint, and the DDL generates a `REFERENCES` clause:

```python
class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")

    content: str = Field(max_length=255)
```

## Relationship Mapping (relationship)

Declare `relationship()` as class attributes inside the model class body; **the direction is determined automatically based on which table the foreign key column is declared in**:

```python
from ErisPulse.Core.Bases import Model, Field, relationship

class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)

    posts = relationship("Post", foreign_key="author")   # Foreign key is on the other table → has-many

class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")
    content: str = Field(max_length=255)

    writer = relationship("User", foreign_key="author")  # Foreign key is on this table → belongs-to
```

**has-many**: the instance attribute returns a query set with the full `QuerySet` chaining capabilities available,
and `create` automatically backfills this table's primary key into the other side's foreign key column:

```python
alice = await User.get(name="Alice")

posts = await alice.posts.all()                          # All posts of this user
latest = await alice.posts.order_by("-id").first()
total = await alice.posts.count()
hot = await alice.posts.where(Post.content != "").all()  # Append conditions on the other table's fields
await alice.posts.delete()                               # Deletes only this user's posts

new_post = await alice.posts.create(content="hi")        # author automatically = alice.id
```

**belongs-to**: directly `await` to obtain the other side's instance (returns `None` if there is no match or the foreign key is NULL):

```python
post = await Post.get(id=1)
writer = await post.writer          # User instance or None
await writer.posts.count()          # Works in both directions
```

**Key points**:

- Pass `related` a class-name string (lazily resolved via the model class-name registry, independent of definition order on either side) or the model class directly
- Relationship queries and the related model each use their own storage backend (cross-backend JOIN is not supported—relationship queries are two independent SQL statements)
- Relationship queries are not cached; every access is an immediate query. You can still use `User.where(...)` for arbitrary custom queries

## Next Steps

### Need to switch databases or deploy to a cloud database

- [Storage Backends](../advanced/storage-backends.md) — Configuration and switching of SQLite / MySQL / PostgreSQL, with zero changes to model code

### No table structure needed, just a few key-value pairs

- [Module Core Concepts - Storage System](modules/core-concepts.md#storage-system) — Lightweight key-value storage usage, no model declaration required