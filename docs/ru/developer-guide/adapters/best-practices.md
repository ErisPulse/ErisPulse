# Рекомендации по разработке адаптера

Документ предоставляет рекомендации по лучшим практикам разработки адаптеров для ErisPulse.

## Управление состоянием бота и Meta-события

Адаптер должен активно отправлять meta-события через `adapter.emit()`, чтобы фреймворк автоматически отслеживал соединение бота, моменты онлайна и пульсации (heartbeat).

### 1. Когда отправлять Meta-события

| Событие | `detail_type` | Триггер | Поведение фреймворка |
|------|--------------|---------|---------|
| Подключение | `"connect"` | При установке соединения между ботом и платформой | Регистрация бота, запуск жизненного цикла `adapter.bot.online` |
| Отключение | `"disconnect"` | При разрыве соединения между ботом и платформой | Пометка бота как оффлайн, запуск жизненного цикла `adapter.bot.offline` |
| Пульсация (Heartbeat) | `"heartbeat"` | Регулярная отправка (рекомендуется каждые 30-60 секунд) | Обновление времени активности и метаданных бота |

### 2. Отправка Meta-события

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Бот онлайн: отправить событие connect
        await self.adapter.emit({
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": bot_id,
                "user_name": "MyBot",
                "nickname": "我的机器人",
                "avatar": "https://example.com/avatar.png",
            }
        })

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Бот оффлайн: отправить событие disconnect
            await self.adapter.emit({
                "type": "meta",
                "detail_type": "disconnect",
                "platform": "myplatform",
                "self": {
                    "platform": "myplatform",
                    "user_id": bot_id,
                }
            })
```

### 3. Событие сердцебиения

Адаптер должен регулярно отправлять событие сердцебиения во время существования соединения, чтобы обновлять время активности бота:

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            await self.adapter.emit({
                "type": "meta",
                "detail_type": "heartbeat",
                "platform": "myplatform",
                "self": {
                    "platform": "myplatform",
                    "user_id": bot_id,
                }
            })
            await asyncio.sleep(30)
```

### 4. Автоматическое определение поля self

Фреймворк `adapter.emit()` автоматически обрабатывает поле `self` во всех событиях (не только в meta-событиях):

- **Поля `self` в обычных событиях** (message/notice/request) автоматически определяются и регистрируют бота
- **Расширенная информация поля `self`**: поддерживаются необязательные поля `user_name`, `nickname`, `avatar`, `account_id`

```python
# Включение поля self в конвертере автоматически зарегистрирует бота
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "我的机器人",
    },
    # ... остальные поля
}
await self.adapter.emit(onebot_event)
# Бот "bot123" автоматически зарегистрирован и обновлено время активности
```

### 5. Запрос состояния бота

Фреймворк предоставляет следующие методы запроса:

```python
from ErisPulse import sdk

# Получение подробной информации о боте
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# Вывод списка всех ботов (группировка по платформе)
all_bots = sdk.adapter.list_bots()

# Вывод списка ботов указанной платформы
platform_bots = sdk.adapter.list_bots("myplatform")

# Проверка, находится ли бот в сети
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Получение сводки полного статуса (подходит для отображения в WebUI)
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
                self.logger.info("Соединение установлено")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # Экспоненциальная задержка
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"Ошибка соединения, повторная попытка через {wait_time} сек ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Ошибка соединения, достигнуто максимальное количество попыток")
                    raise
```

### 2. Управление состоянием подключения

```python
class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
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

### 3. Сердцебиение для поддержки соединения и Meta-пульсация

Сердцебиение адаптера должно выполнять две задачи одновременно: отправлять пульсацию для поддержки соединения на платформе и отправлять событие meta heartbeat во фреймворк.

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. Отправка пульсации на платформу (keep-alive)
                await self.connection.send_json({"type": "ping"})

                # 2. Отправка события meta heartbeat во фреймворк (обновление времени активности бота)
                await self.adapter.emit({
                    "type": "meta",
                    "detail_type": "heartbeat",
                    "platform": "myplatform",
                    "self": {
                        "platform": "myplatform",
                        "user_id": self._bot_id,
                    }
                })

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Ошибка пульсации: {e}")
                break
```

## Конвертация событий

### 1. Строгое соответствие стандарту OneBot12

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
    """Преобразование в 10-значную метку времени в секундах"""
    if not timestamp:
        return int(time.time())
    
    # Если это миллисекундная метка времени
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # Если это метка времени в секундах
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
    # Если платформа не предоставила ID, генерировать UUID
    return str(uuid.uuid4())
```

## Реализация SendDSL

Декораторы `At`/`AtAll`/`Reply` встроены в базовый класс `SendDSL` фреймворка, адаптеру нужно реализовать только `Raw_ob12` и конкретные методы отправки. Используйте `self._apply_modifiers(message)` и `self.send_context` для упрощения разработки.

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

### 2. Методы цепных модификаторов возвращают self

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # Возврат self
```

### 3. Поддержка платформенных методов

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

## Ответ API

### 1. Стандартизированный формат ответа

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return {
            "status": "ok" if raw_response.get("success") else "failed",
            "retcode": 0 if raw_response.get("success") else raw_response.get("code", 10001),
            "data": raw_response.get("data"),
            "message_id": raw_response.get("data", {}).get("message_id", ""),
            "message": "",
            "myplatform_raw": raw_response
        }
    except Exception as e:
        return {
            "status": "failed",
            "retcode": 34000,
            "data": None,
            "message_id": "",
            "message": str(e),
            "myplatform_raw": None
        }
```

### 2. Спецификация кодов ошибок

Соблюдение стандартов кодов ошибок OneBot12:

```python
# 1xxxx - Ошибки запросов на действия
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - Ошибки обработчика действий
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - Ошибки выполнения действий
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## Поддержка нескольких аккаунтов

### 1. Проверка конфигурации аккаунта

```python
def _get_config(self):
    """Проверка конфигурации"""
    config = self.config_manager.getConfig("MyAdapter", {})
    accounts = config.get("accounts", {})
    
    if not accounts:
        # Создание аккаунта по умолчанию
        default_account = {
            "token": "",
            "enabled": False
        }
        config["accounts"] = {"default": default_account}
        self.config_manager.setConfig("MyAdapter", config)
    
    return config
```

### 2. Механизм выбора аккаунта

```python
async def _get_account_for_message(self, event):
    """Выбор аккаунта для отправки на основе события"""
    bot_id = event.get("self", {}).get("user_id")
    
    # Поиск соответствующего аккаунта
    for account_name, account_config in self.accounts.items():
        if account_config.get("bot_id") == bot_id:
            return account_name
    
    # Если не найден, используется первый включенный аккаунт
    for account_name, account_config in self.accounts.items():
        if account_config.get("enabled", True):
            return account_name
    
    return None
```

## Обработка ошибок

### 1. Обработка исключений по категориям

```python
async def call_api(self, endpoint: str, **params):
    try:
        # Рекомендуется использовать встроенный клиент SDK для отправки запросов API
        from ErisPulse.Core import client
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self._standardize_response(response)
    except aiohttp.ClientError as e:
        # Ошибка сети (встроенный механизм повторных попыток клиента обработает это)
        self.logger.error(f"Сетевая ошибка: {e}")
        return self._error_response("Не удалось выполнить сетевой запрос", 33000)
    except asyncio.TimeoutError:
        # Ошибка тайм-аута
        self.logger.error(f"Тайм-аут запроса: {endpoint}")
        return self._error_response("Тайм-аут запроса", 32000)
    except json.JSONDecodeError:
        # Ошибка парсинга JSON
        self.logger.error("Не удалось разобрать JSON")
        return self._error_response("Неверный формат ответа", 10006)
    except Exception as e:
        # Неизвестная ошибка
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        return self._error_response(str(e), 34000)
```

### 2. Логирование

```python
class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.logger = logger.get_child("MyAdapter")
    
    async def start(self):
        self.logger.info("Запуск адаптера...")
        # ...
        self.logger.info("Адаптер запущен")
    
    async def shutdown(self):
        self.logger.info("Завершение работы адаптера...")
        # ...
        self.logger.info("Адаптер остановлен")
```

## Тестирование

### 1. Unit-тесты

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

`Raw_ob12` — это метод, который адаптер **должен реализовать**, являющийся единым входом для обратного преобразования (OneBot12 → Платформа). Стандартные методы (`Text`, `Image` и др.) должны делегировать его `Raw_ob12`, а состояние модификаторов (`At`/`Reply`/`AtAll`) должно быть объединено в сегменты сообщений внутри `Raw_ob12`.

`MessageBuilder` — это инструмент для построения сегментов сообщений, используемый в паре с `Raw_ob12`, поддерживающий цепной вызов и быстрое построение.

> Для полной спецификации реализации, примеров кода и инструкций по использованию см.:
> - [Спецификация методов отправки §6 Обратное преобразование](../../standards/send-method-spec.md#6-обратное-преобразование-onebot12--платформа)
> - [Спецификация методов отправки §11 Конструктор сообщений](../../standards/send-method-spec.md#11-конструктор-сообщений-messagebuilder)

## Расширение платформенных методов событий

Адаптер может регистрировать платформенные специфические методы для классов-оберток событий, чтобы разработчики модулей могли удобнее получать доступ к специфичным данным платформы.

### 1. Использование класса Mixin для пакетной регистрации (Рекомендуется)

Если у платформы много специфических методов, рекомендуется использовать класс Mixin:

```python
# Регистрация на уровне модуля или в start() адаптера
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

# Пакетная регистрация
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. Использование декоратора для регистрации отдельного метода

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
        # Очистка регистрации платформенных методов событий
        unregister_platform_event_methods("myplatform")
        # ... другая очистка
```

> Более подробные инструкции по регистрации и отмене регистрации см. в [API системы событий - Регистрация платформенных расширений](../../api-reference/event-system.md#регистрация-платформенных-расширений-адаптером).

## Поддержка документации

### 1. Поддержка документации платформенных возможностей

Создайте документ `{platform}.md` в папке `docs/ru-RU/platform-guide/` (остальные языковые версии будут созданы автоматически):

```markdown
# Документация адаптера для Название платформы

## Основная информация
- Версия соответствующего модуля: 1.0.0
- Ответственный: Ваше Имя

## Поддерживаемые типы отправки сообщений
...

## Специфические типы событий
...

## Параметры конфигурации
...
```

### 2. Обновление информации о версии

При выпуске новой версии обновляйте информацию о версии в документации:

```toml
[project]
version = "2.0.0"  # Обновление номера версии
```

## Связанные документы

- [Введение в разработку адаптера](getting-started.md) - Создание первого адаптера
- [Основные концепции адаптера](core-concepts.md) - Понимание архитектуры адаптера
- [Подробное описание SendDSL](send-dsl.md) - Изучение отправки сообщений