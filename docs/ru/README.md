# Документация ErisPulse

ErisPulse — это масштабируемая кроссплатформенная платформа обработки сообщений, поддерживающая взаимодействие с различными платформами через адаптеры и предоставляющая гибкую систему модулей для расширения функциональности.

> Устали от терминов? Посмотрите [Словарь терминов](terminology.md) для понятных объяснений.

## Навигация по документации

### Быстрый старт

- [Руководство по быстрому старту](quick-start.md) — руководство по установке и запуску ErisPulse

### Обзор архитектуры

- [Обзор архитектуры](architecture.md) — узнайте о ядре SDK, процессе инициализации, обработке событий и жизненном цикле через визуальные диаграммы

### Для начинающих

Если вы используете ErisPulse впервые, рекомендуется прочитать следующие материалы в указанном порядке:

1. [Обзор руководства для начинающих](getting-started/README.md)
2. [Создание первого бота](getting-started/first-bot.md)
3. [Основные концепции](getting-started/basic-concepts.md)
4. [Основы обработки событий](getting-started/event-handling.md)
5. [Примеры распространенных задач](getting-started/common-tasks.md)

### Руководство для пользователей

- [Установка и настройка](user-guide/installation.md)
- [Справочник по CLI](user-guide/cli-reference.md)
- [Описание файла конфигурации](user-guide/configuration.md)
- [Руководство по развертыванию](user-guide/deployment.md)

### Руководство для разработчиков

#### Разработка модулей

- [Начало работы с разработкой модулей](developer-guide/modules/getting-started.md)
- [Основные концепции модулей](developer-guide/modules/core-concepts.md)
- [Подробно о классе Event Wrapper](developer-guide/modules/event-wrapper.md)
- [Рекомендации по разработке модулей](developer-guide/modules/best-practices.md)

#### Разработка адаптеров

- [Начало работы с разработкой адаптеров](developer-guide/adapters/getting-started.md)
- [Основные концепции адаптеров](developer-guide/adapters/core-concepts.md)
- [Подробно о SendDSL](developer-guide/adapters/send-dsl.md)
- [Рекомендации по разработке адаптеров](developer-guide/adapters/best-practices.md)


#### Публикация

- [Руководство по публикации и модулю магазина](developer-guide/publishing.md) — публикация модулей и адаптеров в магазине модулей ErisPulse

### Руководство по платформенным особенностям

- [Описание платформенных особенностей](platform-guide/README.md)
- [Особенности платформы Yunhu](platform-guide/yunhu.md)
- [Особенности платформы Telegram](platform-guide/telegram.md)
- [Особенности платформы OneBot11](platform-guide/onebot11.md)
- [Особенности платформы OneBot12](platform-guide/onebot12.md)
- [Особенности почтовой платформы](platform-guide/email.md)

### Справочник API

- [API основных модулей](api-reference/core-modules.md)
- [API системы событий](api-reference/event-system.md)
- [API системы адаптеров](api-reference/adapter-system.md)

### Технические стандарты

- [Стандарт преобразования событий](standards/event-conversion.md)
- [Стандарт ответов API](standards/api-response.md)
- [Спецификация методов отправки](standards/send-method-spec.md)

### Расширенные темы

- [Система ленивой загрузки](advanced/lazy-loading.md)
- [Управление жизненным циклом](advanced/lifecycle.md)
- [Система маршрутизации](advanced/router.md)
- [Подробно о MessageBuilder](advanced/message-builder.md)
- [Система типов сессий](advanced/session-types.md)
- [Многоразовые диалоги (Conversation)](advanced/conversation.md)

### AI-поддержка разработки

- [AI-поддержка разработки](ai-support/README.md)

### Руководство по стилю

- [Руководство по стилю документации](styleguide/docstring.md)

## Способы разработки

ErisPulse поддерживает два способа разработки:

### 1. Разработка модулей (рекомендуется)

Создайте независимый пакет модулей и используйте его через менеджер пакетов. Этот способ удобен для распространения и управления, подходит для функций, публикуемых публично.

### 2. Встраиваемая разработка

Внедрите код ErisPulse непосредственно в проект без создания отдельного модуля. Этот способ подходит для быстрой разработки прототипов или функций, используемых внутри проекта.

Пример:

```python
# Внедрить и использовать напрямую
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

# Регистрируем обработчик команды
@command("hello")
async def hello_handler(event):
    await event.reply("Привет!")

# Запуск SDK и удержание работы | нужно работать в асинхронной среде
asyncio.run(sdk.run(keep_running=True))
```

## Получение помощи

- Репозиторий GitHub: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Отправка отчета об ошибке: Создать Issue
- Технические обсуждения: Обзор Discussions

## Связанные ссылки

- [Стандарт OneBot12](https://12.onebot.dev/)
- [Официальная документация Yunhu](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

[English](README.en.md) | [简体中文](README.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Русский**