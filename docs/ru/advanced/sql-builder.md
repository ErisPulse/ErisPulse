# SQL 查询构建器

Модуль хранения ErisPulse предоставляет универсальный SQL-конструктор запросов с цепочечным стилем вызовов, поддерживающий создание, выборку, обновление и удаление данных для пользовательских таблиц.

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

- `BaseStorage` и `BaseQueryBuilder` — абстрактные базовые классы, определяющие единый интерфейс и поддерживающие расширение для других типов хранилищ (Redis, MySQL и т.д.)
- `StorageManager` — конкретная реализация для SQLite, полностью обратно совместима

## Импорт

```python
from ErisPulse import sdk
# или
from ErisPulse.Core import storage

# ABC базовые классы (для аннотации типов или пользовательских реализаций)
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

## Цепочечные запросы

### Вставка данных

```python
# Вставка одной строки (словарь)
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# Вставка нескольких строк (список словарей)
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
    {"name": "Dave", "age": 40}
]).Execute()
```

### Выборка данных

> **Важно**: `Select()` возвращает `list[tuple]` (список кортежей), а не словарь. Доступ к значениям осуществляется по индексу.

```python
# Выборка всех столбцов
rows = sdk.storage.Table("users").Select().Execute()
# rows: [(1, "Alice", 30), (2, "Bob", 25), ...]

# Выборка указанных столбцов
rows = sdk.storage.Table("users").Select("name", "age").Execute()
# rows: [("Alice", 30), ("Bob", 25), ...]

# Доступ по индексу
for row in rows:
    name = row[0]   # "Alice"
    age = row[1]    # 30
```

#### Преобразование кортежей в словари

```python
columns = ["id", "name", "age"]
rows = sdk.storage.Table("users").Select(*columns).Execute()

# Способ 1: zip в цикле
for row in rows:
    record = dict(zip(columns, row))
    print(record["name"], record["age"])

# Способ 2: преобразование в список словарей
records = [dict(zip(columns, row)) for row in rows]
```

#### Получение одной записи

```python
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ExecuteOne()

# row — кортеж или None
if row is not None:
    name = row[0]  # "Alice"
    age = row[1]   # 30
```

### Условия фильтрации

> `Where(condition, *params)` поддерживает несколько параметров, соответствующих нескольким знакам `?`.

```python
# Одно условие (один знак `?`, один параметр)
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 18) \
    .Execute()

# Один вызов Where с несколькими знаками `?`
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ? AND age < ?", 20, 40) \
    .Execute()

# Несколько вызовов Where (AND соединяются)
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 20) \
    .Where("age < ?", 40) \
    .Execute()
```

### Сортировка, пагинация

```python
# Сортировка по возрастанию
rows = sdk.storage.Table("users").Select("name", "age") \
    .OrderBy("name") \
    .Execute()

# Сортировка по убыванию
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

### Подсчет и проверка существования

```python
# Подсчет записей
count = sdk.storage.Table("users").Count()
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# Проверка существования
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()
```

## Повторное использование условий запроса

Используйте `copy()` для глубокого копирования конструктора и повторного использования базовых условий:

```python
base = sdk.storage.Table("users").Where("age > ?", 20)

# Запрос с теми же условиями
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()

# Подсчет с теми же условиями
count = base.copy().Count()

# Проверка существования с теми же условиями
exists = base.copy().Where("name = ?", "Alice").Exists()
```

## Сброс конструктора

```python
builder = sdk.storage.Table("users").Select("name").Where("age > ?", 18)
builder.clear()

# Перестройка запроса
builder.Select("name", "age").Where("name = ?", "Alice")
rows = builder.Execute()
```

## Использование в транзакциях

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
# Запись Alice все еще существует
```

## Описание возвращаемых значений

| Операция | Тип возвращаемого значения | Описание |
|----------|-----------------------------|----------|
| `Select().Execute()` | `list[tuple]` | Список кортежей, значения по порядку столбцов |
| `Select().ExecuteOne()` | `tuple \| None` | Одна строка как кортеж или None |
| `Insert().Execute()` | `int` | Количество затронутых строк |
| `InsertMulti().Execute()` | `int` | Количество вставленных строк |
| `Update().Execute()` | `int` | Количество затронутых строк |
| `Delete().Execute()` | `int` | Количество удаленных строк |
| `Count()` | `int` | Количество соответствующих строк |
| `Exists()` | `bool` | Существует ли запись |

### Пример обработки возвращаемых значений

```python
# Select возвращает кортежи, значения по индексу
rows = sdk.storage.Table("users").Select("name", "age").Execute()
first_name = rows[0][0]  # Первый столбец первой строки
first_age = rows[0][1]   # Второй столбец первой строки

# Рекомендуется: преобразование в словари с помощью zip для лучшей читаемости
cols = ["name", "age"]
rows = sdk.storage.Table("users").Select(*cols).Execute()
for row in rows:
    d = dict(zip(cols, row))
    print(d["name"], d["age"])

# ExecuteOne возвращает кортеж или None
row = sdk.storage.Table("users").Select("name").Where("id = ?", 1).ExecuteOne()
name = row[0] if row else None

# Insert/Update/Delete возвращают количество затронутых строк
affected = sdk.storage.Table("users").Delete().Where("age < ?", 18).Execute()
print(f"Удалено {affected} записей")
```

## Параметризованные запросы

Все параметры WHERE используют знак `?`, параметры передаются как последующие аргументы в `Where()` (а не в виде кортежа или списка):

```python
# Правильно ✓ — несколько параметров по отдельности
sdk.storage.Table("users").Where("age > ? AND name = ?", 18, "Alice").Execute()

# Правильно ✓ — несколько вызовов Where
sdk.storage.Table("users").Where("age > ?", 18).Where("name = ?", "Alice").Execute()

# Неправильно ✗ — не передавайте кортеж
sdk.storage.Table("users").Where("age > ? AND name = ?", (18, "Alice")).Execute()
# Это приведет к передаче всего кортежа как значения первого знака `?`

# Неправильно ✗ — риск SQL-инъекции
sdk.storage.Table("users").Where(f"name = '{user_input}'").Execute()
```

### Правила передачи параметров в Where

```python
# Where(condition: str, *params: Any)
# params — переменное количество аргументов, передаваемых по одному

# Один параметр
.Where("name = ?", "Alice")

# Несколько параметров
.Where("age > ? AND age < ?", 18, 60)

# Запрос LIKE
.Where("name LIKE ?", "A%")

# Запрос IN (необходимо вручную создать знаки `?`)
.Where("name IN (?, ?, ?)", "Alice", "Bob", "Charlie")
```

## Создание пользовательского хранилища

Для реализации пользовательского хранилища наследуйте `BaseStorage` и `BaseQueryBuilder`:

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

class MyQueryBuilder(BaseQueryBuilder):
    def Execute(self):
        # Реализация выполнения запроса
        ...

    def ExecuteOne(self):
        ...

    def Count(self):
        ...

    def Exists(self):
        ...

class MyStorage(BaseStorage):
    def get(self, key, default=None):
        ...

    def set(self, key, value):
        ...

    # Реализация других абстрактных методов
    def Table(self, table_name):
        return MyQueryBuilder(self, table_name)
```

## Связанные документы

- [Справочник API ядра](../api-reference/core-modules.md) — полный API модуля Storage
- [Справочник API базового хранилища](../api-reference/auto_api/ErisPulse/Core/Bases/storage.md) — абстрактные интерфейсы BaseStorage/BaseQueryBuilder
- [Построитель сообщений](message-builder.md) — пример построителя сообщений в цепочечном стиле