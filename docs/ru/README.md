# Документация ErisPulse

ErisPulse — это масштабируемая, многофункциональная платформа для обработки сообщений, поддерживающая взаимодействие с различными платформами через адаптеры и предоставляющая гибкую систему модулей для расширения функциональности.

> Не понимаете термин? Посмотрите [Глоссарий](docs/ru/terminology.md) для простого объяснения.

## Навигация по документации

### Быстрый старт

- [Руководство по быстрому старту](docs/ru/quick-start.md) — руководство по установке и запуску ErisPulse

### Обзор архитектуры

- [Обзор архитектуры](docs/ru/architecture.md) — понимание основной архитектуры SDK, процесса инициализации, обработки событий и жизненного цикла с помощью визуальных диаграмм

### Новичку

Если вы впервые используете ErisPulse, рекомендуем прочитать в следующем порядке:

1. [Обзор руководства для новичков](getting-started/README.md)
2. [Создание первого бота](getting-started/first-bot.md)
3. [Основные понятия](getting-started/basic-concepts.md)
4. [Введение в обработку событий](getting-started/event-handling.md)
5. [Примеры распространённых задач](getting-started/common-tasks.md)

### Руководство пользователя

- [Установка и настройка](user-guide/installation.md)
- [Справочник по командам CLI](user-guide/cli-reference.md)
- [Описание конфигурационного файла](user-guide/configuration.md)
- [Руководство по развертыванию](user-guide/deployment.md)

### Руководство для разработчиков

#### Разработка модулей

- [Введение в разработку модулей](developer-guide/modules/getting-started.md)
- [Основные концепции модулей](developer-guide/modules/core-concepts.md)
- [Подробное объяснение класса обёртки событий](developer-guide/modules/event-wrapper.md)
- [Лучшие практики разработки модулей](developer-guide/modules/best-practices.md)

#### Разработка адаптеров

- [Введение в разработку адаптеров](developer-guide/adapters/getting-started.md)
- [Основные концепции адаптеров](developer-guide/adapters/core-concepts.md)
- [Подробное объяснение SendDSL](developer-guide/adapters/send-dsl.md)
- [Лучшие практики разработки адаптеров](developer-guide/adapters/best-practices.md)

#### Публикация

- [Руководство по публикации и магазину модулей](developer-guide/publishing.md) — публикация модулей и адаптеров в магазине ErisPulse

### Руководство по функциональным возможностям платформ

- [Описание функциональных возможностей платформ](platform-guide/README.md)
- [Функциональные возможности платформы Yunhu](platform-guide/yunhu.md)
- [Функциональные возможности платформы Telegram](platform-guide/telegram.md)
- [Функциональные возможности платформы OneBot11](platform-guide/onebot11.md)
- [Функциональные возможности платформы OneBot12](platform-guide/onebot12.md)
- [Функциональные возможности платформы Email](platform-guide/email.md)

### Справочник API

- [API основных модулей](api-reference/core-modules.md)
- [API системы событий](api-reference/event-system.md)
- [API системы адаптеров](api-reference/adapter-system.md)

### Технические стандарты

- [Стандарт преобразования событий](standards/event-conversion.md)
- [Стандарт ответа API](standards/api-response.md)
- [Спецификация методов отправки](standards/send-method-spec.md)

### Продвинутые темы

- [Процесс запуска и ручное управление](advanced/startup.md) — разбор цепочки запуска и ручной полный запуск
- [Система ленивой загрузки](advanced/lazy-loading.md)
- [Управление жизненным циклом](advanced/lifecycle.md)
- [Система маршрутизации](advanced/router.md)
- [Подробное объяснение MessageBuilder](advanced/message-builder.md)
- [Система типов сессий](advanced/session-types.md)
- [Многошаговые диалоги Conversation](advanced/conversation.md)

### Разработка с помощью ИИ

- [Разработка с помощью ИИ](ai-support/README.md)

### Стиль руководства

- [Стиль руководства по документации](styleguide/docstring.md)

## Способы разработки

ErisPulse поддерживает два способа разработки:

### 1. Разработка модулей (рекомендуется)

Создание независимого пакета модуля, который устанавливается и используется через менеджер пакетов. Такой подход удобен для распространения и управления, подходит для публично доступных функций.

### 2. Встраиваемая разработка

Непосредственное внедрение кода ErisPulse в проект, без создания отдельного модуля. Такой подход подходит для быстрой разработки прототипов или специальных функций для внутреннего использования.

Пример:

```python
# Прямое внедрение и использование
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

# Регистрация обработчика команды
@command("hello")
async def hello_handler(event):
    await event.reply("Привет!")

# Запуск SDK и поддержание работы | Требуется запуск в асинхронной среде
asyncio.run(sdk.run(keep_running=True))
```

## Получение помощи

- Репозиторий на GitHub: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Сообщение об ошибках: отправка Issue
- Технические обсуждения: просмотр Discussions

## Связанные ссылки

- [Стандарт OneBot12](https://12.onebot.dev/)
- [Официальная документация Yunhu](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Русский**