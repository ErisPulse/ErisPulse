# Документация ErisPulse

ErisPulse — это масштабируемый многофункциональный фреймворк для обработки сообщений, поддерживающий взаимодействие с различными платформами через адаптеры и предоставляющий гибкую систему модулей для расширения функциональности.

> Не понимаете термин? Посмотрите [Глоссарий](terminology.md) для понятного объяснения.

## Навигация по документации

### Быстрый старт

- [Руководство по быстрому запуску](quick-start.md) — введение в установку и запуск ErisPulse

### Обзор архитектуры

- [Обзор архитектуры](architecture.md) — визуальное представление основной архитектуры SDK, процесса инициализации, обработки событий и жизненного цикла

### Начинающим

Если вы впервые используете ErisPulse, рекомендуем прочитать следующие материалы в указанном порядке:

1. [Обзор руководства для новичков](getting-started/README.md)
2. [Создание первого бота](getting-started/first-bot.md)
3. [Основные понятия](getting-started/basic-concepts.md)
4. [Введение в обработку событий](getting-started/event-handling.md)
5. [Примеры распространённых задач](getting-started/common-tasks.md)

### Руководство пользователя

- [Установка и настройка](user-guide/installation.md)
- [Справочник команд CLI](user-guide/cli-reference.md)
- [Описание конфигурационного файла](user-guide/configuration.md)
- [Руководство по развертыванию](user-guide/deployment.md)

### Руководство для разработчиков

#### Разработка модулей

- [Введение в разработку модулей](developer-guide/modules/getting-started.md)
- [Основные концепции модулей](developer-guide/modules/core-concepts.md)
- [Подробное объяснение Event-обёртки](developer-guide/modules/event-wrapper.md)
- [Лучшие практики разработки модулей](developer-guide/modules/best-practices.md)

#### Разработка адаптеров

- [Введение в разработку адаптеров](developer-guide/adapters/getting-started.md)
- [Основные концепции адаптеров](developer-guide/adapters/core-concepts.md)
- [Подробное объяснение SendDSL](developer-guide/adapters/send-dsl.md)
- [Лучшие практики разработки адаптеров](developer-guide/adapters/best-practices.md)

#### Публикация

- [Руководство по публикации и магазину модулей](developer-guide/publishing.md) — публикация модулей и адаптеров в магазине модулей ErisPulse

### Руководство по функциональности платформ

- [Описание функциональности платформ](platform-guide/README.md)
- [Функциональность платформы Yunhu](platform-guide/yunhu.md)
- [Функциональность платформы Telegram](platform-guide/telegram.md)
- [Функциональность платформы OneBot11](platform-guide/onebot11.md)
- [Функциональность платформы OneBot12](platform-guide/onebot12.md)
- [Функциональность платформы Email](platform-guide/email.md)

### Справочник API

- [API основных модулей](api-reference/core-modules.md)
- [API системы событий](api-reference/event-system.md)
- [API системы адаптеров](api-reference/adapter-system.md)

### Технические стандарты

- [Стандарт преобразования событий](standards/event-conversion.md)
- [Стандарт ответа API](standards/api-response.md)
- [Спецификация методов отправки](standards/send-method-spec.md)

### Продвинутые темы

- [Система ленивой загрузки](advanced/lazy-loading.md)
- [Управление жизненным циклом](advanced/lifecycle.md)
- [Система маршрутизации](advanced/router.md)
- [Подробное объяснение MessageBuilder](advanced/message-builder.md)
- [Система типов сессий](advanced/session-types.md)
- [Многошаговые диалоги Conversation](advanced/conversation.md)

### Разработка с помощью ИИ

- [Разработка с помощью ИИ](ai-support/README.md)

### Стиль-гайд

- [Стиль-гайд для документации](styleguide/docstring.md)

## Способы разработки

ErisPulse поддерживает два способа разработки:

### 1. Разработка модулей (рекомендуется)

Создание независимого пакета модуля, который устанавливается и используется через менеджер пакетов. Такой подход удобен для распространения и управления, подходит для публично доступных функций.

### 2. Встраиваемая разработка

Прямое внедрение кода ErisPulse в проект без создания отдельного модуля. Такой способ подходит для быстрой разработки прототипов или внутренних специфических функций.

Пример:

```python
# Встраиваемый запуск
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

# Регистрация обработчика команды
@command("hello")
async def hello_handler(event):
    await event.reply("Привет!")

# Запуск SDK и поддержание работы | Должен выполняться в асинхронной среде
asyncio.run(sdk.run(keep_running=True))
```

## Получение помощи

- Репозиторий на GitHub: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Сообщение об ошибках: Открытие Issue
- Технические обсуждения: Просмотр Discussions

## Связанные ссылки

- [Стандарт OneBot12](https://12.onebot.dev/)
- [Официальная документация Yunhu](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Русский**