# 适配器标准化指南（总纲）

本文档是 ErisPulse 适配器标准化的**总纲**：确立跨平台标准化的原则、标准地图、
差异处理模式、新能力进入标准的流程，并给出**交互组件标准**（按钮/键盘、下拉选择等）
与**交互回调事件**的完整定义。任何适配器开发者在实现新功能时应**优先采用标准定义**，
使模块开发者用同一份代码在任意平台获得一致的体验——命名一致、参数一致、返回一致。

---

## 1. 标准化原则

1. **命名一致**：同一概念在所有平台使用同一命名（如撤回统一 `delete_message`，
   按钮段统一 `keyboard`），不因平台而异
2. **参数一致**：标准动作/段/方法的参数结构在所有平台保持一致；平台特有参数
   以**可选扩展参数**或**扩展字段**提供，不污染标准签名
3. **返回一致**：所有 API/发送调用返回标准响应结构（`status/retcode/data/message_id/message`），
   `data` 内的标准字段（如 `user_id/user_name`）语义一致；平台原始数据放 `{platform}_raw`
4. **扩展有据**：平台特有能力按 `{platform}_` 前缀命名（段：`yunhu_form`；
   动作：`yunhu.board`；事件字段：`qqbot_button_id`），明确标识非跨平台
5. **差异在适配器层吸收**：模块代码面向标准编程，平台差异由适配器转换
   （参数映射、字段标准化、能力降级），不要求模块写平台分支
6. **能力降级不报错**：平台不支持某标准能力时，优雅降级（返回 `retcode=10002`、
   组件文本化进 `alt_message`），不抛异常中断模块逻辑

## 2. 标准地图

| 领域 | 标准文档 | 覆盖内容 |
|------|---------|---------|
| 事件转换 | [事件转换标准](event-conversion.md) | 事件结构、标准消息段（text/image/mention/reply/keyboard 等）、平台扩展段规范 |
| 交互组件 | **本文档 §5** | 按钮/键盘、下拉选择、卡片、交互回调事件标准字段、修饰器约定、各平台映射 |
| API 动作 | [API 动作标准](api-action-spec.md) | OneBot12 标准动作（用户/群/频道/消息管理/元动作）的统一接口与 `ApiDSL` |
| 请求操作 | [请求操作规范](request-action-spec.md) | 请求事件字段（request_id）与 Request DSL（approve/reject） |
| 发送方法 | [发送方法规范](send-method-spec.md) | Send 类方法命名、参数、修饰器、反向转换（OB12→平台） |
| 会话类型 | [会话类型标准](session-types.md) | user/group/channel/guild/dms 等会话类型定义与映射 |
| API 响应 | [API 响应标准](api-response.md) | 标准响应结构与 retcode 约定 |

## 3. 标准化工作流（新能力如何进入标准）

```
平台特有能力（{platform}_ 前缀）
        │  ≥2 个平台出现同类能力
        ▼
识别共性（抽取通用概念与参数子集）
        │
        ▼
标准草案（命名 + 参数 + 返回 + 各平台映射表）
        │  评审
        ▼
写入本总纲/各领域标准文档 + 框架基类/适配器实现兼容层
        │
        ▼
标准段/动作（无前缀）——模块可跨平台使用
```

**示例**：按钮最初各平台独立实现（`telegram_inline_keyboard` / 云湖 buttons /
QQBot keyboard）→ 出现在 ≥3 个平台 → 抽取通用结构（`label/type/data` + rows）
→ 发布标准 `keyboard` 段 → 各适配器实现兼容层（修饰器接受通用结构 + 标准段转换 + 原生段透传）。

### 3.1 命名规则

| 对象 | 规则 | 示例 |
|------|------|------|
| 标准消息段 | 小写，通用概念无前缀 | `keyboard`、`select`、`mention` |
| 平台扩展段 | `{platform}_` 前缀 | `telegram_sticker`、`yunhu_form` |
| 标准Api动作 | OB12 标准名（snake_case） | `get_group_info`、`delete_message` |
| 平台扩展动作 | `{platform}.` 前缀或协议通用名 | `yunhu.board`、`send_poke`（OB11 扩展） |
| 修饰器 | PascalCase，通用能力进框架基类 | `.Keyboard(rows)`、`.At(uid)` |
| 事件标准字段 | 通用概念无前缀 | `interaction_id`、`button_data`、`request_id` |
| 事件平台字段 | `{platform}_` 前缀 | `qqbot_event_id`、`telegram_chat_id` |

### 3.2 参数与返回规则

- 标准参数在所有平台**同名同义**；单位/格式在标准文档中明确（如秒级时间戳、字符串ID）
- 必填参数取各平台能力的**公共子集**；平台增强能力为可选参数
- 平台强约束（如 QQBot 富媒体不能与 event_id 混发）由适配器自动处理/降级，不暴露给模块
- 返回 `data` 的标准字段全平台一致；平台额外信息放 `data` 内平台命名字段或 `{platform}_raw`

## 4. 差异处理模式（适配器层）

| 模式 | 说明 | 示例 |
|------|------|------|
| **参数映射** | 标准参数 → 平台原生参数 | `delete_message(message_id)` → TG `deleteMessage(chat_id, message_id)`（登记表补全 chat_id） |
| **结构转换** | 标准段 → 平台原生结构 | `keyboard` 段 → `inline_keyboard` / buttons / QQBot keyboard |
| **动作映射** | 标准动作名 → 平台动作名 | `get_self_info` → `get_login_info`（OB11） |
| **字段标准化** | 平台响应 → 标准字段 | `getMe()` → `{user_id, user_name, user_displayname}` |
| **合成标识** | 平台无原生标识时生成确定性ID | TG join request 无ID → `tjr_{chat}_{user}_{date}` |
| **能力降级** | 不支持时文本化/返回10002 | Kook 无 keyboard → alt_message 文本化；`get_friend_list` → 10002 |
| **归一化** | 平台脏数据 → 标准格式 | QQBot @标记 openid → bot_id（名称归一化） |
| **双轨兼容** | 标准结构与平台原生结构同时接受 | `.Keyboard()` 接受通用 rows 或原生结构 |

---

## 5. 交互组件标准

### 5.1 组件清单与状态

| 组件 | 标准段 type | 状态 | 已支持平台 |
|------|------------|------|-----------|
| 按钮/键盘（keyboard） | `keyboard` | ✅ 已标准化 | Telegram / 云湖 / QQBot |
| 下拉选择（select） | `select` | 📋 预留（结构见 §5.4） | Discord / Telegram(bot) |
| 卡片（card） | `card` | 📋 预留（见 §5.5） | Kook / 云湖(html) |
| 模态框（modal） | `modal` | 📋 预留 | Discord |

> 修饰器层级约定：通用交互组件的 Send 修饰器由**适配器 Send 类实现**（框架基类
> 不内置），命名遵循 §5.2 约定，参数遵循本文档标准结构。

### 5.2 keyboard 按钮/内联键盘

#### 消息段结构（发送方向）

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "选项A", "type": "callback", "data": "vote:A"},
        {"label": "官网",   "type": "link",     "data": "https://example.com"}
      ]
    ]
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `data.rows` | 二维数组 | 是 | 每个子数组为一行按钮 |
| `rows[][].label` | str | 是 | 按钮显示文本 |
| `rows[][].type` | str | 是 | `callback`（点击回传数据）/ `link`（跳转URL） |
| `rows[][].data` | str | 是 | 回调数据（callback）或跳转地址（link） |
| `rows[][].*` | Any | 否 | 平台特有可选字段（如 `web_app`、`menus`），适配器按能力映射或忽略 |

#### 各平台映射对照

| 平台 | 标准段 → 原生结构 | 原生结构参考 |
|------|------------------|-------------|
| Telegram | `reply_markup.inline_keyboard`：`[{text, callback_data \| url}]` | callback→`callback_data`（≤64字节），link→`url` |
| 云湖 | `content.buttons`：`[{label, action_type}]` | callback→`action_type:2` + `action` + `value`，link→`action_type:1` + `url` |
| QQBot | `keyboard.content.rows`：`[{label, type, data}]` | callback→`type:2` + `data`，link→`type:0` + `data`（消息须为 markdown 类型） |
| Kook | 卡片 `action-group` 模块：`[{type, text, value, click}]` | callback→`click:return` + `value`，link→`click:link` + `url` |
| Discord | `components[].components`：`[{label, style, custom_id \| url}]` | callback→`style:1` + `custom_id`，link→`style:5` + `url` |

#### Send 修饰器（各适配器 Send 类实现）

通用修饰器由**各适配器在自己的 Send 类中实现**（不修改框架基类）：

- `.Keyboard(rows)`：标准命名，接受 §5.2 通用 rows 结构，内部生成标准 `keyboard`
  消息段（或直接转换为平台原生结构），由 `Raw_ob12` 统一处理
- `.Buttons(rows)`：可选语义别名，行为一致
- **向后兼容**：检测到平台原生结构时直接透传（不报错、不转换）
- 平台原生扩展段（如 `telegram_inline_keyboard`）继续透传，不受影响

```python
# 同一份代码，任意平台（各适配器提供修饰器与转换）
rows = [[{"label": "赞", "type": "callback", "data": "like:1"},
         {"label": "主页", "type": "link", "data": "https://example.com"}]]
await adapter.Send.To("group", gid).Keyboard(rows).Text("请选择")
```

> 适配器兼容清单：QQBot / Telegram / 云湖 已实现（修饰器 + 标准段转换）；
> 新适配器按本文档实现即可（见 §7 Checklist）。

### 5.3 交互回调事件（点击按钮之后）

用户点击按钮后，平台推送的事件**必须**提供以下标准字段（detail_type 可保留平台命名）：

| 标准字段 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| `interaction_id` | str | 是 | 本次交互的ID（可用于回应，如转圈/提示） |
| `button_data` | str | 是 | 按钮回传数据（即 §5.2 的 `data`） |
| `button_label` | str | 否 | 按钮显示文本 |
| `user_id` | str | 是 | 点击者 |
| `message_id` | str | 否 | 按钮所在消息 |
| `group_id` / `channel_id` | str | 否 | 来源会话 |

**detail_type 约定**：保留各平台现有命名（`qqbot_interaction` / `telegram_callback_query` /
`yunhu_a2ui_button` 等），但**标准字段必须齐备**——模块用 `event.get("button_data")` 即可跨平台取值。

**Event 扩展方法建议**（适配器 EventMixin 提供）：

```python
def get_button_data(self) -> str: ...     # button_data
def get_interaction_id(self) -> str: ...  # interaction_id
```

**回应交互**（按平台能力）：`adapter.reply_interaction(interaction_id, code=0)`（QQBot）/
`answerCallbackQuery`（Telegram）等，命名跟随平台方法族，不强制统一。

#### 各平台回调事件映射

| 平台 | 原生事件 | detail_type | interaction_id 来源 | button_data 来源 |
|------|---------|-------------|--------------------|-----------------|
| Telegram | `callback_query` | `telegram_callback_query`（notice） | `callback_query.id` | `callback_query.data` |
| 云湖 | 按钮点击事件 | `yunhu_button_click` / `yunhu_a2ui_button` | `buttonId` / `sourceComponentId` | `value` / `actionName` |
| QQBot | `INTERACTION_CREATE` | `qqbot_interaction` | `interaction.id` | `data.resolved.button_data` |
| Kook | 按钮 点击事件 | `kook_button_click` | `msg_id`+`value` | `value` |
| Discord | `INTERACTION_CREATE` | `discord_interaction` | `interaction.id` | `data.custom_id` |

### 5.4 select 下拉选择（预留）

```json
{
  "type": "select",
  "data": {
    "placeholder": "请选择",
    "options": [
      {"label": "选项A", "data": "opt:A"},
      {"label": "选项B", "data": "opt:B"}
    ],
    "min_values": 1,
    "max_values": 1
  }
}
```

回调事件复用 §5.3 字段（`button_data` = 所选 `data`，多选时为 JSON 数组）。
首批实现平台：Discord（select menu）、Telegram（keyboard 切换）。未实现平台收到该段
应在 `alt_message` 中降级为文本列表。

### 5.5 card 卡片（预留，暂缓标准化）

卡片结构差异极大（Kook 全功能卡片模块 vs 云湖 html vs QQ markdown+keyboard），
暂不做强标准。建议：

- 富文本卡片用 `text` + `keyboard` 组合表达（多数场景足够）
- 平台全功能卡片继续用 `{platform}_card` 扩展段（如 `kook_card`）
- 待出现 ≥2 个平台的同构卡片能力再评审提升

---

## 6. 未来候选（Roadmap）

以下能力已在 ≥2 平台出现或预期出现，按优先级推进标准化：

| 候选 | 涉及平台 | 优先级 | 备注 |
|------|---------|--------|------|
| select 下拉选择 | Discord / Telegram | 高 | 结构草案见 §5.4 |
| 表态/表情回应（reactions） | QQBot / Telegram / Discord / Kook | 高 | 动作 + 事件两侧标准化 |
| 群管理动作（禁言/踢人/审批） | QQBot / 云湖 / OB11 | 高 | 多数已实现为平台动作，待抽取标准签名 |
| 公告/看板 | 云湖 / Telegram / Discord | 中 | `set_announcement` 类动作 |
| 文件上传标准（file_id 两段式） | 各平台 | 中 | 见 API 动作标准（当前降级可用） |
| 卡片 card | Kook / 云湖 | 低 | 结构差异大，见 §5.5 |
| 表单 form | 云湖 | 低 | 平台特有，保持 `{platform}_` 前缀 |
| 媒体转码/大小探测 | 各平台 | 低 | 适配器内部实现，不对外标准化 |

## 7. 新适配器开发者的标准 Checklist

开发新适配器时，按此清单对照实现（★ 为必须，其余推荐）：

- [ ] ★ 事件转换为 OneBot12 标准结构，继承 `BaseConverter`
- [ ] ★ 标准消息段收发支持（text/image/mention/reply/keyboard…）
- [ ] ★ 实现 `Raw_ob12`（含标准段 → 平台结构转换；标准 `keyboard` 段必做）
- [ ] ★ 返回标准响应结构（`make_response`/`make_error`）
- [ ] ★ 多账户：`AccountConfigClass(BotAccountConfig)` + `_resolve_account`
- [ ] ★ Send 类继承 `BaseAdapter.Send`，用 `_apply_modifiers`/`send_context`
- [ ] ☆ Api DSL：标准动作映射到平台API（见 API 动作标准）
- [ ] ☆ Request DSL：请求事件含 `request_id` + `accept/reject`
- [ ] ☆ 交互组件：`keyboard` 段转换 + 交互回调标准字段 + `.Keyboard()`/`.Buttons()` 修饰器（适配器 Send 类实现）
- [ ] ☆ EventMixin：`get_raw_event()` / `get_button_data()` 等平台扩展方法
- [ ] ☆ 生命周期任务用 `runtime.spawn_background`
- [ ] ☆ 配置读取用 `self.cfg`
- [ ] ☆ 框架软依赖：不声明 ErisPulse 硬依赖 + 运行时版本检测
- [ ] ☆ i18n：配置字段与日志多语言
- [ ] ☆ platform-guide 平台文档 + 适配器仓库 platform-features.md

## 8. 相关文档

- 各领域标准见 §2 标准地图
- 框架内置适配器可作参考实现：QQBot（v5 范式全量）、OneBot11（Api DSL 映射）、云湖（BaseConverter + Web API 扩展）
