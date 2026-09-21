# Модульное тестирование (ErisPulse-Testing)

[ErisPulse-Testing](https://github.com/wsu2059q/ErisPulse-Testing) — это официальный инструментальный пакет для тестирования (направление 3 RFC EPRFC-2026-001):
Предоставляет `TestBot`, фабрику тестовых событий, захват и утверждения исходящих сообщений, делая модульное тестирование таким же простым, как написание обычных pytest-тестов.

```bash
pip install ErisPulse-Testing
```

> Инструмент для разработки с односторонней зависимостью от фреймворка, не вмешивающийся во время выполнения. Для проверки подключения к платформе адаптера используйте `tests/devs/test_adapter.py` из репозитория фреймворка.

## Быстрый старт

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="今天已签到")
        async def daily(event):
            await event.reply("签到成功！")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "签到成功！"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("今天已签到")   # 第二次命中冷却
```

Рекомендуется использовать `TestBot` с `async with`: при запуске регистрируется MockAdapter (перехватывает весь исходящий трафик),
отключается дедупликация событий, применяются переопределения конфигурации; при выходе автоматически очищаются глобальные состояния фреймворка, что предотвращает взаимное загрязнение между тестовыми случаями.

Сопутствующие pytest fixtures (автоматически доступны после установки):

- `testbot`: стандартный TestBot уровня function (`platform=`test`、prefix `/`)
- `make_testbot(**kwargs)`: фабрика с пользовательскими параметрами (`prefix` / `config` / `platform` / `bot_id` ...)

Рекомендуется в конфигурации тестового проекта установить `asyncio_mode = "auto"` (`[tool.pytest.ini_options]`),
или добавить `@pytest.mark.asyncio` к тестовым функциям.

## Фабрика событий

| Функция | Описание |
|------|------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | Событие сообщения; если `group_id` пустой, значит личное сообщение |
| `create_command_event("roll 3", prefix="/")` | Командное сообщение (автоматически добавляет префикс, если уже есть префикс, не добавляет повторно) |
| `create_notice_event(type, ...)` | Событие уведомления (например `friend_add`) |
| `create_request_event(type, ...)` | Событие запроса (например, заявка в друзья) |
| `create_meta_event("connect", ...)` | Мета-событие (например, `connect` может заставить бота войти в сеть) |

Все события используют уникальный `id` в виде uuid, что автоматически предотвращает дублирование событий в рамках фреймворка.

## TestBot API

### Диспетчеризация

```python
trace = await bot.dispatch(event)          # Диспетчеризация и ожидание обработки, возвращает цепочку решений
await bot.dispatch(event, drain=False)     # Первая взаимодействующая отправка: без ожидания (обработчик wait_reply остаётся активным)
await bot.send_message("你好")             # Упрощённый способ отправки сообщения
await bot.reply_as("18", user_id="u1")     # Эмуляция ответа пользователя для wait_reply (автоматически ожидает готовности waiter)
```

`dispatch()` собирает все задачи обработчиков после emit и возвращает управление сразу после завершения обработки — **в тестах не нужно использовать sleep**.

### Утверждения по исходящим сообщениям

```python
bot.replies                # Все исходящие сообщения (список SentMessage)
bot.last_reply.text        # Текст последнего ответа
bot.replies_to("123")      # Фильтрация по целевому идентификатору
bot.clear_replies()        # Изоляция утверждений между этапами
bot.assert_replied()                       # Существование исходящих сообщений
bot.assert_replied(contains="签到", to="123")
bot.assert_not_replied()                   # Отсутствие исходящих сообщений
bot.assert_reply_contains("签到成功")       # Существование исходящего сообщения, содержащего указанный текст
await bot.wait_for_reply(timeout=2)        # Ожидание появления асинхронного ответа
```

Поля `SentMessage`: `text` (первый текстовый сегмент), `segments` (полный список сегментов сообщения),  
`target_type` / `target_id` / `bot_id` (контекст отправки), `has_modifier("at")` и др.

### Загрузка модулей

```python
await bot.load_module("MyModule")   # Имя пакета с уже зарегистрированным entry-point
await bot.load_module(MyModule)     # Или подкласс BaseModule (автоматическая регистрация + загрузка)
await bot.unload_module("MyModule")
```

Команды / обработчики событий, зарегистрированные в `on_load`, принадлежат модулю, при отключении автоматически удаляются, можно напрямую проверять "отключение команды после выгрузки модуля".

### Замена зависимостей

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

Заменяется функция, указанная в `Depends(get_session)` в таблице команд, автоматически восстанавливается при выходе из `with`.

### Переопределение конфигурации

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # Конфигурация модуля (читается через self.cfg)
})
```

Конфигурация внедряется в оперативную память (не сохраняется на диск), префикс команд и другие параметры обновляются в режиме реального времени.

## Декоративная цепочка распределения (диагностика "почему команда не была вызвана")

`dispatch()` возвращает `DispatchTrace` — цепочку причинно-следственных связей, по которым прошла текущая диспетчеризация:

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # построчное объяснение причинно-следственных связей (на текущем языке)
trace.command        # имя команды, которая была вызвана (если не найдено, то None)
trace.steps("cooldown")  # фильтрация записей о проверке по этапам

trace.assert_executed("daily")  # утверждение выполнения (в случае сбоя прикрепляет полную цепочку причинно-следственных связей)
trace.assert_rejected()         # утверждение, что команда была отклонена проверкой на права
trace.assert_dropped()          # утверждение, что команда была скрыто отброшена (например, из-за кулдауна)
trace.assert_no_match()         # утверждение, что команда не была найдена
```

Проверки включают: текст команды, соответствие команды (в случае несовпадения — рекомендации по орфографии), область действия, пользовательские ACL, проверку владельца, функции прав, кулдаун и скрытое отбрасывание, анализ параметров, результат выполнения, промежуточные отрицания промежуточных обработчиков.

В производственной среде также доступны встроенные средства фреймворка `ErisPulse.Core.Event.trace` (`start_dispatch_trace()` / `format_dispatch_trace()`) для сбора и отображения цепочки решений.

[Документация на русском языке](docs/ru/quick-start.md)