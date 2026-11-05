[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

# ErisPulse — ветка дистрибуции документации

Генерируется CI автоматически и принудительно обновляется при каждом запуске конвейера документации. Ветка всегда содержит один коммит с последней сборкой; истории для просмотра нет.

## Содержимое

- `docs/<lang>/` — полное дерево документации для `zh-CN / en / zh-TW / ja / ru`
- `docs/<lang>/ai-support/prompts/` — объединённые AI-материалы (`ErisPulse-ModuleDev.md`, `ErisPulse-AdapterDev.md`, `ErisPulse-Full.md`)
- `docs/<lang>/ai-support/skills.zip` — пакет документации: все документы в исходном виде + README-указатель («когда читать» для каждого)

## Получение файлов

- Карточки загрузки на сайте: <https://www.erisdev.com>
- Прямая ссылка: `https://raw.githubusercontent.com/ErisPulse/ErisPulse/docs-generated/docs/<lang>/ai-support/...`

## Примечания

- Не открывайте PR в эту ветку; исходники — в `Develop/v2`
- Сборка: `python -m scripts.tools gen ...`; коммитер — `erispulse[bot]`
