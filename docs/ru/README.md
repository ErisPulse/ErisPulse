# Документация ErisPulse

ErisPulse — это масштабируемая многофункциональная платформа для обработки сообщений, поддерживающая взаимодействие с различными платформами через адаптеры и предоставляющая гибкую систему модулей для расширения функциональности.

> **Первый раз?** Просто посмотрите на [Быстрый старт за 5 минут](docs/ru/quick-start.md) — от установки до запуска первого бота, шаг за шагом.
>
> Столкнулись с непонятными терминами? Посмотрите на [Глоссарий](docs/ru/terminology.md).

---

## Выберите свой путь

Выберите соответствующий путь обучения в зависимости от ваших целей. Каждый путь организован от простого к сложному.

### 1. Я хочу использовать бота

Запустите бота, установите модули, настройте параметры.

| Этап | Документ | Описание |
|------|----------|----------|
| **① Начало** | [Быстрый старт за 5 минут](docs/ru/quick-start.md) | Установка, инициализация, запуск — единственный входной путь |
| ② Глубже | [Создание первого бота](docs/ru/getting-started/first-bot.md) | Написание первого обработчика команд |
| ③ Понятия | [Основные понятия](docs/ru/getting-started/basic-concepts.md) | Понимание концепции адаптеров/модулей/событий |
| ④ Практика | [Примеры распространённых задач](docs/ru/getting-started/common-tasks.md) | Хранение, планирование задач, управление правами |
| Справка | [Описание файла конфигурации](docs/ru/user-guide/configuration.md) · [Справочник CLI](docs/ru/user-guide/cli-reference.md) · [Руководство по развертыванию](docs/ru/user-guide/deployment.md) | Просмотр по мере необходимости |
| Справка | [Руководство по функциям платформ](docs/ru/platform-guide/README.md) | Различия между платформами (Yunhu/QQ/Telegram и т.д.) |

### 2. Я хочу разрабатывать модули / адаптеры

Разработка расширений для ErisPulse, которые можно распространять.

| Тип | Начало | Продвинутый |
|------|--------|------------|
| **Разработка модулей** (рекомендуется) | [Введение в разработку модулей](docs/ru/developer-guide/modules/getting-started.md) | [Основные понятия](docs/ru/developer-guide/modules/core-concepts.md) · [Обёртка событий](docs/ru/developer-guide/modules/event-wrapper.md) · [Лучшие практики](docs/ru/developer-guide/modules/best-practices.md) |
| **Разработка адаптеров** | [Введение в разработку адаптеров](docs/ru/developer-guide/adapters/getting-started.md) | [Основные понятия](docs/ru/developer-guide/adapters/core-concepts.md) · [Подробное объяснение SendDSL](docs/ru/developer-guide/adapters/send-dsl.md) · [Конвертер событий](docs/ru/developer-guide/adapters/converter.md) · [Лучшие практики](docs/ru/developer-guide/adapters/best-practices.md) |
| **Технические стандарты** | [Обзор стандартов](docs/ru/standards/README.md) | Стандарты, которые необходимо соблюдать при разработке адаптеров: [Типы сессий](docs/ru/standards/session-types.md) · [Преобразование событий](docs/ru/standards/event-conversion.md) · [Методы отправки](docs/ru/standards/send-method-spec.md) · [Ответы API](docs/ru/standards/api-response.md) · [Операции запроса](docs/ru/standards/request-action-spec.md) |
| **Публикация** | [Публикация и магазин модулей](docs/ru/developer-guide/publishing.md) | Публикация в PyPI и магазин модулей |

### 3. Я хочу глубже понять принципы работы

Понимание того, как работает внутренняя архитектура.

| Документ | Описание |
|----------|----------|
| [Обзор архитектуры](docs/ru/architecture.md) | Визуальная диаграмма: основная архитектура, процесс инициализации, обработка событий, жизненный цикл |
| [Процесс запуска и ручное управление](docs/ru/advanced/startup.md) | Разбор цепочки запуска, ручное управление этапами, диагностика ошибок загрузки |
| [Система событий](docs/ru/api-reference/event-system.md) | Полный API для пяти основных типов событий |
| [Система адаптеров](docs/ru/api-reference/adapter-system.md) | Регистрация, запуск и остановка адаптеров, вызов API |
| [Основные модули](docs/ru/api-reference/core-modules.md) | Основные возможности: Storage / Config / Logger / Router и т.д. |
| [Управление жизненным циклом](docs/ru/advanced/lifecycle.md) · [Ленивая загрузка](docs/ru/advanced/lazy-loading.md) · [Система маршрутизации](docs/ru/advanced/router.md) | Внутренние подсистемы |
| [Многошаговый диалог Conversation](docs/ru/advanced/conversation.md) · [MessageBuilder](docs/ru/advanced/message-builder.md) · [SQL Builder](docs/ru/advanced/sql-builder.md) · [HTTP-клиент](docs/ru/advanced/http-client.md) · [Международная локализация](docs/ru/advanced/i18n.md) | Расширенные инструменты |
| [Панель управления Dashboard](docs/ru/advanced/dashboard-view.md) | Веб-интерфейс управления |

---

## Способы разработки

ErisPulse поддерживает два способа разработки:

- **Разработка модулей (рекомендуется):** Создание отдельных пакетов модулей, устанавливаемых через менеджер пакетов, что упрощает распространение и управление.
- **Встраиваемая разработка:** Прямое написание обработчиков в проекте, подходит для быстрой разработки прототипов. Подробности см. в [Быстром старте](docs/ru/quick-start.md).

## Другое

- [Стиль документации](docs/ru/styleguide/docstring.md) — правила написания документации при внесении изменений
- [Поддержка разработки с помощью ИИ](docs/ru/ai-support/README.md) — получение подсказок для помощников по программированию на основе ИИ

## Получите помощь

- Репозиторий на GitHub: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Сообщение об ошибках: создание Issue
- Технические обсуждения: просмотра Discussions

## Связанные ссылки

- [Стандарт OneBot12](https://12.onebot.dev/)
- [Официальная документация Yunhu](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Русский**