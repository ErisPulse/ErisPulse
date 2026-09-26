# Data Model Layer (ORM)

Starting from version 2.9.0, the framework includes a built-in declarative data model layer: by inheriting from `Model` and declaring fields using `Field`, you gain automatic table creation and CRUD capabilities. The model is built directly on the built-in storage layer—SQLite / MySQL / PostgreSQL is determined by the `ErisPulse.storage.backend` configuration. **Switching the backend does not require modifying the model code.**

## Declaring Models

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON column, automatically serialized on read/write
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "Biography"})
```

- The table name defaults to the class name in snake_case (`UserProfile → user_profile`), and can be overwritten using `__tablename__ = "xxx"`
- The constraint list for `Field` is consistent with the declarative configuration class (`choices` / `ge` / `le` / `max_length`, `description` also supports i18n dictionaries); the validator engine is the same as that used for configuration validation

## Field Parameters

| Parameter | Description |
|-----------|-------------|
| `default` | Default value (required if not provided and not auto-incremented → NOT NULL) |
| `default_factory` | Factory for mutable default values (e.g., `list`) |
| `primary_key` | Primary key |
| `autoincrement` | Auto-incrementing primary key (implicitly a primary key, auto-filled after `create`) |
| `max_length` | Maximum string length (generates `VARCHAR(n)`, validates on write) |
| `nullable` | Whether NULL is allowed (default False) |
| `index` | Generates a regular index |
| `unique` | Unique constraint |
| `choices` / `ge` / `le` | Enum / numeric range (validates on write) |
| `description` | Description (i18n dictionary, same format as configuration class) |
| `column_type` | Override the SQL column type definition |

## Table Creation and CRUD

```python
await User.create_table()                      # Idempotent (IF NOT EXISTS)

user = await User.create(name="Alice", age=20) # Insert (auto-incremented primary key automatically filled back)
got = await User.get(id=user.id)               # Equality query for the first record

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # Update by primary key (first validates constraints); if primary key is missing, falls back to insert (auto-incremented primary key is also filled back into the instance)
await user.delete()                            # Delete by primary key

await User.update_all(User.age > 18, role="adult")  # Bulk update
await User.delete_all(User.age > 100)               # Bulk delete
```

Query expressions support `> >= < <= == !=` and `in_([...])`, as well as `&` (AND) / `|` (OR) combinations:

```python
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all()
```

## Transactions

ORM reads and writes share the same transaction routing as the framework's storage layer: when inside a `storage.atransaction()` environment, `create` / `save` / `delete` and queries automatically reuse the transaction connection, committing or rolling back together with the transaction, without independent commits.

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # If an exception is thrown within the block, the above INSERT is rolled back
```

## Relationship with Declarative Configuration Class

Model declarations and `ConfigClass` (`@dataclass + field(metadata=...)`) **share the same underlying system**—constraint lists, validator engine (`validate_field_constraints`), and type category registry (`python_type_category`); however, the class bases are intentionally separated: configuration fields are ordinary values (TOML round-trip, hot reload on load), while model fields are column descriptors (class access = query expression, instance access = row value). One declaration syntax, two distinct bases.

### When to Use Which Declaration

| Dimension | Configuration Class `field(metadata=...)` | Model Field `Field()` |
|-----------|-------------------------------------------|------------------------|
| Use Case | Module behavior parameters (few, human-readable, requiring hot reload) | Business data records (multiple rows, programmatic read/write, requiring queries) |
| Storage Form | `config.toml` (comments preserved, TOML round-trip) | Database table (automatic table creation, SQL dialect) |
| Value Form | Ordinary value (`dataclass` attribute direct read) | Descriptor (class access = column expression, instance access = row value) |
| Constraint Declaration | `metadata={"choices": ..., "min": ..., "max": ...}` | `Field(choices=..., ge=..., le=..., max_length=...)` |
| Shared Underlying | Validator engine + constraint list + type category registry (same set) | Same as above |

Rule of thumb: **Use configuration classes for "how the module runs," and models for "what data the user generates."**

## Boundaries and Notes

- The backend is determined by the global storage configuration; models can overwrite the `__storage__` class attribute to use a custom `BaseStorage` instance (for testing injection)
- `list` / `dict` fields (including parameterized generics like `list[int]`, `dict[str, int]`) are stored as JSON text columns, automatically serialized on read/write
- Constraints are automatically validated before writing (`create` / `save`), failing to throw `ValueError` (localized message)
- Automatic migration is delivered for **new column** scenarios (see below); column type changes and column removal require manual handling
- When storage connection fails, the behavior is consistent with the storage layer: the framework does not crash, and automatic reconnection occurs after cooling

## Automatic Migration (Phase Two)

`create_table()` automatically compares existing columns with model fields when the table already exists: **new fields** automatically execute `ALTER TABLE ADD COLUMN` (migrating column to remove `NOT NULL` constraint, filling NULL for existing rows), and new fields with `index=True` are synchronized with index creation. No manual migration scripts are required.

```python
# After v1 launch, model evolution: adding email / bio fields
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # New: next `create_table()` automatically ADD COLUMN
    bio: str = Field(default="")

await User.create_table()              # Idempotent: only migrates new columns
```

**Boundary**: Only supports adding columns; primary key changes, column type changes, and column removal require manual handling (to avoid destructive ALTER misoperations).

## Foreign Keys (Foundation for Relationship Mapping)

`foreign_key="table.column"` declares column-level foreign key constraints, generating `REFERENCES` clause in DDL:

```python
class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")

    content: str = Field(max_length=255)
```

## Relationship Mapping (relationship)

In the model class body, declare `relationship()` as a class attribute; **the direction is automatically determined by where the foreign key column is declared**:

```python
from ErisPulse.Core.Bases import Model, Field, relationship

class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)

    posts = relationship("Post", foreign_key="author")   # Foreign key in the other table → has-many

class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")
    content: str = Field(max_length=255)

    writer = relationship("User", foreign_key="author")  # Foreign key in this table → belongs-to
```

**Has-Many**: The instance attribute returns a query set, and all `QuerySet` chainable capabilities are available; `create` automatically fills the primary key of this table into the foreign key column of the other table:

```python
alice = await User.get(name="Alice")

posts = await alice.posts.all()                          # All posts of this user
latest = await alice.posts.order_by("-id").first()
total = await alice.posts.count()
hot = await alice.posts.where(Post.content != "").all()  # Add conditions from the other table's fields
await alice.posts.delete()                               # Delete only this user's posts

new_post = await alice.posts.create(content="hi")        # author automatically = alice.id
```

**Belongs-To**: Direct `await` returns the other instance (returns `None` if no match or foreign key is NULL):

```python
post = await Post.get(id=1)
writer = await post.writer          # User instance or None
await writer.posts.count()          # Bidirectional access
```

**Key Points**:

- `related` accepts a class name string (lazily resolved by the model class name registry, order of definition on both sides is irrelevant) or directly passes the model class
- Relationship queries and the other model use their respective storage backends (cross-backend JOINs are not supported—relationship queries are independent SQL statements)
- Relationship queries are not cached; each access is an immediate query; use `User.where(...)` for any custom queries