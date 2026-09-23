# Data Model Layer (ORM)

Starting from version 2.9.0, the framework includes a built-in declarative data model layer: by inheriting `Model` and declaring fields with `Field`, you gain automatic table creation and CRUD capabilities. The model is built directly on top of the built-in storage layer—SQLite / MySQL / PostgreSQL is determined by `ErisPulse.storage.backend` configuration. **Switching the backend does not require modifying model code**.

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
- The constraint word table of `Field` is consistent with the declarative configuration class (`choices` / `ge` / `le` / `max_length`, `description` also supports i18n dictionary); the validator engine is the same as configuration validation

## Field Parameters

| Parameter | Description |
|-----------|-------------|
| `default` | Default value (required NOT NULL if not provided and not auto-increment) |
| `default_factory` | Factory for mutable default values (e.g. `list`) |
| `primary_key` | Primary key |
| `autoincrement` | Auto-incrementing primary key (implicitly a primary key; auto-filled after `create`) |
| `max_length` | Maximum string length (generates `VARCHAR(n)`, validates on write) |
| `nullable` | Whether NULL is allowed (default False) |
| `index` | Generates a regular index |
| `unique` | Unique constraint |
| `choices` / `ge` / `le` | Enum / numeric range (validates on write) |
| `description` | Description (i18n dictionary, same format as configuration class) |
| `column_type` | Override SQL column type definition |

## Table Creation and CRUD

```python
await User.create_table()                      # Idempotent (IF NOT EXISTS)

user = await User.create(name="Alice", age=20) # Insert (auto-incremented primary key auto-filled)
got = await User.get(id=user.id)               # Equal-value query for the first record

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # Update by primary key (first constraint validation); if primary key is missing, it falls back to insert (auto-incremented primary key is still filled back into the instance)
await user.delete()                            # Delete by primary key

await User.update_all(User.age > 18, role="adult")  # Batch update
await User.delete_all(User.age > 100)               # Batch delete
```

Query expressions support `> >= < <= == !=`, `in_([...])`, and combination with `&` (AND) / `|` (OR):

```python
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all()
```

## Transactions

ORM read/write operations share the same transaction routing as the framework’s storage layer: when inside an `storage.atransaction()` environment, `create` / `save` / `delete` and queries automatically reuse the transaction connection, committing or rolling back together with the transaction, and do not submit independently.

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # If an exception is thrown within the block, the above INSERT is rolled back as well
```

## Relationship with Declarative Configuration Classes

Model declaration and `ConfigClass` (`@dataclass + field(metadata=...)`) **share the same underlying system**—constraint word table, validator engine (`validate_field_constraints`), type category registry (`python_type_category`); but the class base is intentionally separated: configuration fields are ordinary values (TOML round-trip, hot reload on one-time load), while model fields are column descriptors (class access = query expression, row-by-row instance). One declaration syntax, two distinct bases.

## Boundaries and Precautions

- The backend is determined by global storage configuration; models can overwrite the `__storage__` class attribute to use a custom `BaseStorage` instance (for testing injection)
- `list` / `dict` fields (including parameterized generics like `list[int]`, `dict[str, int]`) are stored as JSON text columns based on container categories, automatically serialized on read/write
- Constraint validation is automatically executed before writing (`create` / `save`), and throws `ValueError` if it fails (localized message)
- Automatic migration is delivered for **new column** scenarios (see below); column type changes and column deletion require manual handling
- When storage connection fails, the behavior is consistent with the storage layer: the framework does not crash, and automatically reconnects after cooling

## Automatic Migration (Phase Two)

`create_table()` automatically compares existing columns with model fields when the table already exists: **new fields** automatically execute `ALTER TABLE ADD COLUMN` (migrate column to remove `NOT NULL` constraint, fill NULL for existing rows), and new fields with `index=True` are also indexed. No manual migration scripts are required.

```python
# After v1 launch, model evolution: add email / bio fields
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # New: next `create_table()` will automatically ADD COLUMN
    bio: str = Field(default="")

await User.create_table()              # Idempotent: only migrate new columns
```

**Boundary**: Only supports adding new columns; primary key changes, column type changes, and column deletion require manual handling (to avoid destructive `ALTER` misoperations).

## Foreign Keys (Foundation for Relationship Mapping)

`foreign_key="table.column"` declares column-level foreign key constraints, and DDL generates `REFERENCES` clause:

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

**Has-Many**: The instance attribute returns a query set, and all `QuerySet` chaining capabilities are available. `create` automatically fills the primary key of this table into the foreign key column of the other table:

```python
alice = await User.get(name="Alice")

posts = await alice.posts.all()                          # All posts of this user
latest = await alice.posts.order_by("-id").first()
total = await alice.posts.count()
hot = await alice.posts.where(Post.content != "").all()  # Add conditions on the other table's fields
await alice.posts.delete()                               # Delete only this user's posts

new_post = await alice.posts.create(content="hi")        # author automatically = alice.id
```

**Belongs-To**: Directly `await` to get the other instance (returns `None` if no match or foreign key is NULL):

```python
post = await Post.get(id=1)
writer = await post.writer          # User instance or None
await writer.posts.count()          # Bidirectional access
```

**Key Points**:

- `related` accepts a class name string (lazily resolved by the model class name registry, order of definition on both sides is irrelevant) or directly passes the model class
- Relationship queries and the other model use their respective storage backends (cross-backend JOIN is not supported—relationship queries are two independent SQL statements)
- Relationship queries are not cached; each access is an immediate query; use `User.where(...)` for any custom query