# Рекомендации по лучшим практикам разработки адаптеров

Данный документ предоставляет рекомендации по лучшим практикам разработки адаптеров ErisPulse.

## Управление состоянием бота и мета-события

Адаптер должен активно отправлять мета-события через `adapter.emit()`, чтобы фреймворк автоматически отслеживал состояние подключения, онлайн/оффлайн иheartbeat бота.

### 1. Когда отправлять мета-события

| Событие | `detail_type` | Триггер | Поведение фреймворка |
|------|--------------|---------|---------|
| Подключение | `"connect"` | При установлении подключения бота с платформой | Регистрация бота, запуск жизненного цикла `adapter.bot.online` |
| Отключение | `"disconnect"` | При разрыве подключения бота с платформой | Отмечает бота как оффлайн, запуск жизненного цикла `adapter.bot.offline` |
| heartbeat | `"heartbeat"` | Регулярно (рекомендуется 30-60 секунд) | Обновление времени активности и мета-информации бота |

### 2. Отправка мета-событий

Фреймворк предоставляет метод `emit_meta()`, который позволяет отправить мета-событие всего одной строкой:

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Бот онлайн: отправка события connect всего одной строкой
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
            # Бот оффлайн
            await self.emit_meta("disconnect", bot_id)
```

### 3. Событие heartbeat

Адаптер должен регулярно отправлять heartbeat-события в течение активного подключения, чтобы обновить время активности бота:

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # Отправка мета-heartbeat фреймворку (одна строка)
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. Автоматическое обнаружение self-поля

Метод `adapter.emit()` фреймворка автоматически обрабатывает все события (не только мета-события) с полем `self`:

- **Обычные события** (message/notice/request) с полем `self` автоматически регистрируют бота
- **Дополнительная информация в поле self**: поддерживает необязательные поля `user_name`, `nickname`, `avatar`, `account_id`

```python
# В конвертере достаточно иметь поле self для автоматической регистрации бота
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
# Бот "bot123" автоматически зарегистрирован и обновлено время активности
```

### 5. Запрос состояния бота

Фреймворк предоставляет следующие методы для запроса:

```python
from ErisPulse import sdk

# Получение информации о боте
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# Получить список всех ботов (группировка по платформе)
all_bots = sdk.adapter.list_bots()

# Получить список ботов для указанной платформы
platform_bots = sdk.adapter.list_bots("myplatform")

# Проверить, онлайн ли бот
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Получить полную сводку состояния (подходит для WebUI)
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

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
                        f"Подключение не удалось, повтор через {wait_time} секунд ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Подключение не удалось, достигнуто максимальное количество попыток")
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
        self.logger.info("Подключение установлено")
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._process_event(data)
        except WebSocketDisconnect:
            self.logger.info("Подключение разорвано")
        finally:
            self.connection = None
            self._connected = False
```

### 3. heartbeat и мета-heartbeat

Адаптер должен выполнять две задачи в heartbeat: отправлять heartbeat-сообщение платформе и отправлять мета-heartbeat-событие фреймворку.

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. Отправка heartbeat-сообщения платформе
                await self.connection.send_json({"type": "ping"})

                # 2. Отправка мета-heartbeat (одна строка)
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Ошибка heartbeat: {e}")
                break
```

### 4. Информация о подключении

Роуты адаптера должны быть доступны пользователям для настройки адресов обратного вызова. Рекомендуется выводить информацию о подключении в `start()`:

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
                self.logger.info(f"Адрес WebSocket: "
                    f"{info.get('connection', {}).get('base_url', '')}"
                    f"{info.get('connection', {}).get('websocket_routes', [])}")
```

Пользователи могут использовать следующие API для просмотра роутов и адресов подключения:

```python
from ErisPulse import sdk

# Информация о подключении на уровне адаптера (рекомендуется)
info = sdk.adapter.get_connection_info("myplatform")

# Запрос на уровне менеджера роутов
sdk.router.list_namespaces()              # Список всех пространств имён
sdk.router.get_module_routes("myplatform")  # Подробная информация о роутах
sdk.router.get_module_urls("myplatform")    # Полные URL подключения
```

> **Важно**: `module_name` при регистрации роута должен полностью совпадать с именем `platform` адаптера в ErisPulse, иначе `get_connection_info()` не сможет сопоставить роут. Многоаккаунтные адаптеры должны регистрировать подпути (например, `/account1/webhook`, `/account2/webhook`), а не использовать разные `module_name`.

## Преобразование событий

### 1. Строгое следование стандарту OneBot12

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование событий"""
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
            "myplatform_raw": raw_event,  # Сохранить исходные данные (обязательно)
            "myplatform_raw_type": raw_event.get("type", "")  # Тип исходных данных (обязательно)
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

### 3. Генерация идентификатора события

```python
import uuid

def _generate_event_id(self, raw_event):
    """Генерация идентификатора события"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # Если платформа не предоставляет ID, генерируем UUID
    return str(uuid.uuid4())
```

## Реализация SendDSL

Модификаторы `At`/`AtAll`/`Reply` уже встроены в базовый класс SendDSL фреймворка, адаптеру нужно только реализовать `Raw_ob12` и конкретные методы отправки. Использование `self._apply_modifiers(message)` и `self.send_context` упрощает разработку.

### 1. Обязательно возвращать объект Task

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

### 2. Методы-модификаторы возвращают self

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # Возвращает self
```

### 3. Поддержка платформо-специфических методов

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
        """Отправка карточки"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": {"card_data": card_data}}],
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

`make_response()` автоматически генерирует ответ с ключом `{platform}_raw`. `make_error()` по умолчанию использует `retcode=34000` (Platform Error).

### 2. Стандартные коды ошибок

Следование стандартным кодам ошибок OneBot12:

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

Использование `AccountConfigClass` для декларирования класса конфигурации позволяет фреймворку автоматически управлять загрузкой, проверкой и генерацией шаблонов. `BotAccountConfig` базовый класс предоставляет поля `enabled` и `name`, адаптеру не нужно их декларировать:

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
            # bot_id автоматически заполняется фреймворком из протокола платформы/ответа входа
    
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

Фреймворк предоставляет метод `_resolve_account()` для сопоставления аккаунта по приоритету:

1. **Имя аккаунта** — точное совпадение с ключом конфигурации
2. **`bot_id`** — автоматически полученный bot_id (то есть `event["self"]["user_id"]`)
3. **Любое строковое поле** — другие строковые поля в конфигурации
4. **По умолчанию** — первый включенный аккаунт

```python
# По имени аккаунта
name, account = self._resolve_account("account1")

# По bot_id (наиболее часто используемый способ, из события)
name, account = self._resolve_account("bot_123")

# Получить первый включенный аккаунт (передав None)
name, account = self._resolve_account(None)
```

## Обработка ошибок

### 1. Классификация обработки исключений

Использование `make_error()` для построения стандартизированных ответов. При запросах через `sdk.client` ловить исключения ErisPulse:

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
        self.logger.error(f"Ошибка сети: {e}")
        return self.make_error(retcode=33000, message="Ошибка сети")
    except json.JSONDecodeError:
        self.logger.error("Ошибка парсинга JSON")
        return self.make_error(retcode=10006, message="Неверный формат ответа")
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **Обратная совместимость**: старый код адаптера, использующий `aiohttp`, не затрагивается, он по-прежнему может ловить `aiohttp.ClientError`. Преобразование исключений происходит только при запросах через `sdk.client`.

### 2. Логирование

Фреймворк автоматически создает под-logger для адаптера (`sdk.logger.get_child("MyAdapter")`), нет необходимости вручную инициализировать:

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # Объявление класса конфигурации делает self.logger доступным
    
    async def start(self):
        self.logger.info("Запуск адаптера...")
        # ...
        self.logger.info("Запуск адаптера завершен")
    
    async def shutdown(self):
        self.logger.info("Остановка адаптера...")
        # ...
        self.logger.info("Остановка адаптера завершена")
```

## Тестирование

### 1. Модульные тесты

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """Тест конвертера"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """Тест формата ответа API"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. Интеграционные тесты

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """Тест запуска адаптера"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """Тест отправки сообщения"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## Обратное преобразование и построение сообщений

`Raw_ob12` является обязательным методом, который адаптер должен реализовать, это единый вход для обратного преобразования (OneBot12 → платформа). Стандартные методы (`Text`, `Image` и т.д.) должны делегировать вызов `Raw_ob12`, а состояние модификаторов (`At`/`Reply`/`AtAll`) должно объединяться в сообщение внутри `Raw_ob12`.

`MessageBuilder` — это инструмент для построения сообщений, совместимый с `Raw_ob12`, поддерживающий цепочечные вызовы и быстрое построение.

> Полные рекомендации по реализации, примеры кода и инструкции по использованию см. в:
> - [Спецификации методов отправки §6 Спецификация обратного преобразования](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [Спецификации методов отправки §11 Построитель сообщений](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## Расширение методов событий платформы

Адаптер может зарегистрировать платформо-специфические методы для класса Event, чтобы разработчикам модулей было удобнее получать доступ к платформо-специфическим данным.

### 1. Использование Mixin-класса для регистрации (рекомендуется)

При наличии нескольких платформо-специфических методов рекомендуется использовать Mixin-класс:

```python
# Регистрация на уровне start() адаптера или модуля
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """Получение названия чата"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """Определение, является ли сообщение официальным"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """Получение типа сообщения"""
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
        # Очистка зарегистрированных платформо-специфических методов событий
        unregister_platform_event_methods("myplatform")
        # ... другие очистки
```

> Более подробная информация о регистрации и удалении см. в [API системы событий - Регистрация платформо-специфических методов](../../api-reference/event-system.md#适配器注册平台扩展方法).

## Обновление документации

### 1. Обновление документации платформы

Создайте документацию платформы в `docs/ru/platform-guide/` (другие языковые версии будут автоматически генерироваться):

```markdown
# Документация адаптера для платформы

## Основная информация
- Версия модуля: 1.0.0
- Автор: Ваше имя

## Поддерживаемые типы отправки сообщений
...

## Специфические типы событий
...

## Параметры конфигурации
...
```

### 2. Обновление версии

При выпуске новой версии обновите версию в документации:

```toml
[project]
version = "2.0.0"  # Обновите номер версии
```

## Связанные документы

- [Введение в разработку адаптеров](getting-started.md) - Создание первого адаптера
- [Основные понятия адаптеров](core-concepts.md) - Понимание архитектуры адаптеров
- [Подробности SendDSL](send-dsl.md) - Изучение отправки сообщений