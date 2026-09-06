# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) — это **третья сторона модуль рендеринга изображений**, поддерживаемый ccd2s, основанный на [takumi-py](https://github.com/BalconyJH/takumi-py), который позволяет боту рендерить HTML, деревья узлов, шаблоны Jinja, SVG и анимации в изображения. Модуль **включает шрифты на китайском и английском языках** (Noto Sans SC / Roboto / Source Code Pro), не требуя дополнительной настройки.

> [!IMPORTANT]
> Takumi **не является** встроенной функцией фреймворка ErisPulse, его необходимо устанавливать отдельно:
>
> ```bash
> epsdk install Takumi
> ```

Применение:

- Рендеринг данных/статистики в карточечные изображения
- Рендеринг Markdown / длинного текста в стабильно отформатированные изображения, чтобы избежать различий в стилях платформы
- Создание SVG / анимаций для реализации динамических визуальных эффектов
- Смешанная текстово-графическая компоновка на китайском и английском языках (встроенные шрифты готовы к использованию)

---

## Установка и включение

```bash
epsdk install Takumi
```

После установки модуль автоматически загружается, и в конфигурации необходимо убедиться, что он включен:

```toml
[Takumi]
enabled = true
```

---

## Быстрый старт

После автоматической загрузки модуля, его можно получить через менеджер модулей или использовать сокращённый `sdk`:

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# Альтернативная запись: takumi = sdk.Takumi
```

### Рендеринг HTML

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>Привет, ErisPulse</h1>
      <p>Рендерится Takumi</p>
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
    height=None,   # Автоматически подгоняется под содержимое
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

`png` — это `bytes`, который можно отправить с помощью `event.reply(png, method="Image")` (см. [Отправка рендеринга](#отправка-рендеринга)).

---

## API рендеринга

`sdk.Takumi` делегирует все возможности底层 `takumi_py.Renderer`: все методы рендеринга, измерения, SVG, анимации и шаблонов можно вызывать непосредственно через `sdk.Takumi`. Модуль автоматически **вставляет встроенный стек шрифтов** (`takumi.families`) при вызове; если явно передать `font_families`, то будет использоваться настройка вызывающей стороны.

### Список методов

| Категория | Метод | Возвращает | Описание |
|------|------|------|------|
| Статический рендеринг | `render_html(html, ...)` | `bytes` | Рендеринг HTML-строки |
| | `render_node(node, ...)` | `bytes` | Рендеринг дерева узлов (dict) |
| | `render_template(name, ctx, ...)` | `bytes` | Рендеринг Jinja-шаблона |
| | `render_compiled(node, ...)` | `bytes` | Рендеринг предварительно скомпилированного узла |
| SVG-вывод | `render_svg_html(html, ...)` | `str` | Вывод SVG (вход HTML) |
| | `render_svg_node(node, ...)` | `str` | Вывод SVG (вход дерево узлов) |
| | `render_svg_template(name, ctx, ...)` | `str` | Вывод SVG (вход шаблон) |
| | `render_svg_compiled(node, ...)` | `str` | Вывод SVG (вход предварительно скомпилированный) |
| Анимация | `render_animation(scenes, ...)` | `bytes` | Кодирование анимации из нескольких кадров |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | Получение кадра из последовательности в определённое время |
| Измерение | `measure_node(node, ...)` | `dict` | Измерение макета дерева узлов |
| | `measure_html(html, ...)` | `dict` | Измерение макета HTML |
| | `measure_compiled(node, ...)` | `dict` | Измерение предварительно скомпилированного узла |
| Компиляция | `compile_node(node)` | `CompiledNode` | Компиляция дерева узлов |
| | `compile_html(html, ...)` | `CompiledNode` | Компиляция HTML |
| Шрифты | `register_font(font)` | `list[str]` | Регистрация пользовательского шрифта, возвращает список family |
| | `register_fonts(fonts)` | `list[str]` | Массовая регистрация |

> `CompiledNode` предоставляет метод `resource_urls()`, который позволяет заранее обнаружить ссылки на HTTP(S) изображения, что полезно для предварительной подготовки ресурсов.

### Общие параметры

Следующие параметры применимы к статическим и SVG-методам (методы анимации имеют дополнительные параметры, такие как `fps`, см. соответствующие примеры):

| Параметр | Тип | Значение по умолчанию | Описание |
|------|------|--------|------|
| `stylesheets` | `list[str]` | `None` | Список CSS-строк для документа; инлайновые `style` всё ещё анализируются вместе с HTML |
| `width` | `int \| None` | `1200` | Ширина области просмотра (пиксели); `None` означает автоматическое определение по макету |
| `height` | `int \| None` | `630` | Высота холста (пиксели); `None` означает автоматическое подстраивание под содержимое (см. [Размеры и формат вывода](#размеры-и-формат-вывода)) |
| `lang` | `str \| None` | `None` | Тег языка по BCP-47 (например, `zh-CN`), влияет на форматирование и перенос текста |
| `font_families` | `list[str]` | Автоматически вставляется | Стек шрифтов; методы по умолчанию вставляют встроенные шрифты |
| `format` | `str` | `"png"` | Формат вывода (см. [Размеры и формат вывода](#размеры-и-формат-вывода)) |
| `device_pixel_ratio` | `float` | `1.0` | Соотношение пикселей устройства, контролирует разрешение вывода |
| `time_ms` | `int` | `0` | Время в миллисекундах для выборки кадра анимации |
| `dithering` | `str` | `"none"` | Алгоритм дithering: `none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | Качество сжатия с потерями |
| `lossless` | `bool \| None` | `None` | Без потерь |
| `images` | `list` | `None` | Список изображений для рендеринга (объект `ImageResource` или кортеж `(src, bytes)`) |
| `keyframes` | `Mapping` | `None` | Структурированные ключевые кадры, не требуют записи `@keyframes` |
| `options` | `RenderOptions` | — | Группировка параметров через `RenderOptions(...)`, поля совпадают с таблицей выше |

Полное описание полей см. в `takumi_py.RenderOptions`.

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

> Можно через `filters={...}` добавить пользовательские фильтры Jinja или через `environment=...` передать полный `jinja2.Environment`. Конфигурация шаблонов и окружения см. в [документации по шаблонам takumi-py](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md).

### Пример SVG-вывода

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

> Каждый кадр состоит из `AnimationScene(node, duration_ms=...)`, `duration_ms` должен быть положительным.

---

## Размеры и формат вывода

### Форматы вывода

| Сценарий | Значение `format` |
|------|---------------|
| Статическое изображение | `png` (по умолчанию) / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| Анимация | `webp` (по умолчанию) / `apng` / `gif` |

`format="raw"` возвращает байтовый поток RGBA в порядке строк, что полезно для обработки пикселей.

### О ширинах и высотах

`width` и `height` имеют разные роли:

- `width` — **ширина области просмотра**, текст и макет переносятся по ней. **Должна быть фиксированной** (например, `800`), иначе холст будет растягиваться по содержимому, текст не будет переноситься, и размеры будут неконтролируемыми.
- `height` — **высота холста**, автоматически увеличивается по содержимому. Значение по умолчанию `630`; при `height=None` Takumi **автоматически подгоняет высоту холста** (auto viewport).

> [!TIP]
> **Рекомендуемая комбинация: фиксированная `width` + `height=None`.** Только при необходимости фиксированного размера холста или эффекта обрезки следует указывать конкретное значение `height`.

> [!NOTE]
> `width` / `height` может быть передан как `None`, чтобы определить по макету (например, если узел уже имеет размер); при указании обоих параметров размер вывода будет определённым.

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
| `takumi.fonts` | Список имен встроенных шрифтов |
| `takumi.families` | Список зарегистрированных family шрифтов |

### Автоматическая вставка

Все методы рендеринга, измерения, SVG, анимации и шаблонов в `sdk.Takumi` автоматически вставляют `takumi.families` в качестве стека шрифтов. При прямом вызове `takumi.renderer` (оригинальный экземпляр) или при создании независимого экземпляра через `create_renderer()`, необходимо вручную передать `font_families=takumi.families`.

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

`register_font` возвращает список зарегистрированных family, которые можно использовать в последующих рендерингах через `font_families`.

---

## Экземпляры рендерера

### Оригинальный рендерер

`takumi.renderer` — это оригинальный экземпляр `takumi_py.Renderer`. При прямом вызове необходимо вручную передавать `font_families`:

```python
png = takumi.renderer.render_html(
    "<div>Привет</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### Независимый рендерер

Для изоляции шрифтов / изображений / кэша ресурсов (долгоживущие процессы, сценарии с несколькими пользователями) можно создать независимый `Renderer`, в который автоматически будут зарегистрированы встроенные шрифты:

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>Независимый рендерер</div>",
    font_families=takumi.families,
    width=800,
    height=None,
    lang="zh-CN",
)
```

`create_renderer()` принимает параметры конструктора `takumi_py.Renderer`:

| Параметр | Тип | Значение по умолчанию | Описание |
|------|------|--------|------|
| `load_default_fonts` | `bool` | `False` | Загружать ли встроенные шрифты takumi-py (встроенные шрифты всегда загружаются) |
| `fonts` | `list[FontResource]` | `None` | Дополнительные зарегистрированные пользовательские шрифты |
| `cache_max_bytes` | `int \| None` | `None` | Максимальный размер кэша ресурсов (байты); `0` отключает кэш |
| `persistent_images` | `list` | `None` | Постоянные изображения |

> Независимые экземпляры не проходят через модульный прокси, поэтому для сохранения общего встроенного стека шрифтов необходимо явно передавать `font_families=takumi.families`. Если явно передать `font_families`, модуль будет уважать настройки вызывающей стороны и не будет вставлять стек по умолчанию; `RenderOptions(font_families=...)` также будет действовать.

---

## Отправка рендеринга

Результат рендеринга — это `bytes`, который можно отправить через ответ события:

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# Способ 1: Ответ в виде Image
await event.reply(png, method="Image")

# Способ 2: Ответ через OneBot12
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> Разные платформы обрабатывают изображения через адаптеры. Подробнее см. в [разделе MessageBuilder](../advanced/message-builder.md) и [спецификации методов отправки](../standards/send-method-spec.md).

---

## Конфигурация

```toml
[Takumi]
enabled = true
```

---

## Связанные ссылки

- PyPI: <https://pypi.org/project/ErisPulse-Takumi/>
- Репозиторий: <https://github.com/ccd2s/ErisPulse-Takumi> (автор [@ccd2s](https://github.com/ccd2s))
- Базовый движок: <https://github.com/BalconyJH/takumi-py>
- Документация takumi-py: <https://github.com/BalconyJH/takumi-py/blob/main/docs/index.md>