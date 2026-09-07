# ErisPulse-Dashboard

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) — это **веб-панель управления**, поддерживаемая напрямую ErisDev, которая предоставляет визуальный интерфейс для управления ErisPulse в режиме выполнения: запуск и остановка модулей, редактирование конфигурации, просмотр логов, мониторинг событий и т.д.

> [!IMPORTANT]
> Dashboard **не является** встроенной функцией ErisPulse, его необходимо устанавливать отдельно:
>
> ```bash
> epsdk install Dashboard
> ```

Dashboard также поддерживает регистрацию пользовательских страниц управления другими модулями ErisPulse в боковом меню. После регистрации пользователь может переключаться на специальные окна модуля прямо в Dashboard, без необходимости разработки отдельного пользовательского интерфейса.

> [!NOTE]
> Регистрация окон является **необязательной функцией**.
>
> - Если модуль Dashboard **не установлен** или **не загружен**, вызов `sdk.Dashboard.register_view()` приведет к исключению
> - Обязательно используйте `try/except` для обработки кода регистрации, чтобы другие функции модуля не были затронуты
> - Рекомендуется проверять доступность Dashboard перед регистрацией: `hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## Принцип работы

```
Модуль on_load()
  → Вызов sdk.Dashboard.register_view(...)
  → Dashboard сохраняет информацию о окне на бэкенде
  → WebSocket уведомляет фронтенд
  → Фронтенд динамически создает элемент навигации в боковом меню + контейнер страницы
  → Пользователь может переключиться на окно модуля, нажав на элемент
```

---

## API регистрации

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # Обязательный параметр, уникальный идентификатор
    title="Мой модуль",               # Название на китайском
    title_en="My Module",             # Название на английском
    icon_svg='<svg>...</svg>',        # SVG-иконка для бокового меню
    html_content='<div>...</div>',    # HTML-контент страницы (режим встраивания)
    js_content='function xxx() {}',   # JavaScript-логика страницы
    css_content='.my-style {}',        # Необязательный пользовательский CSS
    iframe_url='',                    # URL для режима iframe (выбирается один из html_content или iframe_url)
    loader="loadMyModuleView",        # Имя JS-функции, вызываемой при переключении на эту страницу
    group="group_extensions",         # Идентификатор группы бокового меню
    group_title="",                   # Название группы на китайском (необязательно)
    group_title_en="",                # Название группы на английском (необязательно)
)
```

### Описание параметров

| Параметр | Тип | Обязательный | Описание |
|------|------|------|------|
| `id` | `str` | Да | Уникальный идентификатор окна, рекомендуется использовать название модуля |
| `title` | `str` | Нет | Название для отображения на китайском, по умолчанию используется `id` |
| `title_en` | `str` | Нет | Название для отображения на английском, по умолчанию используется `title` |
| `icon_svg` | `str` | Нет | Полный SVG-код иконки для бокового меню |
| `html_content` | `str` | Нет* | HTML-контент страницы (режим встраивания) |
| `js_content` | `str` | Нет | JavaScript-код страницы |
| `css_content` | `str` | Нет | Пользовательский CSS-стиль страницы |
| `iframe_url` | `str` | Нет* | URL для режима iframe (если задан, html_content игнорируется) |
| `loader` | `str` | Нет | Имя JS-функции, вызываемой при активации страницы |
| `group` | `str` | Нет | Идентификатор группы бокового меню, по умолчанию `group_extensions` |
| `group_title` | `str` | Нет | Название группы на китайском (необязательно) |
| `group_title_en` | `str` | Нет | Название группы на английском (необязательно) |

> *Должен быть предоставлен хотя бы один из параметров `html_content` или `iframe_url`, иначе страница будет пустой.

---

## Два режима встраивания

### Режим 1: Встраивание HTML/JS (рекомендуется)

Непосредственно предоставьте строки HTML, JS и CSS, Dashboard вставит их в страницу. Этот режим полностью соответствует стилям Dashboard, рекомендуется использовать классы CSS, предоставленные Dashboard.

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="Приветствие", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">Это пример страницы</div></div>',
    group="group_tools",
)
```

> Полный пример модуля погоды (включая API-маршруты, взаимодействие JS и т.д.) см. ниже [Полный пример модуля](#полный-пример-модуля).

### Режим 2: Встраивание iframe

Модуль предоставляет собственный URL HTML-страницы (необходимо зарегистрировать маршрут), Dashboard встраивает его в iframe. Подходит для случаев, когда требуется полностью независимый UI или сложные взаимодействия.

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

## Группы бокового меню

Модуль может указать группу, в которую будет добавлено окно. Dashboard содержит следующие встроенные группы:

| Идентификатор группы | Название на китайском | Позиция |
|---------|--------|------|
| `group_overview` | Обзор | 1-я группа |
| `group_events` | События | 2-я группа |
| `group_extensions` | Расширения | 3-я группа (по умолчанию) |
| `group_system` | Система | 4-я группа |
| `group_tools` | Инструменты | 5-я группа |

Использование встроенных названий групп добавит окно в конец соответствующей группы:

```python
group="group_tools"  # Добавление в группу "Инструменты"
```

Также можно использовать пользовательские группы (не начинающиеся с `group_`), Dashboard создаст новую группу:

```python
group="my_group",
group_title="Моя группа",
group_title_en="My Group",
```

---

## Общие CSS-классы

При использовании режима встраивания HTML модуль может использовать уже существующие CSS-классы Dashboard для обеспечения визуальной согласованности:

| Класс | Назначение |
|------|------|
| `page-title` | Заголовок страницы, например `<h1 class="page-title">Заголовок</h1>` |
| `card` | Контейнер карточки |
| `card-header` | Заголовок карточки |
| `card-body` | Тело карточки |
| `grid-2` | Двухколоночное сеточное расположение |
| `grid-3` | Трехколоночное сеточное расположение |
| `btn` | Базовая кнопка |
| `btn-primary` | Основная кнопка (синяя) |
| `btn-secondary` | Второстепенная кнопка |
| `btn-icon` | Кнопка с иконкой |
| `btn-danger` | Кнопка опасного действия |

Dashboard использует CSS-переменные для управления темой, которые можно использовать в модуле:

| CSS-переменная | Назначение |
|----------|------|
| `var(--bg-p)` | Основной цвет фона |
| `var(--bg-s)` | Вторичный цвет фона |
| `var(--bg-t)` | Третичный цвет фона (карточки и т.д.) |
| `var(--tx-p)` | Основной цвет текста |
| `var(--tx-s)` | Вторичный цвет текста |
| `var(--tx-t)` | Вспомогательный цвет текста |
| `var(--bd)` | Цвет границ |
| `var(--accent)` | Подчеркивающий цвет |
| `var(--ok-c)` | Цвет успеха |
| `var(--er-c)` | Цвет ошибки |

Эти переменные автоматически переключаются в зависимости от темы Dashboard (светлая/темная), модулю не нужно их дополнительно обрабатывать.

---

## Аутентификация и вызов API

При вызове API модуля из JavaScript в окне Dashboard необходимо передавать токен Dashboard для аутентификации:

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

Модуль может самостоятельно решить, проверять ли токен. При необходимости проверки можно извлечь его из заголовка:

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## Полный пример модуля

Ниже приведен полный пример модуля погоды, демонстрирующий регистрацию окна, предоставление данных API, а также очистку ресурсов при выгрузке:

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
                    <h1 class="page-title">Погода</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">Просмотр текущей информации о погоде</p>
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
            self.logger.warning(f"Ошибка регистрации окна Dashboard: {e}")
```

---

## Удаление окна

При выгрузке модуля следует вызвать `unregister_view()` для очистки зарегистрированного окна:

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

После удаления окно будет удалено из бокового меню и контента фронтенда Dashboard через WebSocket в реальном времени, без необходимости обновления страницы.

---

## Примечания

1. **Порядок загрузки** — Приоритет загрузки Dashboard установлен на `99999` (высокий приоритет), приоритет вашего модуля должен быть ниже этого значения (например, `50`), чтобы убедиться, что Dashboard загружен первым
2. **Защитное программирование** — Используйте `try/except` при регистрации окна, так как модуль Dashboard может быть не установлен или не загружен
3. **Очистка ресурсов** — В `on_unload` вызывайте `unregister_view()`, чтобы удалить зарегистрированное окно
4. **Уникальность ID** — Параметр `id` должен быть уникальным во всем Dashboard, рекомендуется использовать имя модуля
5. **SVG-иконка** — `icon_svg` должен быть полным тегом `<svg>`, рекомендуется использовать размер `viewBox="0 0 24 24"`, и использовать `stroke="currentColor"`, чтобы унаследовать тему Dashboard
6. **Имя функции JS** — Имя функции в `js_content` должно быть уникальным (например, `loadWeatherView`), чтобы избежать конфликта с другими модулями
7. **Динамическое обновление** — После регистрации или удаления окна Dashboard обновит боковое меню в реальном времени через WebSocket, без необходимости обновления страницы