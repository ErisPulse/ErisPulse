# Рекомендуемые практики разработки адаптеров

> [!TIP]
> **Когда читать эту статью**: после запуска шаблона адаптера рекомендуется прочитать (оптимальные практики инженерии). Если не нужно, пропустите, это не повлияет на использование других функций.

Здесь собраны инженерные соглашения для разработки адаптеров: отчет о состоянии бота, повторное подключение и пинг, разбор нескольких аккаунтов, стандартизированные ответы на ошибки — следуя этим правилам, можно избежать таких распространённых проблем при подключении к платформе, как отсутствие уведомлений об отключении, отправка сообщений на неправильный аккаунт, трудности в поиске ошибок.

## Управление состоянием бота и событие Meta

Адаптер должен активно отправлять событие meta через `adapter.emit()`, чтобы фреймворк автоматически отслеживал состояние подключения, входа/выхода и пинг бота.

### 1. Когда отправлять событие Meta

| Событие | `detail_type` | Триггер | Поведение фреймворка |
|------|--------------|---------|---------|
| Подключение | `"connect"` | При установлении подключения бота к платформе | Регистрирует бота, запускает событие жизненного цикла `adapter.bot.online` |
| Отключение | `"disconnect"` | При разрыве подключения бота к платформе | Отмечает бота как отключённого, запускает событие жизненного цикла `adapter.bot.offline` |
| Пинг | `"heartbeat"` | Регулярная отправка (рекомендуется 30-60 секунд) | Обновляет время активности и метаинформацию бота |

### 2. Отправка события Meta

Фреймворк предоставляет метод `emit_meta()`, с помощью которого можно отправить событие meta одной строкой:

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
            # Бот отключён
            await self.emit_meta("disconnect", bot_id)
```

Также можно вручную создать стандартное событие meta (старый способ по-прежнему совместим):

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

### 3. Событие пинга

Адаптер должен периодически отправлять пинг-событие в течение времени подключения, чтобы обновить время активности бота:

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # Отправка meta heartbeat в фреймворк (одной строкой)
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. Автоматическое обнаружение поля `self`

Метод `adapter.emit()` фреймворка автоматически обрабатывает все события (не только события meta), содержащие поле `self`:

- В полях `self` обычных событий (message/notice/request) будет автоматически обнаружен и зарегистрирован бот
- **Дополнительная информация в поле `self`**: поддерживаются необязательные поля `user_name`, `nickname`, `avatar`, `account_id`

```python
# В конвертере достаточно указать поле `self` для автоматической регистрации бота
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

Интерфейсы API (get_bot_info() / list_bots() / is_bot_online() / get_status_summary()) и таблица событий жизненного цикла бота см. в разделе [API системы адаптера - Управление состоянием бота](../../api-reference/adapter-system.md#bot-状态管理).

## Управление подключением

### 1. Реализация повторного подключения

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
                    # Стратегия экспоненциального отложенного повтора
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

### 3. Пинг и событие meta пинга

Пинг адаптера должен выполнять две задачи: отправлять пинг-сообщение платформе и отправлять событие meta heartbeat в фреймворк.

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. Отправка пинг-сообщения платформе
                await self.connection.send_json({"type": "ping"})

                # 2. Отправка meta heartbeat в фреймворк (одной строкой)
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Ошибка пинга: {e}")
                break
```

### 4. Отображение информации о подключении

Роуты, зарегистрированные адаптером, должны быть доступны пользователям, чтобы они могли настроить обратный адрес на стороне платформы. Рекомендуется в методе `start()` активно выводить информацию о подключении:

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

Пользователи могут использовать следующие API для просмотра всех роутов и адресов подключения адаптера:

```python
from ErisPulse import sdk

# Информация о подключении на уровне адаптера (рекомендуется)
info = sdk.adapter.get_connection_info("myplatform")

# Запросы на уровне менеджера роутов
sdk.router.list_namespaces()              # Список всех пространств имён
sdk.router.get_module_routes("myplatform")  # Подробная информация о роутах
sdk.router.get_module_urls("myplatform")    # Полные адреса подключения
```

> **Важно**: `module_name`, указанный при регистрации роута, должен полностью совпадать с именем `platform`, зарегистрированным в ErisPulse, иначе `get_connection_info()` не сможет сопоставить роут. Для адаптеров с несколькими аккаунтами следует регистрировать подпути (например, `/account1/webhook`, `/account2/webhook`), а не использовать разные `module_name`.

### 5. Жизненный цикл HTTP-роутов

HTTP/WebSocket-роуты, зарегистрированные адаптером/модулем через `router`, управляются фреймворком по принципу принадлежности:

- `module_name` (пространство имён), указанное при регистрации, является идентификатором принадлежности; **при перезагрузке / остановке / выгрузке фреймворк автоматически очищает все роуты и ресурсы подключения в этом пространстве имён**, без необходимости ручного удаления
- Поэтому **в `start()` (для модуля `on_load`) необходимо безусловно повторно регистрировать роуты**. Не используйте булевы флаги на уровне экземпляра для "регистрации только один раз": горячая перезагрузка конфигурации (например, изменение полей аккаунта и немедленное сохранение) вызывает stop/start и **переиспользует тот же экземпляр**, следовательно, оставшийся флаг приведёт к тому, что роуты будут удалены и **навсегда потеряются**, что проявится как 404 ошибки интерфейса и восстановление только после перезапуска процесса

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # Безусловно повторно регистрируем роуты при каждом запуске (роуты были автоматически удалены при предыдущем stop)
        router.register_http_route(self.platform, "/qr/start", self._qr_start, methods=["POST"])
        router.register_http_route(self.platform, "/qr/poll", self._qr_poll, methods=["POST"])
```

Аналогично для модуля (в `on_load`):

```python
class MyModule(BaseModule):
    async def on_load(self):
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

Если необходимо **заранее вручную удалить роут** (например, динамически отключить какой-то вход), можно активно отменить регистрацию:

```python
from ErisPulse.Core import router

router.unregister_http_route(self.platform, "/qr/start")
```

- Пользователи/клиенты могут временно получать ошибку 404 в окне горячей перезагрузки, это кратковременное явление; для интерфейсов, ориентированных на браузер, рекомендуется ограничить автоматические повторные попытки при 404 ошибке

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
            "myplatform_raw": raw_event,  # Сохраняем исходные данные (обязательно)
            "myplatform_raw_type": raw_event.get("type", "")  # Тип исходного события (обязательно)
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

Декораторы `At`/`AtAll`/`Reply` уже встроены в базовый класс SendDSL фреймворка, адаптеру нужно только реализовать `Raw_ob12` и конкретные методы отправки. Использование `self._apply_modifiers(message)` и `self.send_context` упрощает разработку.

### 1. Обязательное возвращение объекта Task

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

### 2. Методы цепочечного декорирования возвращают self

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # возвращаем self
```

### 3. Поддержка платформенных специфичных методов

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """Отправка стикеров"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                message=[{"type": "sticker", "data": {"id": sticker_id}}],
                **self.send_context
            )
        )
    
    def Card(self, card_data: dict):
        """Отправка карточек"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": {"data": card_data}}],
                **self.send_context
            )
        )
```

## Ответы API

### 1. Стандартизированный формат ответа

Фреймворк предоставляет методы `make_response()` и `make_error()` для построения стандартизированного ответа:

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

`make_response()` автоматически сгенерирует словарь ответа с ключом `{platform}_raw`. `make_error()` по умолчанию использует `retcode=34000` (Platform Error).

### 2. Нормы кодов ошибок

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

Использование `AccountConfigClass` для декларативного объявления класса конфигурации позволяет фреймворку автоматически управлять загрузкой, проверкой и генерацией шаблонов нескольких аккаунтов. Базовый класс `BotAccountConfig` предоставляет поля `enabled` и `name`, адаптеру не нужно объявлять их:

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
            # bot_id автоматически получается из протокола платформы/ответа на вход и возвращается обратно
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # name: имя аккаунта, account: экземпляр MyBotConfig
```

Файл конфигурации будет автоматически сгенерирован в формате:

```toml
[MyAdapter.accounts.default]
token = ""
enabled = true
name = ""
```

### 2. Механизм выбора аккаунта

Фреймворк предоставляет встроенный метод `_resolve_account()`, приоритеты сопоставления:

1. **Имя аккаунта** — точное совпадение с ключом конфигурации
2. **Поле `bot_id`** — автоматически получаемый bot_id (т.е. `event["self"]["user_id"]`)
3. **Любое строковое поле** — другие строковые поля конфигурации
4. **По умолчанию** — первый включённый аккаунт

```python
# По имени аккаунта
name, account = self._resolve_account("account1")

# По bot_id (самый распространённый способ, получается из события)
name, account = self._resolve_account("bot_123")

# Получение первого включённого аккаунта (передаём None)
name, account = self._resolve_account(None)
```

## Обработка ошибок

### 1. Классификация обработки исключений

Использование `make_error()` для построения стандартизированного ответа на ошибку. При запросе через `sdk.client` ловим исключения ErisPulse:

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
        self.logger.error("Ошибка декодирования JSON")
        return self.make_error(retcode=10006, message="Неверный формат ответа")
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **Обратная совместимость**: код старых адаптеров, использующих `aiohttp`, не затронут, они по-прежнему могут ловить `aiohttp.ClientError`. Преобразование исключений происходит только при использовании `sdk.client`.

### 2. Логирование

Фреймворк автоматически создаёт под-logger для адаптера (`sdk.logger.get_child("MyAdapter")`), без необходимости ручной инициализации:

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # После объявления класса конфигурации self.logger доступен
    
    async def start(self):
        self.logger.info("Запуск адаптера...")
        # ...
        self.logger.info("Запуск адаптера завершён")
    
    async def shutdown(self):
        self.logger.info("Остановка адаптера...")
        # ...
        self.logger.info("Остановка адаптера завершена")
```

## Тестирование

### 1. Юнит-тесты

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

`Raw_ob12` — это обязательный метод адаптера, единственный вход для обратного преобразования (OneBot12 → платформа). Стандартные методы (`Text`, `Image` и т.д.) должны делегировать вызов `Raw_ob12`, а состояние декораторов (`At`/`Reply`/`AtAll`) нужно объединять в сообщение внутри `Raw_ob12`.

`MessageBuilder` — это инструмент построения сообщений, совместимый с `Raw_ob12`, поддерживающий цепочечные вызовы и быстрое построение.

> Полный список реализации, примеров кода и использования см. в:
> - [Спецификации методов отправки §6 Спецификация обратного преобразования](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [Спецификации методов отправки §11 Конструктор сообщений](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## Расширение методов платформенных событий

Адаптер может зарегистрировать платформенные методы в классе обёртки событий, чтобы разработчики модулей могли более удобно получать доступ к платформенным данным.

### 1. Использование Mixin-класса для массовой регистрации (рекомендуется)

При наличии нескольких платформенных методов рекомендуется использовать Mixin-класс:

```python
# Регистрация в start() адаптера или на уровне модуля
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

### 3. Очистка при закрытии адаптера

```python
from ErisPulse.Core.Event import unregister_platform_event_methods

class MyAdapter(BaseAdapter):
    async def shutdown(self):
        # Очистка зарегистрированных методов платформенных событий
        unregister_platform_event_methods("myplatform")
        # ... другие очистки
```

> Подробные инструкции по регистрации и удалению см. в [API системы событий - Регистрация платформенных расширений](../../api-reference/event-system.md#适配器注册平台扩展方法).

## Обслуживание документации

### 1. Обслуживание документации платформенных характеристик

В каталоге `docs/ru/platform-guide/` создайте документ `{platform}.md` (другие языковые версии будут автоматически сгенерированы):

```markdown
# Документация адаптера платформы

## Основная информация
- Версия модуля: 1.0.0
- Автор: Ваше имя

## Поддерживаемые типы отправки сообщений
...

## Специфичные типы событий
...

## Параметры конфигурации
...
```

### 2. Обновление информации о версии

При выпуске новой версии обновите информацию о версии в документе:

```toml
[project]
version = "2.0.0"  # Обновите номер версии
```

## Связанные документы

### Повторное изучение предварительных знаний

- [Введение в разработку адаптеров](getting-started.md) - Создание первого адаптера
- [Основные понятия адаптера](core-concepts.md) - Ознакомьтесь с архитектурой адаптера
- [Подробности SendDSL](send-dsl.md) - Изучите отправку сообщений

### После улучшения адаптера

- [Руководство по публикации и магазину модулей](../publishing.md) - Публикация в PyPI и магазине модулей