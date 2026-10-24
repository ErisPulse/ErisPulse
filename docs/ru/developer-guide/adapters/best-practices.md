# Лучшие практики разработки адаптеров

> [!TIP]
> **Когда стоит читать этот документ**: рекомендуется к прочтению после того, как скелет адаптера заработал (инженерные лучшие практики). Если это не нужно — пропустите, это не повлияет на использование остальных функций.


Здесь собраны инженерные соглашения при разработке адаптеров: отчёты о состоянии ботов, повторные попытки подключения и heartbeat, разрешение мультиаккаунтов, стандартизированные ответы об ошибках — следование им помогает избежать типичных проблем при интеграции с платформами: незаметных отключений, отправки сообщений не тому адресату при нескольких аккаунтах, трудностей с локализацией ошибок.

## Управление состоянием ботов и Meta-события

Адаптер должен активно отправлять meta-события через `adapter.emit()`, чтобы фреймворк автоматически отслеживал состояние подключения бота, его вход/выход из сети и информацию heartbeat.

### 1. Когда отправлять Meta-события

| Событие | `detail_type` | Когда срабатывает | Поведение фреймворка |
|------|--------------|---------|---------|
| Подключение | `"connect"` | При установлении соединения бота с платформой | Регистрирует бота, вызывает событие жизненного цикла `adapter.bot.online` |
| Отключение | `"disconnect"` | При разрыве соединения бота с платформой | Помечает бота как офлайн, вызывает событие жизненного цикла `adapter.bot.offline` |
| Heartbeat | `"heartbeat"` | Периодически (рекомендуется 30-60 секунд) | Обновляет время активности бота и метаданные |

### 2. Отправка Meta-событий

Фреймворк предоставляет метод `emit_meta()`, позволяющий отправить meta-событие одной строкой:

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Бот в сети: отправка события connect одной строкой
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="Мой бот")

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Бот не в сети
            await self.emit_meta("disconnect", bot_id)
```

Также можно вручную сконструировать стандартное meta-событие (старый способ остаётся совместимым):

```python
await self.adapter.emit({
    "id": str(uuid4()),
    "time": int(time.time()),
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": bot_id,
        "user_name": "MyBot",
        "avatar": "https://example.com/avatar.jpg",
    },
    "myplatform_raw": raw_data,
    "myplatform_raw_type": "connected",
})
```

### 3. События heartbeat

Адаптер должен периодически отправлять события heartbeat, пока соединение активно, обновляя время активности бота:

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # Отправка meta heartbeat фреймворку (одной строкой)
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. Автоматическое обнаружение поля `self`

`adapter.emit()` фреймворка автоматически обрабатывает поле `self` во всех событиях (не только в meta-событиях):

- **В обычных событиях** (message/notice/request) поле `self` автоматически обнаруживается и регистрирует бота
- **Расширенная информация в поле `self`**: поддерживаются необязательные поля `user_name`, `nickname`, `avatar`, `account_id`

```python
# Наличие поля self в конвертере достаточно для автоматической регистрации бота
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "Мой бот",
    },
    # ... другие поля
}
await self.adapter.emit(onebot_event)
# Бот "bot123" автоматически зарегистрирован, время активности обновлено
```

### 5. Запрос состояния бота

API запросов (`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`) и таблицу событий жизненного цикла бота см. в [API системы адаптеров - Управление состоянием ботов](../../api-reference/adapter-system.md#управление-состоянием-ботов).

## Управление подключением

### 1. Реализация повторных попыток подключения

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                self.logger.info("Подключение успешно")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # Стратегия экспоненциальной задержки
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"Не удалось подключиться, повторная попытка через {wait_time} с ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Не удалось подключиться: достигнуто максимальное число попыток")
                    raise
```

### 2. Управление состоянием подключения

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = None
        self._connected = False
    
    async def _ws_handler(self, websocket: WebSocket):
        self.connection = websocket
        self._connected = True
        self.logger.info("Соединение установлено")
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._process_event(data)
        except WebSocketDisconnect:
            self.logger.info("Соединение разорвано")
        finally:
            self.connection = None
            self._connected = False
```

### 3. Поддержание соединения heartbeat и Meta-heartbeat

Heartbeat адаптера должен решать две задачи одновременно: отправлять платформе heartbeat для поддержания соединения и отправлять фреймворку meta-событие heartbeat.

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. Отправка heartbeat платформе для поддержания соединения
                await self.connection.send_json({"type": "ping"})

                # 2. Отправка meta heartbeat фреймворку (одной строкой через emit_meta)
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Ошибка heartbeat: {e}")
                break
```

### 4. Предоставление информации о подключении

Маршруты, зарегистрированные адаптером, должны быть видимы пользователю — это упрощает настройку адреса обратного вызова на стороне платформы. Рекомендуется активно выводить информацию о подключении в `start()`:

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        router.register_websocket(
            module_name=self.platform,
            path="/ws",
            handler=self._ws_handler
        )

        if self.sdk:
            info = self.sdk.adapter.get_connection_info(self.platform)
            if info:
                self.logger.info(f"WebSocket-адрес: "
                    f"{info.get('connection', {}).get('base_url', '')}"
                    f"{info.get('connection', {}).get('websocket_routes', [])}")
```

Пользователи могут использовать следующие API для просмотра всех маршрутов и адресов подключения адаптера:

```python
from ErisPulse import sdk

# Информация о подключении на уровне адаптера (рекомендуется)
info = sdk.adapter.get_connection_info("myplatform")

# Запросы на уровне менеджера маршрутов
sdk.router.list_namespaces()              # Список всех пространств имён
sdk.router.get_module_routes("myplatform")  # Подробная информация о маршрутах
sdk.router.get_module_urls("myplatform")    # Полные URL подключения
```

> **Примечание**: `module_name`, указанный при регистрации маршрута, должен полностью совпадать с именем `platform`, под которым адаптер зарегистрирован в ErisPulse, иначе `get_connection_info()` не сможет связать маршруты. Мультиаккаунтные адаптеры должны регистрировать подпути для каждого аккаунта (например, `/account1/webhook`, `/account2/webhook`), а не использовать разные `module_name`.

## Преобразование событий

### 1. Строгое следование стандарту OneBot12

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование события"""
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,  # Сохранение исходных данных (обязательно)
            "myplatform_raw_type": raw_event.get("type", "")  # Исходный тип (обязательно)
        }
        return onebot_event
```

### 2. Стандартизация временных меток

```python
def _convert_timestamp(self, timestamp):
    """Преобразование в 10-значную временную метку в секундах"""
    if not timestamp:
        return int(time.time())
    
    # Если временная метка в миллисекундах
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # Если временная метка в секундах
    return int(timestamp)
```

### 3. Генерация ID событий

```python
import uuid

def _generate_event_id(self, raw_event):
    """Генерация ID события"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # Если платформа не предоставила ID, генерируется UUID
    return str(uuid.uuid4())
```

## Реализация SendDSL

Модификаторы `At`/`AtAll`/`Reply` уже встроены в базовый класс SendDSL фреймворка — адаптеру достаточно реализовать `Raw_ob12` и конкретные методы отправки. Используйте `self._apply_modifiers(message)` и `self.send_context` для упрощения разработки.

### 1. Обязательный возврат объекта Task

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Рекомендуемая реализация: использование вспомогательных методов фреймворка"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    def Text(self, text: str):
        return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 2. Цепочные методы-модификаторы возвращают self

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # возвращает self
```

### 3. Поддержка специфичных для платформы методов

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """Отправка стикера"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                message=[{"type": "sticker", "data": {"id": sticker_id}}],
                **self.send_context
            )
        )
    
    def Card(self, card_data: dict):
        """Отправка карточного сообщения"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": card_data}],
                **self.send_context
            )
        )
```

## Ответы API

### 1. Стандартизированный формат ответов

Фреймворк предоставляет методы `make_response()` и `make_error()` для построения стандартизированных ответов:

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        if raw_response.get("success"):
            return self.make_response(
                data=raw_response.get("data"),
                message_id=raw_response.get("data", {}).get("message_id", ""),
                raw=raw_response,
            )
        else:
            return self.make_error(
                retcode=raw_response.get("code", 10001),
                message=raw_response.get("message", ""),
                raw=raw_response,
            )
    except Exception as e:
        return self.make_error(message=str(e))
```

`make_response()` автоматически генерирует словарь ответа с ключом `{platform}_raw`. `make_error()` по умолчанию использует `retcode=34000` (Platform Error).

### 2. Спецификация кодов ошибок

Следуйте стандартным кодам ошибок OneBot12:

```python
# 1xxxx - Ошибки запроса действия
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - Ошибки обработчика действия
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - Ошибки выполнения действия
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## Поддержка нескольких аккаунтов

### 1. Декларативная конфигурация (рекомендуется)

После объявления класса конфигурации через `AccountConfigClass` фреймворк автоматически управляет загрузкой нескольких аккаунтов, их валидацией и генерацией шаблонов. Базовый класс `BotAccountConfig` предоставляет поля `enabled` и `name`, поэтому адаптеру не нужно объявлять их самостоятельно:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Bot Token"},
        "required": True,
        "secret": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"Запуск аккаунта {name}")
            await self._connect(name, account.token)
            # bot_id автоматически получается фреймворком из протокола платформы/ответа на авторизацию и заполняется обратно
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # name: имя аккаунта, account: экземпляр MyBotConfig
```

Файл конфигурации генерируется автоматически:

```toml
[MyAdapter.accounts.default]
token = ""
enabled = true
name = ""
```

### 2. Механизм выбора аккаунта

Во фреймворк встроен метод `_resolve_account()` со следующими приоритетами сопоставления:

1. **Имя аккаунта** — точное совпадение с ключом конфигурации
2. **Поле `bot_id`** — автоматически полученный bot_id (т.е. `event["self"]["user_id"]`)
3. **Любое str-поле** — другие строковые поля в конфигурации
4. **Запасной вариант** — первый включённый аккаунт

```python
# Сопоставление по имени аккаунта
name, account = self._resolve_account("account1")

# Сопоставление по bot_id (самый распространённый способ, берётся из события)
name, account = self._resolve_account("bot_123")

# Получение первого включённого аккаунта (передаётся None)
name, account = self._resolve_account(None)
```

## Обработка ошибок

### 1. Классифицированная обработка исключений

Используйте `make_error()` для построения стандартизированных ответов об ошибках. При выполнении запросов через `sdk.client` перехватывайте исключения ErisPulse:

```python
from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError

async def call_api(self, endpoint: str, **params):
    try:
        from ErisPulse.Core import client
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self.make_response(data=response, raw=response)
    except ClientTimeoutError:
        self.logger.error(f"Таймаут запроса: {endpoint}")
        return self.make_error(retcode=32000, message="Таймаут запроса")
    except ClientError as e:
        self.logger.error(f"Сетевая ошибка: {e}")
        return self.make_error(retcode=33000, message="Сбой сетевого запроса")
    except json.JSONDecodeError:
        self.logger.error("Ошибка разбора JSON")
        return self.make_error(retcode=10006, message="Неверный формат ответа")
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **Обратная совместимость**: старый код адаптеров, напрямую использующий `aiohttp`, не затрагивается — по-прежнему можно перехватывать `aiohttp.ClientError`. Преобразование исключений действует только при запросах через `sdk.client`.

### 2. Логирование

Фреймворк автоматически создаёт дочерний logger для адаптера (`sdk.logger.get_child("MyAdapter")`), ручная инициализация не требуется:

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # после объявления класса конфигурации self.logger доступен автоматически
    
    async def start(self):
        self.logger.info("Запуск адаптера...")
        # ...
        self.logger.info("Адаптер запущен")
    
    async def shutdown(self):
        self.logger.info("Остановка адаптера...")
        # ...
        self.logger.info("Адаптер остановлен")
```

## Тестирование

### 1. Модульные тесты

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """Тестирование конвертера"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """Тестирование формата ответа API"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. Интеграционные тесты

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """Тестирование запуска адаптера"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """Тестирование отправки сообщений"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## Обратное преобразование и построение сообщений

`Raw_ob12` — метод, который адаптер **обязан реализовать**: это единая точка входа обратного преобразования (OneBot12 → платформа). Стандартные методы (`Text`, `Image` и т.д.) должны делегировать в `Raw_ob12`, а состояние модификаторов (`At`/`Reply`/`AtAll`) должно объединяться в сегменты сообщения внутри `Raw_ob12`.

`MessageBuilder` — инструмент построения сегментов сообщений, используемый вместе с `Raw_ob12`; поддерживает цепочные вызовы и быстрое построение.

> Полную спецификацию реализации, примеры кода и инструкции по использованию см. в:
> - [Спецификация методов отправки §6 Спецификация обратного преобразования](../../standards/send-method-spec.md#6-спецификация-обратного-преобразованияonebot12--платформа)
> - [Спецификация методов отправки §11 Конструктор сообщений](../../standards/send-method-spec.md#11-конструктор-сообщений-messagebuilder)

## Расширение методами событий платформы

Адаптер может регистрировать специфичные для платформы методы у классов-обёрток Event, чтобы разработчики модулей могли удобнее обращаться к специфичным данным платформы.

### 1. Массовая регистрация с помощью Mixin-класса (рекомендуется)

Если у платформы несколько специфичных методов, рекомендуется использовать Mixin-класс:

```python
# Регистрация в start() адаптера или на уровне модуля
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """Получение названия чата"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """Проверка, является ли сообщение официальным"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """Получение типа сообщения платформы"""
        return self.get("myplatform_raw", {}).get("msg_type", "text")

# Массовая регистрация
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. Регистрация отдельного метода с помощью декоратора

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("myplatform")
def get_chat_name(self):
    return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")
```

### 3. Очистка при остановке адаптера

```python
from ErisPulse.Core.Event import unregister_platform_event_methods

class MyAdapter(BaseAdapter):
    async def shutdown(self):
        # Очистка регистрации методов событий платформы
        unregister_platform_event_methods("myplatform")
        # ... остальная очистка
```

> Более подробные сведения о регистрации и отмене регистрации см. в [API системы событий - Регистрация методов расширения платформы](../../api-reference/event-system.md#регистрация-методов-расширения-платформы-адаптером).

## Поддержка документации

### 1. Поддержка документации по особенностям платформы

Создайте документ `{platform}.md` в каталоге `docs/ru/platform-guide/` (версии на других языках будут сгенерированы автоматически):

```markdown
# Документация адаптера платформы

## Основная информация
- Версия соответствующего модуля: 1.0.0
- Сопровождающий: Ваше имя

## Поддерживаемые типы отправляемых сообщений
...

## Специфичные типы событий
...

## Параметры конфигурации
...
```

### 2. Обновление информации о версии

При выпуске новой версии обновите информацию о версии в документации:

```toml
[project]
version = "2.0.0"  # обновить номер версии
```

## Связанная документация

### Предварительные знания

- [Введение в разработку адаптеров](getting-started.md) — создание первого адаптера
- [Основные концепции адаптеров](core-concepts.md) — знакомство с архитектурой адаптеров
- [Подробно о SendDSL](send-dsl.md) — изучение отправки сообщений

### После доработки адаптера

- [Руководство по публикации и магазину модулей](../publishing.md) — публикация на PyPI и в магазине модулей