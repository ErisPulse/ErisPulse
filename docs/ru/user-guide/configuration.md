# Описание конфигурационного файла
> Этот документ представляет конфигурационный файл фреймворка. Если для стороннего модуля требуется настройка, пожалуйста, обратитесь к документации модуля.

ErisPulse использует файл конфигурации в формате TOML `config/config.toml` для управления настройками проекта.

## Расположение файла конфигурации

Файл конфигурации находится в папке `config/` в корневой директории проекта:

```
project/
├── config/
│   └── config.toml
├── main.py
```

## Полный пример конфигурации

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
log_files = []
memory_limit = 1000

[ErisPulse.framework]
enable_lazy_loading = true

[ErisPulse.storage]
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true
```

## Конфигурация сервера

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| Параметр конфигурации | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| host | string | 0.0.0.0 | Адрес прослушивания (0.0.0.0 означает все интерфейсы) |
| port | integer | 8000 | Порт прослушивания |
| ssl_certfile | string | (пусто) | Путь к файлу SSL-сертификата |
| ssl_keyfile | string | (пусто) | Путь к файлу закрытого ключа SSL |

## Конфигурация логов

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| Параметр конфигурации | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| level | string | INFO | Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| log_files | array | (пусто) | Список файлов для вывода логов |
| memory_limit | integer | 1000 | Количество записей логов, сохраняемых в памяти |

## Конфигурация фреймворка

```toml
[ErisPulse.framework]
enable_lazy_loading = true
```

| Параметр конфигурации | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | Включить ленивую загрузку модулей |

## Конфигурация хранилища

```toml
[ErisPulse.storage]
use_global_db = false
```

| Параметр конфигурации | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| use_global_db | boolean | false | Использовать глобальную базу данных (внутри пакета) вместо базы данных проекта |

## Конфигурация событий

### Конфигурация команд

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| Параметр конфигурации | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| prefix | string | / | Префикс команды |
| case_sensitive | boolean | false | Чувствительность к регистру |
| allow_space_prefix | boolean | false | Разрешить использование пробела в качестве префикса |
| must_at_bot | boolean | false | Требуется упоминание бота (@) для срабатывания команды (в личных сообщениях не ограничено) |

### Конфигурация сообщений

```toml
[ErisPulse.event.message]
ignore_self = true
```

| Параметр конфигурации | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| ignore_self | boolean | true | Игнорировать сообщения от самого бота |

## Конфигурация модулей

Каждый модуль может определять свою собственную конфигурацию в файле конфигурации:

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

Чтение конфигурации внутри модуля:

```python
from ErisPulse import sdk

config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")
```

Запись и чтение конфигурации в модуле:

```python
from ErisPulse import sdk

# Чтение конфигурации
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# Запись конфигурации во время выполнения (отложенное сохранение)
sdk.config.setConfig("MyModule.timeout", 60)

# Немедленное сохранение в файл
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` по умолчанию использует отложенную запись (примерно каждые 5 секунд для пакетного сохранения в файл). Установка `immediate=True` позволяет немедленно сохранить изменения. Изменения конфигурации вызывают событие жизненного цикла `config.set`.

## Далее

*   [Справка по командам CLI](cli-reference.md) - Узнайте обо всех командах командной строки
*   [Руководство разработчика](../developer-guide/) - Научитесь разрабатывать пользовательские модули