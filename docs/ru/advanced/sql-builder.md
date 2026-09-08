# SQL 查询构建器

Модуль Storage в ErisPulse предоставляет универсальный SQL-конструктор запросов с цепочечным стилем вызова, поддерживающий создание, запрос, обновление и удаление пользовательских таблиц.

## Архитектурное проектирование

```
Bases/storage.py                    Core/storage.py
┌─────────────────────┐             ┌──────────────────────────┐
│  BaseStorage (ABC)  │◄────────────│  StorageManager          │
│  BaseQueryBuilder   │             │  (реализация SQLite)     │
│    (ABC)            │             │                          │
└─────────────────────┘             │  SQLiteQueryBuilder      │
                                    │  AlterTableBuilder       │
                                    └──────────────────────────┘
```

- `BaseStorage` / `BaseQueryBuilder` — абстрактные базовые классы, определяющие единый интерфейс и поддерживающие расширение на другие хранилища (Redis, MySQL и т.д.)
- `StorageManager` — текущая конкретная реализация SQLite, полностью обратно совместима

## Импорт

```python
from ErisPulse import sdk
# или
from ErisPulse.Core import storage

# ABC базовые классы (для аннотации типов или пользовательской реализации)
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## Управление таблицами

### Создание таблицы

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0",
    "email": "TEXT"
})
```

### Проверка существования таблицы

```python
if sdk.storage.HasTable("users"):
    print("Таблица users уже существует")
```

### Удаление таблицы

```python
sdk.storage.DropTable("users")
```

### Изменение структуры таблицы

```python
# Добавление столбца
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()

# Переименование таблицы
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# Цепочка нескольких операций
sdk.storage.AlterTable("users") \
    .AddColumn("phone", "TEXT") \
    .AddColumn("address", "TEXT") \
    .Execute()
```

## Цепочечный запрос

### Вставка данных

```python
# Вставка одной строки (словарь)
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# Массовая вставка (список словарей)
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
    {"name": "Dave", "age": 40}
]).Execute()
```

### Запрос данных

> **Важно**: `Select()` возвращает `list[tuple]` (список кортежей), а не словарь. Вам нужно использовать индексацию по порядку столбцов.

```python
# Запрос всех столбцов
rows = sdk.storage.Table("users").Select().Execute()
# rows: [(1, "Alice", 30), (2, "Bob", 25), ...]

# Запрос определённых столбцов
rows = sdk.storage.Table("users").Select("name", "age").Execute()
# rows: [("Alice", 30), ("Bob", 25), ...]

# Доступ по индексу
for row in rows:
    name = row[0]   # "Alice"
    age = row[1]    # 30
```

#### Преобразование кортежа в словарь

Рекомендуется использовать `ToDict()` в цепочке, чтобы результат SELECT автоматически возвращался в виде словаря (имя столбца → значение):

```python
# ToDict в цепочке: результат — list[dict], имена столбцов автоматически берутся из метаданных запроса (SELECT * также поддерживается)
rows = sdk.storage.Table("users").Select("name", "age").ToDict().Execute()
# rows: [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}, ...]

for row in rows:
    print(row["name"], row["age"])

# ExecuteOne также работает
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ToDict() \
    .ExecuteOne()
# row: {"name": "Alice", "age": 30} или None
```

> `ToDict()` — это метка в цепочке (возвращает self): цепочка без вызова ToDict сохраняет поведение list[tuple], полностью обратно совместима; `copy()` сохраняет этот флаг.

Ручной способ zip (эквивалент ToDict, подходит для случаев, когда нельзя изменить цепочку):

```python
columns = ["id", "name", "age"]
rows = sdk.storage.Table("users").Select(*columns).Execute()

# Способ 1: zip в цикле
for row in rows:
    record = dict(zip(columns, row))
    print(record["name"], record["age"])

# Способ 2: однократное преобразование в список словарей
records = [dict(zip(columns, row)) for row in rows]
```

#### Получение одной записи

```python
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ExecuteOne()

# row — tuple или None
if row is not None:
    name = row[0]  # "Alice"
    age = row[1]   # 30
```

### Условия фильтрации

> `Where(condition, *params)` поддерживает передачу нескольких параметров, соответствующих нескольким знакам `?`.

```python
# Одно условие (один знак вопроса, один параметр)
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 18) \
    .Execute()

# Один Where с несколькими знаками вопроса
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ? AND age < ?", 20, 40) \
    .Execute()

# Несколько вызовов Where (AND соединение)
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 20) \
    .Where("age < ?", 40) \
    .Execute()
```

### Сортировка, пагинация

```python
# По возрастанию
rows = sdk.storage.Table("users").Select("name", "age") \
    .OrderBy("name") \
    .Execute()

# По убыванию
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("age", desc=True) \
    .Execute()

# Пагинация
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("id") \
    .Limit(10) \
    .Offset(20) \
    .Execute()
```

### Обновление данных

```python
# Условное обновление
sdk.storage.Table("users") \
    .Update({"age": 31}) \
    .Where("name = ?", "Alice") \
    .Execute()

# Полное обновление
sdk.storage.Table("users") \
    .Update({"status": "active"}) \
    .Execute()
```

### Удаление данных

```python
# Условное удаление
sdk.storage.Table("users") \
    .Delete() \
    .Where("name = ?", "Bob") \
    .Execute()

# Полное удаление
sdk.storage.Table("users").Delete().Execute()
```

### Подсчёт и проверка существования

```python
# Подсчёт
count = sdk.storage.Table("users").Count()
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# Проверка существования
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()
```

## Повторное использование условий запроса

Используйте `copy()` для глубокого копирования конструктора и повторного использования базовых условий:

```python
base = sdk.storage.Table("users").Where("age > ?", 20)

# Запрос на основе одинаковых условий
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()

# Подсчёт на основе одинаковых условий
count = base.copy().Count()

# Проверка существования на основе одинаковых условий
exists = base.copy().Where("name = ?", "Alice").Exists()
```

## Сброс конструктора

```python
builder = sdk.storage.Table("users").Select("name").Where("age > ?", 18)
builder.clear()

# Перестроение запроса
builder.Select("name", "age").Where("name = ?", "Alice")
rows = builder.Execute()
```

## Использование в транзакции

Цепочечные операции полностью поддерживают транзакции:

```python
# Подтверждение транзакции
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Eve", "age": 22}).Execute()
    sdk.storage.Table("users").Update({"age": 23}).Where("name = ?", "Eve").Execute()

# Пример отката
try:
    with sdk.storage.transaction():
        sdk.storage.Table("users").Delete().Where("name = ?", "Alice").Execute()
        raise Exception("force rollback")
except Exception:
    pass
# Запись Alice по-прежнему существует
```

## Асинхронный оригинальный API

Начиная с версии 2.8.0, слой хранилища использует асинхронный интерфейс как основной, все методы, завершающие запрос, имеют соответствующие асинхронные версии с префиксом `a`, рекомендуется использовать в асинхронных обработчиках (чтобы избежать кратковременного блокирования цикла событий синхронной совместимостью):

```python
# Асинхронная транзакция
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.aset("key2", {"nested": True})

# Асинхронный цепочечный запрос
rows = await sdk.storage.Table("users").Select("name", "age").ToDict().aExecute()
row = await sdk.storage.Table("users").Select("*").Where("id = ?", 1).aExecuteOne()
total = await sdk.storage.Table("users").Where("age > ?", 18).aCount()
exists = await sdk.storage.Table("users").Where("name = ?", "Alice").aExists()

# Асинхронный KV
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()
```

| Синхронный (совместимость) | Асинхронный оригинальный |
|------|------|
| `get` / `set` / `delete` | `aget` / `aset` / `adelete` |
| `get_all_keys` / `clear` | `aget_all_keys` / `aclear` |
| `get_multi` / `set_multi` / `delete_multi` | `aget_multi` / `aset_multi` / `adelete_multi` |
| `transaction()` | `atransaction()` |
| `CreateTable` / `DropTable` / `HasTable` | `aCreateTable` / `aDropTable` / `aHasTable` |
| `Execute` / `ExecuteOne` / `Count` / `Exists` | `aExecute` / `aExecuteOne` / `aCount` / `aExists` |

## Описание возвращаемых значений

| Операция | Тип возвращаемого значения | Описание |
|------|---------|------|
| `Select().Execute()` | `list[tuple]` | Список кортежей, отсортированных по порядку столбцов |
| `Select().ExecuteOne()` | `tuple \| None` | Одна строка в виде кортежа или None |
| `Insert().Execute()` | `int` | Количество затронутых строк |
| `InsertMulti().Execute()` | `int` | Количество вставленных строк |
| `Update().Execute()` | `int` | Количество затронутых строк |
| `Delete().Execute()` | `int` | Количество удалённых строк |
| `Count()` | `int` | Количество соответствующих строк |
| `Exists()` | `bool` | Существует ли запись |

### Пример обработки возвращаемых значений

```python
# Select возвращает кортежи, доступ по индексу
rows = sdk.storage.Table("users").Select("name", "age").Execute()
first_name = rows[0][0]  # Первая строка, первый столбец name
first_age = rows[0][1]   # Первая строка, второй столбец age

# Рекомендуется: использовать список имён столбцов + zip для преобразования в словарь, код становится более читаемым
cols = ["name", "age"]
rows = sdk.storage.Table("users").Select(*cols).Execute()
for row in rows:
    d = dict(zip(cols, row))
    print(d["name"], d["age"])

# ExecuteOne возвращает одну строку в виде кортежа или None
row = sdk.storage.Table("users").Select("name").Where("id = ?", 1).ExecuteOne()
name = row[0] if row else None

# Insert/Update/Delete возвращает количество затронутых строк
affected = sdk.storage.Table("users").Delete().Where("age < ?", 18).Execute()
print(f"Удалено {affected} записей")
```

## Параметризованные запросы

Все параметры WHERE используют знак `?` как заполнитель, параметры передаются как последующие аргументы в `Where()` (а **не** как кортеж или список):

```python
# Правильно ✓ — несколько параметров передаются по отдельности
sdk.storage.Table("users").Where("age > ? AND name = ?", 18, "Alice").Execute()

# Правильно ✓ — несколько вызовов Where
sdk.storage.Table("users").Where("age > ?", 18).Where("name = ?", "Alice").Execute()

# Неправильно ✗ — не передавайте кортеж
sdk.storage.Table("users").Where("age > ? AND name = ?", (18, "Alice")).Execute()
# Это приведёт к тому, что весь кортеж будет использован как значение первого заполнителя

# Неправильно ✗ — существует риск SQL-инъекций
sdk.storage.Table("users").Where(f"name = '{user_input}'").Execute()
```

### Правила передачи параметров Where

```python
# Where(condition: str, *params: Any)
# params — переменное количество аргументов, передаётся по отдельности

# Один параметр
.Where("name = ?", "Alice")

# Несколько параметров
.Where("age > ? AND age < ?", 18, 60)

# LIKE-запрос
.Where("name LIKE ?", "A%")

# IN-запрос (требуется ручная генерация заполнителей)
.Where("name IN (?, ?, ?)", "Alice", "Bob", "Charlie")
```

## Пользовательский бэкенд хранилища

Начиная с версии 2.8.0, абстрактный слой использует **асинхронные методы как основной контракт**: наследуйте `BaseStorage` и реализуйте асинхронные абстрактные методы, синхронные `get/set/Execute` и т.д. предоставляются автоматически базовым классом:

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

class MyQueryBuilder(BaseQueryBuilder):
    async def aExecute(self):
        # Реализация конкретной логики выполнения
        ...

    async def aExecuteOne(self):
        ...

    async def aCount(self):
        ...

    async def aExists(self):
        ...


class MyStorage(BaseStorage):
    async def aget(self, key, default=None):
        ...

    async def aset(self, key, value):
        ...

    # Реализация других асинхронных абстрактных методов и хуков транзакций ...
    def Table(self, table_name):
        return MyQueryBuilder(self, table_name)
```

> [!TIP]
> Если вы не хотите реализовывать маршрутизацию транзакций по подключению (`conn` ключевой параметр), оставьте атрибут класса `_SUPPORTS_CONN_ROUTING = False` (по умолчанию), транзакционные функции всё равно будут доступны (ограничение изоляции). Для чисто SQL-бэкендов можно напрямую наследовать `Core/Bases/sql_base.py` классы `SQLStorageBase` + `SQLQueryBuilder`, достаточно лишь предоставить управление подключениями и исполнительную воронку для диалекта, подробнее см. в [Backend хранилища](storage-backends.md).

## Связанные документы

- [Backend хранилища](storage-backends.md) — выбор и настройка бэкендов sqlite / mysql / postgres
- [API основных модулей](../api-reference/core-modules.md) — полный API модуля Storage
- [API базовых классов хранилища](../api-reference/auto_api/ErisPulse/Core/Bases/storage.md) — абстрактные интерфейсы BaseStorage/BaseQueryBuilder
- [MessageBuilder](message-builder.md) — справочник по стилю цепочечных вызовов MessageBuilder