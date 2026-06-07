# Регистрация представлений Dashboard

Dashboard поддерживает, чтобы другие модули ErisPulse регистрировали пользовательские страницы управления в боковой панели Dashboard. После регистрации пользователи могут напрямую переключаться на страницу, эксклюзивную для этого модуля в Dashboard, без необходимости разработки отдельного интерфейса для frontend.

> **Предварительные требования**
>
> Регистрация представлений Dashboard — это **необязательная функция**, требующая установки и загрузки модуля [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/).
>
> *   Если модуль Dashboard **не установлен** или **не загружен**, вызов `sdk.Dashboard.register_view()` вызовет исключение
> *   Обязательно оберните код регистрации в конструкцию `try/except`, чтобы убедиться, что другие функции самого модуля не затронуты
> *   Рекомендуется проверить доступность Dashboard перед регистрацией: `hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## Принцип работы

```
Модуль on_load()
  → Вызов sdk.Dashboard.register_view(...)
  → Backend Dashboard сохраняет информацию о представлении
  → WebSocket уведомляет frontend
  → Frontend динамически создает пункт навигации в боковой панели + контейнер страницы
  → Пользователь нажимает для просмотра модульного представления
```

---

## API регистрации

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # Обязательно, уникальный идентификатор
    title="Мой модуль",                # Название на китайском
    title_en="My Module",             # Название на английском
    icon_svg='<svg>...</svg>',        # SVG-иконка боковой панели
    html_content='<div>...</div>',     # HTML-содержимое страницы
    js_content='function xxx() {}',    # Логика JavaScript страницы
    css_content='.my-style {}',        # Пользовательский CSS (опционально)
    iframe_url='',                     # URL в режиме iframe (выберите одно из html_content или iframe_url)
    loader="loadMyModuleView",         # Имя JS-функции, вызываемой при переключении на эту страницу
    group="group_extensions",          # Группа в боковой панели
    group_title="",                    # Китайское название пользовательской группы
    group_title_en="",                 # Английское название пользовательской группы
)
```

### Описание параметров

| Параметр | Тип | Обязательно | Описание |
|------|------|------|------|
| `id` | `str` | Да | Уникальный идентификатор представления, рекомендуется использовать название модуля |
| `title` | `str` | Нет | Название на китайском языке, по умолчанию используется `id` |
| `title_en` | `str` | Нет | Название на английском языке, по умолчанию используется `title` |
| `icon_svg` | `str` | Нет | Полный SVG-строка иконки боковой панели |
| `html_content` | `str` | Нет* | Содержимое HTML страницы в режиме инъекции |
| `js_content` | `str` | Нет | Код JavaScript страницы |
| `css_content` | `str` | Нет | Пользовательские CSS-стили страницы |
| `iframe_url` | `str` | Нет* | URL в режиме iframe, при установке параметра `html_content` будет проигнорирован |
| `loader` | `str` | Нет | Имя JS-функции, автоматически вызываемой при активации страницы |
| `group` | `str` | Нет | Идентификатор группы в боковой панели, по умолчанию `group_extensions` |
| `group_title` | `str` | Нет | Китайское название пользовательской группы |
| `group_title_en` | `str` | Нет | Английское название пользовательской группы |

> *`html_content` и `iframe_url` должны быть указаны хотя бы один, иначе страница будет пустой.

---

## Два режима инъекции

### Режим 1: HTML/JS инъекция (рекомендуется)

Прямое предоставление строк HTML, JS и CSS; Dashboard вставит содержимое в страницу. Этот режим полностью соответствует стилю Dashboard; рекомендуется использовать предоставленные Dashboard CSS-имена классов.

```python
sdk.Dashboard.register_view(
    id="Weather",
    title="Погода", title_en="Weather",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
    html_content='''
        <h1 class="page-title">Запрос погоды</h1>
        <div class="grid-2">
            <div class="card">
                <div class="card-header">Текущая погода</div>
                <div class="card-body">
                    <div id="weather-info">Загрузка...</div>
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
        async function loadWeatherView() {
            await refreshWeather();
        }
        async function refreshWeather() {
            var el = document.getElementById('weather-info');
            if (!el) return;
            try {
                var token = localStorage.getItem('__ep_tk__');
                var resp = await fetch('/Weather/api/current', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                var data = await resp.json();
                el.innerHTML = '<p>Температура: ' + (data.temp || '--') + '°C</p>' +
                               '<p>Влажность: ' + (data.humidity || '--') + '%</p>';
            } catch (e) {
                el.textContent = 'Ошибка загрузки: ' + e.message;
            }
        }
    ''',
    loader="loadWeatherView",
    group="group_tools",
)
```

### Режим 2: Встраивание iframe

Модуль предоставляет собственный URL страницы HTML (требуется самостоятельная регистрация маршрута), а Dashboard встраивает его в iframe. Подходит для сценариев, требующих полностью независимого UI или сложного взаимодействия.

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="Визуализация данных", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> Режим iframe автоматически добавляет параметр `token` в конец URL для аутентификации.

---

## Группы боковой панели

Модули могут указать, в какую группу боковой панели помещается их представление. Dashboard поддерживает следующие встроенные группы:

| Идентификатор группы | Название (кит.) | Позиция |
|---------|--------|------|
| `group_overview` | Обзор | 1-я группа |
| `group_events` | События | 2-я группа |
| `group_extensions` | Расширения | 3-я группа (по умолчанию) |
| `group_system` | Система | 4-я группа |
| `group_tools` | Инструменты | 5-я группа |

При указании встроенного имени группы (`group_...`) представление модуля будет добавлено в конец этой группы:

```python
group="group_tools"  # Добавить в группу "Инструменты"
```

Также можно использовать пользовательское имя группы (не начинающееся с `group_`); Dashboard автоматически создаст новую группу:

```python
group="my_group",
group_title="Моя группа",
group_title_en="My Group",
```

---

## Часто используемые имена CSS-классов

При использовании режима инъекции HTML модуль может напрямую использовать существующие CSS-имена классов Dashboard для сохранения визуального согласования:

| Имя класса | Назначение |
|------|------|
| `page-title` | Название страницы, например `<h1 class="page-title">Заголовок</h1>` |
| `card` | Контейнер карточки |
| `card-header` | Заголовок карточки |
| `card-body` | Область содержимого карточки |
| `grid-2` | Сетка с двумя колонками |
| `grid-3` | Сетка с тремя колонками |
| `btn` | Базовая кнопка |
| `btn-primary` | Основная кнопка (синяя) |
| `btn-secondary` | Второстепенная кнопка |
| `btn-icon` | Кнопка с иконкой |
| `btn-danger` | Кнопка опасного действия |

Dashboard использует CSS-переменные для управления цветовыми схемами тем; вы можете напрямую ссылаться на них в представлении модуля:

| CSS переменная | Назначение |
|----------|------|
| `var(--bg-p)` | Основной цвет фона |
| `var(--bg-s)` | Вторичный цвет фона |
| `var(--bg-t)` | Третичный цвет фона (карточки и т.д.) |
| `var(--tx-p)` | Основной цвет текста |
| `var(--tx-s)` | Вторичный цвет текста |
| `var(--tx-t)` | Дополнительный цвет текста |
| `var(--bd)` | Цвет границы |
| `var(--accent)` | Цвет акцента |
| `var(--ok-c)` | Цвет успеха |
| `var(--er-c)` | Цвет ошибки |

Эти переменные автоматически переключаются в зависимости от светлой/темной темы Dashboard, дополнительных действий от модуля не требуется.

---

## Аутентификация и вызовы API

При вызове собственного API модуля из JS в представлении модуля необходимо передать токен Dashboard для аутентификации:

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

Конечные точки API модуля могут самостоятельно решать, требуется ли проверка токена. Если проверка необходима, токен можно извлечь из заголовков запроса:

```python
from fastapi.responses import JSONResponse

async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return JSONResponse({"data": "hello"})
```

---

## Полный пример модуля

Ниже приведен полный пример модуля погоды, демонстрирующий, как регистрировать представление, предоставлять API-данные и очищать ресурсы при卸ождении:

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
        self.logger.info("Модуль погоды отключен")

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
        from fastapi.responses import JSONResponse
        return JSONResponse({
            "city": self.config.get("city", "Пекин"),
            "temp": 25,
            "humidity": 60,
        })

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="Погода", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">Запрос погоды</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">Просмотр текущей информации о погоде</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">Текущая погода</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">Нажмите обновить для загрузки</div>
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
                            el.textContent = 'Ошибка загрузки: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"Не удалось зарегистрировать представление Dashboard: {e}")
```

---

## Отмена регистрации (Unregister View)

При отключении модуля следует вызвать `unregister_view()` для очистки зарегистрированного представления:

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

После отмены регистрации интерфейс Dashboard удалит пункты навигации в боковой панели и содержимое страницы через WebSocket в реальном времени; перезагрузка страницы пользователем не требуется.

---

## Важные замечания

1. **Порядок загрузки** — Приоритет загрузки Dashboard равен `99999` (высокий приоритет); приоритет вашего модуля должен быть ниже этого значения (например, `50`), чтобы убедиться, что Dashboard загружен первым
2. **Защитное программирование** — При регистрации представления оберните вызов в `try/except`, так как модуль Dashboard может быть не установлен или не загружен
3. **Очистка ресурсов** — Вызывайте `unregister_view()` в `on_unload` для удаления зарегистрированного представления
4. **Уникальность ID** — Параметр `id` должен быть уникальным во всем Dashboard; рекомендуется использовать название модуля
5. **SVG иконки** — `icon_svg` должен быть полным тегом `<svg>`; рекомендуется использовать `viewBox="0 0 24 24"` и `stroke="currentColor"` для наследования цветовой схемы Dashboard
6. **Именование JS-функций** — Имена функций в `js_content` должны быть уникальными (например, `loadWeatherView`), чтобы избежать конфликтов с другими модулями
7. **Динамическое обновление** — После регистрации/отмены регистрации представления интерфейс Dashboard будет обновлять боковую панель в реальном времени через WebSocket; перезагрузка страницы не требуется