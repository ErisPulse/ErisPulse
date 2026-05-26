# Core Module API

This document details the ErisPulse core module API.

## Storage Module

### Basic Operations

```python
from ErisPulse import sdk

# Set value
sdk.storage.set("key", "value")

# Get value
value = sdk.storage.get("key", default_value)

# Get all keys
keys = sdk.storage.keys()

# Delete value
sdk.storage.delete("key")
```

### Transaction Operations

```python
# Use transactions to ensure data consistency
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # If any operation fails, all changes will be rolled back
```

### Batch Operations

```python
# Batch set
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# Batch get
values = sdk.storage.get_multi(["key1", "key2", "key3"])

# Batch delete
sdk.storage.delete_multi(["key1", "key2", "key3"])
```

### SQL Chain Query

The Storage module provides a chain-style API general-purpose SQL query builder, supporting CRUD operations for custom tables.

> See [SQL Query Builder](../advanced/sql-builder.md) for complete documentation.

```python
from ErisPulse import sdk

# Create custom table
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0"
})

# Insert data
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# Batch insert
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]).Execute()

# Query data
rows = (sdk.storage.Table("users")
    .Select("name", "age")
    .Where("age > ?", 18)
    .OrderBy("name")
    .Limit(10)
    .Execute())

# Update data
sdk.storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()

# Delete data
sdk.storage.Table("users").Delete().Where("name = ?", "Bob").Execute()

# Count
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# Existence check
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()

# Get single record
row = sdk.storage.Table("users").Select("name", "age").Where("name = ?", "Alice").ExecuteOne()

# Modify table structure
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# Check if table exists
if sdk.storage.HasTable("users"):
    sdk.storage.DropTable("users")

# Chained operations in transaction
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Dave", "age": 40}).Execute()
    sdk.storage.Table("users").Update({"age": 41}).Where("name = ?", "Dave").Execute()

# Reuse query conditions
base = sdk.storage.Table("users").Where("age > ?", 20)
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()
count = base.copy().Count()
```

### Storage Backend Abstraction

The `StorageManager` inherits from the `BaseStorage` abstract base class, supporting future expansion to other storage media (Redis, MySQL, etc.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

# BaseStorage defines the unified interface: get/set/delete/Table/CreateTable/DropTable, etc.
# BaseQueryBuilder defines the chained query interface: Select/Insert/Update/Delete/Where/OrderBy/Limit, etc.
```

## Config Module

### Reading Configuration

```python
from ErisPulse import sdk

# Get configuration
config = sdk.config.getConfig("MyModule", {})

# Get nested configuration
value = sdk.config.getConfig("MyModule.subkey.value", "default")
```

### Writing Configuration

```python
# Set configuration
sdk.config.setConfig("MyModule", {"key": "value"})

# Set nested configuration
sdk.config.setConfig("MyModule.subkey.value", "new_value")
```

### Configuration Example

```python
def _load_config(self):
    config = sdk.config.getConfig("MyModule")
    if not config:
        # Create default configuration
        default_config = {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "cache_ttl": 3600
        }
        sdk.config.setConfig("MyModule", default_config, immediate=True)  # When the third parameter is True, save the configuration immediately, making it convenient for users to directly modify the configuration file
        return default_config
    return config
```

### Configuration Auditing

Config module has built-in caller-aware and auditing functionality to track read/write sources of configurations:

```python
# Enable auditing (disabled by default)
sdk.config.enable_audit(True)

# Listen for configuration changes
@sdk.config.on_change("MyModule")
def on_config_change(key, old_value, new_value, caller):
    print(f"Configuration changed: {key}")
    print(f"  Old value: {old_value} -> New value: {new_value}")
    print(f"  Caller: {caller.file}:{caller.lineno} ({caller.function})")

# Get audit logs
log = sdk.config.get_audit_log(limit=10)
for entry in log:
    print(f"[{entry.timestamp}] {entry.operation} {entry.key} by {entry.caller.function}")

# Disable auditing
sdk.config.enable_audit(False)
```

Audit logs contain:
- `operation`: Operation type (`get` / `set`)
- `key`: Configuration key path
- `caller`: Caller information (file name, line number, function name, module name)
- `timestamp`: Operation timestamp

## Logger Module

### Basic Logging

```python
from ErisPulse import sdk

# Different log levels
sdk.logger.debug("Debug info")