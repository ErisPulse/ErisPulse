# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) — это **пользовательский модуль рендеринга изображений**, поддерживаемый ccd2s, основанный на [takumi-py](https://github.com/BalconyJH/takumi-py). Он позволяет боту преобразовывать HTML, дерево узлов, шаблоны Jinja, SVG и анимации в изображения. Модуль **включает в себя шрифты на китайском и английском языках** (Noto Sans SC / Roboto / Source Code Pro), поэтому дополнительная настройка не требуется.

> [!IMPORTANT]
> Takumi **не входит** в состав фреймворка ErisPulse и требует отдельной установки:
>
> ```bash
> epsdk install Takumi
> ```

Применение:

- Преобразование данных/статистики в изображения карточек
- Преобразование Markdown / длинного текста в изображения с устойчивым форматированием, чтобы избежать различий в стилях платформы
- Генерация SVG / анимаций для реализации динамических визуальных эффектов
- Генерация изображений с текстом на китайском и английском языках (встроенные шрифты готовы к использованию без дополнительной настройки)

## Установка и включение

```bash
epsdk install Takumi
```

После установки модуль будет автоматически загружен. Убедитесь, что он включен в конфигурации:

```toml
[Takumi]
enabled = true
```

---

## Быстрый старт

После автоматической загрузки модуля, получите его через менеджер модулей или используйте сокращение `sdk`:

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# Эквивалентная запись: takumi = sdk.Takumi
```

### Отображение HTML

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>Привет, ErisPulse</h1>
      <p>Отрендерено Takumi</p>
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
    height=None,   # Автоматически подстраивается по содержимому
    lang="zh-CN",
)
```

### Отображение узлового дерева

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "Можно отображать как китайский, так и английский текст напрямую",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

`png` является `bytes`, который можно отправить с помощью `event.reply(png, method="Image")` (см. [Отправка результата рендеринга](#отправка-результата-рендеринга)).

---

## API рендеринга

`sdk.Takumi` делегирует все возможности базового `takumi_py.Renderer`: все методы рендеринга, измерения, SVG, анимации и шаблонов доступны напрямую в `sdk.Takumi`. При вызове этих методов модуль автоматически вставляет встроенный стек шрифтов по умолчанию (`takumi.families`), без необходимости явного передачи `font_families`; если шрифты переданы явно, то приоритет отдается настройкам вызывающей стороны.

### Обзор методов

| Категория | Метод | Возвращаемое значение | Описание |
|------|------|------|------|
| Статический рендеринг | `render_html(html, ...)` | `bytes` | Рендеринг строки HTML |
| | `render_node(node, ...)` | `bytes` | Рендеринг дерева узлов (dict) |
| | `render_template(name, ctx, ...)` | `bytes` | Рендеринг шаблона Jinja |
| | `render_compiled(node, ...)` | `bytes` | Рендеринг предварительно скомпилированного узла |
| SVG-вывод | `render_svg_html(html, ...)` | `str` | Вывод SVG (вход HTML) |
| | `render_svg_node(node, ...)` | `str` | Вывод SVG (вход дерево узлов) |
| | `render_svg_template(name, ctx, ...)` | `str` | Вывод SVG (вход шаблон) |
| | `render_svg_compiled(node, ...)` | `str` | Вывод SVG (вход предварительно скомпилированный) |
| Анимация | `render_animation(scenes, ...)` | `bytes` | Кодирование многокадровой анимации |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | Получение кадра последовательности в определённый момент времени |
| Измерение | `measure_node(node, ...)` | `dict` | Измерение макета дерева узлов |
| | `measure_html(html, ...)` | `dict` | Измерение макета HTML |
| | `measure_compiled(node, ...)` | `dict` | Измерение предварительно скомпилированного узла |
| Компиляция | `compile_node(node)` | `CompiledNode` | Компиляция дерева узлов |
| | `compile_html(html, ...)` | `CompiledNode` | Компиляция HTML |
| Шрифты | `register_font(font)` | `list[str]` | Регистрация пользовательского шрифта, возвращает список family |
| | `register_fonts(fonts)` | `list[str]` | Массовая регистрация шрифтов |

> `CompiledNode` предоставляет метод `resource_urls()`, который позволяет заранее обнаружить ссылки на HTTP(S) изображения, что полезно для предварительной подготовки ресурсов.

### Общие параметры

Следующие параметры применимы к статическим методам рендеринга и SVG (методы анимации имеют свои параметры, такие как `fps`, см. соответствующие примеры):

| Параметр | Тип | Значение по умолчанию | Описание |
|------|------|--------|------|
| `stylesheets` | `list[str]` | `None` | Список строк CSS для документа; встроенные `style` всё ещё анализируются вместе с HTML |
| `width` | `int \| None` | `1200` | Ширина области просмотра (пиксели); `None` означает автоматическое определение по макету |
| `height` | `int \| None` | `630` | Высота холста (пиксели); `None` означает автоматическое растягивание по содержимому (см. [Размеры области просмотра и формат вывода](#Размеры-области-просмотра-и-формат-вывода)) |
| `lang` | `str \| None` | `None` | Языковой тег BCP-47 (например, `zh-CN`), влияет на форматирование текста и перенос строк |
| `font_families` | `list[str]` | Автоматически вставляется | Стек шрифтов по умолчанию; в удобных методах автоматически вставляется встроенный шрифт |
| `format` | `str` | `"png"` | Формат вывода (см. [Размеры области просмотра и формат вывода](#Размеры-области-просмотра-и-формат-вывода)) |
| `device_pixel_ratio` | `float` | `1.0` | Соотношение физических пикселей, контролирует разрешение вывода |
| `time_ms` | `int` | `0` | Время выборки для анимации (миллисекунды) |
| `dithering` | `str` | `"none"` | Алгоритм дithering: `none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | Качество кодирования с потерями |
| `lossless` | `bool \| None` | `None` | Использовать ли без потерь кодирование |
| `images` | `list` | `None` | Ресурсы изображений для текущего рендеринга (объекты `ImageResource` или кортежи `(src, bytes)`) |
| `keyframes` | `Mapping` | `None` | Структурированные ключевые кадры, не требует записи в `@keyframes` |
| `options` | `RenderOptions` | — | Агрегация параметров в виде `RenderOptions(...)`, поля соответствуют таблице выше |

Полное определение полей доступно в `takumi_py.RenderOptions`.

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

> Можно добавить пользовательские фильтры Jinja через `filters={...}` или передать полный `jinja2.Environment` через `environment=...`. Дополнительные сведения о настройке шаблонов см. в [документации по шаблонам takumi-py](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md).

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

> Каждый кадр состоит из `AnimationScene(node, duration_ms=...)`, где `duration_ms` должен быть положительным числом.

## Видимая область и формат вывода

### Формат вывода

| Сценарий | Значение `format` |
|---------|-------------------|
| Статичные изображения | `png` (по умолчанию) / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| Анимация | `webp` (по умолчанию) / `apng` / `gif` |

`format="raw"` возвращает байтовый поток RGBA в порядке строк, для пользовательской обработки пикселей.

### О ширинах и высотах

Роли `width` и `height` несимметричны:

- `width` — это **ширина области просмотра**, по ней происходит перенос и перерасчет текста и макета. **Должна быть фиксированной** (например, `800`), иначе холст будет растягиваться по ширине содержимого, текст не будет переноситься, и размеры станут неконтролируемыми.
- `height` — это **высота холста**, она увеличивается по мере роста содержимого. Значение по умолчанию для `height` — `630`; при передаче `height=None` Takumi **автоматически растянет холст** (автоматическая видимая область).

> [!TIP]
> **Рекомендуемое сочетание: фиксированная `width` + `height=None`.** Только в случае необходимости фиксированного размера холста или эффекта обрезки следует указывать конкретное значение `height`.

> [!NOTE]
> Технически, `width` / `height` может быть передано как `None`, чтобы их размеры определялись по макету (например, если размеры узлов уже указаны); если заданы оба значения, размеры вывода будут определенными.

## Шрифты

### Встроенные шрифты

| Шрифт | Семейство | Категория |
|------|--------|------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif (курсив) |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace (курсив) |

Модульные свойства:

| Свойство | Описание |
|------|------|
| `takumi.fonts` | Список имен встроенных шрифтов |
| `takumi.families` | Список зарегистрированных семейств шрифтов |

### Автоматическая вставка

Все методы рендеринга, измерения, SVG, анимации и шаблонов на `sdk.Takumi` автоматически вставляют `takumi.families` в качестве стека резервных шрифтов. Если напрямую вызывать `takumi.renderer` (оригинальный экземпляр) или создавать независимый экземпляр с помощью `create_renderer()`, необходимо вручную передавать `font_families=takumi.families`.

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

Метод `register_font` возвращает список зарегистрированных имен семейств шрифтов, которые можно передавать в качестве `font_families` при последующем рендеринге.

## Экземпляр рендерера

### Оригинальный рендерер

`takumi.renderer` — это оригинальный экземпляр `takumi_py.Renderer`. При прямом вызове необходимо вручную передавать `font_families`:

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### Независимый рендерер

Для изоляции кэша шрифтов / изображений / ресурсов (длинные жизненные циклы процессов, сценарии с несколькими пользователями) можно создать независимый `Renderer`, встроенные шрифты которого автоматически регистрируются:

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
|---------|------|----------------|----------|
| `load_default_fonts` | `bool` | `False` | Загружать ли встроенные шрифты takumi-py (встроенные шрифты всегда загружаются) |
| `fonts` | `list[FontResource]` | `None` | Дополнительно зарегистрированные пользовательские шрифты |
| `cache_max_bytes` | `int \| None` | `None` | Верхний предел кэша ресурсов (в байтах); `0` отключает кэширование |
| `persistent_images` | `list` | `None` | Ресурсы изображений, сохраняемые в постоянном хранилище |

> Независимые экземпляры не проходят через модульный прокси, поэтому для сохранения единой стековой обратной связи встроенных шрифтов необходимо явно передавать `font_families=takumi.families`. Если явно передать `font_families`, модуль будет уважать настройки вызывающей стороны и не будет вставлять стек по умолчанию; то же самое касается `RenderOptions(font_families=...)`.

## Отправка результата рендеринга

Изображения, полученные в результате рендеринга, представляют собой `bytes`, и их можно отправить напрямую с помощью ответа на событие:

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# Способ 1: Отправка с помощью метода Image
await event.reply(png, method="Image")

# Способ 2: Отправка с помощью сегмента сообщения OneBot12
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> Разные платформы обрабатывают изображения через адаптеры. Подробнее см. [Разбор MessageBuilder](../advanced/message-builder.md) и [Спецификация методов отправки](../standards/send-method-spec.md).

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