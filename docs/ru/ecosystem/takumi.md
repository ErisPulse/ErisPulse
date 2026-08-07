# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) — это модуль для рендеринга изображений от **ccd2s**, основанный на [takumi-py](https://github.com/BalconyJH/takumi-py), который позволяет ботам конвертировать HTML, узловые деревья, шаблоны Jinja, SVG и анимации в изображения. Модуль **встроен шрифты китайского и английского языков** (Noto Sans SC / Roboto / Source Code Pro), дополнительные настройки не требуются.

> [!IMPORTANT]
> Takumi **не** является встроенной функцией фреймворка ErisPulse, его необходимо установить отдельно:
>
> ```bash
> epsdk install Takumi
> ```

Используемые сценарии:

- Рендеринг данных / статистики в виде карточек изображений
- Конвертация Markdown / длинного текста в изображения с гарантированной типографикой, чтобы избежать различий в стилях платформ
- Генерация SVG / анимаций для создания динамических визуальных эффектов
- Смешанные китайско-английские иллюстрации (встроенные шрифты готовы к использованию)

---

## Установка и активация

```bash
epsdk install Takumi
```

После установки модуль загружается автоматически. Подтвердите включение в конфигурации:

```toml
[Takumi]
enabled = true

## Быстрый старт

После автоматической загрузки модулей их можно получить через менеджер модулей или с помощью сокращённого способа `sdk`:

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
      <p>Сгенерировано с помощью Takumi</p>
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
    height=None,   # Автоматическое расширение по содержимому
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

`png` — это `bytes`, которые можно отправить через `event.reply(png, method="Image")` (см. [Отправка результата рендеринга](#отправка-результата-рендеринга)).

---

## API Rendering

`sdk.Takumi` проксирует все возможности базового `takumi_py.Renderer`: все операции рендеринга, измерения, SVG, анимации и методы шаблонов можно вызывать напрямую через `sdk.Takumi`. Для этих методов модуль автоматически внедряет стек встроенных шрифтов-запасных (`takumi.families`) при вызове, без необходимости вручную передавать `font_families`; если значение явно передано, оно переопределяет настройки вызывающего объекта.

### Обзор методов

| Категория | Метод | Возврат | Описание |
|-----------|-------|---------|----------|
| Статический рендеринг | `render_html(html, ...)` | `bytes` | Рендеринг строки HTML |
| | `render_node(node, ...)` | `bytes` | Рендеринг дерева узлов (dict) |
| | `render_template(name, ctx, ...)` | `bytes` | Рендеринг шаблона Jinja |
| | `render_compiled(node, ...)` | `bytes` | Рендеринг предварительно скомпилированного узла |
| SVG вывод | `render_svg_html(html, ...)` | `str` | Вывод SVG (вход: HTML) |
| | `render_svg_node(node, ...)` | `str` | Вывод SVG (вход: дерево узлов) |
| | `render_svg_template(name, ctx, ...)` | `str` | Вывод SVG (вход: шаблон) |
| | `render_svg_compiled(node, ...)` | `str` | Вывод SVG (вход: предварительно скомпилированный) |
| Анимация | `render_animation(scenes, ...)` | `bytes` | Кодирование многокадровой анимации |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | Получение кадра последовательности в заданный момент времени |
| Измерение | `measure_node(node, ...)` | `dict` | Измерение верстки дерева узлов |
| | `measure_html(html, ...)` | `dict` | Измерение верстки HTML |
| | `measure_compiled(node, ...)` | `dict` | Измерение предварительно скомпилированного узла |
| Компиляция | `compile_node(node)` | `CompiledNode` | Компиляция дерева узлов |
| | `compile_html(html, ...)` | `CompiledNode` | Компиляция HTML |
| Шрифты | `register_font(font)` | `list[str]` | Регистрация пользовательского шрифта, возвращает список семейств |
| | `register_fonts(fonts)` | `list[str]` | Массовая регистрация |

> `CompiledNode` предоставляет метод `resource_urls()`, позволяющий заранее обнаружить ссылки на HTTP(S) изображения, подлежащие загрузке, что упрощает подготовку ресурсов.

### Общие параметры

Следующие параметры применяются к методам статического рендеринга и SVG (для методов анимации предусмотрены дополнительные параметры, такие как `fps`, см. соответствующие примеры):

| Параметр | Тип | Значение по умолчанию | Описание |
|----------|-----|----------------------|----------|
| `stylesheets` | `list[str]` | `None` | Список строк CSS на уровне документа; встроенные `style` всё равно анализируются вместе с HTML |
| `width` | `int \| None` | `1200` | Ширина области просмотра (пиксели); `None` — определить из верстки |
| `height` | `int \| None` | `630` | Высота холста (пиксели); `None` — автоматически растянуть по содержимому (см. [Viewport and Output Format](#viewport-and-output-format)) |
| `lang` | `str \| None` | `None` | Языковая метка BCP-47 (например, `zh-CN`), влияет на текстовую верстку и переносы строк |
| `font_families` | `list[str]` | Автоматическое внедрение | Стек шрифтов-запасных; в удобных методах по умолчанию внедряются встроенные шрифты |
| `format` | `str` | `"png"` | Формат вывода (см. [Viewport and Output Format](#viewport-and-output-format)) |
| `device_pixel_ratio` | `float` | `1.0` | Коэффициент пикселей устройства, управляет разрешением вывода |
| `time_ms` | `int` | `0` | Момент выборки анимации (в миллисекундах) |
| `dithering` | `str` | `"none"` | Алгоритм дизеринга: `none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | Качество кодирования с потерями |
| `lossless` | `bool \| None` | `None` | Кодирование без потерь |
| `images` | `list` | `None` | Ресурсы изображений для текущего рендеринга (`ImageResource` или кортеж `(src, bytes)`) |
| `keyframes` | `Mapping` | `None` | Структурированные ключевые кадры, не требуют записи `@keyframes` |
| `options` | `RenderOptions` | — | Группировка аргументов через `RenderOptions(...)`; поля соответствуют таблице выше |

Полное определение полей см. в `takumi_py.RenderOptions`.

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

### Пример шаблона Jinja

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

> Пользовательские фильтры Jinja можно внедрить через `filters={...}` или передать полный `jinja2.Environment` через `environment=...`. Подробности о каталоге шаблонов и настройках среды см. в [документации шаблонов takumi-py](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md).

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

> Каждый кадр составлен через `AnimationScene(node, duration_ms=...)`, где `duration_ms` должно быть положительным числом.

---

## Viewport и формат вывода

### Формат вывода

| Сценарий | Значение `format` |
|------|---------------|
| Статичное изображение | `png` (по умолчанию) / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| Анимация | `webp` (по умолчанию) / `apng` / `gif` |

`format="raw"` возвращает поток байтов RGBA в формате строка-первый (row-major) для кастомной обработки на уровне пикселей.

### О width и height

Роли `width` и `height` не симметричны:

- `width` — это**ширина области просмотра (viewport width)**, текст и макет перестраиваются с учетом ширины. Должен быть**фиксированным** конкретным значением (например, `800`), иначе холст будет растягиваться до естественной ширины содержимого, текст не будет переноситься, а размер будет неконтролируемым.
- `height` — это**высота холста**, она растет по мере наполнения контентом. Значение по умолчанию для `height` равно `630`; при передаче `height=None` Takumi **автоматически увеличит высоту области просмотра в соответствии с содержимым** (auto viewport).

> [!TIP]
> **Рекомендуемая комбинация: фиксированный `width` + `height=None`.** Передавайте конкретное значение `height` только тогда, когда вам нужен холст фиксированного размера или эффект обрезки.

> [!NOTE]
> Технически значение `width` / `height` можно передать как `None`, чтобы разрешить выводу определять его на основе макета (например, когда узел сам объявляет свой размер); если оба значения заданы, размер вывода определен однозначно.

---

## Шрифты

### Встроенные шрифты

| Шрифт | family | Категория |
|------|--------|------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif（italic） |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace（italic） |

Свойства модуля:

| Свойство | Описание |
|------|------|
| `takumi.fonts` | Список имен файлов встроенных шрифтов |
| `takumi.families` | Список зарегистрированных шрифтов `family` |

### Автоматическая инъекция

Все методы рендеринга, измерения, SVG, анимации и шаблонов на `sdk.Takumi` автоматически внедряют `takumi.families` как стек отложенных шрифтов. Если вы напрямую вызываете `takumi.renderer` (нативный экземпляр) или создаете независимый экземпляр через `create_renderer()`, необходимо вручную передать `font_families=takumi.families`.

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

`register_font` возвращает список имен зарегистрированных `family`, которые можно передать как `font_families` при последующем рендеринге.

---

## Экземпляр рендерера

### Встроенный Renderer

`takumi.renderer` — это оригинальный экземпляр `takumi_py.Renderer`. При прямом вызове необходимо вручную передать `font_families`:

```python
png = takumi.renderer.render_html(
    "<div>Привет</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### Отдельный Renderer

При необходимости изолировать кэш шрифтов / изображений / ресурсов (долговременные процессы, сценарии мульти-аренды) можно создать отдельный `Renderer`, встроенные шрифты будут автоматически зарегистрированы:

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>Отдельный Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=None,
    lang="zh-CN",
)
```

`create_renderer()` принимает конструкторные аргументы `takumi_py.Renderer`:

| Параметр | Тип | Значение по умолчанию | Описание |
|------|------|--------|------|
| `load_default_fonts` | `bool` | `False` | Загружать ли шрифты, входящие в состав takumi-py (встроенные шрифты всегда загружаются) |
| `fonts` | `list[FontResource]` | `None` | Дополнительные зарегистрированные пользовательские шрифты |
| `cache_max_bytes` | `int \| None` | `None` | Лимит размера кэша ресурсов (байты); `0` отключает |
| `persistent_images` | `list` | `None` | Персистентные ресурсы изображений |

> Отдельный экземпляр не проходит через модульный прокси, поэтому для сохранения унифицированного стека отступов встроенных шрифтов необходимо явно передать `font_families=takumi.families`. Если явно передать `font_families`, модуль будет уважать настройки вызывающей стороны и не внедрять стек отступов по умолчанию; эквивалентно этому работает и `RenderOptions(font_families=...)`.

---

## Отправка результатов рендеринга

Полученное изображение — это `bytes`, которое можно отправить напрямую через ответ на событие:

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="ru-RU")

# Способ 1: ответ через метод Image
await event.reply(png, method="Image")

# Способ 2: ответ через сегмент сообщения OneBot12
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> Обработка инкапсуляции изображений для разных платформ выполняется адаптером. Подробнее см. [MessageBuilder 详解](../ru/advanced/message-builder.md) и [发送方法规范](../ru/standards/send-method-spec.md).

---

## Настройка

```toml
[Takumi]
enabled = true
```

---

## Ссылки

- PyPI: <https://pypi.org/project/ErisPulse-Takumi/>
- Репозиторий: <https://github.com/ccd2s/ErisPulse-Takumi> (автор [@ccd2s](https://github.com/ccd2s))
- Движок: <https://github.com/BalconyJH/takumi-py>
- Документация takumi-py: <https://github.com/BalconyJH/takumi-py/blob/main/docs/index.md>