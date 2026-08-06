# Описание конфигурационного файла
> Этот документ расскажет о конфигурационном файле фреймворка. Если стороннему модулю требуется настройка, обратитесь к документации модуля.

ErisPulse использует конфигурационный файл в формате TOML `config/config.toml` для управления настройками проекта.

docs/ru/quick-start.md

## Расположение конфигурационного файла

Конфигурационный файл находится в папке `config/` в корне проекта:

```
project/
├── config/
│   └── config.toml
├── main.py
```

docs/ru/quick-start.md

## Обработка ошибок загрузки конфигурации

Фреймворк различает три состояния ошибок при загрузке `config.toml` и предоставляет **действенные диагностические сообщения**, а не просто переключается на настройки по умолчанию:

| Состояние ошибки | Условия срабатывания | Поведение фреймворка |
|------------------|----------------------|----------------------|
| Файл отсутствует | `config.toml` не существует | При первом запуске нормально, используется пустая конфигурация без предупреждений |
| Ошибка синтаксиса TOML | Файл существует, но формат некорректен (например, отсутствуют кавычки, не закрыты скобки) | Выводится **номер строки/столбца и причина ошибки**, а также сообщение о возврате к настройкам по умолчанию |
| Ошибка прав/другие ошибки | Нет прав на чтение, ошибки ввода-вывода и т.д. | Выводится **ясная причина**, а также сообщение о возврате к настройкам по умолчанию |

Например, если вы случайно написали конфигурацию как `port = 8000` (строка без кавычек), в логах будет выведено примерно следующее:

```
[ERROR] [Config] Синтаксическая ошибка в конфигурационном файле config/config.toml (строка 3, столбец 1): ...
[WARNING] [Config] Не удалось прочитать конфигурационный файл. Продолжаем работу с предыдущей корректной конфигурацией, изменения в файле не были применены — пожалуйста, исправьте и перезагрузите или перезапустите
```

Таким образом, вы можете сразу определить проблему на уровне **INFO**, а не задаваться вопросом "почему мои изменения не применяются".

> **Изменение конфигурационного файла во время работы?** Если вы вручную отредактируете `config.toml` во время работы робота и внесёте синтаксическую ошибку, фреймворк при следующей попытке записи (объединения конфигурации) выведет сообщение "Конфигурационный файл повреждён (ошибка синтаксиса, строка X), невозможно объединить и записать — пожалуйста, сначала исправьте конфигурационный файл и перезапустите", а не запутанное "ошибка записи". Новые значения конфигурации будут сохранены и не потеряются.

[**English**](docs/ru/quick-start.md) | [**简体中文**](docs/ru/quick-start.md)

## Переменные окружения

Фреймворк поддерживает **переопределение** конфигурационных параметров `ErisPulse.*` с помощью переменных окружения (подходит для Docker / контейнеризации / CI-развертывания, без необходимости изменять `config.toml`).

Правило именования: преобразуйте точечный путь `ErisPulse.<section>.<key>` в верхний регистр, замените `.` на `_` и добавьте префикс `ERISPULSE_`:

| Параметр конфигурации | Переменная окружения | Пример значения |
|----------------------|---------------------|-----------------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `false` |

Описание поведения:
- **Наивысший приоритет**: переменные окружения переопределяют значения из «конфигурационного файла» и «значений по умолчанию», автоматически преобразуя типы (bool / int / float / список, разделённый запятыми / строка)
- **Непостоянное хранение**: переопределение действует только во время выполнения, не сохраняется в `config.toml`
- **Поддержка горячей перезагрузки**: изменение переменных окружения во время работы, в сочетании с перезагрузкой конфигурации при прослушивании, вступает в силу

```bash
# Пример развертывания в Docker: без изменения config.toml, просто переопределяем порт
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> Примечание: такие параметры фреймворка, как `ErisPulse.server.port`, читаются через API, такие как `get_server_config()`, и подвержены влиянию переменных окружения.

[**English**](docs/ru/quick-start.md)

## Hot reload of configuration

Starting from version 2.7.0, the framework provides **systematic support** for hot reloading of configurations. After an external modification of `config.toml` (the background watcher checks every 5 seconds) or after the code calls `setConfig()`, the components automatically respond:

| Component | Configurations supporting hot reload | Behavior |
|------|----------------|------|
| **Logger** | `logger.level` / `log_files` / `memory_limit` / `format` | Automatically reapplied (with change detection) |
| **Command system CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | Takes effect on the next message |
| **Adapters concurrency** | `framework.handler_max_concurrency` | Invalidates cached semaphore, rebuilds with new value |
| **Active GC** | `framework.proactive_gc_interval` | Re-reads each round, supports runtime adjustments/disabling |
| **Master system Master** | `master.users` | Each `is_master()` check reads in real-time, no restart needed |
| **Modules/Adapters configuration** | Their own configuration items | Triggers `on_config_update(old, new)` callback |

**Configurations requiring restart** (cannot be safely hot-switched, warning "Process restart required for effect" is output when changed):

| Configuration | Reason |
|------|------|
| `router.cors.*` / `router.security.*` | Middleware is written into FastAPI at service startup, cannot be safely hot-switched at runtime |
| `storage.use_global_db` | SQLite file handle is already open at runtime, switching paths is unsafe |

> **Error saving while editing midway?** If a transient syntax error occurs while editing `config.toml`, the framework will **retain the last valid configuration** and output diagnostic logs, and will not broadcast an empty configuration to the components (to avoid `on_config_update` receiving null values and mistakenly reverting to defaults).

[**English**](docs/ru/quick-start.md)

## Полный пример конфигурации

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
memory_limit = 1000

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true

[ErisPulse.i18n]
language = "auto"

## Серверная конфигурация

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| Параметр | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| host | string | 0.0.0.0 | Адрес прослушивания, 0.0.0.0 означает все интерфейсы |
| port | integer | 8000 | Прослушиваемый порт |
| ssl_certfile | string | пусто | Путь к файлу SSL-сертификата |
| ssl_keyfile | string | пусто | Путь к файлу SSL-приватного ключа |

Пожалуйста, замените `docs/ru/` на `docs/ru/` в ссылках документации.  
Например: `docs/ru/quick-start.md` должно быть изменено на `docs/ru/quick-start.md`  
Для ссылок на файлы не текущего языка (в формате `README.xx.md`) оставьте без изменений.  
Это гарантирует, что ссылки указывают на правильную версию документации на нужном языке.

## Конфигурация логирования

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| Параметр | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| level | string | INFO | Уровень логирования: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL (TRACE - самый низкий уровень, выводит подробную отладочную информацию внутренней структуры) |
| format | string | rich | Формат вывода логов: `rich` (цветной, по умолчанию), `plain` (чистый текст без цвета, подходит для сбора логов/перенаправления в поток), `json` (структурированный JSON, подходит для ELK и подобных систем) |
| log_files | array | пустой | Список файлов для вывода логов |
| memory_limit | integer | 1000 | Количество записей логов, сохраняемых в памяти |

Пожалуйста, замените в документе `docs/ru/` на `docs/ru/` для всех ссылок на документацию. Например, `docs/ru/quick-start.md` должно быть заменено на `docs/ru/quick-start.md`. Ссылки на файлы других языков (в формате `README.xx.md`) оставьте без изменений. Это обеспечит корректное указание на документацию нужного языка.

## Конфигурация фреймворка

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| Параметр | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | Включает ли ленивую загрузку модулей |
| uninit_timeout | integer | 30 | Общее время ожидания при корректном завершении (секунды), после которого происходит принудительное завершение. Значение 0 означает отсутствие таймаута |
| strict_mode | integer | 0 | Уровень строгого режима, см. описание «Строгий режим» ниже |

### Строгий режим

Строгий режим определяет стратегию обработки компонентов модулей/адаптеров, которые нарушают правила или не могут быть загружены на этапе инициализации. Современные модули/адаптеры должны наследовать соответствующие базовые классы (`BaseModule`/`BaseAdapter`), иначе компоненты, не наследующие базовые классы, могут повлиять на контекстную систему фреймворка и на очистку ресурсов, что может привести к утечке ресурсов.

> **Изменение в 2.5.2**: уровень по умолчанию был изменен с `1` (пропуск) на `0` (допускающий), чтобы уменьшить количество проблем с загрузкой при первом использовании новыми пользователями. Компоненты, не наследующие базовые классы, будут получать предупреждение и попытка загрузки будет продолжена, а не отклонена. Чтобы восстановить старое поведение, явно установите `strict_mode = 1`.

| Уровень | Название | Поведение |
|------|------|------|
| 0 | Допускающий (по умолчанию) | Нарушения только предупреждаются, компоненты, не наследующие базовые классы, все равно будут загружены (для совместимости со старыми компонентами) |
| 1 | Строгий-пропуск | Компоненты, не наследующие базовые классы, отклоняются и пропускаются, остальные запускаются нормально |
| 2 | Строгий-критический | Все нарушения собираются и сообщаются единым списком, после чего запуск прерывается |

На всех уровнях ошибки, возникающие на этапах загрузки/регистрации/инициализации, всегда будут пропущены; различие заключается в следующем:

- **0 → 1**: единственное изменение поведения — компоненты, не наследующие базовые классы, из «все еще загружаются» переходят в «пропускаются».
- **1 → 2**: все нарушения (не наследование базовых классов, сбой загрузки, сбой регистрации, сбой инициализации и т.д.) повышаются до критического уровня, и после сбора на этапе проверки запуска выводится единый список нарушений и запуск прерывается.

#### Список исключений

Если некоторые компоненты действительно временно не могут быть обновлены (например, из-за зависимости от старых модулей), их можно добавить в список исключений. Компоненты, включенные в этот список, будут обрабатываться в соответствии с допускающим режимом, даже если они нарушают правила, и загрузка будет продолжена:

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> Когда какой-либо компонент отклоняется в строгом режиме, в логе будет четко указано, как восстановить загрузку (добавление в список исключений или понижение уровня).

[**English**](docs/ru/quick-start.md)

## Конфигурация хранилища

```toml
[ErisPulse.storage]
use_global_db = false
```

| Параметр | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| use_global_db | boolean | false | Использовать ли глобальную базу данных (внутри пакета) вместо базы данных проекта. При `true` все проекты будут использовать общую базу данных SQLite внутри пакета ErisPulse; при `false` (по умолчанию) каждый проект будет использовать свою независимую базу данных в каталоге `config/` |

[**English**](docs/ru/quick-start.md)

## Конфигурация событий

### Конфигурация команд

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| Параметр | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| prefix | string | / | Префикс команды |
| case_sensitive | boolean | true | Регистр чувствителен (команды `/Help` и `/help` считаются разными) |
| allow_space_prefix | boolean | false | Разрешить пробел в качестве префикса |
| must_at_bot | boolean | false | Команды могут быть вызваны только с упоминанием бота (в личных сообщениях это ограничение не действует) |

### Конфигурация сообщений

```toml
[ErisPulse.event.message]
ignore_self = true
```

| Параметр | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| ignore_self | boolean | true | Игнорировать собственные сообщения бота |

[**English**](docs/ru/quick-start.md) | [**简体中文**](docs/ru/quick-start.md) | [**Русский**](docs/ru/quick-start.md)

## Международная локализация

```toml
[ErisPulse.i18n]
language = "auto"
```

| Параметр | Тип | Значение по умолчанию | Описание |
|---------|------|---------|------|
| language | string | auto | Язык отображения встроенных текстов фреймворка. Установите `auto` для автоматического определения языка системы, или укажите конкретный код языка: `zh-CN`、`zh-TW`、`en`、`ja`、`ru` |

[**Следующая страница**](docs/ru/quick-start.md)

## Конфигурация модуля

Каждый модуль может определить свою собственную конфигурацию в файле конфигурации:

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

Чтение и запись конфигурации в модуле:

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

> `setConfig` по умолчанию использует отложенную запись (примерно каждые 5 секунд пакетное сохранение в файл), установка `immediate=True` приводит к немедленной постоянной записи. Изменение конфигурации запускает событие жизненного цикла `config.set`.

[**中文**](docs/ru/quick-start.md)

## Далее

- [Справочник команд CLI](cli-reference.md) - Узнайте все команды командной строки
- [Руководство для разработчиков](../developer-guide/) - Изучите разработку пользовательских модулей

Пожалуйста, возвращайте непосредственно переведенный полный Markdown-контент, не включая никаких других текстов.