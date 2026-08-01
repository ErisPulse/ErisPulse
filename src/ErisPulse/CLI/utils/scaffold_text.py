"""
脚手架模板多语言文案

`epsdk create` 生成的模块/适配器模板里的注释、docstring 与日志消息
跟随脚手架用户的语言。本模块用独立类集中维护这些文案，避免散落在
``create.py`` 模板字符串里难以维护。

语言代码沿用 CLI i18n 的 5 种：zh-CN / zh-TW / en / ja / ru。
用户语言未知时回退英文（en）。

{!--< internal-use >!--}
{!--< /internal-use >!--}
"""

from typing import Any

# 支持的脚手架文案语言（与 CLI i18n 一致）
SCAFFOLD_LANGS: tuple[str, ...] = ("zh-CN", "zh-TW", "en", "ja", "ru")

# 缺省语言
DEFAULT_SCAFFOLD_LANG: str = "en"

# 每个文案键的默认值（英文），用作缺失语言时的兜底
_EN_FALLBACK: dict[str, str] = {
    # ---- 模块模板 ----
    "module.doc": "{name} module\n\nInherits from BaseModule with standardized lifecycle "
    "and event handling. Config is managed declaratively via ConfigClass (read live "
    "through self.cfg); translation keys are declared in I18nClass.",
    "module.config_doc": "{name} module config",
    "module.config_hint": "Config class declared as a nested class (needs @dataclass); "
    "the framework auto-detects ConfigClass.",
    "module.i18n_hint": "I18nClass declares translation keys; the framework auto-registers "
    "them. Keys referenced by config description / command help must be declared here.",
    "module.config_updated_doc": "Called when module config hot-reloads",
    "module.on_load_doc": "Called when the module is loaded",
    "module.on_unload_doc": "Called when the module is unloaded",
    "module.log.init_done": "{name} initialized",
    "module.log.loaded": "Module loaded: {event}",
    "module.log.unloaded": "Module unloaded: {event}",
    "module.log.config_updated": "Module config hot-reloaded",
    "module.log.private_message": "Received private message: {content}",
    "module.log.friend_add": "New friend added: {nickname}",
    # ---- 适配器模板 ----
    "adapter.doc": "{name} adapter\n\nInherits from BaseAdapter with declarative config "
    "(ConfigClass), SendDSL-style chained calls and bot status tracking.",
    "adapter.config_doc": "{name} adapter config",
    "adapter.config_hint": "Config class declared as a nested class (needs @dataclass); "
    "the framework auto-detects ConfigClass.",
    "adapter.i18n_hint": "I18nClass declares translation keys; the framework auto-registers "
    "them. Keys referenced by config description must be declared here.",
    "adapter.converter_doc": "{name} event converter\n\nConverts platform-native events to "
    "the OneBot12 standard format using BaseConverter helpers.",
    "adapter.dsl.send_doc": "Send message DSL\n\nAt / AtAll / Reply / Using / To are handled "
    "by the framework base class. Standard send methods (Text/Image/Voice/Video/File) are "
    "inherited from the SendDSL base class, delegating to Raw_ob12 by default, so no need to "
    "re-implement. Use self._apply_modifiers(message) to merge modifiers into the message "
    "segments. Use self.send_context to get the send context (target_type, target_id, "
    "account_id).\n\nSupports chained calls:\n"
    'Send.To("group", "123").At("456").Reply("789").Text("hi")',
    "adapter.dsl.send_std_methods_hint": "Standard send methods (Text/Image/Voice/Video/File) "
    "are inherited from the base class, delegating to Raw_ob12 by default.",
    "adapter.dsl.send_override_hint": "To use platform-specific logic, override a single method:",
    "adapter.dsl.send_extra_methods_hint": "You can add platform-specific send methods "
    "(recognized by event.supports()):",
    "adapter.dsl.request_doc": "Request action DSL\n\nAdapters should override accept / reject "
    "to implement platform-specific request handling logic. If the platform does not support "
    "request operations, this inner class may be omitted. The base class returns retcode=10002 "
    "(unsupported operation) by default.",
    "adapter.dsl.api_doc": "Standard API actions DSL\n\nProvides cross-platform OneBot12 "
    "standard actions (info queries / group management / message management / file operations). "
    "The default implementation delegates to call_api; adapters may override individual methods "
    'to map to platform-native APIs. Platform extension actions are invoked via call("prefix.action", **params).',
    "adapter.dsl.api_std_methods_hint": "Standard methods (get_user_info / get_group_info / "
    "delete_message, etc.) are inherited from the base class,",
    "adapter.dsl.api_override_hint": "delegating to call_api by default. Override individual "
    "methods for platform-specific logic:",
    "adapter.log.config_updated": "Adapter config hot-reloaded",
    "adapter.log.starting": "Starting adapter",
    "adapter.log.ws_registered": "WebSocket route registered",
    "adapter.log.bot_connected": "Bot connected",
    "adapter.log.connection_lost": "Connection lost",
    "adapter.log.bot_disconnected": "Bot disconnected",
    "adapter.log.shutdown": "Adapter shut down",
    "adapter.log.api_call_failed": "API call failed: {error}",
}

# 多语言文案表（缺失语言时回退 _EN_FALLBACK）
_TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh-CN": {
        "module.doc": "{name}模块\n\n继承自 BaseModule 基类，实现了标准化的模块生命周期管理和事件处理。"
        "使用声明式配置管理（ConfigClass），通过 self.cfg 实时读取配置；"
        "通过 I18nClass 声明翻译键。",
        "module.config_doc": "{name} 模块配置",
        "module.config_hint": "配置类以嵌套类形式声明（需 @dataclass 装饰），框架自动识别 ConfigClass。",
        "module.i18n_hint": "I18nClass 声明翻译键，框架自动注册；配置描述/命令帮助引用的键必须在此声明。",
        "module.config_updated_doc": "模块配置热更新时调用",
        "module.on_load_doc": "模块被加载时调用",
        "module.on_unload_doc": "模块被卸载时调用",
        "module.log.init_done": "{name} 初始化完成",
        "module.log.loaded": "模块已加载: {event}",
        "module.log.unloaded": "模块已卸载: {event}",
        "module.log.config_updated": "模块配置已热更新",
        "module.log.private_message": "收到私聊消息: {content}",
        "module.log.friend_add": "新好友添加: {nickname}",
        "adapter.doc": "{name} 适配器\n\n继承自 BaseAdapter 基类，使用声明式配置管理（ConfigClass），"
        "实现了 SendDSL 风格的链式调用接口和 Bot 状态追踪。",
        "adapter.config_doc": "{name} 适配器配置",
        "adapter.config_hint": "配置类以嵌套类形式声明（需 @dataclass 装饰），框架自动识别 ConfigClass。",
        "adapter.i18n_hint": "I18nClass 声明翻译键，框架自动注册；配置描述引用的键必须在此声明。",
        "adapter.converter_doc": "{name} 事件转换器\n\n使用 BaseConverter 辅助方法，将平台原生事件转换为 OneBot12 标准格式。",
        "adapter.dsl.send_doc": "Send 消息发送 DSL\n\nAt / AtAll / Reply / Using / To 由框架基类内置处理。"
        "标准发送方法（Text/Image/Voice/Video/File）已从 SendDSL 基类继承，"
        "默认委托给 Raw_ob12，无需重复实现。"
        "使用 self._apply_modifiers(message) 合并修饰器到消息段。"
        "使用 self.send_context 获取发送上下文 (target_type, target_id, account_id)。\n\n"
        "支持链式调用:\n"
        'Send.To("group", "123").At("456").Reply("789").Text("hi")',
        "adapter.dsl.send_std_methods_hint": "标准发送方法（Text/Image/Voice/Video/File）已从基类继承，默认委托给 Raw_ob12。",
        "adapter.dsl.send_override_hint": "如需平台特定逻辑，可覆盖单个方法：",
        "adapter.dsl.send_extra_methods_hint": "可添加平台特有的发送方法（会被 event.supports() 识别）：",
        "adapter.dsl.request_doc": "Request 请求操作 DSL\n\n适配器应重写 accept / reject 实现平台特定的请求处理逻辑。"
        "如果平台不支持请求操作，可不实现此内部类。"
        "基类默认返回 retcode=10002（不支持的操作）。",
        "adapter.dsl.api_doc": "标准 API 动作 DSL\n\n提供跨平台的 OneBot12 标准动作（信息查询/群管理/消息管理/文件操作）。"
        "默认实现委托给 call_api，适配器可覆盖单个方法映射到平台原生 API。"
        '平台扩展动作通过 call("prefix.action", **params) 调用。',
        "adapter.dsl.api_std_methods_hint": "标准方法（get_user_info / get_group_info / delete_message 等）已从基类继承，",
        "adapter.dsl.api_override_hint": "默认委托给 call_api。如需平台特定逻辑，可覆盖单个方法：",
        "adapter.log.config_updated": "适配器配置已热更新",
        "adapter.log.starting": "正在启动适配器",
        "adapter.log.ws_registered": "WebSocket 路由已注册",
        "adapter.log.bot_connected": "Bot 已连接",
        "adapter.log.connection_lost": "连接已断开",
        "adapter.log.bot_disconnected": "Bot 已断开",
        "adapter.log.shutdown": "适配器已关闭",
        "adapter.log.api_call_failed": "API 调用失败: {error}",
    },
    "zh-TW": {
        "module.doc": "{name}模組\n\n繼承自 BaseModule 基類，實現標準化的模組生命週期管理和事件處理。"
        "使用宣告式設定管理（ConfigClass），透過 self.cfg 即時讀取設定；"
        "透過 I18nClass 宣告翻譯鍵。",
        "module.config_doc": "{name} 模組設定",
        "module.config_hint": "設定類以巢狀類別形式宣告（需 @dataclass 裝飾），框架自動識別 ConfigClass。",
        "module.i18n_hint": "I18nClass 宣告翻譯鍵，框架自動註冊；設定描述/命令說明引用的鍵必須在此宣告。",
        "module.config_updated_doc": "模組設定熱更新時呼叫",
        "module.on_load_doc": "模組被載入時呼叫",
        "module.on_unload_doc": "模組被卸載時呼叫",
        "module.log.init_done": "{name} 初始化完成",
        "module.log.loaded": "模組已載入: {event}",
        "module.log.unloaded": "模組已卸載: {event}",
        "module.log.config_updated": "模組設定已熱更新",
        "module.log.private_message": "收到私聊訊息: {content}",
        "module.log.friend_add": "新好友添加: {nickname}",
        "adapter.doc": "{name} 適配器\n\n繼承自 BaseAdapter 基類，使用宣告式設定管理（ConfigClass），"
        "實作 SendDSL 風格的鏈式呼叫介面和 Bot 狀態追蹤。",
        "adapter.config_doc": "{name} 適配器設定",
        "adapter.config_hint": "設定類以巢狀類別形式宣告（需 @dataclass 裝飾），框架自動識別 ConfigClass。",
        "adapter.i18n_hint": "I18nClass 宣告翻譯鍵，框架自動註冊；設定描述引用的鍵必須在此宣告。",
        "adapter.converter_doc": "{name} 事件轉換器\n\n使用 BaseConverter 輔助方法，將平台原生事件轉換為 OneBot12 標準格式。",
        "adapter.dsl.send_doc": "Send 訊息傳送 DSL\n\nAt / AtAll / Reply / Using / To 由框架基類內建處理。"
        "標準傳送方法（Text/Image/Voice/Video/File）已從 SendDSL 基類繼承，"
        "預設委派給 Raw_ob12，無需重複實作。"
        "使用 self._apply_modifiers(message) 合併修飾器到訊息區段。"
        "使用 self.send_context 取得傳送上下文 (target_type, target_id, account_id)。\n\n"
        "支援鏈式呼叫:\n"
        'Send.To("group", "123").At("456").Reply("789").Text("hi")',
        "adapter.dsl.send_std_methods_hint": "標準傳送方法（Text/Image/Voice/Video/File）已從基類繼承，預設委派給 Raw_ob12。",
        "adapter.dsl.send_override_hint": "如需平台特定邏輯，可覆寫單一方法：",
        "adapter.dsl.send_extra_methods_hint": "可新增平台特有的傳送方法（會被 event.supports() 識別）：",
        "adapter.dsl.request_doc": "Request 請求操作 DSL\n\n適配器應覆寫 accept / reject 實作平台特定的請求處理邏輯。"
        "如果平台不支援請求操作，可不實作此內部類別。"
        "基類預設回傳 retcode=10002（不支援的操作）。",
        "adapter.dsl.api_doc": "標準 API 動作 DSL\n\n提供跨平台的 OneBot12 標準動作（資訊查詢/群組管理/訊息管理/檔案操作）。"
        "預設實作委派給 call_api，適配器可覆寫單一方法對應到平台原生 API。"
        '平台擴充動作透過 call("prefix.action", **params) 呼叫。',
        "adapter.dsl.api_std_methods_hint": "標準方法（get_user_info / get_group_info / delete_message 等）已從基類繼承，",
        "adapter.dsl.api_override_hint": "預設委派給 call_api。如需平台特定邏輯，可覆寫單一方法：",
        "adapter.log.config_updated": "適配器設定已熱更新",
        "adapter.log.starting": "正在啟動適配器",
        "adapter.log.ws_registered": "WebSocket 路由已註冊",
        "adapter.log.bot_connected": "Bot 已連線",
        "adapter.log.connection_lost": "連線已斷開",
        "adapter.log.bot_disconnected": "Bot 已斷開",
        "adapter.log.shutdown": "適配器已關閉",
        "adapter.log.api_call_failed": "API 呼叫失敗: {error}",
    },
    "ja": {
        "module.doc": "{name} モジュール\n\nBaseModule を継承し、標準化されたライフサイクル管理とイベント処理を実装。"
        "設定は ConfigClass で宣言的に管理（self.cfg でリアルタイム参照）、翻訳キーは I18nClass で宣言。",
        "module.config_doc": "{name} モジュール設定",
        "module.config_hint": "設定クラスはネストクラスとして宣言（@dataclass 必須）。フレームワークが ConfigClass を自動認識します。",
        "module.i18n_hint": "I18nClass で翻訳キーを宣言すると自動登録されます。設定説明/コマンドヘルプで参照するキーはここで宣言してください。",
        "module.config_updated_doc": "モジュール設定のホットリロード時に呼び出されます",
        "module.on_load_doc": "モジュール読み込み時に呼び出されます",
        "module.on_unload_doc": "モジュールアンロード時に呼び出されます",
        "module.log.init_done": "{name} の初期化が完了しました",
        "module.log.loaded": "モジュールをロードしました: {event}",
        "module.log.unloaded": "モジュールをアンロードしました: {event}",
        "module.log.config_updated": "モジュール設定をホットリロードしました",
        "module.log.private_message": "プライベートメッセージを受信しました: {content}",
        "module.log.friend_add": "新しい友達が追加されました: {nickname}",
        "adapter.doc": "{name} アダプター\n\nBaseAdapter を継承し、宣言的な設定（ConfigClass）、SendDSL チェーン呼び出し、Bot 状態追跡を実装。",
        "adapter.config_doc": "{name} アダプター設定",
        "adapter.config_hint": "設定クラスはネストクラスとして宣言（@dataclass 必須）。フレームワークが ConfigClass を自動認識します。",
        "adapter.i18n_hint": "I18nClass で翻訳キーを宣言すると自動登録されます。設定説明で参照するキーはここで宣言してください。",
        "adapter.converter_doc": "{name} イベントコンバーター\n\nBaseConverter ヘルパーを使い、プラットフォームイベントを OneBot12 形式に変換します。",
        "adapter.dsl.send_doc": "Send メッセージ送信 DSL\n\nAt / AtAll / Reply / Using / To はフレームワークのベースクラスで処理されます。"
        "標準送信メソッド（Text/Image/Voice/Video/File）は SendDSL ベースクラスから継承され、"
        "デフォルトでは Raw_ob12 に委譲されるため、再実装は不要です。"
        "self._apply_modifiers(message) でメッセージセグメントに修飾子をマージします。"
        "self.send_context で送信コンテキスト（target_type, target_id, account_id）を取得します。\n\n"
        "チェーン呼び出しに対応:\n"
        'Send.To("group", "123").At("456").Reply("789").Text("hi")',
        "adapter.dsl.send_std_methods_hint": "標準送信メソッド（Text/Image/Voice/Video/File）はベースクラスから継承され、デフォルトで Raw_ob12 に委譲されます。",
        "adapter.dsl.send_override_hint": "プラットフォーム固有のロジックが必要な場合は、単一のメソッドをオーバーライドしてください：",
        "adapter.dsl.send_extra_methods_hint": "プラットフォーム固有の送信メソッドを追加できます（event.supports() で認識されます）：",
        "adapter.dsl.request_doc": "Request リクエスト操作 DSL\n\nアダプターは accept / reject をオーバーライドして、プラットフォーム固有のリクエスト処理を実装してください。"
        "プラットフォームがリクエスト操作をサポートしていない場合、この内部クラスは実装不要です。"
        "ベースクラスはデフォルトで retcode=10002（サポートされていない操作）を返します。",
        "adapter.dsl.api_doc": "標準 API アクション DSL\n\nクロスプラットフォームの OneBot12 標準アクション（情報取得/グループ管理/メッセージ管理/ファイル操作）を提供します。"
        "デフォルト実装は call_api に委譲します。アダプターは個別メソッドをオーバーライドしてプラットフォーム API にマッピングできます。"
        'プラットフォーム拡張アクションは call("prefix.action", **params) で呼び出します。',
        "adapter.dsl.api_std_methods_hint": "標準メソッド（get_user_info / get_group_info / delete_message など）はベースクラスから継承され、",
        "adapter.dsl.api_override_hint": "デフォルトでは call_api に委譲されます。プラットフォーム固有のロジックが必要な場合は、単一のメソッドをオーバーライドしてください：",
        "adapter.log.config_updated": "アダプター設定をホットリロードしました",
        "adapter.log.starting": "アダプターを起動しています",
        "adapter.log.ws_registered": "WebSocket ルートを登録しました",
        "adapter.log.bot_connected": "Bot に接続しました",
        "adapter.log.connection_lost": "接続が切断されました",
        "adapter.log.bot_disconnected": "Bot が切断されました",
        "adapter.log.shutdown": "アダプターを停止しました",
        "adapter.log.api_call_failed": "API 呼び出しに失敗: {error}",
    },
    "ru": {
        "module.doc": "{name} модуль\n\nНаследует BaseModule: стандартный жизненный цикл и обработка событий. "
        "Конфигурация объявляется через ConfigClass (чтение через self.cfg), ключи переводов — в I18nClass.",
        "module.config_doc": "Конфигурация модуля {name}",
        "module.config_hint": "Класс конфигурации объявляется как вложенный (нужен @dataclass); фреймворк распознаёт ConfigClass.",
        "module.i18n_hint": "Ключи переводов объявляются в I18nClass и регистрируются автоматически; ключи из описания/справки должны быть здесь.",
        "module.config_updated_doc": "Вызывается при горячей перезагрузке конфигурации",
        "module.on_load_doc": "Вызывается при загрузке модуля",
        "module.on_unload_doc": "Вызывается при выгрузке модуля",
        "module.log.init_done": "{name} инициализирован",
        "module.log.loaded": "Модуль загружен: {event}",
        "module.log.unloaded": "Модуль выгружен: {event}",
        "module.log.config_updated": "Конфигурация модуля перезагружена",
        "module.log.private_message": "Получено личное сообщение: {content}",
        "module.log.friend_add": "Добавлен новый друг: {nickname}",
        "adapter.doc": "{name} адаптер\n\nНаследует BaseAdapter: декларативная конфигурация (ConfigClass), "
        "цепочки SendDSL и отслеживание статуса бота.",
        "adapter.config_doc": "Конфигурация адаптера {name}",
        "adapter.config_hint": "Класс конфигурации объявляется как вложенный (нужен @dataclass); фреймворк распознаёт ConfigClass.",
        "adapter.i18n_hint": "Ключи переводов объявляются в I18nClass и регистрируются автоматически; ключи из описания должны быть здесь.",
        "adapter.converter_doc": "{name} конвертер событий\n\nИспользует вспомогательные методы BaseConverter для преобразования в OneBot12.",
        "adapter.dsl.send_doc": "Send — DSL отправки сообщений\n\nAt / AtAll / Reply / Using / To обрабатываются базовым классом фреймворка. "
        "Стандартные методы отправки (Text/Image/Voice/Video/File) наследуются из базового класса SendDSL "
        "и по умолчанию делегируются Raw_ob12, повторная реализация не нужна. "
        "Используйте self._apply_modifiers(message) для слияния модификаторов в сегменты сообщения. "
        "Используйте self.send_context для получения контекста отправки (target_type, target_id, account_id).\n\n"
        "Поддерживается цепной вызов:\n"
        'Send.To("group", "123").At("456").Reply("789").Text("hi")',
        "adapter.dsl.send_std_methods_hint": "Стандартные методы отправки (Text/Image/Voice/Video/File) наследуются из базового класса и по умолчанию делегируются Raw_ob12.",
        "adapter.dsl.send_override_hint": "Для платформо-специфичной логики переопределите отдельный метод:",
        "adapter.dsl.send_extra_methods_hint": "Можно добавить платформо-специфичные методы отправки (распознаются через event.supports()):",
        "adapter.dsl.request_doc": "Request — DSL операций запроса\n\nАдаптер должен переопределить accept / reject для реализации логики обработки запросов платформы. "
        "Если платформа не поддерживает операции запроса, этот внутренний класс можно не реализовывать. "
        "Базовый класс по умолчанию возвращает retcode=10002 (операция не поддерживается).",
        "adapter.dsl.api_doc": "DSL стандартных API-действий\n\nПредоставляет кроссплатформенные стандартные действия OneBot12 (информационные запросы / управление группами / управление сообщениями / работа с файлами). "
        "Реализация по умолчанию делегирует call_api; адаптер может переопределить отдельные методы для отображения на нативные API платформы. "
        'Расширенные действия платформы вызываются через call("prefix.action", **params).',
        "adapter.dsl.api_std_methods_hint": "Стандартные методы (get_user_info / get_group_info / delete_message и т. д.) наследуются из базового класса,",
        "adapter.dsl.api_override_hint": "по умолчанию делегируется call_api. Для платформо-специфичной логики переопределите отдельный метод:",
        "adapter.log.config_updated": "Конфигурация адаптера перезагружена",
        "adapter.log.starting": "Запуск адаптера",
        "adapter.log.ws_registered": "WebSocket маршрут зарегистрирован",
        "adapter.log.bot_connected": "Бот подключён",
        "adapter.log.connection_lost": "Соединение потеряно",
        "adapter.log.bot_disconnected": "Бот отключён",
        "adapter.log.shutdown": "Адаптер остановлен",
        "adapter.log.api_call_failed": "Ошибка вызова API: {error}",
    },
}


class ScaffoldText:
    """
    脚手架模板多语言文案

    按用户语言提供模板注释 / docstring / 日志文本。缺失语言回退英文。
    文案键集中定义在模块级 ``_TRANSLATIONS``，新增语言只需补充对应条目。
    """

    def __init__(self, lang: str | None = None):
        """
        :param lang: [str|None] 目标语言代码；None 时自动检测 CLI 当前语言
        """
        if lang is None:
            lang = self._detect_lang()
        self.lang: str = lang if lang in SCAFFOLD_LANGS else DEFAULT_SCAFFOLD_LANG

    @staticmethod
    def _detect_lang() -> str:
        """从 CLI i18n 检测当前语言，失败回退默认"""
        try:
            from ..i18n import i18n

            return i18n.get_language() or DEFAULT_SCAFFOLD_LANG
        except Exception:
            return DEFAULT_SCAFFOLD_LANG

    def t(self, key: str, **kwargs: Any) -> str:
        """
        获取指定文案键在目标语言下的文本

        :param key: 文案键（见 ``_TRANSLATIONS`` / ``_EN_FALLBACK``）
        :param kwargs: 填充占位符（如 ``name=``/``event=``/``content=``）
        :return: 文本；未知键返回键名
        """
        table = _TRANSLATIONS.get(self.lang) or {}
        text = table.get(key) or _EN_FALLBACK.get(key)
        if text is None:
            return key
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text

    def all(self) -> dict[str, str]:
        """返回当前语言下所有文案（未格式化）"""
        table = _TRANSLATIONS.get(self.lang) or {}
        merged = dict(_EN_FALLBACK)
        merged.update(table)
        return merged


__all__ = ["DEFAULT_SCAFFOLD_LANG", "SCAFFOLD_LANGS", "ScaffoldText"]
