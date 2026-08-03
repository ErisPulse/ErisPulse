# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) — это **третья сторона модуль рендеринга изображений**, поддерживаемый ccd2s, основанный на [takumi-py](https://github.com/BalconyJH/takumi-py), который позволяет рендерить изображения в боте: HTML, дерево узлов, шаблоны Jinja, SVG, анимации — всё возможно, и **встроенные шрифты на китайском и английском** (Noto Sans SC / Roboto / Source Code Pro), без необходимости дополнительной настройки шрифтов.

> [!IMPORTANT]
> Takumi **не** является встроенной функцией фреймворка ErisPulse, его нужно устанавливать отдельно:
>
> ```bash
> epsdk install Takumi
> ```

Особенно подходит для следующих сценариев:

- Преобразование данных/статистики в красивые карточки-изображения для отправки
- Преобразование Markdown / длинного текста в стабильно отформатированные изображения, чтобы избежать различий в стилях платформы
- Генерация SVG / анимаций, для динамических визуальных эффектов
- Вывод изображений с текстом на китайском и английском (встроенные шрифты готовы к использованию)

---

## Установка и активация

```bash
epsdk install Takumi
```

После установки модуль будет автоматически загружен, и нужно только убедиться, что он включен в конфигурационном файле:

```toml
[Takumi]
enabled = true
```

---

## Быстрый старт

После автоматической загрузки модуля, его можно получить через менеджер модулей, или использовать сокращённый способ `sdk`:

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# Альтернативная запись: takumi = sdk.Takumi
```

### Рендеринг HTML

Самый распространённый способ — рендеринг HTML + CSS строки в PNG:

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>你好，ErisPulse</h1>
      <p>Рендерится Takumi</p>
    </div>
    """,
    stylesheets=["""
    .card {
      width: 800px;
      height: 400px;
      padding: 48px;
      color: white;
      background: #111827;
      font-family: "Noto Sans SC";
    }
    """],
    width=800,
    height=400,
    lang="zh-CN",
)
```

`png` — это `bytes`, его можно отправить с помощью `event.reply(png, method="Image")` (см. [Отправка рендеринга](#Отправка рендеринга)).

### Рендеринг дерева узлов

Не нужно писать HTML вручную, достаточно описать структуру с помощью словаря, что удобно для программной сборки:

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "Текст на китайском и English можно рендерить напрямую",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=200,
    lang="zh-CN",
)
```

---

## Шрифты и рендереры

### Встроенные шрифты

Takumi уже содержит распространённые шрифты, дополнительная установка не требуется:

| Ресурс | Описание |
|------|------|
| `takumi.fonts` | Список имён встроенных шрифтов |
| `takumi.families` | Список зарегистрированных шрифтовых семейств |

Удобные методы (`render_html` / `render_node`) автоматически вставляют стек возврата к встроенным шрифтам; если вы используете базовый рендерер напрямую, вам нужно будет передать `font_families` самостоятельно.

### Оригинальный рендерер

`takumi.renderer` — это оригинальный экземпляр `takumi_py.Renderer`. Удобные методы автоматически вставляют стек возврата к встроенным шрифтам; **при прямом вызове рендерера нужно передавать families самостоятельно**:

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### Независимый рендерер

Для изоляции шрифтов / изображений / ресурсов кэша (например, в процессах с длительным временем жизни, или в сценариях с несколькими пользователями), можно создать новый `Renderer`, встроенные шрифты будут автоматически зарегистрированы:

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>Независимый рендерер</div>",
    font_families=takumi.families,
    width=800,
    height=200,
    lang="zh-CN",
)
```

`create_renderer()` принимает параметры конструктора `takumi_py.Renderer`:

- `load_default_fonts=False` (по умолчанию): загружаются только встроенные шрифты
- `load_default_fonts=True`: загружаются как встроенные, так и собственные шрифты Takumi
- `fonts=[...]`: на основе по умолчанию регистрируются пользовательские шрифты

> Независимые экземпляры не проходят через модульный прокси, поэтому, если нужно сохранить единый стек возврата к встроенным шрифтам, нужно явно передать `font_families=takumi.families`.

Если явно передать `font_families`, модуль будет уважать настройки вызывающей стороны и не будет вставлять стек по умолчанию. `RenderOptions(font_families=...)` также будет действовать.

---

## Отправка рендеринга

После получения изображения, его можно отправить напрямую через ответ события:

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# Способ 1: Отправка напрямую методом Image
await event.reply(png, method="Image")

# Способ 2: Отправка через сегмент сообщения OneBot12
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> Разные платформы обрабатывают изображения через адаптеры, без необходимости заботиться о различиях в реализации. Подробнее см. [Пояснение MessageBuilder](../advanced/message-builder.md) и [Спецификация методов отправки](../standards/send-method-spec.md).

---

## Связанные ссылки

- PyPI: <https://pypi.org/project/ErisPulse-Takumi/>
- Репозиторий: <https://github.com/ccd2s/ErispulseTakumi> (автор [@ccd2s](https://github.com/ccd2s))
- Базовый движок: <https://github.com/BalconyJH/takumi-py>