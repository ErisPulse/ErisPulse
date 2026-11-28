# Документация по особенностям платформы WeCom (корпоративный WeChat)

WeComAdapter — это адаптер, построенный на основе API самостоятельно созданных приложений WeCom. Он принимает сообщения через callback, выполняет активную отправку через интерфейс сообщений приложения, а также предоставляет возможности работы с корпоративным справочником и карточками сообщений.

---

## Информация о документе

- Версия соответствующего модуля: 0.1.2
- Сопровождающий: ErisPulse
- Последнее обновление: 2026-11-10

## Основная информация

- Описание платформы: бот самостоятельно созданного приложения WeCom, подходит для внутренних корпоративных уведомлений, интеллектуальных вопросов и ответов, автоматизации офисных задач и других сценариев
- Название адаптера: WeComAdapter
- Зарегистрированное имя платформы: `wecom` (псевдоним `wxwork`)
- Поддержка нескольких аккаунтов: поддерживается одновременная настройка нескольких компаний (каждый аккаунт соответствует одному corpid + приложению)
- Способ подключения: приём через HTTP callback (URL приёма сообщений настраивается в панели администрирования WeCom) + активная отправка через API
- Способ аутентификации: получение access_token через corpid + secret (автоматическое обновление)
- Шифрование/дешифрование callback: Token + EncodingAESKey (официальный протокол шифрования WeCom)
- Сопоставление типов сессий: сообщения приложения → `private` (личные сообщения участникам), групповые чаты приложения → `group`
- Поддержка цепочек модификаторов: поддерживаются цепочечные методы, такие как `.Reply()`
- Совместимость с OneBot12: отправка поддерживает стандартные сегменты сообщений OneBot12

## Соответствие стандартам (0.1.2)

В этой версии завершено приведение адаптера в соответствие со стандартами: структура ответов и коды ошибок следуют [спецификации ответов API](../standards/api-response.md).

### Аккаунты и мультиаккаунтность

- `call_api` поддерживает два совместимых поля аккаунта: `account_id` (стандартное имя) / `_account_id` (старое имя); ApiDSL фреймворка (`Api.Using(...)`) адаптирует их автоматически
- **Для 6 методов Api корпоративного справочника, включая `get_user_info` (`get_user_info` / `get_department_list` / `get_department_users` / `get_user_by_mobile` / `userid_to_openid` / `openid_to_userid`), исправлен фолбэк `Using()`**: если аккаунт не указан, используется аккаунт, заданный через `Api.Using(...)`, вместо игнорирования
- `Send` читает `send_context` (фолбэк аккаунта события): при вызове `Send` из контекста события по умолчанию используется аккаунт-источник

### Стандартные поля

- **События сообщений дополнены верхнеуровневым `message_id`** (берётся MsgId WeCom, при отсутствии — резервный uuid)
- **Запросы вроде `get_user_info` возвращают стандартизированные поля**: `user_id` / `user_name` / `user_displayname`, исходные данные сохраняются в `wecom_raw`
- **`get_self_info` дополнен `user_displayname`** (`user_id` — это corpid, `user_name` / `user_displayname` — `wecom:{имя_аккаунта}`)
- Converter использует фреймворковый `BaseConverter` (общие поля id/time/platform/self/wecom_raw единообразно строятся через `build_base_event`)

### Спецификация кодов ошибок

| retcode | Значение | Описание |
|---------|------|------|
| 0 | Успех | — |
| 34100 | Ошибка платформы | WeCom вернул ошибку (errcode != 0); исходный ответ сохраняется в `wecom_raw` |
| 10003 | Ошибка параметров | Отсутствующие или недопустимые параметры |

## Описание конфигурации

```toml
# config.toml
[WeComAdapter.accounts.default]
corpid = "YOUR_CORP_ID"        # ID компании (обязательно, панель WeCom → Моя компания)
secret = "YOUR_APP_SECRET"     # Secret приложения (обязательно, страница деталей самостоятельно созданного приложения)
agentid = 1000002              # AgentId приложения (обязательно, страница деталей самостоятельно созданного приложения)
callback_enabled = true        # Включить приём через callback (по умолчанию true; при выключении доступна только активная отправка)
token = "YOUR_CALLBACK_TOKEN"  # Токен проверки callback (настройка приёма сообщений в панели WeCom)
encoding_aes_key = "YOUR_AES_KEY_43CHARS"  # Ключ шифрования/дешифрования callback (43 символа)
callback_path = "/wecom/{account}"         # Путь callback, поддерживает заполнитель {account}
enabled = true
```

**Описание параметров конфигурации (для каждого аккаунта):**

| Поле | Тип | Обязательно | Описание |
|------|------|------|------|
| `corpid` | string | Да | ID компании |
| `secret` | string | Да | Secret приложения |
| `agentid` | int | Рекомендуется | AgentID приложения |
| `callback_enabled` | bool | Нет | Переключатель приёма callback (по умолчанию включён) |
| `token` | string | Нет | Токен проверки callback |
| `encoding_aes_key` | string | Нет | Ключ шифрования/дешифрования callback (43 символа) |
| `callback_path` | string | Нет | Путь callback, поддерживает заполнитель `{account}` |
| `enabled` | bool | Нет | Включён ли (по умолчанию true) |

- `corpid` / `secret` / `agentid`: получаются на странице самостоятельно созданных приложений в [панели администрирования WeCom](https://work.weixin.qq.com) (первые два параметра обязательны)
- `callback_enabled`: переключатель приёма callback (по умолчанию включён). **При выключении адаптер пропускает регистрацию callback-маршрута, сохраняя только возможность активной отправки**; связанные с callback поля скрываются в панели
- `token` / `encoding_aes_key`: проверка и шифрование/дешифрование callback-сообщений, должны совпадать с настройкой «Приём сообщений» в панели WeCom
- `callback_path`: путь приёма callback (по умолчанию `/wecom/{имя_аккаунта}`), в панели WeCom необходимо настроить полный URL: `http(s)://ваш_адрес:порт/wecom/<имя_аккаунта>`

**Предварительные условия для приёма сообщений**: панель WeCom → самостоятельно созданное приложение → «Приём сообщений», включите приём через API, в поле URL укажите вышеуказанный полный callback-адрес, Token и EncodingAESKey должны совпадать с конфигурацией. **Внимание**: WeCom требует, чтобы callback URL был доступен из интернета (рекомендуется использовать обратный прокси).

**Окружение API**:
- Базовый адрес API: `https://qyapi.weixin.qq.com/cgi-bin`
- access_token автоматически получается и обновляется в кэше, ручное управление не требуется

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочечный синтаксис, например:

```python
from ErisPulse import sdk
wecom = sdk.adapter.get("wecom")

# Базовые сообщения (target_type: "user"=участник, "group"=групповой чат приложения)
await wecom.Send.To("user", "zhangsan").Text("Привет")
await wecom.Send.To("group", "group_chat_id").Markdown("**Жирное** уведомление")

# Медиа (локальный путь / bytes / URL; автоматическая загрузка временного материала перед отправкой)
await wecom.Send.To("user", "zhangsan").Image("banner.png")
await wecom.Send.To("user", "zhangsan").Voice("voice.amr")
await wecom.Send.To("user", "zhangsan").Video("demo.mp4")
await wecom.Send.To("user", "zhangsan").File("report.pdf")

# Графические сообщения и карточки
await wecom.Send.To("user", "zhangsan").News([
    {"title": "Заголовок", "description": "Аннотация", "url": "https://...", "picurl": "https://.../img.png"},
])  # Максимум 8 элементов

await wecom.Send.To("user", "zhangsan").TextCard(
    title="Напоминание об утверждении",
    description="У вас есть документ, ожидающий утверждения",
    url="https://oa.example.com/approval/1",
    btntxt="Обработать",
)

await wecom.Send.To("user", "zhangsan").TemplateCard(
    card_type="text_notice",  # Тип карточки WeCom, остальные параметры передаются напрямую в официальном JSON карточки
    source={"icon_url": "...", "desc": "OA"},
    main_title={"title": "Напоминание о встрече"},
)

# Пассивный ответ: event.reply() полученного сообщения отвечает напрямую пользователю-отправителю

# Отправка с указанием конкретного аккаунта при нескольких аккаунтах
await wecom.Send.To("user", "UserID", account_id="app2").Text("Отправлено через app2")
```

### Основные методы отправки

| Метод | Описание | Параметры |
|------|------|------|
| `.Text(text)` | Отправка простого текстового сообщения | `text: str` |
| `.Markdown(content)` | Отправка Markdown-сообщения (поддерживается сообщениями приложения) | `content: str` |

### Методы отправки медиа

Методы медиа поддерживают два типа входных данных: `bytes` (автоматическая загрузка с получением media_id) и `str` (уже загруженный media_id или путь/URL):

| Метод | Описание |
|------|------|
| `.Image(file, filename)` | Отправка изображения |
| `.Voice(file, filename)` | Отправка голосового сообщения (требуется формат AMR, ограничение WeCom) |
| `.Audio(file, filename)` | Псевдоним для Voice |
| `.Video(file, filename)` | Отправка видео |
| `.File(file, filename)` | Отправка файла |

### Методы карточек с форматированием

| Метод | Описание |
|------|------|
| `.News(articles)` | Отправка графического сообщения (максимум 8 элементов) |
| `.TextCard(title, description, url, btntxt)` | Отправка текстовой карточки |
| `.TextCardMiniProgram(**kwargs)` | Отправка карточки-уведомления мини-программы |
| `.TemplateCard(card_type, **kwargs)` | Отправка карточки-шаблона |

### Отправка сырых сообщений

- `.Raw_ob12(message: List[Dict])`: отправка сообщений в стандартном формате OneBot12

### Цепочечные методы-модификаторы

| Метод | Описание |
|------|------|
| `.At(user_id)` | Упоминание (@) указанного пользователя (реализовано базовым классом SendDSL фреймворка) |
| `.AtAll()` | Упоминание (@) всех участников (реализовано базовым классом SendDSL фреймворка) |
| `.Reply(message_id)` | Ответ на указанное сообщение (реализовано базовым классом SendDSL фреймворка) |

### Сопоставление целей отправки

| OB12 target_type | Поле цели WeCom | Интерфейс API |
|---|---|---|
| `user` / `private` | `touser` | `message/send` |
| `group` | `chatid` | `appchat/send` |

## Стандартные действия API

```python
info = await wecom.Api.get_self_info()          # Информация о приложении (corpid/agentid)
status = await wecom.Api.get_status()           # Статус работы
ver = await wecom.Api.get_version()             # Версия адаптера

# Корпоративный справочник (access_token подставляется автоматически; начиная с 0.1.2 работает фолбэк Using())
user = await wecom.Api.get_user_info("zhangsan")            # Детали участника (имя/отдел/должность/аватар)
depts = await wecom.Api.get_department_list(0)              # Список отделов (0=корневой отдел)
members = await wecom.Api.get_department_users(2)           # Список участников отдела
uid = await wecom.Api.get_user_by_mobile("13800000000")     # Поиск userid по номеру телефона
openid = await wecom.Api.userid_to_openid("zhangsan")       # userid → openid (красные конверты/внешние платежи)
userid = await wecom.Api.openid_to_userid("oXXXX")          # openid → userid

# Несколько аккаунтов: указание аккаунта компании
result = await wecom.Api.Using("corp2").get_user_info("lisi")

# Прямой вызов любого API WeCom (endpoint относительно cgi-bin, access_token подставляется автоматически)
result = await wecom.Api.call("message/send", touser="zhangsan", msgtype="text", agentid=1000002, text={"content": "hi"})
```

## Специфические типы событий

Перед использованием особенностей данной платформы требуется проверка `platform == "wecom"`. Преобразование событий WeCom следует стандарту OneBot12, при этом расширения платформы предоставляются через префикс `wecom_`.

### Сопоставление detail_type событий сообщений

Сообщения, полученные приложением WeCom, единообразно сопоставляются с `private` (личные сообщения):

| Сообщение WeCom | OneBot12 type / detail_type |
|---|---|
| `text` | `message` / `private` |
| `image` | `message` / `private` |
| `voice` | `message` / `private` |
| `video` / `shortvideo` | `message` / `private` |
| `location` | `message` / `private` |
| `link` | `message` / `private` |

### Специфические типы событий (notice)

| detail_type | Описание |
|---|---|
| `wecom_subscribe` | Подписка пользователя / вход в приложение (subscribe / enter_agent) |
| `wecom_unsubscribe` | Отписка пользователя |
| `wecom_location_report` | Отчёт о географическом местоположении |
| `wecom_menu_click` | Событие клика по пункту меню (click) |
| `wecom_menu_view` | Переход по ссылке в меню (view) |
| `wecom_scancode` | Событие сканирования QR-кода |
| `wecom_menu_photo` | Событие фотосъёмки / выбора из фотоальбома |

> Сообщаемые события (подписка, клики по меню и т. п.) преобразуются в события типов `request` / `notice`.

### Стандартные типы сегментов сообщений

Преобразованные сегменты сообщений используют стандартный формат OneBot12:

| Тип сегмента | Описание | Поле data |
|---|---|---|
| `text` | Простой текст | `text` |
| `image` | Изображение | `file` (PicUrl или MediaId), `url` |
| `audio` | Голосовое сообщение | `file` (MediaId) |
| `video` | Видео | `file` (MediaId), `thumbnail` |
| `location` | Местоположение | `latitude`, `longitude`, `title` |
| `file` | Файл/ссылка | `file`, `filename`, `url` |

### Расширенные сегменты сообщений платформы

Расширенные сегменты сообщений с префиксом `wecom_` (направление отправки):

| Тип сегмента | Описание | Поле data |
|---|---|---|
| `wecom_markdown` | Markdown-сообщение | `content` |
| `wecom_news` | Графическое сообщение | `articles` (list) |
| `wecom_textcard` | Текстовая карточка | `title`, `description`, `url`, `btntxt` |
| `wecom_miniprogram_notice` | Уведомление мини-программы | Нативные поля передаются напрямую |
| `wecom_template_card` | Карточка-шаблон | `card_type` + нативные поля |

### Примеры событий

#### Текстовое сообщение

```python
{
  "id": "1234567890123456",
  "time": 1348831860,
  "type": "message",
  "detail_type": "private",
  "platform": "wecom",
  "self": {"platform": "wecom", "user_id": "Corpid"},
  "message_id": "1234567890123456",
  "user_id": "UserID",
  "user_nickname": "UserID",
  "message": [{"type": "text", "data": {"text": "Содержимое сообщения"}}],
  "alt_message": "Содержимое сообщения",
  "wecom_raw": {"MsgType": "text", "Content": "Содержимое сообщения", "...": "..."},
  "wecom_raw_type": "text",
  "wecom_agentid": "1000002",
  "wecom_corpid": "Corpid",
  "wecom_msg_id": "1234567890123456"
}
```

> **Изменения в 0.1.2**: события сообщений дополнены верхнеуровневым `message_id` (берётся MsgId WeCom, при отсутствии — резервный uuid).

#### Событие клика по меню

```python
{
  "type": "notice",
  "detail_type": "wecom_menu_click",
  "platform": "wecom",
  "user_id": "UserID",
  "wecom_event_key": "menu_key_1",
  "wecom_raw_type": "event"
}
```

## Расширенные методы Event Mixin

Адаптер регистрирует следующие платформоспецифичные методы, доступные только при `platform == "wecom"`:

| Метод | Возвращаемый тип | Описание |
|------|----------|------|
| `get_user_id()` | `str` | Получение UserID отправителя |
| `get_msg_type()` | `str` | Получение типа сообщения WeCom (text/image/...) |
| `get_content()` | `str` | Получение текстового содержимого сообщения |
| `get_agentid()` | `str` | Получение AgentID приложения |
| `get_corpid()` | `str` | Получение Corpid компании |
| `get_msg_id()` | `str` | Получение MsgId сообщения |
| `get_raw_xml()` | `str` | Получение расшифрованного исходного XML |
| `get_raw()` | `dict` | Получение словаря разобранных исходных данных |
| `get_event_key()` | `str` | Получение EventKey события меню |
| `get_media_id()` | `str` | Получение MediaId медиасообщения |

### Пример использования

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "wecom":
        return

    msg_type = event.get_msg_type()
    user_id = event.get_user_id()
    content = event.get_content()

    if msg_type == "text":
        await event.reply(f"Получено: {content}")

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "wecom":
        return

    if event.get("detail_type") == "wecom_menu_click":
        key = event.get_event_key()
        await event.reply(f"Вы нажали пункт меню: {key}")
```

## Описание расширенных полей

- Все специфические поля имеют префикс `wecom_`
- Исходные данные сохраняются в поле `wecom_raw` (разобранный словарь)
- Расшифрованный исходный XML сохраняется в поле `wecom_raw_xml`
- Исходный тип события сохраняется в поле `wecom_raw_type`
- `wecom_corpid`: ID компании
- `wecom_agentid`: AgentID приложения
- `wecom_msg_id`: ID сообщения WeCom

## Аутентификация и шифрование

### Управление access_token

- access_token кэшируется отдельно для каждого аккаунта
- Срок действия 7200 секунд, автоматическое обновление за 5 минут до истечения
- При недействительности token (errcode 40014/42001) кэш автоматически очищается и выполняется повторная попытка

### Шифрование и дешифрование сообщений

- Алгоритм: AES-256-CBC (дополнение PKCS7)
- Ключ: `base64decode(EncodingAESKey + "=")` (32 байта)
- IV: первые 16 байт ключа
- Подпись: `sha1("".join(sorted([token, timestamp, nonce, encrypt])))`
- Зависимость: `cryptography`

## Важные замечания

1. **Callback URL должен быть доступен из интернета**: для локальной разработки можно использовать туннелирование внутренней сети; в продакшене рекомендуется обратный прокси Nginx на порт router ErisPulse
2. **Частота активной отправки**: ограничена интерфейсом сообщений приложения WeCom (дневной лимит на приложение зависит от масштаба компании); для массовых рассылок используйте `TaskCard`/`TemplateCard` в сочетании с тегами
3. **Действительность access_token**: адаптер обновляет его автоматически; при развертывании нескольких экземпляров с одним corpid+secret учитывайте официальное ограничение взаимного вытеснения token (рекомендуется выполнять отправку и приём одним экземпляром)
4. **Медиафайлы**: Voice требует формат AMR (ограничение WeCom); большие файлы отправляются через интерфейс временных материалов (адаптер обрабатывает это автоматически)