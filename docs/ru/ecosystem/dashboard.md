# ErisPulse-Dashboard

> [!TIP]
> **Когда это нужно читать:** Когда вы хотите использовать веб-интерфейс для визуального управления роботом (включение/выключение модулей, редактирование конфигурации, просмотр логов, мониторинг потоков событий), или хотите зарегистрировать страницу управления для своего модуля. Если не нужно — пропустите.

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) — это **веб-панель управления**, поддерживаемая ErisDev, которая предоставляет визуальный интерфейс для управления ErisPulse в режиме выполнения: включение/выключение модулей, редактирование конфигурации, просмотр логов, мониторинг потоков событий и т.д.

> [!IMPORTANT]
> Dashboard **не является** встроенной функцией фреймворка ErisPulse, его нужно устанавливать отдельно:
>
> ```bash
> epsdk install Dashboard
> ```

Dashboard также поддерживает регистрацию пользовательских страниц управления другими модулями ErisPulse в боковой панели. После регистрации пользователь может напрямую переключиться на специальную визуальную страницу модуля в Dashboard, без необходимости дополнительного разработки отдельного пользовательского интерфейса.

> [!NOTE]
> Регистрация визуальных окон — это **необязательная функция**.
>
> - Если модуль Dashboard **не установлен** или **не загружен**, вызов `sdk.Dashboard.register_view()` вызовет исключение
> - Обязательно используйте `try/except` для обертывания кода регистрации, чтобы убедиться, что другие функции модуля не будут затронуты
> - Рекомендуется проверять доступность Dashboard перед регистрацией: `hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## Принцип работы

```
Модуль on_load()
  → вызов sdk.Dashboard.register_view(...)
  → Dashboard сохраняет информацию о визуальном окне
  → WebSocket уведомляет клиент
  → Клиент динамически создает элемент навигации в боковой панели + контейнер страницы
  → Пользователь может переключиться на страницу модуля
```

---

## API регистрации

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # Обязательный, уникальный идентификатор
    title="Мой модуль",                  # Название на китайском
    title_en="My Module",             # Название на английском
    icon_svg='<svg>...</svg>',        # SVG-иконка для боковой панели
    html_content='<div>...</div>',     # HTML-контент страницы
    js_content='function xxx() {}',    # JavaScript-логика страницы
    css_content='.my-style {}',        # Необязательный пользовательский CSS
    iframe_url='',                     # URL для режима iframe (один из двух: html_content или iframe_url)
    loader="loadMyModuleView",         # Имя функции JavaScript, вызываемой при переключении на страницу
    group="group_extensions",          # Группа в боковой панели
    group_title="",                    # Название группы на китайском
    group_title_en="",                 # Название группы на английском
)
```

### Описание параметров

| Параметр | Тип | Обязательно | Описание |
|------|------|------|------|
| `id` | `str` | Да | Уникальный идентификатор визуального окна, рекомендуется использовать название модуля |
| `title` | `str` | Нет | Название для отображения на китайском, по умолчанию используется `id` |
| `title_en` | `str` | Нет | Название для отображения на английском, по умолчанию используется `title` |
| `icon_svg` | `str` | Нет | Полная строка SVG-иконки для боковой панели |
| `html_content` | `str` | Нет* | HTML-контент страницы в режиме встраивания |
| `js_content` | `str` | Нет | JavaScript-код страницы |
| `css_content` | `str` | Нет | Пользовательский CSS-стиль страницы |
| `iframe_url` | `str` | Нет* | URL для режима iframe, при указании игнорируется `html_content` |
| `loader` | `str` | Нет | Имя функции JavaScript, вызываемой при активации страницы |
| `group` | `str` | Нет | Идентификатор группы в боковой панели, по умолчанию `group_extensions` |
| `group_title` | `str` | Нет | Название группы на китайском |
| `group_title_en` | `str` | Нет | Название группы на английском |

> *Обязательно указывать либо `html_content`, либо `iframe_url`, иначе страница будет пустой.

---

## Два режима встраивания

### Режим 1: HTML/JS встраивание (рекомендуется)

Предоставляйте HTML, JS и CSS напрямую, Dashboard вставит содержимое на страницу. Этот режим полностью соответствует стилям Dashboard, рекомендуется использовать CSS-классы, предоставляемые Dashboard.

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="Привет страница", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">Это пример страницы</div></div>',
    group="group_tools",
)
```

> Полный пример модуля погоды (с API-маршрутами, JS-взаимодействием и т.д.) см. ниже [Полный пример модуля](#полный-пример-модуля).

### Режим 2: Встраивание с помощью iframe

Модуль предоставляет URL своей HTML-страницы (необходимо зарегистрировать маршрут), Dashboard встраивает её в iframe. Подходит для сценариев с полностью независимым UI или сложным взаимодействием.

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="Визуализация данных", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> В режиме iframe автоматически добавляется параметр `token` в URL для аутентификации.

---

## Группировка в боковой панели

Модуль может указать группу, в которой будет отображаться визуальное окно. Dashboard предоставляет следующие встроенные группы:

| Идентификатор группы | Название на китайском | Позиция |
|---------|--------|------|
| `group_overview` | Обзор | 1-я группа |
| `group_events` | События | 2-я группа |
| `group_extensions` | Расширения | 3-я группа (по умолчанию) |
| `group_system` | Система | 4-я группа |
| `group_tools` | Инструменты | 5-я группа |

Указав идентификатор встроенной группы, визуальное окно будет добавлено в конец этой группы:

```python
group="group_tools"  # Добавление в группу "Инструменты"
```

Также можно использовать пользовательские идентификаторы групп (не начинающиеся с `group_`), Dashboard автоматически создаст новую группу:

```python
group="my_group",
group_title="Моя группа",
group_title_en="My Group",
```

---

## Распространённые CSS-классы

При использовании режима встраивания HTML, можно напрямую использовать CSS-классы, предоставленные Dashboard, для обеспечения визуальной согласованности:

| Класс | Назначение |
|------|------|
| `page-title` | Заголовок страницы, например `<h1 class="page-title">Заголовок</h1>` |
| `card` | Контейнер карточки |
| `card-header` | Заголовок карточки |
| `card-body` | Тело карточки |
| `grid-2` | Двухколоночный макет сетки |
| `grid-3` | Трёхколоночный макет сетки |
| `btn` | Базовая кнопка |
| `btn-primary` | Основная кнопка (синяя) |
| `btn-secondary` | Второстепенная кнопка |
| `btn-icon` | Кнопка с иконкой |
| `btn-danger` | Кнопка опасного действия |

Dashboard использует CSS-переменные для управления темой, которые можно использовать в модуле:

| CSS-переменная | Назначение |
|----------|------|
| `var(--bg-p)` | Основной фон |
| `var(--bg-s)` | Вторичный фон |
| `var(--bg-t)` | Третичный фон (карточки и т.д.) |
| `var(--tx-p)` | Основной цвет текста |
| `var(--tx-s)` | Вторичный цвет текста |
| `var(--tx-t)` | Вспомогательный цвет текста |
| `var(--bd)` | Цвет границы |
| `var(--accent)` | Акцентный цвет |
| `var(--ok-c)` | Цвет успеха |
| `var(--er-c)` | Цвет ошибки |

Эти переменные автоматически переключаются между светлой и тёмной темами Dashboard, модулю не нужно дополнительно обрабатывать.

---

## Аутентификация и вызов API

При вызове API модуля из JavaScript визуального окна необходимо передавать токен Dashboard для аутентификации:

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

API-точки модуля могут самостоятельно решать, нужно ли проверять токен. Если нужно проверить, можно извлечь его из заголовка:

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## Полный пример модуля

Ниже приведён полный пример модуля погоды, демонстрирующий регистрацию визуального окна, предоставление данных API и очистку ресурсов при выгрузке:

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command


class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("Weather")
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(lazy_load=False, priority=50)

    async def on_load(self, event):
        self._register_routes()
        self._register_dashboard_view()
        self.logger.info("Модуль погоды загружен")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("Модуль погоды выгружен")

    def _load_config(self):
        config = self.sdk.config.getConfig("Weather")
        if not config:
            default = {"city": "Пекин", "api_key": ""}
            self.sdk.config.setConfig("Weather", default)
            return default
        return config

    def _register_routes(self):
        r = self.sdk.router
        r.register_http_route("Weather", "/api/current",
                              handler=self._api_current, methods=["GET"])

    def _unregister_routes(self):
        r = self.sdk.router
        try:
            r.unregister_http_route("Weather", "/api/current")
        except Exception:
            pass

    async def _api_current(self, request):
        return {
            "city": self.config.get("city", "Пекин"),
            "temp": 25,
            "humidity": 60,
        }

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="Погода", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">Погодный запрос</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">Просмотр текущей погоды</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">Текущая погода</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">Нажмите, чтобы обновить</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">Действия</div>
                            <div class="card-body">
                                <button class="btn btn-primary" onclick="refreshWeather()">Обновить</button>
                            </div>
                        </div>
                    </div>
                ''',
                js_content='''
                    async function loadWeatherView() { await refreshWeather(); }
                    async function refreshWeather() {
                        var el = document.getElementById('weather-info');
                        if (!el) return;
                        el.textContent = 'Загрузка...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>Город: ' + (data.city || '--') + '</p>' +
                                           '<p>Температура: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>Влажность: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = 'Загрузка не удалась: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"Регистрация визуального окна Dashboard не удалась: {e}")
```

---

## Удаление визуального окна

При выгрузке модуля следует вызвать `unregister_view()` для удаления зарегистрированного визуального окна:

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

После удаления Dashboard будет удалять элементы навигации и контент в реальном времени через WebSocket, без необходимости обновления страницы.

---

## Примечания

1. **Порядок загрузки** — Dashboard загружается с приоритетом `99999` (очень высокий приоритет), приоритет вашего модуля должен быть ниже, например `50`, чтобы убедиться, что Dashboard загружен первым
2. **Защитное программирование** — оберните код регистрации визуального окна в `try/except`, потому что модуль Dashboard может не быть установлен или загружен
3. **Очистка ресурсов** — в `on_unload` вызовите `unregister_view()`, чтобы удалить зарегистрированное визуальное окно
4. **Уникальность ID** — параметр `id` должен быть уникальным во всём Dashboard, рекомендуется использовать имя модуля
5. **SVG-иконки** — `icon_svg` должен быть полной строкой `<svg>`, рекомендуется использовать `viewBox="0 0 24 24"`, и использовать `stroke="currentColor"` для наследования темы Dashboard
6. **Имена функций JS** — имена функций в `js_content` должны быть уникальными (например, `loadWeatherView`), чтобы избежать конфликтов с другими модулями
7. **Динамическое обновление** — после регистрации/удаления визуального окна Dashboard будет обновлять боковую панель в реальном времени через WebSocket, без необходимости обновления страницы

---

## Дальнейшие шаги

- **Не хотите использовать компьютер, хотите управлять роботом с телефона**: [ErisPulse-App](app.md) (официальный мультиплатформенный клиент, использует ту же API, что и Dashboard, визуальные окна также доступны)
- **Нужно предоставить данные API для визуального окна**: [Менеджер маршрутов](../advanced/router.md) для регистрации HTTP-маршрутов, справочник методов см. в [API основных модулей - Router](../api-reference/core-modules.md)
- **Нужно смотреть в реальном времени логи / потоки событий**: [Подписка на логи (режим push)](../api-reference/core-modules.md) и [Управление жизненным циклом](../advanced/lifecycle.md)