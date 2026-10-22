# Стандарт типов сессий ErisPulse

> [!TIP]
> **Когда нужно читать эту статью**: когда вы адаптируете платформу, сопоставляя нативные сессии с платформы с типами (private/group/channel/guild/thread), или в модуле, если не уверены, какой тип цели нужно передавать в `Send.To()`, или хотите понять, как происходит автоматическое преобразование `event.reply()`. Если не нужно, можете пропустить.

В этом документе определены стандартные типы сессий, поддерживаемые ErisPulse, включая типы событий получения и типы целей отправки.

## 1. Основные понятия

### 1.1 Типы получения и отправки

ErisPulse различает два типа сессий:

- **Тип получения (Receive Type)**: поле `detail_type` события, используемое для получения
- **Тип отправки (Send Type)**: тип цели, используемый в методе `Send.To()` при отправке сообщений

### 1.2 Отношения между типами

```
Тип получения (detail_type)     Тип отправки (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**Ключевые моменты**:
- `private` — это тип получения, при отправке стандартный тип — `user`
- `group`, `channel`, `guild`, `thread` — одинаковые типы при получении и отправке
- **Рекомендуемый путь**: использовать `event.reply()` — автоматически выполняет преобразование типов и вывод цели, без необходимости ручного управления (автоматическое преобразование `private` → `user` происходит здесь)
- **При ручной отправке**: передавайте тип отправки (например, `Send.To("user", ...)`); передача типа получения, например, `Send.To("private", ...)` тоже может быть автоматически преобразована, но не рекомендуется (см. §6.1)

## 2. Стандартные типы сессий

### 2.1 Стандартные типы OneBot12

#### private
- **Тип получения**: `private`
- **Тип отправки**: `user`
- **Описание**: сообщения в личной переписке
- **Поле ID**: `user_id`
- **Применимые платформы**: все платформы, поддерживающие личную переписку

#### group
- **Тип получения**: `group`
- **Тип отправки**: `group`
- **Описание**: сообщения в группе, включая различные формы групп (например, supergroup в Telegram)
- **Поле ID**: `group_id`
- **Применимые платформы**: все платформы, поддерживающие групповые чаты

#### user
- **Тип получения**: `user`
- **Тип отправки**: `user`
- **Описание**: тип пользователя, некоторые платформы (например, Telegram) представляют личные чаты как `user`, а не `private`
- **Поле ID**: `user_id`
- **Применимые платформы**: Telegram и другие платформы

### 2.2 Расширенные типы ErisPulse

#### channel
- **Тип получения**: `channel`
- **Тип отправки**: `channel`
- **Описание**: сообщения в канале, поддерживают широковещательные сообщения нескольким пользователям
- **Поле ID**: `channel_id`
- **Применимые платформы**: Discord, Telegram, Line и др.

#### guild
- **Тип получения**: `guild`
- **Тип отправки**: `guild`
- **Описание**: сообщения в сервере/сообществе, обычно используются для событий уровня сервера Discord
- **Поле ID**: `guild_id`
- **Применимые платформы**: Discord и др.

#### thread
- **Тип получения**: `thread`
- **Тип отправки**: `thread`
- **Описание**: сообщения в теме/подканале, используются для подобсуждений в сообществах
- **Поле ID**: `thread_id`
- **Применимые платформы**: Discord Threads, Telegram Topics и др.

## 3. Сопоставление типов платформ

### 3.1 Принцип сопоставления

Адаптер отвечает за сопоставление нативных типов платформы со стандартными типами ErisPulse:

```
Нативный тип платформы → Стандартный тип ErisPulse → Тип отправки
```

### 3.2 Примеры сопоставления популярных платформ

#### Telegram
```
Тип Telegram          Тип получения ErisPulse    Тип отправки
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group
supergroup             group                   group  # Сопоставляется с group
channel                channel                 channel
```

#### Discord
```
Тип Discord          Тип получения ErisPulse    Тип отправки
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
Тип OneBot11        Тип получения ErisPulse    Тип отправки
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # Сопоставляется с group
```

## 4. Расширение с помощью пользовательских типов

### 4.1 Регистрация пользовательских типов

Адаптер может зарегистрировать пользовательские типы сессий:

```python
from ErisPulse.Core.Event import register_custom_type

# Регистрация пользовательского типа
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 Использование пользовательских типов

После регистрации система автоматически обрабатывает преобразование и вывод типа:

```python
# Автоматический вывод
receive_type = infer_receive_type(event, platform="MyPlatform")
# Возвращает: "my_custom_type"

# Преобразование в тип отправки
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# Возвращает: "custom"

# Получение соответствующего ID
target_id = get_target_id(event, platform="MyPlatform")
# Возвращает: event["custom_id"]
```

### 4.3 Удаление пользовательских типов

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. Автоматическое определение типа

Если у события отсутствует явное поле `detail_type`, система автоматически определяет тип по доступным полям ID:

> [!NOTE]
> **Изменение поведения в 2.7.0+**: `detail_type` используется только если это **известный тип сессии** (стандартный или пользовательский). У событий `notice`/`request` (например, `group_member_increase`, `friend_increase`) `detail_type` является **семантическим подтипом**, а не типом сессии, и система будет определять правильный тип сессии по полям ID.

### 5.1 Приоритет определения

```
Приоритет (от высокого к низкому):
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 Примеры использования

```python
# У события только group_id
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# Возвращает: "group" (используется приоритетный group_id)

# У события только user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# Возвращает: "private"

# У события notice detail_type — семантический подтип, в 2.7.0+ определяется по полю ID
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# Возвращает: "group" (а не "group_member_increase")
```

## 6. Примеры использования API

### 6.1 Отправка сообщений

```python
from ErisPulse import adapter

# Отправка пользователю
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# Отправка в группу
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# Автоматическое преобразование private → user: использование приемлемого, но не рекомендуемого способа (может быть несовместимость)
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# Внутри автоматически преобразуется в: Send.To("user", "789")
# Рекомендуемый способ: при ручной отправке используйте тип отправки user, или используйте event.reply() для автоматического преобразования (см. 6.2)
```

### 6.2 Ответ на событие

```python
from ErisPulse.Core.Event import Event

# Event.reply() автоматически обрабатывает преобразование типов (рекомендуемый путь)
await event.reply("Сообщение ответа")
# Внутри автоматически используется правильный тип отправки (автоматическое преобразование private → user происходит здесь)
```

### 6.3 Обработка команд

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # Система автоматически обрабатывает тип сессии
    # Не нужно вручную проверять group_id или user_id
    await event.reply("Команда выполнена успешно")
```

## 7. Справочник основных API

### 7.1 Преобразование типов

```python
from ErisPulse.Core.Event import convert_to_send_type, convert_to_receive_type

# Преобразование типа получения в тип отправки
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# Преобразование типа отправки в тип получения
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### 7.2 Получение полей ID

```python
from ErisPulse.Core.Event import get_id_field, get_receive_type

get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 7.3 Получение информации для отправки за один вызов

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# Непосредственно для использования в Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 Получение целевого ID

```python
from ErisPulse.Core.Event import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 8. Вспомогательные методы

```python
from ErisPulse.Core.Event import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

is_standard_type("private")     # True
is_standard_type("custom_type") # False

is_valid_send_type("user")      # True
is_valid_send_type("invalid")   # False

get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

clear_custom_types()                # Очистка всех пользовательских типов
clear_custom_types(platform="discord")  # Очистка пользовательских типов только для указанной платформы
```

## 9. Рекомендуемые практики

### 7.1 Разработчики адаптеров

1. **Используйте стандартные сопоставления**: по возможности сопоставляйте с типами стандарта, а не создавайте новые типы
2. **Правильно преобразуйте**: убедитесь, что сопоставление типов получения и отправки корректно
3. **Сохраняйте исходные данные**: сохраняйте оригинальный тип события в `{platform}_raw`
4. **Документируйте**: в документации адаптера укажите сопоставления типов

### 7.2 Разработчики модулей

1. **Используйте вспомогательные методы**: используйте методы, такие как `get_send_type_and_target_id()`
2. **Избегайте жесткого кодирования**: не пишите код вида `if group_id else "private"`
3. **Учитывайте все типы**: код должен поддерживать все стандартные типы, а не только private/group
4. **Гибко проектируйте**: используйте методы обертки событий, а не прямой доступ к полям

### 7.3 Определение типов

- **Предпочитайте detail_type**: если есть явное поле, не используйте определение
- **Рационально используйте определение**: только когда нет явного типа
- **Учитывайте приоритеты**: знайте приоритеты определения, чтобы избежать неожиданных результатов

## 10. Часто задаваемые вопросы

### В1: Почему при отправке private нужно преобразовывать в user?

О: Это требование стандарта OneBot12. `private` — это понятие получения, при отправке лучше использовать `user`, что соответствует семантике.

### В2: Как поддержать новые типы сессий?

О: Зарегистрируйте пользовательский тип с помощью `register_custom_type()`, или используйте стандартные типы, такие как `channel`, `guild`.

### В3: Что делать, если у события нет detail_type?

О: Система автоматически определит тип по доступным полям ID. Приоритет: group > channel > guild > thread > user.

### В4: Как адаптер должен сопоставлять Telegram supergroup?

О: В логике преобразования адаптера сопоставьте `supergroup` со стандартным типом `group`.

### В5: Как обрабатывать специальные платформы, такие как почта?

О: Для неуниверсальных или платформенных специфических типов используйте `{platform}_raw` и `{platform}_raw_type` для сохранения исходных данных, адаптер должен обрабатывать их самостоятельно.

## 11. Связанные документы

**Со стороны адаптера (сопоставление и преобразование)**:
- [Стандарт преобразования событий](event-conversion.md) - полное описание стандарта преобразования событий
- [Спецификация методов отправки](send-method-spec.md) - спецификация методов и параметров класса Send
- [Руководство по разработке адаптеров](../developer-guide/adapters/) - полное руководство по разработке адаптеров

**Со стороны модуля (если не хотите вручную управлять преобразованием типов)**:
- Используйте `event.reply()`, чтобы автоматически выполнить преобразование типов и вывод цели, подробнее см. [Документация по Event Wrapper](../developer-guide/modules/event-wrapper.md)