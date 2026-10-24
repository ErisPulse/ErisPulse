# ErisPulse-Takumi

> [!TIP]
> **Когда читать этот документ**: когда вам нужно отрендерить HTML / дерево узлов / Jinja-шаблон в изображение для отправки в чат-платформу (карточки статистики, таблицы лидеров, длинные статьи с текстом и графикой). Если это не требуется — пропустите.

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) — это **сторонний модуль рендеринга изображений**, поддерживаемый ccd2s и основанный на [takumi-py](https://github.com/BalconyJH/takumi-py), который позволяет боту рендерить HTML, деревья узлов, Jinja-шаблоны, SVG и анимации в изображения. Модуль **включает встроенные шрифты для китайского и английского языков** (Noto Sans SC / Roboto / Source Code Pro), дополнительная настройка не требуется.

> [!IMPORTANT]
> Takumi **не является** встроенной функцией фреймворка ErisPulse, требуется отдельная установка:
>
> ```bash
> epsdk install Takumi
> ```

Сценарии применения:

- Рендеринг данных/статистики в изображения-карточки
- Рендеринг Markdown / длинного текста в изображения со стабильной вёрсткой, чтобы обойти различия стилей платформ
- Генерация SVG / анимаций для динамических визуальных эффектов
- Смешанный китайско-английский текст и графика (встроенные шрифты работают из коробки)

---

## Установка и включение

```bash
epsdk install Takumi
```

После установки модуль загружается автоматически; убедитесь, что он включён в конфигурации:

```toml
[Takumi]
enabled = true
```

---

## Быстрый старт

После автоматической загрузки модуля получите его через менеджер модулей или используйте сокращение `sdk`:

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# Эквивалентная запись: takumi = sdk.Takumi
```

### Рендеринг HTML

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>Привет, ErisPulse</h1>
      <p>Отрендерено с помощью Takumi</p>
    </div>
    """,
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
      font-family: "Noto Sans SC";
    }
    """],
    width=800,
    height=None,   # Автоматическая высота по содержимому
    lang="zh-CN",
)
```

### Рендеринг дерева узлов

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "Китайский и English можно рендерить напрямую",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

`png` — это `bytes`, его можно отправить через `event.reply(png, method="Image")` (подробнее см. [Отправка результата рендеринга](#отправка-результата-рендеринга)).

---

## API рендеринга

`sdk.Takumi` проксирует все возможности низкоуровневого `takumi_py.Renderer`: все методы рендеринга, измерения, SVG, анимации и шаблонов можно вызывать непосредственно на `sdk.Takumi`. Для этих методов модуль при вызове **автоматически внедряет встроенный стек шрифтовых фолбэков** (`takumi.families`), так что вручную передавать `font_families` не требуется; при явной передаче настройки вызывающей стороны имеют приоритет.

### Обзор методов

| Категория | Метод | Возврат | Описание |
|------|------|------|------|
| Статический рендеринг | `render_html(html, ...)` | `bytes` | Рендеринг HTML-строки |
| | `render_node(node, ...)` | `bytes` | Рендеринг дерева узлов (dict) |
| | `render_template(name, ctx, ...)` | `bytes` | Рендеринг Jinja-шаблона |
| | `render_compiled(node, ...)` | `bytes` | Рендеринг предкомпилированного узла |
| Вывод SVG | `render_svg_html(html, ...)` | `str` | Вывод SVG (вход HTML) |
| | `render_svg_node(node, ...)` | `str` | Вывод SVG (вход — дерево узлов) |
| | `render_svg_template(name, ctx, ...)` | `str` | Вывод SVG (вход — шаблон) |
| | `render_svg_compiled(node, ...)` | `str` | Вывод SVG (вход — предкомпилированный) |
| Анимация | `render_animation(scenes, ...)` | `bytes` | Кодирование многокадровой анимации |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | Получение кадра последовательности в заданный момент времени |
| Измерение | `measure_node(node, ...)` | `dict` | Измерение раскладки дерева узлов |
| | `measure_html(html, ...)` | `dict` | Измерение раскладки HTML |
| | `measure_compiled(node, ...)` | `dict` | Измерение предкомпилированного узла |
| Компиляция | `compile_node(node)` | `CompiledNode` | Компиляция дерева узлов |
| | `compile_html(html, ...)` | `CompiledNode` | Компиляция HTML |
| Шрифты | `register_font(font)` | `list[str]` | Регистрация пользовательского шрифта, возвращает список family |
| | `register_fonts(fonts)` | `list[str]` | Пакетная регистрация |

> `CompiledNode` предоставляет метод `resource_urls()`, который позволяет заранее обнаружить HTTP(S)-ссылки на изображения, подлежащие загрузке, чтобы заблаговременно подготовить ресурсы.

### Общие параметры

Следующие параметры применимы к методам статического рендеринга и SVG (у методов анимации есть дополнительные параметры вроде `fps`, см. соответствующие примеры):

| Параметр | Тип | По умолчанию | Описание |
|------|------|--------|------|
| `stylesheets` | `list[str]` | `None` | Список CSS-строк уровня документа; инлайновые `style` по-прежнему разбираются вместе с HTML |
| `width` | `int \| None` | `1200` | Ширина области просмотра (в пикселях); при `None` определяется по раскладке |
| `height` | `int \| None` | `630` | Высота холста (в пикселях); при `None` автоматически увеличивается по содержимому (см. [Область просмотра и форматы вывода](#область-просмотра-и-форматы-вывода)) |
| `lang` | `str \| None` | `None` | Языковой тег BCP-47 (например `zh-CN`), влияет на шейпинг текста и перенос строк |
| `font_families` | `list[str]` | автоматически | Стек шрифтовых фолбэков; в удобные методы по умолчанию внедряются встроенные шрифты |
| `format` | `str` | `"png"` | Формат вывода (см. [Область просмотра и форматы вывода](#область-просмотра-и-форматы-вывода)) |
| `device_pixel_ratio` | `float` | `1.0` | Коэффициент пикселей устройства, управляет разрешением вывода |
| `time_ms` | `int` | `0` | Момент выборки анимации (в миллисекундах) |
| `dithering` | `str` | `"none"` | Алгоритм дизеринга: `none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | Качество кодирования с потерями |
| `lossless` | `bool \| None` | `None` | Выполнять ли кодирование без потерь |
| `images` | `list` | `None` | Ресурсы изображений для текущего рендеринга (`ImageResource` или кортеж `(src, bytes)`) |
| `keyframes` | `Mapping` | `None` | Структурированные ключевые кадры, без необходимости писать `@keyframes` |
| `options` | `RenderOptions` | — | Передача параметров агрегированно через `RenderOptions(...)`, поля совпадают с таблицей выше |

Полные определения полей см. в `takumi_py.RenderOptions`.

### Пример дерева узлов

```python
png = takumi.render_node(
    {
        "type": "container",
        "style": {"padding": "32px", "backgroundColor": "#111827"},
        "children": [
            {"type": "text", "text": "Заголовок", "style": {"fontSize": 32, "color": "white"}},
            {"type": "text", "text": "Основной текст", "style": {"fontSize": 18, "color": "#9ca3af"}},
        ],
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

### Пример Jinja-шаблона

```python
png = takumi.render_template(
    "card.html.jinja",
    {"title": "Takumi", "subtitle": "Jinja to image"},
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
    }
    """],
    width=800,
    height=None,
    lang="zh-CN",
)
```

> Через `filters={...}` можно внедрить пользовательские Jinja-фильтры, а через `environment=...` передать полноценный `jinja2.Environment`. Подробнее о каталоге шаблонов и настройке окружения см. в [документации takumi-py по шаблонам](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md).

### Пример вывода SVG

```python
svg = takumi.render_svg_html(
    '<div class="card">Hello</div>',
    stylesheets=[".card { width: 800px; color: black; }"],
    width=800,
    height=None,
)
```

### Пример анимации

```python
from takumi_py import AnimationScene

webp = takumi.render_animation(
    [
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "black"}},
            duration_ms=100,
        ),
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "white"}},
            duration_ms=100,
        ),
    ],
    width=64,
    height=64,
    fps=20,
    format="webp",
)
```

> Каждый кадр задаётся как `AnimationScene(node, duration_ms=...)`; `duration_ms` должно быть положительным числом.

---

## Область просмотра и форматы вывода

### Форматы вывода

| Сценарий | Значения `format` |
|------|---------------|
| Статическое изображение | `png` (по умолчанию) / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| Анимация | `webp` (по умолчанию) / `apng` / `gif` |

`format="raw"` возвращает поток байтов RGBA в построчном порядке (row-major), предназначенный для пользовательской обработки на уровне пикселей.

### О width и height

Роли `width` и `height` несимметричны:

- `width` — это **ширина области просмотра**, по ней выполняются перенос строк и рефлоу текста и раскладки. Её **следует зафиксировать** конкретным значением (например `800`), иначе холст растянется по естественной ширине содержимого, текст не будет переноситься, и размер станет неуправляемым.
- `height` — это **высота холста**, растущая вместе с содержимым. Значение `height` по умолчанию — `630`; при передаче `height=None` Takumi **автоматически подберёт высоту холста по содержимому** (auto viewport).

> [!TIP]
> **Рекомендуемая комбинация: фиксированный `width` + `height=None`.** Конкретное значение `height` передавайте только тогда, когда нужен холст фиксированного размера или эффект обрезки.

> [!NOTE]
> Технически и `width`, и `height` можно передать как `None`, чтобы значение выводилось из раскладки (например, когда узел сам объявляет размеры); если заданы оба, размер вывода будет однозначно определён.

---

## Шрифты

### Встроенные шрифты

| Шрифт | family | Категория |
|------|--------|------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif (italic) |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace (italic) |

Свойства модуля:

| Свойство | Описание |
|------|------|
| `takumi.fonts` | Список имён файлов встроенных шрифтов |
| `takumi.families` | Список зарегистрированных семейств шрифтов (family) |

### Автоматическое внедрение

Все методы рендеринга, измерения, SVG, анимации и шаблонов на `sdk.Takumi` автоматически внедряют `takumi.families` в качестве стека шрифтовых фолбэков. При прямом вызове `takumi.renderer` (нативный экземпляр) или независимого экземпляра, созданного через `create_renderer()`, потребуется вручную передавать `font_families=takumi.families`.

### Пользовательские шрифты

```python
from takumi_py import FontResource

families = takumi.renderer.register_font(
    FontResource(
        font_bytes,
        name="MyFont",
        weight=400,
        style="normal",
        generic_family="sans-serif",
    )
)
```

`register_font` возвращает список зарегистрированных имён family, которые можно передавать как `font_families` при последующем рендеринге.

---

## Экземпляры рендерера

### Нативный Renderer

`takumi.renderer` — это исходный экземпляр `takumi_py.Renderer`. При прямом вызове нужно вручную передавать `font_families`:

```python
png = takumi.renderer.render_html(
    "<div>Привет</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### Независимый Renderer

Если требуется изолировать кэш шрифтов / изображений / ресурсов (долгоживущие процессы, мультитенантные сценарии), можно создать независимый `Renderer`; встроенные шрифты будут зарегистрированы автоматически:

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>Независимый Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=None,
    lang="zh-CN",
)
```

`create_renderer()` принимает параметры конструктора `takumi_py.Renderer`:

| Параметр | Тип | По умолчанию | Описание |
|------|------|--------|------|
| `load_default_fonts` | `bool` | `False` | Загружать ли шрифты, поставляемые с takumi-py (встроенные шрифты загружаются всегда) |
| `fonts` | `list[FontResource]` | `None` | Дополнительные пользовательские шрифты для регистрации |
| `cache_max_bytes` | `int \| None` | `None` | Верхний предел кэша ресурсов (в байтах); `0` — отключить |
| `persistent_images` | `list` | `None` | Персистентные ресурсы изображений |

> Независимый экземпляр не проходит через прокси модуля, поэтому для сохранения единого стека фолбэков встроенных шрифтов необходимо явно передавать `font_families=takumi.families`. Если `font_families` передан явно, модуль соблюдает настройки вызывающей стороны и не внедряет стек фолбэков по умолчанию; `RenderOptions(font_families=...)` тоже действует.

---

## Отправка результата рендеринга

Изображение, полученное в результате рендеринга, представляет собой `bytes` и может быть отправлено напрямую в ответе на событие:

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# Способ 1: ответ методом Image
await event.reply(png, method="Image")

# Способ 2: ответ через сегмент сообщения OneBot12
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> Оборачивание изображений для разных платформ единообразно обрабатывается адаптерами. Подробнее см. [Подробное руководство по MessageBuilder](../advanced/message-builder.md) и [Спецификацию методов отправки](../standards/send-method-spec.md).

---

## Конфигурация

```toml
[Takumi]
enabled = true
```

---

## Полезные ссылки

- PyPI: <https://pypi.org/project/ErisPulse-Takumi/>
- Репозиторий: <https://github.com/ccd2s/ErisPulse-Takumi> (автор [@ccd2s](https://github.com/ccd2s))
- Базовый движок: <https://github.com/BalconyJH/takumi-py>
- Документация takumi-py: <https://github.com/BalconyJH/takumi-py/blob/main/docs/index.md>

---

## Следующие шаги

- **Отправить результат рендеринга**: способы ответа вроде `event.reply(png, method="Image")` см. в разделе [API системы событий — Методы ответа](../api-reference/event-system.md)
- **Составлять более сложные исходящие сообщения** (изображение + текст + @): [Конструктор сообщений](../advanced/message-builder.md)
- **Рендеринг + отправка по расписанию**: вместе с [ErisPulse-Cron](cron.md) для периодических карточек с данными