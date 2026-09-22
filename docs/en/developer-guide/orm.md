# Data Model Layer (ORM)

Starting from version 2.9.0, the framework includes a built-in declarative data model layer: by inheriting `Model` and declaring fields using `Field`, you automatically gain capabilities for table creation and CRUD operations. The models are built directly on top of the built-in storage layer—SQLite, MySQL, or PostgreSQL is determined by the `ErisPulse.storage.backend` configuration. **Switching the backend requires no changes to the model code.**

## Model Declaration

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON column, automatically serialized on read/write
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "Introduction"})
```

- The table name is automatically derived from the class name in snake_case (`UserProfile → user_profile`), and can be overridden using `__tablename__ = "xxx"`
- The constraint options for `Field` are consistent with the declarative configuration class (`choices` / `ge` / `le` / `max_length`, `description` also supports i18n dictionary); the validator engine shares the same source as configuration validation

## Field Parameters

| Parameter | Description |
|-----------|-------------|
| `default` | Default value (required NOT NULL if not provided and not auto-increment) |
| `default_factory` | Factory for mutable default values (e.g., `list`) |
| `primary_key` | Primary key |
| `autoincrement` | Auto-incrementing primary key (implicitly a primary key, automatically filled after `create`) |
| `max_length` | Maximum string length (generates `VARCHAR(n)`, validation on write) |
| `nullable` | Whether NULL is allowed (default False) |
| `index` | Generate regular index |
| `unique` | Unique constraint |
| `choices` / `ge` / `le` | Enum / numeric range (validation on write) |
| `description` | Description (i18n dictionary, same format as configuration class) |
| `column_type` | Override SQL column type definition |

## Table Creation and CRUD

```python
await User.create_table()                      # Idempotent (IF NOT EXISTS)

user = await User.create(name="Alice", age=20) # Insert (auto-increment primary key is automatically filled back)
got = await User.get(id=user.id)               # Get the first record by exact match

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # Update by primary key (with constraint validation); if primary key is missing, it falls back to insert (auto-increment primary key is also filled back to the instance)
await user.delete()                            # Delete by primary key

await User.update_all(User.age > 18, role="adult")  # Batch update
await User.delete_all(User.age > 100)               # Batch delete
```

Query expressions support `> >= < <= == !=`, `in_([...])`, and combinations using `&` (AND) / `|` (OR):

```python
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all()
```

## Transactions

The ORM's read and write operations share the same transaction routing as the framework's storage layer: within the `storage.atransaction()` context, `create`, `save`, `delete`, and queries automatically reuse the transaction connection, committing or rolling back together with the transaction, and will not be committed independently.

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # If an exception is thrown within the block, the above INSERT will also be rolled back
```

## Relationship with Declarative Configuration Classes

Model declarations and `ConfigClass` (`@dataclass + field(metadata=...)`) **share the same underlying system**—constraint vocabulary, validator engine (`validate_field_constraints`), and type category registry (`python_type_category`). However, their class bases are intentionally separated: configuration fields are ordinary values (TOML round-trip, hot reload on single load), while model fields are column descriptors (class access = query expression, row-by-row instance). One declaration syntax, two distinct bases, each serving their own purpose.

## Boundaries and Precautions

- The backend is determined by the global storage configuration; models can override this with a custom `BaseStorage` instance via the `__storage__` class attribute (for test injection purposes).
- `list` / `dict` fields (including parameterized generics such as `list[int]` and `dict[str, int]`) are stored as JSON text columns by container type, with automatic serialization on read and write.
- Constraint validation is automatically executed before writing (`create` / `save`); failures raise a `ValueError` with localized messages.
- Automatic migration has been delivered for **new column** scenarios (see below); column type changes, column deletion, and ORM-level relationship objects are capabilities for future versions.
- When a storage connection failure is triggered, the behavior is consistent with the storage layer: the framework does not crash, and automatic reconnection occurs after a cooldown period.

## Automatic Migration (Phase Two)

When a table already exists, `create_table()` automatically compares existing columns with model fields: **new fields** automatically execute `ALTER TABLE ADD COLUMN` (migrating columns that remove the `NOT NULL` constraint and backfilling NULL for existing rows), and new fields declared with `index=True` are simultaneously indexed. There is no need to manually write migration scripts.

```python
# After v1 launch, model evolution: adding email / bio fields
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # Added: next create_table() will automatically ADD COLUMN
    bio: str = Field(default="")

await User.create_table()              # Idempotent: only migrates newly added columns
```

**Boundary**: Only supports adding new columns; primary key changes, column type changes, and column removal require manual handling (to avoid destructive ALTER mistakes).

## Foreign Keys (Foundation of Relationship Mapping)

The `foreign_key="table.column"` declaration establishes a column-level foreign key constraint, and DDL will generate a `REFERENCES` clause:

```python
class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")

    content: str = Field(max_length=255)
```

Foreign keys are DDL-level constraints (the database ensures referential integrity); ORM-level relationship objects (`relationship` / reverse queries) are capabilities of later versions.